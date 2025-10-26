import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  UserIcon,
  Cog6ToothIcon,
  BellIcon,
  PowerIcon
} from '@heroicons/react/24/outline';
import { Droplet, Activity } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface ConsumerDashboardProps {
  // Optional props for customization
}

/**
 * Consumer Dashboard Component
 * ✅ Optimized with React.memo to prevent unnecessary re-renders
 * ✅ Uses useCallback for event handlers
 * ✅ Uses useMemo for expensive computations
 */
const ConsumerDashboard: React.FC<ConsumerDashboardProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  // ✅ Fetch dashboard data with caching via custom hook
  const { data: dashboardData, isLoading, error, refetch } = useDashboardData('consumer');
  
  // ✅ Real-time updates with WebSocket
  const { latestUpdate, isConnected } = useRealTimeUpdates('consumer-updates', {
    autoConnect: true
  });

  // ✅ Memoized logout handler - prevents recreation on every render
  const handleLogout = useCallback(async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, [logout, navigate]);

  // ✅ Memoized navigation handlers
  const handleBackToLanding = useCallback(() => {
    navigate('/');
  }, [navigate]);

  const toggleSettings = useCallback(() => {
    setShowSettings(prev => !prev);
  }, []);

  const toggleExportModal = useCallback(() => {
    setShowExportModal(prev => !prev);
  }, []);

  // ✅ Memoized current reading - only recalculates when data changes
  const currentReading = useMemo(() => {
    if (!dashboardData || !('currentReading' in dashboardData)) return null;
    return dashboardData.currentReading || null;
  }, [dashboardData]);

  // ✅ Memoized alerts - only recalculates when data changes
  const recentAlerts = useMemo(() => {
    if (!dashboardData || !('alerts' in dashboardData)) return [];
    return dashboardData.alerts?.slice(0, 5) || [];
  }, [dashboardData]);

  // ✅ Memoized WQI calculation
  const waterQualityIndex = useMemo(() => {
    if (!currentReading) return 0;
    
    // Calculate WQI from sensor readings
    const { pH, turbidity, tds, temperature } = currentReading;
    
    // Simple WQI calculation (0-100 scale)
    const pHScore = pH >= 6.5 && pH <= 8.5 ? 100 : Math.max(0, 100 - Math.abs(7.0 - pH) * 20);
    const turbidityScore = Math.max(0, 100 - (turbidity * 20));
    const tdsScore = Math.max(0, 100 - (tds / 5));
    
    return Math.round((pHScore + turbidityScore + tdsScore) / 3);
  }, [currentReading]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  // Update dashboard when real-time data arrives
  useEffect(() => {
    if (latestUpdate) {
      refetch();
    }
  }, [latestUpdate, refetch]);

  // Loading state
  if (!user || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Dashboard</h1>
          <p className="text-gray-600 mb-6">{error.message}</p>
          <button 
            onClick={() => refetch()}
            className="bg-aqua-600 hover:bg-aqua-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Settings view
  if (showSettings) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={toggleSettings}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200 font-medium"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span>Back to Dashboard</span>
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-xl font-bold text-gray-900">Dashboard Settings</h1>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            >
              <PowerIcon className="w-5 h-5" />
              <span>Logout</span>
            </button>
          </div>
        </header>

        <main className="max-w-4xl mx-auto p-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* User Profile Card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <p className="text-gray-900">{user.profile?.firstName} {user.profile?.lastName}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <p className="text-gray-900 capitalize">{user.role}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Member Since</label>
                  <p className="text-gray-900">
                    {new Date().toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </p>
                </div>
              </div>
            </div>

            {/* Dashboard Preferences */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Preferences</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Real-time Updates</h3>
                    <p className="text-sm text-gray-600">Receive live water quality updates</p>
                  </div>
                  <div className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent ${isConnected ? 'bg-aqua-600' : 'bg-gray-200'} transition-colors duration-200 ease-in-out`}>
                    <span className={`${isConnected ? 'translate-x-5' : 'translate-x-0'} pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}></span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={toggleSettings}
                  className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                >
                  <Activity className="w-5 h-5 text-aqua-600" />
                  <div className="text-left">
                    <h3 className="font-medium text-gray-900">View Water Quality</h3>
                    <p className="text-sm text-gray-600">Check current water quality metrics</p>
                  </div>
                </button>
                
                <button
                  onClick={toggleExportModal}
                  className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
                >
                  <svg className="w-5 h-5 text-aqua-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <div className="text-left">
                    <h3 className="font-medium text-gray-900">Export Data</h3>
                    <p className="text-sm text-gray-600">Download your water quality data</p>
                  </div>
                </button>
              </div>
            </div>
          </motion.div>
        </main>

        {/* Data Export Modal */}
        <DataExportModal
          isOpen={showExportModal}
          onClose={toggleExportModal}
          userRole="consumer"
        />
      </div>
    );
  }

  // Main dashboard view
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-aqua-100 rounded-lg">
                <Droplet className="w-6 h-6 text-aqua-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Consumer Dashboard</h1>
                <p className="text-sm text-gray-600">Welcome back, {user.profile?.firstName || user.email}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1.5 rounded-full text-sm font-medium">
              <UserIcon className="w-4 h-4" />
              <span>Consumer</span>
            </div>
            
            <NotificationCenter userRole="consumer" />
            
            <button
              onClick={toggleSettings}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              title="Settings"
            >
              <Cog6ToothIcon className="w-5 h-5" />
            </button>

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              title="Logout"
            >
              <PowerIcon className="w-5 h-5" />
              <span className="text-sm">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        {/* Connection Status Indicator */}
      {!isConnected && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
          <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.964-1.333-2.732 0L3.732 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="text-sm text-amber-800">Real-time updates disconnected. Showing cached data.</span>
        </div>
      )}

      {/* Water Quality Index */}
      <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Water Quality Index</h2>
        <div className="text-center">
          <div className="text-6xl font-bold text-aqua-600 mb-2">{waterQualityIndex}</div>
          <div className="text-sm text-gray-600">
            {waterQualityIndex >= 80 ? 'Excellent' : waterQualityIndex >= 60 ? 'Good' : waterQualityIndex >= 40 ? 'Fair' : 'Poor'}
          </div>
        </div>
      </div>

      {/* Sensor Readings */}
      {currentReading && (
        <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Readings</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-600">pH</div>
              <div className="text-2xl font-bold text-gray-900">{currentReading.pH}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Turbidity</div>
              <div className="text-2xl font-bold text-gray-900">{currentReading.turbidity}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">TDS</div>
              <div className="text-2xl font-bold text-gray-900">{currentReading.tds}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Temperature</div>
              <div className="text-2xl font-bold text-gray-900">{currentReading.temperature}°C</div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      {recentAlerts.length > 0 && (
        <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h2>
          <div className="space-y-2">
            {recentAlerts.map((alert, index) => (
              <div key={index} className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="text-sm font-medium text-amber-900">{alert.message || 'Alert'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Devices</span>
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Active</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {dashboardData && 'devices' in dashboardData ? dashboardData.devices?.length || 0 : 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Alerts</span>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Today</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{recentAlerts.length}</div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Avg WQI</span>
            <span className="text-xs bg-aqua-100 text-aqua-800 px-2 py-1 rounded-full">7 Days</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{waterQualityIndex}</div>
        </div>
      </div>

      {/* Notification Center */}
      <NotificationCenter userRole="consumer" />

        {/* Data Export Modal */}
        <DataExportModal
          isOpen={showExportModal}
          onClose={toggleExportModal}
          userRole="consumer"
        />
      </main>
    </div>
  );
});

// ✅ Display name for debugging
ConsumerDashboard.displayName = 'ConsumerDashboard';

export default ConsumerDashboard;
