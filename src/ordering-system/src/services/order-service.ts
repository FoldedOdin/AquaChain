/**
 * Order Service
 * Manages order lifecycle with state machine validation
 * Implements Requirements 1.2, 1.5, 6.3
 */

import { v4 as uuidv4 } from 'uuid';
import { Order } from '../types/entities';
import { OrderCreated, OrderApproved, OrderCompleted, OrderCancelled } from '../types/events';
import { EventTypes } from '../types/events';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';
import { validateEvent } from '../schemas/event-schemas';
import { concurrencyService } from './concurrency-service';

export type OrderStatus = 'PENDING' | 'APPROVED' | 'COMPLETED' | 'CANCELLED';
export type PaymentMethod = 'COD' | 'ONLINE';

export interface CreateOrderRequest {
  consumerId: string;
  deviceType: string;
  paymentMethod: PaymentMethod;
  address: string;
  phone: string;
}

export interface ApproveOrderRequest {
  orderId: string;
  approvedBy: string;
  quoteAmount: number;
}

/**
 * Order State Machine
 * Defines valid state transitions and business rules
 */
export class OrderStateMachine {
  private static readonly VALID_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
    PENDING: ['APPROVED', 'CANCELLED'],
    APPROVED: ['COMPLETED', 'CANCELLED'],
    COMPLETED: [], // Terminal state
    CANCELLED: []  // Terminal state
  };

  /**
   * Check if state transition is valid
   */
  static isValidTransition(from: OrderStatus, to: OrderStatus): boolean {
    return this.VALID_TRANSITIONS[from].includes(to);
  }

  /**
   * Get valid next states for current state
   */
  static getValidNextStates(currentState: OrderStatus): OrderStatus[] {
    return [...this.VALID_TRANSITIONS[currentState]];
  }

  /**
   * Validate state transition and throw error if invalid
   */
  static validateTransition(from: OrderStatus, to: OrderStatus): void {
    if (!this.isValidTransition(from, to)) {
      throw new Error(
        `Invalid state transition from ${from} to ${to}. ` +
        `Valid transitions from ${from}: ${this.VALID_TRANSITIONS[from].join(', ')}`
      );
    }
  }
}

/**
 * Order Service Implementation
 */
export class OrderService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('OrderService');
  }

  /**
   * Create a new order with payment method selection
   * Implements Requirements 1.2, 1.5
   */
  async createOrder(request: CreateOrderRequest): Promise<Order> {
    this.logger.info('Creating new order', { request });

    // Validate payment method (Requirement 1.5)
    this.validatePaymentMethod(request.paymentMethod);

    // Validate required fields
    this.validateCreateOrderRequest(request);

    const orderId = uuidv4();
    const now = new Date();

    // Create order entity with version
    const order: Order = {
      id: orderId,
      consumerId: request.consumerId,
      deviceType: request.deviceType,
      paymentMethod: request.paymentMethod,
      status: 'PENDING',
      address: request.address,
      phone: request.phone,
      createdAt: now,
      updatedAt: now,
      version: 1 // Initialize version for optimistic locking
    };

    // Store order in database
    const createdOrder = database.create<Order>('orders', order);

    // Create and validate domain event
    const orderCreatedEvent: OrderCreated = {
      orderId: createdOrder.id,
      consumerId: createdOrder.consumerId,
      deviceType: createdOrder.deviceType,
      paymentMethod: createdOrder.paymentMethod,
      address: createdOrder.address,
      phone: createdOrder.phone,
      createdAt: createdOrder.createdAt
    };

    // Validate event schema
    const validation = validateEvent(EventTypes.ORDER_CREATED, {
      id: uuidv4(),
      aggregateId: orderId,
      aggregateType: 'Order',
      eventType: EventTypes.ORDER_CREATED,
      eventData: orderCreatedEvent,
      version: 1,
      timestamp: now
    });

    if (!validation.isValid) {
      throw new Error(`Event validation failed: ${validation.error}`);
    }

    // Publish domain event
    await eventBus.publish(
      orderId,
      'Order',
      EventTypes.ORDER_CREATED,
      orderCreatedEvent
    );

    this.logger.business('Order created', {
      orderId: createdOrder.id,
      consumerId: createdOrder.consumerId,
      paymentMethod: createdOrder.paymentMethod
    });

    return createdOrder;
  }

  /**
   * Approve an order with quote amount using optimistic locking
   * Implements Requirements 2.2, 2.3, 9.2
   */
  async approveOrder(request: ApproveOrderRequest): Promise<Order> {
    this.logger.info('Approving order with concurrency control', { request });

    return concurrencyService.withOptimisticLock<Order>(
      'orders',
      request.orderId,
      async (order: Order) => {
        // Validate state transition (Requirement 6.3)
        OrderStateMachine.validateTransition(order.status, 'APPROVED');

        // Validate quote amount
        if (request.quoteAmount <= 0) {
          throw new Error('Quote amount must be positive');
        }

        const now = new Date();

        // Create and validate domain event
        const orderApprovedEvent: OrderApproved = {
          orderId: order.id,
          approvedBy: request.approvedBy,
          approvedAt: now,
          quoteAmount: request.quoteAmount
        };

        // Validate event schema
        const validation = validateEvent(EventTypes.ORDER_APPROVED, {
          id: uuidv4(),
          aggregateId: request.orderId,
          aggregateType: 'Order',
          eventType: EventTypes.ORDER_APPROVED,
          eventData: orderApprovedEvent,
          version: 1,
          timestamp: now
        });

        if (!validation.isValid) {
          throw new Error(`Event validation failed: ${validation.error}`);
        }

        // Publish domain event
        await eventBus.publish(
          request.orderId,
          'Order',
          EventTypes.ORDER_APPROVED,
          orderApprovedEvent
        );

        this.logger.business('Order approved with concurrency control', {
          orderId: order.id,
          approvedBy: request.approvedBy,
          quoteAmount: request.quoteAmount,
          oldVersion: order.version,
          newVersion: order.version + 1
        });

        // Return updates to be applied
        return {
          status: 'APPROVED',
          quoteAmount: request.quoteAmount,
          approvedBy: request.approvedBy,
          approvedAt: now,
          updatedAt: now
        };
      },
      'approveOrder'
    );
  }

  /**
   * Complete an order using optimistic locking
   */
  async completeOrder(orderId: string): Promise<Order> {
    this.logger.info('Completing order with concurrency control', { orderId });

    return concurrencyService.withOptimisticLock<Order>(
      'orders',
      orderId,
      async (order: Order) => {
        // Validate state transition
        OrderStateMachine.validateTransition(order.status, 'COMPLETED');

        const now = new Date();

        // Create and publish domain event
        const orderCompletedEvent: OrderCompleted = {
          orderId: order.id,
          completedAt: now
        };

        await eventBus.publish(
          orderId,
          'Order',
          EventTypes.ORDER_COMPLETED,
          orderCompletedEvent
        );

        this.logger.business('Order completed with concurrency control', { 
          orderId: order.id,
          oldVersion: order.version,
          newVersion: order.version + 1
        });

        return {
          status: 'COMPLETED',
          completedAt: now,
          updatedAt: now
        };
      },
      'completeOrder'
    );
  }

  /**
   * Cancel an order using optimistic locking with role-based validation
   */
  async cancelOrder(orderId: string, cancelledBy: string, reason: string, isAdmin: boolean = false): Promise<Order> {
    this.logger.info('Cancelling order with concurrency control', { orderId, cancelledBy, reason, isAdmin });

    return concurrencyService.withOptimisticLock<Order>(
      'orders',
      orderId,
      async (order: Order) => {
        // Role-based validation for state transitions
        if (!isAdmin) {
          // Consumers can only cancel PENDING orders
          if (order.status !== 'PENDING') {
            throw new Error(
              `Consumers can only cancel pending orders. Current status: ${order.status}. ` +
              'Please contact support for approved orders.'
            );
          }
        } else {
          // Admins can cancel PENDING and APPROVED orders, but not COMPLETED
          if (order.status === 'COMPLETED') {
            throw new Error(
              `Order ${orderId} is completed and cannot be cancelled. ` +
              'Please contact support for refund processing.'
            );
          }
        }

        // Validate state transition
        OrderStateMachine.validateTransition(order.status, 'CANCELLED');

        const now = new Date();

        // Create and publish domain event
        const orderCancelledEvent: OrderCancelled = {
          orderId: order.id,
          cancelledBy,
          cancelledAt: now,
          reason
        };

        await eventBus.publish(
          orderId,
          'Order',
          EventTypes.ORDER_CANCELLED,
          orderCancelledEvent
        );

        this.logger.business('Order cancelled with concurrency control', { 
          orderId: order.id, 
          cancelledBy, 
          reason,
          isAdmin,
          oldVersion: order.version,
          newVersion: order.version + 1
        });

        return {
          status: 'CANCELLED',
          cancelledAt: now,
          cancelReason: reason,
          updatedAt: now
        };
      },
      'cancelOrder'
    );
  }

  /**
   * Get order by ID
   */
  async getOrder(orderId: string): Promise<Order | null> {
    return database.findById<Order>('orders', orderId);
  }

  /**
   * Get orders by consumer ID
   */
  async getOrdersByConsumer(consumerId: string): Promise<Order[]> {
    return database.findWhere<Order>('orders', order => order.consumerId === consumerId);
  }

  /**
   * Get all orders
   */
  async getAllOrders(): Promise<Order[]> {
    return database.findAll<Order>('orders');
  }

  /**
   * Get orders by status
   */
  async getOrdersByStatus(status: OrderStatus): Promise<Order[]> {
    return database.findWhere<Order>('orders', order => order.status === status);
  }

  /**
   * Validate payment method selection (Requirement 1.5)
   */
  private validatePaymentMethod(paymentMethod: PaymentMethod): void {
    const validMethods: PaymentMethod[] = ['COD', 'ONLINE'];
    
    if (!validMethods.includes(paymentMethod)) {
      throw new Error(
        `Invalid payment method: ${paymentMethod}. ` +
        `Valid methods: ${validMethods.join(', ')}`
      );
    }
  }

  /**
   * Validate create order request
   */
  private validateCreateOrderRequest(request: CreateOrderRequest): void {
    const errors: string[] = [];

    if (!request.consumerId?.trim()) {
      errors.push('Consumer ID is required');
    }

    if (!request.deviceType?.trim()) {
      errors.push('Device type is required');
    }

    if (!request.address?.trim()) {
      errors.push('Address is required');
    }

    if (!request.phone?.trim()) {
      errors.push('Phone is required');
    } else if (!/^\+?[\d\s\-\(\)]+$/.test(request.phone)) {
      errors.push('Phone number format is invalid');
    }

    if (errors.length > 0) {
      throw new Error(`Validation failed: ${errors.join(', ')}`);
    }
  }
}

// Export singleton instance
export const orderService = new OrderService();