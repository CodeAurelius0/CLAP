/**
 * TopBar — Application header with CLAP branding, backend status,
 * and GitHub connection indicator.
 */
import { useState, useRef, useEffect } from 'react';
import Modal from './Modal.jsx';

export default function TopBar({ connected, github }) {
  const [showPanel, setShowPanel] = useState(false);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const panelRef = useRef(null);

  // Close panel on click outside
  useEffect(() => {
    if (!showPanel) return;
    const handleClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setShowPanel(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showPanel]);

  const handleDisconnect = async () => {
    await github?.disconnect();
    setShowDisconnectConfirm(false);
    setShowPanel(false);
  };

  const handleReconnect = () => {
    setShowPanel(false);
    github?.disconnect().then(() => {
      // After disconnect, the app will show ConnectGitHubPage
    });
  };

  return (
    <>
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
          {/* Backend status */}
          <div className="topbar-status">
            <span className="status-dot" style={{
              background: connected ? 'var(--success-fg)' : 'var(--danger-fg)',
            }} />
            <span>{connected ? 'Backend connected' : 'Disconnected'}</span>
          </div>

          {/* GitHub connection indicator */}
          {github && (
            <div className="topbar-github" ref={panelRef}>
              <button
                className="topbar-github-btn"
                onClick={() => setShowPanel(!showPanel)}
                id="topbar-github-indicator"
              >
                <span
                  className="topbar-github-dot"
                  style={{
                    background: github.authenticated
                      ? 'var(--success-fg)'
                      : 'var(--text-tertiary)',
                  }}
                />
                {github.authenticated ? (
                  <span className="topbar-github-label">
                    <span className="topbar-github-provider">GitHub</span>
                    <span className="topbar-github-user">@{github.user?.login}</span>
                  </span>
                ) : (
                  <span className="topbar-github-label">
                    <span className="topbar-github-provider">GitHub</span>
                    <span className="topbar-github-connect">Connect</span>
                  </span>
                )}
              </button>

              {showPanel && github.authenticated && (
                <div className="topbar-github-panel">
                  <div className="topbar-github-panel-header">
                    <span className="topbar-github-panel-title">GitHub</span>
                  </div>
                  <div className="topbar-github-panel-body">
                    <div className="topbar-github-panel-status">
                      <span style={{ color: 'var(--success-fg)' }}>✓</span>
                      Connected as <strong>@{github.user?.login}</strong>
                    </div>
                    {github.user?.html_url && (
                      <a
                        href={github.user.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="topbar-github-panel-link"
                      >
                        GitHub.com
                      </a>
                    )}
                  </div>
                  <div className="topbar-github-panel-actions">
                    <button
                      className="btn btn-ghost btn-sm w-full"
                      onClick={handleReconnect}
                      id="reconnect-github"
                    >
                      Reconnect
                    </button>
                    <button
                      className="btn btn-danger btn-sm w-full"
                      onClick={() => setShowDisconnectConfirm(true)}
                      id="disconnect-github"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Disconnect confirmation modal */}
      {showDisconnectConfirm && (
        <Modal
          title="Disconnect GitHub?"
          onClose={() => setShowDisconnectConfirm(false)}
          actions={
            <>
              <button
                className="btn btn-secondary"
                onClick={() => setShowDisconnectConfirm(false)}
                id="cancel-disconnect"
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleDisconnect}
                id="confirm-disconnect"
              >
                Disconnect
              </button>
            </>
          }
        >
          <p className="text-muted">
            CLAP will remove its local authentication credentials from this machine.
          </p>
          <p className="text-muted mt-sm">
            Your GitHub repositories will not be deleted.
          </p>
        </Modal>
      )}
    </>
  );
}
