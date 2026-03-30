"""命令沙箱执行器 — subprocess.run + 超时 + 审计日志。"""

import os
import subprocess
from datetime import datetime

from config import (
    AUDIT_LOG_FILE,
    COMMAND_SAFE_CWD,
    COMMAND_TIMEOUT_SEC,
    DATA_DIR,
    MAX_MESSAGE_LENGTH,
)


def _ensure_log_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _write_audit(user_id: str, command: str, result: str):
    """审计日志追加写。"""
    _ensure_log_dir()
    ts = datetime.now().isoformat()
    line = f"[{ts}] user={user_id} cmd={command!r} result_len={len(result)}\n"
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def execute(
    command: str,
    user_id: str = "system",
    timeout: int | None = None,
) -> str:
    """
    在沙箱中执行命令，返回截断后的输出。

    - cwd 固定为项目根目录
    - 超时默认 COMMAND_TIMEOUT_SEC
    - 输出超过 MAX_MESSAGE_LENGTH 自动截断
    """
    timeout = timeout or COMMAND_TIMEOUT_SEC
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=COMMAND_SAFE_CWD,
        )
        output = proc.stdout or ""
        if proc.stderr:
            output += f"\n[stderr] {proc.stderr}"
        output = output.strip()
        if not output:
            output = "命令执行成功，无输出。"
    except subprocess.TimeoutExpired:
        output = f"⏱ 命令执行超时（{timeout}s），已强制终止。"
    except Exception as e:
        output = f"命令执行异常: {e}"

    _write_audit(user_id, command, output)
    return truncate(output)


def truncate(text: str) -> str:
    """截断到安全长度。"""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH] + f"\n\n[已截断，原文共 {len(text)} 字符]"
