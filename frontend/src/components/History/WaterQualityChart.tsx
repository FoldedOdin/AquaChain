import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface DataPoint {
  timestamp: string;
  pH: number;
  turbidity: number;
  tds: number;
  temperature: number;
  humidity: number;
  wqi: number;
}

interface WaterQualityChartProps {
  data: DataPoint[];
  selectedMetrics: string[];
  showMovingAverage?: boolean;
}

const WaterQualityChart: React.FC<WaterQualityChartProps> = ({ 
  data, 
  selectedMetrics,
  showMovingAverage = false 
}) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatTooltipTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Calculate moving average for WQI
  const calculateMovingAverage = (data: DataPoint[], windowSize: number = 5) => {
    return data.map((point, index) => {
      const start = Math.max(0, index - Math.floor(windowSize / 2));
      const end = Math.min(data.length, index + Math.ceil(windowSize / 2));
      const window = data.slice(start, end);
      const average = window.reduce((sum, p) => sum + p.wqi, 0) / window.length;
      return {
        ...point,
        wqiMovingAvg: Math.round(average * 10) / 10
      };
    });
  };

  const chartData = showMovingAverage ? calculateMovingAverage(data) : data;

  const metricConfigs = {
    wqi: { 
      color: '#3b82f6', 
      name: 'Water Quality Index',
      yAxisId: 'wqi',
      domain: [0, 100]
    },
    pH: { 
      color: '#10b981', 
      name: 'pH Level',
      yAxisId: 'pH',
      domain: [0, 14]
    },
    turbidity: { 
      color: '#f59e0b', 
      name: 'Turbidity (NTU)',
      yAxisId: 'turbidity',
      domain: [0, 'dataMax']
    },
    tds: { 
      color: '#ef4444', 
      name: 'TDS (ppm)',
      yAxisId: 'tds',
      domain: [0, 'dataMax']
    },
    temperature: { 
      color: '#8b5cf6', 
      name: 'Temperature (°C)',
      yAxisId: 'temp',
      domain: [0, 50]
    },
    humidity: { 
      color: '#06b6d4', 
      name: 'Humidity (%)',
      yAxisId: 'humidity',
      domain: [0, 100]
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">
            {formatTooltipTimestamp(label)}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.dataKey === 'pH' ? '' : 
               entry.dataKey === 'turbidity' ? ' NTU' :
               entry.dataKey === 'tds' ? ' ppm' :
               entry.dataKey === 'temperature' ? '°C' :
               entry.dataKey === 'humidity' ? '%' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Get unique Y-axis IDs from selected metrics
  const yAxisIds = Array.from(new Set(selectedMetrics.map(metric => metricConfigs[metric as keyof typeof metricConfigs]?.yAxisId)));

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900">Water Quality Trends</h3>
        <p className="text-sm text-gray-500">Historical data visualization with trend analysis</p>
      </div>

      <div style={{ width: '100%', height: '400px' }}>
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            
            <XAxis 
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              stroke="#6b7280"
              fontSize={12}
              interval="preserveStartEnd"
            />
            
            {/* Dynamic Y-axes based on selected metrics */}
            {yAxisIds.includes('wqi') && (
              <YAxis 
                yAxisId="wqi"
                orientation="left"
                domain={[0, 100]}
                stroke="#3b82f6"
                fontSize={12}
              />
            )}
            
            {yAxisIds.includes('pH') && (
              <YAxis 
                yAxisId="pH"
                orientation="right"
                domain={[0, 14]}
                stroke="#10b981"
                fontSize={12}
              />
            )}
            
            {(yAxisIds.includes('turbidity') || yAxisIds.includes('tds') || 
              yAxisIds.includes('temp') || yAxisIds.includes('humidity')) && (
              <YAxis 
                yAxisId={yAxisIds.find(id => ['turbidity', 'tds', 'temp', 'humidity'].includes(id)) || 'left'}
                orientation="left"
                stroke="#6b7280"
                fontSize={12}
              />
            )}

            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Reference lines for safe ranges */}
            {selectedMetrics.includes('pH') && (
              <>
                <ReferenceLine yAxisId="pH" y={6.5} stroke="#10b981" strokeDasharray="2 2" />
                <ReferenceLine yAxisId="pH" y={8.5} stroke="#10b981" strokeDasharray="2 2" />
              </>
            )}
            
            {selectedMetrics.includes('wqi') && (
              <>
                <ReferenceLine yAxisId="wqi" y={60} stroke="#f59e0b" strokeDasharray="2 2" />
                <ReferenceLine yAxisId="wqi" y={80} stroke="#10b981" strokeDasharray="2 2" />
              </>
            )}

            {/* Render lines for selected metrics */}
            {selectedMetrics.map((metric) => {
              const config = metricConfigs[metric as keyof typeof metricConfigs];
              if (!config) return null;
              
              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ fill: config.color, strokeWidth: 2, r: 3 }}
                  activeDot={{ r: 5, stroke: config.color, strokeWidth: 2 }}
                  name={config.name}
                  yAxisId={config.yAxisId}
                  connectNulls={false}
                />
              );
            })}

            {/* Moving average line for WQI */}
            {showMovingAverage && selectedMetrics.includes('wqi') && (
              <Line
                type="monotone"
                dataKey="wqiMovingAvg"
                stroke="#1d4ed8"
                strokeWidth={3}
                strokeDasharray="5 5"
                dot={false}
                name="WQI Moving Average"
                yAxisId="wqi"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <div>• Green dashed lines: Safe pH range (6.5-8.5)</div>
          <div>• Yellow dashed line: WQI warning threshold (60)</div>
          <div>• Green dashed line: WQI good threshold (80)</div>
        </div>
      </div>
    </div>
  );
};

export default WaterQualityChart;