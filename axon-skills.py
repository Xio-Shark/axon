#!/usr/bin/env python3
"""Axon 技能包管理器 — 从 GitHub 仓库安装/管理技能脚本。

用法:
    python axon-skills.py add <github_url> [--skill <name>]
    python axon-skills.py list
    python axon-skills.py remove <name>
    python axon-skills.py info <name>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
REGISTRY_FILE = os.path.join(SKILLS_DIR, ".registry.json")
VALID_EXTENSIONS = (".py", ".sh")
DESC_PREFIX = "# DESC:"


# ── 注册表（记录来源信息） ──

def _load_registry() -> dict:
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(reg: dict):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


def _parse_desc(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            line = f.readline().strip()
        if line.startswith(DESC_PREFIX):
            return line[len(DESC_PREFIX):].strip()
    except Exception:
        pass
    return "无描述"


# ── add 命令 ──

def cmd_add(args):
    url = args.url.rstrip("/")
    if not url.startswith("https://github.com/"):
        _die("仅支持 GitHub 仓库 URL")

    # 克隆到临时目录
    with tempfile.TemporaryDirectory() as tmp:
        clone_url = url if url.endswith(".git") else url + ".git"
        _info(f"克隆仓库: {clone_url}")
        ret = subprocess.run(
            ["git", "clone", "--depth=1", clone_url, tmp],
            capture_output=True, text=True,
        )
        if ret.returncode != 0:
            _die(f"克隆失败: {ret.stderr.strip()}")

        # 扫描可安装的技能文件
        candidates = _scan_skills(tmp)
        if not candidates:
            _die("该仓库中未找到技能文件（需要 .py/.sh 且首行含 # DESC:）")

        # 筛选
        if args.skill:
            matched = [c for c in candidates if args.skill in c["name"]]
            if not matched:
                names = ", ".join(c["name"] for c in candidates)
                _die(f"未找到匹配 '{args.skill}' 的技能\n可用: {names}")
            candidates = matched

        # 安装
        os.makedirs(SKILLS_DIR, exist_ok=True)
        reg = _load_registry()
        installed = []

        for c in candidates:
            dest = os.path.join(SKILLS_DIR, c["name"])
            if os.path.exists(dest) and not args.force:
                _warn(f"跳过 {c['name']}（已存在，用 --force 覆盖）")
                continue
            shutil.copy2(c["path"], dest)
            reg[c["name"]] = {
                "source": url,
                "description": c["description"],
            }
            installed.append(c["name"])
            _ok(f"安装: {c['name']} — {c['description']}")

        _save_registry(reg)
        if installed:
            _ok(f"\n共安装 {len(installed)} 个技能")
        else:
            _warn("无新技能安装")


def _scan_skills(root: str) -> list[dict]:
    """递归扫描目录，找到所有含 DESC 注释的脚本。"""
    results = []
    for dirpath, _, filenames in os.walk(root):
        # 跳过隐藏目录
        if any(part.startswith(".") for part in dirpath.split(os.sep)):
            if dirpath != root:
                continue
        for fname in sorted(filenames):
            if not fname.endswith(VALID_EXTENSIONS):
                continue
            full = os.path.join(dirpath, fname)
            desc = _parse_desc(full)
            if desc != "无描述":
                results.append({
                    "name": fname,
                    "path": full,
                    "description": desc,
                })
    return results


# ── list 命令 ──

def cmd_list(_args):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    reg = _load_registry()
    files = sorted(
        f for f in os.listdir(SKILLS_DIR)
        if f.endswith(VALID_EXTENSIONS)
    )
    if not files:
        print("📭 暂无已安装技能")
        return

    print(f"🛠 已安装 {len(files)} 个技能:\n")
    for f in files:
        desc = _parse_desc(os.path.join(SKILLS_DIR, f))
        source = reg.get(f, {}).get("source", "本地")
        print(f"  {f:<30} {desc}")
        if source != "本地":
            print(f"  {'':30} ↳ {source}")


# ── remove 命令 ──

def cmd_remove(args):
    target = args.name
    # 补全扩展名
    if not target.endswith(VALID_EXTENSIONS):
        for ext in VALID_EXTENSIONS:
            if os.path.exists(os.path.join(SKILLS_DIR, target + ext)):
                target = target + ext
                break

    path = os.path.join(SKILLS_DIR, target)
    if not os.path.exists(path):
        _die(f"技能不存在: {target}")

    os.remove(path)
    reg = _load_registry()
    reg.pop(target, None)
    _save_registry(reg)
    _ok(f"已移除: {target}")


# ── info 命令 ──

def cmd_info(args):
    target = args.name
    if not target.endswith(VALID_EXTENSIONS):
        for ext in VALID_EXTENSIONS:
            if os.path.exists(os.path.join(SKILLS_DIR, target + ext)):
                target = target + ext
                break

    path = os.path.join(SKILLS_DIR, target)
    if not os.path.exists(path):
        _die(f"技能不存在: {target}")

    reg = _load_registry()
    meta = reg.get(target, {})
    desc = _parse_desc(path)

    print(f"📦 {target}")
    print(f"   描述:   {desc}")
    print(f"   来源:   {meta.get('source', '本地')}")
    print(f"   路径:   {path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"   行数:   {len(lines)}")


# ── 输出工具 ──

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def _ok(msg):
    print(f"{GREEN}[✓]{NC} {msg}")


def _warn(msg):
    print(f"{YELLOW}[!]{NC} {msg}")


def _die(msg):
    print(f"{RED}[✗]{NC} {msg}", file=sys.stderr)
    sys.exit(1)


def _info(msg):
    print(f"    {msg}")


# ── CLI 入口 ──

def main():
    parser = argparse.ArgumentParser(
        prog="axon-skills",
        description="Axon 技能包管理器",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="从 GitHub 安装技能")
    p_add.add_argument("url", help="GitHub 仓库 URL")
    p_add.add_argument(
        "--skill", "-s", default=None,
        help="指定安装的技能名（模糊匹配文件名）",
    )
    p_add.add_argument(
        "--force", "-f", action="store_true",
        help="覆盖已存在的同名技能",
    )

    # list
    sub.add_parser("list", help="列出已安装技能")

    # remove
    p_rm = sub.add_parser("remove", help="移除技能")
    p_rm.add_argument("name", help="技能文件名")

    # info
    p_info = sub.add_parser("info", help="查看技能详情")
    p_info.add_argument("name", help="技能文件名")

    args = parser.parse_args()
    dispatch = {
        "add": cmd_add,
        "list": cmd_list,
        "remove": cmd_remove,
        "info": cmd_info,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
