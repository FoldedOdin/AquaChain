import React, { useState, useEffect } from 'react';
import StatusIndicator from '../components/Dashboard/StatusIndicator';
import SensorReadings from '../components/Dashboard/SensorReadings';
import WQIGauge from '../components/Dashboard/WQIGauge';
import AlertHistory from '../components/Dashboard/AlertHistory';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import DataCard from '../components/Dashboard/DataCard';
import AlertPanel from '../components/Dashboard/AlertPanel';
import { WaterQualityReading } from '../types';
import { Alert } from '../types/alert';
import { 
  mockWaterQualityReading, 
  mockAlerts, 
  getWaterQualityStatus,
  generateRandomReading 
} from '../services/mockData';
import { useDashboardData } from '../hooks/useDashboardData';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';
import { useDataExport } from '../hooks/useDataExport';

const Dashboard: React.FC = () => {
  const [currentReading, setCurrentReading] = useState<WaterQualityReading>(mockWaterQualityReading);

  // Use shared hooks
  const dashboardData = useDashboardData();
  const { latestUpdate } = useRealTimeUpdates('consumer-updates');
  const { exportData, exporting } = useDataExport();

  // Extract data from the hook
  const isLoading = dashboardData.loading;
  const error = dashboardData.error;
  const alerts = dashboardData.alerts || mockAlerts;
  const devices = dashboardData.devices || [];
  const stats = {}; // TODO: Implement consumer stats
  
  // Refetch function
  const refetch = React.useCallback(() => {
    window.location.reload();
  }, []);

  // Simulate real-time data updates (fallback to mock data)
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentReading(prev => generateRandomReading(prev));
    }, 30000); // Update every 30 seconds

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Update reading from real-time updates
  useEffect(() => {
    if (latestUpdate?.type === 'water_quality' && latestUpdate.data) {
      setCurrentReading(latestUpdate.data);
    }
  }, [latestUpdate]);

  const waterQualityStatus = getWaterQualityStatus(currentReading.wqi);

  const handleExportData = async () => {
    try {
      await exportData(
        {
          currentReading,
          alerts,
          devices,
          stats
        },
        {
          format: 'json',
          filename: `water-quality-${new Date().toISOString().split('T')[0]}.json`,
          includeMetadata: true
        }
      );
    } catch (err) {
      console.error('Error exporting data:', err);
    }
  };

  const handleDismissAlert = (id: string) => {
    // In a real implementation, this would call an API
    console.log('Dismiss alert:', id);
  };

  const handleAcknowledgeAlert = (id: string) => {
    // In a real implementation, this would call an API
    console.log('Acknowledge alert:', id);
  };

  if (isLoading) {
    return (
      <DashboardLayout
        role="consumer"
        header={
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {[...Array(3)].map((_, i) => (
              <DataCard key={i} title="" value="" loading={true} />
            ))}
          </div>
          <div className="space-y-6">
            <DataCard title="" value="" loading={true} />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout
        role="consumer"
        header={
          <>
            <h2 className="text-2xl font-bold text-gray-900">Water Quality Dashboard</h2>
            <p className="mt-1 text-sm text-gray-500">Real-time monitoring of your water quality sensors</p>
          </>
        }
      >
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Dashboard</h3>
          <p className="text-red-700">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      role="consumer"
      header={
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900">Water Quality Dashboard</h2>
            <p className="mt-1 text-sm text-gray-500">
              Real-time monitoring of your water quality sensors
            </p>
            {latestUpdate && (
              <p className="text-sm text-blue-600 mt-1">
                Latest update: {new Date(latestUpdate.timestamp || new Date()).toLocaleTimeString()}
              </p>
            )}
          </div>
          
          {/* Quick actions */}
          <div className="flex space-x-3">
            <button 
              onClick={() => window.location.href = '/service'}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Request Service
            </button>
            <button
              onClick={handleExportData}
              disabled={exporting}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : 'Export Data'}
            </button>
          </div>
        </div>
      }
    >

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
          
          {/* Alert Panel using shared component */}
          <AlertPanel 
            alerts={alerts.map((alert) => ({
              id: alert.alertId,
              type: alert.severity === 'Critical' ? 'error' : alert.severity === 'Warning' ? 'warning' : 'info',
              title: `Water Quality Alert - ${alert.issue}`,
              message: alert.issue,
              timestamp: alert.timestamp.toISOString(),
              dismissible: true
            }))}
            onDismiss={handleDismissAlert}
            onAcknowledge={handleAcknowledgeAlert}
            maxAlerts={5}
          />
        </div>

        {/* Right Column - WQI Gauge and Quick Stats */}
        <div className="space-y-6">
          <WQIGauge wqi={currentReading.wqi} size="large" />
          
          {/* Quick Stats using DataCard */}
          <DataCard
            title="Active Devices"
            value={devices.filter((d: any) => d.status === 'online').length}
            subtitle={`of ${devices.length || 2}`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            }
          />

          <DataCard
            title="Today's Alerts"
            value={alerts.filter((alert) => {
              const alertDate = new Date(alert.timestamp);
              const today = new Date();
              return alertDate.toDateString() === today.toDateString();
            }).length}
            trend={{
              value: 25,
              direction: 'down',
              label: 'vs yesterday'
            }}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            }
          />

          <DataCard
            title="Avg WQI (7 days)"
            value={75}
            trend={{
              value: 3,
              direction: 'up',
              label: 'vs last week'
            }}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />

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
    </DashboardLayout>
  );
};

export default Dashboard;