import { WaterQualityReading, Alert } from '../types';

// Mock water quality reading data
export const mockWaterQualityReading: WaterQualityReading = {
  deviceId: 'DEV-3421',
  timestamp: new Date().toISOString(),
  location: {
    latitude: 37.7749,
    longitude: -122.4194
  },
  readings: {
    pH: 7.2,
    turbidity: 1.5,
    tds: 145,
    temperature: 24.5,
    humidity: 68.2
  },
  wqi: 85,
  anomalyType: 'normal',
  diagnostics: {
    batteryLevel: 85,
    signalStrength: -65,
    sensorStatus: 'normal'
  }
};

// Mock critical reading for testing
export const mockCriticalReading: WaterQualityReading = {
  deviceId: 'DEV-3421',
  timestamp: new Date().toISOString(),
  location: {
    latitude: 37.7749,
    longitude: -122.4194
  },
  readings: {
    pH: 4.2,
    turbidity: 8.5,
    tds: 650,
    temperature: 35.0,
    humidity: 85.0
  },
  wqi: 25,
  anomalyType: 'contamination',
  diagnostics: {
    batteryLevel: 65,
    signalStrength: -75,
    sensorStatus: 'warning'
  }
};

// Mock warning reading
export const mockWarningReading: WaterQualityReading = {
  deviceId: 'DEV-3421',
  timestamp: new Date().toISOString(),
  location: {
    latitude: 37.7749,
    longitude: -122.4194
  },
  readings: {
    pH: 6.0,
    turbidity: 3.5,
    tds: 450,
    temperature: 28.0,
    humidity: 75.0
  },
  wqi: 55,
  anomalyType: 'sensor_fault',
  diagnostics: {
    batteryLevel: 45,
    signalStrength: -70,
    sensorStatus: 'warning'
  }
};

// Mock alert history
export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    deviceId: 'DEV-3421',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    severity: 'critical',
    message: 'Critical water quality detected - pH level dangerously low (4.2)',
    wqi: 25,
    readings: {
      pH: 4.2,
      turbidity: 8.5,
      tds: 650,
      temperature: 35.0,
      humidity: 85.0
    }
  },
  {
    id: 'alert-2',
    deviceId: 'DEV-3422',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    severity: 'warning',
    message: 'High turbidity detected - water may be contaminated',
    wqi: 45,
    readings: {
      pH: 6.8,
      turbidity: 6.2,
      tds: 320,
      temperature: 26.0,
      humidity: 70.0
    }
  },
  {
    id: 'alert-3',
    deviceId: 'DEV-3421',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
    severity: 'warning',
    message: 'TDS levels elevated - check water source',
    wqi: 52,
    readings: {
      pH: 7.1,
      turbidity: 2.1,
      tds: 480,
      temperature: 25.5,
      humidity: 65.0
    }
  },
  {
    id: 'alert-4',
    deviceId: 'DEV-3422',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    severity: 'safe',
    message: 'Water quality restored to safe levels',
    wqi: 82,
    readings: {
      pH: 7.3,
      turbidity: 1.2,
      tds: 180,
      temperature: 23.0,
      humidity: 60.0
    }
  },
  {
    id: 'alert-5',
    deviceId: 'DEV-3421',
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    severity: 'critical',
    message: 'Sensor malfunction detected - technician dispatched',
    wqi: 0,
    readings: {
      pH: 0,
      turbidity: 0,
      tds: 0,
      temperature: 0,
      humidity: 0
    }
  }
];

// Function to get water quality status based on WQI
export const getWaterQualityStatus = (wqi: number): 'safe' | 'warning' | 'critical' => {
  if (wqi >= 60) return 'safe';
  if (wqi >= 40) return 'warning';
  return 'critical';
};

// Function to simulate real-time data updates
export const generateRandomReading = (baseReading: WaterQualityReading): WaterQualityReading => {
  const variation = 0.1; // 10% variation
  
  return {
    ...baseReading,
    timestamp: new Date().toISOString(),
    readings: {
      pH: Math.max(0, Math.min(14, baseReading.readings.pH + (Math.random() - 0.5) * variation * 2)),
      turbidity: Math.max(0, baseReading.readings.turbidity + (Math.random() - 0.5) * variation * 2),
      tds: Math.max(0, baseReading.readings.tds + (Math.random() - 0.5) * variation * 100),
      temperature: Math.max(-10, Math.min(50, baseReading.readings.temperature + (Math.random() - 0.5) * variation * 5)),
      humidity: Math.max(0, Math.min(100, baseReading.readings.humidity + (Math.random() - 0.5) * variation * 10))
    },
    wqi: Math.max(0, Math.min(100, baseReading.wqi + (Math.random() - 0.5) * variation * 20)),
    diagnostics: {
      ...baseReading.diagnostics,
      batteryLevel: Math.max(0, Math.min(100, baseReading.diagnostics.batteryLevel + (Math.random() - 0.5) * 2))
    }
  };
};