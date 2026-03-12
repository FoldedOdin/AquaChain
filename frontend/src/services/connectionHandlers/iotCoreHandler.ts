/**
 * IoT Core Connection Handler
 * Handles discovery and connection of devices already registered in AWS IoT Core
 */

import {
  DeviceConnectionHandler,
  DiscoveredDevice,
  ConnectionConfig,
  DeviceStatus,
  DeviceCapability
} from '../../types/deviceConnection';

export class IoTCoreConnectionHandler implements DeviceConnectionHandler {
  type = 'auto_discovery' as const;
  name = 'IoT Core Discovery';
  description = 'Discover devices connected to AWS IoT Core';
  icon = 'cloud';

  private discoveredDevices: Map<string, DiscoveredDevice> = new Map();
  private connectedDevices: Set<string> = new Set();
  private isDiscovering = false;

  // Event handlers
  onDeviceDiscovered?: (device: DiscoveredDevice) => void;
  onDeviceConnected?: (deviceId: string) => void;
  onDeviceDisconnected?: (deviceId: string) => void;
  onConnectionError?: (deviceId: string, error: Error) => void;

  canDiscover(): boolean {
    return true;
  }

  async startDiscovery(): Promise<void> {
    if (this.isDiscovering) {
      return;
    }

    this.isDiscovering = true;
    this.discoveredDevices.clear();

    try {
      // Query backend for bridged devices (devices already in IoT Core)
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices/bridged-devices`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        const bridgedDevices = result.devices || [];

        for (const device of bridgedDevices) {
          const discoveredDevice = this.convertToDiscoveredDevice(device);
          this.discoveredDevices.set(device.deviceId, discoveredDevice);
          this.onDeviceDiscovered?.(discoveredDevice);
        }
      }

      // Also check for any active devices in the traditional system
      await this.discoverTraditionalDevices();

    } catch (error) {
      console.error('IoT Core discovery failed:', error);
    }
  }

  async stopDiscovery(): Promise<void> {
    this.isDiscovering = false;
  }

  getDiscoveredDevices(): DiscoveredDevice[] {
    return Array.from(this.discoveredDevices.values());
  }

  async connect(device: DiscoveredDevice, config: ConnectionConfig): Promise<boolean> {
    try {
      // For IoT Core devices, "connection" means registering them in the pluggable system
      // if they're not already registered
      
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices/register-pluggable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        },
        body: JSON.stringify({
          deviceId: device.deviceId,
          name: device.name,
          type: device.type,
          connectionType: device.connectionType,
          capabilities: device.capabilities,
          metadata: {
            ...device.metadata,
            connectedViaIoTCore: true,
            connectionTimestamp: new Date().toISOString()
          },
          connectionConfig: {
            type: 'auto_discovery',
            parameters: {
              iotCoreDevice: true,
              bridged: true
            }
          }
        })
      });

      if (response.ok) {
        this.connectedDevices.add(device.deviceId);
        this.onDeviceConnected?.(device.deviceId);
        return true;
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to connect IoT Core device');
      }

    } catch (error) {
      this.onConnectionError?.(device.deviceId, error as Error);
      return false;
    }
  }

  async disconnect(deviceId: string): Promise<boolean> {
    try {
      // For IoT Core devices, we don't actually disconnect from IoT Core,
      // we just remove them from the pluggable device system
      
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices/${deviceId}/unpair`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        }
      });

      if (response.ok) {
        this.connectedDevices.delete(deviceId);
        this.onDeviceDisconnected?.(deviceId);
        return true;
      }

      return false;
    } catch (error) {
      this.onConnectionError?.(deviceId, error as Error);
      return false;
    }
  }

  isConnected(deviceId: string): boolean {
    return this.connectedDevices.has(deviceId);
  }

  getConnectionStatus(deviceId: string): DeviceStatus {
    if (this.connectedDevices.has(deviceId)) {
      return 'connected';
    }
    
    if (this.discoveredDevices.has(deviceId)) {
      const device = this.discoveredDevices.get(deviceId);
      return this.mapStatusFromMetadata(device?.metadata?.status);
    }
    
    return 'offline';
  }

  /**
   * Convert pluggable device record to discovered device format
   */
  private convertToDiscoveredDevice(pluggableDevice: any): DiscoveredDevice {
    return {
      deviceId: pluggableDevice.deviceId,
      name: pluggableDevice.name,
      type: pluggableDevice.type,
      connectionType: 'auto_discovery',
      capabilities: pluggableDevice.capabilities || [],
      metadata: {
        ...pluggableDevice.metadata,
        status: pluggableDevice.status,
        lastSeen: pluggableDevice.lastSeen,
        isBridged: true,
        source: 'iot_core'
      },
      isConnectable: true,
      requiresPairing: false, // IoT Core devices are already authenticated
      pairingInstructions: 'Device is already connected to AWS IoT Core and ready to use'
    };
  }

  /**
   * Discover traditional devices that might not be bridged yet
   */
  private async discoverTraditionalDevices(): Promise<void> {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        const devices = result.devices || [];

        for (const device of devices) {
          // Check if this device is already in our discovered devices
          if (!this.discoveredDevices.has(device.deviceId || device.device_id)) {
            const discoveredDevice = this.convertTraditionalDevice(device);
            this.discoveredDevices.set(discoveredDevice.deviceId, discoveredDevice);
            this.onDeviceDiscovered?.(discoveredDevice);
          }
        }
      }
    } catch (error) {
      console.error('Failed to discover traditional devices:', error);
    }
  }

  /**
   * Convert traditional device to discovered device format
   */
  private convertTraditionalDevice(device: any): DiscoveredDevice {
    const deviceId = device.deviceId || device.device_id;
    
    return {
      deviceId,
      name: device.deviceName || device.name || `Device ${deviceId}`,
      type: this.determineDeviceType(deviceId),
      connectionType: 'auto_discovery',
      capabilities: this.getCapabilitiesForDeviceType(this.determineDeviceType(deviceId)),
      metadata: {
        location: device.location || 'Not specified',
        status: device.status || 'unknown',
        lastSeen: device.lastSeen || device.last_seen,
        isTraditional: true,
        needsBridging: true,
        source: 'traditional_system'
      },
      isConnectable: true,
      requiresPairing: false,
      pairingInstructions: 'This device will be bridged to the pluggable system when connected'
    };
  }

  /**
   * Determine device type from device ID
   */
  private determineDeviceType(deviceId: string): 'water_quality' | 'air_quality' | 'soil_moisture' | 'weather_station' {
    if (deviceId.startsWith('ESP32-')) {
      return 'water_quality';
    } else if (deviceId.startsWith('DEV-')) {
      return 'water_quality';
    } else if (deviceId.startsWith('AIR-')) {
      return 'air_quality';
    } else if (deviceId.startsWith('SOIL-')) {
      return 'soil_moisture';
    } else if (deviceId.startsWith('WEATHER-')) {
      return 'weather_station';
    }
    
    return 'water_quality'; // Default for AquaChain
  }

  /**
   * Get capabilities for device type
   */
  private getCapabilitiesForDeviceType(deviceType: string): DeviceCapability[] {
    switch (deviceType) {
      case 'water_quality':
        return [
          {
            id: 'ph',
            name: 'pH Level',
            type: 'sensor',
            dataType: 'number',
            unit: 'pH',
            range: { min: 0, max: 14 },
            readonly: true
          },
          {
            id: 'turbidity',
            name: 'Turbidity',
            type: 'sensor',
            dataType: 'number',
            unit: 'NTU',
            range: { min: 0, max: 1000 },
            readonly: true
          },
          {
            id: 'tds',
            name: 'Total Dissolved Solids',
            type: 'sensor',
            dataType: 'number',
            unit: 'ppm',
            range: { min: 0, max: 2000 },
            readonly: true
          },
          {
            id: 'temperature',
            name: 'Temperature',
            type: 'sensor',
            dataType: 'number',
            unit: '°C',
            range: { min: -10, max: 50 },
            readonly: true
          },
          {
            id: 'wqi',
            name: 'Water Quality Index',
            type: 'sensor',
            dataType: 'number',
            unit: 'WQI',
            range: { min: 0, max: 100 },
            readonly: true
          }
        ];

      case 'air_quality':
        return [
          {
            id: 'pm25',
            name: 'PM2.5',
            type: 'sensor',
            dataType: 'number',
            unit: 'μg/m³',
            range: { min: 0, max: 500 },
            readonly: true
          },
          {
            id: 'co2',
            name: 'CO2',
            type: 'sensor',
            dataType: 'number',
            unit: 'ppm',
            range: { min: 0, max: 5000 },
            readonly: true
          }
        ];

      default:
        return [
          {
            id: 'generic_sensor',
            name: 'Generic Sensor',
            type: 'sensor',
            dataType: 'number',
            readonly: true
          }
        ];
    }
  }

  /**
   * Map status from metadata to DeviceStatus
   */
  private mapStatusFromMetadata(status?: string): DeviceStatus {
    switch (status) {
      case 'active':
      case 'online':
        return 'active';
      case 'connected':
        return 'connected';
      case 'offline':
        return 'offline';
      case 'error':
        return 'error';
      default:
        return 'offline';
    }
  }
}