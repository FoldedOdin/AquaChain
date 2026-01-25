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
} from '../../services/adminService';
import { formatRelativeTime } from '../../utils/dateFormat';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface AdminDashboardRestructuredProps {
  // Optional props for customization
}

const AdminDashboardRestructured: React.FC<AdminDashboardRestructuredProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedView, setSelectedView] = useState('overview');
  
  // System configuration state
  const [systemConfig, setSystemConfig] = useState<any>(null);
  const [showSystemConfigModal, setShowSystemConfigModal] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [configChanges, setConfigChanges] = useState<any>({});
  
  // User management state
  const [users, setUsers] = useState<any[]>([]);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showViewUserModal, setShowViewUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showDeleteUserModal, setShowDeleteUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('all');
  
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
  
  // System monitoring state
  const [systemMetrics, setSystemMetrics] = useState<any>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<any[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  
  // Security and audit state
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [complianceReport, setComplianceReport] = useState<any>(null);
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
  const [incidentReports, setIncidentReports] = useState<any[]>([]);

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useDashboardData('admin');
  const { isConnected } = useRealTimeUpdates('admin-updates', { autoConnect: true });
  const { notifications } = useNotifications();

  // Fetch users and system configuration
  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingData(true);
      try {
        const [usersData, configData, healthMetrics, perfMetrics] = await Promise.all([
          getAllUsers(),
          getSystemConfiguration(),
          getSystemHealthMetrics(),
          getPerformanceMetrics('24h')
        ]);
        
        setUsers(usersData);
        setSystemConfig(configData);
        setSystemMetrics(healthMetrics);
        setPerformanceMetrics(perfMetrics);
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
        const [healthMetrics, perfMetrics] = await Promise.all([
          getSystemHealthMetrics(),
          getPerformanceMetrics('24h')
        ]);
        setSystemMetrics(healthMetrics);
        setPerformanceMetrics(perfMetrics);
      } catch (err) {
        console.error('Failed to refresh metrics:', err);
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

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
    if (!systemMetrics) {
      return { uptime: 0, apiSuccess: 0, uptimeDisplay: 'N/A' };
    }
    return {
      uptime: systemMetrics.criticalPathUptime || 100,
      apiSuccess: systemMetrics.apiUptime || 0,
      uptimeDisplay: 'Operational'
    };
  }, [systemMetrics]);

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
    setConfigChanges((prev: any) => {
      const newChanges = { ...prev };
      let current = newChanges;
      
      for (let i = 0; i < path.length - 1; i++) {
        if (!current[path[i]]) {
          current[path[i]] = {};
        }
        current = current[path[i]];
      }
      
      current[path[path.length - 1]] = value;
      return newChanges;
    });
  }, []);

  const handleSaveSystemConfig = useCallback(async () => {
    if (Object.keys(configChanges).length === 0) {
      setShowSystemConfigModal(false);
      return;
    }

    // Show confirmation dialog for system-wide changes
    const confirmed = window.confirm(
      'Are you sure you want to save these system configuration changes? This will affect all users and devices in the system.'
    );
    
    if (!confirmed) return;

    setIsSavingConfig(true);
    try {
      const updatedConfig = await updateSystemConfiguration(configChanges);
      setSystemConfig(updatedConfig);
      alert('System configuration saved successfully!');
      setShowSystemConfigModal(false);
      setConfigChanges({});
    } catch (error) {
      console.error('Error saving system configuration:', error);
      alert('Error saving system configuration');
    } finally {
      setIsSavingConfig(false);
    }
  }, [configChanges]);

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
    setEditFormData((prev: any) => ({ ...prev, [field]: value }));
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
        setUsers((prev: any) => prev.map((u: any) => 
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
    setAddFormData((prev: any) => ({ ...prev, [field]: value }));
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
        setUsers((prev: any) => [...prev, newUser]);
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
        setUsers((prev: any) => prev.filter((u: any) => u.userId !== selectedUser.userId));
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
      // Mock audit logs for demonstration - in real implementation, this would fetch from audit service
      const mockAuditLogs = [
        {
          logId: 'audit-001',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          deviceId: 'AQ-DEV-001',
          wqi: 85.2,
          anomalyType: 'normal',
          verified: true,
          dataHash: 'a1b2c3d4e5f6789012345678901234567890abcd'
        },
        {
          logId: 'audit-002',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          deviceId: 'AQ-DEV-002',
          wqi: 45.8,
          anomalyType: 'contamination',
          verified: false,
          dataHash: 'b2c3d4e5f6789012345678901234567890abcde1'
        },
        {
          logId: 'audit-003',
          timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
          deviceId: 'AQ-DEV-003',
          wqi: 92.1,
          anomalyType: 'sensor_fault',
          verified: true,
          dataHash: 'c3d4e5f6789012345678901234567890abcde12f'
        },
        {
          logId: 'audit-004',
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
          deviceId: 'AQ-DEV-001',
          wqi: 78.9,
          anomalyType: 'calibration_drift',
          verified: true,
          dataHash: 'd4e5f6789012345678901234567890abcde12f34'
        },
        {
          logId: 'audit-005',
          timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
          deviceId: 'AQ-DEV-004',
          wqi: 88.7,
          anomalyType: 'normal',
          verified: true,
          dataHash: 'e5f6789012345678901234567890abcde12f3456'
        }
      ];
      
      setAuditLogs(mockAuditLogs);
      setShowAuditModal(true);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      alert('Error fetching audit logs');
    }
  }, []);

  const handleGenerateComplianceReport = useCallback(async () => {
    try {
      // Mock compliance report for demonstration - in real implementation, this would fetch from compliance service
      const mockComplianceReport = {
        reportId: 'COMP-' + Date.now(),
        generatedAt: new Date().toISOString(),
        dateRange: {
          startDate: auditDateRange.startDate,
          endDate: auditDateRange.endDate
        },
        summary: {
          totalReadings: 45678,
          devicesMonitored: 127,
          alertsGenerated: 23,
          complianceRate: 99.74
        },
        ledgerVerification: {
          totalEntries: 45678,
          verifiedEntries: 45654,
          hashChainIntact: true,
          lastVerificationTime: new Date(Date.now() - 30 * 60 * 1000).toISOString()
        },
        dataIntegrity: {
          missingReadings: 12,
          duplicateReadings: 3,
          invalidReadings: 9,
          integrityScore: 99.95
        },
        securityEvents: {
          unauthorizedAccess: 0,
          failedLogins: 3,
          suspiciousActivity: 1,
          securityScore: 98.2
        },
        regulatoryCompliance: {
          gdprCompliance: true,
          dataRetentionCompliance: true,
          auditTrailCompleteness: 99.98,
          encryptionCompliance: true
        }
      };
      
      setComplianceReport(mockComplianceReport);
      setShowComplianceModal(true);
    } catch (error) {
      console.error('Error generating compliance report:', error);
      alert('Error generating compliance report');
    }
  }, [auditDateRange]);

  const handleViewIncidentReports = useCallback(async () => {
    try {
      // Mock incident reports - in real implementation, this would fetch from incident service
      const incidents = [
        {
          id: 'INC-001',
          title: 'Unauthorized Access Attempt',
          severity: 'high',
          status: 'investigating',
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          assignedTo: 'security-team',
          description: 'Multiple failed login attempts detected from suspicious IP address'
        },
        {
          id: 'INC-002',
          title: 'System Performance Degradation',
          severity: 'medium',
          status: 'resolved',
          createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          assignedTo: 'ops-team',
          description: 'API response times exceeded threshold for 15 minutes'
        }
      ];
      setIncidentReports(incidents);
      setShowIncidentModal(true);
    } catch (error) {
      console.error('Error fetching incident reports:', error);
      alert('Error fetching incident reports');
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
        {/* Connection Status */}
        {!isConnected && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="text-sm text-amber-800">Real-time updates disconnected.</span>
          </div>
        )}

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
                <h3 className="text-lg font-semibold text-gray-900">System Configuration</h3>
                <button
                  onClick={handleOpenSystemConfig}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Configure System
                </button>
              </div>
              
              {systemConfig && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Alert Thresholds</h4>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">pH Range:</span>
                          <span className="ml-2 font-medium">{systemConfig.alertThresholds?.global?.pH?.min} - {systemConfig.alertThresholds?.global?.pH?.max}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Turbidity Max:</span>
                          <span className="ml-2 font-medium">{systemConfig.alertThresholds?.global?.turbidity?.max}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">TDS Max:</span>
                          <span className="ml-2 font-medium">{systemConfig.alertThresholds?.global?.tds?.max}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Temperature Range:</span>
                          <span className="ml-2 font-medium">{systemConfig.alertThresholds?.global?.temperature?.min}° - {systemConfig.alertThresholds?.global?.temperature?.max}°C</span>
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
                          <span className="font-medium">{systemConfig.systemLimits?.maxDevicesPerUser}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Data Retention:</span>
                          <span className="font-medium">{systemConfig.systemLimits?.dataRetentionDays} days</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Audit Retention:</span>
                          <span className="font-medium">{systemConfig.systemLimits?.auditRetentionYears} years</span>
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
                    <span className="text-sm font-semibold text-amber-600">3 (Last 24h)</span>
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
                      <span className="text-sm font-medium text-gray-700">Active Incidents</span>
                    </div>
                    <span className="text-sm font-semibold text-red-600">1 High Priority</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Clock className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Avg Resolution Time</span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">2.3 hours</span>
                  </div>
                  
                  <button
                    onClick={handleViewIncidentReports}
                    className="w-full flex items-center justify-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <span className="text-sm font-medium text-red-700">View Incident Reports</span>
                  </button>
                  
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">99.8%</div>
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
                    <div className="text-2xl font-bold text-green-600 mb-1">99.95%</div>
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
                    <span className="text-sm font-semibold text-green-600">Current</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Last Backup</span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">2 hours ago</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Activity className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">RTO Target</span>
                    </div>
                    <span className="text-sm font-semibold text-purple-600">&lt; 4 hours</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Server className="w-5 h-5 text-indigo-600" />
                      <span className="text-sm font-medium text-gray-700">RPO Target</span>
                    </div>
                    <span className="text-sm font-semibold text-indigo-600">&lt; 1 hour</span>
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
                          value={systemConfig.alertThresholds?.global?.pH?.min || 6.5}
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
                          value={systemConfig.alertThresholds?.global?.pH?.max || 8.5}
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
                          value={systemConfig.alertThresholds?.global?.turbidity?.max || 5.0}
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
                          value={systemConfig.alertThresholds?.global?.tds?.max || 500}
                          onChange={(e) => handleConfigChange(['alertThresholds', 'global', 'tds', 'max'], parseInt(e.target.value))}
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
                          value={systemConfig.systemLimits?.maxDevicesPerUser || 10}
                          onChange={(e) => handleConfigChange(['systemLimits', 'maxDevicesPerUser'], parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          disabled={isSavingConfig}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Data Retention (days)</label>
                        <input
                          type="number"
                          value={systemConfig.systemLimits?.dataRetentionDays || 90}
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
                          <span className="font-medium">{formatRelativeTime(complianceReport.ledgerVerification.lastVerificationTime)}</span>
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
                        <div className="flex justify-between">
                          <span>Integrity Score:</span>
                          <span className="font-medium text-green-600">{complianceReport.dataIntegrity.integrityScore.toFixed(2)}%</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Security Events</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Unauthorized Access:</span>
                          <span className="font-medium">{complianceReport.securityEvents.unauthorizedAccess}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Failed Logins:</span>
                          <span className="font-medium">{complianceReport.securityEvents.failedLogins}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Suspicious Activity:</span>
                          <span className="font-medium">{complianceReport.securityEvents.suspiciousActivity}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Security Score:</span>
                          <span className="font-medium text-green-600">{complianceReport.securityEvents.securityScore.toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Regulatory Compliance</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>GDPR Compliance:</span>
                          <span className={`font-medium ${complianceReport.regulatoryCompliance.gdprCompliance ? 'text-green-600' : 'text-red-600'}`}>
                            {complianceReport.regulatoryCompliance.gdprCompliance ? 'Compliant' : 'Non-Compliant'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Data Retention:</span>
                          <span className={`font-medium ${complianceReport.regulatoryCompliance.dataRetentionCompliance ? 'text-green-600' : 'text-red-600'}`}>
                            {complianceReport.regulatoryCompliance.dataRetentionCompliance ? 'Compliant' : 'Non-Compliant'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Audit Trail:</span>
                          <span className="font-medium text-green-600">{complianceReport.regulatoryCompliance.auditTrailCompleteness.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Encryption:</span>
                          <span className={`font-medium ${complianceReport.regulatoryCompliance.encryptionCompliance ? 'text-green-600' : 'text-red-600'}`}>
                            {complianceReport.regulatoryCompliance.encryptionCompliance ? 'Enabled' : 'Disabled'}
                          </span>
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
                        dateRange: complianceReport.dateRange,
                        summary: complianceReport.summary,
                        ledgerVerification: complianceReport.ledgerVerification,
                        dataIntegrity: complianceReport.dataIntegrity,
                        securityEvents: complianceReport.securityEvents,
                        regulatoryCompliance: complianceReport.regulatoryCompliance
                      };
                      
                      // Create comprehensive CSV content
                      const csvContent = [
                        ['AquaChain Compliance Report'],
                        ['Report ID', complianceReport.reportId],
                        ['Generated At', new Date(complianceReport.generatedAt).toLocaleString()],
                        ['Date Range', `${complianceReport.dateRange.startDate} to ${complianceReport.dateRange.endDate}`],
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
                        ['Last Verification', new Date(complianceReport.ledgerVerification.lastVerificationTime).toLocaleString()],
                        [''],
                        ['DATA INTEGRITY'],
                        ['Missing Readings', complianceReport.dataIntegrity.missingReadings],
                        ['Duplicate Readings', complianceReport.dataIntegrity.duplicateReadings],
                        ['Invalid Readings', complianceReport.dataIntegrity.invalidReadings],
                        ['Integrity Score (%)', complianceReport.dataIntegrity.integrityScore],
                        [''],
                        ['SECURITY EVENTS'],
                        ['Unauthorized Access', complianceReport.securityEvents.unauthorizedAccess],
                        ['Failed Logins', complianceReport.securityEvents.failedLogins],
                        ['Suspicious Activity', complianceReport.securityEvents.suspiciousActivity],
                        ['Security Score (%)', complianceReport.securityEvents.securityScore],
                        [''],
                        ['REGULATORY COMPLIANCE'],
                        ['GDPR Compliance', complianceReport.regulatoryCompliance.gdprCompliance ? 'Compliant' : 'Non-Compliant'],
                        ['Data Retention Compliance', complianceReport.regulatoryCompliance.dataRetentionCompliance ? 'Compliant' : 'Non-Compliant'],
                        ['Audit Trail Completeness (%)', complianceReport.regulatoryCompliance.auditTrailCompleteness],
                        ['Encryption Compliance', complianceReport.regulatoryCompliance.encryptionCompliance ? 'Enabled' : 'Disabled']
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
    </div>
  );
});

export default AdminDashboardRestructured;