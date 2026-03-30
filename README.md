# ⚡ Axon

> 从 QQ 到服务器的神经通路 — 一条消息，即刻执行。

Axon 是一个极简的高权限 QQ AI 助理，基于 NoneBot2 + glm-5-turbo 构建。它让你通过 QQ 消息远程操控服务器、自动执行定时任务、管理长期记忆，同时内置安全拦截机制防止误操作。

## ✨ 核心能力

- 🧠 **Function Calling** — LLM 通过结构化 tool 调用执行命令，而非直接吐裸字符串
- 💬 **多轮对话** — per-user 滑动窗口，保留最近 20 条上下文
- 🔒 **HITL 安全拦截** — 危险命令自动拦截，回复「同意」才放行
- ⏰ **动态定时任务** — QQ 命令注册 cron 任务，重启不丢失
- 📦 **技能系统** — `skills/` 目录放脚本，自动解析描述注入 LLM 上下文
- 📝 **持久化记忆** — 带时间戳和标签的结构化记忆库
- 🛡️ **命令沙箱** — 超时保护 + 审计日志 + 输出截断

## 🚀 一键安装

```bash
# 远程安装（将 install.sh 托管到 GitHub 等平台后）
curl -fsSL https://your-host.com/install.sh | bash

# 或本地安装
git clone https://github.com/yourname/axon.git
cd axon
bash install.sh
```

安装脚本会交互式询问配置信息，自动完成全部初始化。

## 📋 你需要准备什么

| 参数 | 必填 | 说明 |
|------|:----:|------|
| QQ App ID | ✅ | [QQ 开放平台](https://q.qq.com) → 应用管理 |
| QQ Token | ✅ | 同上 |
| QQ Secret | ✅ | 同上 |
| LLM API Key | ✅ | 你的大模型服务商后台获取 |
| LLM Base URL | — | 默认 `https://your-llm-api.com/v1` |
| 你的 QQ 号 | — | 接收每日早报推送（可选） |

## 📁 项目结构

```
axon/
├── bot.py                  # 启动入口
├── config.py               # 集中配置
├── install.sh              # 一键安装脚本
├── .env                    # 凭据（安装时自动生成）
├── qq-ai-bot.service       # systemd 守护文件
├── plugins/
│   ├── chat_handler.py     # 消息路由 + 多轮对话
│   ├── llm_client.py       # LLM + Function Calling + 重试
│   ├── command_executor.py # 沙箱执行 + 审计日志
│   ├── security.py         # HITL 拦截
│   ├── memory.py           # 持久化记忆
│   ├── scheduler_tasks.py  # 动态定时任务
│   └── skill_manager.py    # 技能系统
├── data/                   # 运行时数据
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

**普通消息** 会直接与 AI 对话，AI 按需调用本机命令或文件读取。

## 🛠️ 添加技能

在 `skills/` 目录下创建 `.py` 或 `.sh` 脚本，首行加上描述注释即可：

```python
# DESC: 查看系统资源占用
import psutil
# ...
```

Axon 会自动发现并告知 LLM 可用技能。

## 🖥️ 部署到服务器

```bash
# 启动
python bot.py

# 后台运行
nohup python bot.py > bot.log 2>&1 &

# systemd 守护（推荐）
sudo cp qq-ai-bot.service /etc/systemd/system/
sudo systemctl enable --now qq-ai-bot
```

## ⚙️ 技术栈

- **框架**: NoneBot2 + QQ 官方适配器
- **模型**: glm-5-turbo（固定）
- **调度**: APScheduler
- **语言**: Python 3.10+

## 📄 License

MIT
