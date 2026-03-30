import { useState } from 'react';
import { scheduledTasks as initialTasks, parseCron } from '../mock/data';

export default function Tasks() {
  const [tasks, setTasks] = useState(initialTasks);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ min: '*', hour: '*', day: '*', month: '*', week: '*', desc: '' });

  function handleCancel(id) {
    setTasks(tasks.filter(t => t.id !== id));
  }

  function handleAdd() {
    if (!form.desc.trim()) return;
    const cron = `${form.min} ${form.hour} ${form.day} ${form.month} ${form.week}`;
    const newTask = {
      id: Math.max(0, ...tasks.map(t => t.id)) + 1,
      cron,
      description: form.desc.trim(),
      owner_id: 'user_001',
      job_id: `dynamic_task_${Date.now()}`,
    };
    setTasks([...tasks, newTask]);
    setForm({ min: '*', hour: '*', day: '*', month: '*', week: '*', desc: '' });
    setShowForm(false);
  }

  function updateField(key, value) {
    setForm({ ...form, [key]: value });
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⏰ 定时任务</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + 新建任务
        </button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 50 }}>ID</th>
            <th style={{ width: 140 }}>Cron</th>
            <th style={{ width: 120 }}>周期</th>
            <th>描述</th>
            <th style={{ width: 80 }}>状态</th>
            <th style={{ width: 60 }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(t => (
            <tr key={t.id}>
              <td className="mono">#{t.id}</td>
              <td className="mono">{t.cron}</td>
              <td>
                <span className="tag tag-accent">{parseCron(t.cron)}</span>
              </td>
              <td>{t.description}</td>
              <td>
                <span className="tag tag-success">运行中</span>
              </td>
              <td>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleCancel(t.id)}
                >
                  取消
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {tasks.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <div className="empty-state-text">暂无定时任务</div>
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">新建定时任务</div>
            <div className="form-row">
              {[
                ['min', '分'],
                ['hour', '时'],
                ['day', '日'],
                ['month', '月'],
                ['week', '周'],
              ].map(([key, label]) => (
                <div className="form-group" key={key} style={{ flex: '0 0 auto', width: 64 }}>
                  <label className="form-label">{label}</label>
                  <input
                    value={form[key]}
                    onChange={e => updateField(key, e.target.value)}
                    style={{ fontFamily: 'var(--font-mono)', textAlign: 'center' }}
                  />
                </div>
              ))}
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">任务描述</label>
              <input
                value={form.desc}
                onChange={e => updateField('desc', e.target.value)}
                placeholder="描述这个定时任务的功能..."
              />
            </div>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setShowForm(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleAdd}>
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
