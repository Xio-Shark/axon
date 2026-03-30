/**
 * Mock 数据 — 模拟真实 Axon 后端数据结构。
 * 后续对接 API 时替换为 fetch 调用。
 */

export const systemStatus = {
  uptime: '72h 14m 38s',
  connection: 'STABLE',
  model: 'glm-5-turbo',
  version: 'v1.0.0',
  pid: 28451,
  startedAt: '2026-03-28T08:30:00',
};

export const memories = [
  { id: 1, content: '用户偏好深色模式和等宽字体', tag: 'preference', created_at: '2026-03-28T10:15:00' },
  { id: 2, content: '服务器 IP: 192.168.1.100，SSH 端口 22', tag: 'server', created_at: '2026-03-28T14:22:00' },
  { id: 3, content: '每周五下午 3 点有团队会议', tag: 'schedule', created_at: '2026-03-29T09:00:00' },
  { id: 4, content: '项目截止日期 2026-04-15', tag: 'deadline', created_at: '2026-03-29T11:30:00' },
  { id: 5, content: 'GitHub 仓库: Xio-Shark/axon', tag: 'project', created_at: '2026-03-30T08:00:00' },
  { id: 6, content: 'Python 3.12 环境已配置完毕', tag: 'env', created_at: '2026-03-30T10:45:00' },
  { id: 7, content: '常用命令: htop, df -h, ss -tlnp', tag: 'cmd', created_at: '2026-03-30T15:20:00' },
];

export const scheduledTasks = [
  { id: 1, cron: '30 8 * * *', description: '每日 AI 科技早报', owner_id: 'user_001', job_id: 'daily_routine_task' },
  { id: 2, cron: '0 12 * * 1-5', description: '工作日午间天气提醒', owner_id: 'user_001', job_id: 'dynamic_task_2' },
  { id: 3, cron: '0 0 * * 0', description: '每周日服务器健康检查', owner_id: 'user_001', job_id: 'dynamic_task_3' },
  { id: 4, cron: '*/30 * * * *', description: '每 30 分钟磁盘空间监控', owner_id: 'user_001', job_id: 'dynamic_task_4' },
];

export const skills = [
  { name: 'system_info.py', description: '查看系统资源占用', type: 'python' },
  { name: 'weather.py', description: '查询今日天气', type: 'python' },
  { name: 'network_check.sh', description: '网络连通性测试', type: 'shell' },
  { name: 'disk_usage.py', description: '磁盘空间详情', type: 'python' },
  { name: 'git_status.sh', description: '检查 Git 仓库状态', type: 'shell' },
  { name: 'port_scan.py', description: '扫描本机开放端口', type: 'python' },
];

export const auditLogs = [
  { time: '21:42:15', level: 'info', message: 'run_command: df -h — 执行成功 (exit 0)' },
  { time: '21:40:58', level: 'info', message: 'read_file: /etc/hostname — 读取完成' },
  { time: '21:40:12', level: 'warn', message: 'run_command: apt update — HITL 安全拦截' },
  { time: '21:38:05', level: 'info', message: 'search_web: "AI 大模型最新动态" — 5 条结果' },
  { time: '21:35:44', level: 'ok', message: 'HITL 放行: apt update — 用户确认执行' },
  { time: '21:33:20', level: 'info', message: 'fetch_url: https://news.ycombinator.com — 抓取完成' },
  { time: '21:30:00', level: 'info', message: '定时任务 #4 磁盘空间监控 — 执行完成' },
  { time: '21:28:11', level: 'error', message: 'run_command: cat /etc/shadow — 安全策略拒绝' },
  { time: '21:25:03', level: 'info', message: 'skill 调用: system_info.py — 输出成功' },
  { time: '21:22:47', level: 'warn', message: 'LLM 调用超时，第 1 次重试 (delay 1.0s)' },
  { time: '21:20:15', level: 'info', message: 'run_command: uptime — 执行成功 (exit 0)' },
  { time: '21:18:30', level: 'ok', message: '记忆 #7 已存入: 常用命令: htop, df -h, ss -tlnp' },
  { time: '21:15:00', level: 'info', message: '对话历史已清空 (user_001)' },
  { time: '21:00:00', level: 'info', message: '定时任务 #4 磁盘空间监控 — 执行完成' },
  { time: '20:45:22', level: 'info', message: 'run_command: python3 --version — Python 3.12.0' },
];

export const settings = {
  llm: {
    model: 'glm-5-turbo',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    maxRetries: 3,
    baseDelay: '1.0s',
  },
  command: {
    timeout: '30s',
    safeCwd: '/root/axon',
  },
  message: {
    maxLength: 1500,
    conversationWindow: 20,
  },
  dangerKeywords: [
    'rm ', 'rm -', 'sudo ', 'wget ', 'curl ',
    'apt ', 'brew ', 'mv ', 'yum ', 'pip ',
    'chmod ', 'chown ', 'dd ', 'mkfs', 'shutdown',
    'reboot', 'kill ', 'killall ', '> /dev/',
  ],
};

/** 模拟 cron 表达式的人类可读解释 */
export function parseCron(expr) {
  const map = {
    '30 8 * * *': '每天 08:30',
    '0 12 * * 1-5': '工作日 12:00',
    '0 0 * * 0': '每周日 00:00',
    '*/30 * * * *': '每 30 分钟',
  };
  return map[expr] || expr;
}
