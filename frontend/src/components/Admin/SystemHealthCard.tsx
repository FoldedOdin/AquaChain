import { SystemHealthMetrics } from '../../types/admin';

interface SystemHealthCardProps {
  metrics: SystemHealthMetrics;
}

const SystemHealthCard = ({ metrics }: SystemHealthCardProps) => {
  const getUptimeColor = (uptime: number) => {
    if (uptime >= 99.5) return 'text-green-600';
    if (uptime >= 98.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getErrorRateColor = (errorRate: number) => {
    if (errorRate <= 0.5) return 'text-green-600';
    if (errorRate <= 2.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">System Health</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Critical Path Uptime</div>
          <div className={`text-2xl font-bold ${getUptimeColor(metrics.criticalPathUptime)}`}>
            {metrics.criticalPathUptime.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Target: 99.5%</div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">API Uptime</div>
          <div className={`text-2xl font-bold ${getUptimeColor(metrics.apiUptime)}`}>
            {metrics.apiUptime.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Target: 99.0%</div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Notification Uptime</div>
          <div className={`text-2xl font-bold ${getUptimeColor(metrics.notificationUptime)}`}>
            {metrics.notificationUptime.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Target: 98.0%</div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Error Rate</div>
          <div className={`text-2xl font-bold ${getErrorRateColor(metrics.errorRate)}`}>
            {metrics.errorRate.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Target: &lt;0.5%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        <div className="border rounded-lg p-4 bg-blue-50">
          <div className="text-sm text-gray-600 mb-1">Active Devices</div>
          <div className="text-2xl font-bold text-blue-600">
            {metrics.activeDevices} / {metrics.totalDevices}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((metrics.activeDevices / metrics.totalDevices) * 100).toFixed(1)}% online
          </div>
        </div>

        <div className="border rounded-lg p-4 bg-yellow-50">
          <div className="text-sm text-gray-600 mb-1">Active Alerts</div>
          <div className="text-2xl font-bold text-yellow-600">
            {metrics.activeAlerts}
          </div>
          <div className="text-xs text-gray-500 mt-1">Requiring attention</div>
        </div>

        <div className="border rounded-lg p-4 bg-purple-50">
          <div className="text-sm text-gray-600 mb-1">Pending Service Requests</div>
          <div className="text-2xl font-bold text-purple-600">
            {metrics.pendingServiceRequests}
          </div>
          <div className="text-xs text-gray-500 mt-1">Awaiting assignment</div>
        </div>

        <div className="border rounded-lg p-4 bg-gray-50">
          <div className="text-sm text-gray-600 mb-1">Last Updated</div>
          <div className="text-sm font-medium text-gray-700">
            {new Date(metrics.timestamp).toLocaleTimeString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">Real-time monitoring</div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthCard;
