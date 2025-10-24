import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  BuildingOfficeIcon,
  Cog6ToothIcon,
  BellIcon,
  PowerIcon,
  UsersIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { Activity, Users, Database, Droplet, TrendingUp, TrendingDown } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useRealTimeData } from '../../hooks/useRealTimeData';
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface AdminDashboardProps {
  // Optional props for customization
}

const AdminDashboard: React.FC<AdminDashboardProps> = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  
  // Use real-time data hook instead of demo data
  const {
    waterQuality,
    latestReading,
    devices,
    alerts,
    stats,
    isLoading,
    isConnected,
    lastUpdated,
    error,
    refresh
  } = useRealTimeData({
    enableRealTime: true,
    refreshInterval: 30000,
    autoReconnect: true
  });

  // Redirect to login if not authenticated or not admin
  useEffect(() => {
    if (!user) {
      navigate('/');
    } else if (user.role !== 'admin') {
      // Redirect non-admin users to their appropriate dashboard
      navigate(`/dashboard/${user.role}`);
    }
  }, [user, navigate]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleBackToLanding = () => {
    navigate('/');
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  // If showing demo viewer, render it with auditor role
  if (showDemoViewer) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Custom Header for Admin Dashboard */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BuildingOfficeIcon className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    AquaChain Admin Dashboard
                  </h1>
                  <p className="text-sm text-gray-600">
                    System Administration - {user.profile?.firstName || user.email}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full text-sm font-medium">
                <ShieldCheckIcon className="w-4 h-4" />
                <span>Administrator</span>
              </div>
              
              <NotificationCenter userRole="admin" />
              
              <button
                onClick={() => setShowDemoViewer(false)}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Admin Settings"
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

        {/* Render the demo dashboard with auditor role pre-selected */}
        <div className="relative">
          <DemoDashboardViewer
            isOpen={true}
            onClose={() => setShowDemoViewer(false)}
            onBackToLanding={handleBackToLanding}
            initialRole="auditor"
          />
        </div>
      </div>
    );
  }

  // Admin settings/management view
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowDemoViewer(true)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200 font-medium"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="text-xl font-bold text-gray-900">System Administration</h1>
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

      <main className="max-w-6xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Admin Profile Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Administrator Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <p className="text-gray-900">{user.profile?.firstName} {user.profile?.lastName}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p className="text-gray-900">{user.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Admin Level</label>
                <p className="text-gray-900">System Administrator</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Admin ID</label>
                <p className="text-gray-900 font-mono">ADMIN-{user.userId?.slice(-6) || '001234'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Login</label>
                <p className="text-gray-900">
                  {new Date().toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
                <p className="text-gray-900">Full System Access</p>
              </div>
            </div>
          </div>

          {/* System Overview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <UsersIcon className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900">Total Users</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">1,247</div>
                <div className="text-sm text-blue-700">+23 this week</div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">Active Devices</span>
                </div>
                <div className="text-2xl font-bold text-green-900">89</div>
                <div className="text-sm text-green-700">98.9% uptime</div>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ChartBarIcon className="w-5 h-5 text-purple-600" />
                  <span className="font-semibold text-purple-900">Data Points</span>
                </div>
                <div className="text-2xl font-bold text-purple-900">2.4M</div>
                <div className="text-sm text-purple-700">Today</div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <BellIcon className="w-5 h-5 text-amber-600" />
                  <span className="font-semibold text-amber-900">Active Alerts</span>
                </div>
                <div className="text-2xl font-bold text-amber-900">3</div>
                <div className="text-sm text-amber-700">2 critical</div>
              </div>
            </div>
          </div>

          {/* User Management */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">User Management</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Consumers</span>
                    <span className="text-lg font-bold text-gray-900">1,089</span>
                  </div>
                  <div className="text-xs text-gray-600">87% of total users</div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Technicians</span>
                    <span className="text-lg font-bold text-gray-900">156</span>
                  </div>
                  <div className="text-xs text-gray-600">12% of total users</div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Administrators</span>
                    <span className="text-lg font-bold text-gray-900">2</span>
                  </div>
                  <div className="text-xs text-gray-600">1% of total users</div>
                </div>
              </div>
            </div>
          </div>

          {/* System Settings */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Settings</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Real-time Monitoring</h3>
                  <p className="text-sm text-gray-600">Enable continuous data collection from all sensors</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-purple-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Automatic Alerts</h3>
                  <p className="text-sm text-gray-600">Send notifications when thresholds are exceeded</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-purple-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Data Backup</h3>
                  <p className="text-sm text-gray-600">Automatic daily backups to secure storage</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-purple-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Maintenance Mode</h3>
                  <p className="text-sm text-gray-600">Temporarily disable public access for maintenance</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2">
                  <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
            </div>
          </div>

          {/* System Health Monitoring */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health Monitoring</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">API Services</span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Healthy</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Database</span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Healthy</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                    <span className="text-sm font-medium text-amber-900">Backup System</span>
                  </div>
                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">Warning</span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Network</span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Healthy</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Authentication</span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Healthy</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Monitoring</span>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Healthy</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent System Events */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent System Events</h2>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 border-l-4 border-green-500 bg-green-50">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-green-900">System Backup Completed</p>
                    <span className="text-xs text-green-700">2:30 AM</span>
                  </div>
                  <p className="text-xs text-green-700">Daily backup completed successfully - 2.4GB archived</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border-l-4 border-blue-500 bg-blue-50">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-blue-900">New User Registration</p>
                    <span className="text-xs text-blue-700">1 hour ago</span>
                  </div>
                  <p className="text-xs text-blue-700">3 new consumer accounts created and verified</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border-l-4 border-amber-500 bg-amber-50">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-amber-900">Sensor Maintenance Alert</p>
                    <span className="text-xs text-amber-700">3 hours ago</span>
                  </div>
                  <p className="text-xs text-amber-700">Station #47 pH sensor requires calibration</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border-l-4 border-purple-500 bg-purple-50">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-purple-900">System Update Deployed</p>
                    <span className="text-xs text-purple-700">Yesterday</span>
                  </div>
                  <p className="text-xs text-purple-700">Dashboard v2.1.3 deployed with enhanced security features</p>
                </div>
              </div>
            </div>
          </div>

          {/* Compliance & Audit */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance & Audit Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldCheckIcon className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">EPA Compliance</span>
                </div>
                <div className="text-2xl font-bold text-green-900">98.7%</div>
                <div className="text-sm text-green-700">All standards met</div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900">Data Integrity</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">99.9%</div>
                <div className="text-sm text-blue-700">No data loss detected</div>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ChartBarIcon className="w-5 h-5 text-purple-600" />
                  <span className="font-semibold text-purple-900">Audit Score</span>
                </div>
                <div className="text-2xl font-bold text-purple-900">A+</div>
                <div className="text-sm text-purple-700">Last audit: Oct 2024</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Administrative Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => setShowDemoViewer(true)}
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <ChartBarIcon className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">System Overview</h3>
                  <p className="text-sm text-gray-600">View compliance and audit dashboard</p>
                </div>
              </button>
              
              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <Users className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">User Management</h3>
                  <p className="text-sm text-gray-600">Manage user accounts and permissions</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <Database className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">System Logs</h3>
                  <p className="text-sm text-gray-600">View system activity and audit logs</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <Activity className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Device Management</h3>
                  <p className="text-sm text-gray-600">Configure and monitor all sensors</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <BellIcon className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Alert Configuration</h3>
                  <p className="text-sm text-gray-600">Set up system-wide alert thresholds</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <ShieldCheckIcon className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Security Settings</h3>
                  <p className="text-sm text-gray-600">Configure security and access controls</p>
                </div>
              </button>

              <button
                onClick={() => setShowExportModal(true)}
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Export System Data</h3>
                  <p className="text-sm text-gray-600">Download comprehensive system reports</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">System Maintenance</h3>
                  <p className="text-sm text-gray-600">Schedule and manage system maintenance</p>
                </div>
              </button>
            </div>
          </div>
        </motion.div>
      </main>

      {/* Data Export Modal */}
      <DataExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        userRole="admin"
      />
    </div>
  );
};

export default AdminDashboard;