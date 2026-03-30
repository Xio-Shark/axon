"""安全模块 — HITL 拦截 + 危险命令检测。"""

from config import DANGER_KEYWORDS

# 全局待确认命令队列：{user_id: command_str}
_pending_commands: dict[str, str] = {}


def is_dangerous(command: str) -> bool:
    """检测命令是否命中危险关键词。"""
    lower = command.lower()
    return any(kw in lower for kw in DANGER_KEYWORDS)


def store_pending(user_id: str, command: str):
    """暂存待人类确认的危险命令。"""
    _pending_commands[user_id] = command


def pop_pending(user_id: str) -> str | None:
    """取出并移除用户的待确认命令，不存在返回 None。"""
    return _pending_commands.pop(user_id, None)


def has_pending(user_id: str) -> bool:
    return user_id in _pending_commands
