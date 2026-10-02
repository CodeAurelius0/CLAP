/**
 * PreparePage — Prepare the project for pushing to GitHub.
 *
 * Shows exactly what CLAP will do:
 * - Initialize Git (if needed)
 * - Stage files
 * - Create initial commit
 * The user must confirm each action.
 */
import { useState, useEffect } from 'react';
import FileList from '../components/FileList.jsx';
import CheckItem from '../components/CheckItem.jsx';
import * as api from '../services/api.js';

export default function PreparePage({ project, analysis, onNavigate, onAnalyze }) {
  const [gitStatus, setGitStatus] = useState(null);
  const [filesToCommit, setFilesToCommit] = useState([]);
  const [commitMessage, setCommitMessage] = useState('Initial commit');
  const [showFiles, setShowFiles] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stepStatus, setStepStatus] = useState({});
  const [error, setError] = useState(null);
  const [prepared, setPrepared] = useState(false);

  // Load git status and files on mount
  useEffect(() => {
    if (!project) return;
    loadStatus();
  }, [project]);

  const loadStatus = async () => {
    try {
      const statusRes = await api.getGitStatus(project.path);
      setGitStatus(statusRes.data);

      const filesRes = await api.getFilesToCommit(project.path);
      setFilesToCommit(filesRes.data.files);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!project) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">⚙</div>
          <h1 className="empty-state-title">No project selected</h1>
          <p className="empty-state-description">Select and analyse a project first.</p>
        </div>
      </div>
    );
  }

  const needsInit = gitStatus && !gitStatus.is_repo;
  const needsGitignore = analysis && !analysis.has_gitignore;

  // Steps
  const steps = [];
  if (needsInit) steps.push({ id: 'init', label: 'Initialize Git repository' });
  if (needsGitignore) steps.push({ id: 'gitignore', label: 'Create .gitignore' });
  steps.push({ id: 'stage', label: 'Stage project files' });
  steps.push({ id: 'commit', label: 'Create initial commit' });

  const handlePrepare = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Init git if needed
      if (needsInit) {
        setStepStatus(s => ({ ...s, init: 'active' }));
        await api.initGit(project.path);
        setStepStatus(s => ({ ...s, init: 'done' }));
      }

      // 2. Create .gitignore if needed
      if (needsGitignore && analysis) {
        setStepStatus(s => ({ ...s, gitignore: 'active' }));
        await api.createGitignore(
          project.path,
          analysis.detection.languages,
          analysis.detection.frameworks,
          'create',
        );
        setStepStatus(s => ({ ...s, gitignore: 'done' }));
      }

      // 3. Stage files
      setStepStatus(s => ({ ...s, stage: 'active' }));
      await api.stageFiles(project.path);
      setStepStatus(s => ({ ...s, stage: 'done' }));

      // 4. Commit
      setStepStatus(s => ({ ...s, commit: 'active' }));
      await api.createCommit(project.path, commitMessage);
      setStepStatus(s => ({ ...s, commit: 'done' }));

      setPrepared(true);

      // Re-analyse to refresh state
      if (onAnalyze) onAnalyze();
    } catch (err) {
      setError(err.message);
      // Mark the current active step as error
      setStepStatus(s => {
        const updated = { ...s };
        for (const key of Object.keys(updated)) {
          if (updated[key] === 'active') updated[key] = 'error';
        }
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  if (prepared) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Project Prepared</h1>
        </div>

        <div className="card">
          <div className="progress-steps">
            {steps.map((step) => (
              <div key={step.id} className="progress-step done">
                <span className="progress-step-icon">✓</span>
                {step.label}
              </div>
            ))}
          </div>
        </div>

        <div className="hint-block">
          <div className="hint-block-title">What's next?</div>
          <div className="hint-block-text">
            Your project is committed locally. Connect to GitHub to create
            a repository and push your code.
          </div>
        </div>

        <button className="btn btn-primary btn-lg mt-md" onClick={() => onNavigate('github')}>
          Connect GitHub →
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Prepare Project</h1>
        <p className="page-description">Review and confirm the actions below.</p>
      </div>

      {/* Steps preview */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 'var(--space-md)' }}>Actions</h2>
        <div className="progress-steps">
          {steps.map((step) => {
            const status = stepStatus[step.id] || 'pending';
            const icons = { pending: '○', active: '', done: '✓', error: '✕' };
            return (
              <div key={step.id} className={`progress-step ${status}`}>
                <span className="progress-step-icon">
                  {status === 'active' ? <span className="spinner" /> : icons[status]}
                </span>
                {step.label}
              </div>
            );
          })}
        </div>
      </div>

      {/* Files to commit */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Files to be committed: {filesToCommit.length}</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowFiles(!showFiles)}>
            {showFiles ? 'Hide files' : 'Review files'}
          </button>
        </div>
        {showFiles && <FileList files={filesToCommit} />}
      </div>

      {/* Commit message */}
      <div className="card">
        <div className="input-group">
          <label className="input-label" htmlFor="commit-msg">Commit message</label>
          <input
            id="commit-msg"
            className="input-field"
            type="text"
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-error mb-md">{error}</div>
      )}

      <button
        className="btn btn-primary btn-lg"
        onClick={handlePrepare}
        disabled={loading || !commitMessage.trim()}
      >
        {loading ? (
          <><span className="spinner" /> Preparing…</>
        ) : (
          'Prepare Project'
        )}
      </button>
    </div>
  );
}
