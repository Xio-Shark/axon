"""集中配置管理 — 所有常量与默认值。"""

import os

# ── 项目路径 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

# ── 数据文件 ──
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SCHEDULED_TASKS_FILE = os.path.join(DATA_DIR, "scheduled_tasks.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit.log")

# ── LLM ──
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-5kjaXwucbLWWJ6h1YxV97XJlCmECgw2VhmsxG6DG5TaG1dtG")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://timesniper.club")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "glm-5-turbo")

# ── 机器人主人（接收定时推送的 QQ 用户 ID） ──
OWNER_QQ_ID = os.getenv("OWNER_QQ_ID", "1123646072")

# ── 命令执行 ──
COMMAND_TIMEOUT_SEC = 30
COMMAND_SAFE_CWD = BASE_DIR

# ── 消息 ──
MAX_MESSAGE_LENGTH = 1500
CONVERSATION_WINDOW_SIZE = 20

# ── LLM 重试 ──
LLM_MAX_RETRIES = 3
LLM_BASE_DELAY_SEC = 1.0

# ── 危险关键词（正则或子串均可） ──
DANGER_KEYWORDS = [
    "rm ", "rm -", "sudo ", "wget ", "curl ",
    "apt ", "brew ", "mv ", "yum ", "pip ",
    "chmod ", "chown ", "dd ", "mkfs", "shutdown",
    "reboot", "kill ", "killall ", "> /dev/",
]
