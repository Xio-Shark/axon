#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
#  QQ AI 助理一键安装脚本
#  用法: curl -fsSL <URL>/install.sh | bash
#  或:   bash install.sh
# ═══════════════════════════════════════════════════════════
# 注：安装脚本内嵌所有源码，行数超过 300 行属于部署脚本范畴。

set -euo pipefail

# ── 颜色输出 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
ask()   { echo -en "${CYAN}[?]${NC} $1"; }

# ── 检查前置依赖 ──
command -v python3 >/dev/null 2>&1 || error "未找到 python3，请先安装 Python 3.10+"
command -v pip3 >/dev/null 2>&1    || command -v pip >/dev/null 2>&1 || error "未找到 pip"

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "检测到 Python ${PYTHON_VER}"

# ── 安装目录 ──
INSTALL_DIR="${QQ_BOT_DIR:-$HOME/qq-ai-bot}"

echo ""
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo -e "${CYAN}   QQ AI 助理 — 一键安装${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo ""
echo "安装目录: ${INSTALL_DIR}"
echo ""

# ── 交互式收集配置 ──
ask "QQ 机器人 App ID: "
read -r QQ_APP_ID
[ -z "$QQ_APP_ID" ] && error "App ID 不能为空"

ask "QQ 机器人 Token: "
read -r QQ_TOKEN
[ -z "$QQ_TOKEN" ] && error "Token 不能为空"

ask "QQ 机器人 Secret: "
read -r QQ_SECRET
[ -z "$QQ_SECRET" ] && error "Secret 不能为空"

ask "LLM API Key: "
read -r LLM_API_KEY
[ -z "$LLM_API_KEY" ] && error "LLM API Key 不能为空"

ask "LLM API Base URL [默认: https://your-llm-api.com/v1]: "
read -r LLM_BASE_URL
LLM_BASE_URL="${LLM_BASE_URL:-https://your-llm-api.com/v1}"

ask "你的 QQ 用户 ID（接收每日早报推送，可留空跳过）: "
read -r OWNER_QQ_ID

echo ""
info "开始安装..."

# ── 创建目录 ──
mkdir -p "${INSTALL_DIR}"/{plugins,data,skills}
cd "${INSTALL_DIR}"

# ══════════════════════════════════════
#  写入源码文件
# ══════════════════════════════════════

# ── .env ──
cat > .env << ENVEOF
DRIVER=~fastapi
QQ_IS_SANDBOX=false
QQ_BOTS='[
  {
    "id": "${QQ_APP_ID}",
    "token": "${QQ_TOKEN}",
    "secret": "${QQ_SECRET}",
    "intent": {
      "guild_messages": true,
      "at_messages": true
    }
  }
]'
LLM_API_KEY=${LLM_API_KEY}
LLM_BASE_URL=${LLM_BASE_URL}
OWNER_QQ_ID=${OWNER_QQ_ID}
ENVEOF
info "已生成 .env"

# ── config.py ──
cat > config.py << 'PYEOF'
"""集中配置管理。"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SCHEDULED_TASKS_FILE = os.path.join(DATA_DIR, "scheduled_tasks.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit.log")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://your-llm-api.com/v1")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "glm-5-turbo")

OWNER_QQ_ID = os.getenv("OWNER_QQ_ID", "")

COMMAND_TIMEOUT_SEC = 30
COMMAND_SAFE_CWD = BASE_DIR

MAX_MESSAGE_LENGTH = 1500
CONVERSATION_WINDOW_SIZE = 20

LLM_MAX_RETRIES = 3
LLM_BASE_DELAY_SEC = 1.0

DANGER_KEYWORDS = [
    "rm ", "rm -", "sudo ", "wget ", "curl ",
    "apt ", "brew ", "mv ", "yum ", "pip ",
    "chmod ", "chown ", "dd ", "mkfs", "shutdown",
    "reboot", "kill ", "killall ", "> /dev/",
]
PYEOF
info "已生成 config.py"

# ── bot.py ──
cat > bot.py << 'PYEOF'
"""QQ AI 助理启动入口。"""

import os
import logging

import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter

from config import DATA_DIR, SKILLS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

nonebot.load_plugins("plugins")


@driver.on_startup
async def _on_startup():
    from plugins.scheduler_tasks import restore_tasks
    restore_tasks()
    logging.getLogger(__name__).info("QQ AI 助理启动完成 ✅")


if __name__ == "__main__":
    nonebot.run()
PYEOF
info "已生成 bot.py"

# ── plugins/__init__.py ──
cat > plugins/__init__.py << 'PYEOF'
"""QQ AI 助理插件包。"""
PYEOF

# ── plugins/memory.py ──
cat > plugins/memory.py << 'PYEOF'
"""持久化记忆管理。"""

import json
import os
from datetime import datetime

from config import DATA_DIR, MEMORY_FILE


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_all() -> list[dict]:
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
    entries = load_all()
    before = len(entries)
    entries = [e for e in entries if e["id"] != entry_id]
    if len(entries) == before:
        return False
    _save_all(entries)
    return True


def format_for_prompt() -> str:
    entries = load_all()
    if not entries:
        return ""
    items = [f"- [{e['tag']}] {e['content']}" for e in entries[-10:]]
    return "以下是长期记忆偏好：\n" + "\n".join(items)
PYEOF
info "已生成 plugins/memory.py"

# ── plugins/security.py ──
cat > plugins/security.py << 'PYEOF'
"""安全模块 — HITL 拦截 + 危险命令检测。"""

from config import DANGER_KEYWORDS

_pending_commands: dict[str, str] = {}


def is_dangerous(command: str) -> bool:
    lower = command.lower()
    return any(kw in lower for kw in DANGER_KEYWORDS)


def store_pending(user_id: str, command: str):
    _pending_commands[user_id] = command


def pop_pending(user_id: str) -> str | None:
    return _pending_commands.pop(user_id, None)


def has_pending(user_id: str) -> bool:
    return user_id in _pending_commands
PYEOF
info "已生成 plugins/security.py"

# ── plugins/command_executor.py ──
cat > plugins/command_executor.py << 'PYEOF'
"""命令沙箱执行器。"""

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
    _ensure_log_dir()
    ts = datetime.now().isoformat()
    line = f"[{ts}] user={user_id} cmd={command!r} result_len={len(result)}\n"
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def execute(command: str, user_id: str = "system", timeout: int | None = None) -> str:
    timeout = timeout or COMMAND_TIMEOUT_SEC
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=COMMAND_SAFE_CWD,
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
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH] + f"\n\n[已截断，原文共 {len(text)} 字符]"
PYEOF
info "已生成 plugins/command_executor.py"

# ── plugins/skill_manager.py ──
cat > plugins/skill_manager.py << 'PYEOF'
"""技能系统 — 扫描 skills/ 目录，解析 DESC 注释。"""

import os
from config import SKILLS_DIR

_DESC_PREFIX = "# DESC:"


def _parse_description(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line.startswith(_DESC_PREFIX):
            return first_line[len(_DESC_PREFIX):].strip()
    except Exception:
        pass
    return "无描述"


def list_skills() -> list[dict]:
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
    skills = list_skills()
    if not skills:
        return "当前无可用本地技能脚本。"
    lines = [f"- {s['name']}: {s['description']}" for s in skills]
    return "本地可用技能列表：\n" + "\n".join(lines)


def find_skill_command(keyword: str) -> str | None:
    for s in list_skills():
        if keyword.lower() in s["name"].lower():
            suffix = s["name"].rsplit(".", 1)[-1]
            runner = "python3" if suffix == "py" else "bash"
            return f"{runner} {s['path']}"
    return None
PYEOF
info "已生成 plugins/skill_manager.py"

# ── plugins/llm_client.py ──
cat > plugins/llm_client.py << 'PYEOF'
"""LLM 客户端 — Function Calling + 指数退避重试。模型固定 glm-5-turbo。"""

import asyncio
import json
import logging

from openai import AsyncOpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_BASE_DELAY_SEC, LLM_MAX_RETRIES, MODEL

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "在本机终端执行一条 Bash 命令并返回输出。",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "Bash 命令"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本机指定路径文件的内容。",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件绝对路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "使用搜索引擎检索互联网信息。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
        },
    },
]


async def chat(messages: list[dict], use_tools: bool = True) -> dict:
    kwargs = {"model": MODEL, "messages": messages}
    if use_tools:
        kwargs["tools"] = TOOLS
        kwargs["tool_choice"] = "auto"
    response = await _call_with_retry(**kwargs)
    msg = response.choices[0].message
    if msg.tool_calls:
        call = msg.tool_calls[0]
        try:
            args = json.loads(call.function.arguments)
        except json.JSONDecodeError:
            args = {"raw": call.function.arguments}
        return {"type": "tool_call", "name": call.function.name, "arguments": args}
    return {"type": "text", "content": msg.content or ""}


async def simple_chat(messages: list[dict]) -> str:
    response = await _call_with_retry(model=MODEL, messages=messages)
    return response.choices[0].message.content or ""


async def _call_with_retry(**kwargs):
    last_err = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            return await _client.chat.completions.create(**kwargs)
        except Exception as e:
            last_err = e
            delay = LLM_BASE_DELAY_SEC * (2 ** attempt)
            logger.warning("LLM 调用失败 (第 %d 次): %s，%0.1fs 后重试", attempt + 1, e, delay)
            await asyncio.sleep(delay)
    raise RuntimeError(f"LLM 调用连续失败 {LLM_MAX_RETRIES} 次: {last_err}")
PYEOF
info "已生成 plugins/llm_client.py"

# ── plugins/scheduler_tasks.py ──
cat > plugins/scheduler_tasks.py << 'PYEOF'
"""定时任务管理 — 内置早报 + 动态注册 + 持久化。"""

import json
import logging
import os
import subprocess

from nonebot import get_bot, require
from config import COMMAND_TIMEOUT_SEC, DATA_DIR, OWNER_QQ_ID, SCHEDULED_TASKS_FILE
from plugins import llm_client
from plugins.command_executor import truncate

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

logger = logging.getLogger(__name__)


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


async def _run_dynamic_task(task_desc: str, owner_id: str):
    messages = [
        {
            "role": "system",
            "content": (
                "你是私人助理，执行定时任务。"
                "返回可直接在终端执行的纯 Bash 命令或 Python 代码。"
                "仅限安全的网络请求和数据展现，禁止修改系统配置。"
                "直接返回纯代码，不加 Markdown 包裹。"
            ),
        },
        {"role": "user", "content": task_desc},
    ]
    try:
        code = await llm_client.simple_chat(messages)
        tmp_file = f"/tmp/scheduled_{hash(task_desc) & 0xFFFFFF:06x}.py"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(code)
        proc = subprocess.run(
            f"python3 {tmp_file}", shell=True,
            capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SEC * 2,
        )
        result = (proc.stdout or "") + (proc.stderr or "")
        result = result.strip() or "执行完成，无输出。"
    except Exception as e:
        result = f"定时任务执行失败: {e}"
    result = truncate(result)
    try:
        bot = get_bot()
        await bot.send_msg(user_id=owner_id, message=f"⏰ 定时任务完成：{task_desc}\n\n{result}")
    except Exception as e:
        logger.error("定时任务推送失败: %s", e)


def register_task(cron_expr: str, description: str, owner_id: str) -> dict:
    tasks = _load_tasks()
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError("cron 表达式需要 5 段: 分 时 日 月 周")
    task_id = _next_task_id(tasks)
    job_id = f"dynamic_task_{task_id}"
    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        _run_dynamic_task, "cron",
        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week,
        id=job_id, args=[description, owner_id], replace_existing=True,
    )
    entry = {"id": task_id, "cron": cron_expr, "description": description, "owner_id": owner_id, "job_id": job_id}
    tasks.append(entry)
    _save_tasks(tasks)
    return entry


def cancel_task(task_id: int) -> bool:
    tasks = _load_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        return False
    try:
        scheduler.remove_job(target["job_id"])
    except Exception:
        pass
    tasks = [t for t in tasks if t["id"] != task_id]
    _save_tasks(tasks)
    return True


def list_tasks() -> list[dict]:
    return _load_tasks()


def restore_tasks():
    for task in _load_tasks():
        parts = task["cron"].strip().split()
        if len(parts) != 5:
            continue
        minute, hour, day, month, day_of_week = parts
        scheduler.add_job(
            _run_dynamic_task, "cron",
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week,
            id=task["job_id"], args=[task["description"], task["owner_id"]], replace_existing=True,
        )
    logger.info("已恢复 %d 个持久化定时任务", len(_load_tasks()))


@scheduler.scheduled_job("cron", hour=8, minute=30, id="daily_routine_task")
async def execute_daily_routine():
    task_desc = (
        "请编写一段 Python 代码，搜集今天有关 AI、大模型、科技前沿以及"
        "国内外重大时事热点的简报。代码执行后在终端打印排版良好的结果。"
    )
    if not OWNER_QQ_ID:
        logger.warning("OWNER_QQ_ID 未配置，跳过早报推送")
        return
    await _run_dynamic_task(task_desc, owner_id=OWNER_QQ_ID)
PYEOF
info "已生成 plugins/scheduler_tasks.py"

# ── plugins/chat_handler.py ──
cat > plugins/chat_handler.py << 'PYEOF'
"""消息路由 — 命令分发 + 多轮对话 + Function Calling。"""

import os
import logging

from nonebot import on_message
from nonebot.adapters.qq import Bot, MessageEvent

from config import CONVERSATION_WINDOW_SIZE, MAX_MESSAGE_LENGTH
from plugins import command_executor, llm_client, memory, scheduler_tasks, security, skill_manager

logger = logging.getLogger(__name__)

_conversations: dict[str, list[dict]] = {}


def _get_history(user_id: str) -> list[dict]:
    return _conversations.setdefault(user_id, [])


def _append_history(user_id: str, role: str, content: str):
    history = _get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > CONVERSATION_WINDOW_SIZE:
        _conversations[user_id] = history[-CONVERSATION_WINDOW_SIZE:]


def _clear_history(user_id: str):
    _conversations.pop(user_id, None)


god_mode = on_message(priority=1, block=True)


@god_mode.handle()
async def handle_message(bot: Bot, event: MessageEvent):
    user_msg = event.get_plaintext().strip()
    user_id = event.get_user_id()
    if not user_msg:
        return
    if user_msg == "同意" and security.has_pending(user_id):
        cmd = security.pop_pending(user_id)
        result = command_executor.execute(cmd, user_id=user_id)
        await god_mode.finish(f"✅ 放行操作执行完毕：\n{result}")
    reply = await _handle_slash_command(user_msg, user_id)
    if reply is not None:
        await god_mode.finish(reply)
    await _handle_llm_flow(bot, event, user_msg, user_id)


async def _handle_slash_command(msg: str, user_id: str) -> str | None:
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


async def _handle_llm_flow(bot: Bot, event: MessageEvent, user_msg: str, user_id: str):
    _append_history(user_id, "user", user_msg)
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
    if result["type"] == "text":
        reply = result["content"]
        _append_history(user_id, "assistant", reply)
        await god_mode.finish(_truncate_reply(reply))
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
        reply = f"🔍 搜索功能暂未完整接入，搜索词: {query}"
        _append_history(user_id, "assistant", reply)
        await god_mode.finish(reply)
    else:
        await god_mode.finish(f"❌ 未知 tool: {tool_name}")


async def _execute_command(cmd: str, user_id: str):
    if security.is_dangerous(cmd):
        security.store_pending(user_id, cmd)
        await god_mode.finish(f"⚠️ 拦截高危操作！Agent 试图执行：\n{cmd}\n\n回复「同意」放行。")
    output = command_executor.execute(cmd, user_id=user_id)
    reply = f"> 执行: {cmd}\n\n{output}"
    _append_history(user_id, "assistant", reply)
    await god_mode.finish(_truncate_reply(reply))


async def _read_file(path: str, user_id: str):
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
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH] + f"\n\n[已截断，共 {len(text)} 字符]"
PYEOF
info "已生成 plugins/chat_handler.py"

# ── 示例技能 ──
cat > skills/system_status.py << 'PYEOF'
# DESC: 显示当前系统状态（CPU、内存、磁盘）
import platform, shutil, os

def main():
    print("=" * 40)
    print("  系统状态报告")
    print("=" * 40)
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python:   {platform.python_version()}")
    usage = shutil.disk_usage("/")
    print(f"磁盘: {usage.used / (1024**3):.1f}GB / {usage.total / (1024**3):.1f}GB")
    load = os.getloadavg()
    print(f"负载: {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}")

if __name__ == "__main__":
    main()
PYEOF

# ── 数据文件初始化 ──
echo '[]' > data/memory.json
echo '[]' > data/scheduled_tasks.json

info "所有源码文件已写入完毕"

# ══════════════════════════════════════
#  安装 Python 依赖
# ══════════════════════════════════════
echo ""
info "安装 Python 依赖..."
pip3 install -q nonebot2 nonebot-adapter-qq nonebot-plugin-apscheduler openai 2>&1 | tail -5
info "依赖安装完成"

# ══════════════════════════════════════
#  完成提示
# ══════════════════════════════════════
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ 安装完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "安装位置: ${INSTALL_DIR}"
echo ""
echo "启动命令:"
echo -e "  ${CYAN}cd ${INSTALL_DIR} && python3 bot.py${NC}"
echo ""
echo "后台运行（推荐）:"
echo -e "  ${CYAN}cd ${INSTALL_DIR} && nohup python3 bot.py > bot.log 2>&1 &${NC}"
echo ""
echo "使用 systemd 守护（Linux 服务器）:"
echo -e "  ${CYAN}见下方自动生成的 service 文件${NC}"
echo ""

# ── 生成 systemd service 文件（仅供参考） ──
cat > qq-ai-bot.service << SVCEOF
[Unit]
Description=QQ AI Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${INSTALL_DIR}
ExecStart=$(command -v python3) ${INSTALL_DIR}/bot.py
Restart=on-failure
RestartSec=5
Environment=LLM_API_KEY=${LLM_API_KEY}
Environment=LLM_BASE_URL=${LLM_BASE_URL}
Environment=OWNER_QQ_ID=${OWNER_QQ_ID}

[Install]
WantedBy=multi-user.target
SVCEOF
info "已生成 qq-ai-bot.service（可复制到 /etc/systemd/system/）"
echo ""
echo "完整命令列表:"
echo "  /记住 <内容>     - 存入长期记忆"
echo "  /记忆列表        - 查看记忆"
echo "  /删除记忆 <id>   - 删除记忆"
echo "  /技能            - 查看技能列表"
echo "  /清空            - 清除对话历史"
echo "  /定时 分 时 日 月 周 <描述> - 注册定时任务"
echo "  /任务列表        - 查看定时任务"
echo "  /取消任务 <id>   - 取消定时任务"
echo "  同意             - 放行高危命令"
echo ""
