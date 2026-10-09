/**
 * ConnectGitHubPage — First-run screen for GitHub authentication.
 *
 * Implements:
 *   - Primary: OAuth browser authorization flow
 *   - Secondary: Advanced Personal Access Token (PAT)
 *   - Clean first launch design (Section 2)
 *   - Explicit Section 19 error handling (browser_failed, denied, timeout, network, api)
 *   - Section 10 PAT validation states
 */
import { useState } from 'react';

export default function ConnectGitHubPage({ github }) {
  const {
    oauthStatus,
    oauthUrl,
    startOAuth,
    cancelOAuth,
    deviceFlow,
    deviceFlowStatus,
    cancelDeviceFlow,
    loginWithPAT,
    error,
    errorType,
    clearError,
  } = github;

  const [showPAT, setShowPAT] = useState(false);
  const [patInput, setPATInput] = useState('');
  const [patLoading, setPATLoading] = useState(false);
  const [patError, setPatError] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  // --- Handlers ---
  const handleConnect = () => {
    setShowPAT(false);
    setPatError(null);
    clearError();
    startOAuth();
  };

  const handlePATSubmit = async () => {
    if (!patInput.trim()) return;
    setPATLoading(true);
    setPatError(null);
    try {
      await loginWithPAT(patInput.trim());
      setPATInput('');
    } catch (err) {
      setPatError('invalid');
    } finally {
      setPATLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (oauthUrl) {
      navigator.clipboard.writeText(oauthUrl).then(() => {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
      }).catch(() => {});
    }
  };

  const handleCopyCode = () => {
    if (deviceFlow?.user_code) {
      navigator.clipboard.writeText(deviceFlow.user_code).then(() => {
        setCopiedCode(true);
        setTimeout(() => setCopiedCode(false), 2000);
      }).catch(() => {});
    }
  };

  // ==================================================================
  // 1. Device Flow Active (if fallback device flow is triggered)
  // ==================================================================
  if (deviceFlow && deviceFlowStatus === 'polling') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-flow-card">
            <div className="connect-flow-status">
              <span className="spinner" />
              <span>Waiting for authorization…</span>
            </div>

            <p className="connect-flow-instruction">
              Enter this code on GitHub to authorize CLAP:
            </p>

            <div
              className="connect-user-code"
              onClick={handleCopyCode}
              title="Click to copy"
              id="device-user-code"
            >
              {deviceFlow.user_code}
            </div>
            {copiedCode && <span className="connect-copied-hint">Copied to clipboard!</span>}

            <p className="connect-flow-hint">
              A browser window should have opened. If it didn't, open the link below manually.
            </p>

            <button
              className="btn btn-secondary w-full"
              onClick={() => window.open(deviceFlow.verification_uri, '_blank', 'noopener,noreferrer')}
              id="open-verification-link"
            >
              Open GitHub Verification Page
            </button>

            <button
              className="btn btn-ghost btn-sm connect-cancel-btn"
              onClick={cancelDeviceFlow}
              id="cancel-device-flow"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ==================================================================
  // 2. OAuth In Progress (Connecting state sequence - Section 18)
  // ==================================================================
  if (oauthStatus === 'opening' || oauthStatus === 'waiting') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-status-sequence">
              <span className="spinner spinner-lg mb-md" />
              <h2 className="connect-card-title">
                {oauthStatus === 'opening' ? 'Opening browser…' : 'Waiting for authorization…'}
              </h2>
              <p className="connect-card-subtitle">
                {oauthStatus === 'opening'
                  ? 'Connecting to GitHub…'
                  : 'Please review and approve the requested permissions in your browser.'}
              </p>
            </div>

            {oauthUrl && (
              <div className="connect-manual-link-box mt-md">
                <p className="text-sm text-muted mb-sm">Browser didn't open?</p>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => window.open(oauthUrl, '_blank', 'noopener,noreferrer')}
                    id="open-manual-auth-link"
                  >
                    Open Authorization Page
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={handleCopyLink}
                    id="copy-manual-auth-link"
                  >
                    {copiedLink ? 'Copied!' : 'Copy Link'}
                  </button>
                </div>
              </div>
            )}

            <button
              className="btn btn-ghost btn-sm mt-md"
              onClick={cancelOAuth}
              id="cancel-oauth-btn"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ==================================================================
  // 3. Section 19 Explicit Error States
  // ==================================================================

  // Browser couldn't open
  if (errorType === 'browser_failed' && oauthUrl) {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-error-icon">🌐</div>
            <h2 className="connect-card-title">Couldn't open your browser.</h2>
            <p className="connect-card-subtitle">
              Open this URL manually to authorize CLAP:
            </p>

            <div className="connect-actions-vertical mt-md">
              <button
                className="btn btn-primary w-full"
                onClick={() => window.open(oauthUrl, '_blank', 'noopener,noreferrer')}
                id="error-open-auth-page"
              >
                Open Authorization Page
              </button>
              <button
                className="btn btn-secondary w-full"
                onClick={handleCopyLink}
                id="error-copy-auth-link"
              >
                {copiedLink ? '✓ Copied Link' : 'Copy Link'}
              </button>
              <button
                className="btn btn-ghost btn-sm mt-sm"
                onClick={clearError}
                id="error-browser-back"
              >
                ← Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Authorization denied
  if (errorType === 'denied') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-error-icon" style={{ color: 'var(--text-secondary)' }}>✕</div>
            <h2 className="connect-card-title">GitHub authorization was cancelled.</h2>
            <p className="connect-card-subtitle">
              No changes were made to your account.
            </p>

            <div className="mt-lg">
              <button
                className="btn btn-primary w-full"
                onClick={handleConnect}
                id="error-denied-retry"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Timeout
  if (errorType === 'timeout') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-error-icon">⏱</div>
            <h2 className="connect-card-title">GitHub authorization timed out.</h2>
            <p className="connect-card-subtitle">
              The authorization window was open for too long without completing.
            </p>

            <div className="mt-lg">
              <button
                className="btn btn-primary w-full"
                onClick={handleConnect}
                id="error-timeout-retry"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Network unavailable
  if (errorType === 'network_unavailable') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-error-icon">📡</div>
            <h2 className="connect-card-title">Couldn't connect to GitHub.</h2>
            <p className="connect-card-subtitle">
              Check your internet connection and try again.
            </p>

            <div className="mt-lg">
              <button
                className="btn btn-primary w-full"
                onClick={handleConnect}
                id="error-network-retry"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // GitHub API unavailable
  if (errorType === 'api_unavailable') {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card text-center">
            <div className="connect-error-icon">☁</div>
            <h2 className="connect-card-title">GitHub is currently unavailable.</h2>
            <p className="connect-card-subtitle">
              Your local project is safe.
            </p>

            <div className="mt-lg">
              <button
                className="btn btn-primary w-full"
                onClick={handleConnect}
                id="error-api-retry"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Client ID not configured banner/helper
  const notConfiguredNotice = errorType === 'not_configured' ? (
    <div className="connect-config-notice mb-md">
      <div className="connect-config-title">OAuth Client ID not configured</div>
      <p className="connect-config-desc">
        Set <code>GITHUB_CLIENT_ID</code> in <code>backend/.env</code> to use browser authorization,
        or connect immediately using a Personal Access Token below.
      </p>
      <button
        className="btn btn-secondary btn-sm mt-sm"
        onClick={() => { clearError(); setShowPAT(true); }}
        id="use-pat-instead-btn"
      >
        Use Personal Access Token →
      </button>
    </div>
  ) : null;

  // ==================================================================
  // 4. Advanced: Use Personal Access Token (Section 9 & 10)
  // ==================================================================
  if (showPAT) {
    return (
      <div className="connect-page">
        <div className="connect-container">
          <div className="connect-card">
            <button
              className="btn btn-ghost btn-sm connect-back-btn"
              onClick={() => { setShowPAT(false); setPatError(null); setPATInput(''); clearError(); }}
              id="back-from-pat"
            >
              ← Back
            </button>

            <h2 className="connect-card-title">Use a GitHub Access Token</h2>
            <p className="connect-card-subtitle">
              This option is intended for advanced users.
            </p>

            {/* Section 10 Validation Failure */}
            {(patError === 'invalid' || errorType === 'token_invalid') && (
              <div className="connect-pat-error-card mb-md">
                <div className="connect-pat-error-title">Could not authenticate with this token.</div>
                <div className="connect-pat-error-subtitle">Possible causes:</div>
                <ul className="connect-pat-error-list">
                  <li>• Token is invalid</li>
                  <li>• Token has expired</li>
                  <li>• Required permissions are missing</li>
                </ul>
                <button
                  className="btn btn-secondary btn-sm mt-sm"
                  onClick={() => { setPatError(null); clearError(); }}
                  id="pat-try-again-btn"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Input field */}
            <div className="input-group">
              <label className="input-label" htmlFor="pat-token-input">Token</label>
              <input
                id="pat-token-input"
                className="input-field"
                type="password"
                placeholder="•••••••••••••••••••••••••••••••••••••"
                value={patInput}
                onChange={(e) => { setPATInput(e.target.value); setPatError(null); }}
                onKeyDown={(e) => e.key === 'Enter' && handlePATSubmit()}
                autoFocus
                autoComplete="off"
                spellCheck="false"
              />
            </div>

            <button
              className="btn btn-primary w-full"
              onClick={handlePATSubmit}
              disabled={patLoading || !patInput.trim()}
              id="connect-with-pat"
            >
              {patLoading ? (
                <>
                  <span className="spinner" />
                  Validating GitHub credentials…
                </>
              ) : (
                'Connect'
              )}
            </button>

            <div className="connect-pat-help">
              <span>Don't have a token?</span>
              <a
                href="https://github.com/settings/tokens?type=beta"
                target="_blank"
                rel="noopener noreferrer"
              >
                Create one on GitHub →
              </a>
            </div>

            <div className="connect-pat-warning">
              <span className="connect-pat-warning-icon">⚠</span>
              <span>Never share your token with anyone.</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ==================================================================
  // 5. Main First Launch Screen (Section 2)
  // ==================================================================
  return (
    <div className="connect-page">
      <div className="connect-container">
        {/* Brand */}
        <div className="connect-brand">
          <div className="connect-logo">
            <span className="connect-logo-letter connect-logo-c">C</span>
            <span className="connect-logo-letter connect-logo-l">L</span>
            <span className="connect-logo-letter connect-logo-a">A</span>
            <span className="connect-logo-letter connect-logo-p">P</span>
          </div>
          <div className="connect-tagline">Code • Launch • Analyse • Push</div>
        </div>

        {/* Card */}
        <div className="connect-card">
          <h2 className="connect-card-title">Connect your GitHub account</h2>
          <p className="connect-card-subtitle">
            CLAP uses GitHub to create repositories and
            push your projects directly from your machine.
          </p>

          {notConfiguredNotice}

          {/* Generic error banner if any unhandled error */}
          {error && !notConfiguredNotice && (
            <div className="alert alert-error mb-md">
              <span>{error}</span>
              <button
                className="btn btn-ghost btn-sm"
                onClick={clearError}
                style={{ marginLeft: 'auto', padding: '0 4px' }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Primary Action Button */}
          <button
            className="btn btn-primary btn-lg w-full connect-primary-btn"
            onClick={handleConnect}
            id="connect-github-btn"
          >
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            Connect GitHub
          </button>

          <p className="connect-browser-hint">
            Your browser will open to GitHub.
          </p>

          {/* Advanced / PAT option */}
          <div className="connect-advanced">
            <button
              className="connect-advanced-toggle"
              onClick={() => { clearError(); setShowPAT(true); }}
              id="show-pat-option"
            >
              <span className="connect-advanced-label">Advanced options</span>
              <span className="connect-advanced-sub">Use an access token</span>
            </button>
          </div>

          {/* Privacy note */}
          <div className="connect-privacy">
            <span className="connect-privacy-icon">🔒</span>
            <div>
              <div className="connect-privacy-title">Privacy & Security</div>
              <div className="connect-privacy-text">Your credentials stay protected on this machine.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
