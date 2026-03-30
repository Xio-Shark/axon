"""Axon — QQ AI 助理启动入口。"""

import os
import sys
import logging

import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter

from config import DATA_DIR, LLM_API_KEY, SKILLS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# 启动前校验
if not LLM_API_KEY:
    logging.getLogger(__name__).error("LLM_API_KEY 未配置，请检查 .env 文件")
    sys.exit(1)

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

# 初始化 NoneBot
nonebot.init()

# 注册 QQ 官方适配器
driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

# 加载插件包（自动发现 plugins/ 下的所有模块）
nonebot.load_plugins("plugins")


@driver.on_startup
async def _on_startup():
    """启动后恢复持久化定时任务。"""
    from plugins.scheduler_tasks import restore_tasks
    restore_tasks()
    logging.getLogger(__name__).info("QQ AI 助理启动完成 ✅")


if __name__ == "__main__":
    nonebot.run()
