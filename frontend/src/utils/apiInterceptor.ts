/**
 * API Interceptor for handling token expiration
 * Automatically logs out user when token expires (401 errors)
 */

export const handleApiError = async (response: Response, logout?: () => Promise<void>) => {
  if (response.status === 401) {
    console.warn('🔒 Token expired (401), logging out user');
    
    // Clear local storage
    localStorage.removeItem('aquachain_token');
    localStorage.removeItem('aquachain_user');
    
    // Call logout if provided
    if (logout) {
      await logout();
    }
    
    // Redirect to login
    window.location.href = '/';
    
    throw new Error('Session expired. Please login again.');
  }
  
  return response;
};

/**
 * Wrapper for fetch that handles 401 errors automatically
 */
export const fetchWithAuth = async (
  url: string,
  options: RequestInit = {},
  logout?: () => Promise<void>
): Promise<Response> => {
  const token = localStorage.getItem('aquachain_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': token ? `Bearer ${token}` : '',
    },
  });
  
  await handleApiError(response, logout);
  
  return response;
};
