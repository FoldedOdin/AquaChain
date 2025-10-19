import React from 'react';

interface WQIGaugeProps {
  wqi: number;
  size?: 'small' | 'medium' | 'large';
}

const WQIGauge: React.FC<WQIGaugeProps> = ({ wqi, size = 'medium' }) => {
  const getWQIStatus = (value: number) => {
    if (value >= 80) return { label: 'Excellent', color: '#10b981', bgColor: 'bg-green-50' };
    if (value >= 60) return { label: 'Good', color: '#3b82f6', bgColor: 'bg-blue-50' };
    if (value >= 40) return { label: 'Fair', color: '#f59e0b', bgColor: 'bg-yellow-50' };
    if (value >= 20) return { label: 'Poor', color: '#ef4444', bgColor: 'bg-red-50' };
    return { label: 'Very Poor', color: '#dc2626', bgColor: 'bg-red-100' };
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          container: 'w-32 h-32',
          strokeWidth: 8,
          radius: 50,
          fontSize: 'text-lg',
          labelSize: 'text-sm'
        };
      case 'medium':
        return {
          container: 'w-40 h-40',
          strokeWidth: 10,
          radius: 60,
          fontSize: 'text-2xl',
          labelSize: 'text-base'
        };
      case 'large':
        return {
          container: 'w-48 h-48 sm:w-56 sm:h-56',
          strokeWidth: 12,
          radius: 70,
          fontSize: 'text-3xl sm:text-4xl',
          labelSize: 'text-lg sm:text-xl'
        };
    }
  };

  const status = getWQIStatus(wqi);
  const config = getSizeConfig();
  
  // Calculate circle properties
  const circumference = 2 * Math.PI * config.radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (wqi / 100) * circumference;

  // Create gradient stops for the gauge
  const gradientId = `wqi-gradient-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`${status.bgColor} rounded-lg p-6 flex flex-col items-center`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Water Quality Index</h3>
      
      <div className={`relative ${config.container}`}>
        <svg
          className="transform -rotate-90 w-full h-full"
          viewBox="0 0 160 160"
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="25%" stopColor="#f59e0b" />
              <stop offset="50%" stopColor="#3b82f6" />
              <stop offset="75%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>
          
          {/* Background circle */}
          <circle
            cx="80"
            cy="80"
            r={config.radius}
            stroke="#e5e7eb"
            strokeWidth={config.strokeWidth}
            fill="none"
          />
          
          {/* Progress circle */}
          <circle
            cx="80"
            cy="80"
            r={config.radius}
            stroke={`url(#${gradientId})`}
            strokeWidth={config.strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`${config.fontSize} font-bold text-gray-900`}>
            {wqi}
          </div>
          <div className="text-sm text-gray-600">/ 100</div>
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <div 
          className={`${config.labelSize} font-semibold`}
          style={{ color: status.color }}
        >
          {status.label}
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Quality Rating
        </div>
      </div>

      {/* WQI Scale Reference */}
      <div className="mt-4 w-full">
        <div className="text-xs text-gray-600 mb-2 text-center">Quality Scale</div>
        <div className="flex justify-between text-xs text-gray-500">
          <div className="text-center">
            <div className="w-2 h-2 bg-red-500 rounded-full mx-auto mb-1"></div>
            <div>0-20</div>
            <div>Poor</div>
          </div>
          <div className="text-center">
            <div className="w-2 h-2 bg-yellow-500 rounded-full mx-auto mb-1"></div>
            <div>20-40</div>
            <div>Fair</div>
          </div>
          <div className="text-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full mx-auto mb-1"></div>
            <div>40-60</div>
            <div>Good</div>
          </div>
          <div className="text-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mx-auto mb-1"></div>
            <div>60-80</div>
            <div>V.Good</div>
          </div>
          <div className="text-center">
            <div className="w-2 h-2 bg-green-600 rounded-full mx-auto mb-1"></div>
            <div>80-100</div>
            <div>Excellent</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WQIGauge;