import React from 'react';
import { Shield, Search, AlertTriangle } from 'lucide-react';
import { mockThreatLevel, getThreatLevelColor } from '../../../data/mockSecurityAudit';

const ThreatLevelIndicator: React.FC = () => {
  const colors = getThreatLevelColor(mockThreatLevel.level);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Shield className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">System Threat Level</h3>
            <p className="text-xs text-gray-500">Security Status</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Threat Level Display */}
      <div className={`p-6 ${colors.bg} rounded-lg border-2 border-gray-200 mb-6`}>
        <div className="text-center">
          <div className="text-6xl mb-3">{colors.icon}</div>
          <p className="text-sm font-medium text-gray-600 mb-2">Current Threat Level</p>
          <p className={`text-4xl font-bold ${colors.text} mb-2`}>{mockThreatLevel.level}</p>
          <p className="text-xs text-gray-600">System is operating normally</p>
        </div>
      </div>

      {/* Security Metrics */}
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">Last Security Scan</span>
          </div>
          <span className="text-sm font-semibold text-blue-900">{mockThreatLevel.lastScan}</span>
        </div>

        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-gray-700">Vulnerabilities Found</span>
          </div>
          <span className="text-sm font-semibold text-green-900">{mockThreatLevel.vulnerabilitiesFound}</span>
        </div>
      </div>

      {/* Threat Level Legend */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Threat Levels</h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-lg">🟢</span>
            <span className="text-gray-700"><strong>Low:</strong> Normal operations, no threats detected</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">🟡</span>
            <span className="text-gray-700"><strong>Moderate:</strong> Minor issues detected, monitoring required</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">🔴</span>
            <span className="text-gray-700"><strong>High:</strong> Critical threats detected, immediate action required</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreatLevelIndicator;
