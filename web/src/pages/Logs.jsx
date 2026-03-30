import LogViewer from '../components/LogViewer';
import { auditLogs } from '../mock/data';

export default function Logs() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📋 审计日志</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <LevelBadge level="info" count={countLevel('info')} />
          <LevelBadge level="warn" count={countLevel('warn')} />
          <LevelBadge level="error" count={countLevel('error')} />
          <LevelBadge level="ok" count={countLevel('ok')} />
        </div>
      </div>

      <div className="data-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <span>$ tail -f /data/audit.log</span>
          <span>{auditLogs.length} entries</span>
        </div>
        <LogViewer logs={auditLogs} maxHeight={600} />
      </div>
    </div>
  );
}

function countLevel(level) {
  return auditLogs.filter(l => l.level === level).length;
}

function LevelBadge({ level, count }) {
  const colorMap = {
    info: 'tag-accent',
    warn: 'tag-warning',
    error: 'tag-danger',
    ok: 'tag-success',
  };
  const labelMap = {
    info: 'INFO',
    warn: 'WARN',
    error: 'ERROR',
    ok: 'OK',
  };
  return (
    <span className={`tag ${colorMap[level]}`}>
      {labelMap[level]} {count}
    </span>
  );
}
