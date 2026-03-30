import { settings } from '../mock/data';

export default function Settings() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⚙️ 系统设置</h1>
        <span className="tag tag-accent">只读</span>
      </div>

      {/* LLM 配置 */}
      <div className="settings-section">
        <div className="settings-title">LLM 配置</div>
        <SettingRow label="模型" value={settings.llm.model} />
        <SettingRow label="API 地址" value={settings.llm.baseUrl} />
        <SettingRow label="最大重试" value={settings.llm.maxRetries} />
        <SettingRow label="重试基础延迟" value={settings.llm.baseDelay} />
      </div>

      {/* 命令执行 */}
      <div className="settings-section">
        <div className="settings-title">命令执行</div>
        <SettingRow label="超时时间" value={settings.command.timeout} />
        <SettingRow label="安全工作目录" value={settings.command.safeCwd} />
      </div>

      {/* 消息配置 */}
      <div className="settings-section">
        <div className="settings-title">消息配置</div>
        <SettingRow label="最大消息长度" value={settings.message.maxLength} />
        <SettingRow label="对话窗口大小" value={settings.message.conversationWindow} />
      </div>

      {/* 危险关键词 */}
      <div className="settings-section">
        <div className="settings-title">危险关键词拦截列表</div>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
          marginTop: 4,
        }}>
          {settings.dangerKeywords.map((kw, i) => (
            <span key={i} className="tag tag-danger">
              {kw.trim() || '(空格)'}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function SettingRow({ label, value }) {
  return (
    <div className="settings-row">
      <span className="settings-key">{label}</span>
      <span className="settings-value">{String(value)}</span>
    </div>
  );
}
