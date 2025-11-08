/**
 * Device Service
 * Handles device registration and management API calls
 */

export interface DeviceRegistrationData {
  device_id: string;
  name?: string;
  location?: string;
  water_source_type?: 'household' | 'industrial' | 'agricultural';
  pairing_code?: string;
}

export interface Device {
  device_id: string;
  user_id: string;
  name: string;
  location: string;
  water_source_type: string;
  status: 'active' | 'inactive' | 'pending';
  created_at: string;
  last_reading?: string;
  iot_thing_name?: string;
  certificate_arn?: string;
}

class DeviceService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
  }

  /**
   * Get authentication token from localStorage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('aquachain_token');
  }

  /**
   * Get authorization headers
   */
  private getAuthHeaders(): HeadersInit {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  /**
   * Register a new device
   */
  async registerDevice(data: DeviceRegistrationData): Promise<Device> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices/register`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to register device');
      }

      return result.device;
    } catch (error: any) {
      console.error('Device registration error:', error);
      throw error;
    }
  }

  /**
   * Get all devices for the current user
   */
  async getDevices(): Promise<Device[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch devices');
      }

      return result.devices || [];
    } catch (error: any) {
      console.error('Fetch devices error:', error);
      throw error;
    }
  }

  /**
   * Get a single device by ID
   */
  async getDeviceById(deviceId: string): Promise<Device> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices/${deviceId}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch device');
      }

      return result.device;
    } catch (error: any) {
      console.error('Fetch device error:', error);
      throw error;
    }
  }

  /**
   * Update device information
   */
  async updateDevice(deviceId: string, updates: Partial<DeviceRegistrationData>): Promise<Device> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices/${deviceId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to update device');
      }

      return result.device;
    } catch (error: any) {
      console.error('Update device error:', error);
      throw error;
    }
  }

  /**
   * Delete a device
   */
  async deleteDevice(deviceId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices/${deviceId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete device');
      }
    } catch (error: any) {
      console.error('Delete device error:', error);
      throw error;
    }
  }

  /**
   * Get device status
   */
  async getDeviceStatus(deviceId: string): Promise<{ status: string; lastSeen?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/devices/${deviceId}/status`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch device status');
      }

      return result;
    } catch (error: any) {
      console.error('Fetch device status error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const deviceService = new DeviceService();
export default deviceService;
