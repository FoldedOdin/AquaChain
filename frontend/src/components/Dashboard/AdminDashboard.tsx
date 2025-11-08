import React, { useState, useEffect, useCallback, memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  Cog6ToothIcon,
  PowerIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { 
  Activity, 
  Users, 
  Database, 
  TrendingUp, 
  TrendingDown,
  Server,
  AlertTriangle,
  BarChart3,
  Settings,
  Bell,
  MapPin,
  Eye,
  Edit,
  Trash2,
  Plus,
  UserPlus,
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';
import { useNotifications } from '../../hooks/useNotifications';
import { getAllUsers, getAllDevices, getDeviceFleetStatus } from '../../services/adminService';
import { formatRelativeTime } from '../../utils/dateFormat';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface AdminDashboardProps {
  // Optional props for customization
}

const AdminDashboard: React.FC<AdminDashboardProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedView, setSelectedView] = useState('overview');
  const [deviceFilter, setDeviceFilter] = useState('all');

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useDashboardData('admin');
  const { isConnected } = useRealTimeUpdates('admin-updates', { autoConnect: true });
  const { notifications } = useNotifications();

  // State for dynamic data
  const [users, setUsers] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [deviceFleet, setDeviceFleet] = useState<any[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);

  // Fetch users and devices
  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingData(true);
      try {
        const [usersData, devicesData, fleetData] = await Promise.all([
          getAllUsers(),
          getAllDevices(),
          getDeviceFleetStatus()
        ]);
        setUsers(usersData);
        setDevices(devicesData);
        setDeviceFleet(fleetData);
      } catch (err) {
        console.error('Failed to fetch admin data:', err);
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchData();
  }, []);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-amber-100 text-amber-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'active': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800';
      case 'technician': return 'bg-blue-100 text-blue-800';
      case 'consumer': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Calculate device statistics
  const deviceStats = useMemo(() => {
    const online = deviceFleet.filter(d => d.status === 'online').length;
    const warning = deviceFleet.filter(d => d.status === 'warning').length;
    const offline = deviceFleet.filter(d => d.status === 'offline').length;
    return { online, warning, offline, total: deviceFleet.length };
  }, [deviceFleet]);

  // Calculate user statistics by role
  const userStats = useMemo(() => {
    const consumers = users.filter(u => u.role === 'consumer').length;
    const technicians = users.filter(u => u.role === 'technician').length;
    const admins = users.filter(u => u.role === 'admin').length;
    return { consumers, technicians, admins, total: users.length };
  }, [users]);

  // Device status data for pie chart
  const deviceStatusData = useMemo(() => [
    { name: 'Online', value: deviceStats.online, color: '#10b981' },
    { name: 'Warning', value: deviceStats.warning, color: '#f59e0b' },
    { name: 'Offline', value: deviceStats.offline, color: '#ef4444' },
  ].filter(item => item.value > 0), [deviceStats]);

  // User role data for bar chart
  const userRoleData = useMemo(() => [
    { role: 'Consumer', count: userStats.consumers },
    { role: 'Technician', count: userStats.technicians },
    { role: 'Admin', count: userStats.admins },
  ], [userStats]);

  // Alert trends from notifications
  const alertTrends = useMemo(() => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return {
        date: date.toLocaleDateString('en-US', { weekday: 'short' }),
        alerts: 0
      };
    });

    notifications.forEach(notif => {
      const notifDate = new Date(notif.timestamp);
      const dayIndex = last7Days.findIndex(day => {
        const checkDate = new Date();
        checkDate.setDate(checkDate.getDate() - (6 - last7Days.indexOf(day)));
        return checkDate.toDateString() === notifDate.toDateString();
      });
      if (dayIndex !== -1) {
        last7Days[dayIndex].alerts++;
      }
    });

    return last7Days;
  }, [notifications]);

  // System metrics from dashboard data
  const systemMetrics = useMemo(() => {
    if (!dashboardData || !('performanceMetrics' in dashboardData)) {
      return [];
    }
    const metrics = dashboardData.performanceMetrics || [];
    return metrics.slice(-7).map((m: any, i: number) => ({
      date: new Date(m.timestamp).toLocaleDateString('en-US', { weekday: 'short' }),
      devices: deviceStats.total,
      users: userStats.total
    }));
  }, [dashboardData, deviceStats.total, userStats.total]);

  // Recent activities from notifications
  const recentActivities = useMemo(() => {
    return notifications.slice(0, 4).map(notif => {
      // Determine icon based on notification type
      let icon = Database;
      if (notif.type === 'error' || notif.type === 'warning') {
        icon = AlertTriangle;
      } else if (notif.type === 'success') {
        icon = UserPlus;
      }
      
      return {
        id: notif.id,
        type: notif.type,
        message: notif.message,
        time: formatRelativeTime(notif.timestamp),
        icon,
        color: notif.priority === 'high' ? 'text-red-600' : notif.priority === 'medium' ? 'text-amber-600' : 'text-blue-600'
      };
    });
  }, [notifications]);

  // Filtered devices
  const filteredDevices = useMemo(() => {
    if (deviceFilter === 'all') return deviceFleet;
    return deviceFleet.filter(device => device.status === deviceFilter);
  }, [deviceFilter, deviceFleet]);

  // Performance metrics from dashboard data
  const performanceMetrics = useMemo(() => {
    if (!dashboardData || !('healthMetrics' in dashboardData)) {
      return { uptime: 0, accuracy: 0, satisfaction: 0 };
    }
    const health = dashboardData.healthMetrics;
    return {
      uptime: health?.criticalPathUptime || 0,
      accuracy: health?.apiUptime || 0,
      satisfaction: 4.7 // This would come from user feedback system
    };
  }, [dashboardData]);

  // Memoized handlers
  const handleLogout = useCallback(async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, [logout, navigate]);

  const toggleSettings = useCallback(() => {
    setShowSettings(prev => !prev);
  }, []);

  const toggleExportModal = useCallback(() => {
    setShowExportModal(prev => !prev);
  }, []);

  // Extract admin data
  const adminData = useMemo(() => {
    if (!dashboardData || !('healthMetrics' in dashboardData)) {
      return { healthMetrics: null, deviceFleet: [], performanceMetrics: [], alertAnalytics: null };
    }
    return dashboardData;
  }, [dashboardData]);

  // Active alerts count
  const activeAlertsCount = useMemo(() => {
    return notifications.filter(n => !n.read && n.priority === 'high').length;
  }, [notifications]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  // Loading state
  if (!user || isLoading || isLoadingData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading admin dashboard...</p>
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
              <h1 className="text-xl font-bold text-gray-900">Admin Settings</h1>
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
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Administrator Profile</h2>
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
            </div>
          </motion.div>
        </main>
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
              <div className="p-2 bg-purple-100 rounded-lg">
                <ShieldCheckIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-sm text-gray-600">System Overview & Management</p>
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
        {/* Connection Status */}
        {!isConnected && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="text-sm text-amber-800">Real-time updates disconnected.</span>
          </div>
        )}

        {/* Tabbed Navigation */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setSelectedView('overview')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'overview'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Activity className="w-5 h-5" />
              Overview
            </button>
            <button
              onClick={() => setSelectedView('devices')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'devices'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Server className="w-5 h-5" />
              Devices
            </button>
            <button
              onClick={() => setSelectedView('users')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'users'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Users className="w-5 h-5" />
              Users
            </button>
            <button
              onClick={() => setSelectedView('analytics')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'analytics'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              Analytics
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {selectedView === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* System Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Total Devices</span>
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{deviceStats.total}</div>
                <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                  <span>{deviceStats.online} online, {deviceStats.warning} warning, {deviceStats.offline} offline</span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Total Users</span>
                  <Users className="w-5 h-5 text-green-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{userStats.total}</div>
                <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                  <span>{userStats.consumers} consumers, {userStats.technicians} technicians</span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">System Health</span>
                  <Activity className="w-5 h-5 text-green-600" />
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {adminData.healthMetrics?.criticalPathUptime ? 
                    `${adminData.healthMetrics.criticalPathUptime.toFixed(1)}%` : 
                    'Good'}
                </div>
                <div className="text-xs text-gray-600 mt-1">System uptime</div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Active Alerts</span>
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{activeAlertsCount}</div>
                <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                  <span>Unread high-priority alerts</span>
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* 7-Day Trends */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Overview</h3>
                {systemMetrics.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={systemMetrics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="devices" stroke="#8b5cf6" strokeWidth={2} name="Devices" />
                      <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={2} name="Users" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    No data available
                  </div>
                )}
              </div>

              {/* Device Status Distribution */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Device Status Distribution</h3>
                {deviceStatusData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={deviceStatusData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {deviceStatusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    No devices registered
                  </div>
                )}
              </div>
            </div>

            {/* Recent Activity & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Activity */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                {recentActivities.length > 0 ? (
                  <div className="space-y-3">
                    {recentActivities.map((activity) => (
                      <div key={activity.id} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                        <activity.icon className={`w-5 h-5 ${activity.color} mt-0.5`} />
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{activity.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No recent activity</p>
                )}
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors">
                    <Database className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Backup</span>
                  </button>
                  <button
                    onClick={toggleExportModal}
                    className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
                    <BarChart3 className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Reports</span>
                  </button>
                  <button className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors">
                    <Settings className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Settings</span>
                  </button>
                  <button className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors">
                    <Bell className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Alerts</span>
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Devices Tab */}
        {selectedView === 'devices' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Device Management</h3>
                <div className="flex items-center gap-3">
                  <select
                    value={deviceFilter}
                    onChange={(e) => setDeviceFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Devices ({deviceFleet.length})</option>
                    <option value="online">Online ({deviceStats.online})</option>
                    <option value="warning">Warning ({deviceStats.warning})</option>
                    <option value="offline">Offline ({deviceStats.offline})</option>
                  </select>
                  <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                    <Plus className="w-4 h-4" />
                    Add Device
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                {filteredDevices.length > 0 ? (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Device</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Location</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Owner</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">WQI</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Last Seen</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredDevices.map((device) => (
                        <tr key={device.deviceId} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{device.deviceId}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            <div className="flex items-center gap-1">
                              <MapPin className="w-4 h-4 text-gray-400" />
                              {device.location?.address || 'N/A'}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{device.consumerName || 'Unassigned'}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(device.status)}`}>
                              {device.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{device.currentWQI || 0}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{formatRelativeTime(device.lastSeen)}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <button className="p-1 text-blue-600 hover:bg-blue-50 rounded" title="View">
                                <Eye className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-gray-600 hover:bg-gray-50 rounded" title="Edit">
                                <Edit className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-red-600 hover:bg-red-50 rounded" title="Delete">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    No devices found
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Users Tab */}
        {selectedView === 'users' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
                <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                  <UserPlus className="w-4 h-4" />
                  Add User
                </button>
              </div>

              <div className="overflow-x-auto">
                {users.length > 0 ? (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Email</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Role</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Devices</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Last Login</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.userId} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {user.profile?.firstName} {user.profile?.lastName}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(user.role)}`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{user.deviceCount || 0}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(user.status)}`}>
                              {user.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {user.lastLogin ? formatRelativeTime(user.lastLogin) : 'Never'}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <button className="p-1 text-blue-600 hover:bg-blue-50 rounded" title="View">
                                <Eye className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-gray-600 hover:bg-gray-50 rounded" title="Edit">
                                <Edit className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-red-600 hover:bg-red-50 rounded" title="Delete">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    No users found
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Analytics Tab */}
        {selectedView === 'analytics' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* User Role Distribution */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">User Role Distribution</h3>
                {userRoleData.some(d => d.count > 0) ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={userRoleData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="role" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    No user data available
                  </div>
                )}
              </div>

              {/* Alert Trends */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert Trends (7 Days)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={alertTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="alerts" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {performanceMetrics.uptime.toFixed(1)}%
                  </div>
                  <div className="text-sm font-medium text-gray-700">System Uptime</div>
                  <div className="text-xs text-gray-600 mt-1">Critical path availability</div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {performanceMetrics.accuracy.toFixed(1)}%
                  </div>
                  <div className="text-sm font-medium text-gray-700">API Uptime</div>
                  <div className="text-xs text-gray-600 mt-1">Service availability</div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600 mb-2">
                    {performanceMetrics.satisfaction.toFixed(1)}/5.0
                  </div>
                  <div className="text-sm font-medium text-gray-700">User Satisfaction</div>
                  <div className="text-xs text-gray-600 mt-1">Based on feedback</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Data Export Modal */}
        <DataExportModal
          isOpen={showExportModal}
          onClose={toggleExportModal}
          userRole="admin"
        />
      </main>
    </div>
  );
});

AdminDashboard.displayName = 'AdminDashboard';

export default AdminDashboard;
