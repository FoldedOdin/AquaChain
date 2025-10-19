import React from 'react';

interface MetricOption {
  key: string;
  label: string;
  color: string;
  description: string;
}

interface MetricSelectorProps {
  selectedMetrics: string[];
  onMetricsChange: (metrics: string[]) => void;
}

const MetricSelector: React.FC<MetricSelectorProps> = ({ 
  selectedMetrics, 
  onMetricsChange 
}) => {
  const metrics: MetricOption[] = [
    {
      key: 'wqi',
      label: 'Water Quality Index',
      color: '#3b82f6',
      description: 'Overall water quality score (0-100)'
    },
    {
      key: 'pH',
      label: 'pH Level',
      color: '#10b981',
      description: 'Acidity/alkalinity level (0-14)'
    },
    {
      key: 'turbidity',
      label: 'Turbidity',
      color: '#f59e0b',
      description: 'Water clarity measurement (NTU)'
    },
    {
      key: 'tds',
      label: 'Total Dissolved Solids',
      color: '#ef4444',
      description: 'Dissolved particles concentration (ppm)'
    },
    {
      key: 'temperature',
      label: 'Temperature',
      color: '#8b5cf6',
      description: 'Water temperature (°C)'
    },
    {
      key: 'humidity',
      label: 'Humidity',
      color: '#06b6d4',
      description: 'Environmental humidity (%)'
    }
  ];

  const handleMetricToggle = (metricKey: string) => {
    if (selectedMetrics.includes(metricKey)) {
      onMetricsChange(selectedMetrics.filter(m => m !== metricKey));
    } else {
      onMetricsChange([...selectedMetrics, metricKey]);
    }
  };

  const selectAll = () => {
    onMetricsChange(metrics.map(m => m.key));
  };

  const selectNone = () => {
    onMetricsChange([]);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Select Metrics</h3>
        <div className="flex space-x-2">
          <button
            onClick={selectAll}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Select All
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={selectNone}
            className="text-sm text-gray-600 hover:text-gray-700 font-medium"
          >
            Clear All
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric) => {
          const isSelected = selectedMetrics.includes(metric.key);
          
          return (
            <div
              key={metric.key}
              className={`
                relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
                ${isSelected 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
              onClick={() => handleMetricToggle(metric.key)}
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div
                    className="w-4 h-4 rounded-full border-2"
                    style={{ 
                      backgroundColor: isSelected ? metric.color : 'transparent',
                      borderColor: metric.color 
                    }}
                  ></div>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium text-gray-900">
                      {metric.label}
                    </h4>
                    {isSelected && (
                      <svg className="w-4 h-4 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {metric.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {selectedMetrics.length === 0 && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                No metrics selected
              </h3>
              <div className="mt-1 text-sm text-yellow-700">
                Please select at least one metric to display the chart.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricSelector;