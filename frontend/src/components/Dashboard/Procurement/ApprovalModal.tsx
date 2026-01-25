/**
 * Approval Modal Component
 * Modal for approving/rejecting purchase orders with mandatory justification
 */

import React, { useState, useEffect } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../Loading/LoadingSpinner';
import budgetService from '../../../services/budgetService';
import procurementService, { 
  PendingApproval, 
  ApprovalDecision, 
  BudgetValidation,
  MLForecastVariance 
} from '../../../services/procurementService';

interface ApprovalModalProps {
  approval: PendingApproval;
  onApprove: (decision: ApprovalDecision) => void;
  onClose: () => void;
}

const ApprovalModal: React.FC<ApprovalModalProps> = ({
  approval,
  onApprove,
  onClose
}) => {
  const { showNotification } = useNotification();
  const [decision, setDecision] = useState<'approve' | 'reject' | null>(null);
  const [justification, setJustification] = useState('');
  const [conditions, setConditions] = useState<string[]>([]);
  const [newCondition, setNewCondition] = useState('');
  const [budgetValidation, setBudgetValidation] = useState<BudgetValidation | null>(null);
  const [mlVariance, setMLVariance] = useState<MLForecastVariance | null>(null);
  const [isLoadingValidation, setIsLoadingValidation] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load budget validation and ML forecast data
  useEffect(() => {
    const loadValidationData = async () => {
      try {
        setIsLoadingValidation(true);
        
        // Load budget validation
        const validation = await procurementService.validateBudget(
          approval.purchaseOrder.totalAmount,
          approval.purchaseOrder.budgetCategory
        );
        setBudgetValidation(validation);

        // Load ML forecast variance
        const currentDate = new Date();
        const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        
        const variance = await procurementService.getMLForecastVariance(
          approval.purchaseOrder.budgetCategory,
          {
            start: startOfMonth.toISOString().split('T')[0],
            end: endOfMonth.toISOString().split('T')[0]
          }
        );
        setMLVariance(variance);
      } catch (error) {
        console.error('Error loading validation data:', error);
        showNotification('Failed to load budget validation data', 'error');
      } finally {
        setIsLoadingValidation(false);
      }
    };

    loadValidationData();
  }, [approval, showNotification]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!decision) {
      showNotification('Please select approve or reject', 'error');
      return;
    }

    if (!justification.trim()) {
      showNotification('Justification is required', 'error');
      return;
    }

    if (decision === 'approve' && budgetValidation && !budgetValidation.isValid) {
      showNotification('Cannot approve: Budget validation failed', 'error');
      return;
    }

    try {
      setIsSubmitting(true);
      
      const approvalDecision: ApprovalDecision = {
        action: decision,
        justification: justification.trim(),
        conditions: conditions.length > 0 ? conditions : undefined
      };

      await onApprove(approvalDecision);
    } catch (error) {
      console.error('Error submitting approval:', error);
      showNotification('Failed to submit approval decision', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Add condition
  const addCondition = () => {
    if (newCondition.trim() && !conditions.includes(newCondition.trim())) {
      setConditions([...conditions, newCondition.trim()]);
      setNewCondition('');
    }
  };

  // Remove condition
  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Get risk color
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      default: return 'text-green-600';
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Purchase Order Approval - #{approval.purchaseOrder.orderId}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {isLoadingValidation ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="large" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Purchase Order Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column - Order Details */}
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Order Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Supplier:</span>
                      <span className="font-medium">{approval.purchaseOrder.supplierName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Requester:</span>
                      <span className="font-medium">{approval.purchaseOrder.requesterName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Amount:</span>
                      <span className="font-medium text-lg">{formatCurrency(approval.purchaseOrder.totalAmount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Budget Category:</span>
                      <span className="font-medium">{approval.purchaseOrder.budgetCategory}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Priority:</span>
                      <span className={`font-medium capitalize ${
                        approval.purchaseOrder.priority === 'emergency' ? 'text-red-600' :
                        approval.purchaseOrder.priority === 'high' ? 'text-orange-600' : 'text-gray-600'
                      }`}>
                        {approval.purchaseOrder.priority}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Days Waiting:</span>
                      <span className="font-medium">{approval.daysWaiting} days</span>
                    </div>
                  </div>
                </div>

                {/* Items List */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Items ({approval.purchaseOrder.items.length})</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {approval.purchaseOrder.items.map((item, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <div>
                          <div className="font-medium">{item.itemName}</div>
                          <div className="text-gray-600">Qty: {item.quantity} @ {formatCurrency(item.unitPrice)}</div>
                        </div>
                        <div className="font-medium">{formatCurrency(item.totalPrice)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column - Validation & Risk */}
              <div className="space-y-4">
                {/* Budget Validation */}
                {budgetValidation && (
                  <div className={`p-4 rounded-lg ${budgetValidation.isValid ? 'bg-green-50' : 'bg-red-50'}`}>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                      <svg className={`w-5 h-5 mr-2 ${budgetValidation.isValid ? 'text-green-600' : 'text-red-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={budgetValidation.isValid ? "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" : "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"} />
                      </svg>
                      Budget Validation
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Available Budget:</span>
                        <span className="font-medium">{formatCurrency(budgetValidation.availableBudget)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Requested Amount:</span>
                        <span className="font-medium">{formatCurrency(budgetValidation.requestedAmount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Remaining After:</span>
                        <span className="font-medium">{formatCurrency(budgetValidation.remainingAfterApproval)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Utilization:</span>
                        <span className="font-medium">{budgetValidation.budgetUtilization.toFixed(1)}%</span>
                      </div>
                    </div>
                    {budgetValidation.warnings.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {budgetValidation.warnings.map((warning, index) => (
                          <div key={index} className="text-sm text-amber-700 flex items-start">
                            <svg className="w-4 h-4 mr-1 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                            {warning}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* ML Forecast Variance */}
                {mlVariance && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      ML Forecast Analysis (Read-Only)
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Forecasted Spend:</span>
                        <span className="font-medium">{formatCurrency(mlVariance.forecastedSpend)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Actual Spend:</span>
                        <span className="font-medium">{formatCurrency(mlVariance.actualSpend)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Variance:</span>
                        <span className={`font-medium ${mlVariance.variance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {mlVariance.variance >= 0 ? '+' : ''}{formatCurrency(mlVariance.variance)} ({mlVariance.variancePercentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Trend:</span>
                        <span className={`font-medium capitalize ${
                          mlVariance.trend === 'above_forecast' ? 'text-red-600' :
                          mlVariance.trend === 'below_forecast' ? 'text-green-600' : 'text-blue-600'
                        }`}>
                          {mlVariance.trend.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Confidence:</span>
                        <span className="font-medium">{(mlVariance.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Risk Assessment */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Risk Assessment</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Financial Risk:</span>
                      <span className={`font-medium capitalize ${getRiskColor(approval.riskAssessment.financialRisk)}`}>
                        {approval.riskAssessment.financialRisk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Supplier Risk:</span>
                      <span className={`font-medium capitalize ${getRiskColor(approval.riskAssessment.supplierRisk)}`}>
                        {approval.riskAssessment.supplierRisk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Budget Risk:</span>
                      <span className={`font-medium capitalize ${getRiskColor(approval.riskAssessment.budgetRisk)}`}>
                        {approval.riskAssessment.budgetRisk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Overall Risk:</span>
                      <span className={`font-medium capitalize ${getRiskColor(approval.riskAssessment.overallRisk)}`}>
                        {approval.riskAssessment.overallRisk}
                      </span>
                    </div>
                  </div>
                  {approval.riskAssessment.riskFactors.length > 0 && (
                    <div className="mt-3">
                      <div className="text-sm font-medium text-gray-700 mb-1">Risk Factors:</div>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {approval.riskAssessment.riskFactors.map((factor, index) => (
                          <li key={index} className="flex items-start">
                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Decision Section */}
            <div className="border-t pt-6">
              <h4 className="font-medium text-gray-900 mb-4">Approval Decision</h4>
              
              {/* Decision Buttons */}
              <div className="flex space-x-4 mb-4">
                <button
                  type="button"
                  onClick={() => setDecision('approve')}
                  disabled={budgetValidation && !budgetValidation.isValid}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors duration-200 ${
                    decision === 'approve'
                      ? 'bg-green-600 text-white'
                      : budgetValidation && !budgetValidation.isValid
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => setDecision('reject')}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors duration-200 ${
                    decision === 'reject'
                      ? 'bg-red-600 text-white'
                      : 'bg-red-100 text-red-700 hover:bg-red-200'
                  }`}
                >
                  Reject
                </button>
              </div>

              {/* Justification */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Justification <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Provide detailed justification for your decision..."
                  required
                />
              </div>

              {/* Conditions (for approvals) */}
              {decision === 'approve' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Approval Conditions (Optional)
                  </label>
                  <div className="flex space-x-2 mb-2">
                    <input
                      type="text"
                      value={newCondition}
                      onChange={(e) => setNewCondition(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Add a condition..."
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCondition())}
                    />
                    <button
                      type="button"
                      onClick={addCondition}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Add
                    </button>
                  </div>
                  {conditions.length > 0 && (
                    <div className="space-y-2">
                      {conditions.map((condition, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md">
                          <span className="text-sm">{condition}</span>
                          <button
                            type="button"
                            onClick={() => removeCondition(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!decision || !justification.trim() || isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSubmitting && <LoadingSpinner size="small" />}
                <span>Submit Decision</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ApprovalModal;