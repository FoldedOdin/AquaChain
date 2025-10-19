import { useState, useEffect } from 'react';
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
import {
  getSystemHealthMetrics,
  getDeviceFleetStatus,
  getPerformanceMetrics,
  getAlertAnalytics
} from '../services/adminService';
import {
  SystemHealthMetrics,
  DeviceFleetStatus,
  PerformanceMetrics,
  AlertAnalytics as AlertAnalyticsType
} from '../types/admin';

type TabType = 'overview' | 'fleet' | 'performance' | 'alerts' | 'users' | 'devices' | 'technicians' | 'compliance' | 'audit' | 'config';

const AdminDashboard = () => {
  const [healthMetrics, setHealthMetrics] = useState<SystemHealthMetrics | null>(null);
  const [deviceFleet, setDeviceFleet] = useState<DeviceFleetStatus[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics[]>([]);
  const [alertAnalytics, setAlertAnalytics] = useState<AlertAnalyticsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [health, fleet, performance, alerts] = await Promise.all([
        getSystemHealthMetrics(),
        getDeviceFleetStatus(),
        getPerformanceMetrics('24h'),
        getAlertAnalytics(7)
      ]);

      setHealthMetrics(health);
      setDeviceFleet(fleet);
      setPerformanceMetrics(performance);
      setAlertAnalytics(alerts);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePerformanceTimeRangeChange = async (range: '1h' | '24h' | '7d' | '30d') => {
    try {
      const metrics = await getPerformanceMetrics(range);
      setPerformanceMetrics(metrics);
    } catch (error) {
      console.error('Error loading performance metrics:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Administrator Dashboard</h1>
          <p className="text-gray-600 mt-2">System monitoring and management</p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-4 overflow-x-auto">
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
          {activeTab === 'overview' && healthMetrics && (
            <>
              <SystemHealthCard metrics={healthMetrics} />
              {performanceMetrics.length > 0 && (
                <PerformanceMetricsChart
                  metrics={performanceMetrics}
                  onTimeRangeChange={handlePerformanceTimeRangeChange}
                />
              )}
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

        {/* Quick Actions */}
        {activeTab === 'overview' && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
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
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
