/**
 * App.jsx — Root component for CLAP.
 *
 * First-run flow:
 *   1. Check GitHub auth status
 *   2. If not authenticated → show ConnectGitHubPage
 *   3. If just authenticated → show GitHubConnectedPage briefly
 *   4. If authenticated → show main app (sidebar + pages)
 *
 * Returning users skip straight to step 4.
 */
import { useState, useEffect, useCallback } from 'react';
import TopBar from './components/TopBar.jsx';
import Sidebar from './components/Sidebar.jsx';
import Modal from './components/Modal.jsx';
import OverviewPage from './pages/OverviewPage.jsx';
import AnalysePage from './pages/AnalysePage.jsx';
import PreparePage from './pages/PreparePage.jsx';
import GitHubPage from './pages/GitHubPage.jsx';
import ConnectGitHubPage from './pages/ConnectGitHubPage.jsx';
import GitHubConnectedPage from './pages/GitHubConnectedPage.jsx';
import { useProject } from './hooks/useProject.js';
import { useGitHub } from './hooks/useGitHub.js';
import { checkHealth } from './services/api.js';

export default function App() {
  const [page, setPage] = useState('overview');
  const [backendConnected, setBackendConnected] = useState(false);

  // Track whether the user just connected (for showing the success screen)
  const [justConnected, setJustConnected] = useState(false);
  // Track the previous auth state to detect transitions
  const [prevAuthenticated, setPrevAuthenticated] = useState(null);

  const projectState = useProject();
  const githubState = useGitHub();

  // Health check on mount
  useEffect(() => {
    const check = async () => {
      try {
        await checkHealth();
        setBackendConnected(true);
      } catch {
        setBackendConnected(false);
      }
    };
    check();
    // Periodic check every 30s
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  // Detect when auth transitions from false → true (just connected)
  useEffect(() => {
    if (prevAuthenticated === false && githubState.authenticated === true) {
      setJustConnected(true);
    }
    setPrevAuthenticated(githubState.authenticated);
  }, [githubState.authenticated, prevAuthenticated]);

  const handleContinueAfterConnect = useCallback(() => {
    setJustConnected(false);
  }, []);

  const handleSelectProject = useCallback(async (path) => {
    if (path === null) {
      projectState.clearProject();
      setPage('overview');
      return;
    }
    const result = await projectState.selectProject(path);
    return result;
  }, [projectState]);

  const navigate = useCallback((pageId) => {
    setPage(pageId);
  }, []);

  // --- Loading state ---
  if (githubState.loading && !githubState.authenticated) {
    return (
      <div className="app-layout">
        <TopBar connected={backendConnected} />
        <div className="app-body">
          <div className="main-content" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <div style={{ textAlign: 'center' }}>
              <span className="spinner spinner-lg" />
              <div className="text-muted mt-md">Checking connection…</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- Not authenticated: show Connect GitHub page ---
  if (!githubState.authenticated) {
    return (
      <div className="app-layout">
        <TopBar connected={backendConnected} />
        <div className="app-body">
          <main className="main-content">
            <ConnectGitHubPage github={githubState} />
          </main>
        </div>
      </div>
    );
  }

  // --- Just connected: show success screen briefly ---
  if (justConnected) {
    return (
      <div className="app-layout">
        <TopBar connected={backendConnected} github={githubState} />
        <div className="app-body">
          <main className="main-content">
            <GitHubConnectedPage
              user={githubState.user}
              onContinue={handleContinueAfterConnect}
            />
          </main>
        </div>
      </div>
    );
  }

  // --- Authenticated: show main app ---
  const renderPage = () => {
    switch (page) {
      case 'overview':
        return (
          <OverviewPage
            project={projectState.project}
            analysis={projectState.analysis}
            onSelectProject={handleSelectProject}
            onNavigate={navigate}
            loading={projectState.loading}
            error={projectState.error}
          />
        );
      case 'analyse':
        return (
          <AnalysePage
            project={projectState.project}
            analysis={projectState.analysis}
            onAnalyze={projectState.analyzeProject}
            loading={projectState.loading}
            onNavigate={navigate}
          />
        );
      case 'prepare':
        return (
          <PreparePage
            project={projectState.project}
            analysis={projectState.analysis}
            onNavigate={navigate}
            onAnalyze={projectState.analyzeProject}
          />
        );
      case 'github':
        return (
          <GitHubPage
            project={projectState.project}
            analysis={projectState.analysis}
            github={githubState}
            onNavigate={navigate}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      <TopBar connected={backendConnected} github={githubState} />
      <div className="app-body">
        <Sidebar
          activePage={page}
          onNavigate={navigate}
          projectSelected={!!projectState.project}
        />
        <main className="main-content">
          {renderPage()}
        </main>
      </div>

      {/* GitHub connection expired modal (Section 16) */}
      {githubState.expired && (
        <Modal
          title="GitHub connection expired"
          onClose={() => githubState.disconnect()}
          actions={
            <button
              className="btn btn-primary"
              onClick={() => githubState.disconnect()}
              id="reconnect-expired-btn"
            >
              Reconnect GitHub
            </button>
          }
        >
          <p className="text-muted">
            Your GitHub authentication has expired or was revoked. Please reconnect your account to continue.
          </p>
        </Modal>
      )}
    </div>
  );
}
