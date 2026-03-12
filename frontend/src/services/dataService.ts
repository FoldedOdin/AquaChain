/**
 * Real Data Service - Fetches data from actual backend/database
 * Production data service with real API calls
 */

import { WaterQualityReading, Alert, DeviceStatus, ServiceRequest, User } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3001';
const ENABLE_FALLBACK_MODE = process.env.NODE_ENV === 'development';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

class DataService {
  private authToken: string | null = null;

  constructor() {
    // Get auth token from localStorage or auth context
    // Try both token keys for compatibility
    this.authToken = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T | null> {
    try {
      // Get fresh token on each request (in case user logged in after service was created)
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      
      const url = `${API_BASE_URL}${endpoint}`;
      console.log(`🌐 [makeRequest] Calling: ${url}`);
      console.log(`🔑 [makeRequest] Auth token: ${token ? 'Present' : 'Missing'}`);
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.headers,
        },
      });

      console.log(`📡 [makeRequest] Response status: ${response.status}`);

      if (!response.ok) {
        console.warn(`API request failed: ${response.status} ${response.statusText}`);
        return null;
      }

      const result: ApiResponse<T> = await response.json();
      console.log(`📥 [makeRequest] Raw response:`, result);
      
      if (result.success) {
        console.log(`✅ [makeRequest] Returning result.data:`, result.data);
        return result.data;
      } else {
        console.warn(`API error: ${result.error || result.message}`);
        return null;
      }
    } catch (error) {
      console.warn('Network error:', error);
      return null;
    }
  }

  // Water Quality Data
  async getWaterQualityData(timeRange: string = '24h'): Promise<WaterQualityReading[]> {
    const data = await this.makeRequest<WaterQualityReading[]>(`/water-quality?range=${timeRange}`);
    return data || [];
  }

  async getLatestWaterQuality(): Promise<WaterQualityReading | null> {
    const data = await this.makeRequest<WaterQualityReading>('/water-quality/latest');
    return data;
  }

  // Device Readings
  async getDeviceReadings(deviceId: string, days: number = 7): Promise<any[]> {
    console.log(`🔍 [dataService] Fetching readings for device ${deviceId}`);
    const data = await this.makeRequest<any>(`/api/v1/readings/${deviceId}/history?days=${days}`);
    console.log('📦 [dataService] Readings received:', data);
    return data?.readings || []; // Extract readings from response
  }

  async getLatestDeviceReading(deviceId: string): Promise<any | null> {
    console.log(`🔍 [dataService] Fetching latest reading for device ${deviceId}`);
    const data = await this.makeRequest<any>(`/api/v1/readings/${deviceId}/latest`);
    console.log('📦 [dataService] Latest reading:', data);
    return data?.reading || null; // Extract reading from response
  }

  // Device Management
  async getDevices(): Promise<DeviceStatus[]> {
    console.log('🔍 [dataService] Fetching devices from /api/devices');
    const data = await this.makeRequest<DeviceStatus[]>('/api/devices');
    console.log('📦 [dataService] Devices received:', data);
    console.log('📊 [dataService] Device count:', data?.length || 0);
    return data || [];
  }

  async getDeviceById(deviceId: string): Promise<DeviceStatus | null> {
    const data = await this.makeRequest<DeviceStatus>(`/api/devices/${deviceId}`);
    return data;
  }

  // Alerts
  async getAlerts(limit: number = 50): Promise<Alert[]> {
    const data = await this.makeRequest<Alert[]>(`/alerts?limit=${limit}`);
    return data || [];
  }

  async getCriticalAlerts(): Promise<Alert[]> {
    const data = await this.makeRequest<Alert[]>('/alerts?severity=critical');
    return data || [];
  }

  // Service Requests
  async getServiceRequests(): Promise<ServiceRequest[]> {
    const data = await this.makeRequest<ServiceRequest[]>('/api/v1/service-requests');
    return data || [];
  }

  async createServiceRequest(request: Partial<ServiceRequest>): Promise<ServiceRequest | null> {
    const data = await this.makeRequest<ServiceRequest>('/api/v1/service-requests', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return data;
  }

  // Users
  async getUsers(): Promise<User[]> {
    const data = await this.makeRequest<User[]>('/api/v1/users');
    return data || [];
  }

  async getUserById(userId: string): Promise<User | null> {
    const data = await this.makeRequest<User>(`/api/v1/users/${userId}`);
    return data;
  }

  // Dashboard Statistics
  async getDashboardStats(): Promise<{
    totalDevices: number;
    activeDevices: number;
    criticalAlerts: number;
    averageWQI: number;
    totalUsers: number;
    pendingRequests: number;
  }> {
    const data = await this.makeRequest<any>('/dashboard/stats');
    
    // Return zeros if no data available
    return data || {
      totalDevices: 0,
      activeDevices: 0,
      criticalAlerts: 0,
      averageWQI: 0,
      totalUsers: 0,
      pendingRequests: 0,
    };
  }

  // Real-time data subscription
  async subscribeToRealTimeUpdates(callback: (data: any) => void): Promise<WebSocket | null> {
    try {
      const wsUrl = process.env.REACT_APP_WEBSOCKET_ENDPOINT || 'ws://localhost:3001/ws';
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Connected to real-time updates');
        // Send authentication if needed
        if (this.authToken) {
          ws.send(JSON.stringify({ type: 'auth', token: this.authToken }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          callback(data);
        } catch (error) {
          console.warn('Invalid WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.warn('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };

      return ws;
    } catch (error) {
      console.warn('Failed to establish WebSocket connection:', error);
      return null;
    }
  }

  // Health check
  async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Update auth token
  setAuthToken(token: string | null): void {
    this.authToken = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }
}

// Export singleton instance
export const dataService = new DataService();
export default dataService;