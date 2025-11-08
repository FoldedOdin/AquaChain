import React from 'react';
import { Alert } from '../../types';

interface AlertHistoryProps {
  alerts: Alert[];
  maxItems?: number;
}

const AlertHistory: React.FC<AlertHistoryProps> = ({ alerts, maxItems = 5 }) => {
  const getSeverityConfig = (severity: 'safe' | 'warning' | 'critical') => {
    switch (severity) {
      case 'safe':
        return {
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
          iconColor: 'text-green-600',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )
        };
      case 'warning':
        return {
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-600',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )
        };
      case 'critical':
        return {
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-800',
          iconColor: 'text-red-600',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          )
        };
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const displayedAlerts = alerts.slice(0, maxItems);

  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Alerts</h3>
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No alerts</h3>
            <p className="mt-1 text-sm text-gray-500">
              Your water quality is within safe parameters.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Recent Alerts</h3>
          {alerts.length > maxItems && (
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View all ({alerts.length})
            </button>
          )}
        </div>

        <div className="space-y-3">
          {displayedAlerts.map((alert) => {
            const severityConfig = getSeverityConfig(alert.severity);
            
            return (
              <div
                key={alert.id}
                className={`
                  p-4 rounded-lg border-l-4 
                  ${severityConfig.bgColor} 
                  ${severityConfig.borderColor}
                `}
              >
                <div className="flex items-start space-x-3">
                  <div className={`flex-shrink-0 ${severityConfig.iconColor}`}>
                    {severityConfig.icon}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className={`text-sm font-medium ${severityConfig.textColor}`}>
                        {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)} Alert
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTimestamp(alert.timestamp)}
                      </p>
                    </div>
                    
                    <p className="mt-1 text-sm text-gray-700">
                      {alert.message}
                    </p>
                    
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                      <span>Device: {alert.deviceId}</span>
                      <span>WQI: {alert.wqi}</span>
                      <span>pH: {alert.readings.pH}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {alerts.length > maxItems && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button className="w-full text-center text-sm text-primary-600 hover:text-primary-700 font-medium py-2">
              Load more alerts
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertHistory;