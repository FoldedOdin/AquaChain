import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Package, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Truck, 
  Wrench,
  IndianRupee,
  MapPin,
  Phone,
  Calendar,
  AlertCircle,
  ArrowLeft,
  Copy,
  Check,
  Lock,
  Loader2,
  HelpCircle,
  Info,
  X
} from 'lucide-react';
import Toast from '../Toast/Toast';
import ShipmentTracking from './ShipmentTracking';
import OrderProgressButtons from './OrderProgressButtons';

interface Order {
  orderId: string;
  deviceSKU: string;
  status: string;
  address: string;
  phone: string;
  paymentMethod: string;
  preferredSlot?: string;
  quoteAmount?: number;
  provisionedDeviceId?: string;
  assignedTechnicianName?: string;
  createdAt: string;
  updatedAt: string;
  statusHistory?: Array<{
    status: string;
    timestamp: string;
    message: string;
    metadata?: any;
  }>;
}

interface MyOrdersPageProps {
  onBack: () => void;
}

const MyOrdersPage: React.FC<MyOrdersPageProps> = ({ onBack }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'COD' | 'ONLINE'>('COD');
  const [isSubmittingPayment, setIsSubmittingPayment] = useState(false);
  const [copiedOrderId, setCopiedOrderId] = useState<string | null>(null);
  
  // Ref for auto-scrolling to current step
  const currentStepRef = useRef<HTMLDivElement>(null);
  
  // Bulk operations state
  const [selectedOrderIds, setSelectedOrderIds] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);
  
  // Filtering state
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCancelledOrders, setShowCancelledOrders] = useState(false); // Changed from true to false
  
  // Cancellation reason modal state
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelOrderId, setCancelOrderId] = useState<string | null>(null);
  const [cancellationReason, setCancellationReason] = useState('');
  const [otherReason, setOtherReason] = useState('');
  
  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info'; visible: boolean }>({
    message: '',
    type: 'info',
    visible: false
  });

  const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    setToast({ message, type, visible: true });
  };

  const hideToast = () => {
    setToast(prev => ({ ...prev, visible: false }));
  };

  // Helper functions for bulk operations
  const toggleOrderSelection = (orderId: string) => {
    setSelectedOrderIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(orderId)) {
        newSet.delete(orderId);
      } else {
        newSet.add(orderId);
      }
      return newSet;
    });
  };

  const selectAllCancellableOrders = () => {
    const cancellableOrders = filteredOrders.filter(order => order.status === 'ORDER_PLACED' || order.status === 'pending');
    setSelectedOrderIds(new Set(cancellableOrders.map(order => order.orderId)));
  };

  const clearSelection = () => {
    setSelectedOrderIds(new Set());
  };

  // Remove duplicates and filter orders based on status and visibility preferences
  const filteredOrders = useMemo(() => {
    // First, deduplicate orders using a Map for better performance
    const uniqueOrdersMap = new Map();
    
    orders.forEach(order => {
      const key = `${order.orderId}_${order.createdAt || ''}`;
      if (!uniqueOrdersMap.has(key)) {
        uniqueOrdersMap.set(key, order);
      }
    });
    
    const uniqueOrders = Array.from(uniqueOrdersMap.values());
    
    // Log duplicate count only in development
    if (process.env.NODE_ENV === 'development' && orders.length !== uniqueOrders.length) {
      console.info(`Removed ${orders.length - uniqueOrders.length} duplicate orders`);
    }
    
    // Then apply filters
    return uniqueOrders.filter(order => {
      // Filter out cancelled orders if checkbox is unchecked (handle both lowercase and uppercase)
      if (!showCancelledOrders && (order.status === 'cancelled' || order.status === 'CANCELLED')) {
        return false;
      }
      if (statusFilter === 'all') {
        return true;
      }
      return order.status === statusFilter;
    });
  }, [orders, showCancelledOrders, statusFilter]);

  // Get cancellable orders from selection
  const getCancellableSelectedOrders = () => {
    return Array.from(selectedOrderIds).filter(orderId => {
      const order = orders.find(o => o.orderId === orderId);
      return order && (order.status === 'ORDER_PLACED' || order.status === 'pending');
    });
  };

  // Fetch orders
  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
      
      // Extract consumer ID from stored user data or JWT token
      let consumerId = 'demo-consumer-123'; // Fallback
      
      // Try to get from stored user data first
      const storedUser = localStorage.getItem('aquachain_user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          consumerId = userData.userId || userData.sub || consumerId;
          console.log('✅ Using consumer ID from stored user:', consumerId);
        } catch (e) {
          console.warn('Failed to parse stored user data');
        }
      }
      
      // If still using fallback, try to extract from JWT token
      if (consumerId === 'demo-consumer-123' && token) {
        try {
          const tokenParts = token.split('.');
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            consumerId = payload.sub || payload['cognito:username'] || consumerId;
            console.log('✅ Using consumer ID from JWT token:', consumerId);
          }
        } catch (e) {
          console.warn('Failed to extract consumer ID from token');
        }
      }
      
      console.log(`🔍 Fetching orders for consumer: ${consumerId}`);
      
      // Use the correct endpoint with consumerId query parameter
      const response = await fetch(`${apiEndpoint}/api/orders?consumerId=${consumerId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // The enhanced API returns { success: true, data: [...], count: N }
        setOrders(data.data || data.orders || []);
        console.log(`✅ Fetched ${data.data?.length || data.orders?.length || 0} orders`);
      } else {
        console.error(`❌ Failed to fetch orders: ${response.status} ${response.statusText}`);
        if (response.status === 500) {
          showToast('Backend service error. Please contact support.', 'error');
        } else if (response.status === 403) {
          showToast('Access denied. Please check your permissions.', 'error');
        } else {
          showToast('Failed to load orders. Please try again.', 'error');
        }
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      showToast('Network error. Please check your connection.', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchOrders();
    
    // Set up real-time polling every 10 seconds
    const pollInterval = setInterval(() => {
      fetchOrders();
    }, 10000);
    
    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - fetchOrders is stable with useCallback

  // Get status info
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
      case 'ORDER_PLACED':
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Order Placed' };
      case 'provisioned':
        return { icon: Package, color: 'text-purple-600', bg: 'bg-purple-100', label: 'Device Provisioned' };
      case 'assigned':
        return { icon: Wrench, color: 'text-indigo-600', bg: 'bg-indigo-100', label: 'Technician Assigned' };
      case 'shipped':
      case 'SHIPPED':
        return { icon: Truck, color: 'text-cyan-600', bg: 'bg-cyan-100', label: 'Shipped' };
      case 'OUT_FOR_DELIVERY':
        return { icon: Truck, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Out for Delivery' };
      case 'installing':
        return { icon: Wrench, color: 'text-orange-600', bg: 'bg-orange-100', label: 'Installing' };
      case 'completed':
      case 'DELIVERED':
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' };
      case 'cancelled':
      case 'CANCELLED':
        return { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Cancelled' };
      default:
        return { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100', label: status };
    }
  };

  // Get device name
  const getDeviceName = (sku: string) => {
    if (sku === 'AC-HOME-V1') {
      return 'AquaChain Home V1';
    }
    return sku;
  };

  // Handle view details
  const handleViewDetails = (order: Order) => {
    setSelectedOrder(order);
    setShowDetailsModal(true);
  };

  // Handle choose payment method
  const handleChoosePayment = (order: Order) => {
    setSelectedOrder(order);
    setShowPaymentModal(true);
  };

  // Handle submit payment method
  const handleSubmitPaymentMethod = async () => {
    if (!selectedOrder) return;

    setIsSubmittingPayment(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/orders/${selectedOrder.orderId}/payment-method`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paymentMethod: selectedPaymentMethod })
      });

      if (response.ok) {
        showToast('Payment method selected successfully', 'success');
        fetchOrders();
        setShowPaymentModal(false);
      } else {
        const error = await response.json();
        showToast(error.error || 'Failed to update payment method', 'error');
      }
    } catch (error) {
      console.error('Error updating payment method:', error);
      showToast('Error updating payment method', 'error');
    } finally {
      setIsSubmittingPayment(false);
    }
  };

  // Handle cancel order - show modal first
  const handleCancelOrder = (orderId: string) => {
    setCancelOrderId(orderId);
    setCancellationReason('');
    setOtherReason('');
    setShowCancelModal(true);
  };

  // Confirm cancellation with reason
  const confirmCancellation = async () => {
    if (!cancelOrderId) return;
    
    // Validate reason
    const finalReason = cancellationReason === 'other' ? otherReason.trim() : cancellationReason;
    if (!finalReason) {
      showToast('Please select or enter a cancellation reason', 'error');
      return;
    }

    setIsCancelling(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
      const response = await fetch(`${apiEndpoint}/api/orders/${cancelOrderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cancellationReason: finalReason
        })
      });

      if (response.ok) {
        showToast('Order cancelled successfully', 'success');
        fetchOrders(); // Refresh the orders list
        setShowDetailsModal(false);
        setShowCancelModal(false);
        setCancelOrderId(null);
      } else {
        const error = await response.json();
        showToast(error.error || 'Failed to cancel order', 'error');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      showToast('Error cancelling order. Please try again.', 'error');
    } finally {
      setIsCancelling(false);
    }
  };

  // Handle bulk cancel orders (for multiple selection)
  const handleBulkCancelOrders = async (orderIds: string[]) => {
    if (!confirm(`Are you sure you want to cancel ${orderIds.length} orders? This action cannot be undone.`)) return;

    setIsCancelling(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
      const cancelPromises = orderIds.map(orderId =>
        fetch(`${apiEndpoint}/api/orders/${orderId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      );

      const results = await Promise.allSettled(cancelPromises);
      const successful = results.filter(result => result.status === 'fulfilled').length;
      const failed = results.length - successful;

      if (successful > 0) {
        showToast(`${successful} order(s) cancelled successfully${failed > 0 ? `, ${failed} failed` : ''}`, 
          failed > 0 ? 'warning' : 'success');
        fetchOrders(); // Refresh the orders list
      } else {
        showToast('Failed to cancel orders', 'error');
      }
    } catch (error) {
      console.error('Error cancelling orders:', error);
      showToast('Error cancelling orders. Please try again.', 'error');
    } finally {
      setIsCancelling(false);
    }
  };

  // Get timeline steps with descriptions
  const getTimelineSteps = (order: Order) => {
    const steps = [
      { 
        status: 'ORDER_PLACED', 
        label: 'Order Placed', 
        description: 'Payment confirmed',
        completed: true 
      },
      { 
        status: 'provisioned', 
        label: 'Device Ready', 
        description: 'Assembly & calibration (1–2 days)',
        completed: ['provisioned', 'assigned', 'shipped', 'SHIPPED', 'OUT_FOR_DELIVERY', 'installing', 'completed', 'DELIVERED'].includes(order.status) 
      },
      { 
        status: 'SHIPPED', 
        label: 'Shipped', 
        description: 'Device dispatched • Tracking ID will be shared',
        completed: ['shipped', 'SHIPPED', 'OUT_FOR_DELIVERY', 'installing', 'completed', 'DELIVERED'].includes(order.status) 
      },
      { 
        status: 'OUT_FOR_DELIVERY', 
        label: 'Out for Delivery', 
        description: 'Device is on the way to your location',
        completed: ['OUT_FOR_DELIVERY', 'installing', 'completed', 'DELIVERED'].includes(order.status) 
      },
      { 
        status: 'assigned', 
        label: 'Technician Assigned', 
        description: 'Dedicated technician assigned for support & maintenance',
        completed: ['assigned', 'installing', 'completed', 'DELIVERED'].includes(order.status) 
      },
      { 
        status: 'DELIVERED', 
        label: 'Installed', 
        description: 'Device installed and initial setup completed',
        completed: ['completed', 'DELIVERED'].includes(order.status) 
      },
    ];
    return steps;
  };

  // Get current step index
  const getCurrentStepIndex = (order: Order) => {
    const statusMap: { [key: string]: number } = {
      'pending': 0,
      'ORDER_PLACED': 0,
      'provisioned': 1,
      'shipped': 2,
      'SHIPPED': 2,
      'OUT_FOR_DELIVERY': 3,
      'assigned': 4,
      'installing': 4,
      'completed': 5,
      'DELIVERED': 5,
      'cancelled': -1,
      'CANCELLED': -1
    };
    return statusMap[order.status] ?? 0;
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
    
    if (isToday) {
      return `Today, ${timeStr}`;
    }
    
    const dateStr = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric'
    });
    
    return `${dateStr}, ${timeStr}`;
  };

  // Get next step message
  const getNextStepMessage = (order: Order) => {
    const currentIndex = getCurrentStepIndex(order);
    
    if (order.status === 'cancelled' || order.status === 'CANCELLED') {
      return 'This order has been cancelled. Contact support if you have questions.';
    }
    
    if (order.status === 'completed' || order.status === 'DELIVERED') {
      return 'Your device has been successfully installed and is now active. Enjoy monitoring your water quality!';
    }
    
    const messages: { [key: number]: string } = {
      0: 'Your order is being processed. The device will be provisioned and prepared for shipment. You\'ll receive an email notification once it\'s ready.',
      1: 'Device is ready! A technician will be assigned for installation. You\'ll be notified via email and SMS with their contact details.',
      2: 'Technician has been assigned. Your device will be shipped soon. Track your shipment for real-time updates.',
      3: 'Your device is on the way! The technician will contact you to schedule the installation. Please keep your phone handy.',
      4: 'Installation is in progress. The technician will calibrate the device and ensure everything works perfectly.'
    };
    
    return messages[currentIndex] || 'Your order is being processed. You\'ll receive updates at each step.';
  };

  // Copy order ID to clipboard
  const copyOrderId = (orderId: string) => {
    navigator.clipboard.writeText(orderId).then(() => {
      setCopiedOrderId(orderId);
      setTimeout(() => setCopiedOrderId(null), 2000);
    });
  };

  // Auto-scroll to current step when modal opens
  useEffect(() => {
    if (showDetailsModal && currentStepRef.current) {
      setTimeout(() => {
        currentStepRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 300);
    }
  }, [showDetailsModal]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading orders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <div className="flex items-center gap-3">
              <Package className="w-6 h-6 text-cyan-600" />
              <h1 className="text-xl font-bold text-gray-900">My Orders</h1>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters and Controls */}
        {orders.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                {/* Status Filter */}
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="all">All Orders</option>
                    <option value="ORDER_PLACED">Order Placed</option>
                    <option value="provisioned">Provisioned</option>
                    <option value="assigned">Assigned</option>
                    <option value="SHIPPED">Shipped</option>
                    <option value="OUT_FOR_DELIVERY">Out for Delivery</option>
                    <option value="installing">Installing</option>
                    <option value="DELIVERED">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                {/* Show/Hide Cancelled Orders */}
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showCancelledOrders}
                    onChange={(e) => setShowCancelledOrders(e.target.checked)}
                    className="rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
                  />
                  <span className="text-gray-700">Show cancelled orders</span>
                </label>
              </div>

              {/* Bulk Actions */}
              <div className="flex items-center gap-2">
                {selectedOrderIds.size > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">
                      {selectedOrderIds.size} selected
                    </span>
                    <button
                      onClick={() => {
                        const cancellableIds = getCancellableSelectedOrders();
                        if (cancellableIds.length > 0) {
                          handleBulkCancelOrders(cancellableIds);
                        } else {
                          showToast('No cancellable orders selected', 'warning');
                        }
                      }}
                      disabled={getCancellableSelectedOrders().length === 0 || isCancelling}
                      className="px-3 py-1 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isCancelling ? 'Cancelling...' : `Cancel Selected (${getCancellableSelectedOrders().length})`}
                    </button>
                    <button
                      onClick={clearSelection}
                      className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                )}
                <button
                  onClick={selectAllCancellableOrders}
                  className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Select All Cancellable
                </button>
              </div>
            </div>
          </div>
        )}

        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            {orders.length === 0 ? (
              <>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Orders Yet</h3>
                <p className="text-gray-600 mb-6">
                  You haven't placed any device orders yet. Request a device to get started!
                </p>
                <button
                  onClick={onBack}
                  className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                >
                  Go to Dashboard
                </button>
              </>
            ) : (
              <>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Orders Match Filter</h3>
                <p className="text-gray-600 mb-6">
                  No orders found for the selected status filter. Try adjusting your filters.
                </p>
                <button
                  onClick={() => {
                    setStatusFilter('all');
                    setShowCancelledOrders(true);
                  }}
                  className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                >
                  Show All Orders
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order, index) => {
              const statusInfo = getStatusInfo(order.status);
              const StatusIcon = statusInfo.icon;
              const isSelected = selectedOrderIds.has(order.orderId);
              const isCancellable = order.status === 'ORDER_PLACED' || order.status === 'pending';
              
              // Create unique key combining orderId, index, and timestamp to prevent duplicates
              const uniqueKey = `${order.orderId}_${index}_${order.createdAt || Date.now()}`;

              return (
                <motion.div
                  key={uniqueKey}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`bg-white rounded-lg shadow-sm border transition-all ${
                    isSelected ? 'border-cyan-300 bg-cyan-50' : 'border-gray-200 hover:shadow-md'
                  }`}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {/* Selection Checkbox */}
                        {isCancellable && (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleOrderSelection(order.orderId)}
                            className="mt-1 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
                          />
                        )}
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <div className={`p-2 rounded-lg ${statusInfo.bg}`}>
                              <StatusIcon className={`w-5 h-5 ${statusInfo.color}`} />
                            </div>
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">
                                {getDeviceName(order.deviceSKU)}
                              </h3>
                              <p className="text-sm text-gray-600">Order #{order.orderId.slice(0, 8)}</p>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Calendar className="w-4 h-4" />
                              <span>Placed: {new Date(order.createdAt).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <MapPin className="w-4 h-4" />
                              <span className="truncate">
                                {typeof order.address === 'string' && order.address 
                                  ? order.address.split(',')[0] 
                                  : 'Address not available'
                                }
                              </span>
                            </div>
                            {order.quoteAmount && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <IndianRupee className="w-4 h-4" />
                                <span>₹{order.quoteAmount.toLocaleString()}</span>
                              </div>
                            )}
                          </div>

                          {/* Status Badge */}
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${statusInfo.bg} ${statusInfo.color}`}>
                              <StatusIcon className="w-4 h-4" />
                              {statusInfo.label}
                            </span>
                            {order.assignedTechnicianName && (
                              <span className="text-sm text-gray-600">
                                Technician: {order.assignedTechnicianName}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => handleViewDetails(order)}
                          className="px-4 py-2 text-sm bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                        >
                          View Details
                        </button>
                        {order.status === 'quoted' && !order.paymentMethod && (
                          <button
                            onClick={() => handleChoosePayment(order)}
                            className="px-4 py-2 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
                          >
                            <IndianRupee className="w-4 h-4" />
                            Choose Payment
                          </button>
                        )}
                        {(order.status === 'ORDER_PLACED' || order.status === 'pending') && (
                          <button
                            onClick={() => handleCancelOrder(order.orderId)}
                            disabled={isCancelling}
                            className="px-4 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                          >
                            {isCancelling ? 'Cancelling...' : 'Cancel Order'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      <AnimatePresence>
        {showDetailsModal && selectedOrder && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowDetailsModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Package className="w-6 h-6 text-white" />
                    <h2 className="text-2xl font-bold text-white">Order Details</h2>
                  </div>
                  <button
                    onClick={() => setShowDetailsModal(false)}
                    className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>

                {/* Content */}
                <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
                  {/* Order Info */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Order ID</label>
                        <p className="text-gray-900">{selectedOrder.orderId}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Device Model</label>
                        <p className="text-gray-900">{getDeviceName(selectedOrder.deviceSKU)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Order Date</label>
                        <p className="text-gray-900">{new Date(selectedOrder.createdAt).toLocaleString()}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                        <p className="text-gray-900">{selectedOrder.paymentMethod}</p>
                      </div>
                      {selectedOrder.quoteAmount && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quote Amount</label>
                          <p className="text-gray-900 text-lg font-semibold">₹{selectedOrder.quoteAmount.toLocaleString()}</p>
                        </div>
                      )}
                      {selectedOrder.provisionedDeviceId && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Device ID</label>
                          <p className="text-gray-900">{selectedOrder.provisionedDeviceId}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Installation Details */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Installation Details</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                        <p className="text-gray-900">
                          {typeof selectedOrder.address === 'string' && selectedOrder.address 
                            ? selectedOrder.address 
                            : 'Address not available'
                          }
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
                        <p className="text-gray-900">{selectedOrder.phone}</p>
                      </div>
                      {selectedOrder.preferredSlot && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Slot</label>
                          <p className="text-gray-900">{new Date(selectedOrder.preferredSlot).toLocaleString()}</p>
                        </div>
                      )}
                      {selectedOrder.assignedTechnicianName && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Assigned Technician</label>
                          <p className="text-gray-900">{selectedOrder.assignedTechnicianName}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Shipment Tracking */}
                  <ShipmentTracking orderId={selectedOrder.orderId} orderStatus={selectedOrder.status} />

                  {/* Enhanced Order Timeline */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">Order Progress</h3>
                      {/* Copyable Order ID */}
                      <button
                        onClick={() => copyOrderId(selectedOrder.orderId)}
                        className="flex items-center gap-2 text-sm text-gray-600 hover:text-cyan-600 transition-colors group"
                        title="Copy Order ID"
                      >
                        <span className="font-mono text-xs">#{selectedOrder.orderId.slice(0, 12)}</span>
                        {copiedOrderId === selectedOrder.orderId ? (
                          <Check className="w-4 h-4 text-green-600" />
                        ) : (
                          <Copy className="w-4 h-4 group-hover:scale-110 transition-transform" />
                        )}
                      </button>
                    </div>
                    
                    <div className="relative">
                      {getTimelineSteps(selectedOrder).map((step, index) => {
                        const isLast = index === getTimelineSteps(selectedOrder).length - 1;
                        const currentStepIndex = getCurrentStepIndex(selectedOrder);
                        const isCurrent = index === currentStepIndex;
                        const isUpcoming = index > currentStepIndex;
                        const isCompleted = step.completed;
                        
                        // Determine icon and styling
                        let IconComponent = Clock;
                        let iconBgClass = 'bg-gray-200';
                        let iconColorClass = 'text-gray-400';
                        let lineClass = 'bg-gray-200';
                        let textClass = 'text-gray-400';
                        let iconSize = 'w-8 h-8';
                        
                        if (isCompleted && !isCurrent) {
                          IconComponent = CheckCircle;
                          iconBgClass = 'bg-green-500';
                          iconColorClass = 'text-white';
                          lineClass = 'bg-green-500';
                          textClass = 'text-gray-900';
                        } else if (isCurrent) {
                          IconComponent = Loader2;
                          iconBgClass = 'bg-cyan-500';
                          iconColorClass = 'text-white';
                          lineClass = 'bg-cyan-500';
                          textClass = 'text-gray-900';
                          iconSize = 'w-10 h-10'; // Bigger for current step
                        } else if (isUpcoming) {
                          IconComponent = Lock;
                          iconBgClass = 'bg-gray-100';
                          iconColorClass = 'text-gray-300';
                          lineClass = 'bg-gray-200';
                          textClass = 'text-gray-400';
                        }
                        
                        return (
                          <div 
                            key={step.status} 
                            className={`flex items-start mb-4 transition-all duration-300 ${
                              isCurrent ? 'scale-105' : 'scale-100'
                            }`}
                            ref={isCurrent ? currentStepRef : null}
                          >
                            <div className="flex flex-col items-center mr-4 relative">
                              {/* Icon with animation */}
                              <motion.div 
                                className={`${iconSize} rounded-full flex items-center justify-center ${iconBgClass} ${
                                  isCurrent ? 'ring-4 ring-cyan-100' : ''
                                } transition-all duration-300`}
                                animate={isCurrent ? { scale: [1, 1.1, 1] } : {}}
                                transition={{ repeat: Infinity, duration: 2 }}
                              >
                                <IconComponent 
                                  className={`${isCurrent ? 'w-6 h-6' : 'w-5 h-5'} ${iconColorClass} ${
                                    isCurrent ? 'animate-spin' : ''
                                  }`} 
                                />
                              </motion.div>
                              
                              {/* Animated connecting line */}
                              {!isLast && (
                                <motion.div 
                                  className={`w-0.5 h-12 ${lineClass} transition-all duration-500`}
                                  initial={{ scaleY: 0 }}
                                  animate={{ scaleY: isCompleted || isCurrent ? 1 : 0 }}
                                  style={{ transformOrigin: 'top' }}
                                />
                              )}
                            </div>
                            
                            {/* Step content */}
                            <div className={`flex-1 pt-1 ${
                              isCurrent ? 'bg-cyan-50 -ml-2 pl-2 pr-3 py-2 rounded-lg border border-cyan-100' : ''
                            } transition-all duration-300`}>
                              <div className="flex items-center gap-2 mb-1">
                                <p className={`font-semibold ${textClass} ${
                                  isCurrent ? 'text-lg' : 'text-base'
                                } transition-all`}>
                                  {step.label}
                                </p>
                                {isCurrent && (
                                  <motion.span 
                                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-cyan-500 text-white text-xs font-medium rounded-full"
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                  >
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    In Progress
                                  </motion.span>
                                )}
                                {isCompleted && !isCurrent && (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                )}
                              </div>
                              
                              {/* Step description */}
                              <p className={`text-sm ${
                                isCompleted || isCurrent ? 'text-gray-600' : 'text-gray-400'
                              } mb-1`}>
                                {step.description}
                              </p>
                              
                              {/* Timestamp for completed steps */}
                              {isCompleted && !isCurrent && selectedOrder.statusHistory && (
                                (() => {
                                  const historyEntry = selectedOrder.statusHistory.find(
                                    (h: any) => h.status === step.status || 
                                    (step.status === 'ORDER_PLACED' && (h.status === 'pending' || h.status === 'ORDER_PLACED'))
                                  );
                                  return historyEntry ? (
                                    <p className="text-xs text-gray-500 flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {formatTimestamp(historyEntry.timestamp)}
                                    </p>
                                  ) : null;
                                })()
                              )}
                              
                              {/* Current step timestamp */}
                              {isCurrent && (
                                <motion.p 
                                  className="text-xs text-cyan-600 flex items-center gap-1 font-medium"
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                >
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                  Processing now...
                                </motion.p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* What Happens Next Section */}
                  <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-blue-900 mb-1">What Happens Next?</h4>
                        <p className="text-sm text-blue-800">
                          {getNextStepMessage(selectedOrder)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Order Progress Buttons */}
                  <OrderProgressButtons
                    orderId={selectedOrder.orderId}
                    currentStatus={selectedOrder.status}
                    onStatusUpdate={async (newStatus) => {
                      // Update the selected order status
                      setSelectedOrder({ ...selectedOrder, status: newStatus });
                      // Refresh orders list
                      await fetchOrders();
                    }}
                    disabled={false}
                  />

                  {/* Status Message for Completed Orders */}
                  {(selectedOrder.status === 'completed' || selectedOrder.status === 'DELIVERED') && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                      <div className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-green-900">
                          <p className="font-semibold mb-1">Installation Complete!</p>
                          <p>Your device has been successfully installed and is now active in your dashboard.</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Enhanced Footer */}
                <div className="bg-gray-50 px-6 py-4 border-t">
                  <div className="flex items-center justify-between">
                    {(selectedOrder.status === 'ORDER_PLACED' || selectedOrder.status === 'pending') ? (
                      <>
                        <button
                          onClick={() => handleCancelOrder(selectedOrder.orderId)}
                          disabled={isCancelling}
                          className="px-6 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                        >
                          {isCancelling ? 'Cancelling...' : 'Cancel Order'}
                        </button>
                        <div className="flex items-center gap-3">
                          <a
                            href="mailto:support@aquachain.com"
                            className="flex items-center gap-2 text-sm text-gray-600 hover:text-cyan-600 transition-colors"
                          >
                            <HelpCircle className="w-4 h-4" />
                            Need Help?
                          </a>
                          <button
                            onClick={() => setShowDetailsModal(false)}
                            className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                          >
                            Okay, Got It
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="flex items-center justify-between w-full">
                        <a
                          href="mailto:support@aquachain.com"
                          className="flex items-center gap-2 text-sm text-gray-600 hover:text-cyan-600 transition-colors"
                        >
                          <HelpCircle className="w-4 h-4" />
                          Need Help?
                        </a>
                        <button
                          onClick={() => setShowDetailsModal(false)}
                          className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                        >
                          {selectedOrder.status === 'completed' || selectedOrder.status === 'DELIVERED' 
                            ? 'Close' 
                            : 'Track Later'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Payment Method Selection Modal */}
      <AnimatePresence>
        {showPaymentModal && selectedOrder && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowPaymentModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
                {/* Header */}
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <IndianRupee className="w-6 h-6 text-white" />
                    <h2 className="text-xl font-bold text-white">Choose Payment Method</h2>
                  </div>
                  <button
                    onClick={() => setShowPaymentModal(false)}
                    className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6">
                  <div className="mb-6">
                    <p className="text-gray-600 mb-2">Order ID: <span className="font-semibold text-gray-900">{selectedOrder.orderId.slice(0, 12)}</span></p>
                    <p className="text-gray-600 mb-2">Device: <span className="font-semibold text-gray-900">{getDeviceName(selectedOrder.deviceSKU)}</span></p>
                    <p className="text-gray-600">Quote Amount: <span className="font-semibold text-green-600 text-xl">₹{selectedOrder.quoteAmount?.toLocaleString()}</span></p>
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      Select Payment Method
                    </label>
                    <div className="space-y-3">
                      <button
                        type="button"
                        onClick={() => setSelectedPaymentMethod('COD')}
                        className={`w-full p-4 border-2 rounded-lg transition text-left ${
                          selectedPaymentMethod === 'COD'
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-green-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                            selectedPaymentMethod === 'COD' ? 'border-green-500' : 'border-gray-300'
                          }`}>
                            {selectedPaymentMethod === 'COD' && (
                              <div className="w-3 h-3 rounded-full bg-green-500" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">Cash on Delivery</div>
                            <div className="text-sm text-gray-600">Pay when device is delivered and installed</div>
                          </div>
                        </div>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedPaymentMethod('ONLINE')}
                        className={`w-full p-4 border-2 rounded-lg transition text-left ${
                          selectedPaymentMethod === 'ONLINE'
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-green-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                            selectedPaymentMethod === 'ONLINE' ? 'border-green-500' : 'border-gray-300'
                          }`}>
                            {selectedPaymentMethod === 'ONLINE' && (
                              <div className="w-3 h-3 rounded-full bg-green-500" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">Online Payment</div>
                            <div className="text-sm text-gray-600">Pay now via UPI, Card, or Net Banking</div>
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <p className="text-sm text-blue-900">
                      <strong>Note:</strong> After selecting your payment method, the admin will proceed with device provisioning and technician assignment.
                    </p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowPaymentModal(false)}
                      disabled={isSubmittingPayment}
                      className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmitPaymentMethod}
                      disabled={isSubmittingPayment}
                      className="flex-1 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isSubmittingPayment ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Confirming...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          <span>Confirm Payment Method</span>
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

      {/* Cancellation Reason Modal */}
      <AnimatePresence>
        {showCancelModal && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowCancelModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-red-500 to-red-600 p-6 rounded-t-2xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                        <AlertCircle className="w-6 h-6 text-white" />
                      </div>
                      <h2 className="text-2xl font-bold text-white">Cancel Order</h2>
                    </div>
                    <button
                      onClick={() => setShowCancelModal(false)}
                      className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-sm text-red-800">
                      <strong>Warning:</strong> This action cannot be undone. Please provide a reason for cancellation.
                    </p>
                  </div>

                  {/* Cancellation Reasons */}
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Cancellation Reason *
                    </label>
                    
                    {[
                      { value: 'changed_mind', label: 'Changed my mind' },
                      { value: 'found_better_price', label: 'Found a better price elsewhere' },
                      { value: 'ordered_by_mistake', label: 'Ordered by mistake' },
                      { value: 'delivery_time_too_long', label: 'Delivery time is too long' },
                      { value: 'payment_issues', label: 'Payment issues' },
                      { value: 'other', label: 'Other (please specify)' }
                    ].map((reason) => (
                      <label
                        key={reason.value}
                        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-all ${
                          cancellationReason === reason.value
                            ? 'border-red-500 bg-red-50'
                            : 'border-gray-200 hover:border-red-300 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          name="cancellationReason"
                          value={reason.value}
                          checked={cancellationReason === reason.value}
                          onChange={(e) => setCancellationReason(e.target.value)}
                          className="w-4 h-4 text-red-500 focus:ring-red-500"
                        />
                        <span className="text-sm text-gray-700">{reason.label}</span>
                      </label>
                    ))}
                  </div>

                  {/* Other Reason Text Area */}
                  {cancellationReason === 'other' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Please specify your reason *
                      </label>
                      <textarea
                        value={otherReason}
                        onChange={(e) => setOtherReason(e.target.value)}
                        placeholder="Enter your reason for cancellation..."
                        rows={4}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
                        maxLength={500}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {otherReason.length}/500 characters
                      </p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 px-6 py-4 rounded-b-2xl flex gap-3">
                  <button
                    onClick={() => setShowCancelModal(false)}
                    disabled={isCancelling}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                  >
                    Go Back
                  </button>
                  <button
                    onClick={confirmCancellation}
                    disabled={isCancelling || !cancellationReason || (cancellationReason === 'other' && !otherReason.trim())}
                    className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isCancelling ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Cancelling...
                      </>
                    ) : (
                      'Confirm Cancellation'
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.visible}
        onClose={hideToast}
      />
    </div>
  );
};

export default MyOrdersPage;
