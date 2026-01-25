/**
 * Approval Queue Component
 * Displays purchase order approval queue with filtering, sorting, and bulk actions
 */

import React, { useState, useEffect } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../Loading/LoadingSpinner';
import ApprovalModal from './ApprovalModal';
import EmergencyPurchaseModal from './EmergencyPurchaseModal';
import procurementService, { 
  PendingApproval, 
  QueueFilter, 
  ApprovalDecision,
  EmergencyPurchaseRequest 
} from '../../../services/procurementService';

const ApprovalQueue: React.FC = () => {
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

  useEffect(() => {
    loadApprovalQueue();
  }, [filters]);

  // Handle approval decision
  const handleApprovalDecision = async (orderId: string, decision: ApprovalDecision) => {
    try {
      await procurementService.processApproval(orderId, decision);
      showNotification(
        `Purchase order ${decision.action === 'approve' ? 'approved' : 'rejected'} successfully`,
        'success'
      );
      
      // Refresh the queue
      await loadApprovalQueue();
      setShowApprovalModal(false);
      setSelectedApproval(null);
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
      
      // Refresh the queue to show the new emergency request
      await loadApprovalQueue();
      setShowEmergencyModal(false);
    } catch (error) {
      console.error('Error submitting emergency purchase:', error);
      showNotification('Failed to submit emergency purchase request', 'error');
    }
  };

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<QueueFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Get priority badge color
  const getPriorityBadgeColor = (priority: string) => {
    switch (priority) {
      case 'emergency':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get risk badge color
  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Purchase Order Approval Queue</h2>
          <p className="text-sm text-gray-600 mt-1">
            {approvals.length} pending approval{approvals.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowEmergencyModal(true)}
          className="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span>Emergency Purchase</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              value={filters.priority?.[0] || ''}
              onChange={(e) => handleFilterChange({ 
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Budget Category</label>
            <select
              value={filters.budgetCategory?.[0] || ''}
              onChange={(e) => handleFilterChange({ 
                budgetCategory: e.target.value ? [e.target.value] : undefined 
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="operations">Operations</option>
              <option value="maintenance">Maintenance</option>
              <option value="equipment">Equipment</option>
              <option value="supplies">Supplies</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={filters.sortBy || 'created_date'}
              onChange={(e) => handleFilterChange({ 
                sortBy: e.target.value as QueueFilter['sortBy']
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
              onChange={(e) => handleFilterChange({ 
                sortOrder: e.target.value as 'asc' | 'desc'
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
      </div>

      {/* Approval Queue Table */}
      {approvals.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Approvals</h3>
          <p className="text-gray-600">All purchase orders have been processed.</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {approvals.map((approval) => (
              <li key={approval.orderId} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityBadgeColor(approval.purchaseOrder.priority)}`}>
                          {approval.purchaseOrder.priority}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          Order #{approval.purchaseOrder.orderId}
                        </p>
                        <p className="text-sm text-gray-500">
                          {approval.purchaseOrder.supplierName} • {approval.purchaseOrder.items.length} item{approval.purchaseOrder.items.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                      <span className="font-medium text-gray-900">
                        {formatCurrency(approval.purchaseOrder.totalAmount)}
                      </span>
                      <span>•</span>
                      <span>{approval.purchaseOrder.budgetCategory}</span>
                      <span>•</span>
                      <span>{approval.daysWaiting} day{approval.daysWaiting !== 1 ? 's' : ''} waiting</span>
                      <span>•</span>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskBadgeColor(approval.riskAssessment.overallRisk)}`}>
                        {approval.riskAssessment.overallRisk} risk
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setSelectedApproval(approval);
                        setShowApprovalModal(true);
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition-colors duration-200"
                    >
                      Review
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && selectedApproval && (
        <ApprovalModal
          approval={selectedApproval}
          onApprove={(decision) => handleApprovalDecision(selectedApproval.orderId, decision)}
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

export default ApprovalQueue;