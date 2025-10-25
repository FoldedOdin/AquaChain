/**
 * Data Card Component
 * Displays metric data with optional trend indicators and loading states
 */

import React, { ReactNode } from 'react';

interface TrendData {
  value: number;
  direction: 'up' | 'down' | 'neutral';
  label?: string;
}

interface DataCardProps {
  /** Card title */
  title: string;
  /** Main value to display */
  value: string | number;
  /** Optional trend data */
  trend?: TrendData;
  /** Optional icon */
  icon?: ReactNode;
  /** Loading state */
  loading?: boolean;
  /** Optional subtitle */
  subtitle?: string;
  /** Optional action button */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Optional className for custom styling */
  className?: string;
}

/**
 * DataCard displays a metric with optional trend indicators and actions
 */
export const DataCard: React.FC<DataCardProps> = ({
  title,
  value,
  trend,
  icon,
  loading = false,
  subtitle,
  action,
  className = ''
}) => {
  const getTrendColor = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      case 'neutral':
        return 'text-gray-600';
    }
  };

  const getTrendIcon = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'neutral':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          {trend && <div className="h-3 bg-gray-200 rounded w-1/3"></div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Title */}
          <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>

          {/* Value */}
          <div className="flex items-baseline space-x-2">
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            {subtitle && (
              <span className="text-sm text-gray-500">{subtitle}</span>
            )}
          </div>

          {/* Trend */}
          {trend && (
            <div className={`flex items-center mt-2 text-sm ${getTrendColor(trend.direction)}`}>
              {getTrendIcon(trend.direction)}
              <span className="ml-1 font-medium">{trend.value}%</span>
              {trend.label && (
                <span className="ml-1 text-gray-500">{trend.label}</span>
              )}
            </div>
          )}

          {/* Action Button */}
          {action && (
            <button
              onClick={action.onClick}
              className="mt-4 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
            >
              {action.label} →
            </button>
          )}
        </div>

        {/* Icon */}
        {icon && (
          <div className="flex-shrink-0 ml-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
              {icon}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataCard;
