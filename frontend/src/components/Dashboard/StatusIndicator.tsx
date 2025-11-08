import React from 'react';

interface StatusIndicatorProps {
  status: 'safe' | 'warning' | 'critical';
  wqi: number;
  size?: 'small' | 'medium' | 'large';
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  status, 
  wqi, 
  size = 'large' 
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'safe':
        return {
          color: 'text-safe',
          bgColor: 'bg-safe',
          borderColor: 'border-safe',
          label: 'Safe',
          icon: (
            <svg className="w-full h-full" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )
        };
      case 'warning':
        return {
          color: 'text-warning',
          bgColor: 'bg-warning',
          borderColor: 'border-warning',
          label: 'Warning',
          icon: (
            <svg className="w-full h-full" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )
        };
      case 'critical':
        return {
          color: 'text-critical',
          bgColor: 'bg-critical',
          borderColor: 'border-critical',
          label: 'Critical',
          icon: (
            <svg className="w-full h-full" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          )
        };
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return {
          container: 'w-16 h-16',
          icon: 'w-6 h-6',
          text: 'text-sm',
          wqi: 'text-lg'
        };
      case 'medium':
        return {
          container: 'w-24 h-24',
          icon: 'w-8 h-8',
          text: 'text-base',
          wqi: 'text-xl'
        };
      case 'large':
        return {
          container: 'w-32 h-32 sm:w-40 sm:h-40',
          icon: 'w-12 h-12 sm:w-16 sm:h-16',
          text: 'text-lg sm:text-xl',
          wqi: 'text-2xl sm:text-3xl'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const sizeClasses = getSizeClasses();

  return (
    <div className="flex flex-col items-center space-y-2">
      <div className={`
        ${sizeClasses.container} 
        ${statusConfig.bgColor} 
        ${statusConfig.borderColor}
        border-4 rounded-full flex items-center justify-center
        shadow-lg transition-all duration-300 hover:scale-105
      `}>
        <div className={`${sizeClasses.icon} text-white`}>
          {statusConfig.icon}
        </div>
      </div>
      
      <div className="text-center">
        <div className={`${sizeClasses.text} font-bold ${statusConfig.color}`}>
          {statusConfig.label}
        </div>
        <div className={`${sizeClasses.wqi} font-bold text-gray-900`}>
          WQI: {wqi}
        </div>
      </div>
    </div>
  );
};

export default StatusIndicator;