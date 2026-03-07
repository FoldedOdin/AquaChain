import React from 'react';
import { MapPin, Activity, AlertCircle, TrendingUp } from 'lucide-react';
import { mockRegionalStats, getRegionalStatusColor } from '../../../data/mockGlobalMonitoring';

const RegionalStatistics: React.FC = () => {
  const getWQIColor = (wqi: number) => {
    if (wqi >= 90) return 'text-green-600';
    if (wqi >= 75) return 'text-blue-600';
    if (wqi >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getWQILabel = (wqi: number) => {
    if (wqi >= 90) return 'Excellent';
    if (wqi >= 75) return 'Good';
    if (wqi >= 60) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <MapPin className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Regional Statistics</h3>
            <p className="text-xs text-gray-500">Water Quality by Region</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      <div className="space-y-4">
        {mockRegionalStats.map((region) => (
          <div
            key={region.region}
            className="p-4 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-gray-600" />
                <h4 className="text-base font-semibold text-gray-900">{region.region}</h4>
              </div>
              <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getRegionalStatusColor(region.status)}`}>
                {region.status.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {/* Devices */}
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <Activity className="w-4 h-4 text-blue-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-blue-900">{region.devices}</p>
                <p className="text-xs text-gray-600 mt-1">Devices</p>
              </div>

              {/* Average WQI */}
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <TrendingUp className="w-4 h-4 text-green-600 mx-auto mb-1" />
                <p className={`text-2xl font-bold ${getWQIColor(region.avgWQI)}`}>
                  {region.avgWQI.toFixed(1)}
                </p>
                <p className="text-xs text-gray-600 mt-1">{getWQILabel(region.avgWQI)}</p>
              </div>

              {/* Alerts */}
              <div className="text-center p-3 bg-amber-50 rounded-lg">
                <AlertCircle className="w-4 h-4 text-amber-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-amber-900">{region.alerts}</p>
                <p className="text-xs text-gray-600 mt-1">Active Alerts</p>
              </div>
            </div>

            {/* WQI Progress Bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Water Quality Index</span>
                <span className="font-medium">{region.avgWQI.toFixed(1)}/100</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    region.avgWQI >= 90
                      ? 'bg-green-500'
                      : region.avgWQI >= 75
                      ? 'bg-blue-500'
                      : region.avgWQI >= 60
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${region.avgWQI}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Statistics */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">National Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Total Regions</p>
            <p className="text-xl font-bold text-blue-900">{mockRegionalStats.length}</p>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Total Devices</p>
            <p className="text-xl font-bold text-green-900">
              {mockRegionalStats.reduce((sum, r) => sum + r.devices, 0)}
            </p>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Avg WQI</p>
            <p className="text-xl font-bold text-purple-900">
              {(mockRegionalStats.reduce((sum, r) => sum + r.avgWQI, 0) / mockRegionalStats.length).toFixed(1)}
            </p>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Total Alerts</p>
            <p className="text-xl font-bold text-amber-900">
              {mockRegionalStats.reduce((sum, r) => sum + r.alerts, 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegionalStatistics;
