import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import { useDashboard } from "../../contexts/DashboardContext";
import { MockDataService } from "../../services/mockDataService";
import { SystemHealthData, TimeRange } from "../../types/dashboard";
import TimeRangeSelector from "../common/TimeRangeSelector";
import MockDataBadge from "../common/MockDataBadge";
import LoadingSkeleton from "../common/LoadingSkeleton";

/**
 * SystemHealthDashboard Component
 * 
 * Displays 4 time-series charts showing system health metrics:
 * - API Success Rate (LineChart)
 * - Device Connectivity (AreaChart with stacked areas)
 * - Sensor Data Trends (LineChart with 4 lines)
 * - ML Anomaly Detection (BarChart)
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 2.9, 2.10, 2.11
 */
const SystemHealthDashboard: React.FC = () => {
  const { lastRefreshTimestamp } = useDashboard();
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [data, setData] = useState<SystemHealthData | null>(null);

  useEffect(() => {
    const healthData = MockDataService.getSystemHealthData(timeRange);
    setData(healthData);
  }, [lastRefreshTimestamp, timeRange]);

  if (!data) {
    return <LoadingSkeleton count={4} />;
  }

  // Format data for stacked area chart (device connectivity)
  const connectivityData = data.deviceConnectivity.online.map((point, index) => ({
    timestamp: point.timestamp,
    online: point.value,
    warning: data.deviceConnectivity.warning[index]?.value || 0,
    offline: data.deviceConnectivity.offline[index]?.value || 0,
  }));

  // Format data for multi-line chart (sensor trends)
  const sensorData = data.sensorTrends.pH.map((point, index) => ({
    timestamp: point.timestamp,
    pH: point.value,
    turbidity: data.sensorTrends.turbidity[index]?.value || 0,
    tds: data.sensorTrends.tds[index]?.value || 0,
    temperature: data.sensorTrends.temperature[index]?.value || 0,
  }));

  // Calculate summary statistics for accessibility
  const avgSuccessRate =
    data.apiSuccessRate.reduce((sum, p) => sum + p.value, 0) /
    data.apiSuccessRate.length;
  const totalDevices =
    connectivityData[connectivityData.length - 1]?.online +
    connectivityData[connectivityData.length - 1]?.warning +
    connectivityData[connectivityData.length - 1]?.offline;
  const totalAnomalies = data.mlAnomalies.reduce((sum, p) => sum + p.value, 0);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          System Health
        </h2>
        <div className="flex items-center gap-4">
          <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          <MockDataBadge />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 lg:grid-cols-1">
        {/* API Success Rate Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Success Rate
          </h3>
          <div
            role="img"
            aria-label={`API Success Rate chart showing average success rate of ${avgSuccessRate.toFixed(
              2
            )}% over the selected time range`}
          >
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data.apiSuccessRate}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-gray-200 dark:stroke-gray-700"
                />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) => format(ts, "HH:mm")}
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Time"
                />
                <YAxis
                  domain={[95, 100]}
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Success Rate Percentage"
                />
                <Tooltip
                  labelFormatter={(ts) => format(ts, "PPpp")}
                  formatter={(value: number) => [
                    `${value.toFixed(2)}%`,
                    "Success Rate",
                  ]}
                  contentStyle={{
                    backgroundColor: "rgba(255, 255, 255, 0.95)",
                    border: "1px solid #e5e7eb",
                    borderRadius: "0.5rem",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  animationDuration={300}
                  name="Success Rate"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">
            The API success rate chart shows the percentage of successful API
            requests over time. The average success rate is{" "}
            {avgSuccessRate.toFixed(2)}%. Green indicates healthy performance
            above 95%.
          </p>
        </div>

        {/* Device Connectivity Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Device Connectivity
          </h3>
          <div
            role="img"
            aria-label={`Device Connectivity chart showing ${totalDevices} total devices with distribution across online, warning, and offline states`}
          >
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={connectivityData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-gray-200 dark:stroke-gray-700"
                />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) => format(ts, "HH:mm")}
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Time"
                />
                <YAxis
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Number of Devices"
                />
                <Tooltip
                  labelFormatter={(ts) => format(ts, "PPpp")}
                  contentStyle={{
                    backgroundColor: "rgba(255, 255, 255, 0.95)",
                    border: "1px solid #e5e7eb",
                    borderRadius: "0.5rem",
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="online"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  name="Online"
                  animationDuration={300}
                />
                <Area
                  type="monotone"
                  dataKey="warning"
                  stackId="1"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  name="Warning"
                  animationDuration={300}
                />
                <Area
                  type="monotone"
                  dataKey="offline"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#ef4444"
                  name="Offline"
                  animationDuration={300}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">
            The device connectivity chart shows the distribution of devices
            across three states over time. Green represents online devices,
            yellow represents devices with warnings, and red represents offline
            devices. Currently showing {totalDevices} total devices.
          </p>
        </div>

        {/* Sensor Data Trends Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Sensor Data Trends
          </h3>
          <div
            role="img"
            aria-label="Sensor Data Trends chart showing pH, turbidity, TDS, and temperature measurements over time"
          >
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={sensorData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-gray-200 dark:stroke-gray-700"
                />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) => format(ts, "HH:mm")}
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Time"
                />
                <YAxis
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Sensor Values"
                />
                <Tooltip
                  labelFormatter={(ts) => format(ts, "PPpp")}
                  contentStyle={{
                    backgroundColor: "rgba(255, 255, 255, 0.95)",
                    border: "1px solid #e5e7eb",
                    borderRadius: "0.5rem",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="pH"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="pH"
                  animationDuration={300}
                />
                <Line
                  type="monotone"
                  dataKey="turbidity"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={false}
                  name="Turbidity"
                  animationDuration={300}
                />
                <Line
                  type="monotone"
                  dataKey="tds"
                  stroke="#ec4899"
                  strokeWidth={2}
                  dot={false}
                  name="TDS"
                  animationDuration={300}
                />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Temperature"
                  animationDuration={300}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">
            The sensor data trends chart displays four water quality parameters
            over time. Blue line shows pH levels (target 6.5-8.5), purple shows
            turbidity in NTU, pink shows Total Dissolved Solids (TDS) in ppm,
            and orange shows temperature in Celsius. All measurements are
            averaged across the device fleet.
          </p>
        </div>

        {/* ML Anomaly Detection Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            ML Anomaly Detection
          </h3>
          <div
            role="img"
            aria-label={`ML Anomaly Detection chart showing ${totalAnomalies} total anomalies detected over the selected time range`}
          >
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.mlAnomalies}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-gray-200 dark:stroke-gray-700"
                />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) => format(ts, "HH:mm")}
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Time"
                />
                <YAxis
                  className="text-xs text-gray-600 dark:text-gray-400"
                  aria-label="Number of Anomalies"
                />
                <Tooltip
                  labelFormatter={(ts) => format(ts, "PPpp")}
                  formatter={(value: number) => [value, "Anomalies"]}
                  contentStyle={{
                    backgroundColor: "rgba(255, 255, 255, 0.95)",
                    border: "1px solid #e5e7eb",
                    borderRadius: "0.5rem",
                  }}
                />
                <Bar
                  dataKey="value"
                  fill="#ef4444"
                  name="Anomalies"
                  animationDuration={300}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">
            The ML anomaly detection chart shows the number of water quality
            anomalies detected by the machine learning model per hour. Red bars
            indicate periods with detected anomalies. Total anomalies detected:{" "}
            {totalAnomalies}. Higher bars indicate more anomalies requiring
            investigation.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthDashboard;
