/**
 * OverviewPage — Dashboard / landing page.
 *
 * Shows a greeting and project selector. If a project is selected,
 * shows basic project info and a button to navigate to analysis.
 */
import { useState } from 'react';
import { getGreeting, shortenPath } from '../utils/helpers.js';

export default function OverviewPage({
  project,
  analysis,
  onSelectProject,
  onNavigate,
  loading,
  error,
}) {
  const [pathInput, setPathInput] = useState('');
  const [inputError, setInputError] = useState(null);

  const handleSelect = async () => {
    if (!pathInput.trim()) {
      setInputError('Enter a project path');
      return;
    }
    setInputError(null);
    try {
      await onSelectProject(pathInput.trim());
    } catch (err) {
      setInputError(err.message);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSelect();
  };

  // --- No project selected ---
  if (!project) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">📁</div>
          <h1 className="empty-state-title">{getGreeting()}.</h1>
          <p className="empty-state-description">
            Ready to launch a project? Enter the path to your project directory to get started.
          </p>

          <div style={{ width: '100%', maxWidth: 480 }}>
            <div className="input-group">
              <label className="input-label" htmlFor="project-path">Project path</label>
              <input
                id="project-path"
                className="input-field"
                type="text"
                placeholder="C:\Projects\my-app  or  ~/projects/my-app"
                value={pathInput}
                onChange={(e) => setPathInput(e.target.value)}
                onKeyDown={handleKeyDown}
                autoFocus
              />
              <div className="input-hint">
                Enter the full path to the folder containing your source code.
              </div>
            </div>

            {inputError && (
              <div className="alert alert-error" style={{ marginBottom: 'var(--space-md)' }}>
                {inputError}
              </div>
            )}

            <button
              className="btn btn-primary btn-lg w-full"
              onClick={handleSelect}
              disabled={loading}
            >
              {loading ? (
                <><span className="spinner" /> Validating…</>
              ) : (
                'Select Project'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Project selected ---
  const detection = analysis?.detection;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-description">Current project summary</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">{project.name}</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => {
            onSelectProject(null);
            setPathInput('');
          }}>
            Change project
          </button>
        </div>

        <div className="text-muted text-sm text-mono" style={{ marginBottom: 'var(--space-md)' }}>
          {project.path}
        </div>

        {detection && (
          <div className="tag-group">
            {detection.languages?.map((lang) => (
              <span className="tag" key={lang}>{lang}</span>
            ))}
            {detection.frameworks?.map((fw) => (
              <span className="tag" key={fw}>{fw}</span>
            ))}
            {detection.primary && (
              <span className="project-badge">{detection.primary}</span>
            )}
          </div>
        )}

        {!analysis && (
          <div style={{ marginTop: 'var(--space-lg)' }}>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate('analyse')}
            >
              Analyse Project →
            </button>
          </div>
        )}

        {analysis && (
          <div style={{ marginTop: 'var(--space-lg)' }}>
            <div className="hint-block">
              <div className="hint-block-title">GitHub Readiness</div>
              <div className="hint-block-text">
                Score: <strong>{analysis.readiness.score} / {analysis.readiness.max_score}</strong>
                {' — '}
                <button className="btn btn-ghost btn-sm" onClick={() => onNavigate('analyse')}>
                  View details →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}
    </div>
  );
}
