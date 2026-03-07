import React from 'react';
import { Brain, TrendingUp, AlertTriangle, Calendar, Activity, Target } from 'lucide-react';
import { mockMLStatus } from '../../../data/mockGlobalMonitoring';

const MLMonitoringPanel: React.FC = () => {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'HIGH':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 99) return 'text-green-600';
    if (accuracy >= 95) return 'text-blue-600';
    if (accuracy >= 90) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">AI Model Status</h3>
            <p className="text-xs text-gray-500">Machine Learning Monitoring</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Model Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-medium text-gray-600">Model Version</span>
          </div>
          <p className="text-lg font-bold text-purple-900">{mockMLStatus.modelVersion}</p>
          <p className="text-xs text-purple-700 mt-1">{mockMLStatus.modelType}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <span className="text-xs font-medium text-gray-600">Model Accuracy</span>
          </div>
          <p className={`text-3xl font-bold ${getAccuracyColor(mockMLStatus.accuracy)}`}>
            {mockMLStatus.accuracy}%
          </p>
          <p className="text-xs text-green-700 mt-1">Validation Dataset</p>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-medium text-gray-600">Anomalies Today</span>
          </div>
          <p className="text-2xl font-bold text-blue-900">{mockMLStatus.anomaliesToday}</p>
          <p className="text-xs text-blue-700 mt-1">Detected Issues</p>
        </div>

        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-indigo-600" />
            <span className="text-xs font-medium text-gray-600">Total Predictions</span>
          </div>
          <p className="text-2xl font-bold text-indigo-900">
            {mockMLStatus.totalPredictions.toLocaleString()}
          </p>
          <p className="text-xs text-indigo-700 mt-1">Lifetime</p>
        </div>

        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-medium text-gray-600">Last Training</span>
          </div>
          <p className="text-lg font-bold text-amber-900">{mockMLStatus.lastTraining}</p>
          <p className="text-xs text-amber-700 mt-1">Model Retrained</p>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">Predicted Contamination Risk</p>
            <p className="text-xs text-gray-500">Based on current water quality trends</p>
          </div>
          <div className={`px-4 py-2 rounded-lg border-2 font-bold text-lg ${getRiskColor(mockMLStatus.predictedRisk)}`}>
            {mockMLStatus.predictedRisk}
          </div>
        </div>
      </div>

      {/* Model Health Indicators */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Model Health Indicators</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Prediction Latency</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 rounded-full" style={{ width: '15%' }}></div>
              </div>
              <span className="text-sm font-medium text-green-600">~85ms</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Model Confidence</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '94%' }}></div>
              </div>
              <span className="text-sm font-medium text-blue-600">94%</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Data Quality Score</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: '97%' }}></div>
              </div>
              <span className="text-sm font-medium text-purple-600">97%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 pt-6 border-t border-gray-200 flex gap-3">
        <button className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium">
          View Model Details
        </button>
        <button className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
          Training History
        </button>
      </div>
    </div>
  );
};

export default MLMonitoringPanel;
