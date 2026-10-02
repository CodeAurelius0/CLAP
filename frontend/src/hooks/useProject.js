import { useState, useCallback } from 'react';
import * as api from '../services/api.js';

/**
 * useProject — Manages the currently selected project and its analysis.
 */
export function useProject() {
  const [project, setProject] = useState(null);      // { path, name }
  const [analysis, setAnalysis] = useState(null);     // full analysis result
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const selectProject = useCallback(async (path) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const res = await api.selectProject(path);
      setProject(res.data);
      return res.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeProject = useCallback(async () => {
    if (!project) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.analyzeProject(project.path);
      setAnalysis(res.data);
      return res.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [project]);

  const clearProject = useCallback(() => {
    setProject(null);
    setAnalysis(null);
    setError(null);
  }, []);

  return {
    project,
    analysis,
    loading,
    error,
    selectProject,
    analyzeProject,
    clearProject,
    setProject,
    setAnalysis,
    setError,
  };
}
