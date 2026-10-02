import { useState, useCallback } from 'react';
import * as api from '../services/api.js';

/**
 * useGitHub — Manages GitHub authentication state.
 */
export function useGitHub() {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      const res = await api.getAuthStatus();
      setAuthenticated(res.data.authenticated);
      if (res.data.user) {
        setUser(res.data.user);
      }
      return res.data;
    } catch {
      setAuthenticated(false);
    }
  }, []);

  const loginWithPAT = useCallback(async (token) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.authWithPAT(token);
      setAuthenticated(true);
      setUser(res.data.user);
      return res.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await api.githubLogout();
    setAuthenticated(false);
    setUser(null);
  }, []);

  return {
    authenticated,
    user,
    loading,
    error,
    checkAuth,
    loginWithPAT,
    logout,
    setError,
  };
}
