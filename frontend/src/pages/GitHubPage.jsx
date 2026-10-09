/**
 * GitHubPage — GitHub repository creation and push.
 *
 * Full workflow: Authenticated → Create Repo → Push → Success
 *
 * Authentication is handled at the app level (ConnectGitHubPage).
 * This page assumes the user is already authenticated.
 */
import { useState, useEffect } from 'react';
import * as api from '../services/api.js';
import { isValidRepoName } from '../utils/helpers.js';

export default function GitHubPage({ project, analysis, github, onNavigate }) {
  const { authenticated, user, disconnect } = github;

  // Repo creation
  const [repoName, setRepoName] = useState('');
  const [repoDesc, setRepoDesc] = useState('');
  const [isPrivate, setIsPrivate] = useState(true);
  const [repoCreated, setRepoCreated] = useState(null);

  // Push
  const [pushSteps, setPushSteps] = useState([]);
  const [pushing, setPushing] = useState(false);
  const [pushComplete, setPushComplete] = useState(false);
  const [pushError, setPushError] = useState(null);
  const [repoUrl, setRepoUrl] = useState('');

  // Pre-fill repo name from project
  useEffect(() => {
    if (project && !repoName) {
      setRepoName(project.name);
    }
  }, [project, repoName]);

  // --- Create repo and push ---
  const handleLaunch = async () => {
    if (!project || !authenticated) return;
    if (!repoName.trim() || !isValidRepoName(repoName)) {
      setPushError('Invalid repository name. Use only letters, numbers, hyphens, underscores, and dots.');
      return;
    }

    setPushing(true);
    setPushError(null);
    setPushSteps([]);

    const addStep = (label, status) => {
      setPushSteps((prev) => {
        const existing = prev.findIndex((s) => s.label === label);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = { label, status };
          return updated;
        }
        return [...prev, { label, status }];
      });
    };

    try {
      // 1. Check git status
      addStep('Checking Git repository', 'active');
      const statusRes = await api.getGitStatus(project.path);
      const gitData = statusRes.data;
      addStep('Checking Git repository', 'done');

      // 2. Init if needed
      if (!gitData.is_repo) {
        addStep('Initializing Git', 'active');
        await api.initGit(project.path);
        addStep('Initializing Git', 'done');
      }

      // 3. Check if gitignore exists via analysis
      addStep('.gitignore check', 'active');
      addStep('.gitignore check', 'done');

      // 4. Stage files
      addStep('Staging files', 'active');
      await api.stageFiles(project.path);
      addStep('Staging files', 'done');

      // 5. Create commit (only if no commits yet or there are staged changes)
      if (!gitData.has_commits || gitData.uncommitted_changes) {
        addStep('Creating commit', 'active');
        try {
          await api.createCommit(project.path, 'Initial commit');
          addStep('Creating commit', 'done');
        } catch (err) {
          // If "nothing to commit" that's ok
          if (err.message?.includes('nothing to commit') || err.message?.includes('nothing added')) {
            addStep('Creating commit', 'done');
          } else {
            throw err;
          }
        }
      }

      // 6. Create GitHub repository
      addStep('Creating GitHub repository', 'active');
      const repoRes = await api.createRepository(repoName, repoDesc, isPrivate);
      setRepoCreated(repoRes.data);
      addStep('Creating GitHub repository', 'done');

      // 7. Add remote
      addStep('Configuring remote', 'active');
      await api.addRemote(project.path, repoRes.data.clone_url);
      addStep('Configuring remote', 'done');

      // 8. Push
      addStep('Pushing to main', 'active');
      await api.pushToRemote(project.path);
      addStep('Pushing to main', 'done');

      setRepoUrl(repoRes.data.html_url);
      setPushComplete(true);
    } catch (err) {
      setPushError(err.message);
      // Mark any active step as error
      setPushSteps((prev) => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s));
    } finally {
      setPushing(false);
    }
  };

  // --- No project ---
  if (!project) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">↗</div>
          <h1 className="empty-state-title">No project selected</h1>
          <p className="empty-state-description">Select and prepare a project first.</p>
        </div>
      </div>
    );
  }

  // --- Success screen ---
  if (pushComplete && repoUrl) {
    return (
      <div className="page">
        <div className="success-screen">
          <div className="success-icon">🚀</div>
          <h1 className="success-title">Project launched successfully</h1>
          <a
            className="success-url"
            href={repoUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            {repoUrl.replace('https://', '')}
          </a>
          <div className="success-actions">
            <a
              href={repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary btn-lg"
            >
              Open Repository
            </a>
            <button className="btn btn-secondary btn-lg" onClick={() => onNavigate('overview')}>
              Back to Overview
            </button>
          </div>
        </div>

        {/* Steps recap */}
        <div className="card mt-lg">
          <div className="progress-steps">
            {pushSteps.map((step, i) => (
              <div key={i} className={`progress-step ${step.status}`}>
                <span className="progress-step-icon">
                  {step.status === 'done' ? '✓' : step.status === 'error' ? '✕' : '○'}
                </span>
                {step.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">GitHub</h1>
        <p className="page-description">Create a repository and push your project.</p>
      </div>

      {/* Auth status indicator */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-md">
            {user?.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.login}
                style={{ width: 32, height: 32, borderRadius: '50%' }}
              />
            )}
            <div>
              <div style={{ color: 'var(--success-fg)', fontWeight: 500 }}>
                ✓ Connected as @{user?.login}
              </div>
              {user?.name && <div className="text-sm text-muted">{user.name}</div>}
            </div>
          </div>
        </div>
      </div>

      {/* Repo Creation */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 'var(--space-md)' }}>Create Repository</h2>

        <div className="input-group">
          <label className="input-label" htmlFor="repo-name">Repository name</label>
          <input
            id="repo-name"
            className="input-field"
            type="text"
            value={repoName}
            onChange={(e) => setRepoName(e.target.value)}
            placeholder="my-project"
          />
          {repoName && !isValidRepoName(repoName) && (
            <div className="input-hint" style={{ color: 'var(--danger-fg)' }}>
              Use only letters, numbers, hyphens, underscores, and dots.
            </div>
          )}
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="repo-desc">Description</label>
          <input
            id="repo-desc"
            className="input-field"
            type="text"
            value={repoDesc}
            onChange={(e) => setRepoDesc(e.target.value)}
            placeholder="A short description of your project"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Visibility</label>
          <div className="radio-group">
            <label className="radio-option">
              <input
                type="radio"
                name="visibility"
                checked={!isPrivate}
                onChange={() => setIsPrivate(false)}
              />
              Public
            </label>
            <label className="radio-option">
              <input
                type="radio"
                name="visibility"
                checked={isPrivate}
                onChange={() => setIsPrivate(true)}
              />
              Private
            </label>
          </div>
        </div>

        {pushError && (
          <div className="alert alert-error mb-md">{pushError}</div>
        )}

        {/* Push progress */}
        {pushSteps.length > 0 && (
          <div className="card" style={{ background: 'var(--bg-inset)', marginBottom: 'var(--space-md)' }}>
            <div className="progress-steps">
              {pushSteps.map((step, i) => (
                <div key={i} className={`progress-step ${step.status}`}>
                  <span className="progress-step-icon">
                    {step.status === 'active' ? <span className="spinner" /> :
                     step.status === 'done' ? '✓' :
                     step.status === 'error' ? '✕' : '○'}
                  </span>
                  {step.label}
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          className="btn btn-primary btn-lg"
          onClick={handleLaunch}
          disabled={pushing || !repoName.trim() || !isValidRepoName(repoName)}
          id="create-repo-push"
        >
          {pushing ? (
            <><span className="spinner" /> Launching…</>
          ) : (
            'Create Repository & Push'
          )}
        </button>
      </div>
    </div>
  );
}
