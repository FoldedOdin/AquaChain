/**
 * Authentication Modal Interfaces and Types
 */

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe: boolean;
  csrfToken?: string;
  recaptchaToken?: string;
}

export interface SignupData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  role: 'consumer' | 'technician';
  acceptTerms: boolean;
  csrfToken?: string;
  recaptchaToken?: string;
}

// Types are already exported above, no need to re-export