import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Amplify } from 'aws-amplify';
import { signOut, fetchAuthSession } from 'aws-amplify/auth';
import { UserProfile } from '../types';

// Configure Amplify (this would be loaded from environment variables)
const amplifyConfig: any = {
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_USER_POOL_ID || 'us-east-1_example',
      userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || 'example',
    }
  },
  API: {
    REST: {
      AquaChainAPI: {
        endpoint: process.env.REACT_APP_API_ENDPOINT || 'https://api.aquachain.example.com',
        region: process.env.REACT_APP_AWS_REGION || 'us-east-1'
      }
    }
  }
};

// Add Identity Pool ID only if provided (optional for basic auth)
if (process.env.REACT_APP_IDENTITY_POOL_ID) {
  amplifyConfig.Auth.Cognito.identityPoolId = process.env.REACT_APP_IDENTITY_POOL_ID;
}

Amplify.configure(amplifyConfig);

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getAuthToken: () => Promise<string | null>;
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
          const session = await fetchAuthSession();
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

        const userProfile: UserProfile = {
          userId: result.user.userId || 'user-' + Date.now(),
          email: result.user.email,
          role: result.user.role || 'consumer',
          profile: {
            firstName: result.user.name?.split(' ')[0] || 'User',
            lastName: result.user.name?.split(' ')[1] || '',
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
          deviceIds: ['DEV-3421', 'DEV-3422'],
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
        const { signIn } = await import('aws-amplify/auth');
        const signInResult = await signIn({ username: email, password });

        if (signInResult.isSignedIn) {
          // Get user details and create profile
          const { getCurrentUser } = await import('aws-amplify/auth');
          const currentUser = await getCurrentUser();
          
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
      // Clear localStorage
      localStorage.removeItem('aquachain_user');
      localStorage.removeItem('aquachain_token');

      // Clear state
      setUser(null);
      setIsAuthenticated(false);

      // In production, would call AWS Amplify signOut
      if (process.env.NODE_ENV !== 'development') {
        await signOut();
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Logout error:', error);
    }
  };

  const getAuthToken = async (): Promise<string | null> => {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString() || null;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    getAuthToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};