import React from 'react';
import { Brain, AlertTriangle, Activity, CheckCircle } from 'lucide-react';
import { mockAISecurityInsights, mockAIAlerts } from '../../../data/mockSecurityAudit';

const AISecurityInsights: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">AI Security Insights</h3>
            <p className="text-xs text-gray-500">ML Anomaly Detection</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
          <AlertTriangle className="w-6 h-6 text-red-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-red-900">{mockAISecurityInsights.contaminationAlerts}</p>
          <p className="text-xs text-gray-600 mt-1">Contamination Alerts</p>
        </div>

        <div className="text-center p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg border border-amber-200">
          <Activity className="w-6 h-6 text-amber-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-amber-900">{mockAISecurityInsights.sensorFaults}</p>
          <p className="text-xs text-gray-600 mt-1">Sensor Faults</p>
        </div>

        <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-green-900">{mockAISecurityInsights.falsePositives}</p>
          <p className="text-xs text-gray-600 mt-1">False Positives</p>
        </div>
      </div>

      {/* Recent AI Alerts */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent AI Alerts</h4>
        <div className="space-y-3">
          {mockAIAlerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  <span className="text-sm font-semibold text-purple-900">AI Alert</span>
                </div>
                <span className="text-xs text-gray-500">{alert.time}</span>
              </div>
              <p className="text-sm text-gray-800 mb-2">{alert.message}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">
                  <strong>Location:</strong> {alert.location}
                </span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded font-semibold">
                  Confidence: {alert.confidence}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Model Info */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">ML Model:</span>
          <span className="font-semibold text-gray-900">Random Forest Classifier v2.1</span>
        </div>
        <div className="flex items-center justify-between text-sm mt-2">
          <span className="text-gray-600">Detection Accuracy:</span>
          <span className="font-semibold text-green-600">99.74%</span>
        </div>
      </div>
    </div>
  );
};

export default AISecurityInsights;
