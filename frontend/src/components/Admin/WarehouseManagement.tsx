import React, { useState, useEffect } from 'react';
import {
  Warehouse,
  Package,
  Truck,
  CheckCircle,
  Clock,
  AlertTriangle,
  Users,
  BarChart3,
  MapPin,
  Search,
  Filter,
  RefreshCw
} from 'lucide-react';
import { warehouseService } from '../../services/warehouseService';
import { WarehouseOverview, PickList, QualityCheck } from '../../types/warehouse';

interface WarehouseManagementProps {
  userRole: string;
}

const WarehouseManagement: React.FC<WarehouseManagementProps> = ({ userRole }) => {
  const [overview, setOverview] = useState<WarehouseOverview | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'receiving' | 'fulfillment' | 'quality'>('overview');
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    loadWarehouseData();
  }, []);

  const loadWarehouseData = async () => {
    try {
      setLoading(true);
      const response = await warehouseService.getWarehouseOverview();
      
      if (response.success && response.data) {
        setOverview(response.data);
      }
    } catch (error) {
      console.error('Error loading warehouse data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'approved':
      case 'delivered': return 'text-green-600 bg-green-100';
      case 'pending':
      case 'in_progress': return 'text-yellow-600 bg-yellow-100';
      case 'failed':
      case 'rejected': return 'text-red-600 bg-red-100';
      case 'shipped': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-green-600 bg-green-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading warehouse data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Warehouse Management</h1>
          <p className="text-gray-600">Monitor warehouse operations and logistics</p>
        </div>
        <button
          onClick={loadWarehouseData}
          className="flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Overview Metrics */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Warehouse className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Occupancy Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {overview.overview.occupancy_rate}%
                </p>
                <p className="text-sm text-gray-500">
                  {overview.overview.occupied_locations}/{overview.overview.total_locations} locations
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Truck className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Inbound Shipments</p>
                <p className="text-2xl font-bold text-green-600">
                  {overview.overview.inbound_shipments}
                </p>
                <p className="text-sm text-gray-500">Awaiting processing</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Outbound Orders</p>
                <p className="text-2xl font-bold text-purple-600">
                  {overview.overview.outbound_orders}
                </p>
                <p className="text-sm text-gray-500">Ready for fulfillment</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Available Space</p>
                <p className="text-2xl font-bold text-orange-600">
                  {overview.overview.available_locations}
                </p>
                <p className="text-sm text-gray-500">Open locations</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('receiving')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'receiving'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Receiving ({overview?.inbound_queue.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('fulfillment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'fulfillment'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Fulfillment ({overview?.outbound_queue.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('quality')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'quality'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Quality Control
          </button>
        </nav>
      </div>

      {/* Search and Filter */}
      {activeTab !== 'overview' && (
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      )}

      {/* Overview Tab */}
      {activeTab === 'overview' && overview && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Inbound Shipments */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Inbound Shipments</h3>
            </div>
            <div className="p-6">
              {overview.inbound_queue.length > 0 ? (
                <div className="space-y-4">
                  {overview.inbound_queue.slice(0, 5).map((shipment, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <Truck className="h-5 w-5 text-blue-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            PO: {shipment.po_id}
                          </p>
                          <p className="text-sm text-gray-500">
                            Supplier: {shipment.supplier_id}
                          </p>
                        </div>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(shipment.status)}`}>
                        {shipment.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No pending inbound shipments</p>
              )}
            </div>
          </div>

          {/* Recent Outbound Orders */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Outbound Orders Queue</h3>
            </div>
            <div className="p-6">
              {overview.outbound_queue.length > 0 ? (
                <div className="space-y-4">
                  {overview.outbound_queue.slice(0, 5).map((order, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <Package className="h-5 w-5 text-purple-600 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Order: {order.order_id || `ORD-${index + 1}`}
                          </p>
                          <p className="text-sm text-gray-500">
                            Items: {order.items?.length || 0}
                          </p>
                        </div>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(order.priority || 'normal')}`}>
                        {order.priority || 'normal'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No pending outbound orders</p>
              )}
            </div>
          </div>

          {/* Alerts */}
          {overview.alerts && overview.alerts.length > 0 && (
            <div className="lg:col-span-2 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                <h3 className="text-lg font-medium text-yellow-800">
                  Warehouse Alerts ({overview.alerts.length})
                </h3>
              </div>
              <div className="space-y-2">
                {overview.alerts.map((alert, index) => (
                  <div key={index} className="text-yellow-800">
                    {alert.message || `Alert ${index + 1}: Attention required`}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Receiving Tab */}
      {activeTab === 'receiving' && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Inbound Shipments</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Purchase Order
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Supplier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Expected Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {overview?.inbound_queue.map((shipment, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{shipment.po_id}</div>
                      <div className="text-sm text-gray-500">
                        {shipment.items?.length || 0} items
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {shipment.supplier_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 text-gray-400 mr-1" />
                        <span className="text-sm text-gray-900">
                          {shipment.expected_delivery 
                            ? new Date(shipment.expected_delivery).toLocaleDateString()
                            : 'TBD'
                          }
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(shipment.status)}`}>
                        {shipment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          Process
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          Receive
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fulfillment Tab */}
      {activeTab === 'fulfillment' && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Fulfillment Queue</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Items
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Assigned Picker
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {overview?.outbound_queue.map((order, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {order.order_id || `ORD-${index + 1}`}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.items?.length || 0} items
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(order.priority || 'normal')}`}>
                        {order.priority || 'normal'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Users className="h-4 w-4 text-gray-400 mr-1" />
                        <span className="text-sm text-gray-900">
                          {order.assigned_picker || 'Unassigned'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          Assign
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          Pick List
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quality Control Tab */}
      {activeTab === 'quality' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Quality Control Dashboard</h3>
          </div>
          <div className="p-6">
            <div className="text-center py-12">
              <CheckCircle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Quality Control System</h3>
              <p className="mt-1 text-sm text-gray-500">
                Quality inspection workflows and defect tracking will be displayed here.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Empty States */}
      {((activeTab === 'receiving' && (!overview?.inbound_queue || overview.inbound_queue.length === 0)) ||
        (activeTab === 'fulfillment' && (!overview?.outbound_queue || overview.outbound_queue.length === 0))) && (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No {activeTab === 'receiving' ? 'inbound shipments' : 'outbound orders'} found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            All {activeTab === 'receiving' ? 'shipments have been processed' : 'orders have been fulfilled'}.
          </p>
        </div>
      )}
    </div>
  );
};

export default WarehouseManagement;