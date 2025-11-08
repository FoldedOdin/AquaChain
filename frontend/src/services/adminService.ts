import {
  SystemHealthMetrics,
  DeviceFleetStatus,
  PerformanceMetrics,
  AlertAnalytics,
  UserManagementData,
  DeviceRegistration,
  TechnicianManagementData,
  ComplianceReport,
  AuditTrailEntry,
  SystemConfiguration
} from '../types/admin';

// Mock data for development - will be replaced with actual API calls

export const getSystemHealthMetrics = async (): Promise<SystemHealthMetrics> => {
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 300));
  
  return {
    timestamp: new Date().toISOString(),
    criticalPathUptime: 99.7,
    apiUptime: 99.2,
    notificationUptime: 98.5,
    errorRate: 0.3,
    activeDevices: 847,
    totalDevices: 1000,
    activeAlerts: 12,
    pendingServiceRequests: 5
  };
};

export const getDeviceFleetStatus = async (): Promise<DeviceFleetStatus[]> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  return [
    {
      deviceId: 'DEV-3421',
      status: 'online',
      lastSeen: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
      uptime: 99.8,
      location: {
        latitude: 37.7749,
        longitude: -122.4194,
        address: '123 Main St, San Francisco, CA'
      },
      currentWQI: 85,
      batteryLevel: 85,
      signalStrength: -65,
      consumerId: 'user-001',
      consumerName: 'John Doe',
      maintenanceHistory: [
        {
          date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          type: 'routine',
          technicianId: 'tech-001',
          technicianName: 'Mike Johnson',
          notes: 'Routine calibration and inspection'
        }
      ]
    },
    {
      deviceId: 'DEV-3422',
      status: 'warning',
      lastSeen: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      uptime: 95.2,
      location: {
        latitude: 37.7849,
        longitude: -122.4094,
        address: '456 Oak Ave, San Francisco, CA'
      },
      currentWQI: 55,
      batteryLevel: 45,
      signalStrength: -75,
      consumerId: 'user-002',
      consumerName: 'Jane Smith',
      maintenanceHistory: []
    },
    {
      deviceId: 'DEV-3423',
      status: 'offline',
      lastSeen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      uptime: 88.5,
      location: {
        latitude: 37.7649,
        longitude: -122.4294,
        address: '789 Pine St, San Francisco, CA'
      },
      currentWQI: 0,
      batteryLevel: 15,
      signalStrength: -95,
      consumerId: 'user-003',
      consumerName: 'Bob Wilson',
      maintenanceHistory: [
        {
          date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          type: 'repair',
          technicianId: 'tech-002',
          technicianName: 'Sarah Davis',
          notes: 'Replaced pH sensor'
        }
      ]
    }
  ];
};

export const getPerformanceMetrics = async (timeRange: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<PerformanceMetrics[]> => {
  await new Promise(resolve => setTimeout(resolve, 350));
  
  const now = Date.now();
  const intervals = timeRange === '1h' ? 12 : timeRange === '24h' ? 24 : timeRange === '7d' ? 7 : 30;
  const intervalMs = timeRange === '1h' ? 5 * 60 * 1000 : timeRange === '24h' ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000;
  
  return Array.from({ length: intervals }, (_, i) => ({
    timestamp: new Date(now - (intervals - i - 1) * intervalMs).toISOString(),
    avgAlertLatency: 15 + Math.random() * 10,
    p95AlertLatency: 25 + Math.random() * 8,
    p99AlertLatency: 28 + Math.random() * 5,
    avgApiResponseTime: 150 + Math.random() * 100,
    p95ApiResponseTime: 350 + Math.random() * 150,
    throughput: 50 + Math.random() * 30,
    lambdaInvocations: 5000 + Math.random() * 2000,
    lambdaErrors: Math.floor(Math.random() * 50),
    dynamodbReadCapacity: 1000 + Math.random() * 500,
    dynamodbWriteCapacity: 800 + Math.random() * 400
  }));
};

export const getAlertAnalytics = async (days: number = 7): Promise<AlertAnalytics> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  return {
    period: `Last ${days} days`,
    totalAlerts: 156,
    criticalAlerts: 12,
    warningAlerts: 45,
    safeAlerts: 99,
    avgResolutionTime: 45,
    alertsByDevice: [
      { deviceId: 'DEV-3421', count: 8, severity: 'warning' },
      { deviceId: 'DEV-3422', count: 15, severity: 'critical' },
      { deviceId: 'DEV-3423', count: 12, severity: 'warning' },
      { deviceId: 'DEV-3424', count: 5, severity: 'safe' },
      { deviceId: 'DEV-3425', count: 18, severity: 'warning' }
    ],
    alertsByType: [
      { type: 'contamination', count: 25 },
      { type: 'sensor_fault', count: 32 },
      { type: 'normal', count: 99 }
    ]
  };
};

export const getAllUsers = async (): Promise<UserManagementData[]> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  return [
    {
      userId: 'user-001',
      email: 'john.doe@example.com',
      role: 'consumer',
      status: 'active',
      createdAt: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
      lastLogin: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      deviceCount: 2,
      profile: {
        firstName: 'John',
        lastName: 'Doe',
        phone: '+1-555-0101'
      }
    },
    {
      userId: 'user-002',
      email: 'jane.smith@example.com',
      role: 'consumer',
      status: 'active',
      createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
      lastLogin: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      deviceCount: 1,
      profile: {
        firstName: 'Jane',
        lastName: 'Smith',
        phone: '+1-555-0102'
      }
    },
    {
      userId: 'tech-001',
      email: 'mike.johnson@aquachain.com',
      role: 'technician',
      status: 'active',
      createdAt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
      lastLogin: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      deviceCount: 0,
      profile: {
        firstName: 'Mike',
        lastName: 'Johnson',
        phone: '+1-555-0201'
      }
    }
  ];
};

export const createUser = async (userData: Partial<UserManagementData>): Promise<UserManagementData> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return {
    userId: `user-${Date.now()}`,
    email: userData.email || '',
    role: userData.role || 'consumer',
    status: 'active',
    createdAt: new Date().toISOString(),
    lastLogin: new Date().toISOString(),
    deviceCount: 0,
    profile: userData.profile || {
      firstName: '',
      lastName: '',
      phone: ''
    }
  };
};

export const updateUser = async (userId: string, updates: Partial<UserManagementData>): Promise<UserManagementData> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  const users = await getAllUsers();
  const user = users.find(u => u.userId === userId);
  
  if (!user) {
    throw new Error('User not found');
  }
  
  return {
    ...user,
    ...updates
  };
};

export const deleteUser = async (userId: string): Promise<void> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  console.log(`User ${userId} deleted`);
};

export const getAllDevices = async (): Promise<DeviceRegistration[]> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  return [
    {
      deviceId: 'DEV-3421',
      serialNumber: 'SN-2025-001',
      model: 'AquaChain Pro v2',
      firmwareVersion: '2.1.5',
      status: 'active',
      registeredAt: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
      assignedTo: 'user-001',
      location: {
        latitude: 37.7749,
        longitude: -122.4194,
        address: '123 Main St, San Francisco, CA'
      },
      configuration: {
        readingInterval: 30,
        alertThresholds: {
          pH: { min: 6.5, max: 8.5 },
          turbidity: { max: 5.0 },
          tds: { max: 500 },
          temperature: { min: 0, max: 40 }
        }
      }
    },
    {
      deviceId: 'DEV-3422',
      serialNumber: 'SN-2025-002',
      model: 'AquaChain Pro v2',
      firmwareVersion: '2.1.5',
      status: 'active',
      registeredAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
      assignedTo: 'user-002',
      location: {
        latitude: 37.7849,
        longitude: -122.4094,
        address: '456 Oak Ave, San Francisco, CA'
      },
      configuration: {
        readingInterval: 30,
        alertThresholds: {
          pH: { min: 6.5, max: 8.5 },
          turbidity: { max: 5.0 },
          tds: { max: 500 },
          temperature: { min: 0, max: 40 }
        }
      }
    }
  ];
};

export const registerDevice = async (deviceData: Partial<DeviceRegistration>): Promise<DeviceRegistration> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return {
    deviceId: `DEV-${Date.now()}`,
    serialNumber: deviceData.serialNumber || '',
    model: deviceData.model || 'AquaChain Pro v2',
    firmwareVersion: deviceData.firmwareVersion || '2.1.5',
    status: 'active',
    registeredAt: new Date().toISOString(),
    assignedTo: deviceData.assignedTo,
    location: deviceData.location || {
      latitude: 0,
      longitude: 0,
      address: ''
    },
    configuration: deviceData.configuration || {
      readingInterval: 30,
      alertThresholds: {
        pH: { min: 6.5, max: 8.5 },
        turbidity: { max: 5.0 },
        tds: { max: 500 },
        temperature: { min: 0, max: 40 }
      }
    }
  };
};

export const updateDevice = async (deviceId: string, updates: Partial<DeviceRegistration>): Promise<DeviceRegistration> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  const devices = await getAllDevices();
  const device = devices.find(d => d.deviceId === deviceId);
  
  if (!device) {
    throw new Error('Device not found');
  }
  
  return {
    ...device,
    ...updates
  };
};

export const getAllTechnicians = async (): Promise<TechnicianManagementData[]> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  return [
    {
      technicianId: 'tech-001',
      email: 'mike.johnson@aquachain.com',
      status: 'active',
      profile: {
        firstName: 'Mike',
        lastName: 'Johnson',
        phone: '+1-555-0201',
        certifications: ['Water Quality Specialist', 'IoT Device Technician']
      },
      workSchedule: {
        monday: { start: '09:00', end: '17:00' },
        tuesday: { start: '09:00', end: '17:00' },
        wednesday: { start: '09:00', end: '17:00' },
        thursday: { start: '09:00', end: '17:00' },
        friday: { start: '09:00', end: '17:00' },
        saturday: { start: '', end: '' },
        sunday: { start: '', end: '' },
        overrideStatus: 'available'
      },
      performanceScore: 92.5,
      stats: {
        totalJobs: 145,
        completedJobs: 142,
        avgCompletionTime: 65,
        avgCustomerRating: 4.7,
        activeJobs: 2
      },
      serviceZone: {
        latitude: 37.7749,
        longitude: -122.4194,
        radiusMiles: 25
      }
    },
    {
      technicianId: 'tech-002',
      email: 'sarah.davis@aquachain.com',
      status: 'active',
      profile: {
        firstName: 'Sarah',
        lastName: 'Davis',
        phone: '+1-555-0202',
        certifications: ['Water Quality Specialist', 'Senior Technician']
      },
      workSchedule: {
        monday: { start: '08:00', end: '16:00' },
        tuesday: { start: '08:00', end: '16:00' },
        wednesday: { start: '08:00', end: '16:00' },
        thursday: { start: '08:00', end: '16:00' },
        friday: { start: '08:00', end: '16:00' },
        saturday: { start: '10:00', end: '14:00' },
        sunday: { start: '', end: '' },
        overrideStatus: 'available'
      },
      performanceScore: 95.8,
      stats: {
        totalJobs: 203,
        completedJobs: 201,
        avgCompletionTime: 58,
        avgCustomerRating: 4.9,
        activeJobs: 1
      },
      serviceZone: {
        latitude: 37.7849,
        longitude: -122.4094,
        radiusMiles: 30
      }
    }
  ];
};

export const updateTechnician = async (technicianId: string, updates: Partial<TechnicianManagementData>): Promise<TechnicianManagementData> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  
  const technicians = await getAllTechnicians();
  const technician = technicians.find(t => t.technicianId === technicianId);
  
  if (!technician) {
    throw new Error('Technician not found');
  }
  
  return {
    ...technician,
    ...updates
  };
};

export const generateComplianceReport = async (startDate: string, endDate: string): Promise<ComplianceReport> => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    reportId: `RPT-${Date.now()}`,
    generatedAt: new Date().toISOString(),
    period: {
      startDate,
      endDate
    },
    summary: {
      totalReadings: 2592000,
      devicesMonitored: 1000,
      alertsGenerated: 1245,
      complianceRate: 99.95
    },
    ledgerVerification: {
      totalEntries: 2592000,
      verifiedEntries: 2592000,
      hashChainIntact: true,
      lastVerificationDate: new Date().toISOString()
    },
    dataIntegrity: {
      missingReadings: 125,
      duplicateReadings: 8,
      invalidReadings: 42
    },
    uptimeMetrics: {
      criticalPathUptime: 99.7,
      apiUptime: 99.2,
      notificationUptime: 98.5
    }
  };
};

export const getAuditTrail = async (startDate: string, endDate: string, deviceId?: string): Promise<AuditTrailEntry[]> => {
  await new Promise(resolve => setTimeout(resolve, 600));
  
  return Array.from({ length: 10 }, (_, i) => ({
    logId: `log-${Date.now()}-${i}`,
    sequenceNumber: 1000000 + i,
    timestamp: new Date(Date.now() - i * 60 * 1000).toISOString(),
    deviceId: deviceId || `DEV-342${i % 3 + 1}`,
    dataHash: `hash-${Math.random().toString(36).substring(7)}`,
    previousHash: i > 0 ? `hash-${Math.random().toString(36).substring(7)}` : '0',
    chainHash: `chain-${Math.random().toString(36).substring(7)}`,
    wqi: 70 + Math.random() * 30,
    anomalyType: ['normal', 'sensor_fault', 'contamination'][Math.floor(Math.random() * 3)],
    kmsSignature: `sig-${Math.random().toString(36).substring(7)}`,
    verified: true
  }));
};

export const verifyHashChain = async (startSequence: number, endSequence: number): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 800));
  return true;
};

export const getSystemConfiguration = async (): Promise<SystemConfiguration> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  return {
    alertThresholds: {
      global: {
        pH: { min: 6.5, max: 8.5 },
        turbidity: { max: 5.0 },
        tds: { max: 500 },
        temperature: { min: 0, max: 40 },
        wqi: { critical: 40, warning: 60 }
      }
    },
    notificationSettings: {
      criticalAlertChannels: ['sms', 'email', 'push'],
      warningAlertChannels: ['email', 'push'],
      rateLimits: {
        smsPerHour: 100,
        emailPerHour: 500
      }
    },
    systemLimits: {
      maxDevicesPerUser: 10,
      maxConcurrentDevices: 10000,
      dataRetentionDays: 90,
      auditRetentionYears: 7
    },
    maintenanceMode: {
      enabled: false,
      allowedRoles: ['administrator']
    }
  };
};

export const updateSystemConfiguration = async (config: Partial<SystemConfiguration>): Promise<SystemConfiguration> => {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const currentConfig = await getSystemConfiguration();
  return {
    ...currentConfig,
    ...config
  };
};
