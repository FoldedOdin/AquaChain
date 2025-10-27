import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { EyeIcon, EyeSlashIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import DOMPurify from 'dompurify';
import { LoginCredentials, SignupData } from './AuthModal';
import GoogleOAuthButton from './GoogleOAuthButton';
import EmailVerificationStatus from './EmailVerificationStatus';
import EmailVerificationModal from './EmailVerificationModal';
import PasswordResetModal from './PasswordResetModal';
import authService from '../../services/authService';
import { InputSanitizer, RateLimiter, RecaptchaService, csrfTokenManager } from '../../utils/security';

// Form validation utilities
interface ValidationResult {
  isValid: boolean;
  message: string;
}

interface FormErrors {
  [key: string]: string;
}

// Password strength levels
type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong';

interface PasswordStrengthResult {
  strength: PasswordStrength;
  score: number;
  feedback: string[];
}

// Validation functions using security utilities
const validateEmail = (email: string): ValidationResult => {
  const result = InputSanitizer.sanitizeEmail(email);
  return {
    isValid: result.isValid,
    message: result.error || ''
  };
};

const validatePassword = (password: string): ValidationResult => {
  const sanitized = DOMPurify.sanitize(password);
  
  if (!sanitized) {
    return { isValid: false, message: 'Password is required' };
  }
  
  if (sanitized.length < 8) {
    return { isValid: false, message: 'Password must be at least 8 characters long' };
  }
  
  return { isValid: true, message: '' };
};

const validateName = (name: string): ValidationResult => {
  const result = InputSanitizer.sanitizeName(name);
  return {
    isValid: result.isValid,
    message: result.error || ''
  };
};

const checkPasswordStrength = (password: string): PasswordStrengthResult => {
  let score = 0;
  const feedback: string[] = [];
  
  // Length check
  if (password.length >= 8) score += 1;
  else feedback.push('Use at least 8 characters');
  
  // Uppercase check
  if (/[A-Z]/.test(password)) score += 1;
  else feedback.push('Include uppercase letters');
  
  // Lowercase check
  if (/[a-z]/.test(password)) score += 1;
  else feedback.push('Include lowercase letters');
  
  // Number check
  if (/\d/.test(password)) score += 1;
  else feedback.push('Include numbers');
  
  // Special character check
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
  else feedback.push('Include special characters');
  
  let strength: PasswordStrength;
  if (score <= 2) strength = 'weak';
  else if (score === 3) strength = 'fair';
  else if (score === 4) strength = 'good';
  else strength = 'strong';
  
  return { strength, score, feedback };
};

// Login Form Component
interface LoginFormProps {
  onSubmit: (credentials: LoginCredentials) => Promise<void>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  success: string | null;
  setSuccess: (success: string | null) => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  isLoading,
  setIsLoading,
  error,
  setError,
  success,
  setSuccess
}) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});
  const [showPasswordReset, setShowPasswordReset] = useState(false);

  // Real-time validation
  useEffect(() => {
    const newErrors: FormErrors = {};
    
    if (touched.email) {
      const emailValidation = validateEmail(formData.email);
      if (!emailValidation.isValid) {
        newErrors.email = emailValidation.message;
      }
    }
    
    if (touched.password) {
      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.message;
      }
    }
    
    setErrors(newErrors);
  }, [formData, touched]);

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check rate limiting
    const rateLimitKey = `login_${formData.email}`;
    if (RateLimiter.isRateLimited(rateLimitKey, 5, 15 * 60 * 1000)) {
      setError('Too many login attempts. Please try again in 15 minutes.');
      return;
    }
    
    // Mark all fields as touched
    setTouched({ email: true, password: true });
    
    // Validate all fields
    const emailValidation = validateEmail(formData.email);
    const passwordValidation = validatePassword(formData.password);
    
    const newErrors: FormErrors = {};
    if (!emailValidation.isValid) newErrors.email = emailValidation.message;
    if (!passwordValidation.isValid) newErrors.password = passwordValidation.message;
    
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length > 0) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Get reCAPTCHA token if available
      let recaptchaToken = '';
      try {
        recaptchaToken = await RecaptchaService.executeRecaptcha('login');
      } catch (recaptchaError) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('reCAPTCHA not available:', recaptchaError);
        }
      }

      // Get CSRF token
      const csrfToken = csrfTokenManager.getToken();

      // Sanitize input data
      const sanitizedEmail = InputSanitizer.sanitizeEmail(formData.email);
      
      await onSubmit({
        email: sanitizedEmail.value,
        password: formData.password, // Don't sanitize password as it may contain special chars
        rememberMe: formData.rememberMe,
        csrfToken,
        recaptchaToken
      } as any);
      
      setSuccess('Login successful! Redirecting...');
      
      // Reset rate limit on successful login
      RateLimiter.resetRateLimit(rateLimitKey);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    try {
      await authService.signInWithGoogle();
      setSuccess('Google sign-in successful! Redirecting...');
      
      // Call the parent's onSubmit with a mock credentials object
      // The actual authentication is handled by the auth service
      await onSubmit({
        email: '', // Will be populated from Google OAuth
        password: '', // Not needed for OAuth
        rememberMe: true // Default for OAuth
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed. Please try again.');
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.2 }}
      onSubmit={handleSubmit}
      className="space-y-4"
      noValidate
    >
      {/* Error/Success Messages */}
      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {success && (
        <div className="rounded-md bg-green-50 p-4" role="alert">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* Email Field */}
      <div>
        <label htmlFor="login-email" className="block text-sm font-medium text-gray-700">
          Email Address
        </label>
        <div className="mt-1">
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className={`block w-full rounded-md border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.email ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            disabled={isLoading}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? 'login-email-error' : undefined}
          />
          {errors.email && (
            <p id="login-email-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.email}
            </p>
          )}
        </div>
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="login-password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <div className="mt-1 relative">
          <input
            id="login-password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            required
            className={`block w-full rounded-md border px-3 py-2 pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.password ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your password"
            value={formData.password}
            onChange={(e) => handleInputChange('password', e.target.value)}
            onBlur={() => handleBlur('password')}
            disabled={isLoading}
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? 'login-password-error' : undefined}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isLoading}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeSlashIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            ) : (
              <EyeIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            )}
          </button>
          {errors.password && (
            <p id="login-password-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.password}
            </p>
          )}
        </div>
      </div>

      {/* Remember Me */}
      <div className="flex items-center">
        <input
          id="remember-me"
          name="remember-me"
          type="checkbox"
          className="h-4 w-4 text-aqua-600 focus:ring-aqua-500 border-gray-300 rounded"
          checked={formData.rememberMe}
          onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
          disabled={isLoading}
        />
        <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
          Remember me
        </label>
      </div>

      {/* Google OAuth Button */}
      <div>
        <GoogleOAuthButton
          onSignIn={handleGoogleSignIn}
          disabled={isLoading}
        />
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or continue with email</span>
        </div>
      </div>

      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={isLoading || Object.keys(errors).length > 0}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Signing in...
            </>
          ) : (
            'Sign In'
          )}
        </button>
      </div>

      {/* Forgot Password Link */}
      <div className="text-center">
        <button
          type="button"
          className="text-sm text-aqua-600 hover:text-aqua-500 focus:outline-none focus:underline"
          disabled={isLoading}
          onClick={() => setShowPasswordReset(true)}
        >
          Forgot your password?
        </button>
      </div>

      {/* Password Reset Modal */}
      <PasswordResetModal
        isOpen={showPasswordReset}
        onClose={() => setShowPasswordReset(false)}
      />
    </motion.form>
  );
};

// Signup Form Component
interface SignupFormProps {
  onSubmit: (userData: SignupData) => Promise<void>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  success: string | null;
  setSuccess: (success: string | null) => void;
}

export const SignupForm: React.FC<SignupFormProps> = ({
  onSubmit,
  isLoading,
  setIsLoading,
  error,
  setError,
  success,
  setSuccess
}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'consumer' as 'consumer' | 'technician',
    acceptTerms: false
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrengthResult | null>(null);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [signupEmail, setSignupEmail] = useState('');

  // Real-time validation
  useEffect(() => {
    const newErrors: FormErrors = {};
    
    if (touched.name) {
      const nameValidation = validateName(formData.name);
      if (!nameValidation.isValid) {
        newErrors.name = nameValidation.message;
      }
    }
    
    if (touched.email) {
      const emailValidation = validateEmail(formData.email);
      if (!emailValidation.isValid) {
        newErrors.email = emailValidation.message;
      }
    }
    
    if (touched.password) {
      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.message;
      } else {
        setPasswordStrength(checkPasswordStrength(formData.password));
      }
    }
    
    if (touched.confirmPassword) {
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }
    
    if (touched.acceptTerms && !formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions';
    }
    
    setErrors(newErrors);
  }, [formData, touched]);

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check rate limiting
    const rateLimitKey = `signup_${formData.email}`;
    if (RateLimiter.isRateLimited(rateLimitKey, 3, 60 * 60 * 1000)) {
      setError('Too many signup attempts. Please try again in 1 hour.');
      return;
    }
    
    // Mark all fields as touched
    setTouched({
      name: true,
      email: true,
      password: true,
      confirmPassword: true,
      acceptTerms: true
    });
    
    // Validate all fields
    const nameValidation = validateName(formData.name);
    const emailValidation = validateEmail(formData.email);
    const passwordValidation = validatePassword(formData.password);
    
    const newErrors: FormErrors = {};
    if (!nameValidation.isValid) newErrors.name = nameValidation.message;
    if (!emailValidation.isValid) newErrors.email = emailValidation.message;
    if (!passwordValidation.isValid) newErrors.password = passwordValidation.message;
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    if (!formData.acceptTerms) newErrors.acceptTerms = 'You must accept the terms and conditions';
    
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length > 0) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Get reCAPTCHA token if available
      let recaptchaToken = '';
      try {
        recaptchaToken = await RecaptchaService.executeRecaptcha('signup');
      } catch (recaptchaError) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('reCAPTCHA not available:', recaptchaError);
        }
      }

      // Get CSRF token
      const csrfToken = csrfTokenManager.getToken();

      // Sanitize input data
      const sanitizedName = InputSanitizer.sanitizeName(formData.name);
      const sanitizedEmail = InputSanitizer.sanitizeEmail(formData.email);
      
      await onSubmit({
        name: sanitizedName.value,
        email: sanitizedEmail.value,
        password: formData.password, // Don't sanitize password
        confirmPassword: formData.confirmPassword,
        role: formData.role,
        acceptTerms: formData.acceptTerms,
        csrfToken,
        recaptchaToken
      } as any);
      
      setSuccess('Account created successfully! Please verify your email to continue.');
      setSignupEmail(sanitizedEmail.value);
      
      // Show verification modal after a brief delay
      setTimeout(() => {
        setShowVerificationModal(true);
      }, 1000);
      
      // Reset rate limit on successful signup
      RateLimiter.resetRateLimit(rateLimitKey);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    if (!formData.acceptTerms) {
      setError('You must accept the terms and conditions to continue');
      setTouched(prev => ({ ...prev, acceptTerms: true }));
      return;
    }

    setError(null);
    try {
      await authService.signInWithGoogle();
      setSuccess('Google sign-in successful! Redirecting...');
      
      // For Google OAuth, we'll create a mock signup data object
      // The actual user creation is handled by Cognito
      await onSubmit({
        name: '', // Will be populated from Google profile
        email: '', // Will be populated from Google profile
        password: '', // Not needed for OAuth
        confirmPassword: '', // Not needed for OAuth
        role: formData.role, // Use selected role
        acceptTerms: formData.acceptTerms
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed. Please try again.');
    }
  };

  const getPasswordStrengthColor = (strength: PasswordStrength) => {
    switch (strength) {
      case 'weak': return 'bg-red-500';
      case 'fair': return 'bg-yellow-500';
      case 'good': return 'bg-blue-500';
      case 'strong': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      onSubmit={handleSubmit}
      className="space-y-4"
      noValidate
    >
      {/* Error/Success Messages */}
      {error && (
        <div className="rounded-md bg-red-50 p-4" role="alert">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {success && (
        <div className="rounded-md bg-green-50 p-4" role="alert">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
            <div className="ml-3 space-y-2">
              <p className="text-sm text-green-800">{success}</p>
              {formData.email && (
                <EmailVerificationStatus 
                  email={formData.email}
                  onVerified={() => {
                    setSuccess('Email verified! You can now sign in with your credentials.');
                  }}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Name Field */}
      <div>
        <label htmlFor="signup-name" className="block text-sm font-medium text-gray-700">
          Full Name
        </label>
        <div className="mt-1">
          <input
            id="signup-name"
            name="name"
            type="text"
            autoComplete="name"
            required
            className={`block w-full rounded-md border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your full name"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            onBlur={() => handleBlur('name')}
            disabled={isLoading}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'signup-name-error' : undefined}
          />
          {errors.name && (
            <p id="signup-name-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.name}
            </p>
          )}
        </div>
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="signup-email" className="block text-sm font-medium text-gray-700">
          Email Address
        </label>
        <div className="mt-1">
          <input
            id="signup-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className={`block w-full rounded-md border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.email ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            disabled={isLoading}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? 'signup-email-error' : undefined}
          />
          {errors.email && (
            <p id="signup-email-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.email}
            </p>
          )}
        </div>
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <div className="mt-1 relative">
          <input
            id="signup-password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            required
            className={`block w-full rounded-md border px-3 py-2 pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.password ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Create a password"
            value={formData.password}
            onChange={(e) => handleInputChange('password', e.target.value)}
            onBlur={() => handleBlur('password')}
            disabled={isLoading}
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? 'signup-password-error' : 'password-strength'}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isLoading}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeSlashIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            ) : (
              <EyeIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            )}
          </button>
        </div>
        
        {/* Password Strength Indicator */}
        {passwordStrength && formData.password && (
          <div id="password-strength" className="mt-2">
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength.strength)}`}
                  style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium text-gray-600 capitalize">
                {passwordStrength.strength}
              </span>
            </div>
            {passwordStrength.feedback.length > 0 && (
              <ul className="mt-1 text-xs text-gray-600">
                {passwordStrength.feedback.map((feedback, index) => (
                  <li key={index}>• {feedback}</li>
                ))}
              </ul>
            )}
          </div>
        )}
        
        {errors.password && (
          <p id="signup-password-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.password}
          </p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="signup-confirm-password" className="block text-sm font-medium text-gray-700">
          Confirm Password
        </label>
        <div className="mt-1 relative">
          <input
            id="signup-confirm-password"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            required
            className={`block w-full rounded-md border px-3 py-2 pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500 sm:text-sm ${
              errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Confirm your password"
            value={formData.confirmPassword}
            onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
            onBlur={() => handleBlur('confirmPassword')}
            disabled={isLoading}
            aria-invalid={!!errors.confirmPassword}
            aria-describedby={errors.confirmPassword ? 'signup-confirm-password-error' : undefined}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            disabled={isLoading}
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? (
              <EyeSlashIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            ) : (
              <EyeIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            )}
          </button>
          {errors.confirmPassword && (
            <p id="signup-confirm-password-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.confirmPassword}
            </p>
          )}
        </div>
      </div>

      {/* Role Selection */}
      <div>
        <fieldset>
          <legend className="block text-sm font-medium text-gray-700 mb-2">
            I am a:
          </legend>
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                id="role-consumer"
                name="role"
                type="radio"
                value="consumer"
                className="h-4 w-4 text-aqua-600 focus:ring-aqua-500 border-gray-300"
                checked={formData.role === 'consumer'}
                onChange={(e) => handleInputChange('role', e.target.value)}
                disabled={isLoading}
              />
              <label htmlFor="role-consumer" className="ml-2 block text-sm text-gray-900">
                Consumer - Monitor water quality for my home/community
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="role-technician"
                name="role"
                type="radio"
                value="technician"
                className="h-4 w-4 text-aqua-600 focus:ring-aqua-500 border-gray-300"
                checked={formData.role === 'technician'}
                onChange={(e) => handleInputChange('role', e.target.value)}
                disabled={isLoading}
              />
              <label htmlFor="role-technician" className="ml-2 block text-sm text-gray-900">
                Technician - Provide maintenance and repair services
              </label>
            </div>
          </div>
        </fieldset>
      </div>

      {/* Terms and Conditions */}
      <div>
        <div className="flex items-start">
          <input
            id="accept-terms"
            name="acceptTerms"
            type="checkbox"
            className={`h-4 w-4 text-aqua-600 focus:ring-aqua-500 border-gray-300 rounded mt-0.5 ${
              errors.acceptTerms ? 'border-red-300' : ''
            }`}
            checked={formData.acceptTerms}
            onChange={(e) => handleInputChange('acceptTerms', e.target.checked)}
            onBlur={() => handleBlur('acceptTerms')}
            disabled={isLoading}
            aria-invalid={!!errors.acceptTerms}
            aria-describedby={errors.acceptTerms ? 'accept-terms-error' : undefined}
          />
          <label htmlFor="accept-terms" className="ml-2 block text-sm text-gray-900">
            I agree to the{' '}
            <button
              type="button"
              className="text-aqua-600 hover:text-aqua-500 focus:outline-none focus:underline"
              disabled={isLoading}
            >
              Terms of Service
            </button>
            {' '}and{' '}
            <button
              type="button"
              className="text-aqua-600 hover:text-aqua-500 focus:outline-none focus:underline"
              disabled={isLoading}
            >
              Privacy Policy
            </button>
          </label>
        </div>
        {errors.acceptTerms && (
          <p id="accept-terms-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.acceptTerms}
          </p>
        )}
      </div>

      {/* Google OAuth Button */}
      <div>
        <GoogleOAuthButton
          onSignIn={handleGoogleSignIn}
          disabled={isLoading || !formData.acceptTerms}
        />
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or create account with email</span>
        </div>
      </div>

      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={isLoading || Object.keys(errors).length > 0 || !formData.acceptTerms}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating account...
            </>
          ) : (
            'Create Account'
          )}
        </button>
      </div>

      {/* Email Verification Modal */}
      {signupEmail && (
        <EmailVerificationModal
          isOpen={showVerificationModal}
          onClose={() => setShowVerificationModal(false)}
          email={signupEmail}
          onVerified={() => {
            setSuccess('Email verified! You can now sign in with your credentials.');
            setShowVerificationModal(false);
          }}
        />
      )}
    </motion.form>
  );
};