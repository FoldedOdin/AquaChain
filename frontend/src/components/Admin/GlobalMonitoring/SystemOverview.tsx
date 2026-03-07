import React from 'react';
import { Server, Wifi, WifiOff, AlertTriangle, Activity, Database, Zap } from 'lucide-react';
import { mockSystemStats } from '../../../data/mockGlobalMonitoring';

const SystemOverview: React.FC = () => {
  const deviceOnlinePercentage = ((mockSystemStats.onlineDevices / mockSystemStats.totalDevices) * 100).toFixed(1);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Server className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">System Overview</h3>
            <p className="text-xs text-gray-500">Real-time System Metrics</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <Server className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-medium text-gray-600">Total Devices</span>
          </div>
          <p className="text-3xl font-bold text-blue-900">{mockSystemStats.totalDevices}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <Wifi className="w-4 h-4 text-green-600" />
            <span className="text-xs font-medium text-gray-600">Online</span>
          </div>
          <p className="text-3xl font-bold text-green-900">{mockSystemStats.onlineDevices}</p>
          <p className="text-xs text-green-700 mt-1">{deviceOnlinePercentage}% uptime</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <WifiOff className="w-4 h-4 text-red-600" />
            <span className="text-xs font-medium text-gray-600">Offline</span>
          </div>
          <p className="text-3xl font-bold text-red-900">{mockSystemStats.offlineDevices}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg border border-amber-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-medium text-gray-600">Warnings</span>
          </div>
          <p className="text-3xl font-bold text-amber-900">{mockSystemStats.devicesWithWarnings}</p>
        </div>
      </div>

      {/* Alert Statistics */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">24-Hour Alert Summary</h4>
        <div className="grid grid-cols-4 gap-3">
          <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-gray-900">{mockSystemStats.totalAlerts24h}</p>
            <p className="text-xs text-gray-600 mt-1">Total Alerts</p>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
            <p className="text-2xl font-bold text-red-900">{mockSystemStats.criticalAlerts}</p>
            <p className="text-xs text-gray-600 mt-1">Critical</p>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg border border-amber-200">
            <p className="text-2xl font-bold text-amber-900">{mockSystemStats.warningAlerts}</p>
            <p className="text-xs text-gray-600 mt-1">Warning</p>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-2xl font-bold text-blue-900">{mockSystemStats.infoAlerts}</p>
            <p className="text-xs text-gray-600 mt-1">Info</p>
          </div>
        </div>
      </div>

      {/* System Performance */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">System Performance</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border border-purple-200">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Average System WQI</p>
                <p className="text-xs text-gray-600">Water Quality Index</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-purple-900">{mockSystemStats.avgSystemWQI}</p>
              <p className="text-xs text-purple-700">Good Quality</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg border border-indigo-200">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-indigo-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Data Points Today</p>
                <p className="text-xs text-gray-600">Sensor Readings</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-indigo-900">
                {mockSystemStats.dataPointsToday.toLocaleString()}
              </p>
              <p className="text-xs text-indigo-700">Collected</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-cyan-50 to-cyan-100 rounded-lg border border-cyan-200">
            <div className="flex items-center gap-3">
              <Zap className="w-5 h-5 text-cyan-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">ML Predictions Today</p>
                <p className="text-xs text-gray-600">AI Analysis</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-cyan-900">
                {mockSystemStats.mlPredictionsToday.toLocaleString()}
              </p>
              <p className="text-xs text-cyan-700">Processed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Device Status Distribution */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Device Status Distribution</h4>
        <div className="space-y-2">
          <div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>Online Devices</span>
              <span className="font-medium">{mockSystemStats.onlineDevices} ({deviceOnlinePercentage}%)</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full transition-all"
                style={{ width: `${deviceOnlinePercentage}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>Devices with Warnings</span>
              <span className="font-medium">
                {mockSystemStats.devicesWithWarnings} (
                {((mockSystemStats.devicesWithWarnings / mockSystemStats.totalDevices) * 100).toFixed(1)}%)
              </span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 rounded-full transition-all"
                style={{
                  width: `${(mockSystemStats.devicesWithWarnings / mockSystemStats.totalDevices) * 100}%`
                }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>Offline Devices</span>
              <span className="font-medium">
                {mockSystemStats.offlineDevices} (
                {((mockSystemStats.offlineDevices / mockSystemStats.totalDevices) * 100).toFixed(1)}%)
              </span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500 rounded-full transition-all"
                style={{ width: `${(mockSystemStats.offlineDevices / mockSystemStats.totalDevices) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview;
