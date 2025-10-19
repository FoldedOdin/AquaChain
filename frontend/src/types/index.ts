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
  role: 'consumer' | 'technician' | 'administrator';
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