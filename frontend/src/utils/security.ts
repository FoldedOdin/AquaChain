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
  /**
   * Execute reCAPTCHA (mock implementation for development)
   */
  static async executeRecaptcha(action: string): Promise<string> {
    if (process.env.NODE_ENV === 'development') {
      // Mock token for development
      return 'dev-recaptcha-token-' + Date.now();
    }
    
    // In production, would integrate with Google reCAPTCHA
    const siteKey = process.env.REACT_APP_RECAPTCHA_SITE_KEY;
    if (!siteKey) {
      throw new Error('reCAPTCHA not configured');
    }
    
    // Mock implementation - replace with actual reCAPTCHA integration
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        resolve('mock-recaptcha-token-' + Date.now());
      }, 100);
    });
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