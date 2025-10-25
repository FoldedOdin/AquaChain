import { useState, useMemo, useCallback } from 'react';
import SystemHealthCard from '../components/Admin/SystemHealthCard';
import DeviceFleetOverview from '../components/Admin/DeviceFleetOverview';
import PerformanceMetricsChart from '../components/Admin/PerformanceMetricsChart';
import AlertAnalytics from '../components/Admin/AlertAnalytics';
import UserManagement from '../components/Admin/UserManagement';
import DeviceManagement from '../components/Admin/DeviceManagement';
import TechnicianManagement from '../components/Admin/TechnicianManagement';
import ComplianceReporting from '../components/Admin/ComplianceReporting';
import AuditTrailViewer from '../components/Admin/AuditTrailViewer';
import SystemConfiguration from '../components/Admin/SystemConfiguration';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import DataCard from '../components/Dashboard/DataCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';
import { useDataExport } from '../hooks/useDataExport';
import { getPerformanceMetrics } from '../services/adminService';

type TabType = 'overview' | 'fleet' | 'performance' | 'alerts' | 'users' | 'devices' | 'technicians' | 'compliance' | 'audit' | 'config';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [performanceMetrics, setPerformanceMetrics] = useState<any[]>([]);

  // Use shared hooks
  const { data, loading, error, refetch } = useDashboardData('admin');
  const { latestUpdate } = useRealTimeUpdates('admin-alerts');
  const { exportData, exporting } = useDataExport();

  // Extract data from the hook with memoization
  const adminData = data as any;
  const healthMetrics = useMemo(() => adminData?.healthMetrics, [adminData]);
  const deviceFleet = useMemo(() => adminData?.deviceFleet || [], [adminData]);
  const alertAnalytics = useMemo(() => adminData?.alertAnalytics, [adminData]);

  // Memoize computed values
  const activeDeviceCount = useMemo(
    () => deviceFleet.filter((d: any) => d.status === 'online').length,
    [deviceFleet]
  );

  const criticalAlertCount = useMemo(
    () => alertAnalytics?.criticalCount || 0,
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

  if (loading) {
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
            onClick={refetch}
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
                Latest update: {new Date(latestUpdate.timestamp).toLocaleTimeString()}
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
            { id: 'users', label: 'Users' },
            { id: 'devices', label: 'Devices' },
            { id: 'technicians', label: 'Technicians' },
            { id: 'compliance', label: 'Compliance' },
            { id: 'audit', label: 'Audit Trail' },
            { id: 'config', label: 'Config' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
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
                  value={`${healthMetrics.overallHealth || 0}%`}
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
                  value={deviceFleet.filter((d: any) => d.status === 'online').length}
                  subtitle={`of ${deviceFleet.length}`}
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                  }
                />
                <DataCard
                  title="Critical Alerts"
                  value={alertAnalytics?.criticalCount || 0}
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button 
                  onClick={() => setActiveTab('users')}
                  className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Manage Users
                </button>
                <button 
                  onClick={() => setActiveTab('devices')}
                  className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Register Device
                </button>
                <button 
                  onClick={() => setActiveTab('compliance')}
                  className="px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'fleet' && (
          <DeviceFleetOverview devices={deviceFleet} />
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

        {activeTab === 'users' && <UserManagement />}

        {activeTab === 'devices' && <DeviceManagement />}

        {activeTab === 'technicians' && <TechnicianManagement />}

        {activeTab === 'compliance' && <ComplianceReporting />}

        {activeTab === 'audit' && <AuditTrailViewer />}

        {activeTab === 'config' && <SystemConfiguration />}
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
