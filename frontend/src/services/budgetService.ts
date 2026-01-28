/**
 * Budget Service
 * Handles budget allocation, utilization tracking, and financial oversight
 */

import { apiRequest } from '../utils/apiUtils';

export interface BudgetAllocation {
  budgetId: string;
  category: string;
  period: string; // YYYY-MM format
  allocatedAmount: number;
  utilizedAmount: number;
  remainingAmount: number;
  utilizationPercentage: number;
  status: 'active' | 'exhausted' | 'frozen' | 'expired';
  lastUpdated: string;
  updatedBy: string;
}

export interface BudgetUtilization {
  category: string;
  period: string;
  allocatedAmount: number;
  utilizedAmount: number;
  remainingAmount: number;
  utilizationPercentage: number;
  projectedUtilization: number;
  projectedSpend: number; // Alias for projectedUtilization for UI compatibility
  trend: 'increasing' | 'decreasing' | 'stable';
  transactions: BudgetTransaction[];
}

export interface BudgetTransaction {
  transactionId: string;
  orderId: string;
  amount: number;
  type: 'allocation' | 'utilization' | 'adjustment' | 'reallocation';
  description: string;
  performedBy: string;
  timestamp: string;
  approvedBy?: string;
}

export interface SpendForecastComparison {
  category: string;
  period: string;
  forecastedSpend: number;
  actualSpend: number;
  forecastedAmount: number; // Alias for forecastedSpend for UI compatibility
  actualAmount: number; // Alias for actualSpend for UI compatibility
  variance: number;
  variancePercentage: number;
  trend: 'above_forecast' | 'below_forecast' | 'on_track';
  confidence: number; // Confidence level (0-1) for forecast accuracy
  monthlyBreakdown: MonthlySpendData[];
}

export interface MonthlySpendData {
  month: string;
  forecasted: number;
  actual: number;
  variance: number;
}

export interface BudgetAlert {
  alertId: string;
  category: string;
  budgetCategory: string; // Alias for category for UI compatibility
  alertType: 'threshold_warning' | 'threshold_critical' | 'exhausted' | 'overspend';
  threshold: number;
  currentUtilization: number;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  createdAt: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

export interface BudgetReallocationRequest {
  fromCategory: string;
  toCategory: string;
  amount: number;
  reason: string;
  businessJustification: string;
  expectedImpact: string;
  approvalRequired: boolean;
}

export interface SupplierFinancialRisk {
  supplierId: string;
  supplierName: string;
  totalExposure: number;
  paymentTerms: string;
  creditRating: string;
  riskScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  riskFactors: string[];
  recommendedActions: string[];
  lastAssessment: string;
}

export interface FinancialOverview {
  totalBudget: number;
  totalUtilized: number;
  totalRemaining: number;
  overallUtilization: number;
  categoriesAtRisk: number;
  pendingApprovals: number;
  pendingAmount: number;
  monthlyTrend: {
    month: string;
    budgetUtilization: number;
    approvalVolume: number;
    averageOrderValue: number;
  }[];
}

class BudgetService {
  private baseUrl = process.env.REACT_APP_API_ENDPOINT || '';

  /**
   * Get budget allocations for all categories
   */
  async getBudgetAllocations(period?: string): Promise<BudgetAllocation[]> {
    try {
      const queryParams = period ? `?period=${period}` : '';
      const response = await apiRequest(`/api/budget/allocations${queryParams}`, {
        method: 'GET'
      });

      return response.allocations || [];
    } catch (error) {
      console.error('Error fetching budget allocations:', error);
      throw new Error('Failed to fetch budget allocations');
    }
  }

  /**
   * Get budget utilization for specific category
   */
  async getBudgetUtilization(category: string, period?: string): Promise<BudgetUtilization> {
    try {
      const queryParams = new URLSearchParams({ category });
      if (period) {
        queryParams.append('period', period);
      }

      const response = await apiRequest(`/api/budget/utilization?${queryParams.toString()}`, {
        method: 'GET'
      });

      return response.utilization;
    } catch (error) {
      console.error('Error fetching budget utilization:', error);
      throw new Error('Failed to fetch budget utilization');
    }
  }

  /**
   * Get budget utilization for all categories
   */
  async getAllBudgetUtilizations(period?: string): Promise<BudgetUtilization[]> {
    try {
      const queryParams = period ? `?period=${period}` : '';
      const response = await apiRequest(`/api/budget/utilizations${queryParams}`, {
        method: 'GET'
      });

      return response.utilizations || [];
    } catch (error) {
      console.error('Error fetching budget utilizations:', error);
      throw new Error('Failed to fetch budget utilizations');
    }
  }

  /**
   * Get spend vs forecast comparison
   */
  async getSpendForecastComparison(
    timeRange: { start: string; end: string },
    categories?: string[]
  ): Promise<SpendForecastComparison[]> {
    try {
      const queryParams = new URLSearchParams({
        startDate: timeRange.start,
        endDate: timeRange.end
      });

      if (categories?.length) {
        queryParams.append('categories', categories.join(','));
      }

      const response = await apiRequest(`/api/budget/forecast-comparison?${queryParams.toString()}`, {
        method: 'GET'
      });

      return response.comparisons || [];
    } catch (error) {
      console.error('Error fetching spend forecast comparison:', error);
      throw new Error('Failed to fetch spend forecast comparison');
    }
  }

  /**
   * Get budget alerts
   */
  async getBudgetAlerts(acknowledged?: boolean): Promise<BudgetAlert[]> {
    try {
      const queryParams = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';
      const response = await apiRequest(`/api/budget/alerts${queryParams}`, {
        method: 'GET'
      });

      return response.alerts || [];
    } catch (error) {
      console.error('Error fetching budget alerts:', error);
      throw new Error('Failed to fetch budget alerts');
    }
  }

  /**
   * Acknowledge budget alert
   */
  async acknowledgeBudgetAlert(alertId: string): Promise<void> {
    try {
      await apiRequest(`/api/budget/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error acknowledging budget alert:', error);
      throw new Error('Failed to acknowledge budget alert');
    }
  }

  /**
   * Submit budget reallocation request
   */
  async submitBudgetReallocation(request: BudgetReallocationRequest): Promise<{ requestId: string }> {
    try {
      const response = await apiRequest('/api/budget/reallocation', {
        method: 'POST',
        body: JSON.stringify(request)
      });

      return { requestId: response.requestId };
    } catch (error) {
      console.error('Error submitting budget reallocation:', error);
      throw new Error('Failed to submit budget reallocation request');
    }
  }

  /**
   * Get supplier financial risk overview
   */
  async getSupplierFinancialRisk(): Promise<SupplierFinancialRisk[]> {
    try {
      const response = await apiRequest('/api/budget/supplier-risk', {
        method: 'GET'
      });

      return response.supplierRisks || [];
    } catch (error) {
      console.error('Error fetching supplier financial risk:', error);
      throw new Error('Failed to fetch supplier financial risk overview');
    }
  }

  /**
   * Get financial overview dashboard data
   */
  async getFinancialOverview(period?: string): Promise<FinancialOverview> {
    try {
      const queryParams = period ? `?period=${period}` : '';
      const response = await apiRequest(`/api/budget/overview${queryParams}`, {
        method: 'GET'
      });

      return response.overview;
    } catch (error) {
      console.error('Error fetching financial overview:', error);
      throw new Error('Failed to fetch financial overview');
    }
  }

  /**
   * Update budget allocation
   */
  async updateBudgetAllocation(
    category: string,
    amount: number,
    reason: string
  ): Promise<void> {
    try {
      await apiRequest(`/api/budget/allocations/${category}`, {
        method: 'PUT',
        body: JSON.stringify({
          amount,
          reason
        })
      });
    } catch (error) {
      console.error('Error updating budget allocation:', error);
      throw new Error('Failed to update budget allocation');
    }
  }

  /**
   * Export budget data
   */
  async exportBudgetData(
    timeRange: { start: string; end: string },
    categories?: string[],
    format: 'csv' | 'xlsx' | 'pdf' = 'csv'
  ): Promise<Blob> {
    try {
      const queryParams = new URLSearchParams({
        startDate: timeRange.start,
        endDate: timeRange.end,
        format
      });

      if (categories?.length) {
        queryParams.append('categories', categories.join(','));
      }

      const response = await fetch(`${this.baseUrl}/api/budget/export?${queryParams.toString()}`, {
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
      console.error('Error exporting budget data:', error);
      throw new Error('Failed to export budget data');
    }
  }
}

export default new BudgetService();