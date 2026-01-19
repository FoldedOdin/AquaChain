/**
 * Core Entity Types
 * Defines all entity interfaces used in the ordering system
 */

// Domain Event (imported from events)
export { DomainEvent } from './events';

// Order Entity
export interface Order {
  id: string;
  consumerId: string;
  deviceType: string;
  paymentMethod: 'COD' | 'ONLINE';
  status: 'PENDING' | 'APPROVED' | 'COMPLETED' | 'CANCELLED';
  address: string;
  phone: string;
  quoteAmount?: number;
  createdAt: Date;
  updatedAt: Date;
  approvedBy?: string;
  approvedAt?: Date;
  completedAt?: Date;
  cancelledAt?: Date;
  cancelReason?: string;
  version: number; // For optimistic locking
}

// Payment Entity
export interface Payment {
  id: string;
  orderId: string;
  razorpayOrderId?: string;
  razorpayPaymentId?: string;
  amount: number;
  currency: string;
  status: 'UNPAID' | 'PAID' | 'COD_PENDING' | 'FAILED';
  paymentMethod: 'COD' | 'ONLINE';
  createdAt: Date;
  paidAt?: Date;
  failedAt?: Date;
  failureReason?: string;
  version: number; // For optimistic locking
}

// Delivery Entity
export interface Delivery {
  id: string;
  orderId: string;
  shipmentId: string;
  trackingNumber: string;
  carrier: string;
  status: 'PREPARING' | 'SHIPPED' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'CANCELLED';
  address: Address;
  estimatedDelivery?: Date;
  shippedAt?: Date;
  deliveredAt?: Date;
  cancelledAt?: Date;
  cancelReason?: string;
  version: number; // For optimistic locking
}

// Installation Entity
export interface Installation {
  id: string;
  orderId: string;
  consumerId: string;
  status: 'NOT_REQUESTED' | 'REQUESTED' | 'SCHEDULED' | 'COMPLETED' | 'CANCELLED';
  technicianId?: string;
  deviceId?: string;
  requestedAt?: Date;
  scheduledAt?: Date;
  scheduledDate?: Date;
  completedAt?: Date;
  cancelledAt?: Date;
  cancelReason?: string;
  calibrationData?: any;
  photos?: string[];
  version: number; // For optimistic locking
}

// Address Type
export interface Address {
  street: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

// Razorpay Order Response
export interface RazorpayOrder {
  id: string;
  entity: string;
  amount: number;
  amount_paid: number;
  amount_due: number;
  currency: string;
  receipt: string;
  offer_id?: string;
  status: string;
  attempts: number;
  notes: Record<string, string>;
  created_at: number;
}

// Razorpay Payment Response
export interface RazorpayPayment {
  id: string;
  entity: string;
  amount: number;
  currency: string;
  status: string;
  order_id: string;
  invoice_id?: string;
  international: boolean;
  method: string;
  amount_refunded: number;
  refund_status?: string;
  captured: boolean;
  description?: string;
  card_id?: string;
  bank?: string;
  wallet?: string;
  vpa?: string;
  email: string;
  contact: string;
  notes: Record<string, string>;
  fee?: number;
  tax?: number;
  error_code?: string;
  error_description?: string;
  error_source?: string;
  error_step?: string;
  error_reason?: string;
  acquirer_data?: Record<string, any>;
  created_at: number;
}

// Webhook Payload
export interface WebhookPayload {
  entity: string;
  account_id: string;
  event: string;
  contains: string[];
  payload: {
    payment: {
      entity: RazorpayPayment;
    };
    order?: {
      entity: RazorpayOrder;
    };
  };
  created_at: number;
}

// Technician Entity
export interface Technician {
  id: string;
  name: string;
  email: string;
  phone: string;
  skills: string[];
  availability: 'AVAILABLE' | 'BUSY' | 'OFFLINE';
  location?: {
    latitude: number;
    longitude: number;
  };
  rating?: number;
  completedInstallations: number;
}

// Consumer Entity
export interface Consumer {
  id: string;
  name: string;
  email: string;
  phone: string;
  address?: Address;
  createdAt: Date;
  updatedAt: Date;
}

// Device Entity
export interface Device {
  id: string;
  serialNumber: string;
  model: string;
  status: 'AVAILABLE' | 'RESERVED' | 'INSTALLED' | 'MAINTENANCE';
  consumerId?: string;
  installationId?: string;
  createdAt: Date;
  installedAt?: Date;
  lastMaintenanceAt?: Date;
}

// Inventory Item
export interface InventoryItem {
  sku: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  totalCount: number;
  availableCount: number;
  reservedCount: number;
  updatedAt: Date;
}

// Audit Log Entry
export interface AuditLogEntry {
  id: string;
  entityType: string;
  entityId: string;
  action: string;
  performedBy: string;
  timestamp: Date;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  metadata?: Record<string, any>;
}

// Error Response
export interface ErrorResponse {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  correlationId: string;
  retryable: boolean;
}

// API Response Wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ErrorResponse;
  metadata?: {
    timestamp: Date;
    version: string;
    correlationId: string;
  };
}