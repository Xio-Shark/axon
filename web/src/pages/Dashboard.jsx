import DataCard from '../components/DataCard';
import LogViewer from '../components/LogViewer';
import {
  systemStatus,
  memories,
  scheduledTasks,
  skills,
  auditLogs,
} from '../mock/data';

export default function Dashboard() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⚡ 系统总览</h1>
        <span className="tag tag-success">ALL SYSTEMS NOMINAL</span>
      </div>

      {/* 顶部统计卡片 */}
      <div className="dashboard-grid">
        <DataCard
          title="运行时长"
          value={systemStatus.uptime}
          badge="ONLINE"
          accent
        />
        <DataCard
          title="记忆条目"
          value={memories.length}
          sub="持久化存储"
        />
        <DataCard
          title="定时任务"
          value={scheduledTasks.length}
          sub="活跃调度中"
          badge="CRON"
        />
        <DataCard
          title="已装技能"
          value={skills.length}
          sub={`${skills.filter(s => s.type === 'python').length} Python · ${skills.filter(s => s.type === 'shell').length} Shell`}
        />
      </div>

      {/* 系统信息 */}
      <div className="dashboard-section">
        <div className="section-title">系统信息</div>
        <div className="dashboard-grid">
          <DataCard title="模型">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              <InfoRow label="MODEL" value={systemStatus.model} />
              <InfoRow label="PID" value={systemStatus.pid} />
              <InfoRow label="STARTED" value={systemStatus.startedAt} />
              <InfoRow label="VERSION" value={systemStatus.version} />
            </div>
          </DataCard>
          <DataCard title="连接状态">
            <div style={{ marginTop: 12 }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                marginBottom: 12,
              }}>
                <span
                  className="status-dot"
                  style={{ width: 12, height: 12 }}
                />
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  color: 'var(--accent)',
                }}>
                  {systemStatus.connection}
                </span>
              </div>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem',
                color: 'var(--text-secondary)',
              }}>
                QQ 适配器 · NoneBot2
              </div>
            </div>
          </DataCard>
        </div>
      </div>

      {/* 最近审计日志 */}
      <div className="dashboard-section">
        <div className="section-title">最近活动</div>
        <LogViewer logs={auditLogs.slice(0, 8)} maxHeight={280} />
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.82rem',
    }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span style={{
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-primary)',
      }}>
        {value}
      </span>
    </div>
  );
}
