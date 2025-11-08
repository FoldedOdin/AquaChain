/**
 * Real Data Service - Fetches data from actual backend/database
 * Production data service with real API calls
 */

import { WaterQualityReading, Alert, DeviceStatus, ServiceRequest, User } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3001/api';
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
    this.authToken = localStorage.getItem('authToken');
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T | null> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.authToken ? `Bearer ${this.authToken}` : '',
          ...options.headers,
        },
      });

      if (!response.ok) {
        console.warn(`API request failed: ${response.status} ${response.statusText}`);
        return null;
      }

      const result: ApiResponse<T> = await response.json();
      
      if (result.success) {
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

  // Device Management
  async getDevices(): Promise<DeviceStatus[]> {
    const data = await this.makeRequest<DeviceStatus[]>('/devices');
    return data || [];
  }

  async getDeviceById(deviceId: string): Promise<DeviceStatus | null> {
    const data = await this.makeRequest<DeviceStatus>(`/devices/${deviceId}`);
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
    const data = await this.makeRequest<ServiceRequest[]>('/service-requests');
    return data || [];
  }

  async createServiceRequest(request: Partial<ServiceRequest>): Promise<ServiceRequest | null> {
    const data = await this.makeRequest<ServiceRequest>('/service-requests', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return data;
  }

  // Users
  async getUsers(): Promise<User[]> {
    const data = await this.makeRequest<User[]>('/users');
    return data || [];
  }

  async getUserById(userId: string): Promise<User | null> {
    const data = await this.makeRequest<User>(`/users/${userId}`);
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
      const response = await fetch(`${API_BASE_URL}/health`);
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