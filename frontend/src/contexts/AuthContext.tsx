import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signOut, fetchAuthSession } from 'aws-amplify/auth';
import { UserProfile } from '../types';

// Configure Amplify (this would be loaded from environment variables)
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_USER_POOL_ID || 'us-east-1_example',
      userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || 'example',
      identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID || 'us-east-1:example',
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
});

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
      const currentUser = await getCurrentUser();
      if (currentUser) {
        // Fetch user profile from API
        const token = await getAuthToken();
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/users/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const userProfile = await response.json();
          setUser(userProfile);
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.log('No authenticated user found');
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    // This would use Amplify Auth signIn
    // For now, we'll simulate the login process
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock user data for development
      const mockUser: UserProfile = {
        userId: 'user-123',
        email: email,
        role: 'consumer',
        profile: {
          firstName: 'John',
          lastName: 'Doe',
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
      
      setUser(mockUser);
      setIsAuthenticated(true);
    } catch (error) {
      throw new Error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await signOut();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const getAuthToken = async (): Promise<string | null> => {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString() || null;
    } catch (error) {
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