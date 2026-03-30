"""定时任务管理 — 内置早报 + 动态注册 + 持久化。"""

import json
import logging
import os
import subprocess

from nonebot import get_bot, require

from config import (
    COMMAND_TIMEOUT_SEC,
    DATA_DIR,
    OWNER_QQ_ID,
    SCHEDULED_TASKS_FILE,
)
from plugins import llm_client
from plugins.command_executor import truncate

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

logger = logging.getLogger(__name__)

# ── 持久化读写 ──

def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_tasks() -> list[dict]:
    _ensure_dir()
    if not os.path.exists(SCHEDULED_TASKS_FILE):
        return []
    with open(SCHEDULED_TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_tasks(tasks: list[dict]):
    _ensure_dir()
    with open(SCHEDULED_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def _next_task_id(tasks: list[dict]) -> int:
    return max((t["id"] for t in tasks), default=0) + 1


# ── 动态任务执行器 ──

async def _run_dynamic_task(task_desc: str, owner_id: str):
    """让 LLM 生成代码并执行，结果推送给 owner。"""
    messages = [
        {
            "role": "system",
            "content": (
                "你是私人助理，执行定时任务。"
                "请根据任务描述，返回可直接在终端执行的纯 Bash 命令或 Python 代码。"
                "仅限安全的网络请求和数据展现，禁止修改系统配置。"
                "直接返回纯代码，不加 Markdown 包裹。"
            ),
        },
        {"role": "user", "content": task_desc},
    ]
    try:
        code = await llm_client.simple_chat(messages)
        # 写入临时文件执行
        tmp_file = f"/tmp/scheduled_{hash(task_desc) & 0xFFFFFF:06x}.py"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(code)
        proc = subprocess.run(
            f"python3 {tmp_file}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SEC * 2,
        )
        result = (proc.stdout or "") + (proc.stderr or "")
        result = result.strip() or "执行完成，无输出。"
    except Exception as e:
        result = f"定时任务执行失败: {e}"

    result = truncate(result)
    try:
        bot = get_bot()
        await bot.send_msg(
            user_id=owner_id,
            message=f"⏰ 定时任务完成：{task_desc}\n\n{result}",
        )
    except Exception as e:
        logger.error("定时任务推送失败: %s", e)


# ── 注册 / 取消 ──

def register_task(
    cron_expr: str,
    description: str,
    owner_id: str,
) -> dict:
    """
    注册动态定时任务。

    cron_expr 格式: "分 时 日 月 周" (5 段)
    返回任务条目。
    """
    tasks = _load_tasks()
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError("cron 表达式需要 5 段: 分 时 日 月 周")

    task_id = _next_task_id(tasks)
    job_id = f"dynamic_task_{task_id}"

    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        _run_dynamic_task,
        "cron",
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        id=job_id,
        args=[description, owner_id],
        replace_existing=True,
    )

    entry = {
        "id": task_id,
        "cron": cron_expr,
        "description": description,
        "owner_id": owner_id,
        "job_id": job_id,
    }
    tasks.append(entry)
    _save_tasks(tasks)
    return entry


def cancel_task(task_id: int) -> bool:
    """取消并移除指定定时任务。"""
    tasks = _load_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        return False
    try:
        scheduler.remove_job(target["job_id"])
    except Exception:
        pass  # job 可能已不存在
    tasks = [t for t in tasks if t["id"] != task_id]
    _save_tasks(tasks)
    return True


def list_tasks() -> list[dict]:
    """返回所有注册的动态任务。"""
    return _load_tasks()


def restore_tasks():
    """重启后恢复持久化的动态任务到调度器。"""
    tasks = _load_tasks()
    for task in tasks:
        parts = task["cron"].strip().split()
        if len(parts) != 5:
            continue
        minute, hour, day, month, day_of_week = parts
        scheduler.add_job(
            _run_dynamic_task,
            "cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=task["job_id"],
            args=[task["description"], task["owner_id"]],
            replace_existing=True,
        )
    logger.info("已恢复 %d 个持久化定时任务", len(tasks))


# ── 内置早报任务 ──

@scheduler.scheduled_job("cron", hour=8, minute=30, id="daily_routine_task")
async def execute_daily_routine():
    """每日 8:30 自动生成并执行新闻爬虫。"""
    task_desc = (
        "请编写一段 Python 代码，搜集今天有关 AI、大模型、科技前沿以及"
        "国内外重大时事热点的简报。代码执行后在终端打印排版良好的结果。"
    )
    if not OWNER_QQ_ID:
        logger.warning("OWNER_QQ_ID 未配置，跳过早报推送")
        return
    await _run_dynamic_task(task_desc, owner_id=OWNER_QQ_ID)
