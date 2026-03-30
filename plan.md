# 极简高权限 QQ AI 助理 (NoneBot2 + LLM God Mode)

通过 Python + NoneBot2 构建拥有本机终端执行权限、定时联网、多轮对话能力的专属 QQ 机器人。
模型固定为 **glm-5-turbo**。

## 一键安装（推荐）

在服务器上执行：

```bash
curl -fsSL <你的托管地址>/install.sh | bash
```

或本地执行：

```bash
bash install.sh
```

安装脚本会交互式询问以下必填信息，自动创建项目、安装依赖、生成配置。

## 需要填写的参数

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| **QQ App ID** | 机器人应用 ID | [QQ 开放平台](https://q.qq.com) → 应用管理 → AppID |
| **QQ Token** | 机器人令牌 | 同上 → Token |
| **QQ Secret** | 机器人密钥 | 同上 → AppSecret |
| **LLM API Key** | 大模型 API 密钥 | 你的 LLM 服务商后台获取 |
| LLM Base URL | API 端点（有默认值） | 默认 `https://your-llm-api.com/v1` |
| QQ 用户 ID | 接收每日早报的用户（可选） | 你自己的 QQ 号 |

## 架构概览

```
~/qq-ai-bot/
├── install.sh              # 一键安装脚本
├── bot.py                  # 启动入口
├── config.py               # 集中配置
├── .env                    # 凭据（安装时自动生成）
├── qq-ai-bot.service       # systemd 守护文件
├── plugins/
│   ├── chat_handler.py     # 消息路由 + 多轮对话
│   ├── llm_client.py       # LLM + Function Calling + 重试
│   ├── command_executor.py # 沙箱执行 + 审计日志
│   ├── security.py         # HITL 拦截
│   ├── memory.py           # 持久记忆
│   ├── scheduler_tasks.py  # 动态定时任务
│   └── skill_manager.py    # 技能系统
├── data/                   # 运行时数据
└── skills/                 # 技能脚本
```

## 手动安装

如果不用一键脚本，手动安装步骤：

### 1. 安装依赖
```bash
pip install nonebot2 nonebot-adapter-qq nonebot-plugin-apscheduler openai
```

### 2. 配置 `.env`
```ini
DRIVER=~fastapi
QQ_IS_SANDBOX=false
QQ_BOTS='[{"id": "<APP_ID>", "token": "<TOKEN>", "secret": "<SECRET>", "intent": {"guild_messages": true, "at_messages": true}}]'
LLM_API_KEY=<你的API密钥>
OWNER_QQ_ID=<你的QQ号>
```

### 3. 启动
```bash
python bot.py
```

### 4. 后台守护（Linux 服务器）
```bash
# 复制 service 文件
sudo cp qq-ai-bot.service /etc/systemd/system/
sudo systemctl enable --now qq-ai-bot
```

## 核心特性

### 1. Function Calling 架构
LLM 不再直接返回裸命令字符串，而是通过结构化的 tool_calls 决策：
- `run_command` — 执行本机 Bash 命令
- `read_file` — 读取本机文件
- `search_web` — 搜索互联网信息

### 2. 多轮对话
- per-user 会话历史，滑动窗口保留最近 20 条
- `/清空` 重置对话上下文

### 3. 命令沙箱
- `subprocess.run(timeout=30)` 替代 `getoutput()`，防止挂起
- 固定 `cwd` 到项目目录
- 全部执行记录写入 `data/audit.log`
- 输出超过 1500 字符自动截断

### 4. HITL 安全拦截
扩充危险关键词列表（rm、sudo、chmod、dd、shutdown 等），命中时暂存命令，要求用户回复「同意」才放行。

### 5. 动态定时任务
- 内置每日 8:30 早报任务
- QQ 命令动态注册：`/定时 30 8 * * * 查询天气`
- 持久化到 `data/scheduled_tasks.json`，重启自动恢复
- `/任务列表` 查看、`/取消任务 <id>` 删除

### 6. 技能系统
- `skills/` 目录下放置 `.py` 或 `.sh` 脚本
- 首行注释 `# DESC: 描述文本` 会被解析并注入 LLM 上下文
- LLM 自动识别并优先调用匹配技能

### 7. 固定模型
模型固定为 `glm-5-turbo`，无需手动切换。

### 8. 持久化记忆
```
/记住 我喜欢用 Vim   → 存入带时间戳的结构化记忆
/记忆列表            → 查看所有记忆
/删除记忆 3          → 删除 #3 记忆
```

## 完整命令列表

| 命令 | 说明 |
|------|------|
| `/记住 <内容>` | 存入长期记忆 |
| `/记忆列表` | 查看所有记忆 |
| `/删除记忆 <id>` | 删除指定记忆 |

| `/技能` | 查看可用技能列表 |
| `/清空` | 清除对话历史 |
| `/定时 <分> <时> <日> <月> <周> <描述>` | 注册定时任务 |
| `/任务列表` | 查看定时任务 |
| `/取消任务 <id>` | 取消定时任务 |
| `同意` | 放行被拦截的高危命令 |
