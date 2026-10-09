/**
 * api.js — Central API client for communicating with the CLAP backend.
 *
 * All backend calls go through this module so the base URL
 * is configured in a single place.
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  // FastAPI raises HTTPException with detail containing our error shape
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    // FastAPI wraps HTTPException detail in { detail: { ... } }
    const detail = errorData.detail || errorData;
    const errorMsg =
      detail?.error?.message || detail?.message || `Request failed (${response.status})`;
    throw new Error(errorMsg);
  }

  return response.json();
}

function get(endpoint) {
  return request(endpoint, { method: 'GET' });
}

function post(endpoint, body) {
  return request(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}


/* ----------------------------------------------------------------
   Endpoints
   ---------------------------------------------------------------- */

// Health
export const checkHealth = () => get('/health');

// Project
export const selectProject = (path) => post('/project/select', { path });
export const analyzeProject = (path) => post('/project/analyze', { path });
export const createGitignore = (path, languages, frameworks, mode) =>
  post('/project/gitignore', { path, languages, frameworks, mode });

// Git
export const getGitStatus = (path) => get(`/git/status?path=${encodeURIComponent(path)}`);
export const initGit = (path, branch = 'main') => post('/git/init', { path, branch });
export const stageFiles = (path, files = null) => post('/git/stage', { path, files });
export const getFilesToCommit = (path) => post('/git/files-to-commit', { path });
export const createCommit = (path, message) => post('/git/commit', { path, message });
export const addRemote = (path, url, name = 'origin') => post('/git/remote', { path, url, name });
export const pushToRemote = (path, remote = 'origin', branch = 'main') =>
  post('/git/push', { path, remote, branch });

// Auth — endpoints under /api/auth
export const getAuthStatus = () => get('/auth/status');
export const getAuthUser = () => get('/auth/user');
export const startOAuthFlow = () => get('/auth/github/start?json=true');
export const startDeviceFlow = () => post('/auth/github/start', {});
export const pollDeviceFlow = (deviceCode) =>
  post('/auth/github/poll', { device_code: deviceCode });
export const authWithPAT = (token) => post('/auth/token', { token });
export const authDisconnect = () => post('/auth/disconnect', {});

// GitHub Repo
export const createRepository = (name, description, isPrivate) =>
  post('/github/repository', { name, description, private: isPrivate });
