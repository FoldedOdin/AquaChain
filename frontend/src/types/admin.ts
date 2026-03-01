// Admin-specific types for system monitoring and management

export interface SystemHealthMetrics {
  timestamp: string;
  criticalPathUptime: number; // Percentage
  apiUptime: number; // Percentage
  notificationUptime: number; // Percentage
  errorRate: number; // Percentage
  activeDevices: number;
  totalDevices: number;
  activeAlerts: number;
  pendingServiceRequests: number;
}

export interface DeviceFleetStatus {
  deviceId: string;
  status: 'online' | 'offline' | 'warning' | 'error';
  lastSeen: string;
  uptime: number; // Percentage over last 30 days
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  currentWQI: number;
  batteryLevel: number;
  signalStrength: number;
  consumerId: string;
  consumerName: string;
  maintenanceHistory: MaintenanceRecord[];
}

export interface MaintenanceRecord {
  date: string;
  type: 'routine' | 'repair' | 'replacement' | 'calibration';
  technicianId: string;
  technicianName: string;
  notes: string;
}

export interface PerformanceMetrics {
  timestamp: string;
  avgAlertLatency: number; // Seconds
  p95AlertLatency: number; // Seconds
  p99AlertLatency: number; // Seconds
  avgApiResponseTime: number; // Milliseconds
  p95ApiResponseTime: number; // Milliseconds
  throughput: number; // Requests per second
  lambdaInvocations: number;
  lambdaErrors: number;
  dynamodbReadCapacity: number;
  dynamodbWriteCapacity: number;
}

export interface AlertAnalytics {
  period: string; // e.g., "2025-10-19"
  totalAlerts: number;
  criticalAlerts: number;
  warningAlerts: number;
  safeAlerts: number;
  avgResolutionTime: number; // Minutes
  alertsByDevice: {
    deviceId: string;
    count: number;
    severity: 'critical' | 'warning' | 'safe';
  }[];
  alertsByType: {
    type: 'contamination' | 'sensor_fault' | 'normal';
    count: number;
  }[];
}

export interface UserManagementData {
  userId: string;
  email: string;
  role: 'consumer' | 'technician' | 'administrator';
  status: 'active' | 'inactive' | 'suspended';
  createdAt: string;
  lastLogin: string;
  deviceCount: number;
  profile: {
    firstName: string;
    lastName: string;
    phone: string;
  };
}

export interface DeviceRegistration {
  deviceId: string;
  serialNumber: string;
  model: string;
  firmwareVersion: string;
  status: 'active' | 'inactive' | 'maintenance';
  registeredAt: string;
  assignedTo?: string; // userId
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  configuration: {
    readingInterval: number; // Seconds
    alertThresholds: {
      pH: { min: number; max: number; };
      turbidity: { max: number; };
      tds: { max: number; };
      temperature: { min: number; max: number; };
    };
  };
}

export interface TechnicianManagementData {
  technicianId: string;
  email: string;
  status: 'active' | 'inactive' | 'on_leave';
  profile: {
    firstName: string;
    lastName: string;
    phone: string;
    certifications: string[];
  };
  workSchedule: {
    monday: { start: string; end: string; };
    tuesday: { start: string; end: string; };
    wednesday: { start: string; end: string; };
    thursday: { start: string; end: string; };
    friday: { start: string; end: string; };
    saturday: { start: string; end: string; };
    sunday: { start: string; end: string; };
    overrideStatus: 'available' | 'unavailable' | 'available_overtime';
  };
  performanceScore: number;
  stats: {
    totalJobs: number;
    completedJobs: number;
    avgCompletionTime: number; // Minutes
    avgCustomerRating: number;
    activeJobs: number;
  };
  serviceZone: {
    latitude: number;
    longitude: number;
    radiusMiles: number;
  };
}

export interface ComplianceReport {
  reportId: string;
  generatedAt: string;
  period: {
    startDate: string;
    endDate: string;
  };
  summary: {
    totalReadings: number;
    devicesMonitored: number;
    alertsGenerated: number;
    complianceRate: number; // Percentage
  };
  ledgerVerification: {
    totalEntries: number;
    verifiedEntries: number;
    hashChainIntact: boolean;
    lastVerificationDate: string;
  };
  dataIntegrity: {
    missingReadings: number;
    duplicateReadings: number;
    invalidReadings: number;
  };
  uptimeMetrics: {
    criticalPathUptime: number;
    apiUptime: number;
    notificationUptime: number;
  };
}

export interface AuditTrailEntry {
  logId: string;
  sequenceNumber: number;
  timestamp: string;
  deviceId: string;
  dataHash: string;
  previousHash: string;
  chainHash: string;
  wqi: number;
  anomalyType: string;
  kmsSignature: string;
  verified: boolean;
}

export interface SystemConfiguration {
  alertThresholds: {
    global: {
      pH: {
        // Backward compatible: if no severity levels, use min/max as critical
        min?: number;
        max?: number;
        // New severity levels
        critical?: { min: number; max: number; };
        warning?: { min: number; max: number; };
      };
      turbidity: {
        max?: number;
        critical?: { max: number; };
        warning?: { max: number; };
      };
      tds: {
        max?: number;
        critical?: { max: number; };
        warning?: { max: number; };
      };
      temperature: {
        min?: number;
        max?: number;
        critical?: { min: number; max: number; };
        warning?: { min: number; max: number; };
      };
      wqi: { critical: number; warning: number; };
    };
  };
  notificationSettings: {
    criticalAlertChannels: ('sms' | 'email' | 'push')[];
    warningAlertChannels: ('email' | 'push')[];
    rateLimits: {
      smsPerHour: number;
      emailPerHour: number;
    };
  };
  systemLimits: {
    maxDevicesPerUser: number;
    maxConcurrentDevices: number;
    dataRetentionDays: number;
    auditRetentionYears: number;
  };
  maintenanceMode: {
    enabled: boolean;
    message?: string;
    allowedRoles: string[];
  };
  // Phase 3a: ML Configuration (optional, for future)
  mlSettings?: {
    anomalyDetectionEnabled: boolean;
    modelVersion: string;
    confidenceThreshold: number;
    retrainingFrequencyDays: number;
    driftDetectionEnabled: boolean;
  };
}

// Phase 3c: System Health Monitoring Types

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  lastCheck: string;
  metrics?: {
    [key: string]: number;
  };
  message?: string;
}

export interface SystemHealthResponse {
  services: ServiceHealth[];
  overallStatus: 'healthy' | 'degraded' | 'down';
  checkedAt: string;
  cacheHit: boolean;
}
