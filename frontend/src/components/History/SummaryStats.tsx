import React from 'react';

interface DataPoint {
  timestamp: string;
  pH: number;
  turbidity: number;
  tds: number;
  temperature: number;
  humidity: number;
  wqi: number;
}

interface SummaryStatsProps {
  data: DataPoint[];
  selectedMetrics: string[];
}

const SummaryStats: React.FC<SummaryStatsProps> = ({ data, selectedMetrics }) => {
  const calculateStats = (values: number[]) => {
    if (values.length === 0) return { min: 0, max: 0, avg: 0, trend: 0 };
    
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
    
    // Calculate trend (simple linear regression slope)
    const n = values.length;
    const sumX = (n * (n - 1)) / 2; // Sum of indices 0, 1, 2, ..., n-1
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXY = values.reduce((sum, val, index) => sum + val * index, 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6; // Sum of squares of indices
    
    const trend = n > 1 ? (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX) : 0;
    
    return { min, max, avg, trend };
  };

  const getMetricData = (metric: string) => {
    return data.map(point => point[metric as keyof DataPoint] as number);
  };

  const formatValue = (value: number, metric: string) => {
    const decimals = metric === 'tds' ? 0 : 1;
    return value.toFixed(decimals);
  };

  const getUnit = (metric: string) => {
    switch (metric) {
      case 'pH': return '';
      case 'turbidity': return ' NTU';
      case 'tds': return ' ppm';
      case 'temperature': return '°C';
      case 'humidity': return '%';
      case 'wqi': return '';
      default: return '';
    }
  };

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case 'pH': return 'pH Level';
      case 'turbidity': return 'Turbidity';
      case 'tds': return 'TDS';
      case 'temperature': return 'Temperature';
      case 'humidity': return 'Humidity';
      case 'wqi': return 'WQI';
      default: return metric;
    }
  };

  const getTrendIcon = (trend: number) => {
    if (Math.abs(trend) < 0.01) {
      return (
        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      );
    } else if (trend > 0) {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7H7" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10h10" />
        </svg>
      );
    }
  };

  const getTrendLabel = (trend: number) => {
    if (Math.abs(trend) < 0.01) return 'Stable';
    return trend > 0 ? 'Increasing' : 'Decreasing';
  };

  if (data.length === 0 || selectedMetrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Summary Statistics</h3>
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No data available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Select metrics and time range to view statistics.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Summary Statistics</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {selectedMetrics.map((metric) => {
          const values = getMetricData(metric);
          const stats = calculateStats(values);
          const unit = getUnit(metric);
          
          return (
            <div key={metric} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">
                  {getMetricLabel(metric)}
                </h4>
                <div className="flex items-center space-x-1">
                  {getTrendIcon(stats.trend)}
                  <span className="text-xs text-gray-500">
                    {getTrendLabel(stats.trend)}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Average:</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {formatValue(stats.avg, metric)}{unit}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Min:</span>
                  <span className="text-sm text-gray-700">
                    {formatValue(stats.min, metric)}{unit}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Max:</span>
                  <span className="text-sm text-gray-700">
                    {formatValue(stats.max, metric)}{unit}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Range:</span>
                  <span className="text-sm text-gray-700">
                    {formatValue(stats.max - stats.min, metric)}{unit}
                  </span>
                </div>
              </div>
              
              {/* Visual indicator for metric health */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                {metric === 'wqi' && (
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      stats.avg >= 80 ? 'bg-green-500' :
                      stats.avg >= 60 ? 'bg-blue-500' :
                      stats.avg >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-xs text-gray-600">
                      {stats.avg >= 80 ? 'Excellent' :
                       stats.avg >= 60 ? 'Good' :
                       stats.avg >= 40 ? 'Fair' : 'Poor'}
                    </span>
                  </div>
                )}
                
                {metric === 'pH' && (
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      stats.avg >= 6.5 && stats.avg <= 8.5 ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-xs text-gray-600">
                      {stats.avg >= 6.5 && stats.avg <= 8.5 ? 'Safe Range' : 'Out of Range'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Data period info */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Data Points: {data.length}</span>
          <span>
            Period: {new Date(data[0]?.timestamp).toLocaleDateString()} - {new Date(data[data.length - 1]?.timestamp).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SummaryStats;