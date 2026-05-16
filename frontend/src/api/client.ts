/**
 * AquaChain API Client
 *
 * Centralised, typed HTTP client used by all domain API modules.
 * Previously, the codebase had a private `makeRequest` method inside the
 * `DataService` class that was effectively duplicated across the file.
 * Moving it here ensures:
 *   - One place to change auth strategy (e.g. swap Cognito for OIDC)
 *   - One place to add interceptors (retry, circuit breaker, tracing headers)
 *   - Domain modules remain thin and free of HTTP boilerplate
 *
 * Security: mirrors the logger-based approach in dataService.ts — no raw
 * token values are logged, and the logger is silent in production.
 */

import logger from '../lib/logger';

export const API_BASE_URL =
  process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3001';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ApiError extends Error {
  /** HTTP status code (0 = network failure before server responded) */
  status: number;
  /** Parsed error body from the server, if available */
  details?: unknown;
  /** The endpoint that failed */
  endpoint: string;
}

export interface RequestOptions extends Omit<RequestInit, 'headers'> {
  headers?: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Token retrieval
// ---------------------------------------------------------------------------

function getToken(): string | null {
  return (
    localStorage.getItem('aquachain_token') || localStorage.getItem('authToken')
  );
}

function isDevelopmentToken(token: string | null): boolean {
  return Boolean(token && token.startsWith('dev-token-'));
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

/**
 * Make a typed HTTP request to the AquaChain backend.
 *
 * @param endpoint - Path relative to API_BASE_URL (e.g. `/api/devices`)
 * @param options  - Standard fetch options; `headers` is merged with auth headers
 * @param tokenRefresher - Optional callback that returns a refreshed JWT token
 * @param isRetry  - Internal flag preventing infinite refresh loops
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestOptions = {},
  tokenRefresher?: () => Promise<string | null>,
  isRetry = false
): Promise<T> {
  const token = getToken();
  const url = `${API_BASE_URL}${endpoint}`;

  logger.debug('API request', { url, method: options.method ?? 'GET' });

  if (isDevelopmentToken(token) && url.includes('amazonaws.com')) {
    throw buildError(
      'Development token cannot be used with production API',
      401,
      endpoint
    );
  }

  const response = await fetch(url, {
    ...options,
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
      ...options.headers,
    },
  }).catch((networkErr: Error) => {
    throw buildError(
      `Network error: ${networkErr.message}`,
      0,
      endpoint,
      networkErr
    );
  });

  logger.debug('API response', { status: response.status, url });

  const responseText = await response.text();

  if (!response.ok) {
    // Attempt token refresh on 401
    if (
      response.status === 401 &&
      !isRetry &&
      tokenRefresher &&
      !isDevelopmentToken(token)
    ) {
      logger.info('401 received — attempting token refresh');
      const newToken = await tokenRefresher();
      if (newToken) {
        logger.info('Token refreshed, retrying request');
        return apiFetch<T>(endpoint, options, tokenRefresher, true);
      }
    }

    const errorBody = tryParseJson(responseText);
    const message = resolveErrorMessage(response, token, endpoint, errorBody);
    logger.error('API request failed', { endpoint, status: response.status });
    throw buildError(message, response.status, endpoint, undefined, errorBody);
  }

  const result = tryParseJson(responseText);

  if (result !== null && typeof result === 'object') {
    const r = result as Record<string, unknown>;

    // Unwrap envelope: { success: true, data: ... }
    if ('success' in r) {
      if (r.success) return (r.data ?? r) as T;
      const msg =
        typeof r.error === 'string'
          ? r.error
          : typeof r.message === 'string'
          ? r.message
          : 'API returned success=false';
      throw buildError(msg, response.status, endpoint);
    }
  }

  return (result ?? responseText) as T;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function tryParseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function resolveErrorMessage(
  response: Response,
  token: string | null,
  endpoint: string,
  errorBody?: unknown
): string {
  const bodyMessage =
    errorBody &&
    typeof errorBody === 'object' &&
    ('error' in (errorBody as object) || 'message' in (errorBody as object))
      ? ((errorBody as Record<string, unknown>).error as string | undefined) ??
        ((errorBody as Record<string, unknown>).message as string | undefined)
      : undefined;

  if (bodyMessage) return bodyMessage;

  switch (response.status) {
    case 401:
      if (isDevelopmentToken(token))
        return 'Authentication failed: development token cannot be used with production API';
      if (!token) return 'Authentication failed: no token found — please log in';
      return 'Authentication failed: invalid or expired token';
    case 403:
      return 'Access forbidden: insufficient permissions';
    case 404:
      return `API endpoint not found: ${endpoint}`;
    default:
      if (response.status >= 500) return 'Server error: please try again later';
      return `HTTP ${response.status}: ${response.statusText}`;
  }
}

function buildError(
  message: string,
  status: number,
  endpoint: string,
  originalError?: unknown,
  details?: unknown
): ApiError {
  const err = new Error(message) as ApiError;
  err.status = status;
  err.endpoint = endpoint;
  if (details !== undefined) err.details = details;
  if (originalError instanceof Error) err.cause = originalError;
  return err;
}
