export default function DataCard({
  title,
  value,
  sub,
  badge,
  accent = false,
  children,
}) {
  return (
    <div className="data-card fade-in">
      <div className="data-card-header">
        <span className="data-card-title">{title}</span>
        {badge && <span className="data-card-badge">{badge}</span>}
      </div>
      {value !== undefined && (
        <div
          className="data-card-value"
          style={accent ? { color: 'var(--accent)' } : undefined}
        >
          {value}
        </div>
      )}
      {sub && <div className="data-card-sub">{sub}</div>}
      {children}
    </div>
  );
}
