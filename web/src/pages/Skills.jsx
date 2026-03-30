import { skills } from '../mock/data';

export default function Skills() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📦 技能管理</h1>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.82rem',
          color: 'var(--text-secondary)',
        }}>
          {skills.length} 个已安装
        </span>
      </div>

      <div className="skills-grid">
        {skills.map(s => (
          <div className="skill-card" key={s.name}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div className="skill-name">
                <FileIcon type={s.type} />
                {' '}{s.name}
              </div>
              <span className={`tag ${s.type === 'python' ? 'tag-accent' : 'tag-warning'}`}>
                {s.type === 'python' ? 'PY' : 'SH'}
              </span>
            </div>
            <div className="skill-desc">{s.description}</div>
            <div className="skill-type">
              skills/{s.name}
            </div>
          </div>
        ))}
      </div>

      {/* 安装新技能 */}
      <div style={{ marginTop: 24 }}>
        <div className="section-title">安装新技能</div>
        <div className="data-card">
          <div className="form-row" style={{ marginBottom: 0 }}>
            <div className="form-group">
              <label className="form-label">GitHub 仓库 URL</label>
              <input placeholder="https://github.com/someone/axon-skills-pack" />
            </div>
            <button
              className="btn btn-primary"
              style={{ flexShrink: 0, alignSelf: 'flex-end' }}
            >
              安装
            </button>
          </div>
          <div style={{
            marginTop: 8,
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
          }}>
            python axon-skills.py add &lt;url&gt;
          </div>
        </div>
      </div>
    </div>
  );
}

function FileIcon({ type }) {
  const color = type === 'python' ? 'var(--accent)' : 'var(--warning)';
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      style={{ verticalAlign: 'middle', marginRight: 4 }}
    >
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
      <polyline points="13 2 13 9 20 9" />
    </svg>
  );
}
