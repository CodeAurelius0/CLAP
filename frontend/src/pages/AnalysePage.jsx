/**
 * AnalysePage — Project analysis results.
 *
 * Runs analysis on the selected project and displays:
 * - readiness score
 * - check results (git, readme, gitignore, large files, secrets)
 * - score breakdown
 * - structure overview
 * - recommended actions
 */
import { useState, useEffect } from 'react';
import ScoreRing from '../components/ScoreRing.jsx';
import CheckItem from '../components/CheckItem.jsx';
import Modal from '../components/Modal.jsx';
import * as api from '../services/api.js';

export default function AnalysePage({ project, analysis, onAnalyze, loading, onNavigate }) {
  const [gitignoreModal, setGitignoreModal] = useState(false);
  const [gitignoreMode, setGitignoreMode] = useState('create');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  // Auto-run analysis if not done yet
  useEffect(() => {
    if (project && !analysis && !loading) {
      onAnalyze();
    }
  }, [project, analysis, loading, onAnalyze]);

  if (!project) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">◎</div>
          <h1 className="empty-state-title">No project selected</h1>
          <p className="empty-state-description">
            Select a project from the Overview page first.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="spinner spinner-lg" />
          <p className="mt-md text-muted">Analysing project…</p>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const { readiness, detection, structure, large_files, secrets, has_readme, has_gitignore, git_status, ignorable_dirs, suggested_gitignore, existing_gitignore } = analysis;

  // Build check items
  const checks = [];

  // Git
  checks.push({
    status: git_status.is_repo ? 'pass' : 'warn',
    label: git_status.is_repo ? 'Git repository' : 'Git not initialized',
    detail: git_status.is_repo ? null : 'Initialize Git in the Prepare step',
  });

  // README
  checks.push({
    status: has_readme ? 'pass' : 'warn',
    label: has_readme ? 'README.md' : 'README.md not found',
    detail: has_readme ? null : 'A README helps visitors understand your project',
  });

  // .gitignore
  if (has_gitignore) {
    const ignorableCount = ignorable_dirs?.length || 0;
    if (ignorableCount > 0) {
      checks.push({
        status: 'warn',
        label: '.gitignore exists but may need improvement',
        detail: `${ignorableCount} generated director${ignorableCount === 1 ? 'y' : 'ies'} should be ignored`,
      });
    } else {
      checks.push({ status: 'pass', label: '.gitignore' });
    }
  } else {
    checks.push({
      status: 'warn',
      label: '.gitignore not found',
      detail: 'Generated files and dependencies should be excluded from Git',
    });
  }

  // Large files
  if (large_files.length > 0) {
    checks.push({
      status: large_files.some(f => f.level === 'critical') ? 'fail' : 'warn',
      label: `${large_files.length} large file${large_files.length !== 1 ? 's' : ''} detected`,
      detail: large_files.map(f => `${f.path} (${f.size_display})`).join(', '),
    });
  } else {
    checks.push({ status: 'pass', label: 'No large files' });
  }

  // Secrets
  if (secrets.length > 0) {
    checks.push({
      status: 'warn',
      label: `${secrets.length} possible secret${secrets.length !== 1 ? 's' : ''} detected`,
      detail: secrets.map(s => s.path).join(', '),
    });
  } else {
    checks.push({ status: 'pass', label: 'No obvious secrets' });
  }

  // Structure
  checks.push({
    status: readiness.breakdown.find(b => b.label === 'Recognized project structure')?.passed ? 'pass' : 'info',
    label: 'Project structure',
    detail: `${structure.total_files} files, ${structure.total_dirs} directories, ${structure.source_files} source files`,
  });

  // --- Generate .gitignore handler ---
  const handleCreateGitignore = async () => {
    setActionLoading(true);
    try {
      const mode = has_gitignore ? gitignoreMode : 'create';
      await api.createGitignore(
        project.path,
        detection.languages,
        detection.frameworks,
        mode,
      );
      setActionMsg('✓ .gitignore created successfully');
      setGitignoreModal(false);
      // Re-analyse to update state
      onAnalyze();
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Analyse Project</h1>
        <p className="page-description">
          {project.name}
          <span className="text-mono text-muted" style={{ marginLeft: 8, fontSize: 'var(--text-sm)' }}>
            {project.path}
          </span>
        </p>
      </div>

      {/* Score */}
      <div className="card">
        <ScoreRing score={readiness.score} maxScore={readiness.max_score} />

        <div className="score-breakdown">
          {readiness.breakdown.map((item, i) => (
            <div className="score-breakdown-item" key={i}>
              <div className="score-breakdown-label">
                <span className={`check-icon ${item.passed ? 'pass' : 'warn'}`} style={{ fontSize: 12 }}>
                  {item.passed ? '✓' : '○'}
                </span>
                {item.label}
              </div>
              <span className={`score-breakdown-points ${item.points === 0 ? 'zero' : ''}`}>
                +{item.points}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Checks */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 'var(--space-md)' }}>Checks</h2>
        <div className="check-list">
          {checks.map((c, i) => (
            <CheckItem key={i} status={c.status} label={c.label} detail={c.detail} />
          ))}
        </div>
      </div>

      {/* Actions */}
      {actionMsg && (
        <div className={`alert ${actionMsg.startsWith('✓') ? 'alert-success' : 'alert-error'}`}
             style={{ marginBottom: 'var(--space-md)' }}>
          {actionMsg}
        </div>
      )}

      <div className="flex gap-md" style={{ marginBottom: 'var(--space-md)' }}>
        {!has_gitignore && (
          <button className="btn btn-secondary" onClick={() => setGitignoreModal(true)}>
            Generate .gitignore
          </button>
        )}
        {has_gitignore && ignorable_dirs?.length > 0 && (
          <button className="btn btn-secondary" onClick={() => {
            setGitignoreMode('merge');
            setGitignoreModal(true);
          }}>
            Review .gitignore suggestions
          </button>
        )}
        <button className="btn btn-primary" onClick={() => onNavigate('prepare')}>
          Prepare Project →
        </button>
      </div>

      {/* Structure Details */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 'var(--space-md)' }}>Project Structure</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'max-content 1fr', gap: '4px 24px', fontSize: 'var(--text-sm)' }}>
          <span className="text-muted">Files</span>
          <span className="text-mono">{structure.total_files}</span>
          <span className="text-muted">Directories</span>
          <span className="text-mono">{structure.total_dirs}</span>
          <span className="text-muted">Source files</span>
          <span className="text-mono">{structure.source_files}</span>
          <span className="text-muted">Test files</span>
          <span className="text-mono">{structure.test_files}</span>
          <span className="text-muted">Documentation</span>
          <span className="text-mono">{structure.doc_files}</span>
          <span className="text-muted">Config files</span>
          <span className="text-mono">{structure.config_files}</span>
        </div>

        {structure.notable?.length > 0 && (
          <>
            <div className="divider" />
            <div className="text-sm text-muted mb-md">Detected</div>
            {structure.notable.map((n, i) => (
              <CheckItem key={i} status="pass" label={n.name} detail={n.label} />
            ))}
          </>
        )}
      </div>

      {/* Gitignore Modal */}
      {gitignoreModal && (
        <Modal
          title={has_gitignore ? 'Update .gitignore' : 'Generate .gitignore'}
          onClose={() => setGitignoreModal(false)}
          actions={
            <>
              <button className="btn btn-ghost" onClick={() => setGitignoreModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleCreateGitignore} disabled={actionLoading}>
                {actionLoading ? <><span className="spinner" /> Creating…</> : (
                  has_gitignore ? (gitignoreMode === 'merge' ? 'Merge suggestions' : 'Replace .gitignore') : 'Create .gitignore'
                )}
              </button>
            </>
          }
        >
          {has_gitignore ? (
            <>
              <p className="text-muted mb-md">.gitignore already exists in this project.</p>
              <div className="radio-group mb-md">
                <label className="radio-option">
                  <input type="radio" name="gitignore-mode" value="merge"
                    checked={gitignoreMode === 'merge'} onChange={() => setGitignoreMode('merge')} />
                  Merge with existing
                </label>
                <label className="radio-option">
                  <input type="radio" name="gitignore-mode" value="replace"
                    checked={gitignoreMode === 'replace'} onChange={() => setGitignoreMode('replace')} />
                  Replace existing
                </label>
              </div>
            </>
          ) : (
            <p className="text-muted mb-md">
              This will create a .gitignore file tailored for your project
              ({detection.languages?.join(', ') || 'generic'}).
            </p>
          )}

          <div className="hint-block">
            <div className="hint-block-title">Preview</div>
            <pre className="hint-block-text text-mono" style={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
              {suggested_gitignore}
            </pre>
          </div>
        </Modal>
      )}
    </div>
  );
}
