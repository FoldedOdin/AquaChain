/**
 * Network Error Handler Component
 * Provides network error handling with retry mechanisms and offline detection
 * Requirements: 6.3, 6.4, 6.5
 */

import React, { useState, useEffect, useCallback, ReactNode } from 'react';
import { offlineDetector, retryWithBackoff, OrderingError } from '../../utils/errorHandling';
import { useNotifications } from '../../contexts/NotificationContext';

interface NetworkErrorHandlerProps {
  children: ReactNode;
  onNetworkError?: (error: Error) => void;
  showOfflineIndicator?: boolean;
}

export const NetworkErrorHandler: React.FC<NetworkErrorHandlerProps> = ({
  children,
  onNetworkError,
  showOfflineIndicator = true
}) => {
  const [isOnline, setIsOnline] = useState(offlineDetector.isOnline);
  const [showOfflineBanner, setShowOfflineBanner] = useState(false);
  const { addNotification } = useNotifications();

  useEffect(() => {
    const unsubscribe = offlineDetector.addListener((online) => {
      setIsOnline(online);
      
      if (!online) {
        setShowOfflineBanner(true);
        addNotification({
          type: 'warning',
          title: 'Connection Lost',
          message: 'You are currently offline. Some features may not work properly.',
          duration: 0 // Don't auto-dismiss
        });
      } else {
        setShowOfflineBanner(false);
        addNotification({
          type: 'success',
          title: 'Connection Restored',
          message: 'You are back online. All features are now available.',
          duration: 3000
        });
      }
    });

    return unsubscribe;
  }, [addNotification]);

  const handleNetworkError = useCallback((error: Error) => {
    if (onNetworkError) {
      onNetworkError(error);
    }

    // Show user-friendly notification
    addNotification({
      type: 'error',
      title: 'Network Error',
      message: 'Unable to connect to the server. Please check your internet connection.',
      duration: 8000
    });
  }, [onNetworkError, addNotification]);

  return (
    <div className="relative">
      {/* Offline Banner */}
      {showOfflineIndicator && showOfflineBanner && (
        <OfflineBanner onDismiss={() => setShowOfflineBanner(false)} />
      )}
      
      {/* Network Context Provider */}
      <NetworkContext.Provider value={{
        isOnline,
        handleNetworkError,
        retryWithBackoff
      }}>
        {children}
      </NetworkContext.Provider>
    </div>
  );
};

interface OfflineBannerProps {
  onDismiss: () => void;
}

const OfflineBanner: React.FC<OfflineBannerProps> = ({ onDismiss }) => {
  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
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
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <span className="font-medium">You're offline.</span> Some features may not work properly until your connection is restored.
            </p>
          </div>
        </div>
        <div className="flex-shrink-0">
          <button
            onClick={onDismiss}
            className="bg-yellow-50 rounded-md p-2 inline-flex items-center justify-center text-yellow-400 hover:text-yellow-500 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-yellow-500"
          >
            <span className="sr-only">Dismiss</span>
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

// Network Context for child components
interface NetworkContextType {
  isOnline: boolean;
  handleNetworkError: (error: Error) => void;
  retryWithBackoff: typeof retryWithBackoff;
}

const NetworkContext = React.createContext<NetworkContextType | undefined>(undefined);

export const useNetworkError = () => {
  const context = React.useContext(NetworkContext);
  if (!context) {
    throw new Error('useNetworkError must be used within NetworkErrorHandler');
  }
  return context;
};

/**
 * Hook for making network requests with automatic retry and error handling
 */
export const useRetryableRequest = () => {
  const { handleNetworkError, isOnline } = useNetworkError();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const makeRequest = useCallback(async <T>(
    requestFn: () => Promise<T>,
    options: {
      retryConfig?: Parameters<typeof retryWithBackoff>[1];
      onSuccess?: (result: T) => void;
      onError?: (error: Error) => void;
      context?: {
        component?: string;
        action?: string;
        orderId?: string;
      };
    } = {}
  ): Promise<T | null> => {
    if (!isOnline) {
      const offlineError = new OrderingError('You are currently offline', {
        code: 'OFFLINE',
        retryable: true,
        userMessage: 'Please check your internet connection and try again.'
      });
      
      setError(offlineError);
      handleNetworkError(offlineError);
      
      if (options.onError) {
        options.onError(offlineError);
      }
      
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await retryWithBackoff(requestFn, options.retryConfig);
      
      if (options.onSuccess) {
        options.onSuccess(result);
      }
      
      return result;
    } catch (error: any) {
      const enhancedError = error instanceof OrderingError 
        ? error 
        : new OrderingError(error.message || 'Network request failed', {
            code: 'NETWORK_ERROR',
            context: options.context,
            retryable: true,
            cause: error
          });

      setError(enhancedError);
      handleNetworkError(enhancedError);
      
      if (options.onError) {
        options.onError(enhancedError);
      }
      
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [isOnline, handleNetworkError]);

  const retry = useCallback(() => {
    setError(null);
  }, []);

  return {
    makeRequest,
    isLoading,
    error,
    retry,
    isOnline
  };
};

/**
 * Component for displaying retry UI
 */
interface RetryButtonProps {
  onRetry: () => void;
  isLoading?: boolean;
  error?: Error | null;
  className?: string;
}

export const RetryButton: React.FC<RetryButtonProps> = ({
  onRetry,
  isLoading = false,
  error,
  className = ''
}) => {
  if (!error) return null;

  const isRetryable = error instanceof OrderingError ? error.retryable : true;

  if (!isRetryable) return null;

  return (
    <button
      onClick={onRetry}
      disabled={isLoading}
      className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {isLoading ? (
        <>
          <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Retrying...
        </>
      ) : (
        <>
          <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Try Again
        </>
      )}
    </button>
  );
};

export default NetworkErrorHandler;