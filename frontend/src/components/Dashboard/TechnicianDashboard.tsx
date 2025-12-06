import React, { useState, useEffect, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  PowerIcon
} from '@heroicons/react/24/outline';
import { 
  Settings, 
  Wrench, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  MapPin, 
  Calendar, 
  User, 
  Filter, 
  Search, 
  TrendingUp, 
  ClipboardList, 
  BarChart3 
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';
import { technicianService } from '../../services/technicianService';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';
import EditProfileModal from './EditProfileModal';
import MapModal from './MapModal';
import InventoryModal from './InventoryModal';

interface TechnicianDashboardProps {
  // Optional props for customization
}

const TechnicianDashboard: React.FC<TechnicianDashboardProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout, refreshUser } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [showMapModal, setShowMapModal] = useState(false);
  const [showInventoryModal, setShowInventoryModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState<string | null>(null);

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error, refetch } = useDashboardData('technician');
  const { isConnected } = useRealTimeUpdates('technician-updates', { autoConnect: true });

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
    // Close edit profile modal when leaving settings
    setShowEditProfile(false);
  }, []);

  const toggleExportModal = useCallback(() => {
    setShowExportModal(prev => !prev);
  }, []);

  const toggleEditProfile = useCallback(() => {
    setShowEditProfile(prev => !prev);
  }, []);

  const handleProfileUpdated = useCallback(async () => {
    console.log('Profile updated successfully');
    await refreshUser();
    setShowEditProfile(false);
  }, [refreshUser]);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'assigned': return 'bg-blue-100 text-blue-800';
      case 'accepted': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityIcon = (priority: string) => {
    if (priority === 'high') return <AlertTriangle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  // Task action handlers
  const handleAcceptTask = useCallback(async (taskId: string) => {
    try {
      setIsProcessing(taskId);
      await technicianService.updateTaskStatus(taskId, 'accepted', 'Task accepted by technician');
      await refetch();
    } catch (error) {
      console.error('Error accepting task:', error);
      alert('Failed to accept task. Please try again.');
    } finally {
      setIsProcessing(null);
    }
  }, [refetch]);

  const handleDeclineTask = useCallback(async (taskId: string) => {
    const reason = prompt('Please provide a reason for declining this task:');
    if (!reason) return;

    try {
      setIsProcessing(taskId);
      // Note: Backend needs to support cancellation status
      await technicianService.addTaskNote(taskId, {
        author: user?.email || 'technician',
        type: 'technician_note',
        content: `Task declined: ${reason}`,
        attachments: []
      });
      alert('Task decline note added. Please contact admin to reassign.');
      await refetch();
    } catch (error) {
      console.error('Error declining task:', error);
      alert('Failed to decline task. Please try again.');
    } finally {
      setIsProcessing(null);
    }
  }, [refetch, user]);

  const handleStartTask = useCallback(async (taskId: string) => {
    try {
      setIsProcessing(taskId);
      await technicianService.updateTaskStatus(taskId, 'in_progress', 'Task started');
      await refetch();
    } catch (error) {
      console.error('Error starting task:', error);
      alert('Failed to start task. Please try again.');
    } finally {
      setIsProcessing(null);
    }
  }, [refetch]);

  const handleCompleteTask = useCallback(async (taskId: string, task: any) => {
    const workPerformed = prompt('Please describe the work performed:');
    if (!workPerformed) return;

    try {
      setIsProcessing(taskId);
      await technicianService.completeTask(taskId, {
        taskId,
        deviceId: task.deviceId,
        technicianId: user?.userId || '',
        workPerformed,
        partsUsed: [],
        diagnosticData: {
          deviceStatus: 'operational' as const,
          sensorReadings: {
            pH: { value: 7.0, status: 'normal' as const },
            turbidity: { value: 1.0, status: 'normal' as const },
            tds: { value: 150, status: 'normal' as const },
            temperature: { value: 25, status: 'normal' as const },
            humidity: { value: 60, status: 'normal' as const }
          },
          batteryLevel: 100,
          signalStrength: -50,
          calibrationStatus: 'current' as const
        },
        beforePhotos: [],
        afterPhotos: [],
        recommendations: 'Device is functioning properly'
      });
      await refetch();
      alert('Task completed successfully!');
    } catch (error) {
      console.error('Error completing task:', error);
      alert('Failed to complete task. Please try again.');
    } finally {
      setIsProcessing(null);
    }
  }, [refetch, user]);

  const handleUpdateTask = useCallback(async (taskId: string) => {
    const note = prompt('Add a note about the task progress:');
    if (!note) return;

    try {
      setIsProcessing(taskId);
      await technicianService.addTaskNote(taskId, {
        author: user?.email || 'technician',
        type: 'technician_note',
        content: note,
        attachments: []
      });
      await refetch();
    } catch (error) {
      console.error('Error updating task:', error);
      alert('Failed to update task. Please try again.');
    } finally {
      setIsProcessing(null);
    }
  }, [refetch, user]);

  const handleViewDetails = useCallback((task: any) => {
    setSelectedTask(task);
    // You can implement a modal or navigate to a detail page
    alert(`Task Details:\n\nID: ${task.taskId}\nStatus: ${task.status}\nDescription: ${task.description}\n\nFull details view coming soon!`);
  }, []);

  const handleViewMap = useCallback(() => {
    setShowMapModal(true);
  }, []);

  const handleViewInventory = useCallback(() => {
    setShowInventoryModal(true);
  }, []);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

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
              <h1 className="text-xl font-bold text-gray-900">Settings</h1>
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
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
              <button
                onClick={toggleEditProfile}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
              >
                Edit Profile
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <p className="text-gray-900">{user.profile?.firstName || 'Not set'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <p className="text-gray-900">{user.profile?.lastName || 'Not set'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p className="text-gray-900">{user.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <p className="text-gray-900 capitalize">{user.role}</p>
              </div>
              {user.profile?.phone && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <p className="text-gray-900">{user.profile.phone}</p>
                </div>
              )}
              {user.profile?.address && (
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                  <p className="text-gray-900">
                    {typeof user.profile.address === 'object' 
                      ? `${user.profile.address.street}, ${user.profile.address.city}, ${user.profile.address.state} ${user.profile.address.zipCode}`
                      : user.profile.address}
                  </p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Additional Settings Sections */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Preferences</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Notifications</p>
                  <p className="text-sm text-gray-600">Receive task assignment notifications</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Email Updates</p>
                  <p className="text-sm text-gray-600">Receive daily task summary via email</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </motion.div>
        </main>

        {/* Edit Profile Modal */}
        <EditProfileModal
          isOpen={showEditProfile}
          onClose={toggleEditProfile}
          currentProfile={{
            firstName: user.profile?.firstName || '',
            lastName: user.profile?.lastName || '',
            email: user.email || '',
            phone: user.profile?.phone || '',
            address: typeof user.profile?.address === 'object' 
              ? `${user.profile.address.street}, ${user.profile.address.city}, ${user.profile.address.state} ${user.profile.address.zipCode}`
              : user.profile?.address || ''
          }}
          onProfileUpdated={handleProfileUpdated}
        />
      </div>
    );
  }

  // Main dashboard view
  const tasks = dashboardData && 'tasks' in dashboardData ? dashboardData.tasks : [];
  const recentActivities = (dashboardData && 'recentActivities' in dashboardData ? dashboardData.recentActivities : []) as any[];
  
  // Calculate stats
  const stats = {
    total: tasks.length,
    completed: tasks.filter((t: any) => t.status === 'completed').length,
    pending: tasks.filter((t: any) => t.status === 'assigned').length,
    inProgress: tasks.filter((t: any) => t.status === 'in_progress').length,
    accepted: tasks.filter((t: any) => t.status === 'accepted').length
  };

  // Filter tasks
  const filteredTasks = tasks.filter((task: any) => {
    const matchesFilter = filterStatus === 'all' || task.status === filterStatus;
    const locationStr = typeof task.location === 'object' ? task.location?.address || '' : task.location || '';
    const matchesSearch = searchTerm === '' || 
      task.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      locationStr.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <Wrench className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Technician Dashboard</h1>
                <p className="text-sm text-gray-600">Welcome back, {user.profile?.firstName || user.email}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-600">Technician</span>
              <NotificationCenter userRole="technician" />
              <button onClick={toggleSettings} className="p-2 text-gray-600 hover:text-blue-600">
                <User className="w-6 h-6" />
              </button>
              <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Connection Status */}
        {!isConnected && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.964-1.333-2.732 0L3.732 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm text-amber-800">Real-time updates disconnected.</span>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Tasks</h3>
              <ClipboardList className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
            <p className="text-xs text-gray-500 mt-1">All assigned tasks</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Completed</h3>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.completed}</div>
            <p className="text-xs text-gray-500 mt-1">This week</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Pending</h3>
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.pending}</div>
            <p className="text-xs text-gray-500 mt-1">Awaiting action</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">In Progress</h3>
              <TrendingUp className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.inProgress}</div>
            <p className="text-xs text-gray-500 mt-1">Active work</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Accepted</h3>
              <Settings className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.accepted}</div>
            <p className="text-xs text-gray-500 mt-1">Ready to start</p>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search tasks, locations, devices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-600" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Tasks</option>
                  <option value="assigned">Assigned</option>
                  <option value="accepted">Accepted</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Assigned Tasks</h2>
              <div className="space-y-4">
                {filteredTasks.length > 0 ? (
                  filteredTasks.map((task: any, index: number) => (
                    <div key={task.id || index} className="border-2 border-gray-200 rounded-lg p-5 hover:border-blue-300 transition">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">{task.title || `Task ${index + 1}`}</h3>
                            {task.priority && (
                              <div className={`flex items-center space-x-1 px-2 py-1 rounded border ${getPriorityColor(task.priority)}`}>
                                {getPriorityIcon(task.priority)}
                                <span className="text-xs font-medium capitalize">{task.priority}</span>
                              </div>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{task.description || 'No description'}</p>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            {task.location && (
                              <div className="flex items-center space-x-2 text-gray-600">
                                <MapPin className="w-4 h-4" />
                                <span>{typeof task.location === 'object' ? task.location.address || 'Location' : task.location}</span>
                              </div>
                            )}
                            {task.dueDate && (
                              <div className="flex items-center space-x-2 text-gray-600">
                                <Calendar className="w-4 h-4" />
                                <span>Due: {task.dueDate}</span>
                              </div>
                            )}
                            {task.deviceId && (
                              <div className="flex items-center space-x-2 text-gray-600">
                                <Settings className="w-4 h-4" />
                                <span>Device: {task.deviceId}</span>
                              </div>
                            )}
                            {task.consumer && (
                              <div className="flex items-center space-x-2 text-gray-600">
                                <User className="w-4 h-4" />
                                <span>{typeof task.consumer === 'object' ? task.consumer.name || 'Consumer' : task.consumer}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <span className={`px-3 py-1 text-xs font-medium rounded-full whitespace-nowrap ${getStatusColor(task.status || 'pending')}`}>
                          {(task.status || 'pending').replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3 mt-4 pt-4 border-t border-gray-200">
                        {task.status === 'assigned' && (
                          <>
                            <button 
                              onClick={() => handleAcceptTask(task.taskId)}
                              disabled={isProcessing === task.taskId}
                              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isProcessing === task.taskId ? 'Processing...' : 'Accept Task'}
                            </button>
                            <button 
                              onClick={() => handleDeclineTask(task.taskId)}
                              disabled={isProcessing === task.taskId}
                              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Decline
                            </button>
                          </>
                        )}
                        {task.status === 'accepted' && (
                          <button 
                            onClick={() => handleStartTask(task.taskId)}
                            disabled={isProcessing === task.taskId}
                            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isProcessing === task.taskId ? 'Processing...' : 'Start Task'}
                          </button>
                        )}
                        {task.status === 'in_progress' && (
                          <>
                            <button 
                              onClick={() => handleCompleteTask(task.taskId, task)}
                              disabled={isProcessing === task.taskId}
                              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isProcessing === task.taskId ? 'Processing...' : 'Mark Complete'}
                            </button>
                            <button 
                              onClick={() => handleUpdateTask(task.taskId)}
                              disabled={isProcessing === task.taskId}
                              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Update
                            </button>
                          </>
                        )}
                        <button 
                          onClick={() => handleViewDetails(task)}
                          className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition font-medium"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-600 text-center py-8">No tasks found</p>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Activity</h2>
              <div className="space-y-4">
                {recentActivities.length > 0 ? (
                  recentActivities.map((activity: any) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                        <p className="text-sm text-gray-600 truncate">{activity.task}</p>
                        <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-600">No recent activity</p>
                )}
              </div>
            </div>

            {/* Performance Stats */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Performance</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Completion Rate</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${stats.total > 0 ? (stats.completed / stats.total) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Tasks In Progress</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {stats.total > 0 ? Math.round((stats.inProgress / stats.total) * 100) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${stats.total > 0 ? (stats.inProgress / stats.total) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <button 
                  onClick={toggleExportModal}
                  className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
                >
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-gray-700">View Reports</span>
                </button>
                <button 
                  onClick={handleViewMap}
                  className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
                >
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-gray-700">View Map</span>
                </button>
                <button 
                  onClick={handleViewInventory}
                  className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
                >
                  <Settings className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-gray-700">Inventory</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Data Export Modal */}
        <DataExportModal
          isOpen={showExportModal}
          onClose={toggleExportModal}
          userRole="technician"
        />
      </main>

      {/* Edit Profile Modal */}
      <EditProfileModal
        isOpen={showEditProfile}
        onClose={toggleEditProfile}
        currentProfile={{
          firstName: user.profile?.firstName || '',
          lastName: user.profile?.lastName || '',
          email: user.email || '',
          phone: user.profile?.phone || '',
          address: typeof user.profile?.address === 'object' 
            ? `${user.profile.address.street}, ${user.profile.address.city}, ${user.profile.address.state} ${user.profile.address.zipCode}`
            : user.profile?.address || ''
        }}
        onProfileUpdated={handleProfileUpdated}
      />

      {/* Map Modal */}
      <MapModal
        isOpen={showMapModal}
        onClose={() => setShowMapModal(false)}
        tasks={tasks}
      />

      {/* Inventory Modal */}
      <InventoryModal
        isOpen={showInventoryModal}
        onClose={() => setShowInventoryModal(false)}
      />
    </div>
  );
});

TechnicianDashboard.displayName = 'TechnicianDashboard';

export default TechnicianDashboard;
