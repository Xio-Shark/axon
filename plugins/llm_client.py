"""LLM 客户端 — Function Calling + 指数退避重试 + 动态模型切换。"""

import asyncio
import json
import logging

from openai import AsyncOpenAI

from config import (
    DEFAULT_MODEL,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_BASE_DELAY_SEC,
    LLM_MAX_RETRIES,
)

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

# ── per-user 模型设置（默认取 config.DEFAULT_MODEL） ──
_user_models: dict[str, str] = {}


def get_model(user_id: str) -> str:
    return _user_models.get(user_id, DEFAULT_MODEL)


def set_model(user_id: str, model: str):
    _user_models[user_id] = model


def reset_model(user_id: str):
    _user_models.pop(user_id, None)


# ── Function Calling Tools 定义 ──
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "在本机终端执行一条 Bash 命令并返回输出。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 Bash 命令",
                    }
                },
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
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件绝对路径",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "用搜索引擎搜索互联网信息，返回多条摘要结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "抓取指定 URL 的网页内容，自动转为可读文本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要抓取的完整 URL",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_skill",
            "description": (
                "创建一个新技能脚本并安装到 skills/ 目录。"
                "用户描述需求后，生成完整可运行的代码，"
                "首行必须包含 '# DESC: <描述>' 注释。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "技能文件名（不含扩展名）",
                    },
                    "code": {
                        "type": "string",
                        "description": "完整的技能脚本源代码",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "bash"],
                        "description": "脚本语言",
                    },
                },
                "required": ["name", "code", "language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_skill",
            "description": "删除 skills/ 目录中指定的技能脚本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要删除的技能名",
                    }
                },
                "required": ["name"],
            },
        },
    },
]


# ── 核心调用 ──

async def chat(
    messages: list[dict],
    user_id: str = "",
    use_tools: bool = True,
) -> dict:
    """调用 LLM，返回结构化结果。

    返回:
    - 纯文本: {"type": "text", "content": "..."}
    - Tool:   {"type": "tool_call", "name": "...", "arguments": {...}}
    """
    model = get_model(user_id)
    kwargs = {"model": model, "messages": messages}
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
        return {
            "type": "tool_call",
            "name": call.function.name,
            "arguments": args,
        }

    return {"type": "text", "content": msg.content or ""}


async def simple_chat(messages: list[dict], user_id: str = "") -> str:
    """不使用 tools 的简单聊天，返回纯文本。"""
    model = get_model(user_id)
    response = await _call_with_retry(model=model, messages=messages)
    return response.choices[0].message.content or ""


async def _call_with_retry(**kwargs):
    """指数退避重试。"""
    last_err = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            return await _client.chat.completions.create(**kwargs)
        except Exception as e:
            last_err = e
            delay = LLM_BASE_DELAY_SEC * (2 ** attempt)
            logger.warning(
                "LLM 调用失败 (第 %d 次): %s，%0.1fs 后重试",
                attempt + 1, e, delay,
            )
            await asyncio.sleep(delay)
    raise RuntimeError(f"LLM 调用连续失败 {LLM_MAX_RETRIES} 次: {last_err}")
