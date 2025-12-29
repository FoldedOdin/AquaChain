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
  ClockIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { 
  Droplet, 
  Activity, 
  Thermometer, 
  Beaker, 
  Waves, 
  Eye, 
  Download, 
  Plus,
  AlertTriangle,
  Info,
  Package,
  User
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import AddDeviceModal from './AddDeviceModal';
import EditProfileModal from './EditProfileModal';
import DataExportModal from './DataExportModal';
import RequestDeviceModal from './RequestDeviceModal';
import MyOrdersPage from './MyOrdersPage';

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
  const { user, logout, refreshUser } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showFullReport, setShowFullReport] = useState(false);
  const [showReportIssue, setShowReportIssue] = useState(false);
  const [showAddDevice, setShowAddDevice] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [showRequestDevice, setShowRequestDevice] = useState(false);
  const [showMyOrders, setShowMyOrders] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date>(new Date());
  const [selectedTimeRange, setSelectedTimeRange] = useState('7days');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const [deviceToRemove, setDeviceToRemove] = useState<any>(null);
  const [isRemovingDevice, setIsRemovingDevice] = useState(false);
  const [showProfileIncompleteModal, setShowProfileIncompleteModal] = useState(false);
  const [missingProfileFields, setMissingProfileFields] = useState<string[]>([]);
  
  // Report Issue form state
  const [issueType, setIssueType] = useState<'bug' | 'iot'>('bug');
  const [issueTitle, setIssueTitle] = useState('');
  const [issueDescription, setIssueDescription] = useState('');
  const [issuePriority, setIssuePriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [selectedDevice, setSelectedDevice] = useState('');
  const [isSubmittingIssue, setIsSubmittingIssue] = useState(false);
  const [issueSubmitted, setIssueSubmitted] = useState(false);

  // ✅ Fetch dashboard data with caching via custom hook
  const { data: dashboardData, isLoading, error, refetch } = useDashboardData('consumer');
  
  // ✅ Real-time updates with WebSocket
  const { latestUpdate, isConnected } = useRealTimeUpdates('consumer-updates', {
    autoConnect: true
  });

  // ✅ Get devices list from dashboard data
  const devices = useMemo(() => {
    console.log('🔍 [ConsumerDashboard] dashboardData:', dashboardData);
    console.log('🔍 [ConsumerDashboard] has devices key?', dashboardData && 'devices' in dashboardData);
    if (dashboardData && 'devices' in dashboardData) {
      console.log('📦 [ConsumerDashboard] devices:', dashboardData.devices);
      console.log('📊 [ConsumerDashboard] device count:', dashboardData.devices?.length || 0);
      return dashboardData.devices || [];
    }
    console.log('⚠️ [ConsumerDashboard] No devices found in dashboardData');
    return [];
  }, [dashboardData]);

  // ✅ Get current active device data
  const currentDevice = useMemo(() => {
    return devices.find((d: any) => d.device_id === selectedDeviceId) || devices[0] || null;
  }, [devices, selectedDeviceId]);

  // ✅ Auto-select first device when devices load
  useEffect(() => {
    if (devices.length > 0 && !selectedDeviceId) {
      setSelectedDeviceId(devices[0].device_id);
    }
  }, [devices, selectedDeviceId]);

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

  const toggleFullReport = useCallback(() => {
    setShowFullReport(prev => !prev);
  }, []);

  const toggleReportIssue = useCallback(() => {
    setShowReportIssue(prev => !prev);
    // Reset form when closing
    if (showReportIssue) {
      setIssueType('bug');
      setIssueTitle('');
      setIssueDescription('');
      setIssuePriority('medium');
      setSelectedDevice('');
      setIssueSubmitted(false);
    }
  }, [showReportIssue]);

  const toggleAddDevice = useCallback(() => {
    setShowAddDevice(prev => !prev);
  }, []);

  const handleDeviceAdded = useCallback(() => {
    // Refresh dashboard data after device is added
    refetch();
  }, [refetch]);

  // Check if user profile is complete
  const isProfileComplete = useMemo(() => {
    const address = user?.profile?.address;
    const hasAddress = address && 
      (typeof address === 'string' ? (address as string).trim().length > 0 : 
       !!(address as any)?.street && !!(address as any)?.city);
    const phone = user?.profile?.phone;
    const hasPhone = phone && typeof phone === 'string' && (phone as string).trim().length > 0;
    return !!(hasAddress && hasPhone);
  }, [user]);

  const toggleRequestDevice = useCallback(() => {
    if (!isProfileComplete) {
      // Show modal for incomplete profile
      const address = user?.profile?.address;
      const hasAddress = address && 
        (typeof address === 'string' ? (address as string).trim().length > 0 : 
         !!(address as any)?.street && !!(address as any)?.city);
      const phone = user?.profile?.phone;
      const hasPhone = phone && typeof phone === 'string' && (phone as string).trim().length > 0;
      
      const missing: string[] = [];
      if (!hasAddress) missing.push('Address');
      if (!hasPhone) missing.push('Phone Number');
      
      setMissingProfileFields(missing);
      setShowProfileIncompleteModal(true);
      return;
    }

    setShowRequestDevice(prev => !prev);
  }, [user, isProfileComplete]);

  const handleDeviceRequested = useCallback(() => {
    // Refresh dashboard data after device request
    refetch();
  }, [refetch]);

  const toggleMyOrders = useCallback(() => {
    setShowMyOrders(prev => !prev);
  }, []);

  const toggleEditProfile = useCallback(() => {
    console.log('Toggle Edit Profile clicked, current state:', showEditProfile);
    setShowEditProfile(prev => {
      console.log('Setting showEditProfile from', prev, 'to', !prev);
      return !prev;
    });
  }, [showEditProfile]);

  const handleProfileUpdated = useCallback(async () => {
    // Refresh user data after profile update
    console.log('Profile updated successfully');
    await refreshUser();
    setShowEditProfile(false);
  }, [refreshUser]);

  const handleRemoveDeviceClick = useCallback((device: any) => {
    setDeviceToRemove(device);
    setShowRemoveConfirm(true);
  }, []);

  const handleConfirmRemoveDevice = useCallback(async () => {
    if (!deviceToRemove) return;

    setIsRemovingDevice(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/devices/${deviceToRemove.device_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        console.log(`✅ Device removed: ${deviceToRemove.device_id}`);
        // Refresh dashboard data
        await refetch();
        // Reset selected device if it was the removed one
        if (selectedDeviceId === deviceToRemove.device_id) {
          setSelectedDeviceId(null);
        }
        setShowRemoveConfirm(false);
        setDeviceToRemove(null);
      } else {
        const error = await response.json();
        alert(`Failed to remove device: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error removing device:', error);
      alert('Failed to remove device. Please try again.');
    } finally {
      setIsRemovingDevice(false);
    }
  }, [deviceToRemove, refetch, selectedDeviceId]);

  const handleCancelRemoveDevice = useCallback(() => {
    setShowRemoveConfirm(false);
    setDeviceToRemove(null);
  }, []);

  const handleSubmitIssue = useCallback(async () => {
    if (!issueTitle.trim() || !issueDescription.trim()) {
      alert('Please fill in all required fields');
      return;
    }

    if (issueType === 'iot' && !selectedDevice) {
      alert('Please select a device for IoT issues');
      return;
    }

    setIsSubmittingIssue(true);

    try {
      // Prepare issue data
      const issueData = {
        type: issueType,
        title: issueTitle,
        description: issueDescription,
        priority: issuePriority,
        deviceId: issueType === 'iot' ? selectedDevice : null
      };

      // Call API to submit issue
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch('http://localhost:3002/api/issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(issueData)
      });

      if (!response.ok) {
        throw new Error('Failed to submit issue');
      }

      const result = await response.json();
      console.log('Issue submitted successfully:', result);
      
      // Show success message
      setIssueSubmitted(true);
      
      // Reset form after 3 seconds and close modal
      setTimeout(() => {
        toggleReportIssue();
      }, 3000);

    } catch (error) {
      console.error('Error submitting issue:', error);
      alert('Failed to submit issue. Please try again.');
    } finally {
      setIsSubmittingIssue(false);
    }
  }, [issueType, issueTitle, issueDescription, issuePriority, selectedDevice, user, toggleReportIssue]);

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
    if (!currentReading) return { wqi: 0, status: 'No Data', color: 'gray', metrics: {} };
    
    // Calculate WQI from sensor readings
    const { pH, turbidity, tds, temperature } = currentReading;
    
    // Individual parameter scores (0-100 scale)
    const pHScore = pH >= 6.5 && pH <= 8.5 ? 100 : Math.max(0, 100 - Math.abs(7.0 - pH) * 20);
    const turbidityScore = Math.max(0, 100 - (turbidity * 20));
    const tdsScore = Math.max(0, 100 - (tds / 5));
    const tempScore = temperature >= 15 && temperature <= 25 ? 100 : Math.max(0, 100 - Math.abs(20 - temperature) * 5);
    
    const wqi = Math.round((pHScore + turbidityScore + tdsScore + tempScore) / 4);
    
    // Determine status and color based on WQI scale (0-300)
    let status = 'Poor';
    let color = 'red';
    let bgColor = 'bg-red-100';
    
    if (wqi >= 201) { status = 'Good'; color = 'green'; bgColor = 'bg-green-100'; }
    else if (wqi >= 101) { status = 'Fair'; color = 'yellow'; bgColor = 'bg-yellow-100'; }
    else if (wqi >= 51) { status = 'Moderate'; color = 'orange'; bgColor = 'bg-orange-100'; }
    else { status = 'Poor'; color = 'red'; bgColor = 'bg-red-100'; }
    
    return {
      wqi,
      status,
      color,
      bgColor,
      metrics: {
        pH: { value: pH, min: 6.5, max: 8.5, unit: '', icon: Beaker, status: pH >= 6.5 && pH <= 8.5 ? 'safe' : 'warning' },
        turbidity: { value: turbidity, min: 0, max: 5, unit: 'NTU', icon: Eye, status: turbidity < 5 ? 'safe' : 'warning' },
        tds: { value: tds, min: 0, max: 500, unit: 'ppm', icon: Droplet, status: tds < 500 ? 'safe' : 'warning' },
        temperature: { value: temperature, min: 10, max: 30, unit: '°C', icon: Thermometer, status: temperature >= 15 && temperature <= 25 ? 'safe' : 'warning' }
      }
    };
  }, [currentReading]);

  // ✅ Helper functions for parameter status
  const getParamColor = (status: string) => {
    if (status === 'safe') return 'border-green-500 bg-green-50';
    if (status === 'warning') return 'border-yellow-500 bg-yellow-50';
    return 'border-red-500 bg-red-50';
  };

  // ✅ Memoized historical data for chart
  const historicalData = useMemo(() => {
    // In real app, this would come from API based on selectedTimeRange
    // For now, generate sample data or use empty array
    if (!currentReading) return [];
    
    const days = selectedTimeRange === '7days' ? 7 : selectedTimeRange === '30days' ? 30 : 90;
    const data = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      data.push({
        date: i === 0 ? 'Today' : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        wqi: waterQualityMetrics.wqi + Math.floor(Math.random() * 10 - 5) // Simulate variation
      });
    }
    
    return data;
  }, [currentReading, waterQualityMetrics.wqi, selectedTimeRange]);

  // ✅ Calculate average WQI from historical data
  const averageWQI = useMemo(() => {
    if (historicalData.length === 0) return 0;
    const sum = historicalData.reduce((acc, item) => acc + item.wqi, 0);
    return Math.round(sum / historicalData.length);
  }, [historicalData]);

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

  // My Orders view
  if (showMyOrders) {
    return <MyOrdersPage onBack={toggleMyOrders} />;
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
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
                <button
                  onClick={toggleEditProfile}
                  className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200 font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <span>Edit Profile</span>
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <p className="text-gray-900">{user.profile?.firstName || 'Not set'} {user.profile?.lastName || ''}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <p className="text-gray-900">{user.profile?.phone || 'Not set'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <p className="text-gray-900 capitalize">{user.role}</p>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                  <p className="text-gray-900">
                    {(() => {
                      const addr = user.profile?.address;
                      if (!addr) return 'Not set';
                      
                      // If it's a string, return it directly
                      if (typeof addr === 'string') return addr;
                      
                      // If it's an object, check for formatted field first
                      const addrObj = addr as any;
                      if (addrObj.formatted && typeof addrObj.formatted === 'string') {
                        // Clean up the formatted string to remove "undefined"
                        const cleaned = addrObj.formatted
                          .split(',')
                          .map((part: string) => part.trim())
                          .filter((part: string) => part && part !== 'undefined')
                          .join(', ');
                        if (cleaned) return cleaned;
                      }
                      
                      // Otherwise build from individual fields
                      const parts = [
                        addrObj.flatHouse,
                        addrObj.areaStreet,
                        addrObj.landmark,
                        addrObj.city,
                        addrObj.state,
                        addrObj.pincode,
                        addrObj.country
                      ].filter((part: any) => part && typeof part === 'string' && part.trim() && part !== 'undefined');
                      
                      return parts.length > 0 ? parts.join(', ') : 'Not set';
                    })()}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Member Since</label>
                  <p className="text-gray-900">
                    {new Date().toLocaleDateString('en-GB', { 
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
              <div className="grid grid-cols-1 gap-4">
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
              </div>
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>Need data exports?</strong> Your assigned technician can download and provide water quality data reports for you.
                </p>
              </div>
            </div>
          </motion.div>
        </main>

        {/* Edit Profile Modal */}
        <EditProfileModal
          isOpen={showEditProfile}
          onClose={toggleEditProfile}
          currentProfile={{
            firstName: user.profile?.firstName,
            lastName: user.profile?.lastName,
            email: user.email,
            phone: user.profile?.phone,
            address: user.profile?.address || ''
          }}
          onProfileUpdated={handleProfileUpdated}
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
            {/* My Orders Button */}
            <button
              onClick={toggleMyOrders}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors duration-200"
              title="My Orders"
            >
              <Package className="w-5 h-5" />
              <span className="text-sm font-medium">My Orders</span>
            </button>

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

      {/* Device Selector Tabs */}
      {devices.length > 0 && (
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                My Devices ({devices.length})
              </h3>
              <button
                onClick={toggleAddDevice}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Device
              </button>
            </div>
            
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {devices.map((device: any) => {
                const isSelected = device.device_id === selectedDeviceId;
                const isOnline = device.status === 'active' || device.status === 'online';
                
                return (
                  <div
                    key={device.device_id}
                    className={`
                      flex-shrink-0 rounded-lg border-2 transition-all min-w-[200px] relative
                      ${isSelected 
                        ? 'border-cyan-500 bg-cyan-50 shadow-md' 
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                      }
                    `}
                  >
                    <button
                      onClick={() => setSelectedDeviceId(device.device_id)}
                      className="w-full px-4 py-3 text-left"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`
                          w-10 h-10 rounded-full flex items-center justify-center
                          ${isOnline ? 'bg-green-100' : 'bg-gray-100'}
                        `}>
                          <Activity className={`w-5 h-5 ${isOnline ? 'text-green-600' : 'text-gray-400'}`} />
                        </div>
                        <div className="text-left flex-1">
                          <div className={`font-semibold text-sm ${isSelected ? 'text-cyan-900' : 'text-gray-900'}`}>
                            {device.name || device.device_id}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`
                              inline-block w-2 h-2 rounded-full
                              ${isOnline ? 'bg-green-500' : 'bg-gray-400'}
                            `} />
                            <span className="text-xs text-gray-600">
                              {isOnline ? 'Online' : 'Offline'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveDeviceClick(device);
                      }}
                      className="absolute top-2 right-2 p-1.5 rounded-full bg-red-100 hover:bg-red-200 text-red-600 transition-colors"
                      title="Remove device"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Device Header */}
      {currentDevice && (
        <div className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{currentDevice.name || currentDevice.device_id}</h2>
                <p className="text-cyan-100 mt-1 flex items-center gap-2">
                  <span>📍</span>
                  <span>{currentDevice.location || 'Location not set'}</span>
                </p>
              </div>
              <div className="text-right">
                <div className={`
                  inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
                  ${currentDevice.status === 'active' || currentDevice.status === 'online'
                    ? 'bg-green-500 bg-opacity-20 border border-green-300'
                    : 'bg-gray-500 bg-opacity-20 border border-gray-300'
                  }
                `}>
                  <span className={`w-2 h-2 rounded-full ${
                    currentDevice.status === 'active' || currentDevice.status === 'online'
                      ? 'bg-green-300'
                      : 'bg-gray-300'
                  }`} />
                  {currentDevice.status === 'active' || currentDevice.status === 'online' ? 'Online' : 'Offline'}
                </div>
                <p className="text-xs text-cyan-200 mt-2">
                  Last updated: {new Date().toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {devices.length === 0 && !isLoading && (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-md px-4">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Activity className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              No Devices Yet
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by adding your first water quality monitoring device to track your water parameters in real-time.
            </p>
            <button
              onClick={toggleAddDevice}
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              Add Your First Device
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      {devices.length > 0 && (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* WQI Hero Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 text-center">Water Quality Index</h2>
          <div className="flex flex-col items-center">
            <div className={`relative w-48 h-48 ${waterQualityMetrics.bgColor} rounded-full flex items-center justify-center mb-4`}>
              <div className="text-center">
                <div className={`text-6xl font-bold text-${waterQualityMetrics.color}-600`}>
                  {waterQualityMetrics.wqi}
                </div>
                <div className={`text-lg font-medium text-${waterQualityMetrics.color}-600`}>
                  {waterQualityMetrics.status}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-8 text-sm text-gray-600">
              <div className="text-center">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-red-500 rounded"></div>
                  <span>Poor (0-50)</span>
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-orange-500 rounded"></div>
                  <span>Moderate (51-100)</span>
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                  <span>Fair (101-200)</span>
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-green-500 rounded"></div>
                  <span>Good (201-300)</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Last updated: {lastRefreshTime.toLocaleString('en-GB', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
              })}
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Devices</h3>
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">Active</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {dashboardData && 'devices' in dashboardData ? dashboardData.devices?.length || 0 : 0}
            </div>
            {(!dashboardData || !('devices' in dashboardData) || dashboardData.devices?.length === 0) && (
              <button 
                onClick={toggleAddDevice}
                className="mt-4 w-full flex items-center justify-center space-x-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
              >
                <Plus className="w-4 h-4" />
                <span>Add Your Device</span>
              </button>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Alerts</h3>
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">Today</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">{recentAlerts.length}</div>
            <p className="text-sm text-gray-500 mt-2">
              {recentAlerts.length === 0 ? 'All systems normal' : `${recentAlerts.length} active alerts`}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Water Quality Average</h3>
              <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded">7 Days</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">{averageWQI}</div>
            <p className="text-sm text-gray-500 mt-2">
              {averageWQI >= 75 ? 'Above average' : averageWQI >= 50 ? 'Average' : 'Below average'}
            </p>
          </div>
        </div>

        {/* Water Parameters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Water Parameters</h2>
          {currentReading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(waterQualityMetrics.metrics).map(([key, param]: [string, any]) => {
                const Icon = param.icon;
                return (
                  <div key={key} className={`border-2 rounded-lg p-4 ${getParamColor(param.status)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Icon className="w-5 h-5 text-gray-700" />
                        <h3 className="text-sm font-medium text-gray-700 capitalize">{key}</h3>
                      </div>
                      {param.status === 'safe' ? (
                        <CheckCircleIcon className="w-5 h-5 text-green-600" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      )}
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {param.value}{param.unit}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Safe range: {param.min}{param.unit} - {param.max}{param.unit}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Activity className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>No water quality data available</p>
              <p className="text-sm mt-1">Connect a device to start monitoring</p>
            </div>
          )}
        </div>

        {/* Historical Trend */}
        {historicalData.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Historical Trend</h2>
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
              </select>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="wqi" 
                  stroke="#06b6d4" 
                  strokeWidth={2} 
                  dot={{ fill: '#06b6d4' }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

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

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={toggleRequestDevice}
              className={`relative flex items-center space-x-3 p-4 border-2 rounded-lg transition ${
                isProfileComplete 
                  ? 'border-gray-200 hover:border-blue-500 hover:bg-blue-50' 
                  : 'border-amber-200 bg-amber-50 hover:border-amber-400'
              }`}
            >
              <Plus className={`w-6 h-6 ${isProfileComplete ? 'text-blue-600' : 'text-amber-600'}`} />
              <div className="flex flex-col items-start">
                <span className="font-medium text-gray-700">Request Device</span>
                {!isProfileComplete && (
                  <span className="text-xs text-amber-600 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Complete profile first
                  </span>
                )}
              </div>
            </button>
            <button 
              onClick={toggleReportIssue}
              className="flex items-center space-x-3 p-4 border-2 border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition"
            >
              <AlertTriangle className="w-6 h-6 text-cyan-600" />
              <span className="font-medium text-gray-700">Report Issue</span>
            </button>
            <button 
              onClick={toggleFullReport}
              className="flex items-center space-x-3 p-4 border-2 border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition"
            >
              <Activity className="w-6 h-6 text-cyan-600" />
              <span className="font-medium text-gray-700">View Full Report</span>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-4 text-center">
            💡 Need to download data? Contact your assigned technician for data exports.
          </p>
        </div>

        {/* Report Issue Modal */}
        {showReportIssue && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
            >
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-orange-500 to-red-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Report an Issue</h2>
                </div>
                <button
                  onClick={toggleReportIssue}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
                {issueSubmitted ? (
                  <div className="text-center py-12">
                    <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Issue Submitted Successfully!</h3>
                    <p className="text-gray-600 mb-4">
                      Your {issueType === 'bug' ? 'bug report' : 'IoT issue'} has been submitted to our team.
                    </p>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left max-w-md mx-auto">
                      <p className="text-sm text-blue-900 mb-2">
                        <strong>What happens next?</strong>
                      </p>
                      {issueType === 'bug' ? (
                        <ul className="text-sm text-blue-800 space-y-1">
                          <li>• Admin will review your bug report</li>
                          <li>• If acknowledged, it will be sent to developers</li>
                          <li>• You'll be notified of any updates</li>
                        </ul>
                      ) : (
                        <ul className="text-sm text-blue-800 space-y-1">
                          <li>• Admin will review your IoT issue</li>
                          <li>• Upon approval, nearest technician will be assigned</li>
                          <li>• Technician will contact you shortly</li>
                        </ul>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-gray-600 mb-6">
                      Help us improve by reporting bugs or IoT device issues. Your report will be reviewed by our admin team.
                    </p>

                    {/* Issue Type Selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-3">
                        Issue Type <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          onClick={() => setIssueType('bug')}
                          className={`p-4 border-2 rounded-lg transition ${
                            issueType === 'bug'
                              ? 'border-orange-500 bg-orange-50'
                              : 'border-gray-200 hover:border-orange-300'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-lg ${issueType === 'bug' ? 'bg-orange-100' : 'bg-gray-100'}`}>
                              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                              </svg>
                            </div>
                            <div className="text-left">
                              <div className="font-semibold text-gray-900">Software Bug</div>
                              <div className="text-xs text-gray-600">Report app issues</div>
                            </div>
                          </div>
                        </button>

                        <button
                          onClick={() => setIssueType('iot')}
                          className={`p-4 border-2 rounded-lg transition ${
                            issueType === 'iot'
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-blue-300'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-lg ${issueType === 'iot' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                              <Activity className="w-6 h-6 text-blue-600" />
                            </div>
                            <div className="text-left">
                              <div className="font-semibold text-gray-900">IoT Device</div>
                              <div className="text-xs text-gray-600">Device problems</div>
                            </div>
                          </div>
                        </button>
                      </div>
                    </div>

                    {/* Device Selection (only for IoT issues) */}
                    {issueType === 'iot' && (
                      <div className="mb-6">
                        <label className="block text-sm font-semibold text-gray-900 mb-2">
                          Select Device <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={selectedDevice}
                          onChange={(e) => setSelectedDevice(e.target.value)}
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Choose a device...</option>
                          {dashboardData && 'devices' in dashboardData && dashboardData.devices?.map((device: any, index: number) => (
                            <option key={index} value={device.id || `device-${index}`}>
                              {device.name || `Device ${index + 1}`} - {device.location || 'Unknown Location'}
                            </option>
                          ))}
                          {(!dashboardData || !('devices' in dashboardData) || dashboardData.devices?.length === 0) && (
                            <option value="no-device">No devices available</option>
                          )}
                        </select>
                      </div>
                    )}

                    {/* Priority Level */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        Priority Level <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-4 gap-2">
                        {(['low', 'medium', 'high', 'critical'] as const).map((priority) => (
                          <button
                            key={priority}
                            onClick={() => setIssuePriority(priority)}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                              issuePriority === priority
                                ? priority === 'critical' ? 'bg-red-500 text-white' :
                                  priority === 'high' ? 'bg-orange-500 text-white' :
                                  priority === 'medium' ? 'bg-yellow-500 text-white' :
                                  'bg-green-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {priority.charAt(0).toUpperCase() + priority.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Issue Title */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        Issue Title <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={issueTitle}
                        onChange={(e) => setIssueTitle(e.target.value)}
                        placeholder="Brief description of the issue"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                        maxLength={100}
                      />
                      <p className="text-xs text-gray-500 mt-1">{issueTitle.length}/100 characters</p>
                    </div>

                    {/* Issue Description */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        Detailed Description <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        value={issueDescription}
                        onChange={(e) => setIssueDescription(e.target.value)}
                        placeholder={issueType === 'bug' 
                          ? "Describe the bug, steps to reproduce, and expected behavior..."
                          : "Describe the device issue, when it started, and any error messages..."
                        }
                        rows={6}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none"
                        maxLength={1000}
                      />
                      <p className="text-xs text-gray-500 mt-1">{issueDescription.length}/1000 characters</p>
                    </div>

                    {/* Info Box */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-blue-900">
                          <p className="font-semibold mb-1">Review Process:</p>
                          {issueType === 'bug' ? (
                            <p>Your bug report will be reviewed by an admin. If acknowledged, it will be forwarded to our development team for resolution.</p>
                          ) : (
                            <p>Your IoT issue will be reviewed by an admin. Upon approval, the nearest available technician will be automatically assigned to resolve the issue.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Modal Footer */}
              {!issueSubmitted && (
                <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
                  <button
                    onClick={toggleReportIssue}
                    disabled={isSubmittingIssue}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmitIssue}
                    disabled={isSubmittingIssue || !issueTitle.trim() || !issueDescription.trim()}
                    className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isSubmittingIssue ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-4 h-4" />
                        <span>Submit Issue</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Full Report Modal */}
        {showFullReport && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
            >
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Activity className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Comprehensive Water Quality Report</h2>
                </div>
                <button
                  onClick={toggleFullReport}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6">
                {/* Report Header */}
                <div className="mb-6 pb-4 border-b">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Water Quality Report</h3>
                      <p className="text-sm text-gray-600">{new Date().toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Need a copy?</p>
                      <p className="text-xs text-gray-500">Contact your technician for data exports</p>
                    </div>
                  </div>
                </div>

                {/* Overall Summary */}
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Overall Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                      <div className="text-sm text-blue-700 font-medium mb-1">Current WQI</div>
                      <div className="text-3xl font-bold text-blue-900">{waterQualityMetrics.wqi}</div>
                      <div className="text-xs text-blue-600 mt-1">{waterQualityMetrics.status}</div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                      <div className="text-sm text-purple-700 font-medium mb-1">7-Day Average</div>
                      <div className="text-3xl font-bold text-purple-900">{averageWQI}</div>
                      <div className="text-xs text-purple-600 mt-1">Water Quality Index</div>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                      <div className="text-sm text-green-700 font-medium mb-1">Active Devices</div>
                      <div className="text-3xl font-bold text-green-900">
                        {dashboardData && 'devices' in dashboardData ? dashboardData.devices?.length || 0 : 0}
                      </div>
                      <div className="text-xs text-green-600 mt-1">Monitoring</div>
                    </div>
                    <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4">
                      <div className="text-sm text-amber-700 font-medium mb-1">Active Alerts</div>
                      <div className="text-3xl font-bold text-amber-900">{recentAlerts.length}</div>
                      <div className="text-xs text-amber-600 mt-1">Requires Attention</div>
                    </div>
                  </div>
                </div>

                {/* Detailed Parameters */}
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Detailed Water Parameters</h3>
                  {currentReading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(waterQualityMetrics.metrics).map(([key, param]: [string, any]) => {
                        const Icon = param.icon;
                        return (
                          <div key={key} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center space-x-2">
                                <Icon className="w-5 h-5 text-gray-700" />
                                <h4 className="text-sm font-semibold text-gray-900 capitalize">{key}</h4>
                              </div>
                              {param.status === 'safe' ? (
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">Safe</span>
                              ) : (
                                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded">Warning</span>
                              )}
                            </div>
                            <div className="flex items-baseline space-x-2 mb-2">
                              <span className="text-3xl font-bold text-gray-900">{param.value}</span>
                              <span className="text-lg text-gray-600">{param.unit}</span>
                            </div>
                            <div className="text-xs text-gray-600">
                              Safe Range: {param.min}{param.unit} - {param.max}{param.unit}
                            </div>
                            <div className="mt-2 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${param.status === 'safe' ? 'bg-green-500' : 'bg-yellow-500'}`}
                                style={{
                                  width: `${Math.min(100, (param.value / param.max) * 100)}%`
                                }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <p>No parameter data available</p>
                    </div>
                  )}
                </div>

                {/* Historical Trend */}
                {historicalData.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">7-Day Trend Analysis</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={historicalData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Line 
                            type="monotone" 
                            dataKey="wqi" 
                            stroke="#06b6d4" 
                            strokeWidth={3} 
                            dot={{ fill: '#06b6d4', r: 4 }} 
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Alerts Section */}
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Alerts & Notifications</h3>
                  {recentAlerts.length > 0 ? (
                    <div className="space-y-2">
                      {recentAlerts.map((alert, index) => (
                        <div key={index} className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <p className="text-sm font-medium text-amber-900">{alert.message || 'Water quality alert'}</p>
                              <p className="text-xs text-amber-700 mt-1">
                                {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-green-50 border-l-4 border-green-500 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <CheckCircleIcon className="w-6 h-6 text-green-600" />
                        <p className="text-sm font-medium text-green-900">No active alerts - All systems operating normally</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Recommendations */}
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Recommendations</h3>
                  <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
                    <ul className="space-y-2 text-sm text-blue-900">
                      {waterQualityMetrics.wqi >= 75 ? (
                        <>
                          <li className="flex items-start space-x-2">
                            <CheckCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Your water quality is excellent. Continue regular monitoring.</span>
                          </li>
                          <li className="flex items-start space-x-2">
                            <CheckCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Maintain current water treatment practices.</span>
                          </li>
                        </>
                      ) : waterQualityMetrics.wqi >= 50 ? (
                        <>
                          <li className="flex items-start space-x-2">
                            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Water quality is acceptable but could be improved.</span>
                          </li>
                          <li className="flex items-start space-x-2">
                            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Consider checking filtration systems.</span>
                          </li>
                        </>
                      ) : (
                        <>
                          <li className="flex items-start space-x-2">
                            <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Water quality requires attention. Contact support for assistance.</span>
                          </li>
                          <li className="flex items-start space-x-2">
                            <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <span>Review and address any active alerts immediately.</span>
                          </li>
                        </>
                      )}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
                <p className="text-sm text-gray-600">
                  Report generated for {user?.email || 'Consumer'}
                </p>
                <button
                  onClick={toggleFullReport}
                  className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Add Device Modal */}
        <AddDeviceModal
          isOpen={showAddDevice}
          onClose={toggleAddDevice}
          onDeviceAdded={handleDeviceAdded}
        />

        {/* Request Device Modal */}
        <RequestDeviceModal
          isOpen={showRequestDevice}
          onClose={toggleRequestDevice}
          onSuccess={handleDeviceRequested}
        />

        {/* Edit Profile Modal */}
        <EditProfileModal
          isOpen={showEditProfile}
          onClose={toggleEditProfile}
          currentProfile={{
            firstName: user.profile?.firstName,
            lastName: user.profile?.lastName,
            email: user.email,
            phone: user.profile?.phone,
            address: user.profile?.address || ''
          }}
          onProfileUpdated={handleProfileUpdated}
        />

        {/* Remove Device Confirmation Dialog */}
        <AnimatePresence>
          {showRemoveConfirm && deviceToRemove && (
            <>
              <div 
                className="fixed inset-0 bg-black bg-opacity-50 z-50"
                onClick={handleCancelRemoveDevice}
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                      <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">Remove Device</h3>
                      <p className="text-sm text-gray-600">This action cannot be undone</p>
                    </div>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <p className="text-sm text-red-800 mb-2">
                      <strong>Warning:</strong> You are about to remove the following device:
                    </p>
                    <div className="bg-white rounded-lg p-3 mt-2">
                      <p className="font-semibold text-gray-900">{deviceToRemove.name || deviceToRemove.device_id}</p>
                      <p className="text-sm text-gray-600">ID: {deviceToRemove.device_id}</p>
                      {deviceToRemove.location && (
                        <p className="text-sm text-gray-600">Location: {deviceToRemove.location}</p>
                      )}
                    </div>
                    <p className="text-sm text-red-800 mt-3">
                      All historical data and settings for this device will be permanently deleted.
                    </p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleCancelRemoveDevice}
                      disabled={isRemovingDevice}
                      className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmRemoveDevice}
                      disabled={isRemovingDevice}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isRemovingDevice ? 'Removing...' : 'Remove Device'}
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Profile Incomplete Modal */}
        <AnimatePresence>
          {showProfileIncompleteModal && (
            <>
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowProfileIncompleteModal(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
              >
                <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
                  {/* Header */}
                  <div className="bg-gradient-to-r from-amber-500 to-orange-600 px-6 py-4 flex items-center justify-between rounded-t-xl">
                    <div className="flex items-center gap-3">
                      <User className="w-6 h-6 text-white" />
                      <h2 className="text-xl font-bold text-white">Complete Your Profile</h2>
                    </div>
                    <button
                      onClick={() => setShowProfileIncompleteModal(false)}
                      className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-start gap-3 mb-6">
                      <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <AlertTriangle className="w-6 h-6 text-amber-600" />
                      </div>
                      <div>
                        <p className="text-gray-900 font-medium mb-2">
                          Please complete your profile before requesting a device.
                        </p>
                        <p className="text-sm text-gray-600 mb-3">
                          We need the following information to process your device request:
                        </p>
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                          <p className="text-sm font-semibold text-amber-900 mb-2">Missing Information:</p>
                          <ul className="space-y-1">
                            {missingProfileFields.map((field, index) => (
                              <li key={index} className="flex items-center gap-2 text-sm text-amber-800">
                                <span className="w-1.5 h-1.5 bg-amber-600 rounded-full"></span>
                                {field}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowProfileIncompleteModal(false)}
                        className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => {
                          setShowProfileIncompleteModal(false);
                          setShowSettings(true);
                          setShowEditProfile(true);
                        }}
                        className="flex-1 px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium"
                      >
                        Update Profile
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </main>
      )}
    </div>
  );
});

// ✅ Display name for debugging
ConsumerDashboard.displayName = 'ConsumerDashboard';

export default ConsumerDashboard;

