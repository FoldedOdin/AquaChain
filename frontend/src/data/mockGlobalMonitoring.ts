/**
 * Mock Data for Global Monitoring Dashboard
 * 
 * This file contains simulated data for demonstration purposes.
 * All data is frontend-only and does not connect to backend services.
 */

export interface MockAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  device: string;
  location: string;
  time: string;
  timestamp: Date;
}

export interface MockDeviceLocation {
  device: string;
  lat: number;
  lng: number;
  status: 'online' | 'offline' | 'warning';
  location: string;
  lastReading: string;
}

export interface MockMLStatus {
  modelVersion: string;
  modelType: string;
  accuracy: number;
  anomaliesToday: number;
  predictedRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  lastTraining: string;
  totalPredictions: number;
}

export interface MockRegionalStats {
  region: string;
  devices: number;
  avgWQI: number;
  alerts: number;
  status: 'good' | 'warning' | 'critical';
}

// Live Alert Feed (Simulated)
export const mockAlerts: MockAlert[] = [
  {
    id: 'alert-1',
    severity: 'critical',
    message: 'pH spike detected - Immediate attention required',
    device: 'ESP32-B21',
    location: 'Bangalore, Karnataka',
    time: '2 minutes ago',
    timestamp: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 'alert-2',
    severity: 'warning',
    message: 'Turbidity increasing above threshold',
    device: 'ESP32-A44',
    location: 'Kochi, Kerala',
    time: '8 minutes ago',
    timestamp: new Date(Date.now() - 8 * 60 * 1000)
  },
  {
    id: 'alert-3',
    severity: 'info',
    message: 'Device calibration completed successfully',
    device: 'ESP32-D10',
    location: 'Chennai, Tamil Nadu',
    time: '15 minutes ago',
    timestamp: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: 'alert-4',
    severity: 'warning',
    message: 'TDS levels elevated - Monitoring required',
    device: 'ESP32-C33',
    location: 'Hyderabad, Telangana',
    time: '23 minutes ago',
    timestamp: new Date(Date.now() - 23 * 60 * 1000)
  },
  {
    id: 'alert-5',
    severity: 'critical',
    message: 'Device offline - Connection lost',
    device: 'ESP32-E55',
    location: 'Mumbai, Maharashtra',
    time: '35 minutes ago',
    timestamp: new Date(Date.now() - 35 * 60 * 1000)
  },
  {
    id: 'alert-6',
    severity: 'info',
    message: 'Firmware update completed',
    device: 'ESP32-F12',
    location: 'Pune, Maharashtra',
    time: '42 minutes ago',
    timestamp: new Date(Date.now() - 42 * 60 * 1000)
  },
  {
    id: 'alert-7',
    severity: 'warning',
    message: 'Temperature anomaly detected',
    device: 'ESP32-G88',
    location: 'Thiruvananthapuram, Kerala',
    time: '1 hour ago',
    timestamp: new Date(Date.now() - 60 * 60 * 1000)
  },
  {
    id: 'alert-8',
    severity: 'info',
    message: 'Scheduled maintenance reminder',
    device: 'ESP32-H99',
    location: 'Coimbatore, Tamil Nadu',
    time: '1 hour ago',
    timestamp: new Date(Date.now() - 65 * 60 * 1000)
  }
];

// Device Locations for Map (Simulated)
export const mockDeviceLocations: MockDeviceLocation[] = [
  {
    device: 'ESP32-A1',
    lat: 9.9312,
    lng: 76.2673,
    status: 'online',
    location: 'Kochi, Kerala',
    lastReading: '30 seconds ago'
  },
  {
    device: 'ESP32-B2',
    lat: 12.9716,
    lng: 77.5946,
    status: 'warning',
    location: 'Bangalore, Karnataka',
    lastReading: '1 minute ago'
  },
  {
    device: 'ESP32-C3',
    lat: 13.0827,
    lng: 80.2707,
    status: 'online',
    location: 'Chennai, Tamil Nadu',
    lastReading: '45 seconds ago'
  },
  {
    device: 'ESP32-D4',
    lat: 17.3850,
    lng: 78.4867,
    status: 'online',
    location: 'Hyderabad, Telangana',
    lastReading: '20 seconds ago'
  },
  {
    device: 'ESP32-E5',
    lat: 19.0760,
    lng: 72.8777,
    status: 'offline',
    location: 'Mumbai, Maharashtra',
    lastReading: '35 minutes ago'
  },
  {
    device: 'ESP32-F6',
    lat: 18.5204,
    lng: 73.8567,
    status: 'online',
    location: 'Pune, Maharashtra',
    lastReading: '15 seconds ago'
  },
  {
    device: 'ESP32-G7',
    lat: 8.5241,
    lng: 76.9366,
    status: 'online',
    location: 'Thiruvananthapuram, Kerala',
    lastReading: '50 seconds ago'
  },
  {
    device: 'ESP32-H8',
    lat: 11.0168,
    lng: 76.9558,
    status: 'online',
    location: 'Coimbatore, Tamil Nadu',
    lastReading: '25 seconds ago'
  },
  {
    device: 'ESP32-I9',
    lat: 15.2993,
    lng: 74.1240,
    status: 'online',
    location: 'Goa',
    lastReading: '40 seconds ago'
  },
  {
    device: 'ESP32-J10',
    lat: 23.0225,
    lng: 72.5714,
    status: 'warning',
    location: 'Ahmedabad, Gujarat',
    lastReading: '2 minutes ago'
  }
];

// ML Model Status (Simulated)
export const mockMLStatus: MockMLStatus = {
  modelVersion: 'XGBoost v2.1.0',
  modelType: 'Water Quality Classifier',
  accuracy: 99.74,
  anomaliesToday: 7,
  predictedRisk: 'LOW',
  lastTraining: '2024-03-05',
  totalPredictions: 45823
};

// Regional Statistics (Simulated)
export const mockRegionalStats: MockRegionalStats[] = [
  {
    region: 'Kerala',
    devices: 28,
    avgWQI: 87.5,
    alerts: 2,
    status: 'good'
  },
  {
    region: 'Karnataka',
    devices: 35,
    avgWQI: 72.3,
    alerts: 5,
    status: 'warning'
  },
  {
    region: 'Tamil Nadu',
    devices: 42,
    avgWQI: 91.2,
    alerts: 1,
    status: 'good'
  },
  {
    region: 'Telangana',
    devices: 19,
    avgWQI: 78.9,
    alerts: 3,
    status: 'good'
  },
  {
    region: 'Maharashtra',
    devices: 51,
    avgWQI: 65.4,
    alerts: 8,
    status: 'warning'
  },
  {
    region: 'Gujarat',
    devices: 23,
    avgWQI: 69.7,
    alerts: 4,
    status: 'warning'
  }
];

// System-wide Statistics (Simulated)
export const mockSystemStats = {
  totalDevices: 198,
  onlineDevices: 187,
  offlineDevices: 11,
  devicesWithWarnings: 15,
  totalAlerts24h: 23,
  criticalAlerts: 2,
  warningAlerts: 8,
  infoAlerts: 13,
  avgSystemWQI: 78.6,
  dataPointsToday: 285420,
  mlPredictionsToday: 12847
};

// Helper function to get severity color
export const getSeverityColor = (severity: MockAlert['severity']) => {
  switch (severity) {
    case 'critical':
      return {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        badge: 'bg-red-100 text-red-800',
        icon: 'text-red-600'
      };
    case 'warning':
      return {
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-700',
        badge: 'bg-amber-100 text-amber-800',
        icon: 'text-amber-600'
      };
    case 'info':
      return {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-700',
        badge: 'bg-blue-100 text-blue-800',
        icon: 'text-blue-600'
      };
  }
};

// Helper function to get device status color
export const getDeviceStatusColor = (status: MockDeviceLocation['status']) => {
  switch (status) {
    case 'online':
      return '#10b981'; // green-500
    case 'warning':
      return '#f59e0b'; // amber-500
    case 'offline':
      return '#ef4444'; // red-500
  }
};

// Helper function to get regional status color
export const getRegionalStatusColor = (status: MockRegionalStats['status']) => {
  switch (status) {
    case 'good':
      return 'bg-green-100 text-green-800';
    case 'warning':
      return 'bg-amber-100 text-amber-800';
    case 'critical':
      return 'bg-red-100 text-red-800';
  }
};
