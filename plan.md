# Axon — 设计文档

极简高权限 QQ AI 助理，基于 NoneBot2 + glm-5-turbo。

## 安装

```bash
git clone https://github.com/Xio-Shark/axon.git
cd axon
bash install.sh
```

安装脚本交互式收集以下参数，自动生成 `.env` 并安装依赖。

## 需要填写的参数

| 参数 | 必填 | 获取方式 |
|------|:----:|----------|
| QQ App ID | ✅ | [QQ 开放平台](https://q.qq.com) → 应用管理 → AppID |
| QQ Token | ✅ | 同上 → Token |
| QQ Secret | ✅ | 同上 → AppSecret |
| LLM API Key | ✅ | LLM 服务商后台 |
| LLM Base URL | — | API 端点，安装时可自定义 |
| QQ 用户 ID | — | 你的 QQ 号（接收每日早报，可选） |

## 架构

```
axon/
├── bot.py                  # 启动入口
├── config.py               # 集中配置
├── install.sh              # 一键安装脚本
├── .env                    # 凭据（安装时生成，.gitignore 排除）
├── plugins/
│   ├── chat_handler.py     # 消息路由 + 多轮对话 + 斜杠命令
│   ├── llm_client.py       # LLM + Function Calling + 指数退避重试
│   ├── command_executor.py # 沙箱执行 + 超时 + 审计日志
│   ├── security.py         # HITL 拦截 + 危险命令检测
│   ├── memory.py           # 持久化记忆（时间戳 + 标签 + 增删查）
│   ├── scheduler_tasks.py  # 动态定时任务 + 持久化 + 内置早报
│   └── skill_manager.py    # 技能系统（解析 DESC 注释）
├── data/                   # 运行时数据
└── skills/                 # 自定义技能脚本
```

## 核心特性

### 1. Function Calling
LLM 通过结构化的 tool_calls 决策，而非直接返回裸命令字符串：
- `run_command` — 执行本机 Bash 命令
- `read_file` — 读取本机文件
- `search_web` — 搜索互联网信息

### 2. 多轮对话
- per-user 会话历史，滑动窗口保留最近 20 条
- `/清空` 重置上下文

### 3. 命令沙箱
- `subprocess.run(timeout=30)` 防止挂起
- 固定 `cwd` 到项目目录
- 全部执行记录写入 `data/audit.log`
- 输出超过 1500 字符自动截断

### 4. HITL 安全拦截
扩充危险关键词列表（rm、sudo、chmod、dd、shutdown 等），命中时暂存命令，要求用户回复「同意」才放行。

### 5. 动态定时任务
- 内置每日 8:30 早报任务
- QQ 命令动态注册：`/定时 30 8 * * * 查询天气`
- 持久化到 `data/scheduled_tasks.json`，重启自动恢复

### 6. 技能系统
- `skills/` 目录放置 `.py` 或 `.sh` 脚本
- 首行注释 `# DESC: 描述文本` 自动解析并注入 LLM 上下文

### 7. 持久化记忆
```
/记住 我喜欢用 Vim   → 存入带时间戳的结构化记忆
/记忆列表            → 查看所有记忆
/删除记忆 3          → 删除 #3 记忆
```

## 命令列表

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

## 部署

```bash
# 直接启动
python bot.py

# 后台运行
nohup python bot.py > bot.log 2>&1 &

# systemd 守护（推荐）
sudo cp qq-ai-bot.service /etc/systemd/system/
sudo systemctl enable --now qq-ai-bot
```
