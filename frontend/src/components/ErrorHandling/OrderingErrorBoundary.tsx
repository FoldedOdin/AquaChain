/**
 * Ordering Error Boundary Component
 * Specialized error boundary for the Enhanced Consumer Ordering System
 * Requirements: 6.1, 6.2, 6.4
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { OrderingError, logError, getUserFriendlyMessage } from '../../utils/errorHandling';
import { useNotifications } from '../../contexts/NotificationContext';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  context?: {
    component?: string;
    orderId?: string;
    userId?: string;
  };
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

class OrderingErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Enhanced error logging with context
    const enhancedError = error instanceof OrderingError 
      ? error 
      : new OrderingError(error.message, {
          code: 'COMPONENT_ERROR',
          context: {
            component: this.props.context?.component || 'OrderingErrorBoundary',
            orderId: this.props.context?.orderId,
            userId: this.props.context?.userId,
          },
          cause: error
        });

    logError(enhancedError, {
      component: this.props.context?.component,
      action: 'component_error',
    });

    this.setState({
      error: enhancedError,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/dashboard';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default ordering-specific fallback UI
      return (
        <OrderingErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          onRetry={this.handleRetry}
          onReload={this.handleReload}
          onGoHome={this.handleGoHome}
          context={this.props.context}
        />
      );
    }

    return this.props.children;
  }
}

interface FallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  onRetry: () => void;
  onReload: () => void;
  onGoHome: () => void;
  context?: {
    component?: string;
    orderId?: string;
    userId?: string;
  };
}

const OrderingErrorFallback: React.FC<FallbackProps> = ({
  error,
  errorInfo,
  errorId,
  onRetry,
  onReload,
  onGoHome,
  context
}) => {
  const userMessage = error ? getUserFriendlyMessage(error) : 'An unexpected error occurred';
  const isOrderingError = error instanceof OrderingError;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg border border-gray-200 p-8">
        {/* Error Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
            <svg
              className="w-10 h-10 text-red-600"
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
        </div>

        {/* Error Message */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {isOrderingError && error.code === 'PAYMENT_FAILED' 
              ? 'Payment Failed'
              : isOrderingError && error.code === 'ORDER_CREATION_FAILED'
              ? 'Order Creation Failed'
              : 'Something went wrong'
            }
          </h1>
          
          <p className="text-gray-600 mb-4">
            {userMessage}
          </p>

          {/* Order Context */}
          {context?.orderId && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Order ID:</span> {context.orderId}
              </p>
            </div>
          )}

          {/* Error ID for support */}
          {errorId && (
            <p className="text-xs text-gray-500 mb-4">
              Error ID: {errorId}
            </p>
          )}

          {/* Retry suggestion for retryable errors */}
          {isOrderingError && error.retryable && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-yellow-800">
                This appears to be a temporary issue. Please try again.
              </p>
            </div>
          )}

          {/* Error Details (Development Only) */}
          {process.env.NODE_ENV === 'development' && error && (
            <details className="mt-4 text-left">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 mb-2">
                Error Details (Development Mode)
              </summary>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm font-mono text-red-600 mb-2">
                  {error.toString()}
                </p>
                {isOrderingError && (
                  <div className="text-xs text-gray-700 mb-2">
                    <p><strong>Code:</strong> {error.code}</p>
                    <p><strong>Status:</strong> {error.status}</p>
                    <p><strong>Retryable:</strong> {error.retryable ? 'Yes' : 'No'}</p>
                    {error.context && (
                      <p><strong>Context:</strong> {JSON.stringify(error.context, null, 2)}</p>
                    )}
                  </div>
                )}
                {errorInfo && (
                  <pre className="text-xs text-gray-700 overflow-auto max-h-64">
                    {errorInfo.componentStack}
                  </pre>
                )}
              </div>
            </details>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {/* Retry button for retryable errors */}
          {(!isOrderingError || error.retryable) && (
            <button
              onClick={onRetry}
              className="px-6 py-3 bg-aqua-600 hover:bg-aqua-700 text-white font-semibold rounded-lg transition-colors duration-200"
            >
              Try Again
            </button>
          )}
          
          {/* Reload page button */}
          <button
            onClick={onReload}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold rounded-lg transition-colors duration-200"
          >
            Reload Page
          </button>
          
          {/* Go to dashboard button */}
          <button
            onClick={onGoHome}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold rounded-lg transition-colors duration-200"
          >
            Go to Dashboard
          </button>
        </div>

        {/* Support Information */}
        <div className="mt-8 pt-6 border-t border-gray-200 text-center">
          <p className="text-sm text-gray-600">
            If this problem persists, please{' '}
            <a
              href="/support"
              className="text-aqua-600 hover:text-aqua-700 font-medium"
            >
              contact support
            </a>
            {errorId && (
              <span> and provide the error ID: <code className="bg-gray-100 px-1 rounded">{errorId}</code></span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default OrderingErrorBoundary;

/**
 * Hook-based wrapper for functional components
 */
export const withOrderingErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  context?: {
    component?: string;
    orderId?: string;
    userId?: string;
  }
): React.FC<P> => {
  const WrappedComponent: React.FC<P> = (props) => (
    <OrderingErrorBoundary context={context}>
      <Component {...props} />
    </OrderingErrorBoundary>
  );

  WrappedComponent.displayName = `withOrderingErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
};