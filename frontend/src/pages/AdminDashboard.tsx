import { useState, useMemo, useCallback, lazy, Suspense } from 'react';
import SystemHealthCard from '../components/Admin/SystemHealthCard';
import DeviceFleetOverview from '../components/Admin/DeviceFleetOverview';
import PerformanceMetricsChart from '../components/Admin/PerformanceMetricsChart';
import AlertAnalytics from '../components/Admin/AlertAnalytics';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import DataCard from '../components/Dashboard/DataCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';
import { useDataExport } from '../hooks/useDataExport';
import { getPerformanceMetrics } from '../services/adminService';
import { SystemHealthMetrics, AlertAnalytics as AlertAnalyticsType } from '../types/admin';

// Lazy load heavy admin components
const UserManagement = lazy(() => import('../components/Admin/UserManagement'));
const DeviceManagement = lazy(() => import('../components/Admin/DeviceManagement'));
const TechnicianManagement = lazy(() => import('../components/Admin/TechnicianManagement'));
const ComplianceReporting = lazy(() => import('../components/Admin/ComplianceReporting'));
const AuditTrailViewer = lazy(() => import('../components/Admin/AuditTrailViewer'));
const SystemConfiguration = lazy(() => import('../components/Admin/SystemConfiguration'));
const ShipmentTracking = lazy(() => import('../components/Admin/ShipmentTracking'));

// Loading component for tab content
const TabLoadingFallback = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

type TabType = 'overview' | 'fleet' | 'performance' | 'alerts' | 'shipments' | 'users' | 'devices' | 'technicians' | 'compliance' | 'audit' | 'config';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [performanceMetrics, setPerformanceMetrics] = useState<any[]>([]);

  // Use shared hooks
  const dashboardData = useDashboardData();
  const { latestUpdate } = useRealTimeUpdates('admin-alerts');
  const { exportData, exporting } = useDataExport();

  // Extract data from the hook with memoization
  const isLoading = dashboardData.loading;
  const error = dashboardData.error;
  const healthMetrics = useMemo((): SystemHealthMetrics => ({
    timestamp: new Date().toISOString(),
    criticalPathUptime: 99.95,
    apiUptime: 99.9,
    notificationUptime: 99.8,
    errorRate: 0.05,
    activeDevices: dashboardData.devices?.filter((d: any) => d.status === 'online').length || 0,
    totalDevices: dashboardData.devices?.length || 0,
    activeAlerts: 0,
    pendingServiceRequests: 0
  }), [dashboardData.devices]);
  const deviceFleet = useMemo(() => dashboardData.devices || [], [dashboardData.devices]);
  const alertAnalytics = useMemo((): AlertAnalyticsType => ({
    period: new Date().toISOString().split('T')[0],
    totalAlerts: 0,
    criticalAlerts: 0,
    warningAlerts: 0,
    safeAlerts: 0,
    avgResolutionTime: 0,
    alertsByDevice: [],
    alertsByType: []
  }), []);
  
  // Refetch function
  const refetch = useCallback(() => {
    window.location.reload();
  }, []);

  // Memoize computed values
  const activeDeviceCount = useMemo(
    () => deviceFleet.filter((d: any) => d.status === 'online').length,
    [deviceFleet]
  );

  const criticalAlertCount = useMemo(
    () => alertAnalytics?.criticalAlerts || 0,
    [alertAnalytics]
  );

  // Memoize event handlers
  const handlePerformanceTimeRangeChange = useCallback(async (range: '1h' | '24h' | '7d' | '30d') => {
    try {
      const metrics = await getPerformanceMetrics(range);
      setPerformanceMetrics(metrics);
    } catch (error) {
      console.error('Error loading performance metrics:', error);
    }
  }, []);

  const handleExportData = useCallback(async () => {
    try {
      await exportData(
        {
          healthMetrics,
          deviceFleet,
          performanceMetrics,
          alertAnalytics
        },
        {
          format: 'json',
          filename: `admin-dashboard-${new Date().toISOString().split('T')[0]}.json`,
          includeMetadata: true
        }
      );
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  }, [exportData, healthMetrics, deviceFleet, performanceMetrics, alertAnalytics]);

  const handleTabChange = useCallback((tab: TabType) => {
    setActiveTab(tab);
  }, []);

  if (isLoading) {
    return (
      <DashboardLayout
        role="admin"
        header={
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <DataCard key={i} title="" value="" loading={true} />
          ))}
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout
        role="admin"
        header={
          <>
            <h1 className="text-3xl font-bold text-gray-900">Administrator Dashboard</h1>
            <p className="text-gray-600 mt-2">System monitoring and management</p>
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
      role="admin"
      header={
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Administrator Dashboard</h1>
            <p className="text-gray-600 mt-2">System monitoring and management</p>
            {latestUpdate && (
              <p className="text-sm text-blue-600 mt-1">
                Latest update: {new Date(latestUpdate.timestamp || new Date()).toLocaleTimeString()}
              </p>
            )}
          </div>
          <button
            onClick={handleExportData}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {exporting ? 'Exporting...' : 'Export Data'}
          </button>
        </div>
      }
    >

      {/* Tab Navigation */}
      <div className="mb-6 border-b border-gray-200 bg-white rounded-lg shadow-sm">
        <nav className="-mb-px flex space-x-4 overflow-x-auto px-4">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'fleet', label: 'Fleet' },
            { id: 'performance', label: 'Performance' },
            { id: 'alerts', label: 'Alerts' },
            { id: 'shipments', label: 'Shipments' },
            { id: 'users', label: 'Users' },
            { id: 'devices', label: 'Devices' },
            { id: 'technicians', label: 'Technicians' },
            { id: 'compliance', label: 'Compliance' },
            { id: 'audit', label: 'Audit Trail' },
            { id: 'config', label: 'Config' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id as TabType)}
              className={`py-4 px-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            {/* Quick Stats using DataCard */}
            {healthMetrics && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <DataCard
                  title="System Health"
                  value={`${Math.round((healthMetrics.criticalPathUptime + healthMetrics.apiUptime + healthMetrics.notificationUptime) / 3)}%`}
                  trend={{
                    value: 2.5,
                    direction: 'up',
                    label: 'vs last week'
                  }}
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                />
                <DataCard
                  title="Active Devices"
                  value={activeDeviceCount}
                  subtitle={`of ${deviceFleet.length}`}
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                  }
                />
                <DataCard
                  title="Critical Alerts"
                  value={criticalAlertCount}
                  trend={{
                    value: 15,
                    direction: 'down',
                    label: 'vs yesterday'
                  }}
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  }
                />
              </div>
            )}

            {healthMetrics && <SystemHealthCard metrics={healthMetrics} />}
            
            {performanceMetrics.length > 0 && (
              <PerformanceMetricsChart
                metrics={performanceMetrics}
                onTimeRangeChange={handlePerformanceTimeRangeChange}
              />
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <button 
                  onClick={() => handleTabChange('users')}
                  className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Manage Users
                </button>
                <button 
                  onClick={() => handleTabChange('devices')}
                  className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Register Device
                </button>
                <button 
                  onClick={() => handleTabChange('shipments')}
                  className="px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Track Shipments
                </button>
                <button 
                  onClick={() => handleTabChange('compliance')}
                  className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'fleet' && (
          <DeviceFleetOverview devices={deviceFleet.map((d: any) => ({
            deviceId: d.deviceId,
            status: d.status.toLowerCase() as 'online' | 'offline' | 'warning' | 'error',
            lastSeen: d.lastData?.toISOString() || new Date().toISOString(),
            uptime: 99,
            location: {
              latitude: d.coordinates?.lat || 0,
              longitude: d.coordinates?.lng || 0,
              address: d.location || 'Unknown'
            },
            currentWQI: d.wqi || 0,
            batteryLevel: d.battery || 0,
            signalStrength: d.metadata?.signalStrength || -50,
            consumerId: 'unknown',
            consumerName: 'Unknown',
            maintenanceHistory: []
          }))} />
        )}

        {activeTab === 'performance' && performanceMetrics.length > 0 && (
          <PerformanceMetricsChart
            metrics={performanceMetrics}
            onTimeRangeChange={handlePerformanceTimeRangeChange}
          />
        )}

        {activeTab === 'alerts' && alertAnalytics && (
          <AlertAnalytics analytics={alertAnalytics} />
        )}

        {activeTab === 'shipments' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <ShipmentTracking />
          </Suspense>
        )}

        {activeTab === 'users' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <UserManagement />
          </Suspense>
        )}

        {activeTab === 'devices' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <DeviceManagement />
          </Suspense>
        )}

        {activeTab === 'technicians' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <TechnicianManagement />
          </Suspense>
        )}

        {activeTab === 'compliance' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <ComplianceReporting />
          </Suspense>
        )}

        {activeTab === 'audit' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <AuditTrailViewer />
          </Suspense>
        )}

        {activeTab === 'config' && (
          <Suspense fallback={<TabLoadingFallback />}>
            <SystemConfiguration />
          </Suspense>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
