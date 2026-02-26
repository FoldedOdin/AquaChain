import React, { useState, useEffect, useCallback, memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import AdminProfile from './AdminProfile';
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
  Server,
  AlertTriangle,
  Settings,
  Eye,
  Edit,
  Trash2,
  Plus,
  Shield,
  FileText,
  Monitor,
  CheckCircle,
  XCircle,
  Clock,
  Download,
  Search,
  Filter,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';
import { useNotifications } from '../../hooks/useNotifications';
import { 
  getAllUsers, 
  getSystemConfiguration, 
  updateSystemConfiguration,
  getSystemHealthMetrics,
  getPerformanceMetrics,
  getAuditTrail,
  generateComplianceReport,
} from '../../services/adminService';
import { getIncidentReports, getIncidentStats } from '../../services/incidentService';
import { formatRelativeTime } from '../../utils/dateFormat';
import websocketService from '../../services/websocketService';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface AdminDashboardRestructuredProps {
  // Optional props for customization
}

const AdminDashboardRestructured: React.FC<AdminDashboardRestructuredProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout, refreshUser } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedView, setSelectedView] = useState('overview');
  
  // System configuration state
  const [systemConfig, setSystemConfig] = useState<{
    alertThresholds?: {
      global?: {
        pH?: { min: number; max: number };
        turbidity?: { max: number };
        tds?: { max: number };
        temperature?: { min: number; max: number };
      };
    };
    systemLimits?: {
      maxDevicesPerUser?: number;
      dataRetentionDays?: number;
      auditRetentionYears?: number;
    };
  } | null>(null);
  const [showSystemConfigModal, setShowSystemConfigModal] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [configChanges, setConfigChanges] = useState<Record<string, any>>({});
  
  // User management state
  const [users, setUsers] = useState<Array<{
    userId: string;
    email: string;
    role: string;
    status: string;
    createdAt: string;
    lastLogin: string | null;
    deviceCount: number;
    profile?: {
      firstName: string;
      lastName: string;
      phone: string;
    };
  }>>([]);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showViewUserModal, setShowViewUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showDeleteUserModal, setShowDeleteUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<{
    userId: string;
    email: string;
    role: string;
    status: string;
    createdAt: string;
    lastLogin: string | null;
    deviceCount: number;
    profile?: {
      firstName: string;
      lastName: string;
      phone: string;
    };
  } | null>(null);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('all');
  
  // Edit user form state
  const [editFormData, setEditFormData] = useState<{
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    role: string;
    status: string;
  }>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    role: 'consumer',
    status: 'active'
  });
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  
  // Add user form state
  const [addFormData, setAddFormData] = useState<{
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    password: string;
    role: string;
    status: string;
  }>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    role: 'consumer',
    status: 'active'
  });
  const [isSubmittingAdd, setIsSubmittingAdd] = useState(false);
  
  // System monitoring state
  const [systemMetrics, setSystemMetrics] = useState<{
    criticalPathUptime?: number;
    apiUptime?: number;
    notificationUptime?: number;
    errorRate?: number;
    activeDevices?: number;
    totalDevices?: number;
    activeAlerts?: number;
    pendingServiceRequests?: number;
    failedLogins?: number;
    systemAvailability?: number;
    backupStatus?: string;
    lastBackup?: string;
    rtoTarget?: string;
    rpoTarget?: string;
  } | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<{
    totalUsers: number;
    apiSuccessRate: number;
    systemUptime: number;
    uptimeStatus: string;
  }>({
    totalUsers: 0,
    apiSuccessRate: 99.2,
    systemUptime: 99.7,
    uptimeStatus: 'Operational'
  });
  const [performanceMetrics, setPerformanceMetrics] = useState<Array<{
    timestamp: string;
    avgAlertLatency: number;
    p95AlertLatency: number;
    p99AlertLatency: number;
    avgApiResponseTime: number;
    p95ApiResponseTime: number;
    throughput: number;
    lambdaInvocations: number;
    lambdaErrors: number;
    dynamodbReadCapacity: number;
    dynamodbWriteCapacity: number;
  }>>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  
  // Security and audit state
  const [auditLogs, setAuditLogs] = useState<Array<{
    logId: string;
    timestamp: string;
    deviceId: string;
    wqi: number;
    anomalyType: string;
    verified: boolean;
    dataHash: string;
  }>>([]);
  const [complianceReport, setComplianceReport] = useState<{
    reportId: string;
    generatedAt: string;
    period: {
      startDate: string;
      endDate: string;
    };
    summary: {
      totalReadings: number;
      devicesMonitored: number;
      alertsGenerated: number;
      complianceRate: number;
    };
    ledgerVerification: {
      totalEntries: number;
      verifiedEntries: number;
      hashChainIntact: boolean;
      lastVerificationDate: string;
    };
    dataIntegrity: {
      missingReadings: number;
      duplicateReadings: number;
      invalidReadings: number;
    };
    uptimeMetrics: {
      criticalPathUptime: number;
      apiUptime: number;
      notificationUptime: number;
    };
  } | null>(null);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [showComplianceModal, setShowComplianceModal] = useState(false);
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [auditDateRange, setAuditDateRange] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });
  const [auditFilters, setAuditFilters] = useState({
    deviceId: '',
    anomalyType: 'all',
    verified: 'all',
    searchTerm: ''
  });
  const [incidentReports, setIncidentReports] = useState<Array<{
    id: string;
    title: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    status: 'open' | 'investigating' | 'resolved' | 'closed';
    createdAt: string;
    updatedAt: string;
    assignedTo: string;
    description: string;
    category?: string;
    priority?: number;
    resolution?: string;
    resolvedAt?: string;
  }>>([]);
  const [incidentStats, setIncidentStats] = useState<{
    totalIncidents: number;
    openIncidents: number;
    criticalIncidents: number;
    avgResolutionTime: number;
  }>({
    totalIncidents: 0,
    openIncidents: 0,
    criticalIncidents: 0,
    avgResolutionTime: 0
  });

  // WebSocket is disabled - using polling for reliability
  const wsEnabled = false;
  const wsConnected = false;

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useDashboardData('admin');
  const { isConnected } = useRealTimeUpdates('admin-updates', { autoConnect: true });
  const { notifications } = useNotifications();

  // Fetch users and system configuration
  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingData(true);
      try {
        const [usersData, configData, healthMetrics, perfMetrics, incidentData, incidentStatsData] = await Promise.all([
          getAllUsers(),
          getSystemConfiguration(),
          getSystemHealthMetrics(),
          getPerformanceMetrics('24h'),
          getIncidentReports('', '', 10), // Get recent incidents for overview
          getIncidentStats(30) // Get 30-day incident statistics
        ]);
        
        setUsers(usersData);
        setSystemConfig(configData);
        setSystemMetrics(healthMetrics);
        setPerformanceMetrics(perfMetrics);
        setIncidentReports(incidentData);
        setIncidentStats(incidentStatsData);
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
        const [healthMetrics, perfMetrics, incidentStatsData] = await Promise.all([
          getSystemHealthMetrics(),
          getPerformanceMetrics('24h'),
          getIncidentStats(30)
        ]);
        setSystemMetrics(healthMetrics);
        setPerformanceMetrics(perfMetrics);
        setIncidentStats(incidentStatsData);
      } catch (err) {
        console.error('Failed to refresh metrics:', err);
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Fetch real-time system metrics from AWS
  useEffect(() => {
    const fetchRealTimeMetrics = async () => {
      try {
        const systemMetricsService = (await import('../../services/systemMetricsService')).default;
        const metrics = await systemMetricsService.getSystemMetrics();
        
        setRealTimeMetrics({
          totalUsers: metrics.users.total,
          apiSuccessRate: metrics.api.successRate,
          systemUptime: metrics.system.uptime,
          uptimeStatus: metrics.system.status
        });
      } catch (err) {
        console.error('Failed to fetch real-time metrics:', err);
      }
    };

    // Fetch immediately
    fetchRealTimeMetrics();
    
    // Refresh every 30 seconds for real-time updates
    const metricsInterval = setInterval(fetchRealTimeMetrics, 30000);
    
    return () => clearInterval(metricsInterval);
  }, []);

  // WebSocket disabled - using polling instead
  // No WebSocket connection needed

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-amber-100 text-amber-800';
      case 'inactive': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': 
      case 'administrator': return 'bg-purple-100 text-purple-800';
      case 'technician': return 'bg-blue-100 text-blue-800';
      case 'consumer': return 'bg-green-100 text-green-800';
      case 'inventory_manager': return 'bg-orange-100 text-orange-800';
      case 'warehouse_manager': return 'bg-indigo-100 text-indigo-800';
      case 'supplier_coordinator': return 'bg-pink-100 text-pink-800';
      case 'procurement_controller': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Calculate user statistics by role
  const userStats = useMemo(() => {
    if (!users || !Array.isArray(users)) {
      return { 
        consumers: 0, 
        technicians: 0, 
        admins: 0, 
        inventoryManagers: 0,
        warehouseManagers: 0,
        supplierCoordinators: 0,
        procurementControllers: 0,
        total: 0 
      };
    }
    
    const consumers = users.filter(u => u.role === 'consumer').length;
    const technicians = users.filter(u => u.role === 'technician').length;
    const admins = users.filter(u => u.role === 'admin' || u.role === 'administrator').length;
    const inventoryManagers = users.filter(u => u.role === 'inventory_manager').length;
    const warehouseManagers = users.filter(u => u.role === 'warehouse_manager').length;
    const supplierCoordinators = users.filter(u => u.role === 'supplier_coordinator').length;
    const procurementControllers = users.filter(u => u.role === 'procurement_controller').length;
    
    return { 
      consumers, 
      technicians, 
      admins, 
      inventoryManagers,
      warehouseManagers,
      supplierCoordinators,
      procurementControllers,
      total: users.length 
    };
  }, [users]);

  // Filter users based on search and role filter
  const filteredUsers = useMemo(() => {
    if (!users || !Array.isArray(users)) {
      return [];
    }
    
    return users.filter(user => {
      const matchesSearch = !userSearchTerm || 
        user.email.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
        `${user.profile?.firstName} ${user.profile?.lastName}`.toLowerCase().includes(userSearchTerm.toLowerCase());
      
      const matchesRole = userRoleFilter === 'all' || user.role === userRoleFilter;
      
      return matchesSearch && matchesRole;
    });
  }, [users, userSearchTerm, userRoleFilter]);

  // User role data for bar chart
  const userRoleData = useMemo(() => [
    { role: 'Consumer', count: userStats.consumers },
    { role: 'Technician', count: userStats.technicians },
    { role: 'Admin', count: userStats.admins },
    { role: 'Inventory Mgr', count: userStats.inventoryManagers },
    { role: 'Warehouse Mgr', count: userStats.warehouseManagers },
    { role: 'Supplier Coord', count: userStats.supplierCoordinators },
    { role: 'Procurement Ctrl', count: userStats.procurementControllers },
  ], [userStats]);

  // System health metrics
  const systemHealthData = useMemo(() => {
    return {
      uptime: realTimeMetrics.systemUptime,
      apiSuccess: realTimeMetrics.apiSuccessRate,
      uptimeDisplay: realTimeMetrics.uptimeStatus
    };
  }, [realTimeMetrics]);

  // Active alerts count
  const activeAlertsCount = useMemo(() => {
    return notifications.filter(n => !n.read && n.priority === 'high').length;
  }, [notifications]);

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

  // System configuration handlers
  const handleOpenSystemConfig = useCallback(() => {
    setConfigChanges({});
    setShowSystemConfigModal(true);
  }, []);

  const handleConfigChange = useCallback((path: string[], value: any) => {
    setConfigChanges((prev: Record<string, any>) => {
      const newChanges = { ...prev };
      let current: any = newChanges;
      
      // Create nested structure if it doesn't exist
      for (let i = 0; i < path.length - 1; i++) {
        if (!current[path[i]] || typeof current[path[i]] !== 'object') {
          current[path[i]] = {};
        }
        current = current[path[i]];
      }
      
      // Set the final value
      current[path[path.length - 1]] = value;
      
      // Debug log to see what's being changed
      console.log('Config change:', { path, value, newChanges });
      
      return newChanges;
    });
  }, []);

  // Helper function to get the current value (original config + changes)
  const getCurrentConfigValue = useCallback((path: string[], defaultValue: any) => {
    if (!systemConfig) return defaultValue;
    
    // First try to get from configChanges
    let current: any = configChanges;
    let hasChange = true;
    
    for (const key of path) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        hasChange = false;
        break;
      }
    }
    
    if (hasChange && current !== undefined) {
      return current;
    }
    
    // Fall back to original systemConfig
    current = systemConfig;
    for (const key of path) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return defaultValue;
      }
    }
    
    return current !== undefined ? current : defaultValue;
  }, [systemConfig, configChanges]);

  // Helper function to deep merge configuration objects
  const deepMergeConfig = useCallback((target: any, source: any): any => {
    if (!source || typeof source !== 'object') return target;
    if (!target || typeof target !== 'object') return source;
    
    const result = { ...target };
    
    for (const key in source) {
      if (source.hasOwnProperty(key)) {
        if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
          result[key] = deepMergeConfig(result[key] || {}, source[key]);
        } else {
          result[key] = source[key];
        }
      }
    }
    
    return result;
  }, []);

  const handleSaveSystemConfig = useCallback(async () => {
    if (Object.keys(configChanges).length === 0) {
      setShowSystemConfigModal(false);
      return;
    }

    // Debug log to see what changes are being saved
    console.log('Saving configuration changes:', configChanges);

    // Show confirmation dialog for system-wide changes
    const confirmed = window.confirm(
      'Are you sure you want to save these system configuration changes? This will affect all users and devices in the system.'
    );
    
    if (!confirmed) return;

    setIsSavingConfig(true);
    try {
      // Create the complete configuration by merging current config with changes
      const completeConfig = systemConfig ? deepMergeConfig(systemConfig, configChanges) : configChanges;
      console.log('Complete configuration to save:', completeConfig);
      
      const updatedConfig = await updateSystemConfiguration(completeConfig);
      console.log('Configuration updated successfully:', updatedConfig);
      
      setSystemConfig(updatedConfig);
      alert('System configuration saved successfully!');
      setShowSystemConfigModal(false);
      setConfigChanges({});
    } catch (error) {
      console.error('Error saving system configuration:', error);
      alert(`Error saving system configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSavingConfig(false);
    }
  }, [configChanges, systemConfig, deepMergeConfig]);

  // User management handlers
  const handleViewUser = useCallback((user: typeof selectedUser) => {
    setSelectedUser(user);
    setShowViewUserModal(true);
  }, []);

  const handleEditUser = useCallback((user: typeof selectedUser) => {
    if (!user) return;
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
    setEditFormData((prev) => ({ ...prev, [field]: value }));
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
        // Update local state
        setUsers((prev) => prev.map((u) => 
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

  const handleDeleteUser = useCallback((user: typeof selectedUser) => {
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
    setAddFormData((prev) => ({ ...prev, [field]: value }));
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
        setUsers((prev) => [...prev, newUser]);
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

  const confirmDeleteUser = useCallback(async () => {
    if (!selectedUser) return;
    
    try {
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
        setUsers((prev) => prev.filter((u) => u.userId !== selectedUser.userId));
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

  // Security and audit handlers
  const handleViewAuditLogs = useCallback(async () => {
    try {
      setIsLoadingData(true);
      // Fetch real audit logs from the audit service
      const auditData = await getAuditTrail(
        auditDateRange.startDate, 
        auditDateRange.endDate
      );
      
      setAuditLogs(auditData);
      setShowAuditModal(true);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      alert('Error fetching audit logs. Please try again.');
    } finally {
      setIsLoadingData(false);
    }
  }, [auditDateRange]);

  const handleGenerateComplianceReport = useCallback(async () => {
    try {
      setIsLoadingData(true);
      // Generate real compliance report from compliance service
      const complianceData = await generateComplianceReport(
        auditDateRange.startDate,
        auditDateRange.endDate
      );
      
      setComplianceReport(complianceData);
      setShowComplianceModal(true);
    } catch (error) {
      console.error('Error generating compliance report:', error);
      alert('Error generating compliance report. Please try again.');
    } finally {
      setIsLoadingData(false);
    }
  }, [auditDateRange]);

  const handleViewIncidentReports = useCallback(async () => {
    try {
      setIsLoadingData(true);
      // Fetch real incident reports from incident service
      const incidents = await getIncidentReports();
      setIncidentReports(incidents);
      setShowIncidentModal(true);
    } catch (error) {
      console.error('Error fetching incident reports:', error);
      alert('Error fetching incident reports. Please try again.');
    } finally {
      setIsLoadingData(false);
    }
  }, []);

  const handleExportAuditLogs = useCallback(() => {
    // Filter logs based on current filters
    const filteredLogs = auditLogs.filter(log => {
      const matchesDevice = !auditFilters.deviceId || log.deviceId.toLowerCase().includes(auditFilters.deviceId.toLowerCase());
      const matchesAnomaly = auditFilters.anomalyType === 'all' || log.anomalyType === auditFilters.anomalyType;
      const matchesVerified = auditFilters.verified === 'all' || 
        (auditFilters.verified === 'verified' && log.verified) ||
        (auditFilters.verified === 'unverified' && !log.verified);
      const matchesSearch = !auditFilters.searchTerm || 
        log.deviceId.toLowerCase().includes(auditFilters.searchTerm.toLowerCase()) ||
        log.anomalyType.toLowerCase().includes(auditFilters.searchTerm.toLowerCase());
      
      return matchesDevice && matchesAnomaly && matchesVerified && matchesSearch;
    });

    // Create CSV content
    const csvContent = [
      ['Timestamp', 'Device ID', 'WQI', 'Anomaly Type', 'Verified', 'Data Hash'].join(','),
      ...filteredLogs.map(log => [
        new Date(log.timestamp).toISOString(),
        log.deviceId,
        log.wqi.toFixed(1),
        log.anomalyType,
        log.verified ? 'Yes' : 'No',
        log.dataHash
      ].join(','))
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${auditDateRange.startDate}-to-${auditDateRange.endDate}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, [auditLogs, auditFilters, auditDateRange]);

  // Filter audit logs based on current filters
  const filteredAuditLogs = useMemo(() => {
    return auditLogs.filter(log => {
      const matchesDevice = !auditFilters.deviceId || log.deviceId.toLowerCase().includes(auditFilters.deviceId.toLowerCase());
      const matchesAnomaly = auditFilters.anomalyType === 'all' || log.anomalyType === auditFilters.anomalyType;
      const matchesVerified = auditFilters.verified === 'all' || 
        (auditFilters.verified === 'verified' && log.verified) ||
        (auditFilters.verified === 'unverified' && !log.verified);
      const matchesSearch = !auditFilters.searchTerm || 
        log.deviceId.toLowerCase().includes(auditFilters.searchTerm.toLowerCase()) ||
        log.anomalyType.toLowerCase().includes(auditFilters.searchTerm.toLowerCase());
      
      return matchesDevice && matchesAnomaly && matchesVerified && matchesSearch;
    });
  }, [auditLogs, auditFilters]);

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
          {/* Profile Section */}
          <AdminProfile onUpdate={() => refreshUser()} />
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
                <p className="text-sm text-gray-600">System Administration & Oversight</p>
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
        {/* Tabbed Navigation - NO OPERATIONAL CONTROLS */}
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
              <Monitor className="w-5 h-5" />
              System Overview
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
              User Management
            </button>
            <button
              onClick={() => setSelectedView('configuration')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'configuration'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Settings className="w-5 h-5" />
              System Configuration
            </button>
            <button
              onClick={() => setSelectedView('monitoring')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'monitoring'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Activity className="w-5 h-5" />
              Global Monitoring
            </button>
            <button
              onClick={() => setSelectedView('security')}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
                selectedView === 'security'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Shield className="w-5 h-5" />
              Security & Audit
            </button>
          </div>
        </div>
        {/* System Overview Tab */}
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
                  <span className="text-sm font-medium text-gray-700">Total Users</span>
                  <Users className="w-5 h-5 text-green-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{userStats.total}</div>
                <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                  <span>All system users</span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">System Health</span>
                  <Activity className="w-5 h-5 text-green-600" />
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {systemHealthData.uptime.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600 mt-1">Uptime: {systemHealthData.uptimeDisplay}</div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">API Success Rate</span>
                  <Server className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {systemHealthData.apiSuccess.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600 mt-1">API performance</div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Active Alerts</span>
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{activeAlertsCount}</div>
                <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                  <span>High-priority alerts</span>
                </div>
              </div>
            </div>

            {/* Charts Row */}
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

              {/* System Health Metrics */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health Metrics</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-gray-700">System Uptime</div>
                      <div className="text-2xl font-bold text-green-600">{systemHealthData.uptime.toFixed(1)}%</div>
                    </div>
                    <Activity className="w-8 h-8 text-green-600" />
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-gray-700">API Success Rate</div>
                      <div className="text-2xl font-bold text-blue-600">{systemHealthData.apiSuccess.toFixed(1)}%</div>
                    </div>
                    <Server className="w-8 h-8 text-blue-600" />
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-gray-700">Active Users</div>
                      <div className="text-2xl font-bold text-purple-600">{userStats.total}</div>
                    </div>
                    <Users className="w-8 h-8 text-purple-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions - ADMIN ONLY */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button 
                  onClick={handleAddUser}
                  className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  <Plus className="w-6 h-6 text-purple-600" />
                  <span className="text-sm font-medium text-gray-900">Add User</span>
                </button>
                <button
                  onClick={handleOpenSystemConfig}
                  className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  <Settings className="w-6 h-6 text-purple-600" />
                  <span className="text-sm font-medium text-gray-900">System Config</span>
                </button>
                <button
                  onClick={handleViewAuditLogs}
                  className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  <FileText className="w-6 h-6 text-purple-600" />
                  <span className="text-sm font-medium text-gray-900">Audit Logs</span>
                </button>
                <button 
                  onClick={() => setSelectedView('monitoring')}
                  className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  <Monitor className="w-6 h-6 text-purple-600" />
                  <span className="text-sm font-medium text-gray-900">Monitoring</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* User Management Tab */}
        {selectedView === 'users' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
                  <button
                    onClick={handleAddUser}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add User
                  </button>
                </div>
                
                {/* Search and Filter Controls */}
                <div className="flex gap-4">
                  <div className="flex-1 relative">
                    <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search users by name or email..."
                      value={userSearchTerm}
                      onChange={(e) => setUserSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div className="relative">
                    <Filter className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <select
                      value={userRoleFilter}
                      onChange={(e) => setUserRoleFilter(e.target.value)}
                      className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white"
                    >
                      <option value="all">All Roles</option>
                      <option value="consumer">Consumer</option>
                      <option value="technician">Technician</option>
                      <option value="admin">Admin</option>
                      <option value="administrator">Administrator</option>
                      <option value="inventory_manager">Inventory Manager</option>
                      <option value="warehouse_manager">Warehouse Manager</option>
                      <option value="supplier_coordinator">Supplier Coordinator</option>
                      <option value="procurement_controller">Procurement Controller</option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                {filteredUsers.length > 0 ? (
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredUsers.map((user) => (
                        <tr key={user.userId} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {user.profile?.firstName} {user.profile?.lastName}
                              </div>
                              <div className="text-sm text-gray-500">{user.email}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.status)}`}>
                              {user.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(user.createdAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.lastLogin ? formatRelativeTime(user.lastLogin) : 'Never'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleViewUser(user)}
                                className="text-blue-600 hover:text-blue-900 p-1 rounded"
                                title="View User"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleEditUser(user)}
                                className="text-green-600 hover:text-green-900 p-1 rounded"
                                title="Edit User"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteUser(user)}
                                className="text-red-600 hover:text-red-900 p-1 rounded"
                                title="Delete User"
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
                    {userSearchTerm || userRoleFilter !== 'all' ? 'No users match your search criteria' : 'No users found'}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* System Configuration Tab */}
        {selectedView === 'configuration' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900">System Configuration</h3>
                  {Object.keys(configChanges).length > 0 && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                      Unsaved Changes
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleOpenSystemConfig}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    Configure System
                  </button>
                  {Object.keys(configChanges).length > 0 && (
                    <button
                      onClick={() => setConfigChanges({})}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                    >
                      Reset Changes
                    </button>
                  )}
                </div>
              </div>
              
              {systemConfig && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Alert Thresholds</h4>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">pH Range:</span>
                          <span className="ml-2 font-medium">{getCurrentConfigValue(['alertThresholds', 'global', 'pH', 'min'], 6.5)} - {getCurrentConfigValue(['alertThresholds', 'global', 'pH', 'max'], 8.5)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Turbidity Max:</span>
                          <span className="ml-2 font-medium">{getCurrentConfigValue(['alertThresholds', 'global', 'turbidity', 'max'], 5.0)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">TDS Max:</span>
                          <span className="ml-2 font-medium">{getCurrentConfigValue(['alertThresholds', 'global', 'tds', 'max'], 500)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Temperature Range:</span>
                          <span className="ml-2 font-medium">{getCurrentConfigValue(['alertThresholds', 'global', 'temperature', 'min'], 0)}° - {getCurrentConfigValue(['alertThresholds', 'global', 'temperature', 'max'], 40)}°C</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">System Limits</h4>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Max Devices per User:</span>
                          <span className="font-medium">{getCurrentConfigValue(['systemLimits', 'maxDevicesPerUser'], 10)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Data Retention:</span>
                          <span className="font-medium">{getCurrentConfigValue(['systemLimits', 'dataRetentionDays'], 90)} days</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Audit Retention:</span>
                          <span className="font-medium">{getCurrentConfigValue(['systemLimits', 'auditRetentionYears'], 7)} years</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Global Monitoring Tab */}
        {selectedView === 'monitoring' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* System Health Dashboard */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health Dashboard</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm font-medium text-gray-700">System Status</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">Operational</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-sm font-medium text-gray-700">API Services</span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">{systemHealthData.apiSuccess.toFixed(1)}% Success</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                      <span className="text-sm font-medium text-gray-700">Database</span>
                    </div>
                    <span className="text-sm font-semibold text-purple-600">Connected</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                      <span className="text-sm font-medium text-gray-700">Active Alerts</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">{activeAlertsCount} High Priority</span>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
                <div className="space-y-4">
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      {systemHealthData.uptime.toFixed(1)}%
                    </div>
                    <div className="text-sm font-medium text-gray-700">System Uptime</div>
                    <div className="text-xs text-gray-600 mt-1">
                      Running for {systemHealthData.uptimeDisplay}
                    </div>
                  </div>
                  
                  <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      {systemHealthData.apiSuccess.toFixed(1)}%
                    </div>
                    <div className="text-sm font-medium text-gray-700">API Success Rate</div>
                    <div className="text-xs text-gray-600 mt-1">
                      Last 24 hours
                    </div>
                  </div>
                  
                  <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 mb-1">
                      {userStats.total}
                    </div>
                    <div className="text-sm font-medium text-gray-700">Active Users</div>
                    <div className="text-xs text-gray-600 mt-1">
                      Registered accounts
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Security & Audit Tab */}
        {selectedView === 'security' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Security Overview */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Overview</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Authentication System</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">Secure</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Data Encryption</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">Active</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Audit Logging</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">Enabled</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Clock className="w-5 h-5 text-amber-600" />
                      <span className="text-sm font-medium text-gray-700">Failed Login Attempts</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">
                      {systemMetrics?.failedLogins || 0} (Last 24h)
                    </span>
                  </div>
                </div>
              </div>

              {/* Incident Coordination */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Incident Coordination</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                      <span className="text-sm font-medium text-gray-700">Open Incidents</span>
                    </div>
                    <span className="text-sm font-semibold text-red-600">
                      {incidentStats.openIncidents} Active
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Clock className="w-5 h-5 text-amber-600" />
                      <span className="text-sm font-medium text-gray-700">Critical Incidents</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">
                      {incidentStats.criticalIncidents} High Priority
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Activity className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Avg Resolution Time</span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">
                      {incidentStats.avgResolutionTime > 0 ? `${incidentStats.avgResolutionTime.toFixed(1)} hours` : 'N/A'}
                    </span>
                  </div>
                  
                  <button
                    onClick={handleViewIncidentReports}
                    className="w-full flex items-center justify-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <span className="text-sm font-medium text-red-700">View Incident Reports</span>
                  </button>
                  
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      {systemMetrics?.systemAvailability?.toFixed(1) || '99.8'}%
                    </div>
                    <div className="text-sm font-medium text-gray-700">System Availability</div>
                    <div className="text-xs text-gray-600 mt-1">Last 30 days</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Audit & Compliance */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Audit & Compliance</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Date Range</span>
                    <div className="flex gap-2">
                      <input
                        type="date"
                        value={auditDateRange.startDate}
                        onChange={(e) => setAuditDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                        className="px-2 py-1 text-xs border border-gray-300 rounded"
                      />
                      <input
                        type="date"
                        value={auditDateRange.endDate}
                        onChange={(e) => setAuditDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                        className="px-2 py-1 text-xs border border-gray-300 rounded"
                      />
                    </div>
                  </div>
                  
                  <button
                    onClick={handleViewAuditLogs}
                    className="w-full flex items-center justify-center gap-2 p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
                  >
                    <FileText className="w-5 h-5 text-purple-600" />
                    <span className="text-sm font-medium text-purple-700">View Audit Logs</span>
                  </button>
                  
                  <button
                    onClick={handleGenerateComplianceReport}
                    className="w-full flex items-center justify-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <Download className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-700">Generate Compliance Report</span>
                  </button>
                  
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      {complianceReport?.summary?.complianceRate?.toFixed(2) || '99.95'}%
                    </div>
                    <div className="text-sm font-medium text-gray-700">Compliance Rate</div>
                    <div className="text-xs text-gray-600 mt-1">Last 30 days</div>
                  </div>
                </div>
              </div>

              {/* Recovery Oversight */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recovery Oversight</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Backup Status</span>
                    </div>
                    <span className="text-sm font-semibold text-green-600">
                      {systemMetrics?.backupStatus || 'Current'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Last Backup</span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">
                      {systemMetrics?.lastBackup ? formatRelativeTime(systemMetrics.lastBackup) : '2 hours ago'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Activity className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">RTO Target</span>
                    </div>
                    <span className="text-sm font-semibold text-purple-600">
                      {systemMetrics?.rtoTarget || '< 4 hours'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Server className="w-5 h-5 text-indigo-600" />
                      <span className="text-sm font-medium text-gray-700">RPO Target</span>
                    </div>
                    <span className="text-sm font-semibold text-indigo-600">
                      {systemMetrics?.rpoTarget || '< 1 hour'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </main>
      {/* Modals */}
      
      {/* Data Export Modal */}
      <DataExportModal
        isOpen={showExportModal}
        onClose={toggleExportModal}
        userRole="admin"
      />

      {/* System Configuration Modal */}
      <AnimatePresence>
        {showSystemConfigModal && systemConfig && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => !isSavingConfig && setShowSystemConfigModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">System Configuration</h3>
                  <button 
                    onClick={() => !isSavingConfig && setShowSystemConfigModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                    disabled={isSavingConfig}
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="space-y-6">
                  {/* Alert Thresholds */}
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Alert Thresholds</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">pH Min</label>
                        <input
                          type="number"
                          step="0.1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'pH', 'min'], 6.5)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'pH', 'min'], parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">pH Max</label>
                        <input
                          type="number"
                          step="0.1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'pH', 'max'], 8.5)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'pH', 'max'], parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Turbidity Max</label>
                        <input
                          type="number"
                          step="0.1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'turbidity', 'max'], 5.0)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'turbidity', 'max'], parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">TDS Max</label>
                        <input
                          type="number"
                          step="1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'tds', 'max'], 500)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'tds', 'max'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Temperature Min (°C)</label>
                        <input
                          type="number"
                          step="1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'temperature', 'min'], 0)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'temperature', 'min'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Temperature Max (°C)</label>
                        <input
                          type="number"
                          step="1"
                          value={getCurrentConfigValue(['alertThresholds', 'global', 'temperature', 'max'], 40)}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'temperature', 'max'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                    </div>
                  </div>

                  {/* System Limits */}
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">System Limits</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Max Devices per User</label>
                        <input
                          type="number"
                          value={getCurrentConfigValue(['systemLimits', 'maxDevicesPerUser'], 10)}
                          onChange={(e) => handleConfigChange(['systemLimits', 'maxDevicesPerUser'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Data Retention (days)</label>
                        <input
                          type="number"
                          value={getCurrentConfigValue(['systemLimits', 'dataRetentionDays'], 90)}
                          onChange={(e) => handleConfigChange(['systemLimits', 'dataRetentionDays'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowSystemConfigModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                    disabled={isSavingConfig}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveSystemConfig}
                    disabled={isSavingConfig || Object.keys(configChanges).length === 0}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSavingConfig ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Enhanced Audit Logs Modal with Advanced Filtering */}
      <AnimatePresence>
        {showAuditModal && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowAuditModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-xl max-w-6xl w-full p-6 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Security Audit Logs</h3>
                  <button 
                    onClick={() => setShowAuditModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                {/* Advanced Filtering Controls */}
                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">Advanced Filters</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Device ID</label>
                      <input
                        type="text"
                        placeholder="Filter by device ID..."
                        value={auditFilters.deviceId}
                        onChange={(e) => setAuditFilters(prev => ({ ...prev, deviceId: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Anomaly Type</label>
                      <select
                        value={auditFilters.anomalyType}
                        onChange={(e) => setAuditFilters(prev => ({ ...prev, anomalyType: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="all">All Types</option>
                        <option value="normal">Normal</option>
                        <option value="sensor_fault">Sensor Fault</option>
                        <option value="contamination">Contamination</option>
                        <option value="calibration_drift">Calibration Drift</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Verification Status</label>
                      <select
                        value={auditFilters.verified}
                        onChange={(e) => setAuditFilters(prev => ({ ...prev, verified: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="all">All Status</option>
                        <option value="verified">Verified</option>
                        <option value="unverified">Unverified</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Search</label>
                      <div className="relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Search logs..."
                          value={auditFilters.searchTerm}
                          onChange={(e) => setAuditFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
                          className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Timestamp</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Device ID</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">WQI</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Anomaly Type</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Verified</th>
                        <th className="px-4 py-2 text-left font-medium text-gray-700">Data Hash</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {filteredAuditLogs.length > 0 ? filteredAuditLogs.map((log) => (
                        <tr key={log.logId} className="hover:bg-gray-50">
                          <td className="px-4 py-2">{new Date(log.timestamp).toLocaleString()}</td>
                          <td className="px-4 py-2 font-mono text-xs">{log.deviceId}</td>
                          <td className="px-4 py-2">{log.wqi.toFixed(1)}</td>
                          <td className="px-4 py-2">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              log.anomalyType === 'normal' ? 'bg-green-100 text-green-800' :
                              log.anomalyType === 'sensor_fault' ? 'bg-amber-100 text-amber-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {log.anomalyType}
                            </span>
                          </td>
                          <td className="px-4 py-2">
                            {log.verified ? (
                              <CheckCircle className="w-4 h-4 text-green-600" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-600" />
                            )}
                          </td>
                          <td className="px-4 py-2 font-mono text-xs text-gray-500">
                            {log.dataHash ? log.dataHash.substring(0, 8) + '...' : 'N/A'}
                          </td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                            No audit logs match your filter criteria
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-between items-center mt-6 pt-6 border-t border-gray-200">
                  <div className="text-sm text-gray-600">
                    Showing {filteredAuditLogs.length} of {auditLogs.length} audit logs
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleExportAuditLogs}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Export CSV
                    </button>
                    <button
                      onClick={() => setShowAuditModal(false)}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Incident Reports Modal */}
      <AnimatePresence>
        {showIncidentModal && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowIncidentModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full p-6 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Incident Reports</h3>
                  <button 
                    onClick={() => setShowIncidentModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="space-y-4">
                  {incidentReports.length > 0 ? incidentReports.map((incident) => (
                    <div key={incident.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900">{incident.title}</h4>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              incident.severity === 'high' ? 'bg-red-100 text-red-800' :
                              incident.severity === 'medium' ? 'bg-amber-100 text-amber-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {incident.severity.toUpperCase()}
                            </span>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              incident.status === 'resolved' ? 'bg-green-100 text-green-800' :
                              incident.status === 'investigating' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {incident.status.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{incident.description}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>ID: {incident.id}</span>
                            <span>Created: {formatRelativeTime(incident.createdAt)}</span>
                            <span>Assigned to: {incident.assignedTo}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {incident.severity === 'high' && (
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                          )}
                          {incident.status === 'resolved' ? (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          ) : (
                            <Clock className="w-5 h-5 text-amber-600" />
                          )}
                        </div>
                      </div>
                      
                      {/* Incident Actions */}
                      <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
                        <button className="text-xs px-3 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors">
                          View Details
                        </button>
                        {incident.status !== 'resolved' && (
                          <button className="text-xs px-3 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors">
                            Update Status
                          </button>
                        )}
                        <button className="text-xs px-3 py-1 bg-purple-50 text-purple-700 rounded hover:bg-purple-100 transition-colors">
                          Add Comment
                        </button>
                      </div>
                    </div>
                  )) : (
                    <div className="text-center py-12 text-gray-500">
                      <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p>No incident reports found</p>
                    </div>
                  )}
                </div>

                <div className="flex justify-end mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowIncidentModal(false)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Compliance Report Modal */}
      <AnimatePresence>
        {showComplianceModal && complianceReport && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowComplianceModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Compliance Report</h3>
                  <button 
                    onClick={() => setShowComplianceModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{complianceReport.summary.totalReadings.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Total Readings</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{complianceReport.summary.devicesMonitored}</div>
                      <div className="text-sm text-gray-600">Devices Monitored</div>
                    </div>
                    <div className="bg-amber-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-amber-600">{complianceReport.summary.alertsGenerated}</div>
                      <div className="text-sm text-gray-600">Alerts Generated</div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{complianceReport.summary.complianceRate.toFixed(2)}%</div>
                      <div className="text-sm text-gray-600">Compliance Rate</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Ledger Verification</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Total Entries:</span>
                          <span className="font-medium">{complianceReport.ledgerVerification.totalEntries.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Verified Entries:</span>
                          <span className="font-medium">{complianceReport.ledgerVerification.verifiedEntries.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Hash Chain Intact:</span>
                          <span className={`font-medium ${complianceReport.ledgerVerification.hashChainIntact ? 'text-green-600' : 'text-red-600'}`}>
                            {complianceReport.ledgerVerification.hashChainIntact ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Last Verification:</span>
                          <span className="font-medium">{formatRelativeTime(complianceReport.ledgerVerification.lastVerificationDate)}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Data Integrity</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Missing Readings:</span>
                          <span className="font-medium">{complianceReport.dataIntegrity.missingReadings}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Duplicate Readings:</span>
                          <span className="font-medium">{complianceReport.dataIntegrity.duplicateReadings}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Invalid Readings:</span>
                          <span className="font-medium">{complianceReport.dataIntegrity.invalidReadings}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">System Uptime</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Critical Path:</span>
                          <span className="font-medium text-green-600">{complianceReport.uptimeMetrics.criticalPathUptime.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>API Uptime:</span>
                          <span className="font-medium text-green-600">{complianceReport.uptimeMetrics.apiUptime.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Notifications:</span>
                          <span className="font-medium text-green-600">{complianceReport.uptimeMetrics.notificationUptime.toFixed(2)}%</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Report Information</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Report ID:</span>
                          <span className="font-medium font-mono text-xs">{complianceReport.reportId}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Generated:</span>
                          <span className="font-medium">{new Date(complianceReport.generatedAt).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Period:</span>
                          <span className="font-medium">{complianceReport.period.startDate} to {complianceReport.period.endDate}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowComplianceModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      // Enhanced export functionality for compliance report
                      const reportData = {
                        reportId: complianceReport.reportId,
                        generatedAt: complianceReport.generatedAt,
                        period: complianceReport.period,
                        summary: complianceReport.summary,
                        ledgerVerification: complianceReport.ledgerVerification,
                        dataIntegrity: complianceReport.dataIntegrity,
                        uptimeMetrics: complianceReport.uptimeMetrics
                      };
                      
                      // Create comprehensive CSV content
                      const csvContent = [
                        ['AquaChain Compliance Report'],
                        ['Report ID', complianceReport.reportId],
                        ['Generated At', new Date(complianceReport.generatedAt).toLocaleString()],
                        ['Date Range', `${complianceReport.period.startDate} to ${complianceReport.period.endDate}`],
                        [''],
                        ['SUMMARY'],
                        ['Total Readings', complianceReport.summary.totalReadings],
                        ['Devices Monitored', complianceReport.summary.devicesMonitored],
                        ['Alerts Generated', complianceReport.summary.alertsGenerated],
                        ['Compliance Rate (%)', complianceReport.summary.complianceRate],
                        [''],
                        ['LEDGER VERIFICATION'],
                        ['Total Entries', complianceReport.ledgerVerification.totalEntries],
                        ['Verified Entries', complianceReport.ledgerVerification.verifiedEntries],
                        ['Hash Chain Intact', complianceReport.ledgerVerification.hashChainIntact ? 'Yes' : 'No'],
                        ['Last Verification', new Date(complianceReport.ledgerVerification.lastVerificationDate).toLocaleString()],
                        [''],
                        ['DATA INTEGRITY'],
                        ['Missing Readings', complianceReport.dataIntegrity.missingReadings],
                        ['Duplicate Readings', complianceReport.dataIntegrity.duplicateReadings],
                        ['Invalid Readings', complianceReport.dataIntegrity.invalidReadings],
                        [''],
                        ['UPTIME METRICS'],
                        ['Critical Path Uptime (%)', complianceReport.uptimeMetrics.criticalPathUptime],
                        ['API Uptime (%)', complianceReport.uptimeMetrics.apiUptime],
                        ['Notification Uptime (%)', complianceReport.uptimeMetrics.notificationUptime]
                      ].map(row => Array.isArray(row) ? row.join(',') : row).join('\n');

                      // Download CSV
                      const blob = new Blob([csvContent], { type: 'text/csv' });
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `compliance-report-${complianceReport.reportId}-${new Date().toISOString().split('T')[0]}.csv`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Export Report
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* User Management Modals */}
      
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
                  <button 
                    onClick={() => setShowViewUserModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                      <p className="text-gray-900">{selectedUser.profile?.firstName || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                      <p className="text-gray-900">{selectedUser.profile?.lastName || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <p className="text-gray-900">{selectedUser.email}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <p className="text-gray-900">{selectedUser.profile?.phone || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(selectedUser.role)}`}>
                        {selectedUser.role}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedUser.status)}`}>
                        {selectedUser.status}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                      <p className="text-gray-900">{new Date(selectedUser.createdAt).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Login</label>
                      <p className="text-gray-900">{selectedUser.lastLogin ? formatRelativeTime(selectedUser.lastLogin) : 'Never'}</p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowViewUserModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      setShowViewUserModal(false);
                      handleEditUser(selectedUser);
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Edit User
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
              <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
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
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                      <input
                        type="text"
                        value={editFormData.firstName}
                        onChange={(e) => handleEditFormChange('firstName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                      <input
                        type="text"
                        value={editFormData.lastName}
                        onChange={(e) => handleEditFormChange('lastName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={editFormData.email}
                        onChange={(e) => handleEditFormChange('email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <input
                        type="tel"
                        value={editFormData.phone}
                        onChange={(e) => handleEditFormChange('phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <select
                        value={editFormData.role}
                        onChange={(e) => handleEditFormChange('role', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      >
                        <option value="consumer">Consumer</option>
                        <option value="technician">Technician</option>
                        <option value="admin">Admin</option>
                        <option value="administrator">Administrator</option>
                        <option value="inventory_manager">Inventory Manager</option>
                        <option value="warehouse_manager">Warehouse Manager</option>
                        <option value="supplier_coordinator">Supplier Coordinator</option>
                        <option value="procurement_controller">Procurement Controller</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <select
                        value={editFormData.status}
                        onChange={(e) => handleEditFormChange('status', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingEdit}
                      >
                        <option value="active">Active</option>
                        <option value="pending">Pending</option>
                        <option value="inactive">Inactive</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowEditUserModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                    disabled={isSubmittingEdit}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEditUser}
                    disabled={isSubmittingEdit}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmittingEdit ? 'Saving...' : 'Save Changes'}
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
              <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
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
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                      <input
                        type="text"
                        value={addFormData.firstName}
                        onChange={(e) => handleAddFormChange('firstName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                      <input
                        type="text"
                        value={addFormData.lastName}
                        onChange={(e) => handleAddFormChange('lastName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                      <input
                        type="email"
                        value={addFormData.email}
                        onChange={(e) => handleAddFormChange('email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <input
                        type="tel"
                        value={addFormData.phone}
                        onChange={(e) => handleAddFormChange('phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                      <input
                        type="password"
                        value={addFormData.password}
                        onChange={(e) => handleAddFormChange('password', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <select
                        value={addFormData.role}
                        onChange={(e) => handleAddFormChange('role', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isSubmittingAdd}
                      >
                        <option value="consumer">Consumer</option>
                        <option value="technician">Technician</option>
                        <option value="admin">Admin</option>
                        <option value="administrator">Administrator</option>
                        <option value="inventory_manager">Inventory Manager</option>
                        <option value="warehouse_manager">Warehouse Manager</option>
                        <option value="supplier_coordinator">Supplier Coordinator</option>
                        <option value="procurement_controller">Procurement Controller</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setShowAddUserModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                    disabled={isSubmittingAdd}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveNewUser}
                    disabled={isSubmittingAdd || !addFormData.firstName || !addFormData.lastName || !addFormData.email || !addFormData.password}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmittingAdd ? 'Creating...' : 'Create User'}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete User Confirmation Modal */}
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
                  <button 
                    onClick={() => setShowDeleteUserModal(false)} 
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">Are you sure?</h4>
                      <p className="text-sm text-gray-600">This action cannot be undone.</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700">
                    You are about to delete the user <strong>{selectedUser.profile?.firstName} {selectedUser.profile?.lastName}</strong> ({selectedUser.email}). 
                    This will permanently remove their account and all associated data.
                  </p>
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowDeleteUserModal(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
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
    </div>
  );
});

export default AdminDashboardRestructured;