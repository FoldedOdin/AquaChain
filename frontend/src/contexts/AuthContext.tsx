import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Amplify } from 'aws-amplify';
import { signOut } from 'aws-amplify/auth';
import { fetchAuthSession } from '@aws-amplify/core';
import { UserProfile } from '../types';

// Clear any cached AWS credentials from previous sessions
// This prevents Amplify from trying to use Identity Pool
if (typeof window !== 'undefined') {
  // Clear Amplify-specific storage keys
  const keysToRemove = Object.keys(localStorage).filter(key => 
    key.includes('amplify') || 
    key.includes('CognitoIdentity') || 
    key.includes('aws.cognito')
  );
  keysToRemove.forEach(key => {
    if (!key.includes('aquachain')) { // Keep our app-specific keys
      localStorage.removeItem(key);
    }
  });
}

// Configure Amplify (this would be loaded from environment variables)
const amplifyConfig: any = {
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_USER_POOL_ID || 'us-east-1_example',
      userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || 'example',
      // Explicitly disable Identity Pool to prevent automatic credential fetching
      // Only add identityPoolId if explicitly provided
      ...(process.env.REACT_APP_IDENTITY_POOL_ID && process.env.REACT_APP_IDENTITY_POOL_ID.trim() !== '' 
        ? { identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID }
        : {}
      )
    }
  },
  API: {
    REST: {
      AquaChainAPI: {
        endpoint: process.env.REACT_APP_API_ENDPOINT || 'https://api.aquachain.example.com',
        region: process.env.REACT_APP_AWS_REGION || 'ap-south-1'
      }
    }
  }
};

Amplify.configure(amplifyConfig, {
  // Disable automatic credential refresh to prevent Identity Pool calls
  ssr: false
});

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isMFAVerified: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getAuthToken: () => Promise<string | null>;
  refreshUser: () => Promise<void>;
  requireMFA?: () => void;
  verifyMFA?: (code: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isMFAVerified, setIsMFAVerified] = useState(false);
  const [tokenRefreshTimer, setTokenRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    checkAuthState();
    
    // Cleanup timer on unmount
    return () => {
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Schedule automatic token refresh before expiration
   * Tokens expire after 60 minutes, refresh at 50 minutes
   */
  const scheduleTokenRefresh = () => {
    // Clear existing timer
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }

    // Schedule refresh for 50 minutes (3000 seconds)
    const refreshInterval = 50 * 60 * 1000; // 50 minutes in milliseconds
    const timer = setTimeout(async () => {
      console.log('🔄 Auto-refreshing token...');
      const refreshed = await refreshAuthToken();
      if (refreshed) {
        console.log('✅ Token auto-refreshed successfully');
        // Schedule next refresh
        scheduleTokenRefresh();
      } else {
        console.warn('⚠️ Token auto-refresh failed, user may need to re-login');
      }
    }, refreshInterval);

    setTokenRefreshTimer(timer);
    console.log(`⏰ Token refresh scheduled in ${refreshInterval / 1000 / 60} minutes`);
  };

  /**
   * Refresh authentication token using Cognito refresh token
   */
  const refreshAuthToken = async (): Promise<boolean> => {
    try {
      // Only refresh in AWS/production mode
      if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        console.log('ℹ️ Token refresh skipped in local dev mode');
        return true;
      }

      console.log('🔄 Refreshing authentication token...');
      
      // Force refresh the session to get new tokens
      const session = await fetchAuthSession({ 
        forceRefresh: true  // This uses the refresh token automatically
      });
      
      const newIdToken = session.tokens?.idToken?.toString();
      
      if (newIdToken) {
        // Update stored token
        localStorage.setItem('aquachain_token', newIdToken);
        console.log('✅ Token refreshed and stored');
        return true;
      } else {
        console.error('❌ Failed to get new token from refresh');
        return false;
      }
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      return false;
    }
  };

  const checkAuthState = async () => {
    try {
      // ALWAYS check localStorage first (both dev and prod)
      const storedUser = localStorage.getItem('aquachain_user');
      const storedToken = localStorage.getItem('aquachain_token');

      if (storedUser && storedToken) {
        try {
          const userData = JSON.parse(storedUser);
          
          // ALWAYS restore user session from localStorage first
          // This prevents redirect to landing page on refresh
          setUser(userData);
          setIsAuthenticated(true);
          setIsLoading(false);
          
          // Track login on page load if user doesn't have lastLogin timestamp
          // This ensures we capture the login even if tracking failed during actual login
          (async () => {
            try {
              // Check if user has lastLogin timestamp
              if (!userData.lastLogin) {
                console.log('🔄 No lastLogin found, tracking current session...');
                const token = storedToken;
                const trackResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/admin/users/track-login`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({ userId: userData.userId, email: userData.email })
                });
                
                if (trackResponse.ok) {
                  console.log('✅ Session login timestamp tracked successfully');
                  // Update localStorage with lastLogin
                  userData.lastLogin = new Date().toISOString();
                  localStorage.setItem('aquachain_user', JSON.stringify(userData));
                  setUser(userData);
                } else {
                  console.warn('⚠️ Session login tracking failed:', await trackResponse.text());
                }
              }
            } catch (trackError) {
              console.warn('⚠️ Failed to track session login:', trackError);
            }
          })();
          
          // Validate token in background (non-blocking)
          // This avoids unnecessary 401 errors and uses Cognito's built-in validation
          (async () => {
            try {
              const session = await fetchAuthSession({ forceRefresh: false });
              
              if (session.tokens?.idToken) {
                // Token is valid, schedule automatic token refresh
                scheduleTokenRefresh();
                console.log('✅ Session validated successfully');
                return;
              }
            } catch (sessionError) {
              // Session check failed, try to refresh in background
              console.log('🔄 Session validation failed, attempting background refresh...');
              const refreshed = await refreshAuthToken();
              
              if (refreshed) {
                scheduleTokenRefresh();
                console.log('✅ Token refreshed successfully in background');
                return;
              }
              
              // Refresh failed - user can continue with cached session
              // They'll be prompted to re-login when they try to make API calls
              console.warn('⚠️ Token refresh failed, user may need to re-login for API calls');
            }
          })();
          
          return;
        } catch (error) {
          console.warn('Error parsing stored user data:', error);
          // Clear invalid data
          localStorage.removeItem('aquachain_user');
          localStorage.removeItem('aquachain_token');
        }
      }

      // If no localStorage data, try Cognito (production only)
      if (process.env.NODE_ENV !== 'development' || !process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        // Production mode with AWS Cognito
        try {
          // Fetch session without AWS credentials to avoid Identity Pool calls
          const session = await fetchAuthSession({ 
            forceRefresh: false
          });
          if (session.tokens?.accessToken) {
            // Get user attributes from Cognito
            const { getCurrentUser } = await import('aws-amplify/auth');
            const currentUser = await getCurrentUser();
            
            // Extract groups from ID token to determine role
            const idToken = session.tokens?.idToken;
            const groups = idToken?.payload['cognito:groups'] as string[] || [];
            
            // Determine role from Cognito groups
            let role: 'admin' | 'technician' | 'consumer' = 'consumer';
            if (groups.includes('administrators') || groups.includes('admin')) {
              role = 'admin';
            } else if (groups.includes('technicians')) {
              role = 'technician';
            } else if (groups.includes('consumers')) {
              role = 'consumer';
            }
            
            // Create user profile from Cognito data
            const userProfile: UserProfile = {
              userId: currentUser.userId,
              email: currentUser.signInDetails?.loginId || '',
              role: role,
              profile: {
                firstName: 'User',
                lastName: '',
                phone: '+1234567890',
                address: {
                  street: '123 Main St',
                  city: 'Anytown',
                  state: 'CA',
                  zipCode: '12345',
                  coordinates: {
                    latitude: 37.7749,
                    longitude: -122.4194
                  }
                }
              },
              deviceIds: [],
              preferences: {
                notifications: {
                  push: true,
                  sms: true,
                  email: true
                },
                theme: 'auto',
                language: 'en'
              }
            };

            setUser(userProfile);
            setIsAuthenticated(true);
          } else {
            setIsAuthenticated(false);
          }
        } catch (error) {
          console.log('No authenticated user found');
          setIsAuthenticated(false);
        }
      } else {
        // No stored data and not production Cognito
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.log('Authentication check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // Validate inputs
      if (!email || !password) {
        throw new Error('Email and password are required');
      }

      // Check if we should use local backend
      const hasLocalBackend = process.env.REACT_APP_API_ENDPOINT?.includes('localhost') || 
                             process.env.REACT_APP_API_ENDPOINT?.includes('127.0.0.1');
      const useAWS = process.env.REACT_APP_AUTH_MODE === 'aws';

      if (!useAWS || hasLocalBackend) {
        // Development mode with local dev server
        console.log('🔐 Using local backend for login');
        
        const authService = (await import('../services/authService')).default;
        const result = await authService.signIn({ email, password, rememberMe: true });

        // Use actual data from backend instead of hardcoded values
        const userProfile: UserProfile = {
          userId: result.user.userId || 'user-' + Date.now(),
          email: result.user.email,
          role: result.user.role || 'consumer',
          profile: {
            firstName: result.user.firstName || result.user.name?.split(' ')[0] || '',
            lastName: result.user.lastName || result.user.name?.split(' ')[1] || '',
            phone: result.user.phone || '',
            address: result.user.address || null
          },
          deviceIds: result.user.deviceIds || [],
          preferences: {
            notifications: {
              push: true,
              sms: true,
              email: true
            },
            theme: 'auto',
            language: 'en'
          }
        };

        localStorage.setItem('aquachain_user', JSON.stringify(userProfile));
        localStorage.setItem('aquachain_token', result.session.token || 'dev-token-' + Date.now());

        setUser(userProfile);
        setIsAuthenticated(true);
        
        // Track login timestamp in DynamoDB
        console.log('🔄 Attempting to track login timestamp...');
        try {
          const token = result.session.token || localStorage.getItem('aquachain_token');
          const trackResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/admin/users/track-login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ userId: userProfile.userId, email: userProfile.email })
          });
          
          if (trackResponse.ok) {
            console.log('✅ Login timestamp tracked successfully');
          } else {
            console.warn('⚠️ Login tracking failed:', await trackResponse.text());
          }
        } catch (trackError) {
          console.warn('⚠️ Failed to track login (non-critical):', trackError);
        }
      } else {
        // Production mode with AWS Cognito
        const { signIn, fetchAuthSession, getCurrentUser } = await import('aws-amplify/auth');
        const signInResult = await signIn({ username: email, password });

        console.log('🔐 Cognito signIn result:', {
          isSignedIn: signInResult.isSignedIn,
          nextStep: signInResult.nextStep
        });

        if (signInResult.isSignedIn) {
          // Get user details and session
          const currentUser = await getCurrentUser();
          
          // CRITICAL: Get the ID token and store it in localStorage
          const session = await fetchAuthSession({ 
            forceRefresh: false
          });
          const idToken = session.tokens?.idToken?.toString();
          
          if (!idToken) {
            throw new Error('Failed to get authentication token');
          }
          
          // Store token in localStorage for API calls
          localStorage.setItem('aquachain_token', idToken);
          console.log('✅ Token stored in localStorage after login');
          
          // Extract groups from ID token to determine role
          const groups = session.tokens?.idToken?.payload['cognito:groups'] as string[] || [];
          
          // Determine role from Cognito groups
          let role: 'admin' | 'technician' | 'consumer' = 'consumer';
          if (groups.includes('administrators') || groups.includes('admin')) {
            role = 'admin';
          } else if (groups.includes('technicians')) {
            role = 'technician';
          } else if (groups.includes('consumers')) {
            role = 'consumer';
          }
          
          console.log('👤 User groups:', groups, '→ Role:', role);
          
          // Check if we already have profile data in localStorage
          const existingUser = localStorage.getItem('aquachain_user');
          let userProfile: UserProfile;
          
          if (existingUser) {
            // Use existing profile data
            const existing = JSON.parse(existingUser);
            console.log('✅ Using existing profile from localStorage:', existing);
            userProfile = {
              ...existing,
              userId: currentUser.userId,
              email: email,
              role: role
            };
          } else {
            // Create basic user profile for first-time login
            console.log('ℹ️ Creating new basic profile (first login)');
            userProfile = {
              userId: currentUser.userId,
              email: email,
              role: role,
              profile: {
                firstName: 'User',
                lastName: '',
                phone: '',
                address: null
              },
              deviceIds: [],
              preferences: {
                notifications: {
                  push: true,
                  sms: true,
                  email: true
                },
                theme: 'auto',
                language: 'en'
              }
            };
          }

          localStorage.setItem('aquachain_user', JSON.stringify(userProfile));
          setUser(userProfile);
          setIsAuthenticated(true);
          
          // Track login timestamp in DynamoDB
          console.log('🔄 Attempting to track login timestamp...');
          try {
            const trackResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/admin/users/track-login`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${idToken}`
              },
              body: JSON.stringify({ userId: currentUser.userId, email: email })
            });
            
            if (trackResponse.ok) {
              console.log('✅ Login timestamp tracked successfully');
            } else {
              console.warn('⚠️ Login tracking failed:', await trackResponse.text());
            }
          } catch (trackError) {
            console.warn('⚠️ Failed to track login (non-critical):', trackError);
          }
          
          // Schedule automatic token refresh
          scheduleTokenRefresh();
          
          // Attempt to load fresh profile from DynamoDB in background (optional)
          setTimeout(async () => {
            try {
              console.log('🔄 Attempting to load fresh profile from DynamoDB...');
              const profileResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/update`, {
                method: 'GET',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${idToken}`
                }
              });

              if (profileResponse.ok) {
                const result = await profileResponse.json();
                if (result.success && result.profile) {
                  console.log('✅ Fresh profile loaded from DynamoDB:', result.profile);
                  const loadedProfile: UserProfile = {
                    ...userProfile,
                    profile: {
                      firstName: result.profile.profile?.firstName || result.profile.firstName || userProfile.profile.firstName,
                      lastName: result.profile.profile?.lastName || result.profile.lastName || userProfile.profile.lastName,
                      phone: result.profile.profile?.phone || result.profile.phone || userProfile.profile.phone,
                      address: result.profile.profile?.address || result.profile.address || userProfile.profile.address
                    },
                    deviceIds: result.profile.deviceIds || userProfile.deviceIds,
                    preferences: result.profile.preferences || userProfile.preferences
                  };
                  localStorage.setItem('aquachain_user', JSON.stringify(loadedProfile));
                  setUser(loadedProfile);
                  console.log('✅ Profile updated with fresh data from DynamoDB');
                }
              } else {
                console.log('ℹ️ Could not load fresh profile (using cached data)');
              }
            } catch (error) {
              console.log('ℹ️ Background profile load failed (using cached data):', error);
            }
          }, 500);
        } else {
          // Sign in requires additional steps
          console.error('❌ Sign in not completed. Next step:', signInResult.nextStep);
          
          // Handle different authentication challenges
          if (signInResult.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
            throw new Error('NEW_PASSWORD_REQUIRED');
          } else if (signInResult.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_SMS_CODE') {
            throw new Error('MFA_SMS_REQUIRED');
          } else if (signInResult.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_TOTP_CODE') {
            throw new Error('MFA_TOTP_REQUIRED');
          } else if (signInResult.nextStep?.signInStep === 'CONFIRM_SIGN_UP') {
            throw new Error('UNCONFIRMED_USER');
          } else {
            throw new Error(`Sign in requires additional step: ${signInResult.nextStep?.signInStep || 'UNKNOWN'}`);
          }
        }
      }
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Check for specific Cognito errors
      if (error.name === 'UserNotConfirmedException' || error.message?.includes('User is not confirmed')) {
        // User needs to verify their email
        throw new Error('UNCONFIRMED_USER');
      } else if (error.name === 'NotAuthorizedException') {
        throw new Error('Invalid email or password');
      } else if (error.name === 'UserNotFoundException') {
        throw new Error('User not found');
      } else {
        throw new Error(error.message || 'Login failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Clear token refresh timer
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
        setTokenRefreshTimer(null);
      }

      // Check auth mode: use AWS Cognito if REACT_APP_AUTH_MODE is 'aws' or in production
      const useAWS = process.env.REACT_APP_AUTH_MODE === 'aws' || process.env.NODE_ENV === 'production';
      
      // Clear localStorage
      localStorage.removeItem('aquachain_user');
      localStorage.removeItem('aquachain_token');

      // Clear state
      setUser(null);
      setIsAuthenticated(false);

      // Sign out from AWS Cognito if using AWS mode
      if (useAWS) {
        const { signOut } = await import('aws-amplify/auth');
        await signOut();
      }
      
      console.log('✅ Logged out successfully');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Logout error:', error);
    }
  };

  const getAuthToken = async (): Promise<string | null> => {
    try {
      // First, try to get token from localStorage (works for both dev and prod)
      const storedToken = localStorage.getItem('aquachain_token');
      if (storedToken) {
        // In production/AWS mode, check if token needs refresh
        if (process.env.REACT_APP_AUTH_MODE === 'aws' || process.env.NODE_ENV === 'production') {
          try {
            // Try to decode token to check expiration (JWT tokens have exp claim)
            const tokenParts = storedToken.split('.');
            if (tokenParts.length === 3) {
              const payload = JSON.parse(atob(tokenParts[1]));
              const expirationTime = payload.exp * 1000; // Convert to milliseconds
              const currentTime = Date.now();
              const timeUntilExpiry = expirationTime - currentTime;
              
              // If token expires in less than 5 minutes, refresh it
              if (timeUntilExpiry < 5 * 60 * 1000) {
                console.log('🔄 Token expiring soon, refreshing...');
                const refreshed = await refreshAuthToken();
                if (refreshed) {
                  const newToken = localStorage.getItem('aquachain_token');
                  console.log('✅ Token refreshed proactively');
                  return newToken;
                }
              }
            }
          } catch (decodeError) {
            console.warn('⚠️ Could not decode token for expiration check:', decodeError);
          }
        }
        
        console.log('✅ Using stored token from localStorage');
        return storedToken;
      }

      // If not in localStorage, fetch from Amplify session (AWS mode only)
      if (process.env.REACT_APP_AUTH_MODE === 'aws' || process.env.NODE_ENV === 'production') {
        console.log('🔄 Fetching fresh token from Amplify session');
        const session = await fetchAuthSession({ 
          forceRefresh: false
        });
        const idToken = session.tokens?.idToken?.toString();
        
        // Store it for next time
        if (idToken) {
          localStorage.setItem('aquachain_token', idToken);
          console.log('✅ Token fetched and stored');
          
          // Schedule refresh
          scheduleTokenRefresh();
        }
        
        return idToken || null;
      }

      console.warn('⚠️ No token found in localStorage or Amplify session');
      return null;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('❌ Error getting auth token:', error);
      return null;
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const storedToken = localStorage.getItem('aquachain_token');
      const storedUser = localStorage.getItem('aquachain_user');
      
      if (!storedToken || !storedUser) {
        console.log('ℹ️ No token or user data to refresh');
        return;
      }

      const userData = JSON.parse(storedUser);
      
      // Try to fetch fresh profile from API
      try {
        console.log('🔄 Refreshing profile from API...');
        // Add cache-busting timestamp to ensure fresh data
        const timestamp = Date.now();
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/update?t=${timestamp}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${storedToken}`
          }
        });

        if (response.ok) {
          const result = await response.json();
          if (result.success && result.profile) {
            console.log('✅ Fresh profile received:', result.profile);
            const refreshedProfile: UserProfile = {
              ...userData,
              email: result.profile.email || userData.email, // Update email from API response
              profile: {
                firstName: result.profile.profile?.firstName || result.profile.firstName || userData.profile?.firstName || 'User',
                lastName: result.profile.profile?.lastName || result.profile.lastName || userData.profile?.lastName || '',
                phone: result.profile.profile?.phone || result.profile.phone || userData.profile?.phone || '',
                address: result.profile.profile?.address || result.profile.address || userData.profile?.address || null
              },
              deviceIds: result.profile.deviceIds || userData.deviceIds || [],
              preferences: result.profile.preferences || userData.preferences
            };
            localStorage.setItem('aquachain_user', JSON.stringify(refreshedProfile));
            setUser(refreshedProfile);
            console.log('✅ Profile refreshed successfully');
            return;
          }
        }
      } catch (apiError) {
        console.log('ℹ️ API refresh failed, using localStorage:', apiError);
      }

      // Fallback: just reload from localStorage
      setUser(userData);
      console.log('✅ User data refreshed from localStorage');
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  const requireMFA = () => {
    // In a real implementation, this would trigger MFA challenge
    // For now, we'll simulate MFA verification after a short delay
    setTimeout(() => {
      setIsMFAVerified(true);
    }, 2000);
  };

  const verifyMFA = async (code: string): Promise<boolean> => {
    // In a real implementation, this would verify the MFA code
    // For now, we'll accept any 6-digit code
    if (code.length === 6 && /^\d+$/.test(code)) {
      setIsMFAVerified(true);
      return true;
    }
    return false;
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    isMFAVerified,
    login,
    logout,
    getAuthToken,
    refreshUser,
    requireMFA,
    verifyMFA
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
