/**
 * Mock Data for Security & Audit Dashboard
 * 
 * This file contains simulated security and audit data for demonstration purposes.
 * All data is frontend-only and does not connect to backend services.
 */

export interface MockAuthActivity {
  successfulLogins24h: number;
  failedLogins: number;
  blockedAccounts: number;
  mfaEnabledPercentage: number;
}

export interface MockLoginEvent {
  id: string;
  user: string;
  action: string;
  ip: string;
  location: string;
  time: string;
  timestamp: Date;
  status: 'success' | 'failed' | 'blocked';
}

export interface MockSecurityEvent {
  id: string;
  time: string;
  event: string;
  user: string;
  status: 'Success' | 'Completed' | 'Logged' | 'Failed';
  timestamp: Date;
}

export interface MockLedgerIntegrity {
  entriesVerified: number;
  lastCheck: string;
  hashVerification: 'SUCCESS' | 'FAILED';
  tamperDetection: 'None' | 'Detected';
}

export interface MockAISecurityInsights {
  contaminationAlerts: number;
  sensorFaults: number;
  falsePositives: number;
}

export interface MockAIAlert {
  id: string;
  message: string;
  location: string;
  confidence: number;
  timestamp: Date;
  time: string;
}

export interface MockThreatLevel {
  level: 'LOW' | 'MODERATE' | 'HIGH';
  lastScan: string;
  vulnerabilitiesFound: number;
}

export interface MockLoginLocation {
  country: string;
  logins: number;
  lat: number;
  lng: number;
}

export interface MockBackupInfo {
  verification: 'Passed' | 'Failed';
  lastRestoreTest: string;
  backupSize: string;
  nextScheduledBackup: string;
}

// Authentication Activity Mock Data
export const mockAuthActivity: MockAuthActivity = {
  successfulLogins24h: 148,
  failedLogins: 6,
  blockedAccounts: 1,
  mfaEnabledPercentage: 87
};

// Recent Login Events
export const mockLoginEvents: MockLoginEvent[] = [
  {
    id: 'login-1',
    user: 'admin@aquachain.io',
    action: 'Login Success',
    ip: '49.37.122.11',
    location: 'Kochi, India',
    time: '10:34 AM',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    status: 'success'
  },
  {
    id: 'login-2',
    user: 'technician01@aquachain.io',
    action: 'Login Success',
    ip: '103.21.58.132',
    location: 'Bangalore, India',
    time: '09:52 AM',
    timestamp: new Date(Date.now() - 57 * 60 * 1000),
    status: 'success'
  },
  {
    id: 'login-3',
    user: 'consumer@example.com',
    action: 'Login Failed',
    ip: '157.45.201.88',
    location: 'Chennai, India',
    time: '09:15 AM',
    timestamp: new Date(Date.now() - 94 * 60 * 1000),
    status: 'failed'
  },
  {
    id: 'login-4',
    user: 'admin@aquachain.io',
    action: 'Login Success',
    ip: '49.37.122.11',
    location: 'Kochi, India',
    time: '08:30 AM',
    timestamp: new Date(Date.now() - 139 * 60 * 1000),
    status: 'success'
  },
  {
    id: 'login-5',
    user: 'suspicious@test.com',
    action: 'Login Blocked',
    ip: '185.220.101.45',
    location: 'Unknown',
    time: '07:45 AM',
    timestamp: new Date(Date.now() - 184 * 60 * 1000),
    status: 'blocked'
  }
];

// Recent Security Events (Audit Log)
export const mockSecurityEvents: MockSecurityEvent[] = [
  {
    id: 'event-1',
    time: '14:21',
    event: 'User Login',
    user: 'technician01',
    status: 'Success',
    timestamp: new Date(Date.now() - 10 * 60 * 1000)
  },
  {
    id: 'event-2',
    time: '14:10',
    event: 'Password Reset',
    user: 'admin',
    status: 'Completed',
    timestamp: new Date(Date.now() - 21 * 60 * 1000)
  },
  {
    id: 'event-3',
    time: '13:55',
    event: 'API Key Generated',
    user: 'admin',
    status: 'Logged',
    timestamp: new Date(Date.now() - 36 * 60 * 1000)
  },
  {
    id: 'event-4',
    time: '13:40',
    event: 'Device Certificate Issued',
    user: 'system',
    status: 'Success',
    timestamp: new Date(Date.now() - 51 * 60 * 1000)
  },
  {
    id: 'event-5',
    time: '13:25',
    event: 'User Role Updated',
    user: 'admin',
    status: 'Completed',
    timestamp: new Date(Date.now() - 66 * 60 * 1000)
  },
  {
    id: 'event-6',
    time: '13:10',
    event: 'Backup Initiated',
    user: 'system',
    status: 'Success',
    timestamp: new Date(Date.now() - 81 * 60 * 1000)
  },
  {
    id: 'event-7',
    time: '12:55',
    event: 'Configuration Changed',
    user: 'admin',
    status: 'Logged',
    timestamp: new Date(Date.now() - 96 * 60 * 1000)
  },
  {
    id: 'event-8',
    time: '12:40',
    event: 'Device Decommissioned',
    user: 'technician02',
    status: 'Completed',
    timestamp: new Date(Date.now() - 111 * 60 * 1000)
  }
];

// Ledger Integrity Data
export const mockLedgerIntegrity: MockLedgerIntegrity = {
  entriesVerified: 1284,
  lastCheck: '12 minutes ago',
  hashVerification: 'SUCCESS',
  tamperDetection: 'None'
};

// AI Security Insights
export const mockAISecurityInsights: MockAISecurityInsights = {
  contaminationAlerts: 2,
  sensorFaults: 1,
  falsePositives: 0
};

// AI Alert Events
export const mockAIAlerts: MockAIAlert[] = [
  {
    id: 'ai-alert-1',
    message: 'Turbidity spike detected',
    location: 'Node DEV-1205',
    confidence: 92,
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    time: '45 minutes ago'
  },
  {
    id: 'ai-alert-2',
    message: 'pH anomaly pattern identified',
    location: 'Node DEV-0842',
    confidence: 87,
    timestamp: new Date(Date.now() - 120 * 60 * 1000),
    time: '2 hours ago'
  },
  {
    id: 'ai-alert-3',
    message: 'Sensor calibration drift detected',
    location: 'Node DEV-1567',
    confidence: 94,
    timestamp: new Date(Date.now() - 180 * 60 * 1000),
    time: '3 hours ago'
  }
];

// System Threat Level
export const mockThreatLevel: MockThreatLevel = {
  level: 'LOW',
  lastScan: '2 hours ago',
  vulnerabilitiesFound: 0
};

// Compliance Standards
export const mockComplianceStandards = [
  { name: 'ISO 27001', verified: true, description: 'Information Security Management' },
  { name: 'GDPR', verified: true, description: 'Data Protection Regulation' },
  { name: 'ISO 14001', verified: true, description: 'Environmental Monitoring Standards' },
  { name: 'WHO Guidelines', verified: true, description: 'Water Safety Compliance' }
];

// Login Locations (Geo Map)
export const mockLoginLocations: MockLoginLocation[] = [
  { country: 'India', logins: 124, lat: 20.5937, lng: 78.9629 },
  { country: 'Singapore', logins: 3, lat: 1.3521, lng: 103.8198 },
  { country: 'Germany', logins: 1, lat: 51.1657, lng: 10.4515 },
  { country: 'United States', logins: 8, lat: 37.0902, lng: -95.7129 },
  { country: 'United Kingdom', logins: 5, lat: 55.3781, lng: -3.4360 }
];

// Backup & Disaster Recovery
export const mockBackupInfo: MockBackupInfo = {
  verification: 'Passed',
  lastRestoreTest: '3 days ago',
  backupSize: '14.2 GB',
  nextScheduledBackup: '02:00 AM'
};

// Helper Functions
export const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'success':
      return 'bg-green-100 text-green-800';
    case 'completed':
      return 'bg-blue-100 text-blue-800';
    case 'logged':
      return 'bg-purple-100 text-purple-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const getThreatLevelColor = (level: MockThreatLevel['level']) => {
  switch (level) {
    case 'LOW':
      return { bg: 'bg-green-100', text: 'text-green-800', icon: '🟢' };
    case 'MODERATE':
      return { bg: 'bg-amber-100', text: 'text-amber-800', icon: '🟡' };
    case 'HIGH':
      return { bg: 'bg-red-100', text: 'text-red-800', icon: '🔴' };
  }
};

export const getLoginStatusColor = (status: MockLoginEvent['status']) => {
  switch (status) {
    case 'success':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'blocked':
      return 'text-amber-600';
  }
};
