/**
 * Pluggable Device Manager Component
 * Provides drag-and-drop style device connection interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  WifiIcon,
  QrCodeIcon,
  DevicePhoneMobileIcon,
  SignalIcon,
  Battery0Icon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { Droplet, Waves, Thermometer, Activity } from 'lucide-react';

import deviceConnectionManager from '../../services/deviceConnectionManager';
import { WiFiConnectionHandler } from '../../services/connectionHandlers/wifiHandler';
import { QRCodeConnectionHandler } from '../../services/connectionHandlers/qrCodeHandler';
import { IoTCoreConnectionHandler } from '../../services/connectionHandlers/iotCoreHandler';
import {
  DiscoveredDevice,
  PluggableDevice,
  DeviceConnectionType,
  DeviceStatus,
  ConnectionConfig
} from '../../types/deviceConnection';

interface PluggableDeviceManagerProps {
  onDeviceAdded?: (device: PluggableDevice) => void;
  onDeviceRemoved?: (deviceId: string) => void;
}

const PluggableDeviceManager: React.FC<PluggableDeviceManagerProps> = ({
  onDeviceAdded,
  onDeviceRemoved
}) => {
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState<DiscoveredDevice[]>([]);
  const [connectedDevices, setConnectedDevices] = useState<PluggableDevice[]>([]);
  const [selectedConnectionType, setSelectedConnectionType] = useState<DeviceConnectionType>('auto_discovery');
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null);
  const [connectionConfig, setConnectionConfig] = useState<ConnectionConfig>({
    type: 'wifi',
    parameters: {}
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string>('');
  const [showQRScanner, setShowQRScanner] = useState(false);

  // Initialize connection handlers
  useEffect(() => {
    const wifiHandler = new WiFiConnectionHandler();
    const qrHandler = new QRCodeConnectionHandler();
    const iotCoreHandler = new IoTCoreConnectionHandler();
    
    deviceConnectionManager.registerHandler(wifiHandler);
    deviceConnectionManager.registerHandler(qrHandler);
    deviceConnectionManager.registerHandler(iotCoreHandler);

    // Set up event listeners
    const handleDeviceDiscovered = (device: DiscoveredDevice) => {
      setDiscoveredDevices(prev => {
        const exists = prev.find(d => d.deviceId === device.deviceId);
        if (exists) return prev;
        return [...prev, device];
      });
    };

    const handleDeviceConnected = (deviceId: string) => {
      const connectedDevice = deviceConnectionManager.getConnectedDevices()
        .find(d => d.deviceId === deviceId);
      
      if (connectedDevice) {
        setConnectedDevices(prev => [...prev, connectedDevice]);
        onDeviceAdded?.(connectedDevice);
      }
      
      setShowConnectionModal(false);
      setIsConnecting(false);
    };

    const handleDeviceDisconnected = (deviceId: string) => {
      setConnectedDevices(prev => prev.filter(d => d.deviceId !== deviceId));
      onDeviceRemoved?.(deviceId);
    };

    const handleConnectionError = (deviceId: string, error: Error) => {
      setConnectionError(error.message);
      setIsConnecting(false);
    };

    deviceConnectionManager.on('deviceDiscovered', handleDeviceDiscovered);
    deviceConnectionManager.on('deviceConnected', handleDeviceConnected);
    deviceConnectionManager.on('deviceDisconnected', handleDeviceDisconnected);
    deviceConnectionManager.on('connectionError', handleConnectionError);

    return () => {
      deviceConnectionManager.off('deviceDiscovered', handleDeviceDiscovered);
      deviceConnectionManager.off('deviceConnected', handleDeviceConnected);
      deviceConnectionManager.off('deviceDisconnected', handleDeviceDisconnected);
      deviceConnectionManager.off('connectionError', handleConnectionError);
    };
  }, [onDeviceAdded, onDeviceRemoved]);

  const startDiscovery = useCallback(async () => {
    setIsDiscovering(true);
    setDiscoveredDevices([]);
    setConnectionError('');
    
    try {
      await deviceConnectionManager.startDiscovery(30000);
    } catch (error) {
      setConnectionError('Failed to start device discovery');
    }
  }, []);

  const stopDiscovery = useCallback(async () => {
    setIsDiscovering(false);
    await deviceConnectionManager.stopDiscovery();
  }, []);

  const handleConnectDevice = useCallback(async (device: DiscoveredDevice) => {
    setSelectedDevice(device);
    setConnectionConfig({
      type: device.connectionType,
      parameters: {}
    });
    setShowConnectionModal(true);
  }, []);

  const handleConfirmConnection = useCallback(async () => {
    if (!selectedDevice) return;

    setIsConnecting(true);
    setConnectionError('');

    try {
      await deviceConnectionManager.connectDevice(selectedDevice, connectionConfig);
    } catch (error) {
      setConnectionError(error instanceof Error ? error.message : 'Connection failed');
      setIsConnecting(false);
    }
  }, [selectedDevice, connectionConfig]);

  const handleDisconnectDevice = useCallback(async (deviceId: string) => {
    try {
      await deviceConnectionManager.disconnectDevice(deviceId);
    } catch (error) {
      console.error('Failed to disconnect device:', error);
    }
  }, []);

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'water_quality':
        return <Droplet className="w-6 h-6" />;
      case 'air_quality':
        return <Waves className="w-6 h-6" />;
      case 'weather_station':
        return <Thermometer className="w-6 h-6" />;
      default:
        return <Activity className="w-6 h-6" />;
    }
  };

  const getConnectionIcon = (type: DeviceConnectionType) => {
    switch (type) {
      case 'wifi':
        return <WifiIcon className="w-5 h-5" />;
      case 'qr_code':
        return <QrCodeIcon className="w-5 h-5" />;
      case 'bluetooth':
        return <DevicePhoneMobileIcon className="w-5 h-5" />;
      default:
        return <SignalIcon className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case 'connected':
      case 'active':
        return 'text-green-500';
      case 'discovering':
      case 'pairing':
        return 'text-yellow-500';
      case 'offline':
        return 'text-gray-400';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Connection Type Selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Device Connections</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedConnectionType('auto_discovery')}
            className={`px-3 py-2 rounded-lg flex items-center space-x-2 ${
              selectedConnectionType === 'auto_discovery'
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>IoT Core</span>
          </button>
          <button
            onClick={() => setSelectedConnectionType('wifi')}
            className={`px-3 py-2 rounded-lg flex items-center space-x-2 ${
              selectedConnectionType === 'wifi'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <WifiIcon className="w-4 h-4" />
            <span>WiFi</span>
          </button>
          <button
            onClick={() => setSelectedConnectionType('qr_code')}
            className={`px-3 py-2 rounded-lg flex items-center space-x-2 ${
              selectedConnectionType === 'qr_code'
                ? 'bg-purple-100 text-purple-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <QrCodeIcon className="w-4 h-4" />
            <span>QR Code</span>
          </button>
        </div>
      </div>

      {/* Discovery Controls */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <MagnifyingGlassIcon className="w-5 h-5 text-gray-500" />
          <span className="text-sm text-gray-600">
            {isDiscovering 
              ? selectedConnectionType === 'auto_discovery' 
                ? 'Discovering IoT Core devices...' 
                : 'Scanning for devices...'
              : selectedConnectionType === 'auto_discovery'
                ? 'Ready to discover IoT Core devices'
                : 'Ready to discover devices'
            }
          </span>
        </div>
        <button
          onClick={isDiscovering ? stopDiscovery : startDiscovery}
          disabled={selectedConnectionType === 'qr_code'}
          className={`px-4 py-2 rounded-lg font-medium ${
            isDiscovering
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed'
          }`}
        >
          {isDiscovering ? 'Stop Scanning' : selectedConnectionType === 'auto_discovery' ? 'Discover IoT Devices' : 'Start Discovery'}
        </button>
      </div>

      {/* QR Code Scanner Button */}
      {selectedConnectionType === 'qr_code' && (
        <button
          onClick={() => setShowQRScanner(true)}
          className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors"
        >
          <div className="flex flex-col items-center space-y-2">
            <QrCodeIcon className="w-8 h-8 text-gray-400" />
            <span className="text-sm font-medium text-gray-600">Scan QR Code to Add Device</span>
          </div>
        </button>
      )}

      {/* Discovered Devices */}
      {discoveredDevices.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-md font-medium text-gray-700">Discovered Devices</h4>
          <div className="grid gap-3">
            {discoveredDevices.map((device) => (
              <motion.div
                key={device.deviceId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer"
                onClick={() => handleConnectDevice(device)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      device.metadata?.source === 'iot_core' ? 'bg-green-100' : 'bg-blue-100'
                    }`}>
                      {getDeviceIcon(device.type)}
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-900">{device.name}</h5>
                      <p className="text-sm text-gray-500">{device.deviceId}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        {device.metadata?.source === 'iot_core' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            IoT Core
                          </span>
                        )}
                        {device.metadata?.isBridged && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                            Active Device
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getConnectionIcon(device.connectionType)}
                    {device.signalStrength && (
                      <div className="flex items-center space-x-1">
                        <SignalIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">{device.signalStrength}dBm</span>
                      </div>
                    )}
                    {device.batteryLevel && (
                      <div className="flex items-center space-x-1">
                        <Battery0Icon className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">{device.batteryLevel}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Connected Devices */}
      {connectedDevices.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-md font-medium text-gray-700">Connected Devices</h4>
          <div className="grid gap-3">
            {connectedDevices.map((device) => (
              <motion.div
                key={device.deviceId}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 border border-green-200 bg-green-50 rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      {getDeviceIcon(device.type)}
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-900">{device.name}</h5>
                      <p className="text-sm text-gray-500">{device.deviceId}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <CheckCircleIcon className="w-4 h-4 text-green-500" />
                        <span className="text-xs text-green-600">Connected</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDisconnectDevice(device.deviceId)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Modal */}
      <AnimatePresence>
        {showConnectionModal && selectedDevice && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Connect Device</h3>
                <button
                  onClick={() => setShowConnectionModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    {getDeviceIcon(selectedDevice.type)}
                  </div>
                  <div>
                    <h4 className="font-medium">{selectedDevice.name}</h4>
                    <p className="text-sm text-gray-500">{selectedDevice.deviceId}</p>
                  </div>
                </div>

                {selectedDevice.connectionType === 'wifi' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        WiFi Network (SSID)
                      </label>
                      <input
                        type="text"
                        value={connectionConfig.parameters.ssid || ''}
                        onChange={(e) => setConnectionConfig(prev => ({
                          ...prev,
                          parameters: { ...prev.parameters, ssid: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter WiFi network name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        WiFi Password
                      </label>
                      <input
                        type="password"
                        value={connectionConfig.parameters.password || ''}
                        onChange={(e) => setConnectionConfig(prev => ({
                          ...prev,
                          parameters: { ...prev.parameters, password: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter WiFi password"
                      />
                    </div>
                  </div>
                )}

                {connectionError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                      <span className="text-sm text-red-700">{connectionError}</span>
                    </div>
                  </div>
                )}

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setShowConnectionModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmConnection}
                    disabled={isConnecting}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isConnecting ? 'Connecting...' : 'Connect'}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PluggableDeviceManager;