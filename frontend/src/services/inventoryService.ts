import { apiClient, ApiResponse } from './apiClient';
import { InventoryItem, InventoryAlert, CreateInventoryItemRequest, UpdateInventoryItemRequest } from '../types/inventory';

interface InventoryItemsResponse {
  items: InventoryItem[];
  count: number;
  low_stock_count: number;
  out_of_stock_count: number;
}

interface LowStockAlertsResponse {
  low_stock_items: InventoryAlert[];
}

interface InventoryServiceResponse<T> {
  success: true;
  data: T;
}

interface InventoryServiceError {
  success: false;
  error: string;
}

export const inventoryService = {
  // Get all inventory items with optional filters
  async getInventoryItems(filters?: Record<string, string>): Promise<InventoryServiceResponse<InventoryItemsResponse> | InventoryServiceError> {
    try {
      const params = new URLSearchParams(filters || {});
      const response: ApiResponse<InventoryItemsResponse> = await apiClient.get(`/api/inventory/items?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching inventory items:', error);
      return {
        success: false,
        error: 'Failed to fetch inventory items'
      };
    }
  },

  // Create new inventory item
  async createInventoryItem(itemData: CreateInventoryItemRequest) {
    try {
      const response = await apiClient.post('/api/inventory/items', itemData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error creating inventory item:', error);
      return {
        success: false,
        error: 'Failed to create inventory item'
      };
    }
  },

  // Update inventory item
  async updateInventoryItem(itemId: string, locationId: string, updates: UpdateInventoryItemRequest) {
    try {
      const response = await apiClient.put(`/api/inventory/items/${itemId}/${locationId}`, updates);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating inventory item:', error);
      return {
        success: false,
        error: 'Failed to update inventory item'
      };
    }
  },

  // Get low stock alerts
  async getLowStockAlerts(): Promise<InventoryServiceResponse<LowStockAlertsResponse> | InventoryServiceError> {
    try {
      const response: ApiResponse<LowStockAlertsResponse> = await apiClient.get('/api/inventory/alerts');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching low stock alerts:', error);
      return {
        success: false,
        error: 'Failed to fetch low stock alerts'
      };
    }
  },

  // Get inventory item by ID
  async getInventoryItem(itemId: string, locationId: string) {
    try {
      const response = await apiClient.get(`/api/inventory/items/${itemId}/${locationId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching inventory item:', error);
      return {
        success: false,
        error: 'Failed to fetch inventory item'
      };
    }
  },

  // Delete inventory item
  async deleteInventoryItem(itemId: string, locationId: string) {
    try {
      const response = await apiClient.delete(`/api/inventory/items/${itemId}/${locationId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error deleting inventory item:', error);
      return {
        success: false,
        error: 'Failed to delete inventory item'
      };
    }
  },

  // Bulk update inventory
  async bulkUpdateInventory(updates: Array<{itemId: string, locationId: string, updates: UpdateInventoryItemRequest}>) {
    try {
      const response = await apiClient.post('/api/inventory/bulk-update', { updates });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error bulk updating inventory:', error);
      return {
        success: false,
        error: 'Failed to bulk update inventory'
      };
    }
  },

  // Export inventory data
  async exportInventory(format: 'csv' | 'xlsx' = 'csv', filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams({
        format,
        ...(filters || {})
      });
      
      const response = await apiClient.get(`/api/inventory/export?${params}`, {
        expectBlob: true
      });
      
      // Type assertion for blob data
      const blobData = response.data as Blob;
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inventory-${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return {
        success: true,
        data: 'Export completed'
      };
    } catch (error) {
      console.error('Error exporting inventory:', error);
      return {
        success: false,
        error: 'Failed to export inventory'
      };
    }
  },

  // Get inventory analytics
  async getInventoryAnalytics(timeRange: string = '30d') {
    try {
      const response = await apiClient.get(`/api/inventory/analytics?timeRange=${timeRange}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching inventory analytics:', error);
      return {
        success: false,
        error: 'Failed to fetch inventory analytics'
      };
    }
  }
};