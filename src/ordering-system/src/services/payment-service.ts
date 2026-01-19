/**
 * Payment Service
 * Manages payment processing with Razorpay integration and secure key management
 * Implements Requirements 4.1, 8.1, 8.2
 */

import Razorpay from 'razorpay';
import crypto from 'crypto';
import { v4 as uuidv4 } from 'uuid';
import { Payment, RazorpayOrder } from '../types/entities';
import { PaymentCompleted, PaymentFailed, CODConversionRequested } from '../types/events';
import { EventTypes } from '../types/events';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';
import { concurrencyService } from './concurrency-service';

export type PaymentStatus = 'UNPAID' | 'PAID' | 'COD_PENDING' | 'FAILED';
export type PaymentMethod = 'COD' | 'ONLINE';

export interface CreatePaymentOrderRequest {
  orderId: string;
  amount: number;
  currency?: string;
  receipt?: string;
  notes?: Record<string, string>;
}

export interface ProcessPaymentRequest {
  orderId: string;
  razorpayPaymentId: string;
  razorpayOrderId: string;
  razorpaySignature: string;
}

export interface PaymentConfig {
  keyId: string;
  keySecret: string;
  webhookSecret: string;
  currency: string;
  environment: 'test' | 'live';
}

/**
 * Payment Service Implementation
 */
export class PaymentService {
  private razorpay: Razorpay;
  private logger: Logger;
  private config: PaymentConfig;

  constructor(config?: Partial<PaymentConfig>) {
    this.config = {
      keyId: process.env.RAZORPAY_KEY_ID || 'rzp_test_dummy',
      keySecret: process.env.RAZORPAY_KEY_SECRET || 'dummy_secret',
      webhookSecret: process.env.RAZORPAY_WEBHOOK_SECRET || 'dummy_webhook_secret',
      currency: 'INR',
      environment: (process.env.NODE_ENV === 'production' ? 'live' : 'test') as 'test' | 'live',
      ...config
    };

    this.logger = new Logger('PaymentService');
    
    // Initialize Razorpay client with secure key management
    this.razorpay = new Razorpay({
      key_id: this.config.keyId,
      key_secret: this.config.keySecret
    });

    this.logger.info('Payment service initialized', {
      environment: this.config.environment,
      currency: this.config.currency,
      keyIdMasked: this.maskSensitiveData(this.config.keyId)
    });
  }

  /**
   * Create payment order with unique ID generation
   * Implements Requirements 8.1, 8.2
   */
  async createPaymentOrder(request: CreatePaymentOrderRequest): Promise<{
    payment: Payment;
    razorpayOrder: RazorpayOrder;
  }> {
    this.logger.info('Creating payment order', {
      orderId: request.orderId,
      amount: request.amount,
      currency: request.currency || this.config.currency
    });

    try {
      // Generate unique receipt ID (Requirement 8.2)
      const receipt = request.receipt || `order_${request.orderId}_${Date.now()}`;
      
      // Ensure receipt uniqueness
      const existingPayment = database.findWhere<Payment>('payments', 
        p => p.razorpayOrderId === receipt
      );
      
      if (existingPayment.length > 0) {
        throw new Error(`Payment order with receipt ${receipt} already exists`);
      }

      // Create Razorpay order
      const razorpayOrderData = {
        amount: Math.round(request.amount * 100), // Convert to paise
        currency: request.currency || this.config.currency,
        receipt,
        notes: {
          orderId: request.orderId,
          ...request.notes
        }
      };

      const razorpayOrder = await this.razorpay.orders.create(razorpayOrderData);

      // Create payment entity with version
      const payment: Payment = {
        id: uuidv4(),
        orderId: request.orderId,
        razorpayOrderId: razorpayOrder.id,
        amount: request.amount,
        currency: request.currency || this.config.currency,
        status: 'UNPAID',
        paymentMethod: 'ONLINE',
        createdAt: new Date(),
        version: 1 // Initialize version for optimistic locking
      };

      // Store payment in database
      const createdPayment = database.create<Payment>('payments', payment);

      this.logger.business('Payment order created', {
        paymentId: createdPayment.id,
        orderId: request.orderId,
        razorpayOrderId: razorpayOrder.id,
        amount: request.amount,
        receipt
      });

      return {
        payment: createdPayment,
        razorpayOrder: razorpayOrder as any
      };

    } catch (error) {
      this.logger.error('Failed to create payment order', error, {
        orderId: request.orderId,
        amount: request.amount
      });

      throw new Error(
        `Payment order creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Process payment completion with optimistic locking
   */
  async processPayment(request: ProcessPaymentRequest): Promise<Payment> {
    this.logger.info('Processing payment with concurrency control', {
      orderId: request.orderId,
      razorpayPaymentId: request.razorpayPaymentId,
      razorpayOrderId: request.razorpayOrderId
    });

    try {
      // Verify payment signature
      const isValidSignature = this.verifyPaymentSignature(
        request.razorpayOrderId,
        request.razorpayPaymentId,
        request.razorpaySignature
      );

      if (!isValidSignature) {
        throw new Error('Invalid payment signature');
      }

      // Get payment from database
      const payment = database.findWhere<Payment>('payments', 
        p => p.orderId === request.orderId && p.razorpayOrderId === request.razorpayOrderId
      )[0];

      if (!payment) {
        throw new Error(`Payment not found for order: ${request.orderId}`);
      }

      // Fetch payment details from Razorpay
      const razorpayPayment = await this.razorpay.payments.fetch(request.razorpayPaymentId);

      // Verify payment status
      if (razorpayPayment.status !== 'captured' && razorpayPayment.status !== 'authorized') {
        throw new Error(`Payment not successful. Status: ${razorpayPayment.status}`);
      }

      // Update payment using optimistic locking
      const updatedPayment = await concurrencyService.withOptimisticLock<Payment>(
        'payments',
        payment.id,
        async (currentPayment: Payment) => {
          // Create and publish payment completed event
          const paymentCompletedEvent: PaymentCompleted = {
            orderId: request.orderId,
            paymentId: currentPayment.id,
            razorpayPaymentId: request.razorpayPaymentId,
            amount: currentPayment.amount,
            method: 'ONLINE',
            completedAt: new Date()
          };

          await eventBus.publish(
            request.orderId,
            'Payment',
            EventTypes.PAYMENT_COMPLETED,
            paymentCompletedEvent
          );

          this.logger.business('Payment processed successfully with concurrency control', {
            paymentId: currentPayment.id,
            orderId: request.orderId,
            razorpayPaymentId: request.razorpayPaymentId,
            amount: currentPayment.amount,
            oldVersion: currentPayment.version,
            newVersion: currentPayment.version + 1
          });

          return {
            status: 'PAID',
            razorpayPaymentId: request.razorpayPaymentId,
            paidAt: new Date()
          };
        },
        'processPayment'
      );

      return updatedPayment;

    } catch (error) {
      this.logger.error('Payment processing failed', error, {
        orderId: request.orderId,
        razorpayPaymentId: request.razorpayPaymentId
      });

      // Create payment failed event
      const paymentFailedEvent: PaymentFailed = {
        orderId: request.orderId,
        paymentId: uuidv4(),
        razorpayPaymentId: request.razorpayPaymentId,
        reason: error instanceof Error ? error.message : 'Unknown error',
        failedAt: new Date()
      };

      await eventBus.publish(
        request.orderId,
        'Payment',
        EventTypes.PAYMENT_FAILED,
        paymentFailedEvent
      );

      throw error;
    }
  }

  /**
   * Create COD payment record with version
   */
  async createCODPayment(orderId: string, amount: number): Promise<Payment> {
    this.logger.info('Creating COD payment', { orderId, amount });

    const payment: Payment = {
      id: uuidv4(),
      orderId,
      amount,
      currency: this.config.currency,
      status: 'COD_PENDING',
      paymentMethod: 'COD',
      createdAt: new Date(),
      version: 1 // Initialize version for optimistic locking
    };

    const createdPayment = database.create<Payment>('payments', payment);

    this.logger.business('COD payment created', {
      paymentId: createdPayment.id,
      orderId,
      amount
    });

    return createdPayment;
  }

  /**
   * Convert COD to online payment
   */
  async convertCODToOnline(orderId: string): Promise<{
    payment: Payment;
    razorpayOrder: RazorpayOrder;
  }> {
    this.logger.info('Converting COD to online payment', { orderId });

    // Get existing COD payment
    const codPayment = database.findWhere<Payment>('payments', 
      p => p.orderId === orderId && p.paymentMethod === 'COD'
    )[0];

    if (!codPayment) {
      throw new Error(`COD payment not found for order: ${orderId}`);
    }

    if (codPayment.status !== 'COD_PENDING') {
      throw new Error(`COD payment cannot be converted. Current status: ${codPayment.status}`);
    }

    // Create new online payment order
    const result = await this.createPaymentOrder({
      orderId,
      amount: codPayment.amount,
      notes: {
        convertedFromCOD: 'true',
        originalPaymentId: codPayment.id
      }
    });

    // Create COD conversion requested event
    const codConversionEvent: CODConversionRequested = {
      orderId,
      razorpayOrderId: result.razorpayOrder.id,
      amount: codPayment.amount,
      requestedAt: new Date()
    };

    await eventBus.publish(
      orderId,
      'Payment',
      EventTypes.COD_CONVERSION_REQUESTED,
      codConversionEvent
    );

    this.logger.business('COD conversion initiated', {
      orderId,
      originalPaymentId: codPayment.id,
      newPaymentId: result.payment.id,
      razorpayOrderId: result.razorpayOrder.id
    });

    return result;
  }

  /**
   * Get payment by order ID
   */
  async getPaymentByOrderId(orderId: string): Promise<Payment | null> {
    const payments = database.findWhere<Payment>('payments', p => p.orderId === orderId);
    return payments.length > 0 ? payments[0] : null;
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(orderId: string): Promise<{
    status: PaymentStatus;
    method: PaymentMethod;
    amount?: number;
    paidAt?: Date;
    canConvertToOnline?: boolean;
  }> {
    const payment = await this.getPaymentByOrderId(orderId);
    
    if (!payment) {
      return {
        status: 'UNPAID',
        method: 'ONLINE'
      };
    }

    const result: {
      status: PaymentStatus;
      method: PaymentMethod;
      amount?: number;
      paidAt?: Date;
      canConvertToOnline?: boolean;
    } = {
      status: payment.status,
      method: payment.paymentMethod,
      amount: payment.amount,
      canConvertToOnline: payment.paymentMethod === 'COD' && payment.status === 'COD_PENDING'
    };

    if (payment.paidAt) {
      result.paidAt = payment.paidAt;
    }

    return result;
  }

  /**
   * Verify Razorpay payment signature
   */
  private verifyPaymentSignature(
    razorpayOrderId: string,
    razorpayPaymentId: string,
    razorpaySignature: string
  ): boolean {
    try {
      const body = razorpayOrderId + '|' + razorpayPaymentId;
      const expectedSignature = crypto
        .createHmac('sha256', this.config.keySecret)
        .update(body.toString())
        .digest('hex');

      return expectedSignature === razorpaySignature;
    } catch (error) {
      this.logger.error('Signature verification failed', error);
      return false;
    }
  }

  /**
   * Mask sensitive data for logging
   */
  private maskSensitiveData(data: string): string {
    if (data.length <= 8) {
      return '*'.repeat(data.length);
    }
    return data.substring(0, 4) + '*'.repeat(data.length - 8) + data.substring(data.length - 4);
  }

  /**
   * Get payment statistics
   */
  async getPaymentStatistics(): Promise<{
    totalPayments: number;
    paidPayments: number;
    codPendingPayments: number;
    failedPayments: number;
    totalAmount: number;
    averageAmount: number;
  }> {
    const allPayments = database.findAll<Payment>('payments');
    
    const stats = {
      totalPayments: allPayments.length,
      paidPayments: allPayments.filter(p => p.status === 'PAID').length,
      codPendingPayments: allPayments.filter(p => p.status === 'COD_PENDING').length,
      failedPayments: allPayments.filter(p => p.status === 'FAILED').length,
      totalAmount: allPayments.reduce((sum, p) => sum + p.amount, 0),
      averageAmount: 0
    };

    if (stats.totalPayments > 0) {
      stats.averageAmount = Math.round(stats.totalAmount / stats.totalPayments);
    }

    return stats;
  }
}

// Export singleton instance
export const paymentService = new PaymentService();