/**
 * Device Connection Types and Interfaces
 * Defines the pluggable device connection system
 */

export type DeviceConnectionType = 'wifi' | 'bluetooth' | 'qr_code' | 'manual' | 'auto_discovery';

export type DeviceType = 'water_quality' | 'air_quality' | 'soil_moisture' | 'weather_station' | 'generic_iot';

export type DeviceStatus = 'discovering' | 'pairing' | 'connected' | 'active' | 'offline' | 'error';

export interface DeviceCapability {
  id: string;
  name: string;
  type: 'sensor' | 'actuator' | 'display' | 'storage';
  dataType: 'number' | 'string' | 'boolean' | 'object';
  unit?: string;
  range?: { min: number; max: number };
  readonly?: boolean;
}

export interface DiscoveredDevice {
  deviceId: string;
  name: string;
  type: DeviceType;
  connectionType: DeviceConnectionType;
  signalStrength?: number;
  batteryLevel?: number;
  firmwareVersion?: string;
  capabilities: DeviceCapability[];
  metadata: Record<string, any>;
  isConnectable: boolean;
  requiresPairing: boolean;
  pairingInstructions?: string;
}

export interface ConnectionConfig {
  type: DeviceConnectionType;
  parameters: Record<string, any>;
  timeout?: number;
  retryAttempts?: number;
}

export interface DeviceConnectionHandler {
  type: DeviceConnectionType;
  name: string;
  description: string;
  icon: string;
  
  // Discovery methods
  canDiscover(): boolean;
  startDiscovery(): Promise<void>;
  stopDiscovery(): Promise<void>;
  getDiscoveredDevices(): DiscoveredDevice[];
  
  // Connection methods
  connect(device: DiscoveredDevice, config: ConnectionConfig): Promise<boolean>;
  disconnect(deviceId: string): Promise<boolean>;
  
  // Status methods
  isConnected(deviceId: string): boolean;
  getConnectionStatus(deviceId: string): DeviceStatus;
  
  // Event handlers
  onDeviceDiscovered?: (device: DiscoveredDevice) => void;
  onDeviceConnected?: (deviceId: string) => void;
  onDeviceDisconnected?: (deviceId: string) => void;
  onConnectionError?: (deviceId: string, error: Error) => void;
}

export interface PluggableDevice {
  deviceId: string;
  userId: string;
  name: string;
  type: DeviceType;
  connectionType: DeviceConnectionType;
  status: DeviceStatus;
  capabilities: DeviceCapability[];
  metadata: Record<string, any>;
  connectionConfig: ConnectionConfig;
  createdAt: string;
  lastSeen: string;
  isShared: boolean;
  sharedWith?: string[];
}

export interface DeviceConnectionEvent {
  type: 'discovered' | 'connected' | 'disconnected' | 'error' | 'data_received';
  deviceId: string;
  timestamp: string;
  data?: any;
  error?: string;
}