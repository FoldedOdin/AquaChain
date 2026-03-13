/**
 * Real Data Service - Fetches data from actual backend/database
 * Production data service with real API calls
 */

import { WaterQualityReading, Alert, DeviceStatus, ServiceRequest, User } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3001';
const ENABLE_FALLBACK_MODE = process.env.NODE_ENV === 'development';

// Debug logging for environment
console.log('🔧 [DataService] API_BASE_URL =', API_BASE_URL);
console.log('🔧 [DataService] Environment =', process.env.NODE_ENV);

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
      console.log(`🔑 [makeRequest] Auth token: ${token ? 'Present (' + token.substring(0, 20) + '...)' : 'Missing'}`);
      
      // Check if we're using a development token with production API
      const isDevelopmentToken = token && token.startsWith('dev-token-');
      const isProductionAPI = API_BASE_URL.includes('amazonaws.com');
      
      if (isDevelopmentToken && isProductionAPI) {
        console.warn('⚠️ [makeRequest] Development token detected with production API - requests will fail');
        console.warn('⚠️ [makeRequest] Please use proper authentication or switch to mock data');
        return null;
      }
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.headers,
        },
      });

      console.log(`📡 [makeRequest] Response status: ${response.status} ${response.statusText}`);

      // Get response text first to handle both JSON and text responses
      const responseText = await response.text();
      console.log(`📥 [makeRequest] Raw response text:`, responseText.substring(0, 200) + (responseText.length > 200 ? '...' : ''));

      if (!response.ok) {
        // Try to parse error details from response
        let errorData = null;
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          if (responseText) {
            errorData = JSON.parse(responseText);
            errorMessage = errorData?.error || errorData?.message || errorMessage;
          }
        } catch {
          // If JSON parsing fails, use the text as error message
          if (responseText) {
            errorMessage = responseText;
          }
        }
        
        // Provide helpful error messages for common issues
        if (response.status === 401) {
          if (isDevelopmentToken) {
            errorMessage = 'Authentication failed: Development token cannot be used with production API';
          } else if (!token) {
            errorMessage = 'Authentication failed: No token found - please log in';
          } else {
            errorMessage = 'Authentication failed: Invalid or expired token';
          }
        } else if (response.status === 403) {
          errorMessage = 'Access forbidden: Insufficient permissions';
        } else if (response.status === 404) {
          errorMessage = `API endpoint not found: ${endpoint}`;
        } else if (response.status >= 500) {
          errorMessage = 'Server error: Please try again later';
        }
        
        console.error(`❌ [makeRequest] API request failed: ${errorMessage}`);
        if (errorData) {
          console.error('📋 [makeRequest] Full error details:', errorData);
        }
        
        // Create error object with status for better handling
        const error = new Error(errorMessage) as any;
        error.status = response.status;
        error.details = errorData;
        error.endpoint = endpoint;
        throw error;
      }

      // Try to parse JSON response
      let result: any = null;
      if (responseText) {
        try {
          result = JSON.parse(responseText);
        } catch (parseError) {
          console.warn('⚠️ [makeRequest] Failed to parse JSON response, returning text:', parseError);
          return responseText as any;
        }
      }
      
      console.log(`✅ [makeRequest] Parsed response:`, result);
      
      // Handle different response formats
      if (result && typeof result === 'object') {
        // If response has success field, check it
        if ('success' in result) {
          if (result.success) {
            console.log(`📦 [makeRequest] Returning result.data:`, result.data);
            return result.data;
          } else {
            const errorMsg = result.error || result.message || 'API request failed';
            console.error(`❌ [makeRequest] API error: ${errorMsg}`);
            throw new Error(errorMsg);
          }
        } else {
          // Direct data response
          return result;
        }
      } else {
        // Non-object response (string, number, etc.)
        return result;
      }
    } catch (error) {
      // If it's already a structured error with status, re-throw it
      if (error instanceof Error && (error as any).status) {
        throw error;
      }
      
      console.error('🚨 [makeRequest] Network/Request error:', error);
      
      // Create a proper error object
      const networkError = new Error(`Network error: ${error instanceof Error ? error.message : 'Unable to connect to server'}`) as any;
      networkError.status = 0;
      networkError.originalError = error;
      networkError.endpoint = endpoint;
      throw networkError;
    }
  }

  // Water Quality Data
  async getWaterQualityData(timeRange: string = '24h'): Promise<WaterQualityReading[]> {
    const data = await this.makeRequest<WaterQualityReading[]>(`/api/water-quality?range=${timeRange}`);
    return data || [];
  }

  async getLatestWaterQuality(): Promise<WaterQualityReading | null> {
    const data = await this.makeRequest<WaterQualityReading>('/api/water-quality/latest');
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
    try {
      console.log('🔍 [dataService] Fetching devices from /api/devices');
      const data = await this.makeRequest<DeviceStatus[]>('/api/devices');
      console.log('📦 [dataService] Devices received:', data);
      console.log('📊 [dataService] Device count:', data?.length || 0);
      return data || [];
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      return [];
    }
  }

  async getDeviceById(deviceId: string): Promise<DeviceStatus | null> {
    try {
      const data = await this.makeRequest<DeviceStatus>(`/api/devices/${deviceId}`);
      return data;
    } catch (error) {
      console.error(`Failed to fetch device ${deviceId}:`, error);
      return null;
    }
  }

  // Alerts
  async getAlerts(limit: number = 50): Promise<Alert[]> {
    try {
      // Use /alerts endpoint (not /api/alerts)
      const data = await this.makeRequest<Alert[]>(`/alerts?limit=${limit}`);
      console.log('🔍 [getAlerts] Raw API response:', data);
      console.log('🔍 [getAlerts] Response type:', typeof data);
      console.log('🔍 [getAlerts] Is array:', Array.isArray(data));
      
      // Ensure we always return an array
      if (Array.isArray(data)) {
        console.log('✅ [getAlerts] Returning array with', data.length, 'items');
        return data;
      } else if (data && typeof data === 'object' && 'alerts' in data) {
        console.log('🔧 [getAlerts] Extracting alerts from nested object');
        const alerts = (data as any).alerts;
        return Array.isArray(alerts) ? alerts : [];
      } else if (data && typeof data === 'object' && 'data' in data) {
        console.log('🔧 [getAlerts] Extracting data from nested object');
        const nestedData = (data as any).data;
        return Array.isArray(nestedData) ? nestedData : [];
      } else {
        console.warn('⚠️ [getAlerts] Unexpected response format, returning empty array');
        return [];
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      
      // Handle CORS errors specifically
      if ((error as any)?.message?.includes('CORS') || (error as any)?.message?.includes('NetworkError')) {
        console.warn('🚨 CORS error detected on alerts endpoint - this is a known issue');
        console.warn('💡 The alerts endpoint needs CORS configuration in API Gateway');
        console.warn('🔧 Run: python scripts/deployment/fix-cors-comprehensive.py');
        
        // Return empty array instead of crashing the app
        return [];
      }
      
      // Stop polling on auth errors
      if ((error as any)?.status === 401) {
        console.warn('🛑 [getAlerts] Authentication failed - stopping polling');
      }
      return [];
    }
  }

  async getCriticalAlerts(): Promise<Alert[]> {
    try {
      // Use /alerts endpoint (not /api/alerts)
      const data = await this.makeRequest<Alert[]>('/alerts?severity=critical');
      return data || [];
    } catch (error) {
      console.error('Failed to fetch critical alerts:', error);
      
      // Handle CORS errors specifically
      if ((error as any)?.message?.includes('CORS') || (error as any)?.message?.includes('NetworkError')) {
        console.warn('🚨 CORS error detected on critical alerts endpoint');
        return [];
      }
      
      // Stop polling on auth errors
      if ((error as any)?.status === 401) {
        console.warn('🛑 [getCriticalAlerts] Authentication failed - stopping polling');
      }
      return [];
    }
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
    const data = await this.makeRequest<any>('/api/dashboard/stats');
    
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
      // Store in both keys for compatibility
      localStorage.setItem('aquachain_token', token);
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('aquachain_token');
      localStorage.removeItem('authToken');
    }
  }
}

// Export singleton instance
export const dataService = new DataService();
export default dataService;