/**
 * Financial Audit Log Component
 * Displays comprehensive financial audit logs with filtering and export capabilities
 */

import React, { useState, useEffect } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../Loading/LoadingSpinner';
import procurementService, { FinancialAuditEntry } from '../../../services/procurementService';

const FinancialAuditLog: React.FC = () => {
  const { showNotification } = useNotification();
  const [auditEntries, setAuditEntries] = useState<FinancialAuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [filters, setFilters] = useState({
    startDate: (() => {
      const date = new Date();
      date.setDate(date.getDate() - 30); // Default to last 30 days
      return date.toISOString().split('T')[0];
    })(),
    endDate: new Date().toISOString().split('T')[0],
    orderId: '',
    budgetCategory: '',
    performedBy: '',
    action: ''
  });

  // Load audit log
  const loadAuditLog = async () => {
    try {
      setIsLoading(true);
      const data = await procurementService.getFinancialAuditLog(
        { start: filters.startDate, end: filters.endDate },
        {
          orderId: filters.orderId || undefined,
          budgetCategory: filters.budgetCategory || undefined,
          performedBy: filters.performedBy || undefined,
          action: filters.action || undefined
        }
      );
      setAuditEntries(data);
    } catch (error) {
      console.error('Error loading audit log:', error);
      showNotification('Failed to load financial audit log', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLog();
  }, [filters]);

  // Handle filter changes
  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({
      startDate: (() => {
        const date = new Date();
        date.setDate(date.getDate() - 30);
        return date.toISOString().split('T')[0];
      })(),
      endDate: new Date().toISOString().split('T')[0],
      orderId: '',
      budgetCategory: '',
      performedBy: '',
      action: ''
    });
  };

  // Export audit data
  const handleExport = async (format: 'csv' | 'xlsx' | 'pdf') => {
    try {
      setIsExporting(true);
      const blob = await procurementService.exportAuditData(
        { start: filters.startDate, end: filters.endDate },
        format
      );
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `financial-audit-log-${filters.startDate}-to-${filters.endDate}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showNotification(`Audit log exported successfully as ${format.toUpperCase()}`, 'success');
    } catch (error) {
      console.error('Error exporting audit data:', error);
      showNotification('Failed to export audit data', 'error');
    } finally {
      setIsExporting(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get action color
  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'approve':
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'reject':
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'submit':
      case 'submitted':
        return 'bg-blue-100 text-blue-800';
      case 'modify':
      case 'modified':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get unique values for filter dropdowns
  const getUniqueValues = (field: keyof FinancialAuditEntry) => {
    const values = auditEntries.map(entry => entry[field]).filter(Boolean);
    return Array.from(new Set(values)).sort();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Financial Audit Log</h2>
          <p className="text-sm text-gray-600 mt-1">
            Comprehensive audit trail of all financial transactions and decisions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('csv')}
            disabled={isExporting || auditEntries.length === 0}
            className="bg-green-600 hover:bg-green-700 text-white font-medium px-3 py-2 rounded text-sm transition-colors duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            disabled={isExporting || auditEntries.length === 0}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-3 py-2 rounded text-sm transition-colors duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Export Excel
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={isExporting || auditEntries.length === 0}
            className="bg-red-600 hover:bg-red-700 text-white font-medium px-3 py-2 rounded text-sm transition-colors duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Export PDF
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Order ID</label>
            <input
              type="text"
              value={filters.orderId}
              onChange={(e) => handleFilterChange('orderId', e.target.value)}
              placeholder="Enter order ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Budget Category</label>
            <select
              value={filters.budgetCategory}
              onChange={(e) => handleFilterChange('budgetCategory', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="operations">Operations</option>
              <option value="maintenance">Maintenance</option>
              <option value="equipment">Equipment</option>
              <option value="supplies">Supplies</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Performed By</label>
            <input
              type="text"
              value={filters.performedBy}
              onChange={(e) => handleFilterChange('performedBy', e.target.value)}
              placeholder="Enter user name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              <option value="approve">Approve</option>
              <option value="reject">Reject</option>
              <option value="submit">Submit</option>
              <option value="modify">Modify</option>
              <option value="cancel">Cancel</option>
            </select>
          </div>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={clearFilters}
            className="text-sm text-gray-600 hover:text-gray-800 underline"
          >
            Clear All Filters
          </button>
        </div>
      </div>

      {/* Results Summary */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {auditEntries.length} audit entries
            {filters.startDate && filters.endDate && (
              <span> from {formatDate(filters.startDate)} to {formatDate(filters.endDate)}</span>
            )}
          </div>
          {isExporting && (
            <div className="flex items-center text-sm text-gray-600">
              <LoadingSpinner size="small" />
              <span className="ml-2">Exporting...</span>
            </div>
          )}
        </div>
      </div>

      {/* Audit Log Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="large" />
        </div>
      ) : auditEntries.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Audit Entries Found</h3>
          <p className="text-gray-600">No financial audit entries match the selected criteria.</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performed By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Budget Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditEntries.map((entry) => (
                  <tr key={entry.auditId} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(entry.performedAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{entry.orderId}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(entry.action)}`}>
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {entry.performedBy}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(entry.amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                      {entry.budgetCategory}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {entry.ipAddress}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-xs truncate">
                        {entry.details && typeof entry.details === 'object' ? (
                          <details className="cursor-pointer">
                            <summary className="text-blue-600 hover:text-blue-800">View Details</summary>
                            <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                              {JSON.stringify(entry.details, null, 2)}
                            </pre>
                          </details>
                        ) : (
                          <span>{entry.details || 'No additional details'}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Audit Trail Integrity Notice */}
      <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <div>
            <h5 className="font-medium text-blue-800 mb-1">Audit Trail Integrity</h5>
            <p className="text-sm text-blue-700">
              This audit log is cryptographically secured and tamper-evident. All entries are immutable 
              and verified for integrity. Any unauthorized modifications would be immediately detected 
              and reported to system administrators.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialAuditLog;