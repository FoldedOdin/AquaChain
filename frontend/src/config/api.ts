/**
 * API Configuration
 * Centralized API endpoint configuration
 */

export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev',
  WEBSOCKET_URL: process.env.REACT_APP_WEBSOCKET_ENDPOINT || 'wss://p2lgfqqy50.execute-api.ap-south-1.amazonaws.com/dev',
  TIMEOUT: 30000, // 30 seconds
};

/**
 * Get full API URL for an endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_CONFIG.BASE_URL}/${cleanEndpoint}`;
};

/**
 * Get authorization headers
 */
export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

export default API_CONFIG;
