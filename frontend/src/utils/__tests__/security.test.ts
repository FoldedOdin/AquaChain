import { 
  InputSanitizer, 
  RateLimiter, 
  CSPHelper, 
  csrfTokenManager,
  SecurityManager 
} from '../security';

describe('Security Utils', () => {
  describe('InputSanitizer', () => {
    describe('sanitizeEmail', () => {
      it('should sanitize and validate valid email', () => {
        const result = InputSanitizer.sanitizeEmail('test@example.com');
        expect(result.isValid).toBe(true);
        expect(result.value).toBe('test@example.com');
        expect(result.error).toBeUndefined();
      });

      it('should reject invalid email format', () => {
        const result = InputSanitizer.sanitizeEmail('invalid-email');
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Invalid email format');
      });

      it('should reject empty email', () => {
        const result = InputSanitizer.sanitizeEmail('');
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Email is required');
      });

      it('should sanitize HTML in email', () => {
        const result = InputSanitizer.sanitizeEmail('<script>alert("xss")</script>test@example.com');
        expect(result.value).toBe('test@example.com');
      });

      it('should convert email to lowercase', () => {
        const result = InputSanitizer.sanitizeEmail('TEST@EXAMPLE.COM');
        expect(result.value).toBe('test@example.com');
      });
    });

    describe('sanitizeName', () => {
      it('should sanitize and validate valid name', () => {
        const result = InputSanitizer.sanitizeName('John Doe');
        expect(result.isValid).toBe(true);
        expect(result.value).toBe('John Doe');
      });

      it('should reject name that is too short', () => {
        const result = InputSanitizer.sanitizeName('J');
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Name must be at least 2 characters');
      });

      it('should reject name that is too long', () => {
        const longName = 'a'.repeat(51);
        const result = InputSanitizer.sanitizeName(longName);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Name must be less than 50 characters');
      });

      it('should reject name with invalid characters', () => {
        const result = InputSanitizer.sanitizeName('John123');
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Name contains invalid characters');
      });

      it('should allow valid name characters', () => {
        const result = InputSanitizer.sanitizeName("John O'Connor-Smith Jr.");
        expect(result.isValid).toBe(true);
      });
    });

    describe('sanitizePhone', () => {
      it('should validate valid phone number', () => {
        const result = InputSanitizer.sanitizePhone('+1 (555) 123-4567');
        expect(result.isValid).toBe(true);
        expect(result.value).toBe('+1 (555) 123-4567');
      });

      it('should reject invalid phone format', () => {
        const result = InputSanitizer.sanitizePhone('invalid-phone');
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Invalid phone number format');
      });
    });

    describe('sanitizeMessage', () => {
      it('should sanitize and validate message', () => {
        const result = InputSanitizer.sanitizeMessage('Hello world!');
        expect(result.isValid).toBe(true);
        expect(result.value).toBe('Hello world!');
      });

      it('should reject message that is too long', () => {
        const longMessage = 'a'.repeat(1001);
        const result = InputSanitizer.sanitizeMessage(longMessage);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Message must be less than 1000 characters');
      });

      it('should sanitize HTML in message', () => {
        const result = InputSanitizer.sanitizeMessage('<script>alert("xss")</script>Hello');
        expect(result.value).toBe('Hello');
      });
    });
  });

  describe('RateLimiter', () => {
    beforeEach(() => {
      // Clear rate limiter state
      RateLimiter.resetRateLimit('test-key');
    });

    it('should allow requests within limit', () => {
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(false);
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(false);
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(false);
    });

    it('should block requests over limit', () => {
      // Make 5 requests (should all be allowed)
      for (let i = 0; i < 5; i++) {
        expect(RateLimiter.isRateLimited('test-key', 5)).toBe(false);
      }
      
      // 6th request should be blocked
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(true);
    });

    it('should return correct remaining attempts', () => {
      expect(RateLimiter.getRemainingAttempts('test-key', 5)).toBe(5);
      
      RateLimiter.isRateLimited('test-key', 5);
      expect(RateLimiter.getRemainingAttempts('test-key', 5)).toBe(4);
      
      RateLimiter.isRateLimited('test-key', 5);
      expect(RateLimiter.getRemainingAttempts('test-key', 5)).toBe(3);
    });

    it('should reset rate limit', () => {
      // Make 5 requests
      for (let i = 0; i < 5; i++) {
        RateLimiter.isRateLimited('test-key', 5);
      }
      
      // Should be rate limited
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(true);
      
      // Reset and try again
      RateLimiter.resetRateLimit('test-key');
      expect(RateLimiter.isRateLimited('test-key', 5)).toBe(false);
    });
  });

  describe('CSRFTokenManager', () => {
    beforeEach(() => {
      // Clear session storage
      sessionStorage.clear();
      csrfTokenManager.clearToken();
    });

    it('should generate a token', () => {
      const token = csrfTokenManager.generateToken();
      expect(token).toBeDefined();
      expect(typeof token).toBe('string');
      expect(token.length).toBe(64); // 32 bytes * 2 hex chars
    });

    it('should return the same token when called multiple times', () => {
      const token1 = csrfTokenManager.getToken();
      const token2 = csrfTokenManager.getToken();
      expect(token1).toBe(token2);
    });

    it('should validate token correctly', () => {
      const token = csrfTokenManager.getToken();
      expect(csrfTokenManager.validateToken(token)).toBe(true);
      expect(csrfTokenManager.validateToken('invalid-token')).toBe(false);
    });

    it('should persist token in session storage', () => {
      const token = csrfTokenManager.getToken();
      expect(sessionStorage.getItem('csrf_token')).toBe(token);
    });

    it('should clear token', () => {
      csrfTokenManager.getToken();
      expect(sessionStorage.getItem('csrf_token')).toBeTruthy();
      
      csrfTokenManager.clearToken();
      expect(sessionStorage.getItem('csrf_token')).toBeNull();
    });
  });

  describe('CSPHelper', () => {
    it('should generate a nonce', () => {
      const nonce = CSPHelper.generateNonce();
      expect(nonce).toBeDefined();
      expect(typeof nonce).toBe('string');
      expect(nonce.length).toBeGreaterThan(0);
    });

    it('should generate different nonces', () => {
      const nonce1 = CSPHelper.generateNonce();
      const nonce2 = CSPHelper.generateNonce();
      expect(nonce1).not.toBe(nonce2);
    });

    it('should generate CSP header', () => {
      const csp = CSPHelper.getCSPHeader();
      expect(csp).toContain("default-src 'self'");
      expect(csp).toContain("script-src");
      expect(csp).toContain("style-src");
      expect(csp).toContain("object-src 'none'");
    });
  });

  describe('SecurityManager', () => {
    let securityManager: SecurityManager;

    beforeEach(() => {
      securityManager = SecurityManager.getInstance();
    });

    it('should validate and sanitize form data', () => {
      const formData = {
        name: 'John Doe',
        email: 'john@example.com',
        message: 'Hello world!',
        phone: '+1-555-123-4567'
      };

      const result = securityManager.validateFormData(formData);
      
      expect(result.isValid).toBe(true);
      expect(result.sanitized.name).toBe('John Doe');
      expect(result.sanitized.email).toBe('john@example.com');
      expect(result.errors).toEqual({});
    });

    it('should return errors for invalid data', () => {
      const formData = {
        name: 'J', // Too short
        email: 'invalid-email',
        message: ''
      };

      const result = securityManager.validateFormData(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.name).toBe('Name must be at least 2 characters');
      expect(result.errors.email).toBe('Invalid email format');
    });

    it('should sanitize HTML in form data', () => {
      const formData = {
        name: '<script>alert("xss")</script>John',
        email: '<img src=x onerror=alert(1)>test@example.com',
        message: '<b>Hello</b> world!'
      };

      const result = securityManager.validateFormData(formData);
      
      expect(result.sanitized.name).toBe('John');
      expect(result.sanitized.email).toBe('test@example.com');
      expect(result.sanitized.message).toBe('Hello world!');
    });
  });
});