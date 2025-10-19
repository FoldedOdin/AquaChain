import React from 'react';
import { WaterQualityReading } from '../../types';

interface SensorReadingsProps {
  reading: WaterQualityReading;
}

const SensorReadings: React.FC<SensorReadingsProps> = ({ reading }) => {
  const getSensorStatus = (value: number, min: number, max: number) => {
    if (value < min || value > max) {
      return 'text-critical bg-red-50 border-red-200';
    }
    return 'text-gray-900 bg-white border-gray-200';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const sensorData = [
    {
      label: 'pH Level',
      value: reading.readings.pH.toFixed(1),
      unit: '',
      range: '6.5 - 8.5',
      status: getSensorStatus(reading.readings.pH, 6.5, 8.5),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      label: 'Turbidity',
      value: reading.readings.turbidity.toFixed(1),
      unit: 'NTU',
      range: '< 4.0',
      status: getSensorStatus(reading.readings.turbidity, 0, 4.0),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      label: 'TDS',
      value: reading.readings.tds.toFixed(0),
      unit: 'ppm',
      range: '< 500',
      status: getSensorStatus(reading.readings.tds, 0, 500),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      )
    },
    {
      label: 'Temperature',
      value: reading.readings.temperature.toFixed(1),
      unit: '°C',
      range: '0 - 40',
      status: getSensorStatus(reading.readings.temperature, 0, 40),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l3-3 3 3v13M9 19a3 3 0 106 0M9 19h6" />
        </svg>
      )
    },
    {
      label: 'Humidity',
      value: reading.readings.humidity.toFixed(1),
      unit: '%',
      range: '30 - 70',
      status: getSensorStatus(reading.readings.humidity, 30, 70),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
      )
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Current Readings</h3>
          <div className="text-sm text-gray-500">
            Last updated: {formatTimestamp(reading.timestamp)}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sensorData.map((sensor, index) => (
            <div
              key={index}
              className={`
                p-4 rounded-lg border-2 transition-all duration-200
                ${sensor.status}
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {sensor.icon}
                  <span className="text-sm font-medium">{sensor.label}</span>
                </div>
              </div>
              
              <div className="flex items-baseline space-x-1">
                <span className="text-2xl font-bold">
                  {sensor.value}
                </span>
                <span className="text-sm text-gray-500">
                  {sensor.unit}
                </span>
              </div>
              
              <div className="mt-1 text-xs text-gray-500">
                Safe range: {sensor.range}
              </div>
            </div>
          ))}
        </div>

        {/* Device Status */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`
                w-3 h-3 rounded-full
                ${reading.diagnostics.sensorStatus === 'normal' ? 'bg-green-400' : 'bg-red-400'}
              `}></div>
              <span className="text-sm font-medium text-gray-900">
                Device {reading.deviceId}
              </span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>{reading.diagnostics.signalStrength} dBm</span>
              </div>
              
              <div className="flex items-center space-x-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>{reading.diagnostics.batteryLevel}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SensorReadings;