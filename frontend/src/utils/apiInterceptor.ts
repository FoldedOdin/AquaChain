/**
 * API Interceptor for handling token expiration
 * On a 401 response, attempts a silent Cognito token refresh before logging out.
 * Only forces logout when the refresh itself also fails.
 */

import { fetchAuthSession } from '@aws-amplify/core';

/** How many concurrent refresh attempts are allowed at once */
let refreshPromise: Promise<string | null> | null = null;

/**
 * Try to silently refresh the Cognito session and return the new id-token.
 * Returns null if the refresh fails (session truly expired).
 */
const tryRefreshToken = async (): Promise<string | null> => {
  // Deduplicate: if a refresh is already in-flight, wait for it
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const session = await fetchAuthSession({ forceRefresh: true });
      const newToken = session.tokens?.idToken?.toString() ?? null;

      if (newToken) {
        localStorage.setItem('aquachain_token', newToken);
        const accessToken = session.tokens?.accessToken?.toString();
        if (accessToken) localStorage.setItem('aquachain_access_token', accessToken);
        console.log('✅ Token silently refreshed by apiInterceptor');
      }

      return newToken;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

const clearSession = async (logout?: () => Promise<void>) => {
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('aquachain_access_token');
  localStorage.removeItem('aquachain_user');
  if (logout) {
    try { await logout(); } catch { /* ignore */ }
  }
  window.location.href = '/';
};

export const handleApiError = async (response: Response, logout?: () => Promise<void>) => {
  if (response.status === 401) {
    console.warn('🔒 Token expired (401), attempting silent refresh...');

    const newToken = await tryRefreshToken();

    if (!newToken) {
      console.warn('🔒 Token refresh failed, logging out user');
      await clearSession(logout);
      throw new Error('Session expired. Please login again.');
    }

    // Refresh succeeded — caller should retry the original request
    throw new Error('TOKEN_REFRESHED');
  }

  return response;
};

/**
 * Wrapper for fetch that handles 401 errors with automatic token refresh + one retry.
 */
export const fetchWithAuth = async (
  url: string,
  options: RequestInit = {},
  logout?: () => Promise<void>
): Promise<Response> => {
  const buildHeaders = (): HeadersInit => {
    const token = localStorage.getItem('aquachain_token');
    return {
      ...options.headers,
      Authorization: token ? `Bearer ${token}` : '',
    };
  };

  let response = await fetch(url, { ...options, headers: buildHeaders() });

  if (response.status === 401) {
    console.warn('🔒 401 received, attempting silent token refresh...');
    const newToken = await tryRefreshToken();

    if (newToken) {
      // Retry the original request with the fresh token
      response = await fetch(url, { ...options, headers: buildHeaders() });
    } else {
      console.warn('🔒 Token refresh failed, logging out user');
      await clearSession(logout);
      throw new Error('Session expired. Please login again.');
    }
  }

  return response;
};
