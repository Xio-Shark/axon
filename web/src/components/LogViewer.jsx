export default function LogViewer({ logs, maxHeight = 400 }) {
  return (
    <div className="log-viewer" style={{ maxHeight }}>
      {logs.map((log, i) => (
        <div className="log-entry" key={i}>
          <span className="log-time">{log.time}</span>
          <span className={`log-level ${log.level}`}>
            {levelLabel(log.level)}
          </span>
          <span className="log-message">{log.message}</span>
        </div>
      ))}
    </div>
  );
}

function levelLabel(level) {
  const map = { info: 'INFO', warn: 'WARN', error: 'ERR!', ok: ' OK ' };
  return map[level] || level.toUpperCase();
}
