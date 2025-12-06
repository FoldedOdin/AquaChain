import React, { useState, useEffect, useCallback, memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeftIcon,
  Cog6ToothIcon,
  PowerIcon,
  ShieldCheckIcon,
  XMarkIcon,
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
  Package,
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
import AdminInventoryManagement from './AdminInventoryManagement';

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
  
  // Quick Actions modals
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [showSystemSettingsModal, setShowSystemSettingsModal] = useState(false);
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  const [showInventoryManagement, setShowInventoryManagement] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [backupStatus, setBackupStatus] = useState<string>('');
  
  // System settings state
  const [settingsData, setSettingsData] = useState<any>({
    alertThresholds: { phMin: 6.5, phMax: 8.5, turbidityMax: 5.0, tdsMax: 500 },
    notificationSettings: { emailEnabled: true, smsEnabled: true, pushEnabled: true },
    systemLimits: { maxDevicesPerUser: 10, dataRetentionDays: 90 }
  });
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  
  // Alerts state
  const [systemAlerts, setSystemAlerts] = useState<any[]>([]);
  const [alertStats, setAlertStats] = useState({ critical: 0, warning: 0, info: 0, total: 0 });
  
  // User management modals
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showViewUserModal, setShowViewUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showDeleteUserModal, setShowDeleteUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  
  // Edit user form state
  const [editFormData, setEditFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    role: 'consumer',
    status: 'active'
  });
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  
  // Add user form state
  const [addFormData, setAddFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    role: 'consumer',
    status: 'active'
  });
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);
  
  // Device management modals
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [showViewDeviceModal, setShowViewDeviceModal] = useState(false);
  const [showEditDeviceModal, setShowEditDeviceModal] = useState(false);
  const [showDeleteDeviceModal, setShowDeleteDeviceModal] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<any>(null);
  
  // Edit device form state
  const [editDeviceFormData, setEditDeviceFormData] = useState({
    deviceId: '',
    status: 'online',
    location: '',
    consumerId: '',
    consumerName: ''
  });
  const [isSubmittingEditDevice, setIsSubmittingEditDevice] = useState(false);
  
  // Add device form state
  const [addDeviceFormData, setAddDeviceFormData] = useState({
    deviceId: '',
    location: '',
    consumerId: '',
    consumerName: '',
    status: 'online'
  });
  const [isSubmittingAddDevice, setIsSubmittingAddDevice] = useState(false);

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useDashboardData('admin');
  const { isConnected } = useRealTimeUpdates('admin-updates', { autoConnect: true });
  const { notifications } = useNotifications();

  // State for dynamic data
  const [users, setUsers] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [deviceFleet, setDeviceFleet] = useState<any[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState<any>(null);

  // Get consumer users for dropdown
  const consumerUsers = useMemo(() => {
    return users.filter(u => u.role === 'consumer');
  }, [users]);

  // Fetch users, devices, and metrics
  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingData(true);
      try {
        const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
        
        const [usersData, devicesData, fleetData, metricsResponse] = await Promise.all([
          getAllUsers(),
          getAllDevices(),
          getDeviceFleetStatus(),
          fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/metrics`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })
        ]);
        
        setUsers(usersData);
        setDevices(devicesData);
        setDeviceFleet(fleetData);
        
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setSystemMetrics(metricsData.metrics);
        }
      } catch (err) {
        console.error('Failed to fetch admin data:', err);
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchData();
    
    // Refresh metrics every 30 seconds
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/metrics`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (response.ok) {
          const metricsData = await response.json();
          setSystemMetrics(metricsData.metrics);
        }
      } catch (err) {
        console.error('Failed to refresh metrics:', err);
      }
    }, 30000);
    
    return () => clearInterval(interval);
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

  // System overview chart data
  const systemOverviewData = useMemo(() => {
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

  // Recent activities from system events
  const recentActivities = useMemo(() => {
    const activities: any[] = [];
    
    // Add activities from notifications if available
    if (notifications && notifications.length > 0) {
      notifications.slice(0, 2).forEach(notif => {
        let icon = Database;
        if (notif.type === 'error' || notif.type === 'warning') {
          icon = AlertTriangle;
        } else if (notif.type === 'success') {
          icon = UserPlus;
        }
        
        activities.push({
          id: notif.id,
          type: notif.type,
          message: notif.message,
          time: formatRelativeTime(notif.timestamp),
          icon,
          color: notif.priority === 'high' ? 'text-red-600' : notif.priority === 'medium' ? 'text-amber-600' : 'text-blue-600'
        });
      });
    }
    
    // Add recent user activities
    const recentUsers = users
      .filter(u => u.lastLogin)
      .sort((a, b) => new Date(b.lastLogin).getTime() - new Date(a.lastLogin).getTime())
      .slice(0, 2);
    
    recentUsers.forEach(user => {
      activities.push({
        id: `user-${user.userId}`,
        type: 'user',
        message: `${user.profile?.firstName || 'User'} ${user.profile?.lastName || ''} logged in`,
        time: formatRelativeTime(user.lastLogin),
        icon: Users,
        color: 'text-green-600'
      });
    });
    
    // Add recent device activities
    const recentDevices = deviceFleet
      .filter(d => d.lastSeen)
      .sort((a, b) => new Date(b.lastSeen).getTime() - new Date(a.lastSeen).getTime())
      .slice(0, 2);
    
    recentDevices.forEach(device => {
      const statusColor = device.status === 'online' ? 'text-green-600' : 
                         device.status === 'warning' ? 'text-amber-600' : 'text-red-600';
      activities.push({
        id: `device-${device.deviceId}`,
        type: 'device',
        message: `Device ${device.deviceId} is ${device.status}`,
        time: formatRelativeTime(device.lastSeen),
        icon: Server,
        color: statusColor
      });
    });
    
    // Sort all activities by time (most recent first) and take top 5
    return activities
      .sort((a, b) => {
        // Simple time comparison based on the time string
        const timeA = a.time.includes('ago') ? 1 : 0;
        const timeB = b.time.includes('ago') ? 1 : 0;
        return timeB - timeA;
      })
      .slice(0, 5);
  }, [notifications, users, deviceFleet]);

  // Filtered devices
  const filteredDevices = useMemo(() => {
    if (deviceFilter === 'all') return deviceFleet;
    return deviceFleet.filter(device => device.status === deviceFilter);
  }, [deviceFilter, deviceFleet]);

  // Performance metrics from real server data
  const performanceMetrics = useMemo(() => {
    if (!systemMetrics) {
      return { uptime: 0, accuracy: 0, satisfaction: 0, uptimeDisplay: 'N/A' };
    }
    return {
      uptime: systemMetrics.systemUptime || 100,
      accuracy: parseFloat(systemMetrics.apiUptime) || 0,
      satisfaction: 0, // No user feedback system yet
      uptimeDisplay: systemMetrics.uptimeDays 
        ? `${systemMetrics.uptimeDays} days` 
        : systemMetrics.uptimeHours 
        ? `${systemMetrics.uptimeHours} hours`
        : 'N/A'
    };
  }, [systemMetrics]);

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

  // Quick Actions handlers
  const handleBackup = useCallback(async () => {
    setIsBackingUp(true);
    setBackupStatus('Preparing backup...');
    
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      
      // Backup users
      setBackupStatus('Backing up users...');
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Backup devices
      setBackupStatus('Backing up devices...');
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Backup system settings
      setBackupStatus('Backing up system settings...');
      let systemSettings = null;
      try {
        const settingsResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/settings`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (settingsResponse.ok) {
          const settingsData = await settingsResponse.json();
          systemSettings = settingsData.settings;
        }
      } catch (err) {
        console.error('Failed to backup settings:', err);
      }
      
      // Backup alerts
      setBackupStatus('Backing up alerts...');
      let systemAlerts = [];
      try {
        const alertsResponse = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/alerts`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json();
          systemAlerts = alertsData.alerts;
        }
      } catch (err) {
        console.error('Failed to backup alerts:', err);
      }
      
      setBackupStatus('Finalizing backup...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Create comprehensive backup data
      const backupData = {
        metadata: {
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          backupType: 'full',
          generatedBy: user?.email || 'admin'
        },
        statistics: {
          totalUsers: users.length,
          totalDevices: deviceFleet.length,
          totalAlerts: systemAlerts.length,
          usersByRole: {
            admin: users.filter(u => u.role === 'admin').length,
            technician: users.filter(u => u.role === 'technician').length,
            consumer: users.filter(u => u.role === 'consumer').length
          },
          devicesByStatus: {
            online: deviceFleet.filter(d => d.status === 'online').length,
            warning: deviceFleet.filter(d => d.status === 'warning').length,
            offline: deviceFleet.filter(d => d.status === 'offline').length
          }
        },
        data: {
          users: users.map(u => ({
            userId: u.userId,
            email: u.email,
            role: u.role,
            status: u.status,
            profile: u.profile,
            createdAt: u.createdAt,
            lastLogin: u.lastLogin,
            deviceCount: u.deviceCount
          })),
          devices: deviceFleet.map(d => ({
            deviceId: d.deviceId,
            status: d.status,
            location: d.location,
            consumerName: d.consumerName,
            consumerId: d.consumerId,
            currentWQI: d.currentWQI,
            batteryLevel: d.batteryLevel,
            lastSeen: d.lastSeen
          })),
          systemSettings: systemSettings,
          alerts: systemAlerts
        }
      };
      
      // Download backup file
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `aquachain-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setBackupStatus('Backup completed successfully!');
      setTimeout(() => {
        setShowBackupModal(false);
        setBackupStatus('');
      }, 2000);
    } catch (error) {
      console.error('Backup failed:', error);
      setBackupStatus('Backup failed. Please try again.');
    } finally {
      setIsBackingUp(false);
    }
  }, [users, deviceFleet, user]);

  const handleOpenSystemSettings = useCallback(async () => {
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettingsData(data.settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
    setShowSystemSettingsModal(true);
  }, []);

  const handleSaveSettings = useCallback(async () => {
    setIsSavingSettings(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settingsData)
      });
      
      if (response.ok) {
        alert('Settings saved successfully!');
        setShowSystemSettingsModal(false);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Error saving settings');
    } finally {
      setIsSavingSettings(false);
    }
  }, [settingsData]);

  const handleOpenAlerts = useCallback(async () => {
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/alerts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemAlerts(data.alerts);
        setAlertStats(data.statistics);
      }
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
    setShowAlertsModal(true);
  }, []);

  const handleMarkAllAlertsRead = useCallback(async () => {
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/alerts/read-all`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        // Update local state
        setSystemAlerts(prev => prev.map(a => ({ ...a, read: true })));
        alert('All alerts marked as read');
      }
    } catch (error) {
      console.error('Error marking alerts as read:', error);
    }
  }, []);

  const handleDeleteAlert = useCallback(async (alertId: string) => {
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        // Remove from local state
        setSystemAlerts(prev => prev.filter(a => a.id !== alertId));
        setAlertStats(prev => ({
          ...prev,
          total: prev.total - 1
        }));
      }
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  }, []);

  // User management handlers
  const handleViewUser = useCallback((user: any) => {
    setSelectedUser(user);
    setShowViewUserModal(true);
  }, []);

  const handleEditUser = useCallback((user: any) => {
    setSelectedUser(user);
    setEditFormData({
      firstName: user.profile?.firstName || '',
      lastName: user.profile?.lastName || '',
      email: user.email || '',
      phone: user.profile?.phone || '',
      role: user.role || 'consumer',
      status: user.status || 'active'
    });
    setShowEditUserModal(true);
  }, []);

  const handleEditFormChange = useCallback((field: string, value: string) => {
    setEditFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSaveEditUser = useCallback(async () => {
    if (!selectedUser) return;
    
    setIsSubmittingEdit(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/users/${selectedUser.userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editFormData)
      });

      if (response.ok) {
        const result = await response.json();
        // Update local state
        setUsers(prev => prev.map(u => 
          u.userId === selectedUser.userId 
            ? { 
                ...u, 
                email: editFormData.email,
                role: editFormData.role,
                status: editFormData.status,
                profile: {
                  ...u.profile,
                  firstName: editFormData.firstName,
                  lastName: editFormData.lastName,
                  phone: editFormData.phone
                }
              }
            : u
        ));
        setShowEditUserModal(false);
        setSelectedUser(null);
        console.log('User updated successfully');
      } else {
        const error = await response.json();
        console.error('Failed to update user:', error.error);
        alert(error.error || 'Failed to update user');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      alert('Error updating user');
    } finally {
      setIsSubmittingEdit(false);
    }
  }, [selectedUser, editFormData]);

  const handleDeleteUser = useCallback((user: any) => {
    setSelectedUser(user);
    setShowDeleteUserModal(true);
  }, []);

  const handleAddUser = useCallback(() => {
    // Reset form
    setAddFormData({
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      password: '',
      role: 'consumer',
      status: 'active'
    });
    setShowAddUserModal(true);
  }, []);

  const handleAddFormChange = useCallback((field: string, value: string) => {
    setAddFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSaveNewUser = useCallback(async () => {
    setIsSubmittingAdd(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(addFormData)
      });

      if (response.ok) {
        const result = await response.json();
        // Add to local state
        const newUser = {
          userId: result.user.userId,
          email: result.user.email,
          role: result.user.role,
          status: result.user.status,
          createdAt: result.user.createdAt,
          lastLogin: null,
          deviceCount: 0,
          profile: {
            firstName: result.user.firstName,
            lastName: result.user.lastName,
            phone: result.user.phone
          }
        };
        setUsers(prev => [...prev, newUser]);
        setShowAddUserModal(false);
        console.log('User created successfully');
      } else {
        const error = await response.json();
        console.error('Failed to create user:', error.error);
        alert(error.error || 'Failed to create user');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Error creating user');
    } finally {
      setIsSubmittingAdd(false);
    }
  }, [addFormData]);

  // Device management handlers
  const handleViewDevice = useCallback((device: any) => {
    setSelectedDevice(device);
    setShowViewDeviceModal(true);
  }, []);

  const handleEditDevice = useCallback((device: any) => {
    setSelectedDevice(device);
    setEditDeviceFormData({
      deviceId: device.deviceId || '',
      status: device.status || 'online',
      location: device.location?.address || '',
      consumerId: device.consumerId || '',
      consumerName: device.consumerName || ''
    });
    setShowEditDeviceModal(true);
  }, []);

  const handleEditDeviceFormChange = useCallback((field: string, value: string) => {
    setEditDeviceFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSaveEditDevice = useCallback(async () => {
    if (!selectedDevice) return;
    
    setIsSubmittingEditDevice(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/devices/${selectedDevice.deviceId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editDeviceFormData)
      });

      if (response.ok) {
        const result = await response.json();
        // Update local state
        setDeviceFleet(prev => prev.map(d => 
          d.deviceId === selectedDevice.deviceId 
            ? { 
                ...d, 
                status: editDeviceFormData.status,
                consumerName: editDeviceFormData.consumerName,
                location: {
                  ...d.location,
                  address: editDeviceFormData.location
                }
              }
            : d
        ));
        setShowEditDeviceModal(false);
        setSelectedDevice(null);
        console.log('Device updated successfully');
      } else {
        const error = await response.json();
        console.error('Failed to update device:', error.error);
        alert(error.error || 'Failed to update device');
      }
    } catch (error) {
      console.error('Error updating device:', error);
      alert('Error updating device');
    } finally {
      setIsSubmittingEditDevice(false);
    }
  }, [selectedDevice, editDeviceFormData]);

  const handleDeleteDevice = useCallback((device: any) => {
    setSelectedDevice(device);
    setShowDeleteDeviceModal(true);
  }, []);

  const handleAddDevice = useCallback(() => {
    // Reset form
    setAddDeviceFormData({
      deviceId: '',
      location: '',
      consumerId: '',
      consumerName: '',
      status: 'online'
    });
    setShowAddDeviceModal(true);
  }, []);

  const handleConsumerChange = useCallback((consumerId: string) => {
    const consumer = users.find(u => u.userId === consumerId);
    setAddDeviceFormData(prev => ({
      ...prev,
      consumerId,
      consumerName: consumer ? `${consumer.profile?.firstName} ${consumer.profile?.lastName}` : ''
    }));
  }, [users]);

  const handleAddDeviceFormChange = useCallback((field: string, value: string) => {
    setAddDeviceFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSaveNewDevice = useCallback(async () => {
    setIsSubmittingAddDevice(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/devices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(addDeviceFormData)
      });

      if (response.ok) {
        const result = await response.json();
        // Add to local state
        const newDevice = {
          deviceId: result.device.deviceId,
          status: result.device.status,
          location: {
            address: result.device.location
          },
          consumerName: result.device.consumerName,
          currentWQI: 0,
          batteryLevel: 100,
          lastSeen: new Date().toISOString()
        };
        setDeviceFleet(prev => [...prev, newDevice]);
        setShowAddDeviceModal(false);
        console.log('Device created successfully');
      } else {
        const error = await response.json();
        console.error('Failed to create device:', error.error);
        alert(error.error || 'Failed to create device');
      }
    } catch (error) {
      console.error('Error creating device:', error);
      alert('Error creating device');
    } finally {
      setIsSubmittingAddDevice(false);
    }
  }, [addDeviceFormData]);

  const confirmDeleteDevice = useCallback(async () => {
    if (!selectedDevice) return;
    
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/devices/${selectedDevice.deviceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setDeviceFleet(prev => prev.filter(d => d.deviceId !== selectedDevice.deviceId));
        setShowDeleteDeviceModal(false);
        setSelectedDevice(null);
        console.log('Device deleted successfully');
      } else {
        const error = await response.json();
        console.error('Failed to delete device:', error);
        alert(error.error || 'Failed to delete device');
      }
    } catch (error) {
      console.error('Error deleting device:', error);
      alert('Error deleting device');
    }
  }, [selectedDevice]);

  const confirmDeleteUser = useCallback(async () => {
    if (!selectedUser) return;
    
    try {
      // Call delete API
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/users/${selectedUser.userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Remove from local state
        setUsers(prev => prev.filter(u => u.userId !== selectedUser.userId));
        setShowDeleteUserModal(false);
        setSelectedUser(null);
        console.log('User deleted successfully');
      } else {
        console.error('Failed to delete user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  }, [selectedUser]);

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
                {systemOverviewData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={systemOverviewData}>
                      <defs>
                        <linearGradient id="colorDevices" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="date" 
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                          padding: '8px 12px'
                        }}
                      />
                      <Legend 
                        wrapperStyle={{ paddingTop: '10px' }}
                        iconType="circle"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="devices" 
                        stroke="#8b5cf6" 
                        strokeWidth={3}
                        name="Devices"
                        dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6, strokeWidth: 2 }}
                        isAnimationActive={false}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="users" 
                        stroke="#10b981" 
                        strokeWidth={3}
                        name="Users"
                        dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6, strokeWidth: 2 }}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <Activity className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                      <p>No data available</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Device Status Distribution */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Device Status Distribution</h3>
                {deviceStatusData.length > 0 ? (
                  <div className="space-y-4">
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <defs>
                          <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15"/>
                          </filter>
                        </defs>
                        <Pie
                          data={deviceStatusData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={90}
                          innerRadius={50}
                          fill="#8884d8"
                          dataKey="value"
                          paddingAngle={2}
                          isAnimationActive={false}
                          style={{ filter: 'url(#shadow)' }}
                        >
                          {deviceStatusData.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={entry.color}
                              stroke="#fff"
                              strokeWidth={2}
                            />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                            padding: '8px 12px'
                          }}
                          formatter={(value: any, name: string) => [`${value} devices`, name]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    
                    {/* Legend */}
                    <div className="flex justify-center gap-6">
                      {deviceStatusData.map((entry, index) => (
                        <div key={`legend-${index}`} className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: entry.color }}
                          />
                          <span className="text-sm text-gray-700">
                            {entry.name}: <span className="font-semibold">{entry.value}</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <Database className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                      <p>No devices registered</p>
                    </div>
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
                  <button 
                    onClick={() => setShowBackupModal(true)}
                    className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
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
                  <button 
                    onClick={handleOpenSystemSettings}
                    className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
                    <Settings className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Settings</span>
                  </button>
                  <button 
                    onClick={handleOpenAlerts}
                    className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
                    <Bell className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Alerts</span>
                  </button>
                  <button 
                    onClick={() => setShowInventoryManagement(true)}
                    className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                  >
                    <Package className="w-6 h-6 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Inventory</span>
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
                  <button 
                    onClick={handleAddDevice}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
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
                              <button 
                                onClick={() => handleViewDevice(device)}
                                className="p-1 text-blue-600 hover:bg-blue-50 rounded" 
                                title="View"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button 
                                onClick={() => handleEditDevice(device)}
                                className="p-1 text-gray-600 hover:bg-gray-50 rounded" 
                                title="Edit"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteDevice(device)}
                                className="p-1 text-red-600 hover:bg-red-50 rounded" 
                                title="Delete"
                              >
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
                <button 
                  onClick={handleAddUser}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
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
                              <button 
                                onClick={() => handleViewUser(user)}
                                className="p-1 text-blue-600 hover:bg-blue-50 rounded" 
                                title="View"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button 
                                onClick={() => handleEditUser(user)}
                                className="p-1 text-gray-600 hover:bg-gray-50 rounded" 
                                title="Edit"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteUser(user)}
                                className="p-1 text-red-600 hover:bg-red-50 rounded" 
                                title="Delete"
                              >
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
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8b5cf6" stopOpacity={1}/>
                          <stop offset="100%" stopColor="#a78bfa" stopOpacity={0.8}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="role" 
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        style={{ fontSize: '12px' }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                          padding: '8px 12px'
                        }}
                        cursor={{ fill: 'rgba(139, 92, 246, 0.1)' }}
                      />
                      <Bar 
                        dataKey="count" 
                        fill="url(#barGradient)"
                        radius={[8, 8, 0, 0]}
                        isAnimationActive={false}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <Users className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                      <p>No user data available</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Alert Trends */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert Trends (7 Days)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={alertTrends}>
                    <defs>
                      <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#9ca3af"
                      style={{ fontSize: '12px' }}
                    />
                    <YAxis 
                      stroke="#9ca3af"
                      style={{ fontSize: '12px' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        padding: '8px 12px'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="alerts" 
                      stroke="#ef4444" 
                      strokeWidth={3}
                      fill="url(#colorAlerts)"
                      dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, strokeWidth: 2 }}
                      isAnimationActive={false}
                    />
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
                    {systemMetrics ? `${performanceMetrics.uptime.toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-sm font-medium text-gray-700">System Uptime</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {systemMetrics ? `Running for ${performanceMetrics.uptimeDisplay}` : 'Server metrics unavailable'}
                  </div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {systemMetrics ? `${performanceMetrics.accuracy.toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-sm font-medium text-gray-700">API Success Rate</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {systemMetrics ? `${systemMetrics.successfulApiCalls}/${systemMetrics.totalApiCalls} calls` : 'No API data'}
                  </div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600 mb-2">
                    N/A
                  </div>
                  <div className="text-sm font-medium text-gray-700">User Satisfaction</div>
                  <div className="text-xs text-gray-600 mt-1">No feedback system yet</div>
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

        {/* Admin Inventory Management Modal */}
        <AdminInventoryManagement
          isOpen={showInventoryManagement}
          onClose={() => setShowInventoryManagement(false)}
        />

        {/* View User Modal */}
        <AnimatePresence>
          {showViewUserModal && selectedUser && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowViewUserModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">User Details</h3>
                    <button onClick={() => setShowViewUserModal(false)} className="text-gray-400 hover:text-gray-600">
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                      <p className="text-gray-900">{selectedUser.profile?.firstName} {selectedUser.profile?.lastName}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <p className="text-gray-900">{selectedUser.email}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(selectedUser.role)}`}>
                        {selectedUser.role}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedUser.status)}`}>
                        {selectedUser.status}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <p className="text-gray-900">{selectedUser.profile?.phone || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Devices</label>
                      <p className="text-gray-900">{selectedUser.deviceCount || 0}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Created At</label>
                      <p className="text-gray-900">{new Date(selectedUser.createdAt).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Login</label>
                      <p className="text-gray-900">{selectedUser.lastLogin ? formatRelativeTime(selectedUser.lastLogin) : 'Never'}</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={() => setShowViewUserModal(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Edit User Modal */}
        <AnimatePresence>
          {showEditUserModal && selectedUser && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isSubmittingEdit && setShowEditUserModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Edit User</h3>
                    <button 
                      onClick={() => !isSubmittingEdit && setShowEditUserModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isSubmittingEdit}
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <form onSubmit={(e) => { e.preventDefault(); handleSaveEditUser(); }} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          First Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={editFormData.firstName}
                          onChange={(e) => handleEditFormChange('firstName', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingEdit}
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Last Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={editFormData.lastName}
                          onChange={(e) => handleEditFormChange('lastName', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingEdit}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        value={editFormData.email}
                        onChange={(e) => handleEditFormChange('email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Phone
                      </label>
                      <input
                        type="tel"
                        value={editFormData.phone}
                        onChange={(e) => handleEditFormChange('phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Role <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={editFormData.role}
                          onChange={(e) => handleEditFormChange('role', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingEdit}
                        >
                          <option value="consumer">Consumer</option>
                          <option value="technician">Technician</option>
                          <option value="admin">Admin</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Status <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={editFormData.status}
                          onChange={(e) => handleEditFormChange('status', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingEdit}
                        >
                          <option value="active">Active</option>
                          <option value="pending">Pending</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="mt-6 flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setShowEditUserModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isSubmittingEdit}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmittingEdit}
                      >
                        {isSubmittingEdit ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </form>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Delete User Modal */}
        <AnimatePresence>
          {showDeleteUserModal && selectedUser && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowDeleteUserModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Delete User</h3>
                    <button onClick={() => setShowDeleteUserModal(false)} className="text-gray-400 hover:text-gray-600">
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="mb-6">
                    <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                      <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-red-900">This action cannot be undone</p>
                        <p className="text-sm text-red-700 mt-1">All user data and devices will be permanently deleted.</p>
                      </div>
                    </div>
                    <p className="text-gray-700">
                      Are you sure you want to delete <strong>{selectedUser.profile?.firstName} {selectedUser.profile?.lastName}</strong> ({selectedUser.email})?
                    </p>
                  </div>
                  
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setShowDeleteUserModal(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={confirmDeleteUser}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Delete User
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Device Modals */}
        {/* View Device Modal */}
        <AnimatePresence>
          {showViewDeviceModal && selectedDevice && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowViewDeviceModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Device Details</h3>
                    <button onClick={() => setShowViewDeviceModal(false)} className="text-gray-400 hover:text-gray-600">
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Device ID</label>
                      <p className="text-gray-900">{selectedDevice.deviceId}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedDevice.status)}`}>
                        {selectedDevice.status}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
                      <p className="text-gray-900">{selectedDevice.consumerName || 'Unassigned'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">WQI</label>
                      <p className="text-gray-900">{selectedDevice.currentWQI || 0}</p>
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                      <p className="text-gray-900">{selectedDevice.location?.address || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Battery Level</label>
                      <p className="text-gray-900">{selectedDevice.batteryLevel || 0}%</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Seen</label>
                      <p className="text-gray-900">{formatRelativeTime(selectedDevice.lastSeen)}</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={() => setShowViewDeviceModal(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Edit Device Modal */}
        <AnimatePresence>
          {showEditDeviceModal && selectedDevice && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isSubmittingEditDevice && setShowEditDeviceModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Edit Device</h3>
                    <button 
                      onClick={() => !isSubmittingEditDevice && setShowEditDeviceModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isSubmittingEditDevice}
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <form onSubmit={(e) => { e.preventDefault(); handleSaveEditDevice(); }} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Device ID
                      </label>
                      <input
                        type="text"
                        value={editDeviceFormData.deviceId}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                        disabled
                        readOnly
                      />
                      <p className="text-xs text-gray-500 mt-1">Device ID cannot be changed</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Status <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={editDeviceFormData.status}
                        onChange={(e) => handleEditDeviceFormChange('status', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingEditDevice}
                      >
                        <option value="online">Online</option>
                        <option value="offline">Offline</option>
                        <option value="warning">Warning</option>
                        <option value="maintenance">Maintenance</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Location
                      </label>
                      <input
                        type="text"
                        value={editDeviceFormData.location}
                        onChange={(e) => handleEditDeviceFormChange('location', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEditDevice}
                        placeholder="123 Main St, City, State"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Assign to Consumer
                      </label>
                      <select
                        value={editDeviceFormData.consumerId || ''}
                        onChange={(e) => {
                          const consumerId = e.target.value;
                          const consumer = users.find(u => u.userId === consumerId);
                          handleEditDeviceFormChange('consumerId', consumerId);
                          handleEditDeviceFormChange('consumerName', consumer ? `${consumer.profile?.firstName} ${consumer.profile?.lastName}` : '');
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEditDevice}
                      >
                        <option value="">Unassigned</option>
                        {consumerUsers.map((consumer) => (
                          <option key={consumer.userId} value={consumer.userId}>
                            {consumer.profile?.firstName} {consumer.profile?.lastName} ({consumer.email})
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        {consumerUsers.length === 0 
                          ? 'No consumer users available' 
                          : `${consumerUsers.length} consumer(s) available`}
                      </p>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                      <p className="text-sm text-blue-800">
                        <strong>Note:</strong> Changes to device status and location will be reflected immediately. 
                        Device readings and historical data will not be affected.
                      </p>
                    </div>
                    
                    <div className="mt-6 flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setShowEditDeviceModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isSubmittingEditDevice}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmittingEditDevice}
                      >
                        {isSubmittingEditDevice ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </form>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Delete Device Modal */}
        <AnimatePresence>
          {showDeleteDeviceModal && selectedDevice && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowDeleteDeviceModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Delete Device</h3>
                    <button onClick={() => setShowDeleteDeviceModal(false)} className="text-gray-400 hover:text-gray-600">
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="mb-6">
                    <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                      <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-red-900">This action cannot be undone</p>
                        <p className="text-sm text-red-700 mt-1">All device data and readings will be permanently deleted.</p>
                      </div>
                    </div>
                    <p className="text-gray-700">
                      Are you sure you want to delete device <strong>{selectedDevice.deviceId}</strong>?
                    </p>
                  </div>
                  
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setShowDeleteDeviceModal(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={confirmDeleteDevice}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Delete Device
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Add Device Modal */}
        <AnimatePresence>
          {showAddDeviceModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isSubmittingAddDevice && setShowAddDeviceModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Add New Device</h3>
                    <button 
                      onClick={() => !isSubmittingAddDevice && setShowAddDeviceModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isSubmittingAddDevice}
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <form onSubmit={(e) => { e.preventDefault(); handleSaveNewDevice(); }} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Device ID <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={addDeviceFormData.deviceId}
                        onChange={(e) => handleAddDeviceFormChange('deviceId', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingAddDevice}
                        placeholder="DEV-1234"
                      />
                      <p className="text-xs text-gray-500 mt-1">Unique identifier for the device (e.g., DEV-1234)</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Location
                      </label>
                      <input
                        type="text"
                        value={addDeviceFormData.location}
                        onChange={(e) => handleAddDeviceFormChange('location', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAddDevice}
                        placeholder="123 Main St, City, State"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Assign to Consumer
                      </label>
                      <select
                        value={addDeviceFormData.consumerId}
                        onChange={(e) => handleConsumerChange(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAddDevice}
                      >
                        <option value="">Unassigned</option>
                        {consumerUsers.map((consumer) => (
                          <option key={consumer.userId} value={consumer.userId}>
                            {consumer.profile?.firstName} {consumer.profile?.lastName} ({consumer.email})
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        {consumerUsers.length === 0 
                          ? 'No consumer users available' 
                          : `${consumerUsers.length} consumer(s) available`}
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Initial Status <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={addDeviceFormData.status}
                        onChange={(e) => handleAddDeviceFormChange('status', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingAddDevice}
                      >
                        <option value="online">Online</option>
                        <option value="offline">Offline</option>
                        <option value="maintenance">Maintenance</option>
                      </select>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                      <p className="text-sm text-blue-800">
                        <strong>Note:</strong> The device will be registered in the system and can start sending data immediately. 
                        Make sure the Device ID matches the physical device configuration.
                      </p>
                    </div>
                    
                    <div className="mt-6 flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setShowAddDeviceModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isSubmittingAddDevice}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmittingAddDevice}
                      >
                        {isSubmittingAddDevice ? 'Adding...' : 'Add Device'}
                      </button>
                    </div>
                  </form>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Backup Modal */}
        <AnimatePresence>
          {showBackupModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isBackingUp && setShowBackupModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">System Backup</h3>
                    <button 
                      onClick={() => !isBackingUp && setShowBackupModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isBackingUp}
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <Database className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-blue-900 mb-1">Backup Information</h4>
                          <p className="text-sm text-blue-800">
                            This will create a backup of all system data including users, devices, and configurations.
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                      <h4 className="font-semibold text-gray-900 text-sm mb-2">Backup Contents:</h4>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-purple-600" />
                            <span className="text-gray-600">Users</span>
                          </div>
                          <span className="font-medium text-gray-900">{users.length} records</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <Server className="w-4 h-4 text-blue-600" />
                            <span className="text-gray-600">Devices</span>
                          </div>
                          <span className="font-medium text-gray-900">{deviceFleet.length} records</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <Settings className="w-4 h-4 text-green-600" />
                            <span className="text-gray-600">System Settings</span>
                          </div>
                          <span className="font-medium text-gray-900">✓ Included</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <Bell className="w-4 h-4 text-amber-600" />
                            <span className="text-gray-600">Alerts</span>
                          </div>
                          <span className="font-medium text-gray-900">✓ Included</span>
                        </div>
                      </div>
                      
                      <div className="pt-2 mt-2 border-t border-gray-200">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Backup Date:</span>
                          <span className="font-medium text-gray-900">{new Date().toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    {backupStatus && (
                      <div className={`p-3 rounded-lg ${
                        backupStatus.includes('success') 
                          ? 'bg-green-50 text-green-800' 
                          : backupStatus.includes('failed')
                          ? 'bg-red-50 text-red-800'
                          : 'bg-blue-50 text-blue-800'
                      }`}>
                        <p className="text-sm font-medium">{backupStatus}</p>
                      </div>
                    )}
                    
                    <div className="flex justify-end gap-3 mt-6">
                      <button
                        onClick={() => setShowBackupModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isBackingUp}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleBackup}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        disabled={isBackingUp}
                      >
                        {isBackingUp ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Backing up...</span>
                          </>
                        ) : (
                          <>
                            <Database className="w-4 h-4" />
                            <span>Start Backup</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* System Settings Modal */}
        <AnimatePresence>
          {showSystemSettingsModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowSystemSettingsModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">System Settings</h3>
                    <button 
                      onClick={() => setShowSystemSettingsModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="space-y-6">
                    {/* Alert Thresholds */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">Alert Thresholds</h4>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">pH Min</label>
                            <input
                              type="number"
                              value={settingsData.alertThresholds.phMin}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                alertThresholds: { ...settingsData.alertThresholds, phMin: parseFloat(e.target.value) }
                              })}
                              step="0.1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">pH Max</label>
                            <input
                              type="number"
                              value={settingsData.alertThresholds.phMax}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                alertThresholds: { ...settingsData.alertThresholds, phMax: parseFloat(e.target.value) }
                              })}
                              step="0.1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Turbidity Max (NTU)</label>
                            <input
                              type="number"
                              value={settingsData.alertThresholds.turbidityMax}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                alertThresholds: { ...settingsData.alertThresholds, turbidityMax: parseFloat(e.target.value) }
                              })}
                              step="0.1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">TDS Max (ppm)</label>
                            <input
                              type="number"
                              value={settingsData.alertThresholds.tdsMax}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                alertThresholds: { ...settingsData.alertThresholds, tdsMax: parseInt(e.target.value) }
                              })}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Notification Settings */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">Notification Settings</h4>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">Email Notifications</p>
                            <p className="text-sm text-gray-600">Receive alerts via email</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={settingsData.notificationSettings.emailEnabled}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                notificationSettings: { ...settingsData.notificationSettings, emailEnabled: e.target.checked }
                              })}
                              className="sr-only peer" 
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">SMS Notifications</p>
                            <p className="text-sm text-gray-600">Receive critical alerts via SMS</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={settingsData.notificationSettings.smsEnabled}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                notificationSettings: { ...settingsData.notificationSettings, smsEnabled: e.target.checked }
                              })}
                              className="sr-only peer" 
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">Push Notifications</p>
                            <p className="text-sm text-gray-600">Receive alerts in browser</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={settingsData.notificationSettings.pushEnabled}
                              onChange={(e) => setSettingsData({
                                ...settingsData,
                                notificationSettings: { ...settingsData.notificationSettings, pushEnabled: e.target.checked }
                              })}
                              className="sr-only peer" 
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                          </label>
                        </div>
                      </div>
                    </div>
                    
                    {/* System Limits */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">System Limits</h4>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Max Devices Per User</label>
                          <input
                            type="number"
                            value={settingsData.systemLimits.maxDevicesPerUser}
                            onChange={(e) => setSettingsData({
                              ...settingsData,
                              systemLimits: { ...settingsData.systemLimits, maxDevicesPerUser: parseInt(e.target.value) }
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Data Retention (days)</label>
                          <input
                            type="number"
                            value={settingsData.systemLimits.dataRetentionDays}
                            onChange={(e) => setSettingsData({
                              ...settingsData,
                              systemLimits: { ...settingsData.systemLimits, dataRetentionDays: parseInt(e.target.value) }
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-end gap-3 pt-4 border-t">
                      <button
                        onClick={() => setShowSystemSettingsModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isSavingSettings}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveSettings}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        disabled={isSavingSettings}
                      >
                        {isSavingSettings ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Saving...</span>
                          </>
                        ) : (
                          <span>Save Settings</span>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Alerts Management Modal */}
        <AnimatePresence>
          {showAlertsModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowAlertsModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Alert Management</h3>
                      <p className="text-sm text-gray-600 mt-1">View and manage system alerts</p>
                    </div>
                    <button 
                      onClick={() => setShowAlertsModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  {/* Alert Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-red-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                        <span className="text-sm font-medium text-red-900">Critical</span>
                      </div>
                      <p className="text-2xl font-bold text-red-600">
                        {alertStats.critical}
                      </p>
                    </div>
                    <div className="bg-amber-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                        <span className="text-sm font-medium text-amber-900">Warning</span>
                      </div>
                      <p className="text-2xl font-bold text-amber-600">
                        {alertStats.warning}
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Bell className="w-5 h-5 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">Info</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-600">
                        {alertStats.info}
                      </p>
                    </div>
                  </div>
                  
                  {/* Alerts List */}
                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900">Recent Alerts</h4>
                    {systemAlerts.length > 0 ? (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {systemAlerts.slice(0, 10).map((alert) => (
                          <div 
                            key={alert.id} 
                            className={`p-4 rounded-lg border ${
                              alert.priority === 'high' 
                                ? 'bg-red-50 border-red-200' 
                                : alert.priority === 'medium'
                                ? 'bg-amber-50 border-amber-200'
                                : 'bg-blue-50 border-blue-200'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                                    alert.priority === 'high'
                                      ? 'bg-red-100 text-red-800'
                                      : alert.priority === 'medium'
                                      ? 'bg-amber-100 text-amber-800'
                                      : 'bg-blue-100 text-blue-800'
                                  }`}>
                                    {alert.priority}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {formatRelativeTime(alert.timestamp)}
                                  </span>
                                  {alert.read && (
                                    <span className="text-xs text-gray-400">(Read)</span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-900">{alert.message}</p>
                              </div>
                              <button 
                                onClick={() => handleDeleteAlert(alert.id)}
                                className="text-gray-400 hover:text-red-600 ml-2"
                                title="Delete alert"
                              >
                                <XMarkIcon className="w-5 h-5" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Bell className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                        <p>No alerts at this time</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                    <button
                      onClick={() => setShowAlertsModal(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Close
                    </button>
                    <button
                      onClick={handleMarkAllAlertsRead}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                      disabled={systemAlerts.length === 0}
                    >
                      Mark All as Read
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Add User Modal */}
        <AnimatePresence>
          {showAddUserModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isSubmittingAdd && setShowAddUserModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-gray-900">Add New User</h3>
                    <button 
                      onClick={() => !isSubmittingAdd && setShowAddUserModal(false)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isSubmittingAdd}
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <form onSubmit={(e) => { e.preventDefault(); handleSaveNewUser(); }} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          First Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={addFormData.firstName}
                          onChange={(e) => handleAddFormChange('firstName', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingAdd}
                          placeholder="John"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Last Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={addFormData.lastName}
                          onChange={(e) => handleAddFormChange('lastName', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingAdd}
                          placeholder="Doe"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        value={addFormData.email}
                        onChange={(e) => handleAddFormChange('email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingAdd}
                        placeholder="john.doe@example.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Password <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="password"
                        value={addFormData.password}
                        onChange={(e) => handleAddFormChange('password', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                        disabled={isSubmittingAdd}
                        placeholder="Minimum 8 characters"
                        minLength={8}
                      />
                      <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Phone
                      </label>
                      <input
                        type="tel"
                        value={addFormData.phone}
                        onChange={(e) => handleAddFormChange('phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                        placeholder="+1 (555) 123-4567"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Role <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={addFormData.role}
                          onChange={(e) => handleAddFormChange('role', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingAdd}
                        >
                          <option value="consumer">Consumer</option>
                          <option value="technician">Technician</option>
                          <option value="admin">Admin</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Status <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={addFormData.status}
                          onChange={(e) => handleAddFormChange('status', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          required
                          disabled={isSubmittingAdd}
                        >
                          <option value="active">Active</option>
                          <option value="pending">Pending</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                      <p className="text-sm text-blue-800">
                        <strong>Note:</strong> The user will be created with email verification already completed. 
                        They can log in immediately with the provided credentials.
                      </p>
                    </div>
                    
                    <div className="mt-6 flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setShowAddUserModal(false)}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                        disabled={isSubmittingAdd}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmittingAdd}
                      >
                        {isSubmittingAdd ? 'Creating...' : 'Create User'}
                      </button>
                    </div>
                  </form>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
});

AdminDashboard.displayName = 'AdminDashboard';

export default AdminDashboard;
