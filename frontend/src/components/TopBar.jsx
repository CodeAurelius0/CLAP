/**
 * TopBar — Application header with CLAP branding and status.
 */
export default function TopBar({ connected }) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <div className="topbar-logo">
          <span className="logo-letter">C</span>
          <span className="logo-letter">L</span>
          <span className="logo-letter">A</span>
          <span className="logo-letter">P</span>
        </div>
        <span className="topbar-subtitle">Code • Launch • Analyse • Push</span>
      </div>
      <div className="topbar-actions">
        <div className="topbar-status">
          <span className="status-dot" style={{
            background: connected ? 'var(--success-fg)' : 'var(--danger-fg)',
          }} />
          <span>{connected ? 'Backend connected' : 'Disconnected'}</span>
        </div>
      </div>
    </header>
  );
}
