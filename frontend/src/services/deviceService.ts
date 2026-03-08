/**
 * Device Service
 * API client for device management operations
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'https://api.aquachain.example.com/dev';

export interface Device {
  deviceId: string;
  userId: string;
  deviceName: string;
  location: string;
  waterSourceType: string;
  status: 'active' | 'maintenance' | 'offline' | 'unregistered';
  createdAt: string;
  lastSeen: string;
  metadata: {
    batteryLevel: number;
    signalStrength: number;
    firmwareVersion: string;
  };
}

export interface RegisterDeviceRequest {
  deviceId: string;
  deviceName: string;
  location: string;
  waterSourceType: 'household' | 'industrial' | 'municipal' | 'agricultural';
}

export interface SensorReading {
  deviceId: string;
  timestamp: string;
  readings: {
    pH: number;
    turbidity: number;
    tds: number;
    temperature: number;
  };
  wqi: number;
  anomalyType: string;
}

class DeviceService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Register a new device
   */
  async registerDevice(request: RegisterDeviceRequest): Promise<Device> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/devices/register`,
        request,
        { headers: this.getAuthHeaders() }
      );
      return response.data.device;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to register device');
    }
  }

  /**
   * Get all devices for current user
   */
  async listDevices(): Promise<Device[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/devices`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.devices;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to list devices');
    }
  }

  /**
   * Get device details
   */
  async getDevice(deviceId: string): Promise<Device> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/devices/${deviceId}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.device;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to get device');
    }
  }

  /**
   * Delete/unpair a device
   */
  async deleteDevice(deviceId: string): Promise<void> {
    try {
      await axios.delete(
        `${API_BASE_URL}/devices/${deviceId}`,
        { headers: this.getAuthHeaders() }
      );
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to delete device');
    }
  }

  /**
   * Get latest sensor readings for a device
   */
  async getLatestReadings(deviceId: string): Promise<SensorReading | null> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/devices/${deviceId}/readings/latest`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.reading;
    } catch (error: any) {
      console.error('Failed to get latest readings:', error);
      return null;
    }
  }

  /**
   * Get historical sensor readings for a device
   */
  async getReadings(
    deviceId: string,
    startTime?: string,
    endTime?: string,
    limit: number = 100
  ): Promise<SensorReading[]> {
    try {
      const params = new URLSearchParams();
      if (startTime) params.append('startTime', startTime);
      if (endTime) params.append('endTime', endTime);
      params.append('limit', limit.toString());

      const response = await axios.get(
        `${API_BASE_URL}/devices/${deviceId}/readings?${params.toString()}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.readings;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to get readings');
    }
  }

  /**
   * Update device settings
   */
  async updateDevice(
    deviceId: string,
    updates: Partial<Pick<Device, 'deviceName' | 'location' | 'waterSourceType'>>
  ): Promise<Device> {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/devices/${deviceId}`,
        updates,
        { headers: this.getAuthHeaders() }
      );
      return response.data.device;
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Failed to update device');
    }
  }

  /**
   * Get device status (online/offline)
   */
  async getDeviceStatus(deviceId: string): Promise<'online' | 'offline'> {
    try {
      const device = await this.getDevice(deviceId);
      const lastSeen = new Date(device.lastSeen);
      const now = new Date();
      const minutesSinceLastSeen = (now.getTime() - lastSeen.getTime()) / 1000 / 60;
      
      // Consider offline if no data for 10 minutes
      return minutesSinceLastSeen > 10 ? 'offline' : 'online';
    } catch (error) {
      return 'offline';
    }
  }
}

export const deviceService = new DeviceService();
export default deviceService;
