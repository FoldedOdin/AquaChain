import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { AlertAnalytics as AlertAnalyticsType } from '../../types/admin';

interface AlertAnalyticsProps {
  analytics: AlertAnalyticsType;
}

const AlertAnalytics = ({ analytics }: AlertAnalyticsProps): JSX.Element => {
  const severityData = [
    { name: 'Critical', value: analytics.criticalAlerts, color: '#ef4444' },
    { name: 'Warning', value: analytics.warningAlerts, color: '#f59e0b' },
    { name: 'Safe', value: analytics.safeAlerts, color: '#10b981' }
  ];

  const typeData = analytics.alertsByType.map(item => ({
    name: item.type.replace('_', ' '),
    value: item.count
  }));

  const deviceData = analytics.alertsByDevice.slice(0, 10); // Top 10 devices

  const COLORS = ['#ef4444', '#f59e0b', '#10b981'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Alert Analytics</h2>
        <div className="text-sm text-gray-600">{analytics.period}</div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Total Alerts</div>
          <div className="text-2xl font-bold text-gray-900">{analytics.totalAlerts}</div>
        </div>
        <div className="border rounded-lg p-4 bg-red-50">
          <div className="text-sm text-gray-600 mb-1">Critical</div>
          <div className="text-2xl font-bold text-red-600">{analytics.criticalAlerts}</div>
          <div className="text-xs text-gray-500 mt-1">
            {((analytics.criticalAlerts / analytics.totalAlerts) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="border rounded-lg p-4 bg-yellow-50">
          <div className="text-sm text-gray-600 mb-1">Warning</div>
          <div className="text-2xl font-bold text-yellow-600">{analytics.warningAlerts}</div>
          <div className="text-xs text-gray-500 mt-1">
            {((analytics.warningAlerts / analytics.totalAlerts) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="border rounded-lg p-4 bg-green-50">
          <div className="text-sm text-gray-600 mb-1">Avg Resolution Time</div>
          <div className="text-2xl font-bold text-green-600">{analytics.avgResolutionTime}m</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Alerts by Severity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Type Distribution */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Alerts by Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={typeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {typeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Devices by Alert Count */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Devices by Alert Count</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={deviceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="deviceId" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#3b82f6" name="Alert Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Device List */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Device Alert Details</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Device ID</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Alert Count</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {deviceData.map((device) => (
                <tr key={device.deviceId} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm font-medium text-gray-900">{device.deviceId}</td>
                  <td className="px-4 py-2 text-sm text-gray-700">{device.count}</td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${device.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      device.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                      {device.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AlertAnalytics;
