import { useState } from 'react';
import { DeviceFleetStatus } from '../../types/admin';

interface DeviceFleetOverviewProps {
  devices: DeviceFleetStatus[];
}

const DeviceFleetOverview = ({ devices }: DeviceFleetOverviewProps) => {
  const [filter, setFilter] = useState<'all' | 'online' | 'offline' | 'warning' | 'error'>('all');
  const [sortBy, setSortBy] = useState<'deviceId' | 'uptime' | 'wqi' | 'lastSeen'>('deviceId');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return '●';
      case 'offline': return '○';
      case 'warning': return '⚠';
      case 'error': return '✕';
      default: return '?';
    }
  };

  const filteredDevices = devices.filter(device => 
    filter === 'all' || device.status === filter
  );

  const sortedDevices = [...filteredDevices].sort((a, b) => {
    switch (sortBy) {
      case 'uptime':
        return b.uptime - a.uptime;
      case 'wqi':
        return b.currentWQI - a.currentWQI;
      case 'lastSeen':
        return new Date(b.lastSeen).getTime() - new Date(a.lastSeen).getTime();
      default:
        return a.deviceId.localeCompare(b.deviceId);
    }
  });

  const statusCounts = {
    online: devices.filter(d => d.status === 'online').length,
    offline: devices.filter(d => d.status === 'offline').length,
    warning: devices.filter(d => d.status === 'warning').length,
    error: devices.filter(d => d.status === 'error').length
  };

  const getTimeSince = (timestamp: string) => {
    const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Device Fleet Status</h2>
        <div className="text-sm text-gray-600">
          Total: {devices.length} devices
        </div>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`p-3 rounded-lg border-2 transition-colors ${
            filter === 'all' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-sm text-gray-600">All Devices</div>
          <div className="text-2xl font-bold">{devices.length}</div>
        </button>
        <button
          onClick={() => setFilter('online')}
          className={`p-3 rounded-lg border-2 transition-colors ${
            filter === 'online' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-sm text-gray-600">Online</div>
          <div className="text-2xl font-bold text-green-600">{statusCounts.online}</div>
        </button>
        <button
          onClick={() => setFilter('warning')}
          className={`p-3 rounded-lg border-2 transition-colors ${
            filter === 'warning' ? 'border-yellow-500 bg-yellow-50' : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-sm text-gray-600">Warning</div>
          <div className="text-2xl font-bold text-yellow-600">{statusCounts.warning}</div>
        </button>
        <button
          onClick={() => setFilter('offline')}
          className={`p-3 rounded-lg border-2 transition-colors ${
            filter === 'offline' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-sm text-gray-600">Offline</div>
          <div className="text-2xl font-bold text-red-600">{statusCounts.offline}</div>
        </button>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-4">
        <span className="text-sm text-gray-600 self-center">Sort by:</span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="px-3 py-1 border rounded-md text-sm"
        >
          <option value="deviceId">Device ID</option>
          <option value="uptime">Uptime</option>
          <option value="wqi">WQI</option>
          <option value="lastSeen">Last Seen</option>
        </select>
      </div>

      {/* Device List */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Consumer</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">WQI</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uptime</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Battery</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Seen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedDevices.map((device) => (
              <tr key={device.deviceId} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{device.deviceId}</div>
                  <div className="text-xs text-gray-500">{device.location.address}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
                    <span className="mr-1">{getStatusIcon(device.status)}</span>
                    {device.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900">{device.consumerName}</div>
                  <div className="text-xs text-gray-500">{device.consumerId}</div>
                </td>
                <td className="px-4 py-3">
                  <div className={`text-sm font-medium ${
                    device.currentWQI >= 60 ? 'text-green-600' :
                    device.currentWQI >= 40 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {device.currentWQI}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className={`text-sm ${
                    device.uptime >= 99 ? 'text-green-600' :
                    device.uptime >= 95 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {device.uptime.toFixed(1)}%
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center">
                    <div className={`text-sm ${
                      device.batteryLevel >= 50 ? 'text-green-600' :
                      device.batteryLevel >= 20 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {device.batteryLevel}%
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900">{getTimeSince(device.lastSeen)}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sortedDevices.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No devices found with status: {filter}
        </div>
      )}
    </div>
  );
};

export default DeviceFleetOverview;
