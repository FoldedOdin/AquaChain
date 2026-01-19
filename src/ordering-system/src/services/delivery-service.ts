/**
 * Delivery Service
 * Manages delivery state tracking and shipment creation
 * Implements Requirements 7.1, 7.2, 7.3, 7.4
 */

import { v4 as uuidv4 } from 'uuid';
import { Delivery, Address } from '../types/entities';
import { ShipmentCreated, DeliveryStatusUpdated, DeliveryCompleted } from '../types/events';
import { EventTypes } from '../types/events';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';
import { concurrencyService } from './concurrency-service';

export type DeliveryStatus = 'PREPARING' | 'SHIPPED' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'CANCELLED';

export interface CreateShipmentRequest {
  orderId: string;
  address: Address;
  carrier?: string;
  estimatedDelivery?: Date;
}

export interface UpdateDeliveryStatusRequest {
  shipmentId: string;
  status: DeliveryStatus;
  location?: string;
  notes?: string;
}

export interface TrackingInfo {
  shipmentId: string;
  trackingNumber: string;
  status: DeliveryStatus;
  currentLocation?: string;
  estimatedDelivery?: Date;
  actualDelivery?: Date;
  statusHistory: {
    status: DeliveryStatus;
    timestamp: Date;
    location?: string;
    notes?: string;
  }[];
}

/**
 * Delivery State Machine
 * Defines valid state transitions for delivery tracking
 */
export class DeliveryStateMachine {
  private static readonly VALID_TRANSITIONS: Record<DeliveryStatus, DeliveryStatus[]> = {
    PREPARING: ['SHIPPED', 'CANCELLED'],
    SHIPPED: ['OUT_FOR_DELIVERY', 'CANCELLED'],
    OUT_FOR_DELIVERY: ['DELIVERED', 'CANCELLED'],
    DELIVERED: [], // Terminal state
    CANCELLED: []  // Terminal state
  };

  /**
   * Check if state transition is valid
   */
  static isValidTransition(from: DeliveryStatus, to: DeliveryStatus): boolean {
    return this.VALID_TRANSITIONS[from].includes(to);
  }

  /**
   * Get valid next states for current state
   */
  static getValidNextStates(currentState: DeliveryStatus): DeliveryStatus[] {
    return [...this.VALID_TRANSITIONS[currentState]];
  }

  /**
   * Validate state transition and throw error if invalid
   */
  static validateTransition(from: DeliveryStatus, to: DeliveryStatus): void {
    if (!this.isValidTransition(from, to)) {
      throw new Error(
        `Invalid delivery state transition from ${from} to ${to}. ` +
        `Valid transitions from ${from}: ${this.VALID_TRANSITIONS[from].join(', ')}`
      );
    }
  }
}

/**
 * Delivery Service Implementation
 */
export class DeliveryService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('DeliveryService');
  }

  /**
   * Initiate shipment for an approved order
   * Implements Requirements 7.1, 7.2
   */
  async initiateShipment(request: CreateShipmentRequest): Promise<Delivery> {
    this.logger.info('Initiating shipment', {
      orderId: request.orderId,
      carrier: request.carrier
    });

    try {
      // Validate request
      this.validateCreateShipmentRequest(request);

      // Check if shipment already exists for this order
      const existingDelivery = database.findWhere<Delivery>('deliveries', 
        d => d.orderId === request.orderId
      )[0];

      if (existingDelivery) {
        throw new Error(`Shipment already exists for order: ${request.orderId}`);
      }

      // Generate tracking number
      const trackingNumber = this.generateTrackingNumber();
      const shipmentId = uuidv4();
      const now = new Date();

      // Create delivery entity with version
      const delivery: Delivery = {
        id: shipmentId,
        orderId: request.orderId,
        shipmentId,
        trackingNumber,
        carrier: request.carrier || 'Standard Delivery',
        status: 'PREPARING',
        address: request.address,
        estimatedDelivery: request.estimatedDelivery || this.calculateEstimatedDelivery(),
        version: 1 // Initialize version for optimistic locking
      };

      // Store delivery in database
      const createdDelivery = database.create<Delivery>('deliveries', delivery);

      // Create and publish shipment created event
      const shipmentCreatedEvent: ShipmentCreated = {
        orderId: request.orderId,
        shipmentId,
        trackingNumber,
        carrier: delivery.carrier,
        estimatedDelivery: delivery.estimatedDelivery!,
        createdAt: now
      };

      await eventBus.publish(
        request.orderId,
        'Delivery',
        EventTypes.SHIPMENT_CREATED,
        shipmentCreatedEvent
      );

      this.logger.business('Shipment created', {
        orderId: request.orderId,
        shipmentId,
        trackingNumber,
        carrier: delivery.carrier
      });

      return createdDelivery;

    } catch (error) {
      this.logger.error('Failed to initiate shipment', error, {
        orderId: request.orderId
      });
      throw error;
    }
  }

  /**
   * Update delivery status with proper state machine validation and optimistic locking
   * Implements Requirements 7.3, 7.4, 9.2
   */
  async updateDeliveryStatus(request: UpdateDeliveryStatusRequest): Promise<Delivery> {
    this.logger.info('Updating delivery status with concurrency control', {
      shipmentId: request.shipmentId,
      status: request.status,
      location: request.location
    });

    return concurrencyService.withOptimisticLock<Delivery>(
      'deliveries',
      request.shipmentId,
      async (delivery: Delivery) => {
        // Validate state transition
        DeliveryStateMachine.validateTransition(delivery.status, request.status);

        const now = new Date();
        const updates: Partial<Delivery> = {
          status: request.status
        };

        // Set specific timestamps based on status
        if (request.status === 'SHIPPED') {
          updates.shippedAt = now;
        } else if (request.status === 'DELIVERED') {
          updates.deliveredAt = now;
        }

        // Create and publish delivery status updated event
        const statusUpdatedEvent: DeliveryStatusUpdated = {
          orderId: delivery.orderId,
          shipmentId: request.shipmentId,
          status: request.status,
          timestamp: now,
          ...(request.location && { location: request.location })
        };

        await eventBus.publish(
          delivery.orderId,
          'Delivery',
          EventTypes.DELIVERY_STATUS_UPDATED,
          statusUpdatedEvent
        );

        // If delivered, publish delivery completed event
        if (request.status === 'DELIVERED') {
          const deliveryCompletedEvent: DeliveryCompleted = {
            orderId: delivery.orderId,
            shipmentId: request.shipmentId,
            deliveredAt: now,
            deliveredTo: 'Consumer' // Would be actual recipient in production
          };

          await eventBus.publish(
            delivery.orderId,
            'Delivery',
            EventTypes.DELIVERY_COMPLETED,
            deliveryCompletedEvent
          );
        }

        this.logger.business('Delivery status updated with concurrency control', {
          orderId: delivery.orderId,
          shipmentId: request.shipmentId,
          oldStatus: delivery.status,
          newStatus: request.status,
          location: request.location,
          oldVersion: delivery.version,
          newVersion: delivery.version + 1
        });

        return updates;
      },
      'updateDeliveryStatus'
    );
  }

  /**
   * Get tracking information for a shipment
   */
  async getTrackingInfo(shipmentId: string): Promise<TrackingInfo | null> {
    const delivery = database.findById<Delivery>('deliveries', shipmentId);
    if (!delivery) {
      return null;
    }

    // In a real system, this would fetch from delivery provider APIs
    // For now, we'll construct from our data
    const trackingInfo: TrackingInfo = {
      shipmentId: delivery.shipmentId,
      trackingNumber: delivery.trackingNumber,
      status: delivery.status,
      ...(delivery.estimatedDelivery && { estimatedDelivery: delivery.estimatedDelivery }),
      ...(delivery.deliveredAt && { actualDelivery: delivery.deliveredAt }),
      statusHistory: [
        {
          status: 'PREPARING',
          timestamp: new Date(delivery.id), // Using creation time as preparing time
          notes: 'Shipment being prepared'
        }
      ]
    };

    // Add shipped status if applicable
    if (delivery.shippedAt) {
      trackingInfo.statusHistory.push({
        status: 'SHIPPED',
        timestamp: delivery.shippedAt,
        notes: `Shipped via ${delivery.carrier}`
      });
    }

    // Add delivered status if applicable
    if (delivery.deliveredAt) {
      trackingInfo.statusHistory.push({
        status: 'DELIVERED',
        timestamp: delivery.deliveredAt,
        notes: 'Package delivered successfully'
      });
    }

    return trackingInfo;
  }

  /**
   * Get delivery by order ID
   */
  async getDeliveryByOrderId(orderId: string): Promise<Delivery | null> {
    const deliveries = database.findWhere<Delivery>('deliveries', d => d.orderId === orderId);
    return deliveries.length > 0 ? deliveries[0] : null;
  }

  /**
   * Get all deliveries by status
   */
  async getDeliveriesByStatus(status: DeliveryStatus): Promise<Delivery[]> {
    return database.findWhere<Delivery>('deliveries', d => d.status === status);
  }

  /**
   * Get all deliveries
   */
  async getAllDeliveries(): Promise<Delivery[]> {
    return database.findAll<Delivery>('deliveries');
  }

  /**
   * Cancel delivery (if possible)
   */
  async cancelDelivery(shipmentId: string, reason: string): Promise<Delivery> {
    this.logger.info('Cancelling delivery', { shipmentId, reason });

    const delivery = database.findById<Delivery>('deliveries', shipmentId);
    if (!delivery) {
      throw new Error(`Delivery not found: ${shipmentId}`);
    }

    // Check if cancellation is allowed
    if (delivery.status === 'DELIVERED') {
      throw new Error('Cannot cancel delivered shipment');
    }

    // Validate state transition
    DeliveryStateMachine.validateTransition(delivery.status, 'CANCELLED');

    // Update delivery
    const updatedDelivery = database.update<Delivery>('deliveries', shipmentId, {
      status: 'CANCELLED',
      cancelledAt: new Date(),
      cancelReason: reason
    });

    if (!updatedDelivery) {
      throw new Error('Failed to cancel delivery');
    }

    // Publish status update event
    const statusUpdatedEvent: DeliveryStatusUpdated = {
      orderId: delivery.orderId,
      shipmentId,
      status: 'CANCELLED',
      timestamp: new Date()
    };

    await eventBus.publish(
      delivery.orderId,
      'Delivery',
      EventTypes.DELIVERY_STATUS_UPDATED,
      statusUpdatedEvent
    );

    this.logger.business('Delivery cancelled', {
      orderId: delivery.orderId,
      shipmentId,
      reason
    });

    return updatedDelivery;
  }

  /**
   * Generate unique tracking number
   */
  private generateTrackingNumber(): string {
    const timestamp = Date.now().toString();
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `AC${timestamp.slice(-6)}${random}`;
  }

  /**
   * Calculate estimated delivery date (3-5 business days)
   */
  private calculateEstimatedDelivery(): Date {
    const now = new Date();
    const businessDays = 3 + Math.floor(Math.random() * 3); // 3-5 days
    const estimatedDate = new Date(now);
    
    let addedDays = 0;
    while (addedDays < businessDays) {
      estimatedDate.setDate(estimatedDate.getDate() + 1);
      // Skip weekends (0 = Sunday, 6 = Saturday)
      if (estimatedDate.getDay() !== 0 && estimatedDate.getDay() !== 6) {
        addedDays++;
      }
    }
    
    return estimatedDate;
  }

  /**
   * Validate create shipment request
   */
  private validateCreateShipmentRequest(request: CreateShipmentRequest): void {
    const errors: string[] = [];

    if (!request.orderId?.trim()) {
      errors.push('Order ID is required');
    }

    if (!request.address) {
      errors.push('Delivery address is required');
    } else {
      if (!request.address.street?.trim()) {
        errors.push('Street address is required');
      }
      if (!request.address.city?.trim()) {
        errors.push('City is required');
      }
      if (!request.address.state?.trim()) {
        errors.push('State is required');
      }
      if (!request.address.postalCode?.trim()) {
        errors.push('Postal code is required');
      }
    }

    if (errors.length > 0) {
      throw new Error(`Shipment validation failed: ${errors.join(', ')}`);
    }
  }

  /**
   * Get delivery statistics
   */
  async getDeliveryStatistics(): Promise<{
    totalDeliveries: number;
    preparing: number;
    shipped: number;
    outForDelivery: number;
    delivered: number;
    cancelled: number;
    averageDeliveryTime?: number;
  }> {
    const allDeliveries = await this.getAllDeliveries();
    
    const stats: {
      totalDeliveries: number;
      preparing: number;
      shipped: number;
      outForDelivery: number;
      delivered: number;
      cancelled: number;
      averageDeliveryTime?: number;
    } = {
      totalDeliveries: allDeliveries.length,
      preparing: allDeliveries.filter(d => d.status === 'PREPARING').length,
      shipped: allDeliveries.filter(d => d.status === 'SHIPPED').length,
      outForDelivery: allDeliveries.filter(d => d.status === 'OUT_FOR_DELIVERY').length,
      delivered: allDeliveries.filter(d => d.status === 'DELIVERED').length,
      cancelled: allDeliveries.filter(d => d.status === 'CANCELLED').length
    };

    // Calculate average delivery time for delivered packages
    const deliveredPackages = allDeliveries.filter(d => 
      d.status === 'DELIVERED' && d.shippedAt && d.deliveredAt
    );

    if (deliveredPackages.length > 0) {
      const totalDeliveryTime = deliveredPackages.reduce((sum, delivery) => {
        const deliveryTime = new Date(delivery.deliveredAt!).getTime() - new Date(delivery.shippedAt!).getTime();
        return sum + deliveryTime;
      }, 0);
      
      stats.averageDeliveryTime = Math.round(totalDeliveryTime / deliveredPackages.length / (1000 * 60 * 60 * 24)); // in days
    }

    return stats;
  }
}

// Export singleton instance
export const deliveryService = new DeliveryService();