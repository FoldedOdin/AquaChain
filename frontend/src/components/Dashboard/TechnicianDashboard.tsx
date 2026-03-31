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
  Navigation,
  Calendar, 
  User, 
  Filter, 
  Search, 
  TrendingUp, 
  ClipboardList, 
  BarChart3 
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';
import { technicianService } from '../../services/technicianService';
import { getShipmentByOrderId } from '../../services/shipmentService';
import { ShipmentStatusResponse } from '../../types/shipment';

// Import dashboard components
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';
import EditProfileModal from './EditProfileModal';
// MapModal disabled - AWS Location Service not configured
import InventoryModal from './InventoryModal';

interface TechnicianDashboardProps {
  // Optional props for customization
}

const TechnicianDashboard: React.FC<TechnicianDashboardProps> = memo(() => {
  const navigate = useNavigate();
  const { user, logout, refreshUser, getAuthToken } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  // showMapModal disabled - AWS Location Service not configured
  const [showInventoryModal, setShowInventoryModal] = useState(false);
  const [showTaskDetails, setShowTaskDetails] = useState(false);
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const TASKS_PER_PAGE = 10;
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState<string | null>(null);
  const [declineReason, setDeclineReason] = useState('');
  const [errorModal, setErrorModal] = useState<{ show: boolean; message: string }>({ show: false, message: '' });
  const [successModal, setSuccessModal] = useState<{ show: boolean; message: string; orderId?: string }>({ show: false, message: '' });
  const [shipmentStatuses, setShipmentStatuses] = useState<Record<string, ShipmentStatusResponse>>({});

  const [techOrders, setTechOrders] = useState<any[]>([]);
  const [techOrdersLoading, setTechOrdersLoading] = useState(true);
  const [techOrdersError, setTechOrdersError] = useState<string | null>(null);

  // Completion modal state (replaces browser prompt())
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [completeTaskTarget, setCompleteTaskTarget] = useState<{ orderId: string; task: any } | null>(null);
  const [completeLocation, setCompleteLocation] = useState('');
  const [completeWorkNotes, setCompleteWorkNotes] = useState('');
  // Photo upload state for completion modal
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoViewUrls, setPhotoViewUrls] = useState<string[]>([]); // S3 view URLs after upload
  const [photoUploading, setPhotoUploading] = useState(false);

  // Update-note modal state (replaces browser prompt())
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateTaskTarget, setUpdateTaskTarget] = useState<string | null>(null);
  const [updateNote, setUpdateNote] = useState('');

  const fetchTechnicianOrders = useCallback(async () => {
    try {
      setTechOrdersLoading(true);
      // Use getAuthToken() so expired tokens are refreshed automatically
      let token = await getAuthToken();
      if (!token) throw new Error('Not authenticated');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const isLocalDev = apiBase.includes('localhost');

      // Local dev server uses /api/technician/orders
      // Production uses /api/v1/technician/orders (queries orders table by assignedTechnicianId)
      const endpoint = isLocalDev ? `${apiBase}/api/technician/orders` : `${apiBase}/api/v1/technician/orders`;

      let response = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // If 401, the stored token may be stale — force-refresh once and retry
      if (response.status === 401) {
        console.warn('⚠️ Got 401, forcing token refresh and retrying...');
        const { fetchAuthSession } = await import('aws-amplify/auth');
        try {
          const session = await fetchAuthSession({ forceRefresh: true });
          const freshToken = session.tokens?.idToken?.toString();
          if (freshToken) {
            localStorage.setItem('aquachain_token', freshToken);
            token = freshToken;
            response = await fetch(endpoint, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
          }
        } catch (refreshErr) {
          console.error('Token refresh failed, redirecting to login:', refreshErr);
          // Clear stale session and redirect to login
          localStorage.removeItem('aquachain_token');
          localStorage.removeItem('aquachain_user');
          navigate('/');
          return;
        }
      }

      if (!response.ok) {
        if (response.status === 401) {
          // Still 401 after refresh — session is invalid, force re-login
          console.error('Still 401 after token refresh — clearing session');
          localStorage.removeItem('aquachain_token');
          localStorage.removeItem('aquachain_user');
          navigate('/');
          return;
        }
        throw new Error(`Failed to fetch orders: ${response.status}`);
      }

      const data = await response.json();
      // Dev server returns { orders: [] }, prod returns { tasks: [] }
      setTechOrders(data.orders || data.tasks || []);
      setTechOrdersError(null);
    } catch (err) {
      console.error('Error fetching technician orders:', err);
      setTechOrdersError(err instanceof Error ? err.message : 'Failed to load orders');
    } finally {
      setTechOrdersLoading(false);
    }
  }, [getAuthToken, navigate]);

  useEffect(() => {
    fetchTechnicianOrders();
  }, [fetchTechnicianOrders]);

  // Fallback poll every 2 minutes — WebSocket handles real-time updates;
  // this only catches cases where the WS connection is down for an extended period
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTechnicianOrders();
    }, 120000);
    return () => clearInterval(interval);
  }, [fetchTechnicianOrders]);

  const isLoading = techOrdersLoading;
  const error = techOrdersError ? new Error(techOrdersError) : null;
  const refetch = useCallback(() => { fetchTechnicianOrders(); }, [fetchTechnicianOrders]);

  // Delay WebSocket connection to avoid Firefox aborting the handshake mid-navigation.
  // wsReady gates the connection until after the initial render settles (1500ms),
  // then polls every 500ms until the access token is available in localStorage.
  const [wsReady, setWsReady] = useState(false);
  const [hasAccessToken, setHasAccessToken] = useState(false);
  useEffect(() => {
    const delayTimer = setTimeout(() => {
      if (localStorage.getItem('aquachain_access_token')) {
        setHasAccessToken(true);
        setWsReady(true);
      } else {
        setWsReady(true);
        const interval = setInterval(() => {
          if (localStorage.getItem('aquachain_access_token')) {
            setHasAccessToken(true);
            clearInterval(interval);
          }
        }, 500);
        return () => clearInterval(interval);
      }
    }, 1500);
    return () => clearTimeout(delayTimer);
  }, []);
  const { isConnected, latestUpdate } = useRealTimeUpdates('technician-updates', { autoConnect: wsReady && hasAccessToken });

  // Listen for shipment delivery notifications
  useEffect(() => {
    if (!latestUpdate) return;
    
    // Check if this is a shipment delivery update
    if (latestUpdate.type === 'shipment_delivered' && latestUpdate.data) {
      const { order_id, destination } = latestUpdate.data;
      
      // Check if this order is assigned to this technician
      const assignedTask = techOrders.find((task: any) => task.orderId === order_id);
      
      if (assignedTask) {
        // Show success notification with order ID for "View Details" button
        setSuccessModal({
          show: true,
          message: `Device delivered to ${destination?.contact_name || 'customer'}! You can now accept and start the installation task. Address: ${destination?.address || 'See task details'}`,
          orderId: order_id
        });
        
        // Refresh shipment statuses (only in local dev — shipments API not deployed to prod)
        const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
        if (apiBase.includes('localhost')) {
          getShipmentByOrderId(order_id).then(shipmentData => {
            setShipmentStatuses(prev => ({
              ...prev,
              [order_id]: shipmentData
            }));
          }).catch(() => {});
        }
      }
    }
  }, [latestUpdate, techOrders]);

  // Refresh user profile on mount to ensure firstName/lastName are up to date
  useEffect(() => {
    refreshUser();
  }, []); // eslint-disable-line

  // Fetch shipment statuses for all tasks
  // Only attempt if the shipments API is available (endpoint may not be deployed yet)
  useEffect(() => {
    const fetchShipmentStatuses = async () => {
      if (!techOrders.length) return;

      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      // Skip shipment fetch if running against production API where shipments aren't deployed
      // The UI gracefully shows "No Shipment Info" when statuses are empty
      const isLocalDev = apiBase.includes('localhost');
      if (!isLocalDev) return;

      const statuses: Record<string, ShipmentStatusResponse> = {};
      for (const task of techOrders) {
        try {
          const shipmentData = await getShipmentByOrderId(task.orderId);
          statuses[task.orderId] = shipmentData;
        } catch {
          // Shipment not found for this order — expected when not yet created
        }
      }
      setShipmentStatuses(statuses);
    };

    fetchShipmentStatuses();
  }, [techOrders]);

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
    // Add a small delay to ensure DynamoDB consistency
    await new Promise(resolve => setTimeout(resolve, 500));
    await refreshUser();
    setShowEditProfile(false);
  }, [refreshUser]);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'assigned': return 'bg-blue-100 text-blue-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'accepted': return 'bg-indigo-100 text-indigo-800';
      case 'en_route': return 'bg-purple-100 text-purple-800';
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

  const getDeliveryStatusBadge = (orderId: string) => {
    const shipment = shipmentStatuses[orderId];
    
    if (!shipment || !shipment.shipment) {
      return (
        <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
          <span>📦</span>
          <span>No Shipment Info</span>
        </div>
      );
    }
    
    const status = shipment.shipment.internal_status;
    
    if (status === 'delivered') {
      return (
        <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
          <span>✅</span>
          <span>Ready to Install</span>
        </div>
      );
    }
    
    return (
      <div className="flex items-center space-x-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
        <span>⏳</span>
        <span>Awaiting Delivery</span>
      </div>
    );
  };

  const isDeliveryConfirmed = (orderId: string): boolean => {
    // Check shipment API status (local dev only)
    const shipment = shipmentStatuses[orderId];
    if (shipment?.shipment?.internal_status === 'delivered') return true;
    // Fallback: check the order's own raw status — device is at customer's location for any of these
    const task = techOrders.find((t: any) => t.orderId === orderId);
    const s = (task?.status || '').toUpperCase();
    return ['DELIVERED', 'SHIPPED', 'OUT_FOR_DELIVERY', 'TECHNICIAN_ASSIGNED', 'ASSIGNED'].includes(s);
  };

  // Returns elapsed time string since a given ISO timestamp (e.g. "2h 15m")
  const getElapsedTime = (isoTimestamp: string | undefined): string | null => {
    if (!isoTimestamp) return null;
    try {
      const start = new Date(isoTimestamp).getTime();
      const now = Date.now();
      const diffMs = now - start;
      if (diffMs < 0) return null;
      const totalMinutes = Math.floor(diffMs / 60000);
      if (totalMinutes < 1) return 'Just now';
      if (totalMinutes < 60) return `${totalMinutes}m`;
      const hours = Math.floor(totalMinutes / 60);
      const mins = totalMinutes % 60;
      return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    } catch {
      return null;
    }
  };

  // Task action handlers
  const handleAcceptTask = useCallback(async (orderId: string) => {
    try {
      setIsProcessing(orderId);
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const response = await fetch(`${apiBase}/api/v1/technician/tasks/${orderId}/accept`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setErrorModal({ 
          show: true, 
          message: data.error || 'Failed to accept task. Please try again.' 
        });
        return;
      }
      
      setSuccessModal({ 
        show: true, 
        message: 'Task accepted successfully! You can now start working on it.' 
      });
      await refetch();
    } catch (error) {
      console.error('Error accepting task:', error);
      setErrorModal({ 
        show: true, 
        message: 'Failed to accept task. Please check your connection and try again.' 
      });
    } finally {
      setIsProcessing(null);
    }
  }, [refetch]);

  const handleDeclineTask = useCallback((task: any) => {
    setSelectedTask(task);
    setShowDeclineModal(true);
  }, []);

  const handleConfirmDecline = useCallback(async () => {
    if (!selectedTask || !declineReason.trim()) {
      alert('Please provide a reason for declining');
      return;
    }

    try {
      setIsProcessing(selectedTask.taskId);
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const response = await fetch(`${apiBase}/api/v1/technician/tasks/${selectedTask.taskId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'declined', note: declineReason })
      });
      
      if (!response.ok) throw new Error('Failed to decline task');
      
      setShowDeclineModal(false);
      setDeclineReason('');
      setSelectedTask(null);
      await refetch();
      setSuccessModal({ 
        show: true, 
        message: 'Task declined successfully. Admin has been notified.' 
      });
    } catch (error) {
      console.error('Error declining task:', error);
      setErrorModal({ 
        show: true, 
        message: 'Failed to decline task. Please try again.' 
      });
    } finally {
      setIsProcessing(null);
    }
  }, [selectedTask, declineReason, refetch]);

  const handleViewDetails = useCallback((task: any) => {
    setSelectedTask(task);
    setShowTaskDetails(true);
  }, []);

  const handleStartTask = useCallback(async (orderId: string) => {
    try {
      setIsProcessing(orderId);
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const response = await fetch(`${apiBase}/api/v1/technician/tasks/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'en_route' })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setErrorModal({ 
          show: true, 
          message: data.error || 'Failed to start navigation. Please try again.' 
        });
        return;
      }
      
      setSuccessModal({ 
        show: true, 
        message: 'Navigation started! Mark "Arrived" when you reach the customer.' 
      });
      await refetch();
    } catch (error) {
      console.error('Error starting navigation:', error);
      setErrorModal({ 
        show: true, 
        message: 'Failed to start navigation. Please check your connection and try again.' 
      });
    } finally {
      setIsProcessing(null);
    }
  }, [refetch]);

  const handleMarkArrived = useCallback(async (orderId: string) => {
    try {
      setIsProcessing(orderId);
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const response = await fetch(`${apiBase}/api/v1/technician/tasks/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'in_progress' })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setErrorModal({ 
          show: true, 
          message: data.error || 'Failed to mark arrived. Please try again.' 
        });
        return;
      }
      
      setSuccessModal({ 
        show: true, 
        message: 'Marked as on-site! Start the installation work.' 
      });
      await refetch();
    } catch (error) {
      console.error('Error marking arrived:', error);
      setErrorModal({ 
        show: true, 
        message: 'Failed to mark arrived. Please check your connection and try again.' 
      });
    } finally {
      setIsProcessing(null);
    }
  }, [refetch]);

  // Opens the completion modal instead of the browser prompt()
  const handleCompleteTask = useCallback((orderId: string, task: any) => {
    setCompleteTaskTarget({ orderId, task });
    setCompleteLocation('');
    setCompleteWorkNotes('');
    setPhotoFiles([]);
    setPhotoViewUrls([]);
    setShowCompleteModal(true);
  }, []);

  // Upload selected photos via Lambda (Lambda → S3), returns S3 keys (not presigned URLs)
  const uploadPhotos = useCallback(async (orderId: string, files: File[]): Promise<string[]> => {
    if (!files.length) return [];
    const token = await getAuthToken();
    if (!token) throw new Error('Not authenticated');
    const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
    const s3Keys: string[] = [];

    for (const file of files) {
      // Read file as base64
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve((reader.result as string).split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      // POST to Lambda which uploads to S3 and returns s3Key + viewUrl
      const res = await fetch(`${apiBase}/api/v1/technician/tasks/${orderId}/upload-url`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileName: file.name,
          contentType: file.type || 'image/jpeg',
          fileData: base64
        })
      });
      if (!res.ok) throw new Error(`Upload failed for ${file.name}`);
      const { s3Key } = await res.json();
      s3Keys.push(s3Key);
    }
    return s3Keys;
  }, [getAuthToken]);

  // Called when technician confirms location in the modal
  const handleConfirmComplete = useCallback(async () => {
    if (!completeTaskTarget || !completeLocation.trim() || !completeWorkNotes.trim()) return;
    const { orderId, task } = completeTaskTarget;
    try {
      setIsProcessing(orderId);
      setPhotoUploading(photoFiles.length > 0);
      setShowCompleteModal(false);

      // Upload photos first (if any) — returns S3 keys, not presigned URLs
      let uploadedPhotoS3Keys: string[] = [];
      if (photoFiles.length > 0) {
        uploadedPhotoS3Keys = await uploadPhotos(orderId, photoFiles);
      }
      setPhotoUploading(false);

      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiBase = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const response = await fetch(`${apiBase}/api/v1/technician/tasks/${orderId}/complete`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deviceId: task.deviceId || task.provisionedDeviceId,
          location: completeLocation.trim(),
          workNotes: completeWorkNotes.trim(),
          photoS3Keys: uploadedPhotoS3Keys,
          calibrationData: { phOffset: 0, tdsFactor: 1 }
        })
      });
      const data = await response.json();
      if (!response.ok) {
        setErrorModal({ show: true, message: data.error || 'Failed to complete installation. Please try again.' });
        return;
      }
      setSuccessModal({ show: true, message: 'Installation completed successfully! Great work!' });
      await refetch();
    } catch (error) {
      console.error('Error completing installation:', error);
      setPhotoUploading(false);
      setErrorModal({ show: true, message: 'Failed to complete installation. Please check your connection and try again.' });
    } finally {
      setIsProcessing(null);
      setCompleteTaskTarget(null);
    }
  }, [completeTaskTarget, completeLocation, completeWorkNotes, photoFiles, uploadPhotos, refetch]);

  // Opens the update-note modal instead of browser prompt()
  const handleUpdateTask = useCallback((taskId: string) => {
    setUpdateTaskTarget(taskId);
    setUpdateNote('');
    setShowUpdateModal(true);
  }, []);

  // Called when technician submits the note in the modal
  const handleConfirmUpdate = useCallback(async () => {
    if (!updateTaskTarget || !updateNote.trim()) return;
    try {
      setIsProcessing(updateTaskTarget);
      setShowUpdateModal(false);
      await technicianService.addTaskNote(updateTaskTarget, {
        author: user?.email || 'technician',
        type: 'technician_note',
        content: updateNote.trim(),
        attachments: []
      });
      await refetch();
      setSuccessModal({ show: true, message: 'Note added successfully.' });
    } catch (error) {
      console.error('Error updating task:', error);
      setErrorModal({ show: true, message: 'Failed to add note. Please try again.' });
    } finally {
      setIsProcessing(null);
      setUpdateTaskTarget(null);
    }
  }, [updateTaskTarget, updateNote, refetch, user]);

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
                    {(() => {
                      const addr = user.profile.address;
                      if (!addr) return '';
                      
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
                      
                      return parts.length > 0 ? parts.join(', ') : '';
                    })()}
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
            address: user.profile?.address || ''
          }}
          onProfileUpdated={handleProfileUpdated}
        />
      </div>
    );
  }

  // Main dashboard view - use real technician orders from API
  const tasks = techOrders;
  const recentActivities: any[] = [];
  
  // Map order statuses to task statuses for display
  const tasksWithMappedStatus = tasks.map((task: any) => {
    const rawStatus = (task.status || '').toUpperCase();
    let mappedStatus = task.status;
    // Normalize all status variants (backend uses uppercase, dev server may use mixed case)
    if (['SHIPPED', 'TECHNICIAN_ASSIGNED', 'ASSIGNED', 'OUT_FOR_DELIVERY', 'DELIVERED'].includes(rawStatus)) {
      mappedStatus = 'assigned'; // Device on the way or delivered — technician can accept
    }
    if (rawStatus === 'ACCEPTED') mappedStatus = 'accepted';
    if (rawStatus === 'EN_ROUTE') mappedStatus = 'en_route';
    if (['INSTALLING', 'IN_PROGRESS'].includes(rawStatus)) mappedStatus = 'in_progress';
    if (['COMPLETED', 'INSTALLED', 'DELIVERED_AND_INSTALLED'].includes(rawStatus)) mappedStatus = 'completed';

    // Resolve consumer name from multiple possible fields (do NOT fall back to email)
    const isEmail = (val: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
    const consumerName = 
      (task.consumerName && !isEmail(task.consumerName) ? task.consumerName : null) ||
      task.customerName ||
      task.name ||
      (task.contactInfo && typeof task.contactInfo === 'object' ? task.contactInfo.name : null) ||
      (task.contactInfo && typeof task.contactInfo === 'string' ? (() => { try { return JSON.parse(task.contactInfo).name; } catch { return null; } })() : null) ||
      'Customer';

    // Parse deliveryAddress — may be an object or a JSON string
    let deliveryAddr = task.deliveryAddress;
    if (typeof deliveryAddr === 'string') {
      try { deliveryAddr = JSON.parse(deliveryAddr); } catch { deliveryAddr = null; }
    }

    // Build a human-readable address string
    const formatAddress = (addr: any): string => {
      if (!addr || typeof addr !== 'object') return '';
      const parts = [
        addr.flatHouse || addr.flat,
        addr.street || addr.areaStreet,  // existing orders use 'street', new ones use 'areaStreet'
        addr.landmark,
        addr.city,
        addr.state,
        addr.pincode || addr.zip,
        addr.country !== 'India' ? addr.country : undefined,
      ].filter((p): p is string => Boolean(p && typeof p === 'string' && p.trim()));
      return parts.join(', ');
    };

    const address = task.address || formatAddress(deliveryAddr) || '';

    // Build a navigation-safe address (no landmark — landmarks confuse geocoders)
    const formatNavAddress = (addr: any): string => {
      if (!addr || typeof addr !== 'object') return '';
      const parts = [
        addr.flatHouse || addr.flat,
        addr.street || addr.areaStreet,  // existing orders use 'street', new ones use 'areaStreet'
        addr.city,
        addr.state,
        addr.pincode || addr.zip,
        'India',
      ].filter((p): p is string => Boolean(p && typeof p === 'string' && p.trim()));
      return parts.join(', ');
    };
    const navAddress = formatNavAddress(deliveryAddr) || address;

    // Extract phone from contactInfo (may be object or JSON string)
    let contactInfo = task.contactInfo;
    if (typeof contactInfo === 'string') {
      try { contactInfo = JSON.parse(contactInfo); } catch { contactInfo = null; }
    }
    const phone = task.phone || task.consumerPhone || (contactInfo && contactInfo.phone) || '';

    return {
      ...task,
      taskId: task.orderId,
      title: `Install ${task.deviceSKU || task.deviceType || 'Device'}`,
      description: `Install device for ${consumerName}`,
      location: address,
      address,
      navAddress,
      phone,
      consumer: consumerName,
      consumerName,
      deviceId: task.provisionedDeviceId || task.deviceId,
      dueDate: task.preferredSlot ? new Date(task.preferredSlot).toLocaleDateString() : null,
      priority: 'medium',
      mappedStatus
    };
  });

  // Calculate stats using mapped statuses (mappedStatus is the normalized field)
  const todayStr = new Date().toDateString();
  const stats = {
    total: tasksWithMappedStatus.length,
    completed: tasksWithMappedStatus.filter((t: any) => t.mappedStatus === 'completed').length,
    pending: tasksWithMappedStatus.filter((t: any) => t.mappedStatus === 'assigned').length,
    inProgress: tasksWithMappedStatus.filter((t: any) => t.mappedStatus === 'in_progress').length,
    accepted: tasksWithMappedStatus.filter((t: any) => t.mappedStatus === 'accepted').length,
    enRoute: tasksWithMappedStatus.filter((t: any) => t.mappedStatus === 'en_route').length,
    completedToday: tasksWithMappedStatus.filter((t: any) =>
      t.mappedStatus === 'completed' && t.completedAt && new Date(t.completedAt).toDateString() === todayStr
    ).length,
  };

  // Completion rate and SLA (tasks completed within due date).
  // slaTracked: how many completed tasks have *both* dueDate and completedAt set by the backend.
  // When the backend doesn't supply these fields (e.g. installation tasks), slaRate would
  // incorrectly show 0% even though all tasks are done. We show "N/A" in that case.
  const completionRate = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;
  const slaTracked = tasksWithMappedStatus.filter((t: any) =>
    t.mappedStatus === 'completed' && t.dueDate && t.completedAt
  ).length;
  const slaCompliant = tasksWithMappedStatus.filter((t: any) =>
    t.mappedStatus === 'completed' && t.dueDate && t.completedAt &&
    new Date(t.completedAt) <= new Date(t.dueDate)
  ).length;
  // Only compute a percentage when we have trackable tasks; otherwise null means "N/A"
  const slaRate: number | null = slaTracked > 0 ? Math.round((slaCompliant / slaTracked) * 100) : null;

  // Filter tasks using mapped tasks
  const filteredTasks = tasksWithMappedStatus.filter((task: any) => {
    const matchesStatus = filterStatus === 'all' || task.mappedStatus === filterStatus;
    const matchesPriority = filterPriority === 'all' || task.priority === filterPriority;
    const locationStr = typeof task.location === 'object' ? task.location?.address || '' : task.location || '';
    const matchesSearch = searchTerm === '' ||
      task.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      locationStr.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.deviceId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.consumerName?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesPriority && matchesSearch;
  });

  // Pagination
  const totalPages = Math.ceil(filteredTasks.length / TASKS_PER_PAGE);
  const paginatedTasks = filteredTasks.slice((currentPage - 1) * TASKS_PER_PAGE, currentPage * TASKS_PER_PAGE);

  // Navigate to task location using Google Maps (regular function, not a hook)
  const handleNavigateToTask = () => {
    const activeTask = tasksWithMappedStatus.find((t: any) =>
      t.status === 'shipped' ||
      t.status === 'TECHNICIAN_ASSIGNED' ||
      t.status === 'assigned' ||
      t.status === 'accepted' ||
      t.status === 'installing' ||
      t.status === 'in_progress'
    );

    if (activeTask) {
      // Prefer navAddress (landmark-free) for accurate geocoding, fall back to location string
      const destination = activeTask.navAddress || activeTask.address || activeTask.location;
      const addr = typeof destination === 'object' ? destination?.address : destination;

      if (addr) {
        const encodedAddress = encodeURIComponent(addr);
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodedAddress}`, '_blank');
      } else {
        alert('No address available for navigation');
      }
    } else {
      alert('No active tasks to navigate to');
    }
  };

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
              <button
                onClick={() => refetch()}
                className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                title="Refresh orders"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
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
        {/* Connection Status - Only show in production */}
        {!isConnected && process.env.NODE_ENV === 'production' && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.964-1.333-2.732 0L3.732 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm text-amber-800">Real-time updates disconnected.</span>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Tasks</h3>
              <ClipboardList className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
            <p className="text-xs text-gray-500 mt-1">All assigned</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Pending</h3>
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div className="text-3xl font-bold text-orange-700">{stats.pending}</div>
            <p className="text-xs text-gray-500 mt-1">Awaiting action</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Accepted</h3>
              <Settings className="w-5 h-5 text-indigo-600" />
            </div>
            <div className="text-3xl font-bold text-indigo-700">{stats.accepted}</div>
            <p className="text-xs text-gray-500 mt-1">Ready to go</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">En Route</h3>
              <Navigation className="w-5 h-5 text-purple-600" />
            </div>
            <div className="text-3xl font-bold text-purple-700">{stats.enRoute}</div>
            <p className="text-xs text-gray-500 mt-1">Travelling</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">In Progress</h3>
              <TrendingUp className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="text-3xl font-bold text-yellow-700">{stats.inProgress}</div>
            <p className="text-xs text-gray-500 mt-1">On site</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Completed</h3>
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-green-700">{stats.completed}</div>
            <p className="text-xs text-gray-500 mt-1">{stats.completedToday} today</p>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, device, location..."
                  value={searchTerm}
                  onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-500" />
                <select
                  value={filterStatus}
                  onChange={(e) => { setFilterStatus(e.target.value); setCurrentPage(1); }}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="assigned">Assigned</option>
                  <option value="accepted">Accepted</option>
                  <option value="en_route">En Route</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              <select
                value={filterPriority}
                onChange={(e) => { setFilterPriority(e.target.value); setCurrentPage(1); }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Priority</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <span className="text-sm text-gray-500">{filteredTasks.length} task{filteredTasks.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Assigned Tasks
                {isConnected && (
                  <span className="ml-2 inline-flex items-center gap-1 text-xs font-normal text-green-600">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    Live
                  </span>
                )}
              </h2>
              <div className="space-y-4">
                {paginatedTasks.length > 0 ? (
                  paginatedTasks.map((task: any, index: number) => (
                    <div key={task.id || index} className="border-2 border-gray-200 rounded-lg p-5 hover:border-blue-300 transition">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center flex-wrap gap-2 mb-2">
                            <h3 className="text-base font-semibold text-gray-900">{task.title || `Task ${index + 1}`}</h3>
                            {task.priority && (
                              <div className={`flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${getPriorityColor(task.priority)}`}>
                                {getPriorityIcon(task.priority)}
                                <span className="capitalize">{task.priority}</span>
                              </div>
                            )}
                          </div>

                          {/* Device + Status row */}
                          <div className="flex flex-wrap gap-2 mb-2">
                            {task.deviceId && (
                              <span className="inline-flex items-center gap-1 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                <Settings className="w-3 h-3" />
                                {task.deviceId}
                              </span>
                            )}
                            {/* Delivery Status Badge */}
                            {getDeliveryStatusBadge(task.orderId)}
                          </div>

                          <p className="text-sm text-gray-600 mb-3">{task.description || 'No description'}</p>

                          <div className="grid grid-cols-1 gap-2 text-sm">
                            {task.location && (
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-gray-600">
                                  <MapPin className="w-4 h-4 flex-shrink-0" />
                                  <span className="break-words">{task.address || (typeof task.location === 'object' ? task.location.address || 'Location' : task.location)}</span>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    const dest = task.navAddress || task.address || (typeof task.location === 'object' ? task.location.address : task.location);
                                    if (dest) window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(dest)}`, '_blank');
                                  }}
                                  className="flex items-center gap-1 px-2 py-1 text-xs text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition flex-shrink-0"
                                >
                                  <Navigation className="w-3 h-3" />
                                  Navigate
                                </button>
                              </div>
                            )}
                            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                              {task.consumer && (
                                <div className="flex items-center gap-1">
                                  <User className="w-3 h-3" />
                                  <span>{typeof task.consumer === 'object' ? task.consumer.name || 'Consumer' : task.consumer}</span>
                                </div>
                              )}
                              {task.phone && (
                                <div className="flex items-center gap-1">
                                  <span>📞</span>
                                  <span>{task.phone}</span>
                                </div>
                              )}
                              {task.dueDate && (
                                <div className="flex items-center gap-1">
                                  <Calendar className="w-3 h-3" />
                                  <span>Due: {task.dueDate}</span>
                                </div>
                              )}
                              {/* SLA elapsed time — show for active tasks */}
                              {task.mappedStatus !== 'completed' && task.mappedStatus !== 'assigned' && task.acceptedAt && (() => {
                                const elapsed = getElapsedTime(task.acceptedAt);
                                return elapsed ? (
                                  <div className="flex items-center gap-1 text-amber-600">
                                    <Clock className="w-3 h-3" />
                                    <span>Active: {elapsed}</span>
                                  </div>
                                ) : null;
                              })()}
                            </div>
                          </div>
                        </div>
                        <span className={`ml-3 px-3 py-1 text-xs font-medium rounded-full whitespace-nowrap ${getStatusColor(task.status?.toUpperCase() === 'DELIVERED' ? 'delivered' : task.mappedStatus || task.status || 'pending')}`}>
                          {task.status?.toUpperCase() === 'DELIVERED' ? 'DELIVERED' : (task.mappedStatus || task.status || 'pending').replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-200 flex-wrap">
                        {task.mappedStatus === 'assigned' && (
                          <>
                            <div className="flex-1 relative group">
                              <button
                                onClick={() => handleAcceptTask(task.taskId)}
                                disabled={isProcessing === task.taskId || !isDeliveryConfirmed(task.orderId)}
                                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                                title={!isDeliveryConfirmed(task.orderId) ? 'Device must be delivered before accepting task' : ''}
                              >
                                {isProcessing === task.taskId ? 'Processing...' : '✅ Accept Task'}
                              </button>
                              {!isDeliveryConfirmed(task.orderId) && (
                                <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-10">
                                  Device must be delivered before accepting
                                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
                                    <div className="border-4 border-transparent border-t-gray-900"></div>
                                  </div>
                                </div>
                              )}
                            </div>
                            <button
                              onClick={() => handleDeclineTask(task)}
                              disabled={isProcessing === task.taskId}
                              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium disabled:opacity-50 text-sm"
                            >
                              ❌ Decline
                            </button>
                          </>
                        )}
                        {task.mappedStatus === 'accepted' && (
                          <button
                            onClick={() => handleStartTask(task.taskId)}
                            disabled={isProcessing === task.taskId}
                            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium disabled:opacity-50 text-sm"
                          >
                            {isProcessing === task.taskId ? 'Processing...' : '🚗 Start Navigation'}
                          </button>
                        )}
                        {task.mappedStatus === 'en_route' && (
                          <button
                            onClick={() => handleMarkArrived(task.taskId)}
                            disabled={isProcessing === task.taskId}
                            className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium disabled:opacity-50 text-sm"
                          >
                            {isProcessing === task.taskId ? 'Processing...' : '📍 Mark Arrived'}
                          </button>
                        )}
                        {task.mappedStatus === 'in_progress' && (
                          <>
                            <button
                              onClick={() => handleCompleteTask(task.taskId, task)}
                              disabled={isProcessing === task.taskId}
                              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 text-sm"
                            >
                              {isProcessing === task.taskId ? 'Processing...' : '✔️ Complete'}
                            </button>
                            <button
                              onClick={() => handleUpdateTask(task.taskId)}
                              disabled={isProcessing === task.taskId}
                              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium disabled:opacity-50 text-sm"
                            >
                              Update
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleViewDetails(task)}
                          className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition font-medium text-sm"
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

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                  <span className="text-sm text-gray-600">
                    Page {currentPage} of {totalPages} ({filteredTasks.length} tasks)
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-40 hover:bg-gray-50"
                    >
                      ← Prev
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-40 hover:bg-gray-50"
                    >
                      Next →
                    </button>
                  </div>
                </div>
              )}
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
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-600">Completion Rate</span>
                    <span className="text-sm font-semibold text-gray-900">{completionRate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full transition-all" style={{ width: `${completionRate}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-600">SLA Compliance</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {slaRate === null ? <span className="text-gray-400 italic">N/A</span> : `${slaRate}%`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    {slaRate !== null ? (
                      <div
                        className={`h-2 rounded-full transition-all ${slaRate >= 90 ? 'bg-green-600' : slaRate >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${slaRate}%` }}
                      />
                    ) : (
                      <div className="h-2 rounded-full bg-gray-300" style={{ width: '100%' }} />
                    )}
                  </div>
                  {slaRate === null && (
                    <p className="text-xs text-gray-400 mt-1">SLA tracking data not yet available</p>
                  )}
                </div>
                <div className="pt-2 border-t border-gray-100 grid grid-cols-2 gap-3">
                  <div className="text-center bg-green-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-green-700">{stats.completedToday}</div>
                    <div className="text-xs text-gray-500 mt-1">Done Today</div>
                  </div>
                  <div className="text-center bg-blue-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-blue-700">{stats.completed}</div>
                    <div className="text-xs text-gray-500 mt-1">All Time</div>
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
                  onClick={handleNavigateToTask}
                  className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition"
                >
                  <Navigation className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-gray-700">Navigate to Task</span>
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
          address: user.profile?.address || ''
        }}
        onProfileUpdated={handleProfileUpdated}
      />

      {/* Map Modal */}
      {/* MapModal disabled - AWS Location Service not configured */}

      {/* Inventory Modal */}
      <InventoryModal
        isOpen={showInventoryModal}
        onClose={() => setShowInventoryModal(false)}
      />

      {/* Task Details Modal */}
      {showTaskDetails && selectedTask && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowTaskDetails(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ClipboardList className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Task Details</h2>
                </div>
                <button
                  onClick={() => setShowTaskDetails(false)}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
                {/* Order Information */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Information</h3>
                  <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Order ID</label>
                      <p className="text-gray-900">{selectedTask.orderId}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${
                        selectedTask.status === 'shipped' ? 'bg-yellow-100 text-yellow-800' :
                        selectedTask.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                        selectedTask.status === 'installing' ? 'bg-orange-100 text-orange-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {selectedTask.status?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Device Model</label>
                      <p className="text-gray-900">{selectedTask.deviceSKU || selectedTask.deviceType || selectedTask.productName || 'Not specified'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Device ID</label>
                      <p className="text-gray-900">{selectedTask.deviceId || selectedTask.provisionedDeviceId || selectedTask.iotDeviceId || 'Not assigned'}</p>
                    </div>
                  </div>
                </div>

                {/* Customer Information */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Customer Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                      <p className="text-gray-900">{selectedTask.consumerName}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <p className="text-gray-900">{selectedTask.consumerEmail}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <p className="text-gray-900">{selectedTask.phone || 'Not provided'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Installation Address</label>
                      <p className="text-gray-900">{selectedTask.address || selectedTask.location || 'Not provided'}</p>
                    </div>
                  </div>
                </div>

                {/* Installation Details */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Installation Details</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    {selectedTask.preferredSlot && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Date/Time</label>
                        <p className="text-gray-900">{new Date(selectedTask.preferredSlot).toLocaleString()}</p>
                      </div>
                    )}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                      <p className="text-gray-900">{selectedTask.paymentMethod || 'Not specified'}</p>
                    </div>
                    {selectedTask.quoteAmount && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Quote Amount</label>
                        <p className="text-gray-900 text-lg font-semibold">₹{selectedTask.quoteAmount.toLocaleString()}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Timeline */}
                {selectedTask.auditTrail && selectedTask.auditTrail.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h3>
                    <div className="space-y-3">
                      {selectedTask.auditTrail.map((entry: any, index: number) => (
                        <div key={index} className="flex items-start gap-3 bg-gray-50 rounded-lg p-3">
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{entry.action.replace(/_/g, ' ')}</p>
                            <p className="text-sm text-gray-600">{new Date(entry.at).toLocaleString()}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 border-t">
                <button
                  onClick={() => setShowTaskDetails(false)}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Close
                </button>
                {(selectedTask.status === 'shipped' || selectedTask.status === 'assigned' || selectedTask.mappedStatus === 'assigned' || selectedTask.status === 'delivered') && (
                  <button
                    onClick={() => {
                      setShowTaskDetails(false);
                      handleAcceptTask(selectedTask.taskId);
                    }}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Accept Task
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Complete Task Modal */}
      {showCompleteModal && completeTaskTarget && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowCompleteModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
              <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4 flex items-center justify-between rounded-t-xl">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-bold text-white">Complete Installation</h2>
                </div>
                <button
                  onClick={() => setShowCompleteModal(false)}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <p className="font-semibold text-gray-900">{completeTaskTarget.task?.title || 'Installation Task'}</p>
                  <p className="text-sm text-gray-600">Customer: {completeTaskTarget.task?.consumerName || '—'}</p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Installation Location <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={completeLocation}
                    onChange={e => setCompleteLocation(e.target.value)}
                    placeholder="e.g. Kitchen, under the sink"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    autoFocus
                  />
                  {!completeLocation.trim() && (
                    <p className="text-xs text-red-500 mt-1">Please enter the installation location to continue.</p>
                  )}
                </div>
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Work Performed <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={completeWorkNotes}
                    onChange={e => setCompleteWorkNotes(e.target.value)}
                    placeholder="Describe the work done, any issues encountered, parts used..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                  />
                  {!completeWorkNotes.trim() && (
                    <p className="text-xs text-red-500 mt-1">Please describe the work performed.</p>
                  )}
                </div>

                {/* Photo Upload */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Installation Photos <span className="text-gray-400 font-normal">(optional, max 5)</span>
                  </label>
                  <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-green-400 hover:bg-green-50 transition-colors">
                    <div className="flex items-center gap-2 text-gray-500">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm">Tap to add photos</span>
                    </div>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={e => {
                        const selected = Array.from(e.target.files || []).slice(0, 5);
                        setPhotoFiles(selected);
                      }}
                    />
                  </label>
                  {photoFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {photoFiles.map((f, i) => (
                        <div key={i} className="relative">
                          <img
                            src={URL.createObjectURL(f)}
                            alt={f.name}
                            className="w-16 h-16 object-cover rounded-lg border border-gray-200"
                          />
                          <button
                            onClick={() => setPhotoFiles(prev => prev.filter((_, idx) => idx !== i))}
                            className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center"
                          >×</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => { setShowCompleteModal(false); setCompleteLocation(''); setCompleteWorkNotes(''); setPhotoFiles([]); setPhotoViewUrls([]); }}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmComplete}
                    disabled={!completeLocation.trim() || !completeWorkNotes.trim() || isProcessing === completeTaskTarget.orderId || photoUploading}
                    className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {photoUploading ? 'Uploading photos…' : isProcessing === completeTaskTarget.orderId ? 'Completing…' : 'Confirm Complete'}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Decline Task Modal */}
      {showDeclineModal && selectedTask && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowDeclineModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
              {/* Header */}
              <div className="bg-gradient-to-r from-red-500 to-pink-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-bold text-white">Decline Task</h2>
                </div>
                <button
                  onClick={() => setShowDeclineModal(false)}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Content */}
              <div className="p-6">
                <div className="mb-4">
                  <p className="text-gray-700 mb-2">
                    You are about to decline the following task:
                  </p>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="font-semibold text-gray-900">{selectedTask.title}</p>
                    <p className="text-sm text-gray-600">Customer: {selectedTask.consumerName}</p>
                    <p className="text-sm text-gray-600">Location: {selectedTask.address}</p>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Reason for Declining <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={declineReason}
                    onChange={(e) => setDeclineReason(e.target.value)}
                    placeholder="Please provide a detailed reason..."
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
                    required
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    The admin will be notified and may reassign this task to another technician.
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowDeclineModal(false);
                      setDeclineReason('');
                    }}
                    disabled={isProcessing === selectedTask.taskId}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmDecline}
                    disabled={isProcessing === selectedTask.taskId || !declineReason.trim()}
                    className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isProcessing === selectedTask.taskId ? 'Declining...' : 'Confirm Decline'}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Error Modal */}
      {errorModal.show && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setErrorModal({ show: false, message: '' })} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
              <div className="bg-gradient-to-r from-red-500 to-red-600 px-6 py-4 flex items-center justify-between rounded-t-xl">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-bold text-white">Error</h2>
                </div>
                <button
                  onClick={() => setErrorModal({ show: false, message: '' })}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <p className="text-gray-700 text-center mb-6">{errorModal.message}</p>
                <button
                  onClick={() => setErrorModal({ show: false, message: '' })}
                  className="w-full px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                >
                  OK
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Success Modal */}
      {successModal.show && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setSuccessModal({ show: false, message: '' })} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
              <div className="bg-gradient-to-r from-green-500 to-green-600 px-6 py-4 flex items-center justify-between rounded-t-xl">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-bold text-white">Success</h2>
                </div>
                <button
                  onClick={() => setSuccessModal({ show: false, message: '' })}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <p className="text-gray-700 text-center mb-6">{successModal.message}</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setSuccessModal({ show: false, message: '' })}
                    className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                  >
                    OK
                  </button>
                  {successModal.orderId && (
                    <button
                      onClick={() => {
                        const tasks = techOrders;
                        const task = tasks.find((t: any) => t.orderId === successModal.orderId);
                        if (task) {
                          const mappedTask = {
                            ...task,
                            taskId: task.orderId,
                            title: `Install ${task.deviceSKU || 'Device'}`,
                            description: `Install device for ${task.consumerName}`,
                            location: task.address,
                            consumer: task.consumerName,
                            deviceId: task.provisionedDeviceId || task.deviceId,
                            dueDate: task.preferredSlot ? new Date(task.preferredSlot).toLocaleDateString() : null,
                            priority: 'medium'
                          };
                          setSelectedTask(mappedTask);
                          setShowTaskDetails(true);
                        }
                        setSuccessModal({ show: false, message: '' });
                      }}
                      className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      View Details
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
});

TechnicianDashboard.displayName = 'TechnicianDashboard';

export default TechnicianDashboard;

