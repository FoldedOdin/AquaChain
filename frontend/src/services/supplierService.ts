import { apiClient } from './apiClient';
import { Supplier, PurchaseOrder, CreateSupplierRequest, CreatePurchaseOrderRequest } from '../types/supplier';

export const supplierService = {
  // Get all suppliers with optional filters
  async getSuppliers(filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams(filters || {});
      const response = await apiClient.get(`/api/suppliers?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      return {
        success: false,
        error: 'Failed to fetch suppliers'
      };
    }
  },

  // Create new supplier
  async createSupplier(supplierData: CreateSupplierRequest) {
    try {
      const response = await apiClient.post('/api/suppliers', supplierData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error creating supplier:', error);
      return {
        success: false,
        error: 'Failed to create supplier'
      };
    }
  },

  // Update supplier
  async updateSupplier(supplierId: string, updates: Partial<Supplier>) {
    try {
      const response = await apiClient.put(`/api/suppliers/${supplierId}`, updates);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating supplier:', error);
      return {
        success: false,
        error: 'Failed to update supplier'
      };
    }
  },

  // Get supplier by ID
  async getSupplier(supplierId: string) {
    try {
      const response = await apiClient.get(`/api/suppliers/${supplierId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching supplier:', error);
      return {
        success: false,
        error: 'Failed to fetch supplier'
      };
    }
  },

  // Get supplier performance metrics
  async getSupplierPerformance(supplierId: string) {
    try {
      const response = await apiClient.get(`/api/suppliers/${supplierId}/performance`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching supplier performance:', error);
      return {
        success: false,
        error: 'Failed to fetch supplier performance'
      };
    }
  },

  // Get all purchase orders with optional filters
  async getPurchaseOrders(filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams(filters || {});
      const response = await apiClient.get(`/api/purchase-orders?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching purchase orders:', error);
      return {
        success: false,
        error: 'Failed to fetch purchase orders'
      };
    }
  },

  // Create new purchase order
  async createPurchaseOrder(orderData: CreatePurchaseOrderRequest) {
    try {
      const response = await apiClient.post('/api/purchase-orders', orderData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error creating purchase order:', error);
      return {
        success: false,
        error: 'Failed to create purchase order'
      };
    }
  },

  // Update purchase order status
  async updatePurchaseOrderStatus(poId: string, status: string, notes?: string) {
    try {
      const response = await apiClient.put(`/api/purchase-orders/${poId}/status`, {
        status,
        notes
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating purchase order status:', error);
      return {
        success: false,
        error: 'Failed to update purchase order status'
      };
    }
  },

  // Get purchase order by ID
  async getPurchaseOrder(poId: string) {
    try {
      const response = await apiClient.get(`/api/purchase-orders/${poId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching purchase order:', error);
      return {
        success: false,
        error: 'Failed to fetch purchase order'
      };
    }
  },

  // Approve purchase order
  async approvePurchaseOrder(poId: string, notes?: string) {
    try {
      const response = await apiClient.post(`/api/purchase-orders/${poId}/approve`, {
        notes
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error approving purchase order:', error);
      return {
        success: false,
        error: 'Failed to approve purchase order'
      };
    }
  },

  // Cancel purchase order
  async cancelPurchaseOrder(poId: string, reason: string) {
    try {
      const response = await apiClient.post(`/api/purchase-orders/${poId}/cancel`, {
        reason
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error cancelling purchase order:', error);
      return {
        success: false,
        error: 'Failed to cancel purchase order'
      };
    }
  },

  // Get supplier analytics
  async getSupplierAnalytics(timeRange: string = '30d') {
    try {
      const response = await apiClient.get(`/api/suppliers/analytics?timeRange=${timeRange}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching supplier analytics:', error);
      return {
        success: false,
        error: 'Failed to fetch supplier analytics'
      };
    }
  },

  // Export supplier data
  async exportSuppliers(format: 'csv' | 'xlsx' = 'csv') {
    try {
      const response = await apiClient.get(`/api/suppliers/export?format=${format}`, {
        expectBlob: true
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `suppliers-${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return {
        success: true,
        data: 'Export completed'
      };
    } catch (error) {
      console.error('Error exporting suppliers:', error);
      return {
        success: false,
        error: 'Failed to export suppliers'
      };
    }
  }
};