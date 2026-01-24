import React, { useState, useEffect, useCallback } from 'react';
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
  ArrowLeft
} from 'lucide-react';
import Toast from '../Toast/Toast';
import ShipmentTracking from './ShipmentTracking';

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

  // Fetch orders
  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch('http://localhost:3002/api/orders/my', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    
    // Set up real-time polling every 10 seconds
    const pollInterval = setInterval(() => {
      fetchOrders();
    }, 10000);
    
    return () => clearInterval(pollInterval);
  }, [fetchOrders]);

  // Get status info
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Pending Review' };
      case 'quoted':
        return { icon: IndianRupee, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Quote Provided' };
      case 'provisioned':
        return { icon: Package, color: 'text-purple-600', bg: 'bg-purple-100', label: 'Device Provisioned' };
      case 'assigned':
        return { icon: Wrench, color: 'text-indigo-600', bg: 'bg-indigo-100', label: 'Technician Assigned' };
      case 'shipped':
        return { icon: Truck, color: 'text-cyan-600', bg: 'bg-cyan-100', label: 'Shipped' };
      case 'installing':
        return { icon: Wrench, color: 'text-orange-600', bg: 'bg-orange-100', label: 'Installing' };
      case 'completed':
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' };
      case 'cancelled':
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

  // Handle cancel order
  const handleCancelOrder = async (orderId: string) => {
    if (!confirm('Are you sure you want to cancel this order?')) return;

    setIsCancelling(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/orders/${orderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        showToast('Order cancelled successfully', 'success');
        fetchOrders();
        setShowDetailsModal(false);
      } else {
        const error = await response.json();
        showToast(error.error || 'Failed to cancel order', 'error');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      showToast('Error cancelling order', 'error');
    } finally {
      setIsCancelling(false);
    }
  };

  // Get timeline steps
  const getTimelineSteps = (order: Order) => {
    const steps = [
      { status: 'pending', label: 'Order Placed', completed: true },
      { status: 'quoted', label: 'Quote Provided', completed: ['quoted', 'provisioned', 'assigned', 'shipped', 'installing', 'completed'].includes(order.status) },
      { status: 'provisioned', label: 'Device Ready', completed: ['provisioned', 'assigned', 'shipped', 'installing', 'completed'].includes(order.status) },
      { status: 'assigned', label: 'Technician Assigned', completed: ['assigned', 'shipped', 'installing', 'completed'].includes(order.status) },
      { status: 'shipped', label: 'Shipped', completed: ['shipped', 'installing', 'completed'].includes(order.status) },
      { status: 'completed', label: 'Installed', completed: order.status === 'completed' },
    ];
    return steps;
  };

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
        {orders.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
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
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => {
              const statusInfo = getStatusInfo(order.status);
              const StatusIcon = statusInfo.icon;

              return (
                <motion.div
                  key={order.orderId}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
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
                          <span className="truncate">{order.address.split(',')[0]}</span>
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

                    <div className="flex flex-col gap-2">
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
                      {order.status === 'pending' && (
                        <button
                          onClick={() => handleCancelOrder(order.orderId)}
                          className="px-4 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          Cancel Order
                        </button>
                      )}
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
                        <p className="text-gray-900">{selectedOrder.address}</p>
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

                  {/* Order Timeline */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Order Progress</h3>
                    <div className="relative">
                      {getTimelineSteps(selectedOrder).map((step, index) => {
                        const isLast = index === getTimelineSteps(selectedOrder).length - 1;
                        return (
                          <div key={step.status} className="flex items-start mb-4">
                            <div className="flex flex-col items-center mr-4">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                step.completed ? 'bg-green-500' : 'bg-gray-300'
                              }`}>
                                {step.completed ? (
                                  <CheckCircle className="w-5 h-5 text-white" />
                                ) : (
                                  <Clock className="w-5 h-5 text-gray-600" />
                                )}
                              </div>
                              {!isLast && (
                                <div className={`w-0.5 h-12 ${step.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
                              )}
                            </div>
                            <div className="flex-1 pt-1">
                              <p className={`font-medium ${step.completed ? 'text-gray-900' : 'text-gray-500'}`}>
                                {step.label}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Status Message */}
                  {selectedOrder.status === 'pending' && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-yellow-900">
                          <p className="font-semibold mb-1">Awaiting Admin Review</p>
                          <p>Your order is being reviewed by our admin team. You'll receive a quote within 24 hours.</p>
                        </div>
                      </div>
                    </div>
                  )}
                  {selectedOrder.status === 'quoted' && !selectedOrder.paymentMethod && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-green-900">
                          <p className="font-semibold mb-1">Action Required: Choose Payment Method</p>
                          <p>Admin has provided a quote of ₹{selectedOrder.quoteAmount?.toLocaleString()}. Please select your payment method (COD or Online) to proceed with device provisioning.</p>
                        </div>
                      </div>
                    </div>
                  )}
                  {selectedOrder.status === 'quoted' && selectedOrder.paymentMethod && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <IndianRupee className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-blue-900">
                          <p className="font-semibold mb-1">Quote Accepted</p>
                          <p>Quote: ₹{selectedOrder.quoteAmount?.toLocaleString()} | Payment: {selectedOrder.paymentMethod}. Waiting for admin to provision device.</p>
                        </div>
                      </div>
                    </div>
                  )}
                  {selectedOrder.status === 'completed' && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
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

                {/* Footer */}
                <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
                  {selectedOrder.status === 'pending' ? (
                    <>
                      <button
                        onClick={() => handleCancelOrder(selectedOrder.orderId)}
                        disabled={isCancelling}
                        className="px-6 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                      >
                        {isCancelling ? 'Cancelling...' : 'Cancel Order'}
                      </button>
                      <button
                        onClick={() => setShowDetailsModal(false)}
                        className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        Close
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setShowDetailsModal(false)}
                      className="ml-auto px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                    >
                      Close
                    </button>
                  )}
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
