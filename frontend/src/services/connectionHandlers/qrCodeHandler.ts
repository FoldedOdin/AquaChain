/**
 * QR Code Connection Handler
 * Handles QR code-based device pairing
 */

import {
  DeviceConnectionHandler,
  DiscoveredDevice,
  ConnectionConfig,
  DeviceStatus,
  DeviceCapability
} from '../../types/deviceConnection';

export class QRCodeConnectionHandler implements DeviceConnectionHandler {
  type = 'qr_code' as const;
  name = 'QR Code Pairing';
  description = 'Scan QR code to pair device';
  icon = 'qr-code';

  private pairedDevices: Map<string, DiscoveredDevice> = new Map();
  private connectedDevices: Set<string> = new Set();

  // Event handlers
  onDeviceDiscovered?: (device: DiscoveredDevice) => void;
  onDeviceConnected?: (deviceId: string) => void;
  onDeviceDisconnected?: (deviceId: string) => void;
  onConnectionError?: (deviceId: string, error: Error) => void;

  canDiscover(): boolean {
    return false; // QR code doesn't support automatic discovery
  }

  async startDiscovery(): Promise<void> {
    // QR code handler doesn't support automatic discovery
    throw new Error('QR code handler does not support automatic discovery');
  }

  async stopDiscovery(): Promise<void> {
    // No-op for QR code handler
  }

  getDiscoveredDevices(): DiscoveredDevice[] {
    return Array.from(this.pairedDevices.values());
  }

  /**
   * Parse QR code and create device from scanned data
   */
  async parseQRCode(qrData: string): Promise<DiscoveredDevice> {
    try {
      // QR code format: aquachain://device?id=ESP32-001&type=water_quality&key=abc123
      const url = new URL(qrData);
      
      if (url.protocol !== 'aquachain:' || url.hostname !== 'device') {
        throw new Error('Invalid AquaChain device QR code');
      }

      const deviceId = url.searchParams.get('id');
      const deviceType = url.searchParams.get('type') as any;
      const pairingKey = url.searchParams.get('key');
      const deviceName = url.searchParams.get('name') || `Device ${deviceId}`;

      if (!deviceId || !deviceType || !pairingKey) {
        throw new Error('Missing required parameters in QR code');
      }

      // Get device capabilities based on type
      const capabilities = this.getCapabilitiesForType(deviceType);

      const device: DiscoveredDevice = {
        deviceId,
        name: deviceName,
        type: deviceType,
        connectionType: 'qr_code',
        capabilities,
        metadata: {
          pairingKey,
          qrCodeData: qrData,
          scannedAt: new Date().toISOString()
        },
        isConnectable: true,
        requiresPairing: true,
        pairingInstructions: 'Device will be paired automatically after QR code scan'
      };

      this.pairedDevices.set(deviceId, device);
      this.onDeviceDiscovered?.(device);

      return device;
    } catch (error) {
      throw new Error(`Failed to parse QR code: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async connect(device: DiscoveredDevice, config: ConnectionConfig): Promise<boolean> {
    try {
      // Validate pairing key with backend
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices/validate-pairing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        },
        body: JSON.stringify({
          deviceId: device.deviceId,
          pairingKey: device.metadata.pairingKey,
          connectionType: 'qr_code'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Pairing validation failed');
      }

      const result = await response.json();
      
      if (result.valid) {
        this.connectedDevices.add(device.deviceId);
        this.onDeviceConnected?.(device.deviceId);
        return true;
      }

      throw new Error('Invalid pairing key');
    } catch (error) {
      this.onConnectionError?.(device.deviceId, error as Error);
      return false;
    }
  }

  async disconnect(deviceId: string): Promise<boolean> {
    try {
      // Send unpair request to backend
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/v1/devices/${deviceId}/unpair`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        }
      });

      if (response.ok) {
        this.connectedDevices.delete(deviceId);
        this.pairedDevices.delete(deviceId);
        this.onDeviceDisconnected?.(deviceId);
        return true;
      }

      throw new Error('Failed to unpair device');
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
    
    if (this.pairedDevices.has(deviceId)) {
      return 'pairing';
    }
    
    return 'offline';
  }

  /**
   * Get device capabilities based on device type
   */
  private getCapabilitiesForType(deviceType: string): DeviceCapability[] {
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
        return [];
    }
  }
}