export default function StatusBar() {
  return (
    <footer className="statusbar">
      <Item label="MODEL" value="glm-5-turbo" />
      <Item label="PID" value="28451" />
      <Item label="MEM" value="128 MB" />
      <Item label="UPTIME" value="72h 14m" />
      <Item label="TASKS" value="4 active" />
      <div style={{ marginLeft: 'auto' }}>
        <Item label="ENGINE" value="NoneBot2 + FastAPI" />
      </div>
    </footer>
  );
}

function Item({ label, value }) {
  return (
    <div className="statusbar-item">
      <span className="label">{label}:</span>
      <span className="value">{value}</span>
    </div>
  );
}
