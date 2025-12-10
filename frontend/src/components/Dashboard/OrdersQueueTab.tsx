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
  User,
  Filter,
  Search
} from 'lucide-react';
import QuoteModal from './QuoteModal';
import ProvisionModal from './ProvisionModal';
import Toast from '../Toast/Toast';

interface Order {
  orderId: string;
  consumerName: string;
  consumerEmail: string;
  deviceSKU: string;
  status: string;
  address: string;
  phone: string;
  paymentMethod: string;
  preferredSlot?: string;
  quoteAmount?: number;
  provisionedDeviceId?: string;
  assignedTechnicianId?: string;
  assignedTechnicianName?: string;
  createdAt: string;
  updatedAt: string;
}

interface OrderStats {
  total: number;
  pending: number;
  quoted: number;
  provisioned: number;
  assigned: number;
  shipped: number;
  installing: number;
  completed: number;
  cancelled: number;
}

const OrdersQueueTab: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<OrderStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal states
  const [showQuoteModal, setShowQuoteModal] = useState(false);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  
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
      const response = await fetch('http://localhost:3002/api/admin/orders', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
        setStats(data.stats || null);
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
        return { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Pending' };
      case 'quoted':
        return { icon: IndianRupee, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Quoted' };
      case 'provisioned':
        return { icon: Package, color: 'text-purple-600', bg: 'bg-purple-100', label: 'Provisioned' };
      case 'assigned':
        return { icon: Wrench, color: 'text-indigo-600', bg: 'bg-indigo-100', label: 'Assigned' };
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

  // Handle actions
  const handleSetQuote = (order: Order) => {
    setSelectedOrder(order);
    setShowQuoteModal(true);
  };

  const handleProvision = (order: Order) => {
    setSelectedOrder(order);
    setShowProvisionModal(true);
  };



  const handleCancel = async (orderId: string) => {
    if (!confirm('Are you sure you want to cancel this order?')) return;

    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/admin/orders/${orderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        showToast('Order cancelled successfully', 'success');
        fetchOrders();
      } else {
        const error = await response.json();
        showToast(error.error || 'Failed to cancel order', 'error');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      showToast('Error cancelling order', 'error');
    }
  };

  // Filter orders
  const filteredOrders = orders.filter(order => {
    const matchesStatus = filterStatus === 'all' || order.status === filterStatus;
    const matchesSearch = searchQuery === '' || 
      order.consumerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.orderId.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading orders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="text-sm font-medium text-gray-700 mb-1">Total Orders</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          </div>
          <div className="bg-yellow-50 rounded-lg shadow-sm border border-yellow-200 p-4">
            <div className="text-sm font-medium text-yellow-700 mb-1">Pending</div>
            <div className="text-2xl font-bold text-yellow-900">{stats.pending}</div>
          </div>
          <div className="bg-blue-50 rounded-lg shadow-sm border border-blue-200 p-4">
            <div className="text-sm font-medium text-blue-700 mb-1">Quoted</div>
            <div className="text-2xl font-bold text-blue-900">{stats.quoted}</div>
          </div>
          <div className="bg-purple-50 rounded-lg shadow-sm border border-purple-200 p-4">
            <div className="text-sm font-medium text-purple-700 mb-1">In Progress</div>
            <div className="text-2xl font-bold text-purple-900">{stats.provisioned + stats.assigned + stats.shipped}</div>
          </div>
          <div className="bg-green-50 rounded-lg shadow-sm border border-green-200 p-4">
            <div className="text-sm font-medium text-green-700 mb-1">Completed</div>
            <div className="text-2xl font-bold text-green-900">{stats.completed}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by consumer name or order ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="quoted">Quoted</option>
              <option value="provisioned">Provisioned</option>
              <option value="assigned">Assigned</option>
              <option value="shipped">Shipped</option>
              <option value="installing">Installing</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Orders List */}
      {filteredOrders.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Orders Found</h3>
          <p className="text-gray-600">
            {searchQuery || filterStatus !== 'all' 
              ? 'Try adjusting your filters' 
              : 'No device orders have been placed yet'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredOrders.map((order) => {
            const statusInfo = getStatusInfo(order.status);
            const StatusIcon = statusInfo.icon;

            return (
              <motion.div
                key={order.orderId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
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

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <User className="w-4 h-4" />
                        <span>{order.consumerName}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(order.createdAt).toLocaleDateString()}</span>
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

                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${statusInfo.bg} ${statusInfo.color}`}>
                        <StatusIcon className="w-4 h-4" />
                        {statusInfo.label}
                      </span>
                      {order.provisionedDeviceId && (
                        <span className="text-sm text-gray-600">
                          Device: {order.provisionedDeviceId}
                        </span>
                      )}
                      {order.assignedTechnicianName && (
                        <span className="text-sm text-gray-600">
                          Tech: {order.assignedTechnicianName}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 ml-4">
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleSetQuote(order)}
                        className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors whitespace-nowrap"
                      >
                        Set Quote
                      </button>
                    )}
                    {order.status === 'quoted' && (
                      <button
                        onClick={() => handleProvision(order)}
                        className="px-4 py-2 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors whitespace-nowrap"
                      >
                        Provision Device
                      </button>
                    )}

                    {['pending', 'quoted'].includes(order.status) && (
                      <button
                        onClick={() => handleCancel(order.orderId)}
                        className="px-4 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors whitespace-nowrap"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Modals */}
      {selectedOrder && (
        <>
          <QuoteModal
            isOpen={showQuoteModal}
            onClose={() => {
              setShowQuoteModal(false);
              setSelectedOrder(null);
            }}
            order={selectedOrder}
            onSuccess={() => {
              fetchOrders();
              showToast('Quote set successfully', 'success');
            }}
          />
          <ProvisionModal
            isOpen={showProvisionModal}
            onClose={() => {
              setShowProvisionModal(false);
              setSelectedOrder(null);
            }}
            order={selectedOrder}
            onSuccess={() => {
              fetchOrders();
              showToast('Device provisioned successfully', 'success');
            }}
          />
        </>
      )}

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

export default OrdersQueueTab;
