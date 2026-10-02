/**
 * App.jsx — Root component for CLAP.
 *
 * Manages page routing, project state, and GitHub auth state.
 * Renders the layout: TopBar + Sidebar + Content area.
 */
import { useState, useEffect, useCallback } from 'react';
import TopBar from './components/TopBar.jsx';
import Sidebar from './components/Sidebar.jsx';
import OverviewPage from './pages/OverviewPage.jsx';
import AnalysePage from './pages/AnalysePage.jsx';
import PreparePage from './pages/PreparePage.jsx';
import GitHubPage from './pages/GitHubPage.jsx';
import { useProject } from './hooks/useProject.js';
import { useGitHub } from './hooks/useGitHub.js';
import { checkHealth } from './services/api.js';

export default function App() {
  const [page, setPage] = useState('overview');
  const [backendConnected, setBackendConnected] = useState(false);

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

  // Render current page
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
      <TopBar connected={backendConnected} />
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
    </div>
  );
}
