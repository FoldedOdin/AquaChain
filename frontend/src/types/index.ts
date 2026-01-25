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
  role: 'consumer' | 'technician' | 'admin' | 'inventory_manager' | 'warehouse_manager' | 'supplier_coordinator' | 'procurement_controller';
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
  role: 'consumer' | 'technician' | 'admin' | 'inventory_manager' | 'warehouse_manager' | 'supplier_coordinator' | 'procurement_controller';
  profile: UserProfile;
  createdAt: string;
  lastLogin?: string;
  isActive: boolean;
}

// Operations Dashboard Types
export interface InventoryItem {
  itemId: string;
  itemName: string;
  currentStock: number;
  reorderPoint: number;
  reorderQuantity: number;
  unitCost: number;
  supplierId: string;
  warehouseLocation: string;
  lastUpdated: string;
  updatedBy: string;
  category: string;
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'discontinued';
}

export interface StockAlert {
  alertId: string;
  itemId: string;
  itemName: string;
  currentStock: number;
  reorderPoint: number;
  severity: 'warning' | 'critical';
  recommendedAction: string;
  createdAt: string;
}

export interface DemandForecast {
  itemId: string;
  itemName: string;
  forecastPeriod: string;
  predictedDemand: number;
  confidence: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  seasonalFactors: number[];
}

export interface WarehouseLocation {
  locationId: string;
  zone: string;
  aisle: string;
  shelf: string;
  bin: string;
  capacity: number;
  currentOccupancy: number;
  itemIds: string[];
  status: 'available' | 'full' | 'reserved' | 'maintenance';
}

export interface StockMovement {
  movementId: string;
  itemId: string;
  itemName: string;
  movementType: 'receipt' | 'dispatch' | 'transfer' | 'adjustment';
  quantity: number;
  fromLocation?: string;
  toLocation?: string;
  reason: string;
  performedBy: string;
  timestamp: string;
  referenceNumber?: string;
}

export interface ReceivingWorkflow {
  workflowId: string;
  purchaseOrderId: string;
  supplierId: string;
  supplierName: string;
  expectedItems: ReceivingItem[];
  receivedItems: ReceivingItem[];
  status: 'pending' | 'in_progress' | 'completed' | 'discrepancy';
  startedAt?: string;
  completedAt?: string;
  performedBy?: string;
  notes: string;
}

export interface ReceivingItem {
  itemId: string;
  itemName: string;
  expectedQuantity: number;
  receivedQuantity?: number;
  condition: 'good' | 'damaged' | 'expired';
  lotNumber?: string;
  expiryDate?: string;
}

export interface DispatchWorkflow {
  workflowId: string;
  orderId: string;
  customerId: string;
  customerName: string;
  items: DispatchItem[];
  status: 'pending' | 'picking' | 'packed' | 'shipped' | 'delivered';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignedTo?: string;
  startedAt?: string;
  completedAt?: string;
  trackingNumber?: string;
}

export interface DispatchItem {
  itemId: string;
  itemName: string;
  requestedQuantity: number;
  pickedQuantity?: number;
  fromLocation: string;
  status: 'pending' | 'picked' | 'packed';
}

export interface SupplierProfile {
  supplierId: string;
  supplierName: string;
  contactInfo: {
    primaryContact: string;
    email: string;
    phone: string;
    address: {
      street: string;
      city: string;
      state: string;
      zipCode: string;
      country: string;
    };
  };
  businessInfo: {
    taxId: string;
    businessType: string;
    yearsInBusiness: number;
    certifications: string[];
  };
  performanceMetrics: {
    onTimeDeliveryRate: number;
    qualityScore: number;
    responseTime: number;
    defectRate: number;
  };
  riskIndicators: {
    financialRisk: 'low' | 'medium' | 'high';
    operationalRisk: 'low' | 'medium' | 'high';
    complianceRisk: 'low' | 'medium' | 'high';
    overallRisk: 'low' | 'medium' | 'high';
  };
  status: 'active' | 'inactive' | 'suspended' | 'under_review';
  createdAt: string;
  lastUpdated: string;
}

export interface SupplierContract {
  contractId: string;
  supplierId: string;
  contractType: 'purchase_agreement' | 'service_contract' | 'framework_agreement';
  startDate: string;
  endDate: string;
  value: number;
  currency: string;
  terms: {
    paymentTerms: string;
    deliveryTerms: string;
    qualityRequirements: string;
    penaltyClauses: string[];
  };
  status: 'draft' | 'active' | 'expired' | 'terminated';
  documents: ContractDocument[];
  renewalDate?: string;
  createdBy: string;
  createdAt: string;
}

export interface ContractDocument {
  documentId: string;
  filename: string;
  documentType: 'contract' | 'amendment' | 'certificate' | 'insurance';
  uploadedAt: string;
  uploadedBy: string;
  url: string;
  size: number;
}

export interface WarehouseMetrics {
  totalCapacity: number;
  currentOccupancy: number;
  utilizationRate: number;
  throughputToday: number;
  throughputWeek: number;
  throughputMonth: number;
  averagePickTime: number;
  averagePackTime: number;
  errorRate: number;
  onTimeShipmentRate: number;
}

export interface AuditEntry {
  auditId: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId: string;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  beforeState?: any;
  afterState?: any;
  success: boolean;
  errorMessage?: string;
}