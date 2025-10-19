import React, { useState, useEffect } from 'react';
import TimeRangeFilter, { TimeRange } from '../components/History/TimeRangeFilter';
import MetricSelector from '../components/History/MetricSelector';
import WaterQualityChart from '../components/History/WaterQualityChart';
import SummaryStats from '../components/History/SummaryStats';
import { getHistoricalData, HistoricalDataPoint } from '../services/historicalData';

const History: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('1week');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['wqi', 'pH']);
  const [showMovingAverage, setShowMovingAverage] = useState(false);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load historical data when time range changes
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate API call delay
    const loadData = async () => {
      await new Promise(resolve => setTimeout(resolve, 500));
      const data = getHistoricalData(selectedTimeRange);
      setHistoricalData(data);
      setIsLoading(false);
    };
    
    loadData();
  }, [selectedTimeRange]);

  const handleExportData = () => {
    const csvContent = [
      ['Timestamp', 'pH', 'Turbidity (NTU)', 'TDS (ppm)', 'Temperature (°C)', 'Humidity (%)', 'WQI'].join(','),
      ...historicalData.map(point => [
        point.timestamp,
        point.pH.toFixed(1),
        point.turbidity.toFixed(1),
        point.tds.toFixed(0),
        point.temperature.toFixed(1),
        point.humidity.toFixed(1),
        point.wqi.toString()
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `water-quality-data-${selectedTimeRange}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Historical Data
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            View historical water quality trends and data analysis
          </p>
        </div>
        
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          <button
            onClick={handleExportData}
            disabled={historicalData.length === 0}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Time Range</h3>
            <TimeRangeFilter
              selectedRange={selectedTimeRange}
              onRangeChange={setSelectedTimeRange}
            />
          </div>
          
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showMovingAverage}
                onChange={(e) => setShowMovingAverage(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Show Moving Average</span>
            </label>
          </div>
        </div>
      </div>

      {/* Metric Selection */}
      <MetricSelector
        selectedMetrics={selectedMetrics}
        onMetricsChange={setSelectedMetrics}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      )}

      {/* Chart */}
      {!isLoading && selectedMetrics.length > 0 && (
        <WaterQualityChart
          data={historicalData}
          selectedMetrics={selectedMetrics}
          showMovingAverage={showMovingAverage}
        />
      )}

      {/* Summary Statistics */}
      {!isLoading && (
        <SummaryStats
          data={historicalData}
          selectedMetrics={selectedMetrics}
        />
      )}

      {/* Data Quality Info */}
      {!isLoading && historicalData.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Data Information
              </h3>
              <div className="mt-1 text-sm text-blue-700">
                <p>
                  Showing {historicalData.length} data points for the selected time range. 
                  Data is collected every {
                    selectedTimeRange === '1day' ? 'hour' :
                    selectedTimeRange === '1week' ? '3 hours' :
                    selectedTimeRange === '1month' ? '6 hours' : 'day'
                  }.
                </p>
                <p className="mt-1">
                  Reference lines show safe operating ranges: pH (6.5-8.5), WQI thresholds (60: Warning, 80: Good).
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;