import { useState, useEffect } from 'react';
import TimeRangeFilter, { TimeRange } from '../components/History/TimeRangeFilter';
import MetricSelector from '../components/History/MetricSelector';
import WaterQualityChart from '../components/History/WaterQualityChart';
import SummaryStats from '../components/History/SummaryStats';
import { HistoricalDataPoint } from '../services/historicalData';
import { useAuth } from '../contexts/AuthContext';
import dataService from '../services/dataService';

const timeRangeToDays: Record<TimeRange, number> = {
  '1day': 1,
  '1week': 7,
  '1month': 30,
  '3months': 90,
};

const History = () => {
  const { user } = useAuth();
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>('1week');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['wqi', 'pH']);
  const [showMovingAverage, setShowMovingAverage] = useState(false);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const deviceId = user?.deviceIds?.[0] ?? null;

  // Load historical data when time range or device changes
  useEffect(() => {
    if (!deviceId) {
      setHistoricalData([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    const loadData = async () => {
      try {
        const days = timeRangeToDays[selectedTimeRange];
        const readings = await dataService.getDeviceReadings(deviceId, days);

        // Map API response fields to HistoricalDataPoint
        const mapped: HistoricalDataPoint[] = (readings || []).map((r: any) => ({
          timestamp: r.timestamp,
          pH: Number(r.pH ?? r.ph ?? 0),
          turbidity: Number(r.turbidity ?? 0),
          tds: Number(r.tds ?? 0),
          temperature: Number(r.temperature ?? 0),
          humidity: 0, // not measured by ESP32
          wqi: Number(r.wqi ?? r.qualityScore ?? 0),
        }));

        // Sort oldest → newest for chart rendering
        mapped.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        setHistoricalData(mapped);
      } catch (err: any) {
        console.error('[History] Failed to load readings:', err);
        setError(err?.message || 'Failed to load historical data');
        setHistoricalData([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [selectedTimeRange, deviceId]);

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

      {/* Error state */}
      {!isLoading && error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Failed to load data</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* No device registered */}
      {!isLoading && !error && !deviceId && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-yellow-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">No device registered</h3>
              <p className="mt-1 text-sm text-yellow-700">Register an AquaChain device to see historical data.</p>
            </div>
          </div>
        </div>
      )}

      {/* No data for range */}
      {!isLoading && !error && deviceId && historicalData.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <p className="text-gray-500 text-sm">No readings found for the selected time range.</p>
        </div>
      )}

      {/* Data info */}
      {!isLoading && historicalData.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-blue-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Live Data</h3>
              <p className="mt-1 text-sm text-blue-700">
                Showing {historicalData.length} readings from your ESP32 device ({deviceId}).
                Reference lines: pH safe range 6.5–8.5, WQI thresholds 50 (Fair), 70 (Good), 90 (Excellent).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;