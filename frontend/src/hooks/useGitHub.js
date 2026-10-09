import { useState, useCallback, useEffect, useRef } from 'react';
import * as api from '../services/api.js';

/**
 * useGitHub — Manages GitHub authentication state, OAuth browser flow,
 * Device Flow, PAT validation, and session lifecycle.
 */
export function useGitHub() {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);

  // General error state & type
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);
  // errorType: 'browser_failed' | 'denied' | 'timeout' | 'network_unavailable' | 'api_unavailable' | 'not_configured' | null

  // OAuth Browser Flow state
  const [oauthStatus, setOauthStatus] = useState('idle'); // idle | opening | waiting | complete | error
  const [oauthUrl, setOauthUrl] = useState(null);
  const oauthPollRef = useRef(null);
  const oauthTimeoutRef = useRef(null);

  // Device Flow state (fallback)
  const [deviceFlow, setDeviceFlow] = useState(null);
  const [deviceFlowStatus, setDeviceFlowStatus] = useState('idle'); // idle | polling | complete | error
  const devicePollTimerRef = useRef(null);

  // ------------------------------------------------------------------
  // Check auth on mount & status
  // ------------------------------------------------------------------
  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.getAuthStatus();
      const data = res.data;
      setAuthenticated(data.authenticated);
      if (data.user) {
        setUser(data.user);
        setExpired(false);
      } else {
        setUser(null);
        if (data.expired) {
          setExpired(true);
        }
      }
      return data;
    } catch {
      setAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Check URL parameters for OAuth redirect on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
      window.history.replaceState({}, document.title, window.location.pathname);
      checkAuth();
    } else if (params.get('auth_error') === 'denied') {
      window.history.replaceState({}, document.title, window.location.pathname);
      setErrorType('denied');
      setError('GitHub authorization was cancelled.');
    } else {
      checkAuth();
    }
  }, [checkAuth]);

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (oauthPollRef.current) clearInterval(oauthPollRef.current);
      if (oauthTimeoutRef.current) clearTimeout(oauthTimeoutRef.current);
      if (devicePollTimerRef.current) clearTimeout(devicePollTimerRef.current);
    };
  }, []);

  // Listen for postMessage from OAuth callback popup
  useEffect(() => {
    const handleMessage = async (event) => {
      if (!event.data || typeof event.data !== 'object') return;

      if (event.data.type === 'CLAP_AUTH_SUCCESS') {
        if (oauthPollRef.current) clearInterval(oauthPollRef.current);
        if (oauthTimeoutRef.current) clearTimeout(oauthTimeoutRef.current);
        setOauthStatus('complete');
        setError(null);
        setErrorType(null);
        await checkAuth();
      } else if (event.data.type === 'CLAP_AUTH_ERROR') {
        if (oauthPollRef.current) clearInterval(oauthPollRef.current);
        if (oauthTimeoutRef.current) clearTimeout(oauthTimeoutRef.current);
        setOauthStatus('error');
        if (event.data.errorCode === 'denied') {
          setErrorType('denied');
          setError('GitHub authorization was cancelled.');
        } else {
          setErrorType('api_unavailable');
          setError('GitHub authorization failed.');
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [checkAuth]);

  // ------------------------------------------------------------------
  // Primary OAuth Browser Flow
  // ------------------------------------------------------------------
  const startOAuth = useCallback(async () => {
    setError(null);
    setErrorType(null);
    setOauthStatus('opening');

    try {
      const res = await api.startOAuthFlow();
      const authUrl = res.data?.auth_url;
      if (!authUrl) throw new Error('No authorization URL returned from server.');

      setOauthUrl(authUrl);

      // Attempt to open the authorization window
      const width = 600;
      const height = 750;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      const popup = window.open(
        authUrl,
        'github_oauth_popup',
        `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=yes, copyhistory=no, width=${width}, height=${height}, top=${top}, left=${left}`
      );

      // Check if popup was blocked
      if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        setOauthStatus('idle');
        setErrorType('browser_failed');
        return;
      }

      setOauthStatus('waiting');

      // Set timeout (3 minutes)
      oauthTimeoutRef.current = setTimeout(() => {
        if (oauthPollRef.current) clearInterval(oauthPollRef.current);
        setOauthStatus('error');
        setErrorType('timeout');
        setError('GitHub authorization timed out.');
      }, 180000);

      // Poll auth status while waiting for popup to complete
      oauthPollRef.current = setInterval(async () => {
        try {
          const statusRes = await api.getAuthStatus();
          if (statusRes.data?.authenticated) {
            clearInterval(oauthPollRef.current);
            if (oauthTimeoutRef.current) clearTimeout(oauthTimeoutRef.current);
            setOauthStatus('complete');
            setUser(statusRes.data.user);
            setAuthenticated(true);
            try {
              if (popup && !popup.closed) popup.close();
            } catch {
              // Ignore popup close error
            }
          }
        } catch {
          // Ignore polling errors
        }
      }, 2000);

    } catch (err) {
      setOauthStatus('error');
      const msg = err.message || '';
      if (msg.includes('not configured') || msg.includes('Client ID')) {
        setErrorType('not_configured');
        setError(msg);
      } else if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
        setErrorType('network_unavailable');
        setError("Couldn't connect to GitHub. Check your internet connection.");
      } else {
        setErrorType('api_unavailable');
        setError(msg || 'GitHub is currently unavailable.');
      }
    }
  }, []);

  const cancelOAuth = useCallback(() => {
    if (oauthPollRef.current) clearInterval(oauthPollRef.current);
    if (oauthTimeoutRef.current) clearTimeout(oauthTimeoutRef.current);
    setOauthStatus('idle');
    setError(null);
    setErrorType(null);
  }, []);

  // ------------------------------------------------------------------
  // Device Flow (Fallback)
  // ------------------------------------------------------------------
  const startDeviceAuth = useCallback(async () => {
    setError(null);
    setErrorType(null);
    setDeviceFlowStatus('idle');
    try {
      const res = await api.startDeviceFlow();
      const data = res.data;
      setDeviceFlow(data);
      setDeviceFlowStatus('polling');

      const interval = (data.interval || 5) * 1000;
      const deviceCode = data.device_code;

      const poll = async () => {
        try {
          const pollRes = await api.pollDeviceFlow(deviceCode);
          const pollData = pollRes.data;

          if (pollData.status === 'complete') {
            setDeviceFlowStatus('complete');
            setDeviceFlow(null);
            await checkAuth();
            return;
          }

          if (pollData.status === 'error') {
            setDeviceFlowStatus('error');
            setError(pollData.message || 'Authentication failed.');
            setDeviceFlow(null);
            return;
          }

          const nextInterval = pollData.slow_down ? interval + 5000 : interval;
          devicePollTimerRef.current = setTimeout(poll, nextInterval);
        } catch (err) {
          setDeviceFlowStatus('error');
          setError(err.message || 'Authentication failed.');
          setDeviceFlow(null);
        }
      };

      devicePollTimerRef.current = setTimeout(poll, interval);
      return data;
    } catch (err) {
      setDeviceFlowStatus('error');
      const msg = err.message || '';
      if (msg.includes('not configured') || msg.includes('Client ID')) {
        setErrorType('not_configured');
      }
      setError(msg || 'Could not start GitHub authentication.');
      return null;
    }
  }, [checkAuth]);

  const cancelDeviceFlow = useCallback(() => {
    if (devicePollTimerRef.current) {
      clearTimeout(devicePollTimerRef.current);
      devicePollTimerRef.current = null;
    }
    setDeviceFlow(null);
    setDeviceFlowStatus('idle');
    setError(null);
  }, []);

  // ------------------------------------------------------------------
  // PAT login
  // ------------------------------------------------------------------
  const loginWithPAT = useCallback(async (token) => {
    setError(null);
    setErrorType(null);
    try {
      const res = await api.authWithPAT(token);
      setAuthenticated(true);
      setUser(res.data.user);
      setExpired(false);
      return res.data;
    } catch (err) {
      const msg = err.message || '';
      if (msg.includes('NetworkError') || msg.includes('Failed to fetch')) {
        setErrorType('network_unavailable');
      } else {
        setErrorType('token_invalid');
      }
      setError(msg);
      throw err;
    }
  }, []);

  // ------------------------------------------------------------------
  // Disconnect
  // ------------------------------------------------------------------
  const disconnect = useCallback(async () => {
    try {
      await api.authDisconnect();
    } catch {
      // Ignore errors — clear local state regardless
    }
    setAuthenticated(false);
    setUser(null);
    setExpired(false);
    setOauthStatus('idle');
    setDeviceFlow(null);
    setDeviceFlowStatus('idle');
    setError(null);
    setErrorType(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setErrorType(null);
    setOauthStatus('idle');
  }, []);

  return {
    // State
    authenticated,
    user,
    loading,
    expired,
    error,
    errorType,

    // OAuth
    oauthStatus,
    oauthUrl,
    startOAuth,
    cancelOAuth,

    // Device flow
    deviceFlow,
    deviceFlowStatus,
    startDeviceAuth,
    cancelDeviceFlow,

    // PAT & Disconnect
    loginWithPAT,
    disconnect,
    checkAuth,
    setError,
    clearError,
  };
}
