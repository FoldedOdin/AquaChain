import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Amplify } from 'aws-amplify';
import { signOut, fetchAuthSession } from 'aws-amplify/auth';
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

  useEffect(() => {
    checkAuthState();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const checkAuthState = async () => {
    try {
      if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        // Development mode with local dev server
        const storedUser = localStorage.getItem('aquachain_user');
        const storedToken = localStorage.getItem('aquachain_token');

        if (storedUser && storedToken) {
          const userData = JSON.parse(storedUser);

          try {
            const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/auth/validate`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storedToken}`
              },
              body: JSON.stringify({ email: userData.email })
            });

            if (response.ok) {
              const validatedUser = await response.json();
              setUser(validatedUser.user);
              setIsAuthenticated(true);
            } else {
              localStorage.removeItem('aquachain_user');
              localStorage.removeItem('aquachain_token');
              setIsAuthenticated(false);
            }
          } catch (error) {
            console.warn('Dev server not available, using stored user data');
            setUser(userData);
            setIsAuthenticated(true);
          }
        } else {
          setIsAuthenticated(false);
        }
      } else {
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
            
            // Create user profile from Cognito data
            const userProfile: UserProfile = {
              userId: currentUser.userId,
              email: currentUser.signInDetails?.loginId || '',
              role: 'consumer', // Default role, should be set from Cognito groups
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
      if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        // Development mode with local dev server
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
      } else {
        // Production mode with AWS Cognito
        const { signIn, fetchAuthSession, getCurrentUser } = await import('aws-amplify/auth');
        const signInResult = await signIn({ username: email, password });

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
          
          const userProfile: UserProfile = {
            userId: currentUser.userId,
            email: email,
            role: 'consumer', // Should be determined from Cognito groups
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

          localStorage.setItem('aquachain_user', JSON.stringify(userProfile));
          setUser(userProfile);
          setIsAuthenticated(true);
        } else {
          throw new Error('Sign in not completed');
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      throw new Error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
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
      if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        const storedToken = localStorage.getItem('aquachain_token');
        const storedUser = localStorage.getItem('aquachain_user');
        
        if (storedToken && storedUser) {
          const userData = JSON.parse(storedUser);
          
          console.log('🔄 Refreshing user data for:', userData.email);
          
          const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/auth/validate`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${storedToken}`
            },
            body: JSON.stringify({ email: userData.email })
          });

          if (response.ok) {
            const validatedUser = await response.json();
            console.log('📥 Fresh user data received:', validatedUser.user);
            setUser(validatedUser.user);
            localStorage.setItem('aquachain_user', JSON.stringify(validatedUser.user));
            console.log('✅ User data refreshed and state updated');
          } else {
            console.error('❌ Failed to refresh user data:', response.status);
          }
        }
      } else {
        // Production: re-validate with Cognito
        await checkAuthState();
      }
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