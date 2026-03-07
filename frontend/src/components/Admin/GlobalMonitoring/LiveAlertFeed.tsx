import React from 'react';
import { AlertTriangle, Info, AlertCircle, Clock } from 'lucide-react';
import { mockAlerts, getSeverityColor, type MockAlert } from '../../../data/mockGlobalMonitoring';

const LiveAlertFeed: React.FC = () => {
  const getSeverityIcon = (severity: MockAlert['severity']) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      case 'info':
        return <Info className="w-5 h-5" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Live Event Feed</h3>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {mockAlerts.map((alert) => {
          const colors = getSeverityColor(alert.severity);
          return (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border ${colors.bg} ${colors.border} transition-all hover:shadow-md`}
            >
              <div className="flex items-start gap-3">
                <div className={colors.icon}>
                  {getSeverityIcon(alert.severity)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded uppercase ${colors.badge}`}>
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {alert.time}
                    </span>
                  </div>
                  <p className={`text-sm font-medium ${colors.text} mb-1`}>
                    {alert.message}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-gray-600">
                    <span className="font-mono">{alert.device}</span>
                    <span>•</span>
                    <span>{alert.location}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium">
          View All Alerts →
        </button>
      </div>
    </div>
  );
};

export default LiveAlertFeed;
