/**
 * API Utilities
 * Provides common API request functionality with authentication
 */

interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: string;
  headers?: Record<string, string>;
}

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  success: boolean;
}

/**
 * Make authenticated API request
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const baseUrl = process.env.REACT_APP_API_ENDPOINT || '';
  const token = localStorage.getItem('aquachain_token');

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const requestOptions: RequestInit = {
    method: options.method || 'GET',
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  if (options.body) {
    requestOptions.body = options.body;
  }

  const response = await fetch(`${baseUrl}${endpoint}`, requestOptions);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Make API request with response wrapper
 */
export async function apiRequestWithWrapper<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  try {
    const data = await apiRequest<T>(endpoint, options);
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error('API request failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}