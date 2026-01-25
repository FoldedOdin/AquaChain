import React, { useState, useEffect } from 'react';
import { WarehouseLocation, StockMovement, WarehouseMetrics } from '../../../types';
import { useNotification } from '../../../contexts/NotificationContext';

interface ReceivingItem {
  id: string;
  poNumber: string;
  supplier: string;
  expectedDate: string;
  status: 'pending' | 'in-progress' | 'completed';
  items: Array<{
    sku: string;
    description: string;
    expectedQty: number;
    receivedQty: number;
  }>;
}

interface DispatchItem {
  id: string;
  orderNumber: string;
  customer: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'picking' | 'packed' | 'shipped';
  items: Array<{
    sku: string;
    description: string;
    quantity: number;
    location: string;
  }>;
}

const WarehouseManagerView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'workflows' | 'locations' | 'movements' | 'metrics'>('workflows');
  const [receivingItems, setReceivingItems] = useState<ReceivingItem[]>([]);
  const [dispatchItems, setDispatchItems] = useState<DispatchItem[]>([]);
  const [warehouseLocations, setWarehouseLocations] = useState<WarehouseLocation[]>([]);
  const [stockMovements, setStockMovements] = useState<StockMovement[]>([]);
  const [metrics, setMetrics] = useState<WarehouseMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const { showNotification } = useNotification();

  useEffect(() => {
    loadWarehouseData();
  }, []);

  const loadWarehouseData = async () => {
    try {
      setLoading(true);
      
      // Mock data - replace with actual API calls
      const mockReceiving: ReceivingItem[] = [
        {
          id: 'RCV-001',
          poNumber: 'PO-2024-001',
          supplier: 'AquaTech Solutions',
          expectedDate: '2024-01-25',
          status: 'pending',
          items: [
            { sku: 'ESP32-001', description: 'ESP32 Water Sensor', expectedQty: 50, receivedQty: 0 },
            { sku: 'PROBE-PH', description: 'pH Probe Sensor', expectedQty: 25, receivedQty: 0 }
          ]
        },
        {
          id: 'RCV-002',
          poNumber: 'PO-2024-002',
          supplier: 'Sensor Dynamics',
          expectedDate: '2024-01-26',
          status: 'in-progress',
          items: [
            { sku: 'TDS-METER', description: 'TDS Measurement Device', expectedQty: 30, receivedQty: 15 }
          ]
        }
      ];

      const mockDispatch: DispatchItem[] = [
        {
          id: 'DSP-001',
          orderNumber: 'ORD-2024-001',
          customer: 'City Water Department',
          priority: 'high',
          status: 'pending',
          items: [
            { sku: 'ESP32-001', description: 'ESP32 Water Sensor', quantity: 10, location: 'A1-B2' },
            { sku: 'PROBE-PH', description: 'pH Probe Sensor', quantity: 5, location: 'A2-C1' }
          ]
        },
        {
          id: 'DSP-002',
          orderNumber: 'ORD-2024-002',
          customer: 'Industrial Water Co.',
          priority: 'medium',
          status: 'picking',
          items: [
            { sku: 'TDS-METER', description: 'TDS Measurement Device', quantity: 8, location: 'B1-A3' }
          ]
        }
      ];

      const mockLocations: WarehouseLocation[] = [
        { id: 'A1-B2', zone: 'A', aisle: '1', shelf: 'B', position: '2', capacity: 100, occupied: 75, items: ['ESP32-001'] },
        { id: 'A2-C1', zone: 'A', aisle: '2', shelf: 'C', position: '1', capacity: 50, occupied: 30, items: ['PROBE-PH'] },
        { id: 'B1-A3', zone: 'B', aisle: '1', shelf: 'A', position: '3', capacity: 80, occupied: 45, items: ['TDS-METER'] },
        { id: 'B2-D1', zone: 'B', aisle: '2', shelf: 'D', position: '1', capacity: 120, occupied: 0, items: [] }
      ];

      const mockMovements: StockMovement[] = [
        {
          id: 'MOV-001',
          timestamp: '2024-01-25T10:30:00Z',
          type: 'inbound',
          sku: 'ESP32-001',
          quantity: 25,
          fromLocation: 'RECEIVING',
          toLocation: 'A1-B2',
          operator: 'John Smith',
          reason: 'Stock receipt'
        },
        {
          id: 'MOV-002',
          timestamp: '2024-01-25T11:15:00Z',
          type: 'outbound',
          sku: 'PROBE-PH',
          quantity: 5,
          fromLocation: 'A2-C1',
          toLocation: 'SHIPPING',
          operator: 'Jane Doe',
          reason: 'Order fulfillment'
        }
      ];

      const mockMetrics: WarehouseMetrics = {
        utilizationRate: 78,
        averagePickTime: 4.2,
        orderAccuracy: 99.5,
        throughputPerHour: 45,
        pendingReceipts: 12,
        pendingDispatches: 8,
        dailyMovements: 156,
        performanceScore: 92
      };

      setReceivingItems(mockReceiving);
      setDispatchItems(mockDispatch);
      setWarehouseLocations(mockLocations);
      setStockMovements(mockMovements);
      setMetrics(mockMetrics);
    } catch (error) {
      console.error('Error loading warehouse data:', error);
      showNotification('Failed to load warehouse data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReceiveItem = (receivingId: string, itemSku: string, quantity: number) => {
    setReceivingItems(prev => prev.map(item => {
      if (item.id === receivingId) {
        return {
          ...item,
          items: item.items.map(i => 
            i.sku === itemSku 
              ? { ...i, receivedQty: Math.min(i.receivedQty + quantity, i.expectedQty) }
              : i
          )
        };
      }
      return item;
    }));
    showNotification(`Received ${quantity} units of ${itemSku}`, 'success');
  };

  const handleDispatchUpdate = (dispatchId: string, newStatus: DispatchItem['status']) => {
    setDispatchItems(prev => prev.map(item => 
      item.id === dispatchId ? { ...item, status: newStatus } : item
    ));
    showNotification(`Dispatch ${dispatchId} updated to ${newStatus}`, 'success');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in-progress': case 'picking': return 'bg-blue-100 text-blue-800';
      case 'completed': case 'packed': return 'bg-green-100 text-green-800';
      case 'shipped': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Warehouse Operations</h2>
        <p className="text-gray-600">
          Manage receiving and dispatch workflows, location management, and warehouse performance metrics.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Pending Receipts</p>
              <p className="text-2xl font-semibold text-gray-900">{metrics?.pendingReceipts || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8l-4 4m0 0l4 4m-4-4h18" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Pending Dispatches</p>
              <p className="text-2xl font-semibold text-gray-900">{metrics?.pendingDispatches || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Warehouse Utilization</p>
              <p className="text-2xl font-semibold text-gray-900">{metrics?.utilizationRate || 0}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-amber-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Pick Time</p>
              <p className="text-2xl font-semibold text-gray-900">{metrics?.averagePickTime || 0}m</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'workflows', name: 'Workflows', icon: '🔄' },
              { id: 'locations', name: 'Locations', icon: '📍' },
              { id: 'movements', name: 'Movements', icon: '📦' },
              { id: 'metrics', name: 'Metrics', icon: '📊' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'workflows' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Receiving Workflows */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Receiving Workflows</h3>
                <div className="space-y-4">
                  {receivingItems.map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">{item.poNumber}</h4>
                          <p className="text-sm text-gray-600">{item.supplier}</p>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                          {item.status}
                        </span>
                      </div>
                      <div className="space-y-2">
                        {item.items.map((subItem) => (
                          <div key={subItem.sku} className="flex items-center justify-between text-sm">
                            <span>{subItem.description}</span>
                            <div className="flex items-center space-x-2">
                              <span>{subItem.receivedQty}/{subItem.expectedQty}</span>
                              <button
                                onClick={() => handleReceiveItem(item.id, subItem.sku, 1)}
                                className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                                disabled={subItem.receivedQty >= subItem.expectedQty}
                              >
                                +1
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Dispatch Workflows */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Dispatch Workflows</h3>
                <div className="space-y-4">
                  {dispatchItems.map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">{item.orderNumber}</h4>
                          <p className="text-sm text-gray-600">{item.customer}</p>
                        </div>
                        <div className="flex space-x-2">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(item.priority)}`}>
                            {item.priority}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                            {item.status}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-2 mb-3">
                        {item.items.map((subItem) => (
                          <div key={subItem.sku} className="flex items-center justify-between text-sm">
                            <span>{subItem.description}</span>
                            <span>{subItem.quantity} @ {subItem.location}</span>
                          </div>
                        ))}
                      </div>
                      <div className="flex space-x-2">
                        {item.status === 'pending' && (
                          <button
                            onClick={() => handleDispatchUpdate(item.id, 'picking')}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            Start Picking
                          </button>
                        )}
                        {item.status === 'picking' && (
                          <button
                            onClick={() => handleDispatchUpdate(item.id, 'packed')}
                            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                          >
                            Mark Packed
                          </button>
                        )}
                        {item.status === 'packed' && (
                          <button
                            onClick={() => handleDispatchUpdate(item.id, 'shipped')}
                            className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
                          >
                            Ship Order
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'locations' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Location Management Grid</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {warehouseLocations.map((location) => (
                  <div
                    key={location.id}
                    className={`border-2 border-dashed rounded-lg p-4 ${
                      location.occupied > 0 ? 'border-blue-300 bg-blue-50' : 'border-gray-300 bg-gray-50'
                    }`}
                  >
                    <div className="text-center">
                      <h4 className="font-medium text-gray-900">{location.id}</h4>
                      <p className="text-sm text-gray-600">Zone {location.zone}</p>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(location.occupied / location.capacity) * 100}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {location.occupied}/{location.capacity} units
                        </p>
                      </div>
                      {location.items.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-600">Items:</p>
                          {location.items.map((item) => (
                            <span key={item} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mt-1 mr-1">
                              {item}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'movements' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Stock Movement Log</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        From → To
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Operator
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reason
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {stockMovements.map((movement) => (
                      <tr key={movement.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(movement.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            movement.type === 'inbound' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {movement.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {movement.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {movement.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {movement.fromLocation} → {movement.toLocation}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {movement.operator}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {movement.reason}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'metrics' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Warehouse Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Order Accuracy</h4>
                  <p className="text-3xl font-bold">{metrics?.orderAccuracy}%</p>
                  <p className="text-blue-100 text-sm">Last 30 days</p>
                </div>
                
                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Throughput</h4>
                  <p className="text-3xl font-bold">{metrics?.throughputPerHour}/hr</p>
                  <p className="text-green-100 text-sm">Items processed</p>
                </div>
                
                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Performance Score</h4>
                  <p className="text-3xl font-bold">{metrics?.performanceScore}</p>
                  <p className="text-purple-100 text-sm">Overall rating</p>
                </div>
                
                <div className="bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Daily Movements</h4>
                  <p className="text-3xl font-bold">{metrics?.dailyMovements}</p>
                  <p className="text-amber-100 text-sm">Today's activity</p>
                </div>
                
                <div className="bg-gradient-to-r from-red-500 to-red-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Utilization Rate</h4>
                  <p className="text-3xl font-bold">{metrics?.utilizationRate}%</p>
                  <p className="text-red-100 text-sm">Space efficiency</p>
                </div>
                
                <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-lg p-6 text-white">
                  <h4 className="text-lg font-medium mb-2">Pick Time</h4>
                  <p className="text-3xl font-bold">{metrics?.averagePickTime}m</p>
                  <p className="text-indigo-100 text-sm">Average duration</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarehouseManagerView;