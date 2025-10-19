import React, { useState, useEffect } from 'react';
import StatusIndicator from '../components/Dashboard/StatusIndicator';
import SensorReadings from '../components/Dashboard/SensorReadings';
import WQIGauge from '../components/Dashboard/WQIGauge';
import AlertHistory from '../components/Dashboard/AlertHistory';
import { WaterQualityReading, Alert } from '../types';
import { 
  mockWaterQualityReading, 
  mockAlerts, 
  getWaterQualityStatus,
  generateRandomReading 
} from '../services/mockData';

const Dashboard: React.FC = () => {
  const [currentReading, setCurrentReading] = useState<WaterQualityReading>(mockWaterQualityReading);
  const [alerts] = useState<Alert[]>(mockAlerts);
  const [isLoading, setIsLoading] = useState(true);

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentReading(prev => generateRandomReading(prev));
    }, 30000); // Update every 30 seconds

    // Initial load delay to simulate API call
    const loadTimeout = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(loadTimeout);
    };
  }, []);

  const waterQualityStatus = getWaterQualityStatus(currentReading.wqi);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Water Quality Dashboard
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Real-time monitoring of your water quality sensors
            </p>
          </div>
        </div>

        {/* Loading skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-24 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="animate-pulse">
                <div className="h-40 bg-gray-200 rounded-full mx-auto"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Water Quality Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Real-time monitoring of your water quality sensors
          </p>
        </div>
        
        {/* Quick actions */}
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button 
            onClick={() => window.location.href = '/service'}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Request Service
          </button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
          <StatusIndicator 
            status={waterQualityStatus} 
            wqi={currentReading.wqi}
            size="large"
          />
          
          <div className="text-center sm:text-right">
            <div className="text-sm text-gray-500 mb-1">Last Updated</div>
            <div className="text-lg font-medium text-gray-900">
              {new Date(currentReading.timestamp).toLocaleTimeString()}
            </div>
            <div className="text-sm text-gray-500">
              {new Date(currentReading.timestamp).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Sensor Readings */}
        <div className="lg:col-span-2 space-y-6">
          <SensorReadings reading={currentReading} />
          
          {/* Alert History */}
          <AlertHistory alerts={alerts} maxItems={3} />
        </div>

        {/* Right Column - WQI Gauge and Quick Stats */}
        <div className="space-y-6">
          <WQIGauge wqi={currentReading.wqi} size="large" />
          
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Active Devices</span>
                <span className="text-lg font-semibold text-gray-900">2</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Today's Alerts</span>
                <span className="text-lg font-semibold text-red-600">
                  {alerts.filter(alert => {
                    const alertDate = new Date(alert.timestamp);
                    const today = new Date();
                    return alertDate.toDateString() === today.toDateString();
                  }).length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Avg WQI (7 days)</span>
                <span className="text-lg font-semibold text-green-600">78</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">System Status</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Online
                </span>
              </div>
            </div>
          </div>

          {/* Device Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Device Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">DEV-3421</div>
                    <div className="text-xs text-gray-500">Kitchen Sink</div>
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  {currentReading.diagnostics.batteryLevel}%
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">DEV-3422</div>
                    <div className="text-xs text-gray-500">Main Water Line</div>
                  </div>
                </div>
                <div className="text-sm text-gray-600">92%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;