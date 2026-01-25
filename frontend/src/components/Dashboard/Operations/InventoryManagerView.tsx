import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import { useNotification } from '../../../contexts/NotificationContext';
import { InventoryItem, StockAlert, DemandForecast, AuditEntry } from '../../../types';
import LoadingSpinner from '../../Loading/LoadingSpinner';

const InventoryManagerView: React.FC = () => {
  const { user } = useAuth();
  const { showNotification } = useNotification();
  const [isLoading, setIsLoading] = useState(true);
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([]);
  const [stockAlerts, setStockAlerts] = useState<StockAlert[]>([]);
  const [demandForecasts, setDemandForecasts] = useState<DemandForecast[]>([]);
  const [auditHistory, setAuditHistory] = useState<AuditEntry[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock data for demonstration
  useEffect(() => {
    const loadInventoryData = async () => {
      setIsLoading(true);
      try {
        // Simulate API calls
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Mock inventory items
        const mockItems: InventoryItem[] = [
          {
            itemId: 'INV001',
            itemName: 'Water Quality Sensor pH-7',
            currentStock: 45,
            reorderPoint: 20,
            reorderQuantity: 50,
            unitCost: 125.99,
            supplierId: 'SUP001',
            warehouseLocation: 'A-1-B-3',
            lastUpdated: new Date().toISOString(),
            updatedBy: user?.userId || 'system',
            category: 'Sensors',
            status: 'in_stock'
          },
          {
            itemId: 'INV002',
            itemName: 'Turbidity Sensor Module',
            currentStock: 8,
            reorderPoint: 15,
            reorderQuantity: 30,
            unitCost: 89.50,
            supplierId: 'SUP002',
            warehouseLocation: 'A-2-C-1',
            lastUpdated: new Date().toISOString(),
            updatedBy: user?.userId || 'system',
            category: 'Sensors',
            status: 'low_stock'
          },
          {
            itemId: 'INV003',
            itemName: 'TDS Measurement Kit',
            currentStock: 0,
            reorderPoint: 10,
            reorderQuantity: 25,
            unitCost: 67.25,
            supplierId: 'SUP001',
            warehouseLocation: 'B-1-A-2',
            lastUpdated: new Date().toISOString(),
            updatedBy: user?.userId || 'system',
            category: 'Test Kits',
            status: 'out_of_stock'
          }
        ];

        // Mock stock alerts
        const mockAlerts: StockAlert[] = [
          {
            alertId: 'ALT001',
            itemId: 'INV002',
            itemName: 'Turbidity Sensor Module',
            currentStock: 8,
            reorderPoint: 15,
            severity: 'warning',
            recommendedAction: 'Reorder 30 units from Supplier SUP002',
            createdAt: new Date().toISOString()
          },
          {
            alertId: 'ALT002',
            itemId: 'INV003',
            itemName: 'TDS Measurement Kit',
            currentStock: 0,
            reorderPoint: 10,
            severity: 'critical',
            recommendedAction: 'Urgent reorder required - 25 units from Supplier SUP001',
            createdAt: new Date().toISOString()
          }
        ];

        // Mock demand forecasts
        const mockForecasts: DemandForecast[] = [
          {
            itemId: 'INV001',
            itemName: 'Water Quality Sensor pH-7',
            forecastPeriod: '30d',
            predictedDemand: 35,
            confidence: 0.87,
            trend: 'stable',
            seasonalFactors: [1.0, 1.1, 1.2, 0.9]
          },
          {
            itemId: 'INV002',
            itemName: 'Turbidity Sensor Module',
            forecastPeriod: '30d',
            predictedDemand: 22,
            confidence: 0.92,
            trend: 'increasing',
            seasonalFactors: [1.0, 1.3, 1.4, 1.1]
          }
        ];

        // Mock audit history
        const mockAudit: AuditEntry[] = [
          {
            auditId: 'AUD001',
            userId: user?.userId || 'system',
            userName: `${user?.profile.firstName} ${user?.profile.lastName}` || 'System',
            action: 'UPDATE_REORDER_POINT',
            resource: 'inventory_item',
            resourceId: 'INV001',
            timestamp: new Date().toISOString(),
            ipAddress: '192.168.1.100',
            userAgent: 'Mozilla/5.0...',
            beforeState: { reorderPoint: 15 },
            afterState: { reorderPoint: 20 },
            success: true
          }
        ];

        setInventoryItems(mockItems);
        setStockAlerts(mockAlerts);
        setDemandForecasts(mockForecasts);
        setAuditHistory(mockAudit);
      } catch (error) {
        showNotification('Failed to load inventory data', 'error');
      } finally {
        setIsLoading(false);
      }
    };

    loadInventoryData();
  }, [user, showNotification]);

  // Filter inventory items based on search and category
  const filteredItems = inventoryItems.filter(item => {
    const matchesSearch = item.itemName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.itemId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(inventoryItems.map(item => item.category)))];

  // Calculate summary statistics
  const totalItems = inventoryItems.length;
  const lowStockItems = inventoryItems.filter(item => item.status === 'low_stock').length;
  const outOfStockItems = inventoryItems.filter(item => item.status === 'out_of_stock').length;
  const totalValue = inventoryItems.reduce((sum, item) => sum + (item.currentStock * item.unitCost), 0);

  const handleReorderPointUpdate = async (itemId: string, newReorderPoint: number) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setInventoryItems(prev => prev.map(item => 
        item.itemId === itemId 
          ? { ...item, reorderPoint: newReorderPoint, lastUpdated: new Date().toISOString() }
          : item
      ));
      
      showNotification(`Reorder point updated for item ${itemId}`, 'success');
    } catch (error) {
      showNotification('Failed to update reorder point', 'error');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" />
        <span className="ml-3 text-gray-600">Loading inventory data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Inventory Management</h2>
        <p className="text-gray-600">
          Manage stock levels, reorder points, and demand forecasting for all inventory items.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Items</p>
              <p className="text-2xl font-semibold text-gray-900">{totalItems}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-amber-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Low Stock Alerts</p>
              <p className="text-2xl font-semibold text-gray-900">{lowStockItems}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Out of Stock</p>
              <p className="text-2xl font-semibold text-gray-900">{outOfStockItems}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Value</p>
              <p className="text-2xl font-semibold text-gray-900">${totalValue.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stock Alerts */}
      {stockAlerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Stock Alerts</h3>
          <div className="space-y-3">
            {stockAlerts.map(alert => (
              <div key={alert.alertId} className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'critical' 
                  ? 'bg-red-50 border-red-400' 
                  : 'bg-amber-50 border-amber-400'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{alert.itemName}</h4>
                    <p className="text-sm text-gray-600">
                      Current stock: {alert.currentStock} | Reorder point: {alert.reorderPoint}
                    </p>
                    <p className="text-sm font-medium text-gray-700 mt-1">
                      {alert.recommendedAction}
                    </p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    alert.severity === 'critical'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {alert.severity.toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search Items
            </label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by item name or ID..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent"
            />
          </div>
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Inventory Items Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Inventory Items</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Item
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Stock
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reorder Point
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unit Cost
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
              {filteredItems.map(item => (
                <tr key={item.itemId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{item.itemName}</div>
                      <div className="text-sm text-gray-500">{item.itemId}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.currentStock}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.reorderPoint}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${item.unitCost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      item.status === 'in_stock' 
                        ? 'bg-green-100 text-green-800'
                        : item.status === 'low_stock'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {item.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => {
                        const newPoint = prompt('Enter new reorder point:', item.reorderPoint.toString());
                        if (newPoint && !isNaN(Number(newPoint))) {
                          handleReorderPointUpdate(item.itemId, Number(newPoint));
                        }
                      }}
                      className="text-aqua-600 hover:text-aqua-900 mr-3"
                    >
                      Edit Reorder Point
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Demand Forecasting */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Demand Forecasting</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {demandForecasts.map(forecast => (
            <div key={forecast.itemId} className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">{forecast.itemName}</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Predicted Demand (30d):</span>
                  <span className="text-sm font-medium">{forecast.predictedDemand} units</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Confidence:</span>
                  <span className="text-sm font-medium">{(forecast.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Trend:</span>
                  <span className={`text-sm font-medium ${
                    forecast.trend === 'increasing' ? 'text-green-600' :
                    forecast.trend === 'decreasing' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {forecast.trend.charAt(0).toUpperCase() + forecast.trend.slice(1)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit History */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Inventory Audit History</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Changes
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {auditHistory.map(entry => (
                <tr key={entry.auditId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(entry.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.userName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.action.replace(/_/g, ' ')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.resourceId}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {entry.beforeState && entry.afterState && (
                      <div className="space-y-1">
                        <div>Before: {JSON.stringify(entry.beforeState)}</div>
                        <div>After: {JSON.stringify(entry.afterState)}</div>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default InventoryManagerView;