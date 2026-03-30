# ⚡ Axon

> 从 QQ 到服务器的神经通路 — 一条消息，即刻执行。

Axon 是一个极简的高权限 QQ AI 助理，基于 NoneBot2 + glm-5-turbo 构建。通过 QQ 消息远程操控服务器、自动执行定时任务、管理长期记忆，内置安全拦截机制防止误操作。

## ✨ 核心能力

- 🧠 **Function Calling** — LLM 通过结构化 tool 调用决策，而非直接吐裸命令
- 💬 **多轮对话** — per-user 滑动窗口，保留最近 20 条上下文
- 🔒 **HITL 安全拦截** — 危险命令自动拦截，回复「同意」才放行
- ⏰ **动态定时任务** — QQ 命令注册 cron 任务，持久化，重启不丢
- 📦 **技能系统** — `skills/` 目录放脚本，自动解析描述注入 LLM
- 📝 **持久化记忆** — 带时间戳和标签的结构化记忆库
- 🛡️ **命令沙箱** — 超时保护 + 审计日志 + 输出截断

## 🚀 快速开始

```bash
git clone https://github.com/Xio-Shark/axon.git
cd axon
bash install.sh
```

安装脚本会交互式询问配置信息，自动完成依赖安装和全部初始化。

## 📋 安装前准备

| 参数 | 必填 | 说明 |
|------|:----:|------|
| QQ App ID | ✅ | [QQ 开放平台](https://q.qq.com) → 应用管理 → AppID |
| QQ Token | ✅ | 同上 → Token |
| QQ Secret | ✅ | 同上 → AppSecret |
| LLM API Key | ✅ | 你的大模型服务商后台获取 |
| LLM Base URL | — | API 端点地址，安装时可自定义 |
| 你的 QQ 号 | — | 接收每日早报推送（可选） |

## 📁 项目结构

```
axon/
├── bot.py                  # 启动入口
├── config.py               # 集中配置
├── install.sh              # 一键安装脚本
├── .env                    # 凭据（安装时自动生成，不上传）
├── qq-ai-bot.service       # systemd 守护文件（安装时生成）
├── plugins/
│   ├── chat_handler.py     # 消息路由 + 多轮对话 + 斜杠命令
│   ├── llm_client.py       # LLM + Function Calling + 指数退避重试
│   ├── command_executor.py # 沙箱执行 + 超时 + 审计日志
│   ├── security.py         # HITL 拦截 + 危险命令检测
│   ├── memory.py           # 持久化记忆（带时间戳 + 标签）
│   ├── scheduler_tasks.py  # 动态定时任务 + 内置每日早报
│   └── skill_manager.py    # 技能系统（解析 DESC 注释）
├── data/                   # 运行时数据（记忆、任务、审计日志）
└── skills/                 # 自定义技能脚本
```

## 🎮 命令列表

| 命令 | 说明 |
|------|------|
| `/记住 <内容>` | 存入长期记忆 |
| `/记忆列表` | 查看所有记忆 |
| `/删除记忆 <id>` | 删除指定记忆 |
| `/技能` | 查看可用技能 |
| `/清空` | 清除对话历史 |
| `/定时 <分> <时> <日> <月> <周> <描述>` | 注册定时任务 |
| `/任务列表` | 查看定时任务 |
| `/取消任务 <id>` | 取消定时任务 |
| `同意` | 放行被拦截的高危命令 |

普通消息会直接与 AI 对话，AI 按需调用本机命令或文件读取。

## 🛠️ 添加技能

在 `skills/` 目录下创建 `.py` 或 `.sh` 脚本，首行加上描述注释：

```python
# DESC: 查看系统资源占用
import platform, shutil, os

def main():
    usage = shutil.disk_usage("/")
    print(f"磁盘: {usage.used / (1024**3):.1f}GB / {usage.total / (1024**3):.1f}GB")

if __name__ == "__main__":
    main()
```

Axon 会自动发现并告知 LLM 可用技能。

## 🖥️ 部署

```bash
# 直接启动
python bot.py

# 后台运行
nohup python bot.py > bot.log 2>&1 &

# systemd 守护（推荐，Linux 服务器）
sudo cp qq-ai-bot.service /etc/systemd/system/
sudo systemctl enable --now qq-ai-bot

# 查看日志
sudo journalctl -u qq-ai-bot -f
```

## ⚙️ 技术栈

| 组件 | 技术 |
|------|------|
| 框架 | NoneBot2 + QQ 官方适配器 |
| 模型 | glm-5-turbo（固定） |
| 调度 | APScheduler |
| 语言 | Python 3.10+ |

## 📄 License

MIT
