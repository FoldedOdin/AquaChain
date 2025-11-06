import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeftIcon,
  UserIcon,
  Cog6ToothIcon,
  BellIcon,
  PowerIcon,
  ArrowPathIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { Droplet, Activity, Thermometer, Beaker, Waves } from 'lucide-react';
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
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date>(new Date());

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

  const handleManualRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await refetch();
    setLastRefreshTime(new Date());
    setTimeout(() => setIsRefreshing(false), 500);
  }, [refetch]);

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

  // ✅ Memoized WQI calculation with detailed metrics
  const waterQualityMetrics = useMemo(() => {
    if (!currentReading) return { wqi: 0, status: 'Unknown', color: 'gray', metrics: {} };
    
    // Calculate WQI from sensor readings
    const { pH, turbidity, tds, temperature } = currentReading;
    
    // Individual parameter scores (0-100 scale)
    const pHScore = pH >= 6.5 && pH <= 8.5 ? 100 : Math.max(0, 100 - Math.abs(7.0 - pH) * 20);
    const turbidityScore = Math.max(0, 100 - (turbidity * 20));
    const tdsScore = Math.max(0, 100 - (tds / 5));
    const tempScore = temperature >= 15 && temperature <= 25 ? 100 : Math.max(0, 100 - Math.abs(20 - temperature) * 5);
    
    const wqi = Math.round((pHScore + turbidityScore + tdsScore + tempScore) / 4);
    
    // Determine status and color
    let status = 'Poor';
    let color = 'red';
    if (wqi >= 90) { status = 'Excellent'; color = 'green'; }
    else if (wqi >= 75) { status = 'Good'; color = 'blue'; }
    else if (wqi >= 50) { status = 'Fair'; color = 'yellow'; }
    else if (wqi >= 25) { status = 'Poor'; color = 'orange'; }
    else { status = 'Very Poor'; color = 'red'; }
    
    return {
      wqi,
      status,
      color,
      metrics: {
        pH: { value: pH, score: pHScore, status: pH >= 6.5 && pH <= 8.5 ? 'good' : 'warning' },
        turbidity: { value: turbidity, score: turbidityScore, status: turbidity < 5 ? 'good' : 'warning' },
        tds: { value: tds, score: tdsScore, status: tds < 500 ? 'good' : 'warning' },
        temperature: { value: temperature, score: tempScore, status: temperature >= 15 && temperature <= 25 ? 'good' : 'warning' }
      }
    };
  }, [currentReading]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  // Update last refresh time when data changes
  useEffect(() => {
    if (dashboardData) {
      setLastRefreshTime(new Date());
    }
  }, [dashboardData]);

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
            {/* Connection Status */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              isConnected 
                ? 'bg-green-100 text-green-700' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
              <span>{isConnected ? 'Live' : 'Offline'}</span>
            </div>

            {/* Manual Refresh */}
            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200 disabled:opacity-50"
              title="Refresh data"
            >
              <ArrowPathIcon className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
            
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
        {/* Last Updated Info */}
        <div className="mb-4 flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <ClockIcon className="w-4 h-4" />
            <span>Last updated: {lastRefreshTime.toLocaleTimeString()}</span>
          </div>
          {!isConnected && (
            <div className="flex items-center gap-2 text-amber-600">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span>Real-time updates unavailable</span>
            </div>
          )}
        </div>

        {/* Water Quality Index - Enhanced */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-lg border border-gray-200 p-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Water Quality Index</h2>
            <div className={`px-4 py-2 rounded-full text-sm font-semibold ${
              waterQualityMetrics.color === 'green' ? 'bg-green-100 text-green-700' :
              waterQualityMetrics.color === 'blue' ? 'bg-blue-100 text-blue-700' :
              waterQualityMetrics.color === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
              waterQualityMetrics.color === 'orange' ? 'bg-orange-100 text-orange-700' :
              'bg-red-100 text-red-700'
            }`}>
              {waterQualityMetrics.status}
            </div>
          </div>
          
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <svg className="w-48 h-48 transform -rotate-90">
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  className="text-gray-200"
                />
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 88}`}
                  strokeDashoffset={`${2 * Math.PI * 88 * (1 - waterQualityMetrics.wqi / 100)}`}
                  className={`transition-all duration-1000 ${
                    waterQualityMetrics.color === 'green' ? 'text-green-500' :
                    waterQualityMetrics.color === 'blue' ? 'text-blue-500' :
                    waterQualityMetrics.color === 'yellow' ? 'text-yellow-500' :
                    waterQualityMetrics.color === 'orange' ? 'text-orange-500' :
                    'text-red-500'
                  }`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-5xl font-bold text-gray-900">{waterQualityMetrics.wqi}</div>
                  <div className="text-sm text-gray-600 mt-1">out of 100</div>
                </div>
              </div>
            </div>
          </div>

          {/* Parameter Breakdown */}
          {currentReading && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* pH */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Beaker className="w-5 h-5 text-purple-500" />
                    <span className="text-sm font-medium text-gray-700">pH Level</span>
                  </div>
                  {waterQualityMetrics.metrics.pH?.status === 'good' ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
                  )}
                </div>
                <div className="text-3xl font-bold text-gray-900">{currentReading.pH}</div>
                <div className="text-xs text-gray-500 mt-1">Ideal: 6.5-8.5</div>
              </div>

              {/* Turbidity */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Waves className="w-5 h-5 text-blue-500" />
                    <span className="text-sm font-medium text-gray-700">Turbidity</span>
                  </div>
                  {waterQualityMetrics.metrics.turbidity?.status === 'good' ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
                  )}
                </div>
                <div className="text-3xl font-bold text-gray-900">{currentReading.turbidity}</div>
                <div className="text-xs text-gray-500 mt-1">NTU (Lower is better)</div>
              </div>

              {/* TDS */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Droplet className="w-5 h-5 text-cyan-500" />
                    <span className="text-sm font-medium text-gray-700">TDS</span>
                  </div>
                  {waterQualityMetrics.metrics.tds?.status === 'good' ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
                  )}
                </div>
                <div className="text-3xl font-bold text-gray-900">{currentReading.tds}</div>
                <div className="text-xs text-gray-500 mt-1">ppm (Ideal: &lt;500)</div>
              </div>

              {/* Temperature */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-5 h-5 text-red-500" />
                    <span className="text-sm font-medium text-gray-700">Temperature</span>
                  </div>
                  {waterQualityMetrics.metrics.temperature?.status === 'good' ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
                  )}
                </div>
                <div className="text-3xl font-bold text-gray-900">{currentReading.temperature}°C</div>
                <div className="text-xs text-gray-500 mt-1">Ideal: 15-25°C</div>
              </div>
            </div>
          )}
        </motion.div>

      {/* Recent Alerts - Enhanced */}
      {recentAlerts.length > 0 ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
            <span className="text-sm text-gray-600">{recentAlerts.length} active</span>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {recentAlerts.map((alert, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-lg hover:bg-amber-100 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-amber-900">{alert.message || 'Water quality alert'}</div>
                      <div className="text-xs text-amber-700 mt-1">
                        {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div className="text-center py-8">
            <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">All Clear!</h3>
            <p className="text-sm text-gray-600">No active alerts. Your water quality is within normal parameters.</p>
          </div>
        </motion.div>
      )}

      {/* Quick Stats - Enhanced */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6"
        >
          {/* Devices Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
              <span className="text-xs bg-green-100 text-green-800 px-3 py-1 rounded-full font-medium">Active</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">
              {dashboardData && 'devices' in dashboardData ? dashboardData.devices?.length || 0 : 0}
            </div>
            <div className="text-sm text-gray-600">Connected Devices</div>
          </div>

          {/* Alerts Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <BellIcon className="w-6 h-6 text-amber-600" />
              </div>
              <span className="text-xs bg-amber-100 text-amber-800 px-3 py-1 rounded-full font-medium">Today</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{recentAlerts.length}</div>
            <div className="text-sm text-gray-600">Active Alerts</div>
          </div>

          {/* WQI Trend Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${
                waterQualityMetrics.color === 'green' ? 'bg-green-100' :
                waterQualityMetrics.color === 'blue' ? 'bg-blue-100' :
                waterQualityMetrics.color === 'yellow' ? 'bg-yellow-100' :
                'bg-orange-100'
              }`}>
                <ChartBarIcon className={`w-6 h-6 ${
                  waterQualityMetrics.color === 'green' ? 'text-green-600' :
                  waterQualityMetrics.color === 'blue' ? 'text-blue-600' :
                  waterQualityMetrics.color === 'yellow' ? 'text-yellow-600' :
                  'text-orange-600'
                }`} />
              </div>
              <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                waterQualityMetrics.color === 'green' ? 'bg-green-100 text-green-800' :
                waterQualityMetrics.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                waterQualityMetrics.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                'bg-orange-100 text-orange-800'
              }`}>Current</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{waterQualityMetrics.wqi}</div>
            <div className="text-sm text-gray-600">Water Quality Index</div>
          </div>
        </motion.div>

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
