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
  SystemConfiguration,
  SystemHealthResponse
} from '../types/admin';
import { fetchWithAuth } from '../utils/apiInterceptor';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';

/**
 * Get logout function from AuthContext
 * This is used by the API interceptor to handle 401 errors
 */
const getLogoutFunction = async () => {
  // Import dynamically to avoid circular dependencies
  const { useAuth } = await import('../contexts/AuthContext');
  // Note: This won't work outside React components
  // The interceptor will handle logout directly via localStorage and redirect
  return undefined;
};

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
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/devices`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch devices');
    }

    const data = await response.json();
    
    // Transform dev server device data to match DeviceFleetStatus interface
    return data.devices.map((device: any) => ({
      deviceId: device.device_id,
      status: device.status || 'offline',
      lastSeen: device.created_at,
      uptime: 0,
      location: {
        latitude: 0,
        longitude: 0,
        address: device.location || 'N/A'
      },
      currentWQI: 0,
      batteryLevel: 100,
      signalStrength: -65,
      consumerId: device.user_id,
      consumerName: device.consumerName || 'Unassigned',
      maintenanceHistory: []
    }));
  } catch (error) {
    console.error('Error fetching devices:', error);
    // Return empty array on error instead of dummy data
    return [];
  }
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
  try {
    // Try both token names for compatibility
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/users`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch users');
    }

    const data = await response.json();
    
    console.log('📊 Raw user data from backend:', data.users?.slice(0, 2)); // Log first 2 users for debugging
    console.log('📊 Full first user object:', JSON.stringify(data.users?.[0], null, 2)); // Log complete structure
    
    // Transform dev server user data to match UserManagementData interface
    return data.users.map((user: any) => {
      const mappedUser = {
        userId: user.userId,
        email: user.email,
        role: user.role,
        status: user.status || 'pending',  // Use status from backend
        createdAt: user.createdAt,
        lastLogin: user.lastLogin || null,
        deviceCount: 0, // Will be calculated from devices
        profile: {
          firstName: user.firstName || user.name?.split(' ')[0] || '',
          lastName: user.lastName || user.name?.split(' ').slice(1).join(' ') || '',
          phone: user.phone || ''
        }
      };
      console.log(`👤 Mapped user ${user.email}: lastLogin = ${mappedUser.lastLogin}`);
      return mappedUser;
    });
  } catch (error) {
    console.error('Error fetching users:', error);
    // Return empty array on error instead of dummy data
    return [];
  }
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
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Transform the data to match backend expectations
    const updatePayload: any = {};
    
    if (updates.profile) {
      updatePayload.firstName = updates.profile.firstName;
      updatePayload.lastName = updates.profile.lastName;
      updatePayload.phone = updates.profile.phone;
    }
    
    if (updates.email) {
      updatePayload.email = updates.email;
    }
    
    if (updates.status !== undefined) {
      // Map frontend status to Cognito enabled flag
      updatePayload.enabled = updates.status === 'active';
    }

    console.log('Updating user:', userId, 'with payload:', updatePayload);

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/users/${userId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatePayload)
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to update user');
    }

    const result = await response.json();
    console.log('User update response:', result);
    
    // Fetch the updated user data
    const users = await getAllUsers();
    const updatedUser = users.find(u => u.userId === userId);
    
    if (!updatedUser) {
      throw new Error('User not found after update');
    }
    
    return updatedUser;
  } catch (error) {
    console.error('Error updating user:', error);
    throw error;
  }
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
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/configuration`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch system configuration');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching system configuration:', error);
    // Return default configuration as fallback
    return {
      alertThresholds: {
        global: {
          pH: { 
            warning: { min: 5.5, max: 8.5 },
            critical: { min: 6.0, max: 8.0 }
          },
          turbidity: { 
            warning: { max: 4.0 },
            critical: { max: 5.0 }
          },
          tds: { 
            warning: { max: 400 },
            critical: { max: 500 }
          },
          temperature: { 
            warning: { min: 0.5, max: 39.5 },
            critical: { min: 0, max: 40 }
          },
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
      },
      mlSettings: {
        anomalyDetectionEnabled: true,
        modelVersion: 'latest',
        confidenceThreshold: 0.85,
        retrainingFrequencyDays: 30,
        driftDetectionEnabled: true
      }
    };
  }
};

export const updateSystemConfiguration = async (config: Partial<SystemConfiguration>): Promise<SystemConfiguration> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/configuration`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      }
    );

    if (!response.ok) {
      // If the endpoint doesn't exist yet, simulate the update locally
      if (response.status === 404) {
        console.warn('System configuration endpoint not implemented yet - simulating update');
        await new Promise(resolve => setTimeout(resolve, 500));
        const currentConfig = await getSystemConfiguration();
        return {
          ...currentConfig,
          ...config
        };
      }
      
      // Parse validation errors from backend
      const errorData = await response.json();
      if (errorData.validationErrors && Array.isArray(errorData.validationErrors)) {
        const errorMessage = errorData.validationErrors.join('\n');
        throw new Error(errorMessage);
      }
      
      throw new Error(errorData.error || 'Failed to update system configuration');
    }

    const data = await response.json();
    return data.configuration;
  } catch (error) {
    console.error('Error updating system configuration:', error);
    throw error; // Re-throw to let the caller handle it
  }
};

export const updateProfile = async (updates: { profile: { firstName: string; lastName: string; phone: string } }): Promise<void> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Transform nested structure to flat structure expected by Lambda
    // Frontend component sends: {profile: {firstName, lastName, phone}}
    // Lambda expects: {firstName, lastName, phone}
    const flatUpdates = {
      firstName: updates.profile.firstName,
      lastName: updates.profile.lastName,
      phone: updates.profile.phone
    };

    console.log('Sending profile update request:', flatUpdates);

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/profile/update`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(flatUpdates)
      }
    );

    console.log('Profile update response status:', response.status);

    // Try to parse response as JSON
    let data;
    try {
      const text = await response.text();
      console.log('Profile update response text:', text);
      data = text ? JSON.parse(text) : {};
    } catch (parseError) {
      console.error('Failed to parse response:', parseError);
      throw new Error('Invalid response from server');
    }

    if (!response.ok) {
      const errorMessage = data.error || data.message || `Server error: ${response.status}`;
      console.error('Profile update failed:', errorMessage, data);
      throw new Error(errorMessage);
    }

    // Update localStorage with new profile data
    const storedUser = localStorage.getItem('aquachain_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      userData.profile = {
        ...userData.profile,
        ...updates.profile
      };
      localStorage.setItem('aquachain_user', JSON.stringify(userData));
    }
    
    console.log('Profile updated successfully:', data);
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

export const revealSensitiveData = async (userId: string): Promise<{
  userId: string;
  email: string;
  phone: string;
  lastName: string;
  revealedAt: string;
  expiresIn: number;
}> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Simplified approach: Just fetch user data directly
    // Security: JWT authentication (admin role required) + audit logging in Lambda
    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/users/${userId}?reveal=true`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to reveal sensitive data');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error revealing sensitive data:', error);
    throw error;
  }
};

export const getSystemHealth = async (forceRefresh: boolean = false): Promise<SystemHealthResponse> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const queryParam = forceRefresh ? '?refresh=true' : '';
    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/health${queryParam}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch system health');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching system health:', error);
    throw error;
  }
};

export const getConfigurationHistory = async (limit: number = 50): Promise<{
  history: Array<{
    version: string;
    updatedBy: string;
    updatedAt: string;
    previousVersion: string;
    changes: Record<string, { old: any; new: any }>;
    ipAddress: string;
  }>;
  count: number;
}> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/configuration/history?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch configuration history');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching configuration history:', error);
    throw error;
  }
};

export const validateConfiguration = async (config: Partial<SystemConfiguration>): Promise<{ 
  valid: boolean; 
  errors: string[] 
}> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/configuration/validate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      }
    );

    if (!response.ok) {
      // Try to get detailed error message
      try {
        const errorData = await response.json();
        console.error('Validation failed:', errorData);
        
        // If it's a 403 with details, show specific error
        if (response.status === 403 && errorData.details) {
          const { requiredGroup, yourGroups, email } = errorData.details;
          return { 
            valid: false, 
            errors: [
              `Access Denied: Admin privileges required`,
              `Your account (${email}) has groups: ${yourGroups.join(', ') || 'none'}`,
              `Required group: ${requiredGroup}`,
              `Please contact your administrator or log out and log back in if you were recently granted admin access.`
            ] 
          };
        }
        
        return { valid: false, errors: [errorData.message || 'Validation service unavailable'] };
      } catch (parseError) {
        return { valid: false, errors: ['Validation service unavailable'] };
      }
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error validating configuration:', error);
    return { valid: false, errors: ['Validation service unavailable'] };
  }
};

export const rollbackConfiguration = async (version: string): Promise<{
  message: string;
  version: string;
  rolledBackFrom: string;
  rolledBackTo: string;
  changes: Record<string, { old: any; new: any }>;
}> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/system/configuration/rollback`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ version })
      }
    );

    if (!response.ok) {
      throw new Error('Failed to rollback configuration');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error rolling back configuration:', error);
    throw error;
  }
};

export default {
  getSystemHealthMetrics,
  getDeviceFleetStatus,
  getPerformanceMetrics,
  getAlertAnalytics,
  getAllUsers,
  createUser,
  updateUser,
  deleteUser,
  getAllDevices,
  registerDevice,
  updateDevice,
  getAllTechnicians,
  updateTechnician,
  generateComplianceReport,
  getAuditTrail,
  verifyHashChain,
  getSystemConfiguration,
  updateSystemConfiguration,
  getConfigurationHistory,
  validateConfiguration,
  rollbackConfiguration,
  updateProfile,
  revealSensitiveData,
  getSystemHealth
};
