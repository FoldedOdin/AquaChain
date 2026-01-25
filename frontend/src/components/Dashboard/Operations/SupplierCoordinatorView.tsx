import React, { useState, useEffect } from 'react';
import { 
  BuildingOfficeIcon, 
  DocumentTextIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CloudArrowUpIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { supplierService } from '../../../services/supplierService';
import { Supplier, SupplierContract, SupplierPerformanceReport } from '../../../types/supplier';

interface SupplierStats {
  activeSuppliers: number;
  activeContracts: number;
  riskAlerts: number;
  avgPerformance: number;
}

const SupplierCoordinatorView: React.FC = () => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [contracts, setContracts] = useState<SupplierContract[]>([]);
  const [stats, setStats] = useState<SupplierStats>({
    activeSuppliers: 0,
    activeContracts: 0,
    riskAlerts: 0,
    avgPerformance: 0
  });
  const [loading, setLoading] = useState(true);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [showContractModal, setShowContractModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [suppliersResult, analyticsResult] = await Promise.all([
        supplierService.getSuppliers(),
        supplierService.getSupplierAnalytics()
      ]);

      if (suppliersResult.success) {
        setSuppliers(suppliersResult.data);
        
        // Calculate stats from suppliers data
        const activeSuppliers = suppliersResult.data.filter((s: Supplier) => s.status === 'active').length;
        const avgPerformance = suppliersResult.data.reduce((sum: number, s: Supplier) => sum + s.performance_score, 0) / suppliersResult.data.length;
        const riskAlerts = suppliersResult.data.filter((s: Supplier) => s.performance_score < 70).length;
        
        setStats({
          activeSuppliers,
          activeContracts: 23, // This would come from contracts API
          riskAlerts,
          avgPerformance: Math.round(avgPerformance * 10) / 10
        });
      }
    } catch (error) {
      console.error('Error loading supplier data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSuppliers = suppliers
    .filter(supplier => {
      const matchesSearch = supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           supplier.contact_email.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || supplier.status === filterStatus;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let aValue, bValue;
      switch (sortBy) {
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'performance':
          aValue = a.performance_score;
          bValue = b.performance_score;
          break;
        case 'orders':
          aValue = a.total_orders;
          bValue = b.total_orders;
          break;
        default:
          aValue = a.name;
          bValue = b.name;
      }
      
      if (typeof aValue === 'string') {
        return sortOrder === 'asc' ? aValue.localeCompare(bValue as string) : (bValue as string).localeCompare(aValue);
      } else {
        return sortOrder === 'asc' ? (aValue as number) - (bValue as number) : (bValue as number) - (aValue as number);
      }
    });

  const getRiskLevel = (score: number): { level: string; color: string } => {
    if (score >= 90) return { level: 'Low', color: 'text-green-600 bg-green-100' };
    if (score >= 70) return { level: 'Medium', color: 'text-yellow-600 bg-yellow-100' };
    return { level: 'High', color: 'text-red-600 bg-red-100' };
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'inactive': return 'text-gray-600 bg-gray-100';
      case 'under_review': return 'text-yellow-600 bg-yellow-100';
      case 'suspended': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div 
          data-testid="loading-spinner"
          className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
        ></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Supplier Management</h2>
            <p className="text-gray-600">
              Manage supplier profiles, contracts, performance scoring, and risk indicators.
            </p>
          </div>
          <button
            onClick={() => setShowSupplierModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <PlusIcon className="w-5 h-5" />
            Add Supplier
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <BuildingOfficeIcon className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Suppliers</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.activeSuppliers}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Contracts</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.activeContracts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-amber-100 rounded-md flex items-center justify-center">
                <ExclamationTriangleIcon className="w-5 h-5 text-amber-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Risk Alerts</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.riskAlerts}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                <ChartBarIcon className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Performance</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.avgPerformance}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Supplier Profiles Management */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-gray-900">Supplier Profiles</h3>
          <div className="flex gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search suppliers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            {/* Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="under_review">Under Review</option>
              <option value="suspended">Suspended</option>
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="name">Sort by Name</option>
              <option value="performance">Sort by Performance</option>
              <option value="orders">Sort by Orders</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? <ArrowUpIcon className="w-5 h-5" /> : <ArrowDownIcon className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Suppliers Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Supplier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Orders
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Level
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
              {filteredSuppliers.map((supplier) => {
                const risk = getRiskLevel(supplier.performance_score);
                return (
                  <tr key={supplier.supplier_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                        <div className="text-sm text-gray-500">{supplier.contact_email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {supplier.supplier_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{supplier.performance_score}%</div>
                        <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${supplier.performance_score}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {supplier.total_orders}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${risk.color}`}>
                        {risk.level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(supplier.status)}`}>
                        {supplier.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedSupplier(supplier)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedSupplier(supplier);
                            setShowSupplierModal(true);
                          }}
                          className="text-green-600 hover:text-green-900"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Contract Management */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-gray-900">Contract Management</h3>
          <button
            onClick={() => setShowContractModal(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <DocumentTextIcon className="w-5 h-5" />
            New Contract
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Sample contracts - in real implementation, this would come from API */}
          {[
            { id: '1', supplier: 'AquaTech Solutions', type: 'Service Agreement', status: 'active', expires: '2024-12-31' },
            { id: '2', supplier: 'FlowSense Inc', type: 'Purchase Agreement', status: 'active', expires: '2024-06-30' },
            { id: '3', supplier: 'WaterPure Corp', type: 'Master Agreement', status: 'expiring', expires: '2024-03-15' }
          ].map((contract) => (
            <div key={contract.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-medium text-gray-900">{contract.supplier}</h4>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  contract.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {contract.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{contract.type}</p>
              <p className="text-sm text-gray-500 mb-3">Expires: {contract.expires}</p>
              <div className="flex justify-between items-center">
                <button className="text-blue-600 hover:text-blue-800 text-sm">View Details</button>
                <div className="flex space-x-2">
                  <button className="text-gray-400 hover:text-gray-600">
                    <CloudArrowUpIcon className="w-4 h-4" />
                  </button>
                  <button className="text-gray-400 hover:text-gray-600">
                    <PencilIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Scoring Visualization */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Performance Scoring</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Chart */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-4">Top Performers</h4>
            <div className="space-y-3">
              {filteredSuppliers
                .sort((a, b) => b.performance_score - a.performance_score)
                .slice(0, 5)
                .map((supplier, index) => (
                  <div key={supplier.supplier_id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-medium mr-3">
                        {index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{supplier.name}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-600 mr-2">{supplier.performance_score}%</span>
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${supplier.performance_score}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Performance Metrics */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-4">Key Metrics</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">On-Time Delivery</p>
                <p className="text-2xl font-semibold text-gray-900">92.5%</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Quality Score</p>
                <p className="text-2xl font-semibold text-gray-900">94.8%</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Response Time</p>
                <p className="text-2xl font-semibold text-gray-900">2.3h</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Defect Rate</p>
                <p className="text-2xl font-semibold text-gray-900">1.2%</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Indicators Dashboard */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Supplier Risk Indicators</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Financial Risk */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Financial Risk</h4>
              <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">Medium</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Payment Delays</span>
                <span className="text-gray-900">2 suppliers</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Credit Issues</span>
                <span className="text-gray-900">1 supplier</span>
              </div>
            </div>
          </div>

          {/* Operational Risk */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Operational Risk</h4>
              <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Low</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Delivery Delays</span>
                <span className="text-gray-900">3 suppliers</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Quality Issues</span>
                <span className="text-gray-900">1 supplier</span>
              </div>
            </div>
          </div>

          {/* Compliance Risk */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Compliance Risk</h4>
              <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">High</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Expired Certificates</span>
                <span className="text-gray-900">2 suppliers</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Missing Documentation</span>
                <span className="text-gray-900">1 supplier</span>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Alerts */}
        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-4">Recent Risk Alerts</h4>
          <div className="space-y-3">
            {[
              { supplier: 'WaterPure Corp', risk: 'Contract expiring in 30 days', severity: 'medium' },
              { supplier: 'FlowSense Inc', risk: 'Quality score below threshold', severity: 'high' },
              { supplier: 'AquaTech Solutions', risk: 'Payment terms violation', severity: 'low' }
            ].map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className={`w-5 h-5 mr-3 ${
                    alert.severity === 'high' ? 'text-red-500' : 
                    alert.severity === 'medium' ? 'text-yellow-500' : 'text-blue-500'
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alert.supplier}</p>
                    <p className="text-sm text-gray-600">{alert.risk}</p>
                  </div>
                </div>
                <button className="text-blue-600 hover:text-blue-800 text-sm">Review</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modals would be implemented here */}
      {showSupplierModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {selectedSupplier ? 'Edit Supplier' : 'Add New Supplier'}
            </h3>
            <p className="text-gray-600 mb-4">Supplier form would be implemented here</p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowSupplierModal(false);
                  setSelectedSupplier(null);
                }}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {showContractModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">New Contract</h3>
            <p className="text-gray-600 mb-4">Contract form with document upload would be implemented here</p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowContractModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                Create Contract
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplierCoordinatorView;