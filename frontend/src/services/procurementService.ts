/**
 * Procurement Service
 * Handles purchase order management, approval workflows, and financial operations
 */

import { apiRequest } from '../utils/apiUtils';

export interface PurchaseOrder {
  orderId: string;
  requesterId: string;
  requesterName: string;
  supplierId: string;
  supplierName: string;
  items: PurchaseOrderItem[];
  totalAmount: number;
  budgetCategory: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled';
  priority: 'normal' | 'high' | 'emergency';
  workflowId: string;
  createdAt: string;
  approvedBy?: string;
  approvedAt?: string;
  rejectedBy?: string;
  rejectedAt?: string;
  justification?: string;
  emergencyReason?: string;
  budgetValidation?: BudgetValidation;
  mlForecastVariance?: MLForecastVariance;
}

export interface PurchaseOrderItem {
  itemId: string;
  itemName: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  specifications?: string;
}

export interface BudgetValidation {
  isValid: boolean;
  availableBudget: number;
  requestedAmount: number;
  remainingAfterApproval: number;
  budgetUtilization: number;
  warnings: string[];
}

export interface MLForecastVariance {
  forecastedSpend: number;
  actualSpend: number;
  variance: number;
  variancePercentage: number;
  trend: 'above_forecast' | 'below_forecast' | 'on_track';
  confidence: number;
}

export interface ApprovalDecision {
  action: 'approve' | 'reject';
  justification: string;
  conditions?: string[];
}

export interface PendingApproval {
  orderId: string;
  purchaseOrder: PurchaseOrder;
  submittedAt: string;
  daysWaiting: number;
  riskAssessment: RiskAssessment;
}

export interface RiskAssessment {
  financialRisk: 'low' | 'medium' | 'high';
  supplierRisk: 'low' | 'medium' | 'high';
  budgetRisk: 'low' | 'medium' | 'high';
  overallRisk: 'low' | 'medium' | 'high';
  riskFactors: string[];
}

export interface QueueFilter {
  status?: string[];
  priority?: string[];
  budgetCategory?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  amountRange?: {
    min: number;
    max: number;
  };
  sortBy?: 'created_date' | 'amount' | 'priority' | 'days_waiting';
  sortOrder?: 'asc' | 'desc';
}

export interface EmergencyPurchaseRequest {
  supplierId: string;
  items: PurchaseOrderItem[];
  totalAmount: number;
  budgetCategory: string;
  emergencyReason: string;
  businessJustification: string;
  expectedDelivery: string;
  alternativeOptions?: string;
}

export interface FinancialAuditEntry {
  auditId: string;
  orderId: string;
  action: string;
  performedBy: string;
  performedAt: string;
  amount: number;
  budgetCategory: string;
  details: any;
  ipAddress: string;
}

class ProcurementService {
  private baseUrl = process.env.REACT_APP_API_ENDPOINT || '';

  /**
   * Get approval queue for finance controllers
   */
  async getApprovalQueue(filters?: QueueFilter): Promise<PendingApproval[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.status?.length) {
          queryParams.append('status', filters.status.join(','));
        }
        if (filters.priority?.length) {
          queryParams.append('priority', filters.priority.join(','));
        }
        if (filters.budgetCategory?.length) {
          queryParams.append('budgetCategory', filters.budgetCategory.join(','));
        }
        if (filters.dateRange) {
          queryParams.append('startDate', filters.dateRange.start);
          queryParams.append('endDate', filters.dateRange.end);
        }
        if (filters.amountRange) {
          queryParams.append('minAmount', filters.amountRange.min.toString());
          queryParams.append('maxAmount', filters.amountRange.max.toString());
        }
        if (filters.sortBy) {
          queryParams.append('sortBy', filters.sortBy);
        }
        if (filters.sortOrder) {
          queryParams.append('sortOrder', filters.sortOrder);
        }
      }

      const url = `/api/procurement/approval-queue${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await apiRequest(url, {
        method: 'GET'
      });

      return response.approvals || [];
    } catch (error) {
      console.error('Error fetching approval queue:', error);
      throw new Error('Failed to fetch approval queue');
    }
  }

  /**
   * Get purchase order details
   */
  async getPurchaseOrder(orderId: string): Promise<PurchaseOrder> {
    try {
      const response = await apiRequest(`/api/procurement/orders/${orderId}`, {
        method: 'GET'
      });

      return response.order;
    } catch (error) {
      console.error('Error fetching purchase order:', error);
      throw new Error('Failed to fetch purchase order details');
    }
  }

  /**
   * Approve or reject a purchase order
   */
  async processApproval(orderId: string, decision: ApprovalDecision): Promise<void> {
    try {
      await apiRequest(`/api/procurement/orders/${orderId}/approve`, {
        method: 'POST',
        body: JSON.stringify(decision)
      });
    } catch (error) {
      console.error('Error processing approval:', error);
      throw new Error('Failed to process approval decision');
    }
  }

  /**
   * Submit emergency purchase request
   */
  async submitEmergencyPurchase(request: EmergencyPurchaseRequest): Promise<{ workflowId: string; orderId: string }> {
    try {
      const response = await apiRequest('/api/procurement/emergency-purchase', {
        method: 'POST',
        body: JSON.stringify(request)
      });

      return {
        workflowId: response.workflowId,
        orderId: response.orderId
      };
    } catch (error) {
      console.error('Error submitting emergency purchase:', error);
      throw new Error('Failed to submit emergency purchase request');
    }
  }

  /**
   * Get financial audit log
   */
  async getFinancialAuditLog(
    timeRange: { start: string; end: string },
    filters?: {
      orderId?: string;
      budgetCategory?: string;
      performedBy?: string;
      action?: string;
    }
  ): Promise<FinancialAuditEntry[]> {
    try {
      const queryParams = new URLSearchParams({
        startDate: timeRange.start,
        endDate: timeRange.end
      });

      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) {
            queryParams.append(key, value);
          }
        });
      }

      const response = await apiRequest(`/api/procurement/audit-log?${queryParams.toString()}`, {
        method: 'GET'
      });

      return response.auditEntries || [];
    } catch (error) {
      console.error('Error fetching financial audit log:', error);
      throw new Error('Failed to fetch financial audit log');
    }
  }

  /**
   * Export financial audit data
   */
  async exportAuditData(
    timeRange: { start: string; end: string },
    format: 'csv' | 'xlsx' | 'pdf' = 'csv'
  ): Promise<Blob> {
    try {
      const queryParams = new URLSearchParams({
        startDate: timeRange.start,
        endDate: timeRange.end,
        format
      });

      const response = await fetch(`${this.baseUrl}/api/procurement/audit-export?${queryParams.toString()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      return await response.blob();
    } catch (error) {
      console.error('Error exporting audit data:', error);
      throw new Error('Failed to export audit data');
    }
  }

  /**
   * Validate budget availability for purchase order
   */
  async validateBudget(amount: number, budgetCategory: string): Promise<BudgetValidation> {
    try {
      const response = await apiRequest('/api/procurement/validate-budget', {
        method: 'POST',
        body: JSON.stringify({
          amount,
          budgetCategory
        })
      });

      return response.validation;
    } catch (error) {
      console.error('Error validating budget:', error);
      throw new Error('Failed to validate budget availability');
    }
  }

  /**
   * Get ML forecast variance analysis
   */
  async getMLForecastVariance(
    budgetCategory: string,
    timeRange: { start: string; end: string }
  ): Promise<MLForecastVariance> {
    try {
      const queryParams = new URLSearchParams({
        budgetCategory,
        startDate: timeRange.start,
        endDate: timeRange.end
      });

      const response = await apiRequest(`/api/procurement/ml-forecast-variance?${queryParams.toString()}`, {
        method: 'GET'
      });

      return response.variance;
    } catch (error) {
      console.error('Error fetching ML forecast variance:', error);
      throw new Error('Failed to fetch ML forecast variance analysis');
    }
  }
}

export default new ProcurementService();