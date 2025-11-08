import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { PerformanceMetrics } from '../../types/admin';

interface PerformanceMetricsChartProps {
  metrics: PerformanceMetrics[];
  onTimeRangeChange: (range: '1h' | '24h' | '7d' | '30d') => void;
}

const PerformanceMetricsChart = ({ metrics, onTimeRangeChange }: PerformanceMetricsChartProps) => {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedMetric, setSelectedMetric] = useState<'latency' | 'throughput' | 'lambda' | 'dynamodb'>('latency');

  const handleTimeRangeChange = (range: '1h' | '24h' | '7d' | '30d') => {
    setTimeRange(range);
    onTimeRangeChange(range);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (timeRange === '1h') {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (timeRange === '24h') {
      return date.toLocaleTimeString([], { hour: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const chartData = metrics.map(m => ({
    timestamp: formatTimestamp(m.timestamp),
    avgLatency: m.avgAlertLatency,
    p95Latency: m.p95AlertLatency,
    p99Latency: m.p99AlertLatency,
    apiResponse: m.avgApiResponseTime,
    throughput: m.throughput,
    lambdaInvocations: m.lambdaInvocations / 1000, // Convert to thousands
    lambdaErrors: m.lambdaErrors,
    dynamodbRead: m.dynamodbReadCapacity,
    dynamodbWrite: m.dynamodbWriteCapacity
  }));

  const renderChart = () => {
    switch (selectedMetric) {
      case 'latency':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis label={{ value: 'Seconds', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="avgLatency" stroke="#3b82f6" name="Avg Alert Latency" strokeWidth={2} />
              <Line type="monotone" dataKey="p95Latency" stroke="#f59e0b" name="P95 Latency" strokeWidth={2} />
              <Line type="monotone" dataKey="p99Latency" stroke="#ef4444" name="P99 Latency" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      case 'throughput':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis label={{ value: 'Requests/sec', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="throughput" stroke="#10b981" name="Throughput" strokeWidth={2} />
              <Line type="monotone" dataKey="apiResponse" stroke="#8b5cf6" name="API Response (ms)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      case 'lambda':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="lambdaInvocations" stroke="#3b82f6" name="Invocations (K)" strokeWidth={2} />
              <Line type="monotone" dataKey="lambdaErrors" stroke="#ef4444" name="Errors" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      case 'dynamodb':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis label={{ value: 'Capacity Units', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="dynamodbRead" stroke="#3b82f6" name="Read Capacity" strokeWidth={2} />
              <Line type="monotone" dataKey="dynamodbWrite" stroke="#10b981" name="Write Capacity" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  const latestMetrics = metrics[metrics.length - 1];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Performance Metrics</h2>
        <div className="flex gap-2">
          {(['1h', '24h', '7d', '30d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => handleTimeRangeChange(range)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Selector */}
      <div className="flex gap-2 mb-4 overflow-x-auto">
        <button
          onClick={() => setSelectedMetric('latency')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            selectedMetric === 'latency'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-500'
              : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-gray-300'
          }`}
        >
          Alert Latency
        </button>
        <button
          onClick={() => setSelectedMetric('throughput')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            selectedMetric === 'throughput'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-500'
              : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-gray-300'
          }`}
        >
          Throughput & API
        </button>
        <button
          onClick={() => setSelectedMetric('lambda')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            selectedMetric === 'lambda'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-500'
              : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-gray-300'
          }`}
        >
          Lambda Functions
        </button>
        <button
          onClick={() => setSelectedMetric('dynamodb')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            selectedMetric === 'dynamodb'
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-500'
              : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-gray-300'
          }`}
        >
          DynamoDB
        </button>
      </div>

      {/* Chart */}
      <div className="mb-4">
        {renderChart()}
      </div>

      {/* Current Metrics Summary */}
      {latestMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          <div>
            <div className="text-xs text-gray-600">Avg Alert Latency</div>
            <div className={`text-lg font-bold ${
              latestMetrics.avgAlertLatency < 30 ? 'text-green-600' : 'text-red-600'
            }`}>
              {latestMetrics.avgAlertLatency.toFixed(1)}s
            </div>
            <div className="text-xs text-gray-500">Target: &lt;30s</div>
          </div>
          <div>
            <div className="text-xs text-gray-600">P95 Latency</div>
            <div className={`text-lg font-bold ${
              latestMetrics.p95AlertLatency < 30 ? 'text-green-600' : 'text-red-600'
            }`}>
              {latestMetrics.p95AlertLatency.toFixed(1)}s
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600">Throughput</div>
            <div className="text-lg font-bold text-blue-600">
              {latestMetrics.throughput.toFixed(0)} req/s
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600">Lambda Errors</div>
            <div className={`text-lg font-bold ${
              latestMetrics.lambdaErrors < 50 ? 'text-green-600' : 'text-red-600'
            }`}>
              {latestMetrics.lambdaErrors}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMetricsChart;
