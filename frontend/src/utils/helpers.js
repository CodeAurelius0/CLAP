/**
 * helpers.js — Small utility functions used across the frontend.
 */

/**
 * Get a greeting based on the time of day.
 */
export function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Format bytes as a human-readable string.
 */
export function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 ** 3)).toFixed(1)} GB`;
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 ** 2)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

/**
 * Truncate a path for display, keeping the last N segments.
 */
export function shortenPath(fullPath, segments = 3) {
  if (!fullPath) return '';
  const parts = fullPath.replace(/\\/g, '/').split('/').filter(Boolean);
  if (parts.length <= segments) return fullPath;
  return '~/' + parts.slice(-segments).join('/');
}

/**
 * Validate a GitHub repository name.
 */
export function isValidRepoName(name) {
  return /^[a-zA-Z0-9._-]+$/.test(name);
}
