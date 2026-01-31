import { apiClient, ApiResponse } from './apiClient';
import { WarehouseOverview, PickList, QualityCheck, WarehouseLocation } from '../types/warehouse';

interface WarehouseServiceResponse<T> {
  success: true;
  data: T;
}

interface WarehouseServiceError {
  success: false;
  error: string;
}

export const warehouseService = {
  // Get warehouse overview
  async getWarehouseOverview(): Promise<WarehouseServiceResponse<WarehouseOverview> | WarehouseServiceError> {
    try {
      const response: ApiResponse<WarehouseOverview> = await apiClient.get('/api/warehouse/overview');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching warehouse overview:', error);
      return {
        success: false,
        error: 'Failed to fetch warehouse overview'
      };
    }
  },

  // Process inbound shipment
  async processInboundShipment(shipmentData: {
    po_id: string;
    supplier_id: string;
    items: Array<{
      item_id: string;
      quantity_received: number;
      condition?: string;
    }>;
    received_by: string;
    notes?: string;
  }) {
    try {
      const response = await apiClient.post('/api/warehouse/receiving', shipmentData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error processing inbound shipment:', error);
      return {
        success: false,
        error: 'Failed to process inbound shipment'
      };
    }
  },

  // Perform quality check
  async performQualityCheck(qualityData: {
    receiving_id: string;
    inspector: string;
    overall_status: 'passed' | 'failed' | 'partial';
    items_checked: Array<{
      item_id: string;
      location_id: string;
      status: 'approved' | 'rejected';
      quantity_approved?: number;
      quantity_rejected?: number;
      rejection_reason?: string;
    }>;
    notes?: string;
  }) {
    try {
      const response = await apiClient.post('/api/warehouse/quality-check', qualityData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error performing quality check:', error);
      return {
        success: false,
        error: 'Failed to perform quality check'
      };
    }
  },

  // Create pick list
  async createPickList(orderData: {
    order_id: string;
    items: Array<{
      item_id: string;
      name?: string;
      quantity: number;
      priority?: 'low' | 'normal' | 'high' | 'urgent';
    }>;
    priority?: 'low' | 'normal' | 'high' | 'urgent';
  }) {
    try {
      const response = await apiClient.post('/api/warehouse/pick-list', orderData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error creating pick list:', error);
      return {
        success: false,
        error: 'Failed to create pick list'
      };
    }
  },

  // Assign picker to pick list
  async assignPicker(pickListId: string, pickerId: string) {
    try {
      const response = await apiClient.put(`/api/warehouse/pick-list/${pickListId}/assign`, {
        picker_id: pickerId
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error assigning picker:', error);
      return {
        success: false,
        error: 'Failed to assign picker'
      };
    }
  },

  // Complete picking process
  async completePicking(pickListId: string, pickingData: {
    picker_id: string;
    items_picked: Array<{
      item_id: string;
      location_id: string;
      quantity_picked: number;
      condition?: string;
    }>;
    notes?: string;
  }) {
    try {
      const response = await apiClient.put(`/api/warehouse/pick-list/${pickListId}/complete`, pickingData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error completing picking:', error);
      return {
        success: false,
        error: 'Failed to complete picking'
      };
    }
  },

  // Get warehouse locations
  async getWarehouseLocations(filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams(filters || {});
      const response = await apiClient.get(`/api/warehouse/locations?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching warehouse locations:', error);
      return {
        success: false,
        error: 'Failed to fetch warehouse locations'
      };
    }
  },

  // Update warehouse location
  async updateWarehouseLocation(locationId: string, updates: Partial<WarehouseLocation>) {
    try {
      const response = await apiClient.put(`/api/warehouse/locations/${locationId}`, updates);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating warehouse location:', error);
      return {
        success: false,
        error: 'Failed to update warehouse location'
      };
    }
  },

  // Get pick lists
  async getPickLists(filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams(filters || {});
      const response = await apiClient.get(`/api/warehouse/pick-lists?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching pick lists:', error);
      return {
        success: false,
        error: 'Failed to fetch pick lists'
      };
    }
  },

  // Get quality checks
  async getQualityChecks(filters?: Record<string, string>) {
    try {
      const params = new URLSearchParams(filters || {});
      const response = await apiClient.get(`/api/warehouse/quality-checks?${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching quality checks:', error);
      return {
        success: false,
        error: 'Failed to fetch quality checks'
      };
    }
  },

  // Get warehouse analytics
  async getWarehouseAnalytics(timeRange: string = '30d') {
    try {
      const response = await apiClient.get(`/api/warehouse/analytics?timeRange=${timeRange}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching warehouse analytics:', error);
      return {
        success: false,
        error: 'Failed to fetch warehouse analytics'
      };
    }
  },

  // Get staff performance
  async getStaffPerformance(timeRange: string = '30d') {
    try {
      const response = await apiClient.get(`/api/warehouse/staff-performance?timeRange=${timeRange}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching staff performance:', error);
      return {
        success: false,
        error: 'Failed to fetch staff performance'
      };
    }
  },

  // Export warehouse data
  async exportWarehouseData(type: 'locations' | 'pick-lists' | 'quality-checks', format: 'csv' | 'xlsx' = 'csv') {
    try {
      const response = await apiClient.get(`/api/warehouse/export/${type}?format=${format}`, {
        expectBlob: true
      });
      
      // Type assertion for blob data
      const blobData = response.data as Blob;
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `warehouse-${type}-${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return {
        success: true,
        data: 'Export completed'
      };
    } catch (error) {
      console.error('Error exporting warehouse data:', error);
      return {
        success: false,
        error: 'Failed to export warehouse data'
      };
    }
  }
};