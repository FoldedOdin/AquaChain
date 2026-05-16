/**
 * Real Data Service — fetches data from the AquaChain backend API.
 *
 * Security: all console statements have been replaced with the structured
 * logger (src/lib/logger.ts) which:
 *   - Is a no-op in production for non-error messages
 *   - Automatically redacts fields matching /token|secret|key|authorization/i
 *
 * WHY: The previous implementation called console.log with raw token substrings
 * (e.g. `token.substring(0, 20)`), which are visible to anyone who opens
 * DevTools. This violates OWASP A02 (Cryptographic Failures).
 */

import logger from '../lib/logger';
import { WaterQualityReading, Alert, DeviceStatus, ServiceRequest, User } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3001';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

class DataService {
  private authToken: string | null = null;
  /** Injected by AuthProvider so makeRequest can refresh expired tokens automatically. */
  private tokenRefresher: (() => Promise<string | null>) | null = null;

  constructor() {
    this.authToken =
      localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  }

  setTokenRefresher(refresher: () => Promise<string | null>): void {
    this.tokenRefresher = refresher;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry = false
  ): Promise<T | null> {
    try {
      const token =
        localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

      const url = `${API_BASE_URL}${endpoint}`;
      logger.debug('API request', { url, method: options.method ?? 'GET' });

      const isDevelopmentToken = Boolean(token && token.startsWith('dev-token-'));
      const isProductionAPI = API_BASE_URL.includes('amazonaws.com');

      if (isDevelopmentToken && isProductionAPI) {
        logger.warn('Development token used with production API — request blocked');
        return null;
      }

      const response = await fetch(url, {
        ...options,
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
          ...options.headers,
        },
      });

      logger.debug('API response received', { status: response.status, url });

      const responseText = await response.text();

      if (!response.ok) {
        let errorData: Record<string, unknown> | null = null;
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        try {
          if (responseText) {
            errorData = JSON.parse(responseText) as Record<string, unknown>;
            const msg = errorData?.error ?? errorData?.message;
            if (typeof msg === 'string') errorMessage = msg;
          }
        } catch {
          if (responseText) errorMessage = responseText;
        }

        if (response.status === 401) {
          if (!isRetry && this.tokenRefresher && !isDevelopmentToken) {
            logger.info('401 received — attempting token refresh');
            const newToken = await this.tokenRefresher();
            if (newToken) {
              logger.info('Token refreshed, retrying request');
              return this.makeRequest<T>(endpoint, options, true);
            }
          }

          if (isDevelopmentToken) {
            errorMessage = 'Authentication failed: development token cannot be used with production API';
          } else if (!token) {
            errorMessage = 'Authentication failed: no token found — please log in';
          } else {
            errorMessage = 'Authentication failed: invalid or expired token';
          }
        } else if (response.status === 403) {
          errorMessage = 'Access forbidden: insufficient permissions';
        } else if (response.status === 404) {
          errorMessage = `API endpoint not found: ${endpoint}`;
        } else if (response.status >= 500) {
          errorMessage = 'Server error: please try again later';
        }

        // Log error details but never log raw token or auth headers
        logger.error('API request failed', { endpoint, status: response.status, errorMessage });

        const error = new Error(errorMessage) as Error & {
          status: number;
          details: unknown;
          endpoint: string;
        };
        error.status = response.status;
        error.details = errorData;
        error.endpoint = endpoint;
        throw error;
      }

      let result: unknown = null;
      if (responseText) {
        try {
          result = JSON.parse(responseText);
        } catch (parseError) {
          logger.warn('Failed to parse JSON response — returning raw text', { endpoint });
          return responseText as unknown as T;
        }
      }

      if (result && typeof result === 'object') {
        const r = result as Record<string, unknown>;
        if ('success' in r) {
          if (r.success) {
            return (r.data ?? r) as T;
          } else {
            const errorMsg =
              typeof r.error === 'string'
                ? r.error
                : typeof r.message === 'string'
                ? r.message
                : 'API request failed';
            logger.error('API returned success=false', { endpoint, errorMsg });
            throw new Error(errorMsg);
          }
        }
        return result as T;
      }

      return result as T;
    } catch (error) {
      if (error instanceof Error && (error as any).status) throw error;

      logger.error('Network/request error', {
        endpoint,
        message: error instanceof Error ? error.message : String(error),
      });

      const networkError = new Error(
        `Network error: ${error instanceof Error ? error.message : 'Unable to connect to server'}`
      ) as Error & { status: number; originalError: unknown; endpoint: string };
      networkError.status = 0;
      networkError.originalError = error;
      networkError.endpoint = endpoint;
      throw networkError;
    }
  }

  // ---------------------------------------------------------------------------
  // Water Quality
  // ---------------------------------------------------------------------------

  async getWaterQualityData(timeRange = '24h'): Promise<WaterQualityReading[]> {
    const data = await this.makeRequest<WaterQualityReading[]>(
      `/api/water-quality?range=${timeRange}`
    );
    return data || [];
  }

  async getLatestWaterQuality(): Promise<WaterQualityReading | null> {
    return this.makeRequest<WaterQualityReading>('/api/water-quality/latest');
  }

  // ---------------------------------------------------------------------------
  // Device Readings
  // ---------------------------------------------------------------------------

  async getDeviceReadings(deviceId: string, days = 7): Promise<any[]> {
    logger.debug('Fetching device readings', { deviceId, days });
    const data = await this.makeRequest<any>(
      `/api/v1/readings/${deviceId}/history?days=${days}`
    );
    return data?.readings || [];
  }

  async getHistoricalTrendData(
    deviceId: string,
    days = 7
  ): Promise<{ date: string; wqi: number }[]> {
    logger.debug('Fetching trend data', { deviceId, days });
    try {
      const readings = await this.getDeviceReadings(deviceId, days);
      if (!readings || readings.length === 0) return [];

      const oldestReading = new Date(readings[readings.length - 1]?.timestamp);
      const requestedStart = new Date();
      requestedStart.setDate(requestedStart.getDate() - days);
      if (oldestReading > requestedStart) return [];

      const dailyData = new Map<string, { wqiSum: number; count: number }>();
      readings.forEach((reading) => {
        if (reading.wqi && reading.wqi > 0) {
          const date = new Date(reading.timestamp).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          });
          const existing = dailyData.get(date) ?? { wqiSum: 0, count: 0 };
          existing.wqiSum += reading.wqi;
          existing.count += 1;
          dailyData.set(date, existing);
        }
      });

      return Array.from(dailyData.entries())
        .map(([date, d]) => ({ date, wqi: Math.round(d.wqiSum / d.count) }))
        .sort((a, b) => new Date(a.date + ', 2024').getTime() - new Date(b.date + ', 2024').getTime());
    } catch (error) {
      logger.error('Error fetching trend data', {
        deviceId,
        message: error instanceof Error ? error.message : String(error),
      });
      return [];
    }
  }

  async getLatestDeviceReading(deviceId: string): Promise<any | null> {
    logger.debug('Fetching latest device reading', { deviceId });
    const data = await this.makeRequest<any>(
      `/api/v1/readings/${deviceId}/latest?_t=${Date.now()}`
    );

    if (data && typeof data === 'object') {
      if ('reading' in data) return data.reading;
      if ('data' in data) return data.data;
      return data;
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // Device Management
  // ---------------------------------------------------------------------------

  async getDevices(): Promise<DeviceStatus[]> {
    try {
      const data = await this.makeRequest<any>('/api/devices');
      return Array.isArray(data) ? data : (data?.devices ?? data?.data ?? []);
    } catch (error) {
      logger.error('Failed to fetch devices', {
        message: error instanceof Error ? error.message : String(error),
      });
      return [];
    }
  }

  async getDeviceById(deviceId: string): Promise<DeviceStatus | null> {
    try {
      return this.makeRequest<DeviceStatus>(`/api/devices/${deviceId}`);
    } catch (error) {
      logger.error('Failed to fetch device', {
        deviceId,
        message: error instanceof Error ? error.message : String(error),
      });
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Alerts
  // ---------------------------------------------------------------------------

  async getAlerts(limit = 50): Promise<Alert[]> {
    try {
      const data = await this.makeRequest<Alert[]>(`/alerts?limit=${limit}`);
      if (Array.isArray(data)) return data;
      if (data && typeof data === 'object') {
        const d = data as Record<string, unknown>;
        if (Array.isArray(d.alerts)) return d.alerts as Alert[];
        if (Array.isArray(d.data)) return d.data as Alert[];
      }
      logger.warn('Unexpected alerts response format');
      return [];
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      if (msg.includes('CORS') || msg.includes('NetworkError')) {
        logger.warn('CORS error on alerts endpoint — returning empty array');
      } else if ((error as any)?.status === 401) {
        logger.warn('Authentication failed on alerts — stopping polling');
      } else {
        logger.error('Failed to fetch alerts', { message: msg });
      }
      return [];
    }
  }

  async getCriticalAlerts(): Promise<Alert[]> {
    try {
      const data = await this.makeRequest<Alert[]>('/alerts?severity=critical');
      return data || [];
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      if (msg.includes('CORS') || msg.includes('NetworkError')) {
        logger.warn('CORS error on critical alerts — returning empty array');
      } else {
        logger.error('Failed to fetch critical alerts', { message: msg });
      }
      return [];
    }
  }

  async acknowledgeAlert(alertId: string): Promise<boolean> {
    try {
      await this.makeRequest(`/api/alerts/${alertId}/acknowledge`, { method: 'PUT' });
      return true;
    } catch (error) {
      logger.error('Failed to acknowledge alert', { alertId });
      return false;
    }
  }

  async muteAlert(
    alertId: string,
    deviceId: string,
    parameter: string,
    minutes = 120
  ): Promise<boolean> {
    try {
      await this.makeRequest(`/api/alerts/${alertId}/mute`, {
        method: 'PUT',
        body: JSON.stringify({ deviceId, parameter, muteMinutes: minutes }),
      });
      return true;
    } catch (error) {
      logger.error('Failed to mute alert', { alertId, deviceId });
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // Service Requests
  // ---------------------------------------------------------------------------

  async getServiceRequests(): Promise<ServiceRequest[]> {
    const data = await this.makeRequest<ServiceRequest[]>('/api/v1/service-requests');
    return data || [];
  }

  async createServiceRequest(request: Partial<ServiceRequest>): Promise<ServiceRequest | null> {
    return this.makeRequest<ServiceRequest>('/api/v1/service-requests', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ---------------------------------------------------------------------------
  // Users
  // ---------------------------------------------------------------------------

  async getUsers(): Promise<User[]> {
    const data = await this.makeRequest<User[]>('/api/v1/users');
    return data || [];
  }

  async getUserById(userId: string): Promise<User | null> {
    return this.makeRequest<User>(`/api/v1/users/${userId}`);
  }

  // ---------------------------------------------------------------------------
  // Dashboard Statistics
  // ---------------------------------------------------------------------------

  async getDashboardStats(): Promise<{
    totalDevices: number;
    activeDevices: number;
    criticalAlerts: number;
    averageWQI: number;
    totalUsers: number;
    pendingRequests: number;
  }> {
    const data = await this.makeRequest<any>('/api/dashboard/stats');
    return data || {
      totalDevices: 0,
      activeDevices: 0,
      criticalAlerts: 0,
      averageWQI: 0,
      totalUsers: 0,
      pendingRequests: 0,
    };
  }

  // ---------------------------------------------------------------------------
  // Real-time / WebSocket
  // ---------------------------------------------------------------------------

  async subscribeToRealTimeUpdates(
    callback: (data: any) => void
  ): Promise<WebSocket | null> {
    try {
      const wsUrl = process.env.REACT_APP_WEBSOCKET_ENDPOINT || 'ws://localhost:3001/ws';
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        logger.info('WebSocket connected');
        // WHY: we send only the token, not token substrings or debug info
        if (this.authToken) {
          ws.send(JSON.stringify({ type: 'auth', token: this.authToken }));
        }
      };

      ws.onmessage = (event) => {
        try {
          callback(JSON.parse(event.data));
        } catch {
          logger.warn('Received invalid WebSocket message');
        }
      };

      ws.onerror = () => logger.warn('WebSocket error');
      ws.onclose = () => logger.info('WebSocket connection closed');

      return ws;
    } catch (error) {
      logger.warn('Failed to establish WebSocket connection');
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Health check
  // ---------------------------------------------------------------------------

  async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // Token management
  // ---------------------------------------------------------------------------

  setAuthToken(token: string | null): void {
    this.authToken = token;
    if (token) {
      localStorage.setItem('aquachain_token', token);
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('aquachain_token');
      localStorage.removeItem('authToken');
    }
  }
}

export const dataService = new DataService();
export default dataService;