/**
 * Google OAuth Configuration
 * 
 * This file contains the configuration for Google OAuth authentication.
 * Make sure to set up environment variables in .env file.
 */

export interface GoogleOAuthConfig {
  clientId: string;
  redirectUri: string;
  scope: string;
  responseType: string;
  prompt: string;
}

// Get configuration from environment variables
const getGoogleOAuthConfig = (): GoogleOAuthConfig => {
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';
  const baseUrl = process.env.REACT_APP_BASE_URL || 'http://localhost:3000';
  const redirectUri = process.env.REACT_APP_OAUTH_REDIRECT_URI || `${baseUrl}/auth/google/callback`;

  if (!clientId) {
    console.warn('⚠️ REACT_APP_GOOGLE_CLIENT_ID is not set. Google OAuth will not work.');
  }

  return {
    clientId,
    redirectUri,
    scope: 'openid email profile',
    responseType: 'code',
    prompt: 'select_account'
  };
};

export const googleOAuthConfig = getGoogleOAuthConfig();

/**
 * Generate Google OAuth authorization URL
 */
export const getGoogleAuthUrl = (state?: string): string => {
  const config = googleOAuthConfig;
  
  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    response_type: config.responseType,
    scope: config.scope,
    prompt: config.prompt,
    access_type: 'offline',
    ...(state && { state })
  });

  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
};

/**
 * Generate a random state parameter for CSRF protection
 */
export const generateState = (): string => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
};

/**
 * Store state in session storage for verification
 */
export const storeOAuthState = (state: string): void => {
  sessionStorage.setItem('oauth_state', state);
  sessionStorage.setItem('oauth_state_timestamp', Date.now().toString());
};

/**
 * Verify OAuth state parameter
 */
export const verifyOAuthState = (state: string): boolean => {
  const storedState = sessionStorage.getItem('oauth_state');
  const timestamp = sessionStorage.getItem('oauth_state_timestamp');
  
  // Debug logging
  console.log('🔐 OAuth State Verification:');
  console.log('  Returned state:', state);
  console.log('  Stored state:', storedState);
  console.log('  Timestamp:', timestamp);
  
  // Verify state matches BEFORE clearing
  if (!storedState) {
    console.error('❌ No stored state found - state may have been cleared or never set');
    return false;
  }
  
  if (storedState !== state) {
    console.error('❌ OAuth state mismatch - possible CSRF attack');
    console.error('  Expected:', storedState);
    console.error('  Received:', state);
    // Clear stored state after failed verification
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('oauth_state_timestamp');
    return false;
  }
  
  // Verify state is not too old (5 minutes max)
  if (timestamp) {
    const age = Date.now() - parseInt(timestamp);
    if (age > 5 * 60 * 1000) {
      console.error('❌ OAuth state expired (age:', Math.floor(age / 1000), 'seconds)');
      // Clear expired state
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('oauth_state_timestamp');
      return false;
    }
    console.log('  ✅ State age:', Math.floor(age / 1000), 'seconds (valid)');
  }
  
  // Clear stored state after successful verification
  sessionStorage.removeItem('oauth_state');
  sessionStorage.removeItem('oauth_state_timestamp');
  
  console.log('✅ OAuth state verified successfully');
  return true;
};

/**
 * Parse OAuth callback URL parameters
 */
export interface OAuthCallbackParams {
  code?: string;
  state?: string;
  error?: string;
  error_description?: string;
}

export const parseOAuthCallback = (url: string = window.location.href): OAuthCallbackParams => {
  const urlObj = new URL(url);
  const params = new URLSearchParams(urlObj.search);
  
  return {
    code: params.get('code') || undefined,
    state: params.get('state') || undefined,
    error: params.get('error') || undefined,
    error_description: params.get('error_description') || undefined
  };
};

export default googleOAuthConfig;
