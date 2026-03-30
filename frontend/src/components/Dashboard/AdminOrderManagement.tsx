import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package, CheckCircle, XCircle,
  IndianRupee, Phone, Filter,
  Search, RefreshCw, ChevronDown, AlertCircle, X, UserCheck
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

type OrderStatus =
  | 'PENDING_PAYMENT' | 'PENDING_CONFIRMATION' | 'ORDER_PLACED'
  | 'DEVICE_READY' | 'TECHNICIAN_ASSIGNED' | 'SHIPPED'
  | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'INSTALLED' | 'CANCELLED' | 'FAILED';

interface Technician {
  userId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
}

interface AdminOrder {
  orderId: string;
  consumerName?: string;
  consumerEmail?: string;
  deviceSKU?: string;
  status: OrderStatus | string;
  address?: string;
  phone?: string;
  paymentMethod?: string;
  quoteAmount?: number;
  assignedTechnicianId?: string;
  assignedTechnicianName?: string;
  paymentStatus?: string;
  paymentId?: string;
  gatewayRef?: string;
  createdAt: string;
  updatedAt: string;
  statusHistory?: Array<{ status: string; timestamp: string; message: string }>;
}

interface OrderStats {
  total: number;
  pending: number;
  inProgress: number;
  delivered: number;
  cancelled: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const STATUS_TRANSITIONS: Record<string, OrderStatus[]> = {
  PENDING_CONFIRMATION: ['ORDER_PLACED', 'CANCELLED'],
  ORDER_PLACED:         ['DEVICE_READY', 'CANCELLED'],
  DEVICE_READY:         ['TECHNICIAN_ASSIGNED', 'CANCELLED'],
  TECHNICIAN_ASSIGNED:  ['SHIPPED', 'CANCELLED'],
  SHIPPED:              ['OUT_FOR_DELIVERY', 'CANCELLED'],
  OUT_FOR_DELIVERY:     ['DELIVERED', 'CANCELLED'],
  DELIVERED:            ['INSTALLED'],
  INSTALLED:            [],
  CANCELLED:            [],
  FAILED:               [],
};

const STATUS_LABELS: Record<string, string> = {
  PENDING_PAYMENT:      'Pending Payment',
  PENDING_CONFIRMATION: 'Pending Confirmation',
  ORDER_PLACED:         'Order Placed',
  DEVICE_READY:         'Device Ready',
  TECHNICIAN_ASSIGNED:  'Technician Assigned',
  SHIPPED:              'Shipped',
  OUT_FOR_DELIVERY:     'Out for Delivery',
  DELIVERED:            'Delivered',
  INSTALLED:            'Installed',
  CANCELLED:            'Cancelled',
  FAILED:               'Failed',
};

const STATUS_COLORS: Record<string, string> = {
  PENDING_PAYMENT:      'bg-yellow-100 text-yellow-800',
  PENDING_CONFIRMATION: 'bg-orange-100 text-orange-800',
  ORDER_PLACED:         'bg-blue-100 text-blue-800',
  DEVICE_READY:         'bg-indigo-100 text-indigo-800',
  TECHNICIAN_ASSIGNED:  'bg-purple-100 text-purple-800',
  SHIPPED:              'bg-cyan-100 text-cyan-800',
  OUT_FOR_DELIVERY:     'bg-teal-100 text-teal-800',
  DELIVERED:            'bg-green-100 text-green-800',
  INSTALLED:            'bg-emerald-100 text-emerald-800',
  CANCELLED:            'bg-red-100 text-red-800',
  FAILED:               'bg-gray-100 text-gray-800',
};

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  SUCCESS:   'bg-green-100 text-green-800',
  COMPLETED: 'bg-green-100 text-green-800',
  PENDING:   'bg-yellow-100 text-yellow-800',
  COD_PENDING: 'bg-orange-100 text-orange-800',
  FAILED:    'bg-red-100 text-red-800',
  REFUNDED:  'bg-purple-100 text-purple-800',
};

const API_BASE = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getToken(): string | null {
  return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || 'bg-gray-100 text-gray-700';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function PaymentBadge({ status }: { status?: string }) {
  if (!status) return <span className="text-gray-400 text-xs">—</span>;
  const color = PAYMENT_STATUS_COLORS[status.toUpperCase()] || 'bg-gray-100 text-gray-700';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

const AdminOrderManagement: React.FC = () => {
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [stats, setStats] = useState<OrderStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<AdminOrder | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [selectedTechnicianId, setSelectedTechnicianId] = useState('');

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Fetch technicians ────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API_BASE}/api/technicians`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => setTechnicians(data.technicians || []))
      .catch(() => {}); // non-critical, silently fail
  }, []);

  // ── Fetch orders ────────────────────────────────────────────────────────────
  const fetchOrders = useCallback(async (refresh = false) => {
    refresh ? setIsRefreshing(true) : setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/orders`, {
        headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        const list: AdminOrder[] = data.orders || [];
        setOrders(list);
        // Compute stats from list
        setStats({
          total:      list.length,
          pending:    list.filter(o => ['PENDING_PAYMENT','PENDING_CONFIRMATION','ORDER_PLACED'].includes(o.status)).length,
          inProgress: list.filter(o => ['DEVICE_READY','TECHNICIAN_ASSIGNED','SHIPPED','OUT_FOR_DELIVERY'].includes(o.status)).length,
          delivered:  list.filter(o => ['DELIVERED','INSTALLED'].includes(o.status)).length,
          cancelled:  list.filter(o => ['CANCELLED','FAILED'].includes(o.status)).length,
        });
      }
    } catch (e) {
      console.error('Failed to fetch admin orders', e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);

  // ── Update order status ─────────────────────────────────────────────────────
  const handleStatusUpdate = async (orderId: string, newStatus: OrderStatus) => {
    setIsUpdating(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        showToast(`Order status updated to ${STATUS_LABELS[newStatus] || newStatus}`);
        await fetchOrders(true);
        if (selectedOrder?.orderId === orderId) {
          setSelectedOrder(prev => prev ? { ...prev, status: newStatus } : prev);
        }
      } else {
        const err = await res.json();
        showToast(err.error || 'Failed to update status', 'error');
      }
    } catch {
      showToast('Network error updating status', 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  // ── Assign technician ───────────────────────────────────────────────────────
  const handleAssignTechnician = async (orderId: string, technicianId: string) => {
    setIsUpdating(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/orders/${orderId}/assign-technician`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ technicianId }),
      });
      if (res.ok) {
        showToast('Technician assigned successfully');
        await fetchOrders(true);
      } else {
        const err = await res.json();
        showToast(err.error || 'Failed to assign technician', 'error');
      }
    } catch {
      showToast('Network error assigning technician', 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  // ── Filtered orders ─────────────────────────────────────────────────────────
  const [filterUser, setFilterUser] = useState('all');

  // Derive unique users from loaded orders for the user filter dropdown
  const userOptions = React.useMemo(() => {
    const seen = new Map<string, string>();
    orders.forEach(o => {
      const email = o.consumerEmail || '';
      const name  = o.consumerName  || email;
      if (email && !seen.has(email)) seen.set(email, name);
    });
    return Array.from(seen.entries()).map(([email, name]) => ({ email, name }));
  }, [orders]);

  const filteredOrders = orders.filter(o => {
    const matchesStatus = filterStatus === 'all' || o.status === filterStatus;
    const matchesUser   = filterUser   === 'all' || o.consumerEmail === filterUser;
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q
      || o.orderId.toLowerCase().includes(q)
      || (o.consumerName  || '').toLowerCase().includes(q)
      || (o.consumerEmail || '').toLowerCase().includes(q);
    return matchesStatus && matchesUser && matchesSearch;
  });

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white text-sm flex items-center gap-2 ${
              toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'
            }`}
          >
            {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {[
            { label: 'Total Orders', value: stats.total, color: 'text-gray-900', bg: 'bg-white' },
            { label: 'Pending',      value: stats.pending,    color: 'text-orange-600', bg: 'bg-orange-50' },
            { label: 'In Progress',  value: stats.inProgress, color: 'text-blue-600',   bg: 'bg-blue-50' },
            { label: 'Delivered',    value: stats.delivered,  color: 'text-green-600',  bg: 'bg-green-50' },
            { label: 'Cancelled',    value: stats.cancelled,  color: 'text-red-600',    bg: 'bg-red-50' },
          ].map(s => (
            <div key={s.label} className={`${s.bg} rounded-lg p-4 border border-gray-100 shadow-sm`}>
              <p className="text-xs text-gray-500 mb-1">{s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3 flex-1">
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by order ID or customer..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white"
            >
              <option value="all">All Statuses</option>
              {Object.entries(STATUS_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
          <div className="relative">
            <select
              value={filterUser}
              onChange={e => setFilterUser(e.target.value)}
              className="pl-3 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white max-w-[200px]"
            >
              <option value="all">All Users</option>
              {userOptions.map(u => (
                <option key={u.email} value={u.email}>
                  {u.name !== u.email ? `${u.name} (${u.email})` : u.email}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
        <button
          onClick={() => fetchOrders(true)}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Package className="w-12 h-12 mb-3 opacity-40" />
            <p className="text-sm">No orders found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Order ID', 'Customer', 'Status', 'Payment', 'Technician', 'Created', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredOrders.map(order => (
                  <tr key={order.orderId} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">
                      {order.orderId.slice(0, 12)}…
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{order.consumerName || '—'}</p>
                      <p className="text-xs text-gray-500">{order.consumerEmail || ''}</p>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={order.status} /></td>
                    <td className="px-4 py-3">
                      <PaymentBadge status={order.paymentStatus} />
                      <p className="text-xs text-gray-500 mt-0.5">{order.paymentMethod || ''}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {order.assignedTechnicianName || <span className="text-gray-400">Unassigned</span>}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {new Date(order.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => { setSelectedOrder(order); setShowDetailModal(true); }}
                        className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Order Detail Modal */}
      <AnimatePresence>
        {showDetailModal && selectedOrder && (
          <>
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowDetailModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Package className="w-6 h-6 text-white" />
                    <div>
                      <h2 className="text-lg font-bold text-white">Order Management</h2>
                      <p className="text-purple-200 text-xs font-mono">{selectedOrder.orderId}</p>
                    </div>
                  </div>
                  <button onClick={() => setShowDetailModal(false)} className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6 space-y-6">
                  {/* Customer Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Customer</p>
                      <p className="font-medium text-gray-900">{selectedOrder.consumerName || '—'}</p>
                      <p className="text-sm text-gray-600">{selectedOrder.consumerEmail || ''}</p>
                      {selectedOrder.phone && (
                        <p className="text-sm text-gray-600 flex items-center gap-1 mt-1">
                          <Phone className="w-3 h-3" />{selectedOrder.phone}
                        </p>
                      )}
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Payment</p>
                      <PaymentBadge status={selectedOrder.paymentStatus} />
                      <p className="text-sm text-gray-600 mt-1">{selectedOrder.paymentMethod || '—'}</p>
                      {selectedOrder.quoteAmount && (
                        <p className="text-sm font-semibold text-gray-900 flex items-center gap-1 mt-1">
                          <IndianRupee className="w-3 h-3" />{selectedOrder.quoteAmount.toLocaleString()}
                        </p>
                      )}
                      {selectedOrder.gatewayRef && (
                        <p className="text-xs text-gray-500 mt-1 font-mono">Ref: {selectedOrder.gatewayRef}</p>
                      )}
                    </div>
                  </div>

                  {/* Current Status */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Current Status</p>
                    <StatusBadge status={selectedOrder.status} />
                  </div>

                  {/* Order Timeline */}
                  {selectedOrder.statusHistory && selectedOrder.statusHistory.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-3">Timeline</p>
                      <div className="space-y-2">
                        {selectedOrder.statusHistory.map((h, i) => (
                          <div key={i} className="flex items-start gap-3">
                            <div className="w-2 h-2 rounded-full bg-purple-400 mt-1.5 flex-shrink-0" />
                            <div>
                              <p className="text-sm font-medium text-gray-800">{STATUS_LABELS[h.status] || h.status}</p>
                              <p className="text-xs text-gray-500">{new Date(h.timestamp).toLocaleString()}</p>
                              {h.message && <p className="text-xs text-gray-600">{h.message}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Admin Actions */}
                  {STATUS_TRANSITIONS[selectedOrder.status]?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-3">Admin Actions</p>
                      <div className="flex flex-wrap gap-2">
                        {STATUS_TRANSITIONS[selectedOrder.status].map(nextStatus => (
                          <button
                            key={nextStatus}
                            onClick={() => handleStatusUpdate(selectedOrder.orderId, nextStatus)}
                            disabled={isUpdating}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                              nextStatus === 'CANCELLED'
                                ? 'bg-red-100 text-red-700 hover:bg-red-200 border border-red-300'
                                : 'bg-purple-600 text-white hover:bg-purple-700'
                            }`}
                          >
                            {isUpdating ? 'Updating…' : (
                              nextStatus === 'CANCELLED' ? 'Cancel Order' : `Mark as ${STATUS_LABELS[nextStatus]}`
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Technician Assignment */}
                  {selectedOrder.status === 'DEVICE_READY' && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Assign Technician</p>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <UserCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                          <select
                            value={selectedTechnicianId}
                            onChange={e => setSelectedTechnicianId(e.target.value)}
                            className="w-full pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white"
                          >
                            <option value="">Select a technician…</option>
                            {technicians.map(t => (
                              <option key={t.userId} value={t.userId}>
                                {t.firstName} {t.lastName} — {t.email}
                              </option>
                            ))}
                          </select>
                          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                        </div>
                        <button
                          onClick={() => {
                            if (selectedTechnicianId) {
                              handleAssignTechnician(selectedOrder.orderId, selectedTechnicianId);
                              setSelectedTechnicianId('');
                            }
                          }}
                          disabled={isUpdating || !selectedTechnicianId}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                          Assign
                        </button>
                      </div>
                      {technicians.length === 0 && (
                        <p className="text-xs text-gray-400 mt-1">No technicians available</p>
                      )}
                    </div>
                  )}

                  {/* Terminal states */}
                  {['INSTALLED', 'CANCELLED', 'FAILED'].includes(selectedOrder.status) && (
                    <div className={`rounded-lg p-4 flex items-start gap-3 ${
                      selectedOrder.status === 'INSTALLED' ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
                    }`}>
                      {selectedOrder.status === 'INSTALLED'
                        ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        : <AlertCircle className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
                      }
                      <p className="text-sm text-gray-700">
                        {selectedOrder.status === 'INSTALLED'
                          ? 'Order complete. Device installed and active.'
                          : `Order is in a terminal state: ${STATUS_LABELS[selectedOrder.status]}.`}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdminOrderManagement;
