"""技能系统 — 扫描 skills/ 目录，解析首行 DESC 注释注入 LLM 上下文。"""

import os

from config import SKILLS_DIR

# 约定：技能脚本第一行格式  # DESC: <描述文本>
_DESC_PREFIX = "# DESC:"


def _parse_description(filepath: str) -> str:
    """读取脚本首行的 DESC 注释，没有则返回 '无描述'。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line.startswith(_DESC_PREFIX):
            return first_line[len(_DESC_PREFIX):].strip()
    except Exception:
        pass
    return "无描述"


def list_skills() -> list[dict]:
    """返回 [{name, description, path}] 列表。"""
    os.makedirs(SKILLS_DIR, exist_ok=True)
    skills = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        if not (name.endswith(".py") or name.endswith(".sh")):
            continue
        full_path = os.path.join(SKILLS_DIR, name)
        desc = _parse_description(full_path)
        skills.append({"name": name, "description": desc, "path": full_path})
    return skills


def format_for_prompt() -> str:
    """生成注入 system prompt 的技能清单。"""
    skills = list_skills()
    if not skills:
        return "当前无可用本地技能脚本。"
    lines = [f"- {s['name']}: {s['description']}" for s in skills]
    return "本地可用技能列表：\n" + "\n".join(lines)


def find_skill_command(keyword: str) -> str | None:
    """按关键词模糊匹配技能，返回执行命令或 None。"""
    for s in list_skills():
        if keyword.lower() in s["name"].lower():
            suffix = s["name"].rsplit(".", 1)[-1]
            runner = "python3" if suffix == "py" else "bash"
            return f"{runner} {s['path']}"
    return None
