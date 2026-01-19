/**
 * Domain Event Types and Schemas
 * Defines all event types used in the event-driven ordering system
 */

// Base Domain Event Interface
export interface DomainEvent {
  id: string;
  aggregateId: string;
  aggregateType: 'Order' | 'Payment' | 'Delivery' | 'Installation';
  eventType: string;
  eventData: any;
  version: number;
  timestamp: Date;
  correlationId?: string;
}

// Order Events
export interface OrderCreated {
  orderId: string;
  consumerId: string;
  deviceType: string;
  paymentMethod: 'COD' | 'ONLINE';
  address: string;
  phone: string;
  createdAt: Date;
}

export interface OrderApproved {
  orderId: string;
  approvedBy: string;
  approvedAt: Date;
  quoteAmount: number;
}

export interface OrderCompleted {
  orderId: string;
  completedAt: Date;
}

export interface OrderCancelled {
  orderId: string;
  cancelledBy: string;
  cancelledAt: Date;
  reason: string;
}

// Payment Events
export interface PaymentCompleted {
  orderId: string;
  paymentId: string;
  razorpayPaymentId: string;
  amount: number;
  method: 'COD' | 'ONLINE';
  completedAt: Date;
}

export interface PaymentFailed {
  orderId: string;
  paymentId: string;
  razorpayPaymentId?: string;
  reason: string;
  failedAt: Date;
}

export interface CODConversionRequested {
  orderId: string;
  razorpayOrderId: string;
  amount: number;
  requestedAt: Date;
}

export interface CODConversionCompleted {
  orderId: string;
  razorpayPaymentId: string;
  amount: number;
  convertedAt: Date;
}

// Delivery Events
export interface ShipmentCreated {
  orderId: string;
  shipmentId: string;
  trackingNumber: string;
  carrier: string;
  estimatedDelivery: Date;
  createdAt: Date;
}

export interface DeliveryStatusUpdated {
  orderId: string;
  shipmentId: string;
  status: 'PREPARING' | 'SHIPPED' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'CANCELLED';
  timestamp: Date;
  location?: string;
}

export interface DeliveryCompleted {
  orderId: string;
  shipmentId: string;
  deliveredAt: Date;
  deliveredTo: string;
  signature?: string;
}

// Installation Events
export interface InstallationRequested {
  orderId: string;
  consumerId: string;
  requestedAt: Date;
  preferredDate?: Date;
}

export interface InstallationScheduled {
  orderId: string;
  installationId: string;
  technicianId: string;
  scheduledDate: Date;
  scheduledAt: Date;
}

export interface InstallationCompleted {
  orderId: string;
  installationId: string;
  deviceId: string;
  technicianId: string;
  completedAt: Date;
  calibrationData?: any;
  photos?: string[];
}

export interface InstallationCancelled {
  orderId: string;
  installationId: string;
  cancelledBy: string;
  cancelledAt: Date;
  reason: string;
}

// Event Type Union
export type OrderingEvent = 
  | OrderCreated
  | OrderApproved
  | OrderCompleted
  | OrderCancelled
  | PaymentCompleted
  | PaymentFailed
  | CODConversionRequested
  | CODConversionCompleted
  | ShipmentCreated
  | DeliveryStatusUpdated
  | DeliveryCompleted
  | InstallationRequested
  | InstallationScheduled
  | InstallationCompleted
  | InstallationCancelled;

// Event Type Constants
export const EventTypes = {
  // Order Events
  ORDER_CREATED: 'ORDER_CREATED',
  ORDER_APPROVED: 'ORDER_APPROVED',
  ORDER_COMPLETED: 'ORDER_COMPLETED',
  ORDER_CANCELLED: 'ORDER_CANCELLED',
  
  // Payment Events
  PAYMENT_COMPLETED: 'PAYMENT_COMPLETED',
  PAYMENT_FAILED: 'PAYMENT_FAILED',
  COD_CONVERSION_REQUESTED: 'COD_CONVERSION_REQUESTED',
  COD_CONVERSION_COMPLETED: 'COD_CONVERSION_COMPLETED',
  
  // Delivery Events
  SHIPMENT_CREATED: 'SHIPMENT_CREATED',
  DELIVERY_STATUS_UPDATED: 'DELIVERY_STATUS_UPDATED',
  DELIVERY_COMPLETED: 'DELIVERY_COMPLETED',
  
  // Installation Events
  INSTALLATION_REQUESTED: 'INSTALLATION_REQUESTED',
  INSTALLATION_SCHEDULED: 'INSTALLATION_SCHEDULED',
  INSTALLATION_COMPLETED: 'INSTALLATION_COMPLETED',
  INSTALLATION_CANCELLED: 'INSTALLATION_CANCELLED'
} as const;

// Event Schema Validation (using Joi for runtime validation)
export const EventSchemas = {
  ORDER_CREATED: {
    orderId: 'string.required',
    consumerId: 'string.required',
    deviceType: 'string.required',
    paymentMethod: 'string.valid(COD, ONLINE).required',
    address: 'string.required',
    phone: 'string.required',
    createdAt: 'date.required'
  },
  
  ORDER_APPROVED: {
    orderId: 'string.required',
    approvedBy: 'string.required',
    approvedAt: 'date.required',
    quoteAmount: 'number.positive.required'
  },
  
  PAYMENT_COMPLETED: {
    orderId: 'string.required',
    paymentId: 'string.required',
    razorpayPaymentId: 'string.required',
    amount: 'number.positive.required',
    method: 'string.valid(COD, ONLINE).required',
    completedAt: 'date.required'
  },
  
  DELIVERY_STATUS_UPDATED: {
    orderId: 'string.required',
    shipmentId: 'string.required',
    status: 'string.valid(PREPARING, SHIPPED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED).required',
    timestamp: 'date.required',
    location: 'string.optional'
  },
  
  INSTALLATION_COMPLETED: {
    orderId: 'string.required',
    installationId: 'string.required',
    deviceId: 'string.required',
    technicianId: 'string.required',
    completedAt: 'date.required',
    calibrationData: 'object.optional',
    photos: 'array.items(string).optional'
  }
};