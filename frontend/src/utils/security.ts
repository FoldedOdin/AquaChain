import DOMPurify from 'dompurify';

// CSRF Token Management
class CSRFTokenManager {
  private static instance: CSRFTokenManager;
  private token: string | null = null;
  private tokenExpiry: number | null = null;
  private readonly TOKEN_LIFETIME = 30 * 60 * 1000; // 30 minutes

  private constructor() {}

  public static getInstance(): CSRFTokenManager {
    if (!CSRFTokenManager.instance) {
      CSRFTokenManager.instance = new CSRFTokenManager();
    }
    return CSRFTokenManager.instance;
  }

  /**
   * Generate a new CSRF token
   */
  public generateToken(): string {
    const array = new Uint8Array(32);
    
    // Use crypto.getRandomValues in browser, fallback for Node.js tests
    if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
    } else if (typeof global !== 'undefined' && global.crypto && global.crypto.getRandomValues) {
      global.crypto.getRandomValues(array);
    } else {
      // Fallback for Node.js test environment
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }
    
    this.token = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    this.tokenExpiry = Date.now() + this.TOKEN_LIFETIME;
    
    // Store in sessionStorage for persistence across page reloads
    sessionStorage.setItem('csrf_token', this.token);
    sessionStorage.setItem('csrf_token_expiry', this.tokenExpiry.toString());
    
    return this.token;
  }

  /**
   * Get current CSRF token, generating a new one if needed
   */
  public getToken(): string {
    // Check if we have a valid token in memory
    if (this.token && this.tokenExpiry && Date.now() < this.tokenExpiry) {
      return this.token;
    }

    // Check sessionStorage for existing token
    const storedToken = sessionStorage.getItem('csrf_token');
    const storedExpiry = sessionStorage.getItem('csrf_token_expiry');

    if (storedToken && storedExpiry && Date.now() < parseInt(storedExpiry)) {
      this.token = storedToken;
      this.tokenExpiry = parseInt(storedExpiry);
      return this.token;
    }

    // Generate new token if none exists or expired
    return this.generateToken();
  }

  /**
   * Validate CSRF token
   */
  public validateToken(token: string): boolean {
    const currentToken = this.getToken();
    return token === currentToken;
  }

  /**
   * Clear CSRF token
   */
  public clearToken(): void {
    this.token = null;
    this.tokenExpiry = null;
    sessionStorage.removeItem('csrf_token');
    sessionStorage.removeItem('csrf_token_expiry');
  }
}

// Input Sanitization and Validation
export class InputSanitizer {
  private static readonly EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private static readonly PHONE_REGEX = /^\+?[\d\s\-\(\)]+$/;
  private static readonly NAME_REGEX = /^[a-zA-Z\s\-'\.]+$/;
  private static readonly ALPHANUMERIC_REGEX = /^[a-zA-Z0-9\s]+$/;

  /**
   * Sanitize HTML content
   */
  public static sanitizeHTML(input: string): string {
    return DOMPurify.sanitize(input, {
      ALLOWED_TAGS: [],
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true
    });
  }

  /**
   * Sanitize and validate email
   */
  public static sanitizeEmail(email: string): { value: string; isValid: boolean; error?: string } {
    const sanitized = this.sanitizeHTML(email.trim().toLowerCase());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Email is required' };
    }

    if (sanitized.length > 254) {
      return { value: sanitized, isValid: false, error: 'Email is too long' };
    }

    if (!this.EMAIL_REGEX.test(sanitized)) {
      return { value: sanitized, isValid: false, error: 'Invalid email format' };
    }

    return { value: sanitized, isValid: true };
  }

  /**
   * Sanitize and validate name
   */
  public static sanitizeName(name: string): { value: string; isValid: boolean; error?: string } {
    const sanitized = this.sanitizeHTML(name.trim());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Name is required' };
    }

    if (sanitized.length < 2) {
      return { value: sanitized, isValid: false, error: 'Name must be at least 2 characters' };
    }

    if (sanitized.length > 50) {
      return { value: sanitized, isValid: false, error: 'Name must be less than 50 characters' };
    }

    if (!this.NAME_REGEX.test(sanitized)) {
      return { value: sanitized, isValid: false, error: 'Name contains invalid characters' };
    }

    return { value: sanitized, isValid: true };
  }

  /**
   * Sanitize and validate phone number
   */
  public static sanitizePhone(phone: string): { value: string; isValid: boolean; error?: string } {
    const sanitized = this.sanitizeHTML(phone.trim());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Phone number is required' };
    }

    if (!this.PHONE_REGEX.test(sanitized)) {
      return { value: sanitized, isValid: false, error: 'Invalid phone number format' };
    }

    return { value: sanitized, isValid: true };
  }

  /**
   * Sanitize message/textarea content
   */
  public static sanitizeMessage(message: string): { value: string; isValid: boolean; error?: string } {
    const sanitized = this.sanitizeHTML(message.trim());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Message is required' };
    }

    if (sanitized.length > 1000) {
      return { value: sanitized, isValid: false, error: 'Message must be less than 1000 characters' };
    }

    return { value: sanitized, isValid: true };
  }

  /**
   * Sanitize general text input
   */
  public static sanitizeText(text: string, maxLength: number = 255): { value: string; isValid: boolean; error?: string } {
    const sanitized = this.sanitizeHTML(text.trim());
    
    if (sanitized.length > maxLength) {
      return { value: sanitized, isValid: false, error: `Text must be less than ${maxLength} characters` };
    }

    return { value: sanitized, isValid: true };
  }

  /**
   * Remove potentially dangerous characters for SQL injection prevention
   */
  public static sanitizeForDatabase(input: string): string {
    return input
      .replace(/['"\\;]/g, '') // Remove quotes and semicolons
      .replace(/--/g, '') // Remove SQL comments
      .replace(/\/\*/g, '') // Remove block comment start
      .replace(/\*\//g, '') // Remove block comment end
      .trim();
  }
}

// Content Security Policy Helper
export class CSPHelper {
  /**
   * Generate CSP nonce for inline scripts/styles
   */
  public static generateNonce(): string {
    const array = new Uint8Array(16);
    
    // Use crypto.getRandomValues in browser, fallback for Node.js tests
    if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
    } else if (typeof global !== 'undefined' && global.crypto && global.crypto.getRandomValues) {
      global.crypto.getRandomValues(array);
    } else {
      // Fallback for Node.js test environment
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }
    
    return btoa(String.fromCharCode.apply(null, Array.from(array)));
  }

  /**
   * Get CSP header value
   */
  public static getCSPHeader(): string {
    const nonce = this.generateNonce();
    
    return [
      "default-src 'self'",
      `script-src 'self' 'nonce-${nonce}' https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://cognito-idp.*.amazonaws.com`,
      `style-src 'self' 'nonce-${nonce}' https://fonts.googleapis.com`,
      "img-src 'self' data: https://*.amazonaws.com https://www.google.com/recaptcha/",
      "connect-src 'self' https://*.amazonaws.com https://www.google-analytics.com",
      "font-src 'self' https://fonts.gstatic.com",
      "frame-src https://www.google.com/recaptcha/",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'"
    ].join('; ');
  }
}

// Rate Limiting (Client-side)
export class RateLimiter {
  private static attempts: Map<string, { count: number; resetTime: number }> = new Map();

  /**
   * Check if action is rate limited
   */
  public static isRateLimited(key: string, maxAttempts: number = 5, windowMs: number = 15 * 60 * 1000): boolean {
    const now = Date.now();
    const attempt = this.attempts.get(key);

    if (!attempt || now > attempt.resetTime) {
      // Reset or create new attempt record
      this.attempts.set(key, { count: 1, resetTime: now + windowMs });
      return false;
    }

    if (attempt.count >= maxAttempts) {
      return true;
    }

    // Increment attempt count
    attempt.count++;
    return false;
  }

  /**
   * Reset rate limit for a key
   */
  public static resetRateLimit(key: string): void {
    this.attempts.delete(key);
  }

  /**
   * Get remaining attempts
   */
  public static getRemainingAttempts(key: string, maxAttempts: number = 5): number {
    const attempt = this.attempts.get(key);
    if (!attempt || Date.now() > attempt.resetTime) {
      return maxAttempts;
    }
    return Math.max(0, maxAttempts - attempt.count);
  }
}

// reCAPTCHA Integration
export class RecaptchaService {
  private static siteKey: string = process.env.REACT_APP_RECAPTCHA_SITE_KEY || '';
  private static isLoaded: boolean = false;

  /**
   * Load reCAPTCHA script
   */
  public static async loadRecaptcha(): Promise<void> {
    if (this.isLoaded || !this.siteKey) {
      return;
    }

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `https://www.google.com/recaptcha/api.js?render=${this.siteKey}`;
      script.async = true;
      script.defer = true;
      
      script.onload = () => {
        this.isLoaded = true;
        resolve();
      };
      
      script.onerror = () => {
        reject(new Error('Failed to load reCAPTCHA'));
      };
      
      document.head.appendChild(script);
    });
  }

  /**
   * Execute reCAPTCHA and get token
   */
  public static async executeRecaptcha(action: string): Promise<string> {
    if (!this.isLoaded || !this.siteKey) {
      throw new Error('reCAPTCHA not loaded or site key not configured');
    }

    return new Promise((resolve, reject) => {
      (window as any).grecaptcha.ready(() => {
        (window as any).grecaptcha.execute(this.siteKey, { action })
          .then((token: string) => resolve(token))
          .catch((error: any) => reject(error));
      });
    });
  }

  /**
   * Verify reCAPTCHA token (client-side validation)
   */
  public static async verifyRecaptcha(token: string, action: string): Promise<boolean> {
    try {
      // This would typically be done on the server-side
      // For client-side, we can only do basic validation
      return !!(token && token.length > 0);
    } catch (error) {
      return false;
    }
  }
}

// Security Headers Helper
export class SecurityHeaders {
  /**
   * Set security headers (for development/testing)
   */
  public static setSecurityHeaders(): void {
    // These would typically be set by the server
    // This is for development/testing purposes only
    
    if (process.env.NODE_ENV === 'development') {
      console.log('Security Headers (would be set by server):');
      console.log('X-Content-Type-Options: nosniff');
      console.log('X-Frame-Options: DENY');
      console.log('X-XSS-Protection: 1; mode=block');
      console.log('Referrer-Policy: strict-origin-when-cross-origin');
      console.log('Permissions-Policy: geolocation=(), microphone=(), camera=()');
      console.log('Content-Security-Policy:', CSPHelper.getCSPHeader());
    }
  }
}

// Export singleton instances
export const csrfTokenManager = CSRFTokenManager.getInstance();

// Main Security Manager
export class SecurityManager {
  private static instance: SecurityManager;
  
  private constructor() {
    this.initialize();
  }

  public static getInstance(): SecurityManager {
    if (!SecurityManager.instance) {
      SecurityManager.instance = new SecurityManager();
    }
    return SecurityManager.instance;
  }

  private initialize(): void {
    // Initialize security features
    SecurityHeaders.setSecurityHeaders();
    
    // Load reCAPTCHA if configured
    if (process.env.REACT_APP_RECAPTCHA_SITE_KEY) {
      RecaptchaService.loadRecaptcha().catch(console.warn);
    }
  }

  /**
   * Validate and sanitize form data
   */
  public validateFormData(data: Record<string, any>): { 
    sanitized: Record<string, any>; 
    errors: Record<string, string>;
    isValid: boolean;
  } {
    const sanitized: Record<string, any> = {};
    const errors: Record<string, string> = {};

    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'string') {
        let result;
        
        switch (key) {
          case 'email':
            result = InputSanitizer.sanitizeEmail(value);
            break;
          case 'name':
          case 'firstName':
          case 'lastName':
            result = InputSanitizer.sanitizeName(value);
            break;
          case 'phone':
            result = InputSanitizer.sanitizePhone(value);
            break;
          case 'message':
          case 'description':
            result = InputSanitizer.sanitizeMessage(value);
            break;
          default:
            result = InputSanitizer.sanitizeText(value);
        }
        
        sanitized[key] = result.value;
        if (!result.isValid && result.error) {
          errors[key] = result.error;
        }
      } else {
        sanitized[key] = value;
      }
    }

    return {
      sanitized,
      errors,
      isValid: Object.keys(errors).length === 0
    };
  }

  /**
   * Create secure form submission with CSRF protection
   */
  public async secureFormSubmit(
    url: string, 
    data: Record<string, any>, 
    options: RequestInit = {}
  ): Promise<Response> {
    // Validate and sanitize data
    const { sanitized, errors, isValid } = this.validateFormData(data);
    
    if (!isValid) {
      throw new Error(`Form validation failed: ${Object.values(errors).join(', ')}`);
    }

    // Get CSRF token
    const csrfToken = csrfTokenManager.getToken();

    // Get reCAPTCHA token if available
    let recaptchaToken = '';
    try {
      recaptchaToken = await RecaptchaService.executeRecaptcha('form_submit');
    } catch (error) {
      console.warn('reCAPTCHA not available:', error);
    }

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
      ...(recaptchaToken && { 'X-Recaptcha-Token': recaptchaToken }),
      ...options.headers
    };

    // Submit form
    return fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(sanitized),
      credentials: 'same-origin',
      ...options
    });
  }
}

// Export singleton instance
export const securityManager = SecurityManager.getInstance();

// Convenience functions for backward compatibility
export const sanitizeInput = (input: string, type: 'email' | 'name' | 'message' | 'text' = 'text'): string => {
  switch (type) {
    case 'email':
      return InputSanitizer.sanitizeEmail(input).value;
    case 'name':
      return InputSanitizer.sanitizeName(input).value;
    case 'message':
      return InputSanitizer.sanitizeMessage(input).value;
    default:
      return InputSanitizer.sanitizeText(input).value;
  }
};

export const validateEmail = (email: string): boolean => {
  return InputSanitizer.sanitizeEmail(email).isValid;
};

export const validatePhone = (phone: string): boolean => {
  return InputSanitizer.sanitizePhone(phone).isValid;
};