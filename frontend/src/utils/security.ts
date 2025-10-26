/**
 * Security utilities for input validation, rate limiting, and CSRF protection
 */

import DOMPurify from 'dompurify';

// Input sanitization results
interface SanitizationResult {
  value: string;
  isValid: boolean;
  error?: string;
}

// Rate limiting storage
const rateLimitStore = new Map<string, { count: number; firstAttempt: number }>();

export class InputSanitizer {
  /**
   * Sanitize and validate email addresses
   */
  static sanitizeEmail(email: string): SanitizationResult {
    const sanitized = DOMPurify.sanitize(email.trim().toLowerCase());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Email is required' };
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(sanitized)) {
      return { value: sanitized, isValid: false, error: 'Please enter a valid email address' };
    }
    
    return { value: sanitized, isValid: true };
  }

  /**
   * Sanitize and validate names
   */
  static sanitizeName(name: string): SanitizationResult {
    const sanitized = DOMPurify.sanitize(name.trim());
    
    if (!sanitized) {
      return { value: '', isValid: false, error: 'Name is required' };
    }
    
    if (sanitized.length < 2) {
      return { value: sanitized, isValid: false, error: 'Name must be at least 2 characters long' };
    }
    
    if (sanitized.length > 50) {
      return { value: sanitized, isValid: false, error: 'Name must be less than 50 characters' };
    }
    
    // Only allow letters, spaces, hyphens, and apostrophes
    const nameRegex = /^[a-zA-Z\s\-']+$/;
    if (!nameRegex.test(sanitized)) {
      return { value: sanitized, isValid: false, error: 'Name can only contain letters, spaces, hyphens, and apostrophes' };
    }
    
    return { value: sanitized, isValid: true };
  }
}

export class RateLimiter {
  /**
   * Check if a key is rate limited
   */
  static isRateLimited(key: string, maxAttempts: number, windowMs: number): boolean {
    const now = Date.now();
    const record = rateLimitStore.get(key);
    
    if (!record) {
      rateLimitStore.set(key, { count: 1, firstAttempt: now });
      return false;
    }
    
    // Check if window has expired
    if (now - record.firstAttempt > windowMs) {
      rateLimitStore.set(key, { count: 1, firstAttempt: now });
      return false;
    }
    
    // Increment count
    record.count++;
    
    return record.count > maxAttempts;
  }

  /**
   * Reset rate limit for a key
   */
  static resetRateLimit(key: string): void {
    rateLimitStore.delete(key);
  }
}

export class RecaptchaService {
  private static isLoaded = false;
  private static loadPromise: Promise<void> | null = null;

  /**
   * Load reCAPTCHA script
   */
  private static loadRecaptchaScript(): Promise<void> {
    if (this.loadPromise) {
      return this.loadPromise;
    }

    this.loadPromise = new Promise((resolve, reject) => {
      if (this.isLoaded || typeof (window as any).grecaptcha !== 'undefined') {
        this.isLoaded = true;
        resolve();
        return;
      }

      const siteKey = process.env.REACT_APP_RECAPTCHA_SITE_KEY;
      if (!siteKey) {
        reject(new Error('reCAPTCHA site key not configured'));
        return;
      }

      const script = document.createElement('script');
      script.src = `https://www.google.com/recaptcha/api.js?render=${siteKey}`;
      script.async = true;
      script.defer = true;

      script.onload = () => {
        this.isLoaded = true;
        resolve();
      };

      script.onerror = () => {
        reject(new Error('Failed to load reCAPTCHA script'));
      };

      document.head.appendChild(script);
    });

    return this.loadPromise;
  }

  /**
   * Execute reCAPTCHA v3
   */
  static async executeRecaptcha(action: string): Promise<string> {
    // Development mode - return mock token
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEV] reCAPTCHA mock token for action: ${action}`);
      return 'dev-recaptcha-token-' + Date.now();
    }

    // Production mode - use real reCAPTCHA
    const siteKey = process.env.REACT_APP_RECAPTCHA_SITE_KEY;
    if (!siteKey) {
      throw new Error('reCAPTCHA not configured. Set REACT_APP_RECAPTCHA_SITE_KEY in environment.');
    }

    try {
      // Load reCAPTCHA script if not already loaded
      await this.loadRecaptchaScript();

      // Execute reCAPTCHA
      return new Promise((resolve, reject) => {
        const grecaptcha = (window as any).grecaptcha;
        
        if (!grecaptcha || !grecaptcha.ready) {
          reject(new Error('reCAPTCHA not ready'));
          return;
        }

        grecaptcha.ready(() => {
          grecaptcha
            .execute(siteKey, { action })
            .then((token: string) => {
              if (!token) {
                reject(new Error('reCAPTCHA returned empty token'));
                return;
              }
              resolve(token);
            })
            .catch((error: Error) => {
              reject(new Error(`reCAPTCHA execution failed: ${error.message}`));
            });
        });
      });
    } catch (error) {
      console.error('reCAPTCHA error:', error);
      throw error;
    }
  }

  /**
   * Verify reCAPTCHA token on backend
   */
  static async verifyToken(token: string, action: string): Promise<boolean> {
    try {
      const response = await fetch('/api/auth/verify-recaptcha', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, action }),
      });

      if (!response.ok) {
        throw new Error('reCAPTCHA verification failed');
      }

      const result = await response.json();
      return result.success && result.score >= 0.5; // Threshold for v3
    } catch (error) {
      console.error('reCAPTCHA verification error:', error);
      return false;
    }
  }

  /**
   * Reset reCAPTCHA (for v2 checkbox)
   */
  static reset(): void {
    const grecaptcha = (window as any).grecaptcha;
    if (grecaptcha && grecaptcha.reset) {
      grecaptcha.reset();
    }
  }
}

export class CSRFTokenManager {
  private token: string | null = null;

  /**
   * Get CSRF token
   */
  getToken(): string {
    if (!this.token) {
      this.token = this.generateToken();
    }
    return this.token;
  }

  /**
   * Generate new CSRF token
   */
  private generateToken(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Refresh token
   */
  refreshToken(): string {
    this.token = this.generateToken();
    return this.token;
  }
}

// Export singleton instance
export const csrfTokenManager = new CSRFTokenManager();

/**
 * Validate email address format
 * @param email - Email address to validate
 * @returns true if valid, false otherwise
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate phone number format
 * @param phone - Phone number to validate
 * @returns true if valid, false otherwise
 */
export function validatePhone(phone: string): boolean {
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  // Check if it's 10 or 11 digits (with or without country code)
  return cleaned.length >= 10 && cleaned.length <= 11;
}

/**
 * Sanitize user input to prevent XSS
 * @param input - User input string
 * @returns Sanitized string
 */
export function sanitizeInput(input: string): string {
  const result = InputSanitizer.sanitizeName(input);
  return result.value;
}
