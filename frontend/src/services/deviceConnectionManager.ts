/**
 * Device Connection Manager
 * Manages pluggable device connections and discovery
 */

import { EventEmitter } from 'events';
import {
  DeviceConnectionHandler,
  DeviceConnectionType,
  DiscoveredDevice,
  PluggableDevice,
  DeviceConnectionEvent,
  ConnectionConfig,
  DeviceStatus
} from '../types/deviceConnection';

class DeviceConnectionManager extends EventEmitter {
  private handlers: Map<DeviceConnectionType, DeviceConnectionHandler> = new Map();
  private discoveredDevices: Map<string, DiscoveredDevice> = new Map();
  private connectedDevices: Map<string, PluggableDevice> = new Map();
  private isDiscovering = false;
  private discoveryTimeout?: NodeJS.Timeout;

  constructor() {
    super();
    this.initializeDefaultHandlers();
  }

  /**
   * Register a connection handler
   */
  registerHandler(handler: DeviceConnectionHandler): void {
    this.handlers.set(handler.type, handler);
    
    // Set up event listeners
    if (handler.onDeviceDiscovered) {
      handler.onDeviceDiscovered = (device: DiscoveredDevice) => {
        this.discoveredDevices.set(device.deviceId, device);
        this.emit('deviceDiscovered', device);
      };
    }
    
    if (handler.onDeviceConnected) {
      handler.onDeviceConnected = (deviceId: string) => {
        this.emit('deviceConnected', deviceId);
      };
    }
    
    if (handler.onDeviceDisconnected) {
      handler.onDeviceDisconnected = (deviceId: string) => {
        this.emit('deviceDisconnected', deviceId);
      };
    }
    
    if (handler.onConnectionError) {
      handler.onConnectionError = (deviceId: string, error: Error) => {
        this.emit('connectionError', deviceId, error);
      };
    }
  }

  /**
   * Get all registered handlers
   */
  getHandlers(): DeviceConnectionHandler[] {
    return Array.from(this.handlers.values());
  }

  /**
   * Start device discovery for all handlers
   */
  async startDiscovery(timeout: number = 30000): Promise<void> {
    if (this.isDiscovering) {
      return;
    }

    this.isDiscovering = true;
    this.discoveredDevices.clear();
    
    // Start discovery for all handlers that support it
    const discoveryPromises = Array.from(this.handlers.values())
      .filter(handler => handler.canDiscover())
      .map(handler => handler.startDiscovery().catch(error => {
        console.error(`Discovery failed for ${handler.type}:`, error);
      }));

    await Promise.allSettled(discoveryPromises);

    // Set timeout for discovery
    this.discoveryTimeout = setTimeout(() => {
      this.stopDiscovery();
    }, timeout);

    this.emit('discoveryStarted');
  }

  /**
   * Stop device discovery
   */
  async stopDiscovery(): Promise<void> {
    if (!this.isDiscovering) {
      return;
    }

    this.isDiscovering = false;
    
    if (this.discoveryTimeout) {
      clearTimeout(this.discoveryTimeout);
      this.discoveryTimeout = undefined;
    }

    // Stop discovery for all handlers
    const stopPromises = Array.from(this.handlers.values())
      .map(handler => handler.stopDiscovery().catch(error => {
        console.error(`Stop discovery failed for ${handler.type}:`, error);
      }));

    await Promise.allSettled(stopPromises);
    this.emit('discoveryStopped');
  }

  /**
   * Get all discovered devices
   */
  getDiscoveredDevices(): DiscoveredDevice[] {
    return Array.from(this.discoveredDevices.values());
  }

  /**
   * Connect to a discovered device
   */
  async connectDevice(device: DiscoveredDevice, config: ConnectionConfig): Promise<boolean> {
    const handler = this.handlers.get(device.connectionType);
    if (!handler) {
      throw new Error(`No handler found for connection type: ${device.connectionType}`);
    }

    try {
      const success = await handler.connect(device, config);
      
      if (success) {
        // Create pluggable device record
        const pluggableDevice: PluggableDevice = {
          deviceId: device.deviceId,
          userId: '', // Will be set by backend
          name: device.name,
          type: device.type,
          connectionType: device.connectionType,
          status: 'connected',
          capabilities: device.capabilities,
          metadata: device.metadata,
          connectionConfig: config,
          createdAt: new Date().toISOString(),
          lastSeen: new Date().toISOString(),
          isShared: false
        };

        this.connectedDevices.set(device.deviceId, pluggableDevice);
        
        // Register device with backend
        await this.registerDeviceWithBackend(pluggableDevice);
        
        this.emit('deviceConnected', device.deviceId);
      }
      
      return success;
    } catch (error) {
      this.emit('connectionError', device.deviceId, error as Error);
      throw error;
    }
  }

  /**
   * Disconnect a device
   */
  async disconnectDevice(deviceId: string): Promise<boolean> {
    const device = this.connectedDevices.get(deviceId);
    if (!device) {
      return false;
    }

    const handler = this.handlers.get(device.connectionType);
    if (!handler) {
      return false;
    }

    try {
      const success = await handler.disconnect(deviceId);
      
      if (success) {
        this.connectedDevices.delete(deviceId);
        this.emit('deviceDisconnected', deviceId);
      }
      
      return success;
    } catch (error) {
      this.emit('connectionError', deviceId, error as Error);
      throw error;
    }
  }

  /**
   * Get connection status for a device
   */
  getDeviceStatus(deviceId: string): DeviceStatus {
    const device = this.connectedDevices.get(deviceId);
    if (!device) {
      return 'offline';
    }

    const handler = this.handlers.get(device.connectionType);
    if (!handler) {
      return 'error';
    }

    return handler.getConnectionStatus(deviceId);
  }

  /**
   * Get all connected devices
   */
  getConnectedDevices(): PluggableDevice[] {
    return Array.from(this.connectedDevices.values());
  }

  /**
   * Initialize default connection handlers
   */
  private initializeDefaultHandlers(): void {
    // Handlers will be registered by individual modules
    // This allows for lazy loading and modular architecture
  }

  /**
   * Register device with backend API
   */
  private async registerDeviceWithBackend(device: PluggableDevice): Promise<void> {
    try {
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
          metadata: device.metadata,
          connectionConfig: device.connectionConfig
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to register device with backend');
      }

      const result = await response.json();
      
      // Update device with backend-assigned properties
      device.userId = result.device.userId;
      this.connectedDevices.set(device.deviceId, device);
      
    } catch (error) {
      console.error('Failed to register device with backend:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const deviceConnectionManager = new DeviceConnectionManager();
export default deviceConnectionManager;