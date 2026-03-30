import { useState, useEffect } from 'react';

export default function TopBar() {
  const [time, setTime] = useState(formatTime());

  useEffect(() => {
    const timer = setInterval(() => setTime(formatTime()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <BoltIcon />
        <span>AXON</span>
        <span className="accent">CONTROL</span>
      </div>
      <div className="topbar-right">
        <span>{time}</span>
        <div className="status-indicator">
          <span className="status-dot" />
          <span>CONNECTED</span>
        </div>
      </div>
    </header>
  );
}

function formatTime() {
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function BoltIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="var(--accent)"
      stroke="none"
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}
