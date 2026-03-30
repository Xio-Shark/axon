import { useState } from 'react';
import { memories as initialMemories } from '../mock/data';

export default function Memory() {
  const [items, setItems] = useState(initialMemories);
  const [showForm, setShowForm] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newTag, setNewTag] = useState('general');
  const [filter, setFilter] = useState('');

  const tags = [...new Set(items.map(m => m.tag))];
  const filtered = filter
    ? items.filter(m => m.tag === filter)
    : items;

  function handleAdd() {
    if (!newContent.trim()) return;
    const entry = {
      id: Math.max(0, ...items.map(m => m.id)) + 1,
      content: newContent.trim(),
      tag: newTag,
      created_at: new Date().toISOString(),
    };
    setItems([...items, entry]);
    setNewContent('');
    setNewTag('general');
    setShowForm(false);
  }

  function handleDelete(id) {
    setItems(items.filter(m => m.id !== id));
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">🧠 记忆管理</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + 新增记忆
        </button>
      </div>

      {/* 标签过滤 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <button
          className={`btn btn-sm ${!filter ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('')}
        >
          全部 ({items.length})
        </button>
        {tags.map(t => (
          <button
            key={t}
            className={`btn btn-sm ${filter === t ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilter(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {/* 记忆表格 */}
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 50 }}>ID</th>
            <th>内容</th>
            <th style={{ width: 100 }}>标签</th>
            <th style={{ width: 160 }}>创建时间</th>
            <th style={{ width: 60 }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(m => (
            <tr key={m.id}>
              <td className="mono">#{m.id}</td>
              <td>{m.content}</td>
              <td><span className="tag tag-accent">{m.tag}</span></td>
              <td className="mono">{formatDate(m.created_at)}</td>
              <td>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(m.id)}
                >
                  删除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {filtered.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <div className="empty-state-text">暂无记忆条目</div>
        </div>
      )}

      {/* 新增弹窗 */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">新增记忆</div>
            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">内容</label>
              <textarea
                rows={3}
                value={newContent}
                onChange={e => setNewContent(e.target.value)}
                placeholder="输入要记住的内容..."
                style={{ resize: 'vertical' }}
              />
            </div>
            <div className="form-group">
              <label className="form-label">标签</label>
              <input
                value={newTag}
                onChange={e => setNewTag(e.target.value)}
                placeholder="general"
              />
            </div>
            <div className="modal-actions">
              <button
                className="btn btn-outline"
                onClick={() => setShowForm(false)}
              >
                取消
              </button>
              <button className="btn btn-primary" onClick={handleAdd}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatDate(iso) {
  const d = new Date(iso);
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
