/**
 * Approval Queue View
 * Displays purchase order approval queue with filtering and sorting
 */

import React, { useState, useEffect } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../Loading/LoadingSpinner';
import procurementService, { 
  PendingApproval, 
  QueueFilter, 
  ApprovalDecision,
  PurchaseOrder,
  EmergencyPurchaseRequest
} from '../../../services/procurementService';
import ApprovalModal from './ApprovalModal';
import EmergencyPurchaseModal from './EmergencyPurchaseModal';

const ApprovalQueueView: React.FC = () => {
  const { showNotification } = useNotification();
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [filters, setFilters] = useState<QueueFilter>({
    sortBy: 'created_date',
    sortOrder: 'desc'
  });

  // Load approval queue
  useEffect(() => {
    loadApprovalQueue();
  }, [filters]);

  const loadApprovalQueue = async () => {
    try {
      setIsLoading(true);
      const data = await procurementService.getApprovalQueue(filters);
      setApprovals(data);
    } catch (error) {
      console.error('Error loading approval queue:', error);
      showNotification('Failed to load approval queue', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle approval decision
  const handleApprovalDecision = async (decision: ApprovalDecision) => {
    if (!selectedApproval) return;

    try {
      await procurementService.processApproval(selectedApproval.orderId, decision);
      showNotification(
        `Purchase order ${decision.action === 'approve' ? 'approved' : 'rejected'} successfully`,
        'success'
      );
      setShowApprovalModal(false);
      setSelectedApproval(null);
      await loadApprovalQueue(); // Refresh the queue
    } catch (error) {
      console.error('Error processing approval:', error);
      showNotification('Failed to process approval decision', 'error');
    }
  };

  // Handle emergency purchase submission
  const handleEmergencyPurchase = async (request: EmergencyPurchaseRequest) => {
    try {
      const result = await procurementService.submitEmergencyPurchase(request);
      showNotification(
        `Emergency purchase request submitted successfully. Order ID: ${result.orderId}`,
        'success'
      );
      setShowEmergencyModal(false);
      await loadApprovalQueue(); // Refresh to show new request
    } catch (error) {
      console.error('Error submitting emergency purchase:', error);
      showNotification('Failed to submit emergency purchase request', 'error');
    }
  };

  // Get risk color class
  const getRiskColorClass = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get priority color class
  const getPriorityColorClass = (priority: string) => {
    switch (priority) {
      case 'emergency': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'normal': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="text-gray-600 mt-4">Loading approval queue...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Purchase Order Approval Queue</h2>
          <p className="text-gray-600 mt-1">
            {approvals.length} pending approval{approvals.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowEmergencyModal(true)}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span>Emergency Purchase</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              value={filters.priority?.[0] || ''}
              onChange={(e) => setFilters({
                ...filters,
                priority: e.target.value ? [e.target.value] : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="emergency">Emergency</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amount Range</label>
            <select
              onChange={(e) => {
                const value = e.target.value;
                if (value) {
                  const [min, max] = value.split('-').map(Number);
                  setFilters({
                    ...filters,
                    amountRange: { min, max: max || Infinity }
                  });
                } else {
                  setFilters({
                    ...filters,
                    amountRange: undefined
                  });
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Amounts</option>
              <option value="0-1000">$0 - $1,000</option>
              <option value="1000-5000">$1,000 - $5,000</option>
              <option value="5000-10000">$5,000 - $10,000</option>
              <option value="10000">$10,000+</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={filters.sortBy || 'created_date'}
              onChange={(e) => setFilters({
                ...filters,
                sortBy: e.target.value as any
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="created_date">Date Created</option>
              <option value="amount">Amount</option>
              <option value="priority">Priority</option>
              <option value="days_waiting">Days Waiting</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Order</label>
            <select
              value={filters.sortOrder || 'desc'}
              onChange={(e) => setFilters({
                ...filters,
                sortOrder: e.target.value as 'asc' | 'desc'
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {/* Approval Queue Table */}
      {approvals.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Approvals</h3>
          <p className="text-gray-600">All purchase orders have been processed.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Supplier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Waiting
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {approvals.map((approval) => (
                  <tr key={approval.orderId} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          Order #{approval.orderId.slice(-8)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {approval.purchaseOrder.items.length} item{approval.purchaseOrder.items.length !== 1 ? 's' : ''}
                        </div>
                        <div className="text-sm text-gray-500">
                          Requested by: {approval.purchaseOrder.requesterName}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{approval.purchaseOrder.supplierName}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        ${approval.purchaseOrder.totalAmount.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500">
                        {approval.purchaseOrder.budgetCategory}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColorClass(approval.purchaseOrder.priority)}`}>
                        {approval.purchaseOrder.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColorClass(approval.riskAssessment.overallRisk)}`}>
                        {approval.riskAssessment.overallRisk}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {approval.daysWaiting} day{approval.daysWaiting !== 1 ? 's' : ''}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => {
                          setSelectedApproval(approval);
                          setShowApprovalModal(true);
                        }}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && selectedApproval && (
        <ApprovalModal
          approval={selectedApproval}
          onApprove={handleApprovalDecision}
          onClose={() => {
            setShowApprovalModal(false);
            setSelectedApproval(null);
          }}
        />
      )}

      {/* Emergency Purchase Modal */}
      {showEmergencyModal && (
        <EmergencyPurchaseModal
          onSubmit={handleEmergencyPurchase}
          onClose={() => setShowEmergencyModal(false)}
        />
      )}
    </div>
  );
};

export default ApprovalQueueView;