/**
 * Error Handling Components Export
 * Centralized exports for all error handling components and utilities
 */

export { default as OrderingErrorBoundary, withOrderingErrorBoundary } from './OrderingErrorBoundary';
export { default as NetworkErrorHandler, useNetworkError, useRetryableRequest, RetryButton } from './NetworkErrorHandler';
export { 
  default as ErrorNotification, 
  useErrorNotification, 
  InlineError 
} from './ErrorNotificationSystem';

// Re-export utilities
export {
  OrderingError,
  retryWithBackoff,
  makeRetryableRequest,
  logError,
  getUserFriendlyMessage,
  offlineDetector,
  DEFAULT_RETRY_CONFIG
} from '../../utils/errorHandling';

export type {
  RetryConfig,
  ErrorContext,
  EnhancedError
} from '../../utils/errorHandling';

export type {
  ErrorNotificationOptions
} from './ErrorNotificationSystem';