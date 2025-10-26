import { LoginCredentials, SignupData } from '../components/LandingPage/AuthModal';

// AWS Amplify imports (loaded dynamically for production)
let amplifyAuth: any = null;

// Lazy load AWS Amplify Auth for production
const loadAmplifyAuth = async () => {
  if (!amplifyAuth && process.env.NODE_ENV === 'production') {
    try {
      const { signIn, signUp, confirmSignUp, getCurrentUser, signOut } = await import('aws-amplify/auth');
      amplifyAuth = { signIn, signUp, confirmSignUp, getCurrentUser, signOut };
    } catch (error) {
      console.warn('AWS Amplify not available:', error);
    }
  }
  return amplifyAuth;
};

// User role types
export type UserRole = 'consumer' | 'technician' | 'admin';

// Authentication result interface
export interface AuthResult {
  user: any;
  session: any;
  userRole: UserRole;
  redirectPath: string;
}

// User profile interface
export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  emailVerified: boolean;
  createdAt: string;
  lastLogin?: string;
}

// Authentication errors
export class AuthError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: any
  ) {
    super(message);
    this.name = 'AuthError';
  }
}

class AuthService {
  private currentUser: any = null;
  private currentSession: any = null;

  /**
   * Initialize authentication service
   */
  async initialize(): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'production') {
        // Load AWS Amplify for production
        await loadAmplifyAuth();
        
        // Try to get current authenticated user
        if (amplifyAuth) {
          try {
            this.currentUser = await amplifyAuth.getCurrentUser();
            this.currentSession = { isValid: () => true };
          } catch (error) {
            // User not authenticated, which is fine
            this.currentUser = null;
            this.currentSession = null;
          }
        }
      } else {
        // Development mode - no initialization needed
        this.currentUser = null;
        this.currentSession = null;
      }
    } catch (error) {
      console.warn('Auth service initialization failed:', error);
      this.currentUser = null;
      this.currentSession = null;
    }
  }

  /**
   * Sign in with email and password
   */
  async signIn(credentials: LoginCredentials): Promise<AuthResult> {
    try {
      // In development, use the dev server
      if (process.env.NODE_ENV === 'development') {
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/auth/signin`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(credentials),
        });

        const result = await response.json();
        
        if (!response.ok) {
          throw new AuthError(result.error || 'Sign in failed', 'SIGNIN_FAILED');
        }

        const user = result.user;
        const session = { isValid: () => true, token: result.token };
        const userRole: UserRole = user.role || 'consumer';
        const redirectPath = this.getRedirectPath(userRole);

        this.currentUser = user;
        this.currentSession = session;

        // Track login event
        await this.trackAuthEvent('login', userRole);

        return {
          user,
          session,
          userRole,
          redirectPath
        };
      }

      // Production: Use AWS Amplify Cognito
      const auth = await loadAmplifyAuth();
      if (auth) {
        try {
          const result = await auth.signIn({
            username: credentials.email,
            password: credentials.password
          });

          const user = result.user || await auth.getCurrentUser();
          const session = { isValid: () => true, ...result };
          const userRole: UserRole = user.attributes?.['custom:role'] || 'consumer';
          const redirectPath = this.getRedirectPath(userRole);

          this.currentUser = user;
          this.currentSession = session;

          // Track login event
          await this.trackAuthEvent('login', userRole);

          return {
            user,
            session,
            userRole,
            redirectPath
          };
        } catch (error: any) {
          throw new AuthError(
            error.message || 'Sign in failed',
            error.code || 'SIGNIN_FAILED',
            error
          );
        }
      }

      // Fallback if Amplify not available
      throw new AuthError('Authentication service not available', 'SERVICE_UNAVAILABLE');
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Sign up new user
   */
  async signUp(userData: SignupData): Promise<{ user: any; confirmationRequired: boolean }> {
    try {
      // In development, use the dev server
      if (process.env.NODE_ENV === 'development') {
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/auth/signup`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(userData),
        });

        const result = await response.json();
        
        if (!response.ok) {
          throw new AuthError(result.error || 'Signup failed', 'SIGNUP_FAILED');
        }

        // Track signup event
        await this.trackAuthEvent('signup', userData.role);

        return {
          user: { email: userData.email, userId: result.userId },
          confirmationRequired: result.confirmationRequired
        };
      }

      // Production: Use AWS Amplify Cognito
      const auth = await loadAmplifyAuth();
      if (auth) {
        try {
          const result = await auth.signUp({
            username: userData.email,
            password: userData.password,
            attributes: {
              email: userData.email,
              name: userData.name,
              'custom:role': userData.role
            }
          });

          // Track signup event
          await this.trackAuthEvent('signup', userData.role);

          return {
            user: result.user,
            confirmationRequired: !result.isSignUpComplete
          };
        } catch (error: any) {
          throw new AuthError(
            error.message || 'Signup failed',
            error.code || 'SIGNUP_FAILED',
            error
          );
        }
      }

      // Fallback if Amplify not available
      throw new AuthError('Authentication service not available', 'SERVICE_UNAVAILABLE');
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Confirm email verification with code
   */
  async confirmSignUp(email: string, confirmationCode: string): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - auto-confirm
        console.log(`Development: Auto-confirming signup for ${email}`);
        return;
      }

      // Production: Use AWS Amplify Cognito
      const auth = await loadAmplifyAuth();
      if (auth) {
        await auth.confirmSignUp({
          username: email,
          confirmationCode
        });
      } else {
        throw new AuthError('Authentication service not available', 'SERVICE_UNAVAILABLE');
      }
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Resend confirmation code
   */
  async resendConfirmationCode(email: string): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - simulate resend
        console.log(`Development: Simulating resend confirmation for ${email}`);
        return;
      }

      // Production: Use AWS Amplify Cognito
      const auth = await loadAmplifyAuth();
      if (auth) {
        await auth.resendSignUp({ username: email });
      } else {
        throw new AuthError('Authentication service not available', 'SERVICE_UNAVAILABLE');
      }
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Sign in with Google OAuth
   */
  async signInWithGoogle(): Promise<AuthResult> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - simulate OAuth
        const user = { 
          email: 'google-user@example.com',
          name: 'Google User',
          provider: 'google'
        };
        const session = { isValid: () => true };
        const userRole: UserRole = 'consumer';
        const redirectPath = this.getRedirectPath(userRole);

        this.currentUser = user;
        this.currentSession = session;

        await this.trackAuthEvent('oauth_login', userRole, 'google');

        return { user, session, userRole, redirectPath };
      }

      // Production: Use AWS Amplify v6 OAuth
      const { signInWithRedirect } = await import('aws-amplify/auth');
      
      // Initiate OAuth flow
      await signInWithRedirect({ 
        provider: 'Google',
        customState: JSON.stringify({ returnUrl: window.location.pathname })
      });

      // Note: This will redirect to Google, then back to callback URL
      // The actual user data will be retrieved in handleOAuthCallback()
      
      // Return placeholder - actual auth happens after redirect
      return {
        user: null,
        session: null,
        userRole: 'consumer',
        redirectPath: '/auth/callback'
      };
      
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Handle OAuth callback after redirect
   */
  async handleOAuthCallback(): Promise<AuthResult> {
    try {
      const { getCurrentUser, fetchAuthSession } = await import('aws-amplify/auth');
      
      // Get authenticated user
      const user = await getCurrentUser();
      const session = await fetchAuthSession();
      
      const userRole: UserRole = user.signInDetails?.loginId?.includes('admin') 
        ? 'admin' 
        : 'consumer';
      const redirectPath = this.getRedirectPath(userRole);

      this.currentUser = user;
      this.currentSession = session;

      // Track successful OAuth login
      await this.trackAuthEvent('oauth_login', userRole, 'google');

      return {
        user,
        session,
        userRole,
        redirectPath
      };
      
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Sign out current user
   */
  async signOut(): Promise<void> {
    try {
      const userRole = this.getCurrentUserRole();
      
      if (process.env.NODE_ENV === 'development') {
        // Development mode - clear local state
        this.currentUser = null;
        this.currentSession = null;
        
        // Clear localStorage
        localStorage.removeItem('aquachain_user');
        localStorage.removeItem('aquachain_token');
      } else {
        // Production: Use AWS Amplify v6
        const { signOut } = await import('aws-amplify/auth');
        await signOut({ global: true }); // Sign out from all devices
        
        this.currentUser = null;
        this.currentSession = null;
      }

      // Track logout event
      if (userRole) {
        await this.trackAuthEvent('logout', userRole);
      }
    } catch (error: any) {
      console.error('Sign out error:', error);
      // Force local cleanup even if remote signout fails
      this.currentUser = null;
      this.currentSession = null;
      localStorage.clear();
      
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<any> {
    return this.currentUser;
  }

  /**
   * Get current user session
   */
  async getCurrentSession(): Promise<any> {
    if (process.env.NODE_ENV === 'development') {
      return this.currentSession;
    }

    try {
      const { fetchAuthSession } = await import('aws-amplify/auth');
      const session = await fetchAuthSession();
      
      // Check if session is valid
      if (session.tokens?.accessToken) {
        this.currentSession = session;
        return session;
      }
      
      return null;
    } catch (error) {
      console.warn('Failed to fetch session:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    if (process.env.NODE_ENV === 'development') {
      return this.currentUser !== null;
    }

    try {
      const session = await this.getCurrentSession();
      return session !== null && session.tokens?.accessToken !== undefined;
    } catch (error) {
      return false;
    }
  }

  /**
   * Refresh authentication session
   */
  async refreshSession(): Promise<boolean> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - session doesn't expire
        return this.currentUser !== null;
      }

      const { fetchAuthSession } = await import('aws-amplify/auth');
      const session = await fetchAuthSession({ forceRefresh: true });
      
      if (session.tokens?.accessToken) {
        this.currentSession = session;
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Session refresh failed:', error);
      return false;
    }
  }

  /**
   * Get authentication token for API requests
   */
  async getAuthToken(): Promise<string | null> {
    try {
      if (process.env.NODE_ENV === 'development') {
        const token = localStorage.getItem('aquachain_token');
        return token;
      }

      const session = await this.getCurrentSession();
      return session?.tokens?.idToken?.toString() || null;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  /**
   * Get current user role
   */
  getCurrentUserRole(): UserRole | null {
    if (this.currentUser) {
      // In development mode, get role from user object
      if (process.env.NODE_ENV === 'development') {
        return this.currentUser.role || 'consumer';
      }
      // In production, get role from Cognito attributes
      return this.currentUser.attributes?.['custom:role'] || 'consumer';
    }
    return null;
  }

  /**
   * Request password reset
   * Sends verification code to user's email
   */
  async requestPasswordReset(email: string): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - simulate API call
        console.log('Password reset requested for:', email);
        await new Promise(resolve => setTimeout(resolve, 1000));
        return;
      }

      // Production: Use AWS Amplify v6
      const { resetPassword } = await import('aws-amplify/auth');
      await resetPassword({ username: email });
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Confirm password reset with verification code
   */
  async confirmPasswordReset(
    email: string,
    verificationCode: string,
    newPassword: string
  ): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        // Development mode - simulate API call
        console.log('Password reset confirmed for:', email);
        await new Promise(resolve => setTimeout(resolve, 1000));
        return;
      }

      // Production: Use AWS Amplify v6
      const { confirmResetPassword } = await import('aws-amplify/auth');
      await confirmResetPassword({
        username: email,
        confirmationCode: verificationCode,
        newPassword: newPassword
      });
    } catch (error: any) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get redirect path based on user role
   */
  private getRedirectPath(role: UserRole): string {
    switch (role) {
      case 'consumer':
        return '/dashboard/consumer';
      case 'technician':
        return '/dashboard/technician';
      case 'admin':
        return '/dashboard/admin';
      default:
        return '/dashboard';
    }
  }

  /**
   * Handle authentication errors
   */
  private handleAuthError(error: any): AuthError {
    let message = 'An authentication error occurred';
    let code = 'UNKNOWN_ERROR';

    if (error.code) {
      code = error.code;
      message = error.message || message;
    } else if (error.message) {
      message = error.message;
    }

    return new AuthError(message, code, error);
  }

  /**
   * Track authentication events for analytics
   */
  private async trackAuthEvent(
    event: string, 
    userRole: UserRole, 
    provider?: string
  ): Promise<void> {
    try {
      // Import analytics service dynamically to avoid circular dependencies
      const { analyticsService } = await import('./analyticsService');
      
      await analyticsService.trackConversion(
        event as 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
        undefined,
        {
          user_role: userRole,
          auth_provider: provider || 'email',
          timestamp: new Date().toISOString()
        }
      );

      // Set user role in analytics
      analyticsService.setUserRole(userRole);

      if (process.env.NODE_ENV === 'development') {
        console.log('Auth Event:', { event, userRole, provider, timestamp: new Date().toISOString() });
      }
    } catch (error) {
      // Don't throw errors for analytics tracking failures
      console.warn('Failed to track auth event:', error);
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;