/**
 * Enhanced Error Handling Utilities
 * Provides comprehensive error handling for the Enhanced Consumer Ordering System
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryCondition?: (error: any) => boolean;
}

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  orderId?: string;
  timestamp: Date;
  userAgent: string;
  url: string;
}

export interface EnhancedError extends Error {
  code?: string;
  status?: number;
  context?: ErrorContext;
  retryable?: boolean;
  userMessage?: string;
}

/**
 * Default retry configuration for network operations
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  retryCondition: (error: any) => {
    // Retry on network errors, timeouts, and 5xx server errors
    return (
      error.name === 'NetworkError' ||
      error.name === 'TimeoutError' ||
      (error.status >= 500 && error.status < 600) ||
      error.code === 'NETWORK_ERROR' ||
      error.code === 'TIMEOUT'
    );
  }
};

/**
 * Enhanced error class with additional context and retry information
 */
export class OrderingError extends Error implements EnhancedError {
  public code?: string;
  public status?: number;
  public context?: ErrorContext;
  public retryable?: boolean;
  public userMessage?: string;

  constructor(
    message: string,
    options: {
      code?: string;
      status?: number;
      context?: Partial<ErrorContext>;
      retryable?: boolean;
      userMessage?: string;
      cause?: Error;
    } = {}
  ) {
    super(message);
    this.name = 'OrderingError';
    this.code = options.code;
    this.status = options.status;
    this.retryable = options.retryable ?? false;
    this.userMessage = options.userMessage || this.getDefaultUserMessage();
    
    this.context = {
      timestamp: new Date(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...options.context
    };

    if (options.cause) {
      this.cause = options.cause;
    }
  }

  private getDefaultUserMessage(): string {
    switch (this.code) {
      case 'PAYMENT_FAILED':
        return 'Payment processing failed. Please try again or use a different payment method.';
      case 'NETWORK_ERROR':
        return 'Network connection issue. Please check your internet connection and try again.';
      case 'TIMEOUT':
        return 'The request timed out. Please try again.';
      case 'ORDER_CREATION_FAILED':
        return 'Failed to create order. Please try again.';
      case 'TECHNICIAN_ASSIGNMENT_FAILED':
        return 'Unable to assign technician. Please try again later.';
      case 'VALIDATION_ERROR':
        return 'Please check your input and try again.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
  let lastError: any;

  for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // Don't retry if this is the last attempt
      if (attempt === finalConfig.maxRetries) {
        break;
      }

      // Check if error is retryable
      if (finalConfig.retryCondition && !finalConfig.retryCondition(error)) {
        break;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        finalConfig.baseDelay * Math.pow(finalConfig.backoffMultiplier, attempt),
        finalConfig.maxDelay
      );

      console.warn(`Operation failed (attempt ${attempt + 1}/${finalConfig.maxRetries + 1}), retrying in ${delay}ms:`, error);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  // If we get here, all retries failed
  throw new OrderingError(
    `Operation failed after ${finalConfig.maxRetries + 1} attempts`,
    {
      code: 'MAX_RETRIES_EXCEEDED',
      retryable: false,
      userMessage: 'The operation failed multiple times. Please try again later.',
      cause: lastError
    }
  );
}

/**
 * Network request wrapper with retry logic
 */
export async function makeRetryableRequest<T>(
  requestFn: () => Promise<T>,
  context: Partial<ErrorContext> = {},
  retryConfig?: Partial<RetryConfig>
): Promise<T> {
  return retryWithBackoff(async () => {
    try {
      return await requestFn();
    } catch (error: any) {
      // Enhance error with context
      const enhancedError = new OrderingError(
        error.message || 'Network request failed',
        {
          code: getErrorCode(error),
          status: error.status,
          context,
          retryable: isRetryableError(error),
          cause: error
        }
      );

      throw enhancedError;
    }
  }, retryConfig);
}

/**
 * Determine error code from various error types
 */
function getErrorCode(error: any): string {
  if (error.code) return error.code;
  if (error.name === 'NetworkError') return 'NETWORK_ERROR';
  if (error.name === 'TimeoutError') return 'TIMEOUT';
  if (error.status >= 400 && error.status < 500) return 'CLIENT_ERROR';
  if (error.status >= 500) return 'SERVER_ERROR';
  return 'UNKNOWN_ERROR';
}

/**
 * Check if an error is retryable
 */
function isRetryableError(error: any): boolean {
  // Network errors are retryable
  if (error.name === 'NetworkError' || error.name === 'TimeoutError') {
    return true;
  }

  // 5xx server errors are retryable
  if (error.status >= 500 && error.status < 600) {
    return true;
  }

  // Specific error codes that are retryable
  const retryableCodes = ['NETWORK_ERROR', 'TIMEOUT', 'RATE_LIMITED'];
  if (retryableCodes.includes(error.code)) {
    return true;
  }

  // 4xx client errors are generally not retryable (except for specific cases)
  if (error.status >= 400 && error.status < 500) {
    // 408 Request Timeout and 429 Too Many Requests are retryable
    return error.status === 408 || error.status === 429;
  }

  return false;
}

/**
 * Error logging utility
 */
export function logError(error: EnhancedError | Error, context?: Partial<ErrorContext>): void {
  const errorData = {
    message: error.message,
    name: error.name,
    stack: error.stack,
    ...(error instanceof OrderingError && {
      code: error.code,
      status: error.status,
      retryable: error.retryable,
      userMessage: error.userMessage,
      context: { ...error.context, ...context }
    })
  };

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Enhanced Ordering System Error:', errorData);
  }

  // In production, send to error tracking service
  if (process.env.NODE_ENV === 'production') {
    // Example: Send to Sentry, CloudWatch, or other error tracking service
    // Sentry.captureException(error, { extra: errorData });
  }
}

/**
 * Create user-friendly error message from technical error
 */
export function getUserFriendlyMessage(error: any): string {
  if (error instanceof OrderingError && error.userMessage) {
    return error.userMessage;
  }

  // Map common error patterns to user-friendly messages
  const message = error.message?.toLowerCase() || '';

  if (message.includes('network') || message.includes('fetch')) {
    return 'Network connection issue. Please check your internet connection and try again.';
  }

  if (message.includes('timeout')) {
    return 'The request timed out. Please try again.';
  }

  if (message.includes('payment')) {
    return 'Payment processing failed. Please try again or use a different payment method.';
  }

  if (message.includes('validation') || message.includes('invalid')) {
    return 'Please check your input and try again.';
  }

  if (error.status === 401) {
    return 'Your session has expired. Please log in again.';
  }

  if (error.status === 403) {
    return 'You do not have permission to perform this action.';
  }

  if (error.status === 404) {
    return 'The requested resource was not found.';
  }

  if (error.status >= 500) {
    return 'A server error occurred. Please try again later.';
  }

  return 'An unexpected error occurred. Please try again.';
}

/**
 * Offline detection utility
 */
export class OfflineDetector {
  private listeners: Set<(isOnline: boolean) => void> = new Set();
  private _isOnline: boolean = navigator.onLine;

  constructor() {
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  private handleOnline = () => {
    this._isOnline = true;
    this.notifyListeners(true);
  };

  private handleOffline = () => {
    this._isOnline = false;
    this.notifyListeners(false);
  };

  private notifyListeners(isOnline: boolean) {
    this.listeners.forEach(listener => listener(isOnline));
  }

  public get isOnline(): boolean {
    return this._isOnline;
  }

  public addListener(listener: (isOnline: boolean) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  public destroy(): void {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    this.listeners.clear();
  }
}

// Global offline detector instance
export const offlineDetector = new OfflineDetector();