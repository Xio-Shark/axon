"""持久化记忆管理 — 支持带时间戳的结构化记忆条目。"""

import json
import os
from datetime import datetime

from config import DATA_DIR, MEMORY_FILE


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_all() -> list[dict]:
    """加载全部记忆条目。"""
    _ensure_dir()
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all(entries: list[dict]):
    _ensure_dir()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add(content: str, tag: str = "general") -> dict:
    """新增一条记忆，返回该条目。"""
    entries = load_all()
    entry = {
        "id": len(entries) + 1,
        "content": content,
        "tag": tag,
        "created_at": datetime.now().isoformat(),
    }
    entries.append(entry)
    _save_all(entries)
    return entry


def remove(entry_id: int) -> bool:
    """按 id 删除记忆，成功返回 True。"""
    entries = load_all()
    before = len(entries)
    entries = [e for e in entries if e["id"] != entry_id]
    if len(entries) == before:
        return False
    _save_all(entries)
    return True


def format_for_prompt() -> str:
    """生成注入 system prompt 的记忆摘要。"""
    entries = load_all()
    if not entries:
        return ""
    items = [f"- [{e['tag']}] {e['content']}" for e in entries[-10:]]
    return "以下是长期记忆偏好：\n" + "\n".join(items)
