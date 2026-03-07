import React, { useState } from 'react';
import { MapPin, Globe } from 'lucide-react';
import { mockLoginLocations } from '../../../data/mockSecurityAudit';

const GeoSecurityMap: React.FC = () => {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const totalLogins = mockLoginLocations.reduce((sum, loc) => sum + loc.logins, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-100 rounded-lg">
            <Globe className="w-6 h-6 text-cyan-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Login Activity Map</h3>
            <p className="text-xs text-gray-500">Geographic Distribution</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Map Placeholder */}
      <div className="relative bg-gradient-to-br from-cyan-50 to-blue-50 rounded-lg p-6 mb-4 min-h-[300px] border-2 border-dashed border-cyan-200">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <Globe className="w-16 h-16 text-cyan-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 font-medium">Interactive World Map</p>
            <p className="text-xs text-gray-500 mt-1">
              Production: Integrate react-simple-maps or similar library
            </p>
          </div>
        </div>

        {/* Simulated map markers */}
        <div className="absolute top-1/3 left-1/4 animate-pulse">
          <div className="w-4 h-4 bg-blue-500 rounded-full shadow-lg"></div>
        </div>
        <div className="absolute top-1/2 right-1/3 animate-pulse">
          <div className="w-3 h-3 bg-green-500 rounded-full shadow-lg"></div>
        </div>
        <div className="absolute bottom-1/3 left-1/2 animate-pulse">
          <div className="w-3 h-3 bg-purple-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      {/* Country List */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Login Activity by Country</h4>
        <div className="space-y-2">
          {mockLoginLocations.map((location) => {
            const percentage = ((location.logins / totalLogins) * 100).toFixed(1);
            return (
              <div
                key={location.country}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedCountry === location.country
                    ? 'bg-cyan-100 border-cyan-300'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                }`}
                onClick={() => setSelectedCountry(location.country)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-cyan-600" />
                    <span className="text-sm font-semibold text-gray-900">{location.country}</span>
                  </div>
                  <span className="text-sm font-bold text-cyan-600">{location.logins} logins</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
                <div className="flex items-center justify-between mt-1 text-xs text-gray-600">
                  <span>{percentage}% of total</span>
                  <span className="font-mono">
                    {location.lat.toFixed(2)}, {location.lng.toFixed(2)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Total Countries</p>
            <p className="text-2xl font-bold text-cyan-900">{mockLoginLocations.length}</p>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Total Logins</p>
            <p className="text-2xl font-bold text-blue-900">{totalLogins}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeoSecurityMap;
