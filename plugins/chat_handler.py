"""消息路由 — 命令分发 + 多轮对话 + Function Calling 循环执行。"""

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
    web_search,
)

logger = logging.getLogger(__name__)

# ── per-user 对话历史（滑动窗口） ──
_conversations: dict[str, list[dict]] = {}

# tool-call 循环最大轮次
_MAX_TOOL_ROUNDS = 5


def _get_history(user_id: str) -> list[dict]:
    return _conversations.setdefault(user_id, [])


def _append_history(user_id: str, role: str, content: str):
    history = _get_history(user_id)
    history.append({"role": role, "content": content})
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

    # HITL 放行
    if user_msg == "同意" and security.has_pending(user_id):
        cmd = security.pop_pending(user_id)
        result = command_executor.execute(cmd, user_id=user_id)
        await god_mode.finish(f"✅ 放行操作执行完毕：\n{result}")

    # 斜杠命令
    reply = _handle_slash_command(user_msg, user_id)
    if reply is not None:
        await god_mode.finish(reply)

    # LLM 主流程
    await _handle_llm_flow(user_msg, user_id)


# ── 斜杠命令 ──

def _handle_slash_command(msg: str, user_id: str) -> str | None:
    if msg == "/help":
        return (
            "📖 Axon 命令列表：\n"
            "/模型 <名称> — 切换 LLM 模型\n"
            "/模型 — 查看当前模型\n"
            "/记住 <内容> — 存入长期记忆\n"
            "/记忆列表 — 查看所有记忆\n"
            "/删除记忆 <id> — 删除指定记忆\n"
            "/技能 — 查看可用技能\n"
            "/清空 — 清除对话历史\n"
            "/定时 <分> <时> <日> <月> <周> <描述> — 注册定时任务\n"
            "/任务列表 — 查看定时任务\n"
            "/取消任务 <id> — 取消定时任务\n"
            "同意 — 放行被拦截的高危命令"
        )

    if msg.startswith("/模型"):
        model_name = msg[len("/模型"):].strip()
        if not model_name:
            current = llm_client.get_model(user_id)
            return f"🤖 当前模型: {current}"
        llm_client.set_model(user_id, model_name)
        return f"✅ 模型已切换为: {model_name}"

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

    return None


def _handle_schedule_command(msg: str, user_id: str) -> str:
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


# ── LLM 主流程（tool-call 循环） ──

async def _handle_llm_flow(user_msg: str, user_id: str):
    """多轮对话 + Function Calling 循环。

    LLM 调用 tool → 执行 → 结果回填 → LLM 再决策，
    循环至 LLM 返回纯文本或达到最大轮次。
    """
    _append_history(user_id, "user", user_msg)

    mem_prompt = memory.format_for_prompt()
    skill_prompt = skill_manager.format_for_prompt()
    sys_prompt = (
        "你是 Axon，专属个人 AI 助理。你可以通过 tool 在本机执行命令、"
        "读取文件、搜索互联网或抓取网页内容。\n"
        "可以连续调用多个 tool 完成复杂任务（如先搜索再抓取详情）。\n"
        "优先使用对话回复；需要最新信息或操作本机时才调用 tool。\n"
        "【安全准则】：绝不可修改系统核心文件配置。\n"
    )
    if mem_prompt:
        sys_prompt += f"\n{mem_prompt}\n"
    if skill_prompt:
        sys_prompt += f"\n{skill_prompt}\n"

    messages = [
        {"role": "system", "content": sys_prompt},
    ] + _get_history(user_id)

    for _ in range(_MAX_TOOL_ROUNDS):
        try:
            result = await llm_client.chat(messages, user_id=user_id)
        except Exception as e:
            logger.error("LLM 调用失败: %s", e)
            await god_mode.finish(f"❌ AI 服务暂时不可用: {e}")
            return

        # 纯文本 → 最终回复
        if result["type"] == "text":
            reply = result["content"]
            _append_history(user_id, "assistant", reply)
            await god_mode.finish(_truncate_reply(reply))
            return

        # Tool Call → 执行
        tool_name = result["name"]
        tool_args = result["arguments"]
        tool_output = await _dispatch_tool(tool_name, tool_args, user_id)

        # HITL 拦截时已 finish，直接退出
        if tool_output is None:
            return

        # 回填结果供 LLM 下一轮决策
        messages.append({
            "role": "assistant",
            "content": f"[调用 {tool_name}({tool_args})]",
        })
        messages.append({
            "role": "user",
            "content": f"[tool 结果]\n{tool_output}",
        })

    # 达到最大轮次
    _append_history(user_id, "assistant", "⚠️ 已达到最大工具调用轮次。")
    await god_mode.finish("⚠️ 已执行多轮工具调用，自动停止。请查看以上结果。")


# ── Tool 分发 ──

async def _dispatch_tool(
    name: str, args: dict, user_id: str,
) -> str | None:
    """执行单个 tool，返回输出文本。None = HITL 已拦截。"""
    if name == "run_command":
        cmd = args.get("command", "")
        if security.is_dangerous(cmd):
            security.store_pending(user_id, cmd)
            await god_mode.finish(
                f"⚠️ 拦截高危操作！\n{cmd}\n\n回复「同意」放行。"
            )
            return None
        return command_executor.execute(cmd, user_id=user_id)

    if name == "read_file":
        return _safe_read_file(args.get("path", ""))

    if name == "search_web":
        return web_search.search(args.get("query", ""))

    if name == "fetch_url":
        return web_search.fetch_url(args.get("url", ""))

    if name == "create_skill":
        return skill_manager.create_skill(
            name=args.get("name", "unnamed"),
            code=args.get("code", ""),
            language=args.get("language", "python"),
        )

    if name == "remove_skill":
        return skill_manager.remove_skill(args.get("name", ""))

    return f"❌ 未知 tool: {name}"


# ── 安全文件读取 ──
_BLOCKED_PATHS = ("/etc/shadow", "/etc/passwd", "/proc", "/sys")


def _safe_read_file(path: str) -> str:
    if any(path.startswith(p) for p in _BLOCKED_PATHS):
        return f"🚫 安全策略拒绝读取: {path}"
    try:
        if not os.path.isfile(path):
            return f"❌ 文件不存在: {path}"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return _truncate_reply(f"📄 {path}:\n\n{content}")
    except Exception as e:
        return f"❌ 读取失败: {e}"


def _truncate_reply(text: str) -> str:
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH] + f"\n\n[已截断，共 {len(text)} 字符]"
