import React, { useState } from 'react';
import { MapPin, Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { mockDeviceLocations, getDeviceStatusColor } from '../../../data/mockGlobalMonitoring';

/**
 * Device Map Component
 * 
 * Note: This is a simplified map visualization without external dependencies.
 * For production, consider using react-leaflet or similar mapping library.
 */
const DeviceMap: React.FC = () => {
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <Wifi className="w-4 h-4 text-green-600" />;
      case 'offline':
        return <WifiOff className="w-4 h-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-amber-100 text-amber-800';
    }
  };

  // Group devices by location for better display
  const locationGroups = mockDeviceLocations.reduce((acc, device) => {
    const city = device.location.split(',')[0];
    if (!acc[city]) {
      acc[city] = [];
    }
    acc[city].push(device);
    return acc;
  }, {} as Record<string, typeof mockDeviceLocations>);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Device Map</h3>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Map Placeholder - Replace with actual map library in production */}
      <div className="relative bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 mb-4 min-h-[400px] border-2 border-dashed border-blue-200">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <MapPin className="w-16 h-16 text-blue-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 font-medium">Interactive Map Visualization</p>
            <p className="text-xs text-gray-500 mt-1">
              Production: Integrate react-leaflet or similar library
            </p>
          </div>
        </div>

        {/* Simulated map markers */}
        <div className="absolute top-1/4 left-1/4 animate-pulse">
          <div className="w-3 h-3 bg-green-500 rounded-full shadow-lg"></div>
        </div>
        <div className="absolute top-1/3 right-1/3 animate-pulse">
          <div className="w-3 h-3 bg-amber-500 rounded-full shadow-lg"></div>
        </div>
        <div className="absolute bottom-1/3 left-1/2 animate-pulse">
          <div className="w-3 h-3 bg-green-500 rounded-full shadow-lg"></div>
        </div>
        <div className="absolute top-1/2 right-1/4 animate-pulse">
          <div className="w-3 h-3 bg-red-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      {/* Device List by Location */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Devices by Location</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto">
          {Object.entries(locationGroups).map(([city, devices]) => (
            <div key={city} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-semibold text-gray-900">{city}</span>
                <span className="text-xs text-gray-500">({devices.length})</span>
              </div>
              <div className="space-y-2">
                {devices.map((device) => (
                  <div
                    key={device.device}
                    className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                      selectedDevice === device.device
                        ? 'bg-blue-100 border border-blue-300'
                        : 'bg-white hover:bg-gray-100 border border-gray-200'
                    }`}
                    onClick={() => setSelectedDevice(device.device)}
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {getStatusIcon(device.status)}
                      <span className="text-xs font-mono text-gray-700 truncate">
                        {device.device}
                      </span>
                    </div>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusBadge(device.status)}`}>
                      {device.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Device Details */}
      {selectedDevice && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h5 className="text-sm font-semibold text-gray-900 mb-2">Device Details</h5>
          {mockDeviceLocations
            .filter((d) => d.device === selectedDevice)
            .map((device) => (
              <div key={device.device} className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Device ID:</span>
                  <span className="font-mono text-gray-900">{device.device}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Location:</span>
                  <span className="text-gray-900">{device.location}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Coordinates:</span>
                  <span className="font-mono text-gray-900">
                    {device.lat.toFixed(4)}, {device.lng.toFixed(4)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Reading:</span>
                  <span className="text-gray-900">{device.lastReading}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusBadge(device.status)}`}>
                    {device.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Online</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
            <span className="text-gray-600">Warning</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-gray-600">Offline</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeviceMap;
