/**
 * Error Notification System
 * Enhanced notification system specifically for ordering errors
 * Requirements: 6.1, 6.2, 6.4, 6.5
 */

import React, { useCallback } from 'react';
import { useNotifications } from '../../contexts/NotificationContext';
import { OrderingError, getUserFriendlyMessage } from '../../utils/errorHandling';

export interface ErrorNotificationOptions {
  showRetry?: boolean;
  onRetry?: () => void;
  showDetails?: boolean;
  persistent?: boolean;
  context?: {
    orderId?: string;
    component?: string;
    action?: string;
  };
}

/**
 * Hook for showing error notifications with enhanced features
 */
export const useErrorNotification = () => {
  const { addNotification } = useNotifications();

  const showErrorNotification = useCallback((
    error: Error | OrderingError,
    options: ErrorNotificationOptions = {}
  ) => {
    const {
      showRetry = false,
      onRetry,
      showDetails = false,
      persistent = false,
      context
    } = options;

    const isOrderingError = error instanceof OrderingError;
    const userMessage = getUserFriendlyMessage(error);
    
    // Determine notification type based on error
    let notificationType: 'error' | 'warning' = 'error';
    if (isOrderingError && error.retryable) {
      notificationType = 'warning';
    }

    // Create notification title
    let title = 'Error';
    if (isOrderingError) {
      switch (error.code) {
        case 'PAYMENT_FAILED':
          title = 'Payment Failed';
          break;
        case 'ORDER_CREATION_FAILED':
          title = 'Order Creation Failed';
          break;
        case 'NETWORK_ERROR':
          title = 'Connection Error';
          break;
        case 'TIMEOUT':
          title = 'Request Timeout';
          break;
        case 'VALIDATION_ERROR':
          title = 'Validation Error';
          break;
        default:
          title = 'Error';
      }
    }

    // Build notification message
    let message = userMessage;
    
    // Add context information
    if (context?.orderId) {
      message += ` (Order: ${context.orderId})`;
    }

    // Add retry suggestion for retryable errors
    if (isOrderingError && error.retryable && !showRetry) {
      message += ' Please try again.';
    }

    // Add error details in development
    if (showDetails && process.env.NODE_ENV === 'development') {
      message += `\n\nTechnical details: ${error.message}`;
      if (isOrderingError && error.code) {
        message += ` (Code: ${error.code})`;
      }
    }

    addNotification({
      type: notificationType,
      title,
      message,
      duration: persistent ? 0 : (notificationType === 'error' ? 8000 : 5000)
    });

    // Log error for debugging
    console.error('Error notification shown:', {
      error: error.message,
      code: isOrderingError ? error.code : undefined,
      context,
      userMessage
    });
  }, [addNotification]);

  const showPaymentError = useCallback((
    error: Error,
    options: Omit<ErrorNotificationOptions, 'context'> & { orderId?: string } = {}
  ) => {
    const { orderId, ...restOptions } = options;
    showErrorNotification(error, {
      ...restOptions,
      context: {
        component: 'PaymentSystem',
        action: 'payment_processing',
        orderId
      }
    });
  }, [showErrorNotification]);

  const showOrderError = useCallback((
    error: Error,
    options: Omit<ErrorNotificationOptions, 'context'> & { orderId?: string } = {}
  ) => {
    const { orderId, ...restOptions } = options;
    showErrorNotification(error, {
      ...restOptions,
      context: {
        component: 'OrderSystem',
        action: 'order_management',
        orderId
      }
    });
  }, [showErrorNotification]);

  const showNetworkError = useCallback((
    error: Error,
    options: ErrorNotificationOptions = {}
  ) => {
    showErrorNotification(error, {
      ...options,
      showRetry: true,
      context: {
        component: 'NetworkLayer',
        action: 'network_request',
        ...options.context
      }
    });
  }, [showErrorNotification]);

  return {
    showErrorNotification,
    showPaymentError,
    showOrderError,
    showNetworkError
  };
};

/**
 * Error notification component with action buttons
 */
interface ErrorNotificationProps {
  error: Error | OrderingError;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  className?: string;
}

export const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  error,
  onRetry,
  onDismiss,
  showDetails = false,
  className = ''
}) => {
  const isOrderingError = error instanceof OrderingError;
  const userMessage = getUserFriendlyMessage(error);
  const isRetryable = isOrderingError ? error.retryable : true;

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.964-1.333-2.732 0L3.732 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            {isOrderingError && error.code === 'PAYMENT_FAILED' 
              ? 'Payment Failed'
              : isOrderingError && error.code === 'ORDER_CREATION_FAILED'
              ? 'Order Creation Failed'
              : 'Error Occurred'
            }
          </h3>
          
          <div className="mt-2 text-sm text-red-700">
            <p>{userMessage}</p>
            
            {/* Show technical details in development */}
            {showDetails && process.env.NODE_ENV === 'development' && (
              <details className="mt-2">
                <summary className="cursor-pointer font-medium">Technical Details</summary>
                <div className="mt-1 bg-red-100 rounded p-2 font-mono text-xs">
                  <p><strong>Message:</strong> {error.message}</p>
                  {isOrderingError && (
                    <>
                      <p><strong>Code:</strong> {error.code}</p>
                      <p><strong>Retryable:</strong> {error.retryable ? 'Yes' : 'No'}</p>
                      {error.context && (
                        <p><strong>Context:</strong> {JSON.stringify(error.context, null, 2)}</p>
                      )}
                    </>
                  )}
                </div>
              </details>
            )}
          </div>
          
          {/* Action buttons */}
          <div className="mt-4 flex space-x-3">
            {isRetryable && onRetry && (
              <button
                onClick={onRetry}
                className="bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium px-3 py-1 rounded-md transition-colors"
              >
                Try Again
              </button>
            )}
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium px-3 py-1 rounded-md transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
        
        {/* Close button */}
        {onDismiss && (
          <div className="flex-shrink-0 ml-4">
            <button
              onClick={onDismiss}
              className="bg-red-50 rounded-md p-2 inline-flex items-center justify-center text-red-400 hover:text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-red-500"
            >
              <span className="sr-only">Close</span>
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Inline error display component for forms and inputs
 */
interface InlineErrorProps {
  error?: Error | OrderingError | string | null;
  className?: string;
}

export const InlineError: React.FC<InlineErrorProps> = ({ error, className = '' }) => {
  if (!error) return null;

  const message = typeof error === 'string' 
    ? error 
    : getUserFriendlyMessage(error);

  return (
    <div className={`flex items-center mt-1 text-sm text-red-600 ${className}`}>
      <svg className="h-4 w-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.964-1.333-2.732 0L3.732 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{message}</span>
    </div>
  );
};

export default ErrorNotification;