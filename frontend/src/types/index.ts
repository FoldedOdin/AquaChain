export interface WaterQualityReading {
  deviceId: string;
  timestamp: string;
  location: {
    latitude: number;
    longitude: number;
  };
  readings: {
    pH: number;
    turbidity: number;
    tds: number;
    temperature: number;
    humidity: number;
  };
  wqi: number;
  anomalyType: 'normal' | 'sensor_fault' | 'contamination';
  diagnostics: {
    batteryLevel: number;
    signalStrength: number;
    sensorStatus: string;
  };
}

export interface ServiceRequest {
  requestId: string;
  consumerId: string;
  technicianId?: string;
  deviceId: string;
  status: 'pending' | 'assigned' | 'accepted' | 'en_route' | 'in_progress' | 'completed' | 'cancelled';
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  estimatedArrival?: string;
  notes: ServiceNote[];
  createdAt: string;
  completedAt?: string;
  customerRating?: number;
}

export interface ServiceNote {
  timestamp: string;
  author: string;
  type: 'status_update' | 'technician_note' | 'customer_feedback';
  content: string;
  attachments?: string[];
}

export interface UserProfile {
  userId: string;
  email: string;
  role: 'consumer' | 'technician' | 'admin';
  profile: {
    firstName: string;
    lastName: string;
    phone: string;
    address: {
      street: string;
      city: string;
      state: string;
      zipCode: string;
      coordinates: {
        latitude: number;
        longitude: number;
      };
    };
  };
  deviceIds: string[];
  preferences: {
    notifications: {
      push: boolean;
      sms: boolean;
      email: boolean;
    };
    theme: 'light' | 'dark' | 'auto';
    language: string;
  };
  workSchedule?: {
    monday: { start: string; end: string; };
    tuesday: { start: string; end: string; };
    wednesday: { start: string; end: string; };
    thursday: { start: string; end: string; };
    friday: { start: string; end: string; };
    saturday: { start: string; end: string; };
    sunday: { start: string; end: string; };
    overrideStatus: 'available' | 'unavailable' | 'available_overtime';
  };
  performanceScore?: number;
}

export interface Alert {
  id: string;
  deviceId: string;
  timestamp: string;
  severity: 'safe' | 'warning' | 'critical';
  message: string;
  wqi: number;
  readings: {
    pH: number;
    turbidity: number;
    tds: number;
    temperature: number;
    humidity: number;
  };
}

export interface TechnicianTask {
  taskId: string;
  serviceRequestId: string;
  deviceId: string;
  consumerId: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'assigned' | 'accepted' | 'en_route' | 'in_progress' | 'completed';
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  estimatedArrival?: string;
  actualArrival?: string;
  description: string;
  deviceInfo: {
    model: string;
    serialNumber: string;
    lastReading?: WaterQualityReading;
  };
  customerInfo: {
    name: string;
    phone: string;
    email: string;
  };
  assignedAt: string;
  dueDate?: string;
  notes: TaskNote[];
}

export interface TaskNote {
  id: string;
  timestamp: string;
  author: string;
  type: 'status_update' | 'technician_note' | 'customer_feedback' | 'diagnostic';
  content: string;
  attachments?: TaskAttachment[];
}

export interface TaskAttachment {
  id: string;
  filename: string;
  url: string;
  type: 'photo' | 'document' | 'diagnostic_report';
  uploadedAt: string;
}

export interface MaintenanceReport {
  reportId: string;
  taskId: string;
  deviceId: string;
  technicianId: string;
  completedAt: string;
  workPerformed: string;
  partsUsed: MaintenancePart[];
  diagnosticData: DiagnosticData;
  beforePhotos: string[];
  afterPhotos: string[];
  customerSignature?: string;
  nextMaintenanceDate?: string;
  recommendations: string;
}

export interface MaintenancePart {
  partNumber: string;
  description: string;
  quantity: number;
  cost?: number;
}

export interface DiagnosticData {
  deviceStatus: 'operational' | 'needs_repair' | 'replaced';
  sensorReadings: {
    pH: { value: number; status: 'normal' | 'warning' | 'error'; };
    turbidity: { value: number; status: 'normal' | 'warning' | 'error'; };
    tds: { value: number; status: 'normal' | 'warning' | 'error'; };
    temperature: { value: number; status: 'normal' | 'warning' | 'error'; };
    humidity: { value: number; status: 'normal' | 'warning' | 'error'; };
  };
  batteryLevel: number;
  signalStrength: number;
  calibrationStatus: 'current' | 'needs_calibration' | 'failed';
  lastCalibrationDate?: string;
}

export interface DeviceStatus {
  id: string;
  name: string;
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  status: 'online' | 'offline' | 'maintenance' | 'error';
  lastSeen: string;
  batteryLevel: number;
  signalStrength: number;
  firmwareVersion: string;
  lastReading?: WaterQualityReading;
  diagnostics: DiagnosticData;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'consumer' | 'technician' | 'admin';
  profile: UserProfile;
  createdAt: string;
  lastLogin?: string;
  isActive: boolean;
}