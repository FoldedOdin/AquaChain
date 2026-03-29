import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Calendar, Filter, FileText, FileSpreadsheet, Database, Search, RefreshCw } from 'lucide-react';
import { dataService } from '../../services/dataService';

interface ReadingHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceId: string;
}

interface Reading {
  timestamp: string;
  pH: number;
  turbidity: number;
  tds: number;
  temperature: number;
  wqi?: number;
  quality?: string;
}

interface FilterOptions {
  startDate: string;
  endDate: string;
  parameter: string;
  minValue: string;
  maxValue: string;
  timeRange: string;
}

export const ReadingHistoryModal: React.FC<ReadingHistoryModalProps> = ({ isOpen, onClose, deviceId }) => {
  const [readings, setReadings] = useState<Reading[]>([]);
  const [filteredReadings, setFilteredReadings] = useState<Reading[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    startDate: '',
    endDate: '',
    parameter: 'all',
    minValue: '',
    maxValue: '',
    timeRange: '30d'
  });

  useEffect(() => {
    if (isOpen && deviceId) {
      fetchReadings();
    }
  }, [isOpen, deviceId, filters.timeRange]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  useEffect(() => {
    applyFilters();
  }, [readings, filters]);

  const fetchReadings = async () => {
    setLoading(true);
    try {
      const days = filters.timeRange === '1d' ? 1 :
                   filters.timeRange === '7d' ? 7 :
                   filters.timeRange === '30d' ? 30 : 90;

      const data = await dataService.getDeviceReadings(deviceId, days);
      // Normalize nested-format records (old format: { readings: { pH, ... } })
      // into the flat format the table expects
      const normalized = (data || []).map((r: any) => {
        if (r.readings && typeof r.readings === 'object') {
          return { ...r, ...r.readings };
        }
        return r;
      });
      setReadings(normalized);
    } catch (error) {
      console.error('Error fetching readings:', error);
      setReadings([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...readings];

    // Date range filter
    if (filters.startDate) {
      filtered = filtered.filter(r => new Date(r.timestamp) >= new Date(filters.startDate));
    }
    if (filters.endDate) {
      filtered = filtered.filter(r => new Date(r.timestamp) <= new Date(filters.endDate));
    }

    // Parameter value filter
    if (filters.parameter !== 'all' && filters.minValue) {
      const minVal = parseFloat(filters.minValue);
      filtered = filtered.filter(r => {
        const value = r[filters.parameter as keyof Reading] as number;
        return value >= minVal;
      });
    }
    if (filters.parameter !== 'all' && filters.maxValue) {
      const maxVal = parseFloat(filters.maxValue);
      filtered = filtered.filter(r => {
        const value = r[filters.parameter as keyof Reading] as number;
        return value <= maxVal;
      });
    }

    setFilteredReadings(filtered);
  };

  const exportData = (format: 'csv' | 'json' | 'pdf') => {
    const data = filteredReadings;
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `water-readings-${deviceId}-${timestamp}`;

    if (format === 'csv') {
      const headers = ['Timestamp', 'pH', 'Turbidity (NTU)', 'TDS (ppm)', 'Temperature (°C)', 'WQI', 'Quality'];
      const csvContent = [
        headers.join(','),
        ...data.map(r => [
          r.timestamp,
          r.pH,
          r.turbidity,
          r.tds,
          r.temperature,
          r.wqi || '',
          r.quality || ''
        ].join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'json') {
      const jsonContent = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonContent], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'pdf') {
      // For PDF, we'll create a simple HTML report and print it
      const reportWindow = window.open('', '_blank');
      if (reportWindow) {
        const htmlContent = `
          <html>
            <head>
              <title>Water Quality Report - ${deviceId}</title>
              <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .header { text-align: center; margin-bottom: 20px; }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>Water Quality Report</h1>
                <p>Device ID: ${deviceId}</p>
                <p>Generated: ${new Date().toLocaleString()}</p>
                <p>Total Readings: ${data.length}</p>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>pH</th>
                    <th>Turbidity (NTU)</th>
                    <th>TDS (ppm)</th>
                    <th>Temperature (°C)</th>
                    <th>WQI</th>
                    <th>Quality</th>
                  </tr>
                </thead>
                <tbody>
                  ${data.map(r => `
                    <tr>
                      <td>${new Date(r.timestamp).toLocaleString()}</td>
                      <td>${r.pH}</td>
                      <td>${r.turbidity}</td>
                      <td>${r.tds}</td>
                      <td>${r.temperature}</td>
                      <td>${r.wqi || 'N/A'}</td>
                      <td>${r.quality || 'N/A'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </body>
          </html>
        `;
        reportWindow.document.open();
        reportWindow.document.write(htmlContent);
        reportWindow.document.close();
        reportWindow.print();
      }
    }
  };

  const resetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      parameter: 'all',
      minValue: '',
      maxValue: '',
      timeRange: '7d'
    });
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-hidden"
      style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflowY: 'hidden'
      }}
      onClick={(e) => {
        // Close modal if clicking on backdrop
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="flex items-center justify-center min-h-full p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-lg shadow-xl max-w-6xl w-full h-[90vh] flex flex-col relative"
          onClick={(e) => e.stopPropagation()} // Prevent event bubbling
        >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Water Reading History</h2>
            <p className="text-sm text-gray-600">Device: {deviceId}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Controls */}
        <div className="p-6 border-b border-gray-200 bg-gray-50 flex-shrink-0">
          <div className="flex flex-wrap items-center gap-4">
            {/* Time Range Selector */}
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <select
                value={filters.timeRange}
                onChange={(e) => setFilters(prev => ({ ...prev, timeRange: e.target.value }))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="1d">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                showFilters ? 'bg-aqua-100 text-aqua-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="w-4 h-4" />
              Advanced Filters
            </button>

            {/* Refresh */}
            <button
              onClick={fetchReadings}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            {/* Export Options */}
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-sm text-gray-600">Export:</span>
              <button
                onClick={() => exportData('csv')}
                className="flex items-center gap-1 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm"
              >
                <FileSpreadsheet className="w-4 h-4" />
                CSV
              </button>
              <button
                onClick={() => exportData('json')}
                className="flex items-center gap-1 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm"
              >
                <Database className="w-4 h-4" />
                JSON
              </button>
              <button
                onClick={() => exportData('pdf')}
                className="flex items-center gap-1 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
              >
                <FileText className="w-4 h-4" />
                PDF Report
              </button>
            </div>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-4 bg-white rounded-lg border border-gray-200"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={filters.startDate}
                    onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                  <input
                    type="date"
                    value={filters.endDate}
                    onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Parameter</label>
                  <select
                    value={filters.parameter}
                    onChange={(e) => setFilters(prev => ({ ...prev, parameter: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="all">All Parameters</option>
                    <option value="pH">pH</option>
                    <option value="turbidity">Turbidity</option>
                    <option value="tds">TDS</option>
                    <option value="temperature">Temperature</option>
                    <option value="wqi">WQI</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Value</label>
                    <input
                      type="number"
                      step="0.1"
                      value={filters.minValue}
                      onChange={(e) => setFilters(prev => ({ ...prev, minValue: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      disabled={filters.parameter === 'all'}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Value</label>
                    <input
                      type="number"
                      step="0.1"
                      value={filters.maxValue}
                      onChange={(e) => setFilters(prev => ({ ...prev, maxValue: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      disabled={filters.parameter === 'all'}
                    />
                  </div>
                </div>
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  onClick={resetFilters}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Reset Filters
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {/* Data Table - Scrollable */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 animate-spin text-aqua-600" />
                <span className="text-gray-600">Loading readings...</span>
              </div>
            </div>
          ) : filteredReadings.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No readings found</h3>
                <p className="text-gray-600">Try adjusting your filters or time range.</p>
              </div>
            </div>
          ) : (
            <div className="h-full overflow-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      pH
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Turbidity (NTU)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      TDS (ppm)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Temperature (°C)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      WQI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredReadings.map((reading, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(reading.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reading.pH != null ? Number(reading.pH).toFixed(2) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reading.turbidity != null ? Number(reading.turbidity).toFixed(2) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reading.tds != null ? Number(reading.tds).toFixed(0) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reading.temperature != null ? Number(reading.temperature).toFixed(1) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reading.wqi ? reading.wqi.toFixed(0) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {reading.quality ? (
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            reading.quality === 'Excellent' ? 'bg-green-100 text-green-800' :
                            reading.quality === 'Good' ? 'bg-blue-100 text-blue-800' :
                            reading.quality === 'Fair' ? 'bg-yellow-100 text-yellow-800' :
                            reading.quality === 'Poor' ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {reading.quality}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex-shrink-0">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Showing {filteredReadings.length} of {readings.length} readings</span>
            <span>Last updated: {new Date().toLocaleString()}</span>
          </div>
        </div>
        </motion.div>
      </div>
    </div>
  );
};