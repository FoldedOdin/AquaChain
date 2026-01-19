/**
 * Domain Event JSON Schemas and Versioning Strategy
 * Provides schema validation and backward compatibility for all domain events
 */

import Joi from 'joi';

// Schema version constants
export const SCHEMA_VERSION = {
  CURRENT: '1.0.0',
  SUPPORTED: ['1.0.0']
} as const;

// Base event schema
const baseEventSchema = Joi.object({
  id: Joi.string().uuid().required(),
  aggregateId: Joi.string().required(),
  aggregateType: Joi.string().valid('Order', 'Payment', 'Delivery', 'Installation').required(),
  eventType: Joi.string().required(),
  version: Joi.number().integer().min(1).required(),
  timestamp: Joi.date().required(),
  correlationId: Joi.string().uuid().optional(),
  schemaVersion: Joi.string().default(SCHEMA_VERSION.CURRENT)
});

// Order Event Schemas
export const OrderEventSchemas = {
  ORDER_CREATED: baseEventSchema.keys({
    eventType: Joi.string().valid('ORDER_CREATED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      consumerId: Joi.string().required(),
      deviceType: Joi.string().required(),
      paymentMethod: Joi.string().valid('COD', 'ONLINE').required(),
      address: Joi.string().required(),
      phone: Joi.string().pattern(/^\+?[\d\s\-\(\)]+$/).required(),
      createdAt: Joi.date().required()
    }).required()
  }),

  ORDER_APPROVED: baseEventSchema.keys({
    eventType: Joi.string().valid('ORDER_APPROVED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      approvedBy: Joi.string().required(),
      approvedAt: Joi.date().required(),
      quoteAmount: Joi.number().positive().required()
    }).required()
  }),

  ORDER_COMPLETED: baseEventSchema.keys({
    eventType: Joi.string().valid('ORDER_COMPLETED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      completedAt: Joi.date().required()
    }).required()
  }),

  ORDER_CANCELLED: baseEventSchema.keys({
    eventType: Joi.string().valid('ORDER_CANCELLED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      cancelledBy: Joi.string().required(),
      cancelledAt: Joi.date().required(),
      reason: Joi.string().required()
    }).required()
  })
};

// Payment Event Schemas
export const PaymentEventSchemas = {
  PAYMENT_COMPLETED: baseEventSchema.keys({
    eventType: Joi.string().valid('PAYMENT_COMPLETED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      paymentId: Joi.string().required(),
      razorpayPaymentId: Joi.string().required(),
      amount: Joi.number().positive().required(),
      method: Joi.string().valid('COD', 'ONLINE').required(),
      completedAt: Joi.date().required()
    }).required()
  }),

  PAYMENT_FAILED: baseEventSchema.keys({
    eventType: Joi.string().valid('PAYMENT_FAILED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      paymentId: Joi.string().required(),
      razorpayPaymentId: Joi.string().optional(),
      reason: Joi.string().required(),
      failedAt: Joi.date().required()
    }).required()
  }),

  COD_CONVERSION_REQUESTED: baseEventSchema.keys({
    eventType: Joi.string().valid('COD_CONVERSION_REQUESTED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      razorpayOrderId: Joi.string().required(),
      amount: Joi.number().positive().required(),
      requestedAt: Joi.date().required()
    }).required()
  }),

  COD_CONVERSION_COMPLETED: baseEventSchema.keys({
    eventType: Joi.string().valid('COD_CONVERSION_COMPLETED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      razorpayPaymentId: Joi.string().required(),
      amount: Joi.number().positive().required(),
      convertedAt: Joi.date().required()
    }).required()
  })
};

// Delivery Event Schemas
export const DeliveryEventSchemas = {
  SHIPMENT_CREATED: baseEventSchema.keys({
    eventType: Joi.string().valid('SHIPMENT_CREATED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      shipmentId: Joi.string().required(),
      trackingNumber: Joi.string().required(),
      carrier: Joi.string().required(),
      estimatedDelivery: Joi.date().required(),
      createdAt: Joi.date().required()
    }).required()
  }),

  DELIVERY_STATUS_UPDATED: baseEventSchema.keys({
    eventType: Joi.string().valid('DELIVERY_STATUS_UPDATED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      shipmentId: Joi.string().required(),
      status: Joi.string().valid('PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED').required(),
      timestamp: Joi.date().required(),
      location: Joi.string().optional()
    }).required()
  }),

  DELIVERY_COMPLETED: baseEventSchema.keys({
    eventType: Joi.string().valid('DELIVERY_COMPLETED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      shipmentId: Joi.string().required(),
      deliveredAt: Joi.date().required(),
      deliveredTo: Joi.string().required(),
      signature: Joi.string().optional()
    }).required()
  })
};

// Installation Event Schemas
export const InstallationEventSchemas = {
  INSTALLATION_REQUESTED: baseEventSchema.keys({
    eventType: Joi.string().valid('INSTALLATION_REQUESTED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      consumerId: Joi.string().required(),
      requestedAt: Joi.date().required(),
      preferredDate: Joi.date().optional()
    }).required()
  }),

  INSTALLATION_SCHEDULED: baseEventSchema.keys({
    eventType: Joi.string().valid('INSTALLATION_SCHEDULED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      installationId: Joi.string().required(),
      technicianId: Joi.string().required(),
      scheduledDate: Joi.date().required(),
      scheduledAt: Joi.date().required()
    }).required()
  }),

  INSTALLATION_COMPLETED: baseEventSchema.keys({
    eventType: Joi.string().valid('INSTALLATION_COMPLETED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      installationId: Joi.string().required(),
      deviceId: Joi.string().required(),
      technicianId: Joi.string().required(),
      completedAt: Joi.date().required(),
      calibrationData: Joi.object().optional(),
      photos: Joi.array().items(Joi.string()).optional()
    }).required()
  }),

  INSTALLATION_CANCELLED: baseEventSchema.keys({
    eventType: Joi.string().valid('INSTALLATION_CANCELLED').required(),
    eventData: Joi.object({
      orderId: Joi.string().required(),
      installationId: Joi.string().required(),
      cancelledBy: Joi.string().required(),
      cancelledAt: Joi.date().required(),
      reason: Joi.string().required()
    }).required()
  })
};

// Combined schema registry
export const EventSchemaRegistry = {
  ...OrderEventSchemas,
  ...PaymentEventSchemas,
  ...DeliveryEventSchemas,
  ...InstallationEventSchemas
};

/**
 * Event Schema Validator
 */
export class EventSchemaValidator {
  /**
   * Validate an event against its schema
   */
  static validate(eventType: string, event: any): { isValid: boolean; error?: string } {
    const schema = EventSchemaRegistry[eventType as keyof typeof EventSchemaRegistry];
    
    if (!schema) {
      return {
        isValid: false,
        error: `No schema found for event type: ${eventType}`
      };
    }

    const { error } = schema.validate(event);
    
    if (error) {
      return {
        isValid: false,
        error: error.details.map(d => d.message).join(', ')
      };
    }

    return { isValid: true };
  }

  /**
   * Check if schema version is supported
   */
  static isSupportedVersion(version: string): boolean {
    return SCHEMA_VERSION.SUPPORTED.includes(version as any);
  }

  /**
   * Migrate event to current schema version
   */
  static migrateEvent(event: any): any {
    const eventVersion = event.schemaVersion || '1.0.0';
    
    if (eventVersion === SCHEMA_VERSION.CURRENT) {
      return event;
    }

    // Migration logic for different versions
    switch (eventVersion) {
      case '1.0.0':
        // No migration needed - this is current version
        return event;
      
      default:
        throw new Error(`Unsupported schema version: ${eventVersion}`);
    }
  }

  /**
   * Get all supported event types
   */
  static getSupportedEventTypes(): string[] {
    return Object.keys(EventSchemaRegistry);
  }
}

/**
 * Event Version Manager
 */
export class EventVersionManager {
  private static versionHistory: Record<string, string[]> = {
    'ORDER_CREATED': ['1.0.0'],
    'ORDER_APPROVED': ['1.0.0'],
    'ORDER_COMPLETED': ['1.0.0'],
    'ORDER_CANCELLED': ['1.0.0'],
    'PAYMENT_COMPLETED': ['1.0.0'],
    'PAYMENT_FAILED': ['1.0.0'],
    'COD_CONVERSION_REQUESTED': ['1.0.0'],
    'COD_CONVERSION_COMPLETED': ['1.0.0'],
    'SHIPMENT_CREATED': ['1.0.0'],
    'DELIVERY_STATUS_UPDATED': ['1.0.0'],
    'DELIVERY_COMPLETED': ['1.0.0'],
    'INSTALLATION_REQUESTED': ['1.0.0'],
    'INSTALLATION_SCHEDULED': ['1.0.0'],
    'INSTALLATION_COMPLETED': ['1.0.0'],
    'INSTALLATION_CANCELLED': ['1.0.0']
  };

  /**
   * Get version history for an event type
   */
  static getVersionHistory(eventType: string): string[] {
    return this.versionHistory[eventType] || [];
  }

  /**
   * Check if event type supports a specific version
   */
  static supportsVersion(eventType: string, version: string): boolean {
    const history = this.getVersionHistory(eventType);
    return history.includes(version);
  }

  /**
   * Get latest version for an event type
   */
  static getLatestVersion(eventType: string): string {
    const history = this.getVersionHistory(eventType);
    return history[history.length - 1] || SCHEMA_VERSION.CURRENT;
  }

  /**
   * Add new version for an event type
   */
  static addVersion(eventType: string, version: string): void {
    if (!this.versionHistory[eventType]) {
      this.versionHistory[eventType] = [];
    }
    
    if (!this.versionHistory[eventType].includes(version)) {
      this.versionHistory[eventType].push(version);
    }
  }
}

/**
 * Backward Compatibility Manager
 */
export class BackwardCompatibilityManager {
  /**
   * Transform event from old version to new version
   */
  static transformEvent(event: any, fromVersion: string, toVersion: string): any {
    if (fromVersion === toVersion) {
      return event;
    }

    // Add transformation logic here as schemas evolve
    // For now, we only have version 1.0.0
    return event;
  }

  /**
   * Check if transformation is possible between versions
   */
  static canTransform(fromVersion: string, toVersion: string): boolean {
    // For now, all supported versions can be transformed
    return SCHEMA_VERSION.SUPPORTED.includes(fromVersion as any) && 
           SCHEMA_VERSION.SUPPORTED.includes(toVersion as any);
  }
}

// Export validation functions for easy use
export const validateEvent = EventSchemaValidator.validate;
export const isSupportedVersion = EventSchemaValidator.isSupportedVersion;
export const migrateEvent = EventSchemaValidator.migrateEvent;