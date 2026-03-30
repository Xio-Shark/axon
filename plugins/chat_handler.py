"""消息路由 — 命令分发 + 多轮对话 + Function Calling 执行。"""

import os
import logging

from nonebot import on_message
from nonebot.adapters.qq import Bot, MessageEvent

from config import CONVERSATION_WINDOW_SIZE, MAX_MESSAGE_LENGTH
from plugins import (
    command_executor,
    llm_client,
    memory,
    scheduler_tasks,
    security,
    skill_manager,
)

logger = logging.getLogger(__name__)

# ── per-user 对话历史（滑动窗口） ──
_conversations: dict[str, list[dict]] = {}


def _get_history(user_id: str) -> list[dict]:
    return _conversations.setdefault(user_id, [])


def _append_history(user_id: str, role: str, content: str):
    history = _get_history(user_id)
    history.append({"role": role, "content": content})
    # 滑动窗口：保留最近 N 条
    if len(history) > CONVERSATION_WINDOW_SIZE:
        _conversations[user_id] = history[-CONVERSATION_WINDOW_SIZE:]


def _clear_history(user_id: str):
    _conversations.pop(user_id, None)


# ── NoneBot 消息入口 ──
god_mode = on_message(priority=1, block=True)


@god_mode.handle()
async def handle_message(bot: Bot, event: MessageEvent):
    user_msg = event.get_plaintext().strip()
    user_id = event.get_user_id()

    if not user_msg:
        return

    # ── 1. HITL 放行 ──
    if user_msg == "同意" and security.has_pending(user_id):
        cmd = security.pop_pending(user_id)
        result = command_executor.execute(cmd, user_id=user_id)
        await god_mode.finish(f"✅ 放行操作执行完毕：\n{result}")

    # ── 2. 斜杠命令路由 ──
    reply = await _handle_slash_command(user_msg, user_id)
    if reply is not None:
        await god_mode.finish(reply)

    # ── 3. LLM Function Calling 主流程 ──
    await _handle_llm_flow(bot, event, user_msg, user_id)


async def _handle_slash_command(msg: str, user_id: str) -> str | None:
    """处理斜杠命令，返回回复文本；非命令返回 None。"""

    if msg.startswith("/记住"):
        content = msg[len("/记住"):].strip()
        if not content:
            return "用法: /记住 <内容>"
        entry = memory.add(content)
        return f"🧠 已存入记忆库 (#{entry['id']})：\n「{content}」"

    if msg.startswith("/删除记忆"):
        try:
            mid = int(msg[len("/删除记忆"):].strip())
        except ValueError:
            return "用法: /删除记忆 <编号>"
        ok = memory.remove(mid)
        return f"✅ 记忆 #{mid} 已删除" if ok else f"❌ 未找到记忆 #{mid}"

    if msg == "/记忆列表":
        entries = memory.load_all()
        if not entries:
            return "📭 记忆库为空"
        lines = [f"#{e['id']} [{e['tag']}] {e['content']}" for e in entries]
        return "🧠 记忆列表：\n" + "\n".join(lines)

    if msg == "/技能":
        return f"🛠 {skill_manager.format_for_prompt()}"

    if msg == "/清空":
        _clear_history(user_id)
        return "🗑 对话记录已清空"

    if msg.startswith("/定时"):
        return _handle_schedule_command(msg, user_id)

    if msg == "/任务列表":
        tasks = scheduler_tasks.list_tasks()
        if not tasks:
            return "📭 无动态定时任务"
        lines = [f"#{t['id']} [{t['cron']}] {t['description']}" for t in tasks]
        return "⏰ 定时任务列表：\n" + "\n".join(lines)

    if msg.startswith("/取消任务"):
        try:
            tid = int(msg[len("/取消任务"):].strip())
        except ValueError:
            return "用法: /取消任务 <编号>"
        ok = scheduler_tasks.cancel_task(tid)
        return f"✅ 任务 #{tid} 已取消" if ok else f"❌ 未找到任务 #{tid}"

    return None  # 不是斜杠命令


def _handle_schedule_command(msg: str, user_id: str) -> str:
    """解析 /定时 <cron5段> <描述>"""
    parts = msg[len("/定时"):].strip().split(maxsplit=5)
    if len(parts) < 6:
        return "用法: /定时 <分> <时> <日> <月> <周> <任务描述>"
    cron_expr = " ".join(parts[:5])
    desc = parts[5]
    try:
        entry = scheduler_tasks.register_task(cron_expr, desc, user_id)
        return f"✅ 定时任务注册成功 (#{entry['id']})：\n[{cron_expr}] {desc}"
    except ValueError as e:
        return f"❌ 注册失败: {e}"


# ── LLM 主流程 ──

async def _handle_llm_flow(
    bot: Bot,
    event: MessageEvent,
    user_msg: str,
    user_id: str,
):
    """多轮对话 + Function Calling 执行循环。"""
    _append_history(user_id, "user", user_msg)

    # 构建 system prompt
    mem_prompt = memory.format_for_prompt()
    skill_prompt = skill_manager.format_for_prompt()
    sys_prompt = (
        "你是专属个人 AI 助理。你可以通过 tool 调用在本机执行命令、读取文件或搜索网络。"
        "优先使用对话回复解答问题；只有用户明确要求操作本机时才调用 tool。\n"
        "【安全准则】：绝不可修改系统核心文件配置。\n"
    )
    if mem_prompt:
        sys_prompt += f"\n{mem_prompt}\n"
    if skill_prompt:
        sys_prompt += f"\n{skill_prompt}\n"

    messages = [{"role": "system", "content": sys_prompt}] + _get_history(user_id)

    try:
        result = await llm_client.chat(messages)
    except Exception as e:
        logger.error("LLM 调用失败: %s", e)
        await god_mode.finish(f"❌ AI 服务暂时不可用: {e}")
        return

    # ── 纯文本回复 ──
    if result["type"] == "text":
        reply = result["content"]
        _append_history(user_id, "assistant", reply)
        await god_mode.finish(_truncate_reply(reply))

    # ── Tool Call 处理 ──
    tool_name = result["name"]
    tool_args = result["arguments"]

    if tool_name == "run_command":
        cmd = tool_args.get("command", "")
        await _execute_command(cmd, user_id)

    elif tool_name == "read_file":
        path = tool_args.get("path", "")
        await _read_file(path, user_id)

    elif tool_name == "search_web":
        query = tool_args.get("query", "")
        # 简化实现：用 curl 搜索
        cmd = f'curl -s "https://google.com/search?q={query}" | head -100'
        reply = f"🔍 搜索功能暂未完整接入，搜索词: {query}"
        _append_history(user_id, "assistant", reply)
        await god_mode.finish(reply)

    else:
        await god_mode.finish(f"❌ 未知 tool: {tool_name}")


async def _execute_command(cmd: str, user_id: str):
    """执行命令，含 HITL 拦截。"""
    if security.is_dangerous(cmd):
        security.store_pending(user_id, cmd)
        await god_mode.finish(
            f"⚠️ 拦截高危操作！Agent 试图执行：\n{cmd}\n\n回复「同意」放行。"
        )

    output = command_executor.execute(cmd, user_id=user_id)
    reply = f"> 执行: {cmd}\n\n{output}"
    _append_history(user_id, "assistant", reply)
    await god_mode.finish(_truncate_reply(reply))


async def _read_file(path: str, user_id: str):
    """读取文件内容。"""
    try:
        if not os.path.isfile(path):
            reply = f"❌ 文件不存在: {path}"
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            reply = f"📄 {path}:\n\n{content}"
    except Exception as e:
        reply = f"❌ 读取失败: {e}"

    _append_history(user_id, "assistant", reply)
    await god_mode.finish(_truncate_reply(reply))


def _truncate_reply(text: str) -> str:
    """消息截断。"""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH] + f"\n\n[已截断，共 {len(text)} 字符]"
