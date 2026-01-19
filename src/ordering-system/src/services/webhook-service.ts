/**
 * Webhook Service
 * Handles Razorpay webhooks with signature verification and idempotent processing
 * Implements Requirements 4.2, 4.3, 4.4, 4.5
 */

import crypto from 'crypto';
import { v4 as uuidv4 } from 'uuid';
import { WebhookPayload, Payment } from '../types/entities';
import { PaymentCompleted, PaymentFailed, CODConversionCompleted } from '../types/events';
import { EventTypes } from '../types/events';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';

export interface WebhookProcessingResult {
  success: boolean;
  message: string;
  eventId?: string;
  processed: boolean;
  duplicate: boolean;
}

/**
 * Webhook Service Implementation
 */
export class WebhookService {
  private logger: Logger;
  private webhookSecret: string;
  private processedWebhooks: Set<string> = new Set(); // In-memory deduplication

  constructor() {
    this.logger = new Logger('WebhookService');
    this.webhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET || 'dummy_webhook_secret';
    
    this.logger.info('Webhook service initialized');
  }

  /**
   * Process incoming webhook with signature verification and idempotent handling
   * Implements Requirements 4.2, 4.3, 4.4, 4.5
   */
  async processWebhook(
    payload: string,
    signature: string,
    headers: Record<string, string>
  ): Promise<WebhookProcessingResult> {
    const webhookId = headers['x-razorpay-event-id'] || uuidv4();
    
    this.logger.info('Processing webhook', {
      webhookId,
      event: this.extractEventType(payload),
      signature: this.maskSignature(signature)
    });

    try {
      // Step 1: Verify webhook signature (Requirement 4.2, 4.3)
      const isValidSignature = this.verifyWebhookSignature(payload, signature);
      
      if (!isValidSignature) {
        this.logger.security('Invalid webhook signature detected', 'high', {
          webhookId,
          signature: this.maskSignature(signature),
          sourceIP: headers['x-forwarded-for'] || 'unknown'
        });

        return {
          success: false,
          message: 'Invalid webhook signature',
          processed: false,
          duplicate: false
        };
      }

      // Step 2: Check for duplicate webhook (Requirement 4.5 - Idempotent processing)
      if (this.processedWebhooks.has(webhookId)) {
        this.logger.info('Duplicate webhook detected', { webhookId });
        
        return {
          success: true,
          message: 'Webhook already processed',
          eventId: webhookId,
          processed: true,
          duplicate: true
        };
      }

      // Step 3: Parse and validate webhook payload
      const webhookData = this.parseWebhookPayload(payload);
      
      // Step 4: Process webhook based on event type
      const result = await this.handleWebhookEvent(webhookData, webhookId);

      // Step 5: Mark webhook as processed (Requirement 4.5)
      this.processedWebhooks.add(webhookId);

      this.logger.info('Webhook processed successfully', {
        webhookId,
        event: webhookData.event,
        result: result.success
      });

      return {
        success: result.success,
        message: result.message,
        eventId: webhookId,
        processed: true,
        duplicate: false
      };

    } catch (error) {
      this.logger.error('Webhook processing failed', error, {
        webhookId,
        signature: this.maskSignature(signature)
      });

      return {
        success: false,
        message: error instanceof Error ? error.message : 'Webhook processing failed',
        eventId: webhookId,
        processed: false,
        duplicate: false
      };
    }
  }

  /**
   * Verify webhook signature against Razorpay's public key
   * Implements Requirements 4.2, 4.3
   */
  private verifyWebhookSignature(payload: string, signature: string): boolean {
    try {
      const expectedSignature = crypto
        .createHmac('sha256', this.webhookSecret)
        .update(payload)
        .digest('hex');

      // Use timingSafeEqual to prevent timing attacks
      const receivedSignature = Buffer.from(signature, 'hex');
      const computedSignature = Buffer.from(expectedSignature, 'hex');

      if (receivedSignature.length !== computedSignature.length) {
        return false;
      }

      return crypto.timingSafeEqual(receivedSignature, computedSignature);
    } catch (error) {
      this.logger.error('Signature verification error', error);
      return false;
    }
  }

  /**
   * Parse webhook payload and validate structure
   */
  private parseWebhookPayload(payload: string): WebhookPayload {
    try {
      const data = JSON.parse(payload);
      
      // Validate required fields
      if (!data.event || !data.payload) {
        throw new Error('Invalid webhook payload structure');
      }

      return data as WebhookPayload;
    } catch (error) {
      throw new Error(`Failed to parse webhook payload: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle different webhook event types
   */
  private async handleWebhookEvent(
    webhookData: WebhookPayload,
    webhookId: string
  ): Promise<{ success: boolean; message: string }> {
    
    switch (webhookData.event) {
      case 'payment.captured':
        return await this.handlePaymentCaptured(webhookData, webhookId);
      
      case 'payment.failed':
        return await this.handlePaymentFailed(webhookData, webhookId);
      
      case 'order.paid':
        return await this.handleOrderPaid(webhookData, webhookId);
      
      default:
        this.logger.info('Unhandled webhook event type', {
          event: webhookData.event,
          webhookId
        });
        
        return {
          success: true,
          message: `Event type ${webhookData.event} acknowledged but not processed`
        };
    }
  }

  /**
   * Handle payment captured webhook
   */
  private async handlePaymentCaptured(
    webhookData: WebhookPayload,
    webhookId: string
  ): Promise<{ success: boolean; message: string }> {
    
    const payment = webhookData.payload.payment.entity;
    
    this.logger.info('Processing payment captured webhook', {
      paymentId: payment.id,
      orderId: payment.order_id,
      amount: payment.amount,
      webhookId
    });

    try {
      // Find payment in database
      const dbPayment = database.findWhere<Payment>('payments', 
        p => p.razorpayOrderId === payment.order_id
      )[0];

      if (!dbPayment) {
        throw new Error(`Payment not found for Razorpay order: ${payment.order_id}`);
      }

      // Update payment status (Requirement 4.4)
      const updatedPayment = database.update<Payment>('payments', dbPayment.id, {
        status: 'PAID',
        razorpayPaymentId: payment.id,
        paidAt: new Date()
      });

      if (!updatedPayment) {
        throw new Error('Failed to update payment status');
      }

      // Determine if this is a COD conversion
      const isCODConversion = payment.notes?.convertedFromCOD === 'true';

      if (isCODConversion) {
        // Handle COD conversion completion
        const codConversionEvent: CODConversionCompleted = {
          orderId: dbPayment.orderId,
          razorpayPaymentId: payment.id,
          amount: payment.amount / 100, // Convert from paise
          convertedAt: new Date()
        };

        await eventBus.publish(
          dbPayment.orderId,
          'Payment',
          EventTypes.COD_CONVERSION_COMPLETED,
          codConversionEvent
        );

        this.logger.business('COD conversion completed via webhook', {
          orderId: dbPayment.orderId,
          paymentId: payment.id,
          amount: payment.amount / 100
        });
      } else {
        // Handle regular payment completion
        const paymentCompletedEvent: PaymentCompleted = {
          orderId: dbPayment.orderId,
          paymentId: dbPayment.id,
          razorpayPaymentId: payment.id,
          amount: payment.amount / 100, // Convert from paise
          method: 'ONLINE',
          completedAt: new Date()
        };

        await eventBus.publish(
          dbPayment.orderId,
          'Payment',
          EventTypes.PAYMENT_COMPLETED,
          paymentCompletedEvent
        );

        this.logger.business('Payment completed via webhook', {
          orderId: dbPayment.orderId,
          paymentId: payment.id,
          amount: payment.amount / 100
        });
      }

      return {
        success: true,
        message: 'Payment captured successfully'
      };

    } catch (error) {
      this.logger.error('Failed to process payment captured webhook', error, {
        paymentId: payment.id,
        orderId: payment.order_id,
        webhookId
      });

      throw error;
    }
  }

  /**
   * Handle payment failed webhook
   */
  private async handlePaymentFailed(
    webhookData: WebhookPayload,
    webhookId: string
  ): Promise<{ success: boolean; message: string }> {
    
    const payment = webhookData.payload.payment.entity;
    
    this.logger.info('Processing payment failed webhook', {
      paymentId: payment.id,
      orderId: payment.order_id,
      errorCode: payment.error_code,
      errorDescription: payment.error_description,
      webhookId
    });

    try {
      // Find payment in database
      const dbPayment = database.findWhere<Payment>('payments', 
        p => p.razorpayOrderId === payment.order_id
      )[0];

      if (!dbPayment) {
        throw new Error(`Payment not found for Razorpay order: ${payment.order_id}`);
      }

      // Update payment status
      const updatedPayment = database.update<Payment>('payments', dbPayment.id, {
        status: 'FAILED',
        razorpayPaymentId: payment.id,
        failedAt: new Date(),
        failureReason: payment.error_description || payment.error_code || 'Payment failed'
      });

      if (!updatedPayment) {
        throw new Error('Failed to update payment status');
      }

      // Create payment failed event
      const paymentFailedEvent: PaymentFailed = {
        orderId: dbPayment.orderId,
        paymentId: dbPayment.id,
        razorpayPaymentId: payment.id,
        reason: payment.error_description || payment.error_code || 'Payment failed',
        failedAt: new Date()
      };

      await eventBus.publish(
        dbPayment.orderId,
        'Payment',
        EventTypes.PAYMENT_FAILED,
        paymentFailedEvent
      );

      this.logger.business('Payment failed via webhook', {
        orderId: dbPayment.orderId,
        paymentId: payment.id,
        reason: payment.error_description || payment.error_code
      });

      return {
        success: true,
        message: 'Payment failure processed successfully'
      };

    } catch (error) {
      this.logger.error('Failed to process payment failed webhook', error, {
        paymentId: payment.id,
        orderId: payment.order_id,
        webhookId
      });

      throw error;
    }
  }

  /**
   * Handle order paid webhook
   */
  private async handleOrderPaid(
    webhookData: WebhookPayload,
    webhookId: string
  ): Promise<{ success: boolean; message: string }> {
    
    // This is typically fired after payment.captured for orders
    // We can use this for additional validation or business logic
    
    this.logger.info('Order paid webhook received', {
      orderId: webhookData.payload.order?.entity.id,
      webhookId
    });

    return {
      success: true,
      message: 'Order paid webhook acknowledged'
    };
  }

  /**
   * Extract event type from payload for logging
   */
  private extractEventType(payload: string): string {
    try {
      const data = JSON.parse(payload);
      return data.event || 'unknown';
    } catch {
      return 'unknown';
    }
  }

  /**
   * Mask signature for secure logging
   */
  private maskSignature(signature: string): string {
    if (signature.length <= 8) {
      return '*'.repeat(signature.length);
    }
    return signature.substring(0, 4) + '*'.repeat(signature.length - 8) + signature.substring(signature.length - 4);
  }

  /**
   * Get webhook processing statistics
   */
  getWebhookStatistics(): {
    totalProcessed: number;
    duplicatesDetected: number;
    processingErrors: number;
  } {
    return {
      totalProcessed: this.processedWebhooks.size,
      duplicatesDetected: 0, // Would be tracked in production
      processingErrors: 0    // Would be tracked in production
    };
  }

  /**
   * Clear processed webhooks cache (for testing)
   */
  clearProcessedWebhooks(): void {
    this.processedWebhooks.clear();
    this.logger.info('Processed webhooks cache cleared');
  }
}

// Export singleton instance
export const webhookService = new WebhookService();