/**
 * Alert Panel Component
 * Displays and manages alerts with dismiss and acknowledge functionality
 */

import React from 'react';

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  acknowledged?: boolean;
  dismissible?: boolean;
}

interface AlertPanelProps {
  /** Array of alerts to display */
  alerts: Alert[];
  /** Callback when an alert is dismissed */
  onDismiss?: (id: string) => void;
  /** Callback when an alert is acknowledged */
  onAcknowledge?: (id: string) => void;
  /** Maximum number of alerts to display */
  maxAlerts?: number;
  /** Optional className for custom styling */
  className?: string;
}

/**
 * AlertPanel displays a list of alerts with actions for dismissing and acknowledging
 */
export const AlertPanel: React.FC<AlertPanelProps> = ({
  alerts,
  onDismiss,
  onAcknowledge,
  maxAlerts = 10,
  className = ''
}) => {
  const getAlertStyles = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-400',
          title: 'text-red-800',
          message: 'text-red-700'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-400',
          title: 'text-yellow-800',
          message: 'text-yellow-700'
        };
      case 'success':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          icon: 'text-green-400',
          title: 'text-green-800',
          message: 'text-green-700'
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-400',
          title: 'text-blue-800',
          message: 'text-blue-700'
        };
    }
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return (
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'success':
        return (
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const displayedAlerts = alerts.slice(0, maxAlerts);

  if (displayedAlerts.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No alerts</h3>
          <p className="mt-1 text-sm text-gray-500">All systems are operating normally</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Alerts</h3>
        <p className="text-sm text-gray-500 mt-1">
          {displayedAlerts.length} active alert{displayedAlerts.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {displayedAlerts.map((alert) => {
          const styles = getAlertStyles(alert.type);

          return (
            <div
              key={alert.id}
              className={`p-4 ${styles.bg} ${alert.acknowledged ? 'opacity-60' : ''}`}
            >
              <div className="flex">
                <div className="flex-shrink-0">
                  <div className={styles.icon}>
                    {getAlertIcon(alert.type)}
                  </div>
                </div>

                <div className="ml-3 flex-1">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className={`text-sm font-medium ${styles.title}`}>
                        {alert.title}
                      </h4>
                      <p className={`mt-1 text-sm ${styles.message}`}>
                        {alert.message}
                      </p>
                      <p className="mt-1 text-xs text-gray-500">
                        {formatTimestamp(alert.timestamp)}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="ml-4 flex-shrink-0 flex space-x-2">
                      {!alert.acknowledged && onAcknowledge && (
                        <button
                          onClick={() => onAcknowledge(alert.id)}
                          className="text-xs font-medium text-gray-600 hover:text-gray-800 transition-colors"
                          title="Acknowledge"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                      )}

                      {(alert.dismissible !== false) && onDismiss && (
                        <button
                          onClick={() => onDismiss(alert.id)}
                          className="text-xs font-medium text-gray-600 hover:text-gray-800 transition-colors"
                          title="Dismiss"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {alerts.length > maxAlerts && (
        <div className="p-3 bg-gray-50 border-t border-gray-200 text-center">
          <p className="text-sm text-gray-600">
            +{alerts.length - maxAlerts} more alert{alerts.length - maxAlerts !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
