/**
 * Delivery Provider Service
 * Handles integration with external delivery providers while maintaining service boundaries
 * Implements Requirements 2.6 - External service boundary enforcement
 */

import { deliveryService, UpdateDeliveryStatusRequest } from './delivery-service';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';

export interface DeliveryProviderEvent {
  trackingNumber: string;
  status: string;
  location?: string;
  timestamp: Date;
  providerName: string;
  providerEventId: string;
}

export interface DeliveryProviderConfig {
  name: string;
  apiEndpoint?: string;
  apiKey?: string;
  webhookSecret?: string;
  statusMapping: Record<string, string>;
}

/**
 * Delivery Provider Service
 * Acts as a boundary between external delivery providers and internal delivery service
 */
export class DeliveryProviderService {
  private logger: Logger;
  private providers: Map<string, DeliveryProviderConfig> = new Map();
  private processedEvents: Set<string> = new Set(); // Idempotency tracking

  constructor() {
    this.logger = new Logger('DeliveryProviderService');
    this.initializeProviders();
    this.setupEventHandlers();
  }

  /**
   * Initialize supported delivery providers
   */
  private initializeProviders(): void {
    // Standard Delivery Provider
    this.providers.set('standard', {
      name: 'Standard Delivery',
      statusMapping: {
        'PICKED_UP': 'SHIPPED',
        'IN_TRANSIT': 'SHIPPED',
        'OUT_FOR_DELIVERY': 'OUT_FOR_DELIVERY',
        'DELIVERED': 'DELIVERED',
        'CANCELLED': 'CANCELLED',
        'RETURNED': 'CANCELLED'
      }
    });

    // Express Delivery Provider
    this.providers.set('express', {
      name: 'Express Delivery',
      statusMapping: {
        'COLLECTED': 'SHIPPED',
        'SORTING': 'SHIPPED',
        'ON_ROUTE': 'OUT_FOR_DELIVERY',
        'DELIVERED': 'DELIVERED',
        'FAILED_DELIVERY': 'OUT_FOR_DELIVERY',
        'CANCELLED': 'CANCELLED'
      }
    });

    this.logger.info('Delivery providers initialized', {
      providers: Array.from(this.providers.keys())
    });
  }

  /**
   * Setup event handlers for cross-service coordination
   */
  private setupEventHandlers(): void {
    // Listen for shipment created events to register with providers
    eventBus.subscribe('SHIPMENT_CREATED', async (event) => {
      await this.handleShipmentCreated(event);
    });

    this.logger.info('Delivery provider event handlers registered');
  }

  /**
   * Handle shipment created event
   */
  private async handleShipmentCreated(event: any): Promise<void> {
    try {
      this.logger.info('Registering shipment with delivery provider', {
        orderId: event.orderId,
        trackingNumber: event.trackingNumber,
        carrier: event.carrier
      });

      // In a real system, this would register the shipment with the actual provider
      // For now, we'll simulate the registration
      await this.simulateProviderRegistration(event);

    } catch (error) {
      this.logger.error('Failed to register shipment with provider', error, {
        orderId: event.orderId,
        trackingNumber: event.trackingNumber
      });
    }
  }

  /**
   * Process delivery provider webhook/event
   * Implements Requirements 2.6 - Ensures delivery events don't directly modify order/payment states
   */
  async processProviderEvent(providerEvent: DeliveryProviderEvent): Promise<{
    success: boolean;
    message: string;
    processed: boolean;
  }> {
    this.logger.info('Processing delivery provider event', {
      trackingNumber: providerEvent.trackingNumber,
      status: providerEvent.status,
      provider: providerEvent.providerName,
      eventId: providerEvent.providerEventId
    });

    try {
      // Check for duplicate events (idempotency)
      if (this.processedEvents.has(providerEvent.providerEventId)) {
        this.logger.info('Duplicate provider event detected', {
          eventId: providerEvent.providerEventId
        });
        
        return {
          success: true,
          message: 'Event already processed',
          processed: true
        };
      }

      // Validate provider
      const provider = this.providers.get(providerEvent.providerName.toLowerCase());
      if (!provider) {
        throw new Error(`Unknown delivery provider: ${providerEvent.providerName}`);
      }

      // Map provider status to internal status
      const internalStatus = this.mapProviderStatus(providerEvent.status, provider);
      if (!internalStatus) {
        this.logger.warn('Unknown provider status', {
          providerStatus: providerEvent.status,
          provider: providerEvent.providerName
        });
        
        return {
          success: true,
          message: 'Status not mapped, event acknowledged',
          processed: true
        };
      }

      // Find delivery by tracking number
      const delivery = await this.findDeliveryByTrackingNumber(providerEvent.trackingNumber);
      if (!delivery) {
        throw new Error(`No delivery found for tracking number: ${providerEvent.trackingNumber}`);
      }

      // CRITICAL: Ensure external events don't directly modify order/payment states
      // Only update delivery state through proper service boundaries
      await this.updateDeliveryStatusSafely(delivery.shipmentId, internalStatus, providerEvent);

      // Mark event as processed
      this.processedEvents.add(providerEvent.providerEventId);

      // Emit internal domain event (not directly modifying other service states)
      await eventBus.publish(
        delivery.orderId,
        'Delivery',
        'DELIVERY_PROVIDER_EVENT_PROCESSED',
        {
          orderId: delivery.orderId,
          shipmentId: delivery.shipmentId,
          trackingNumber: providerEvent.trackingNumber,
          providerName: providerEvent.providerName,
          providerStatus: providerEvent.status,
          internalStatus,
          processedAt: new Date()
        }
      );

      this.logger.business('Delivery provider event processed', {
        orderId: delivery.orderId,
        trackingNumber: providerEvent.trackingNumber,
        providerStatus: providerEvent.status,
        internalStatus,
        provider: providerEvent.providerName
      });

      return {
        success: true,
        message: 'Event processed successfully',
        processed: true
      };

    } catch (error) {
      this.logger.error('Failed to process delivery provider event', error, {
        trackingNumber: providerEvent.trackingNumber,
        provider: providerEvent.providerName,
        eventId: providerEvent.providerEventId
      });

      return {
        success: false,
        message: error instanceof Error ? error.message : 'Processing failed',
        processed: false
      };
    }
  }

  /**
   * Simulate provider registration (would be actual API call in production)
   */
  private async simulateProviderRegistration(shipmentEvent: any): Promise<void> {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 100));

    this.logger.info('Shipment registered with provider', {
      trackingNumber: shipmentEvent.trackingNumber,
      carrier: shipmentEvent.carrier,
      orderId: shipmentEvent.orderId
    });

    // Simulate initial status update from provider
    setTimeout(async () => {
      const providerEvent: DeliveryProviderEvent = {
        trackingNumber: shipmentEvent.trackingNumber,
        status: 'PICKED_UP',
        location: 'Warehouse',
        timestamp: new Date(),
        providerName: 'standard',
        providerEventId: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };

      await this.processProviderEvent(providerEvent);
    }, 2000); // Simulate 2 second delay
  }

  /**
   * Map provider-specific status to internal delivery status
   */
  private mapProviderStatus(providerStatus: string, provider: DeliveryProviderConfig): string | null {
    return provider.statusMapping[providerStatus.toUpperCase()] || null;
  }

  /**
   * Find delivery by tracking number
   */
  private async findDeliveryByTrackingNumber(trackingNumber: string): Promise<any> {
    // This would query the database for delivery by tracking number
    // For now, we'll use the delivery service to get all deliveries and find the match
    const allDeliveries = await deliveryService.getAllDeliveries();
    return allDeliveries.find(d => d.trackingNumber === trackingNumber);
  }

  /**
   * Update delivery status safely through proper service boundaries
   * Implements Requirements 2.6 - Service boundary enforcement
   */
  private async updateDeliveryStatusSafely(
    shipmentId: string,
    status: string,
    providerEvent: DeliveryProviderEvent
  ): Promise<void> {
    try {
      // Use the delivery service to update status (proper service boundary)
      const updateRequest: UpdateDeliveryStatusRequest = {
        shipmentId,
        status: status as any,
        location: providerEvent.location,
        notes: `Updated by ${providerEvent.providerName} provider`
      };

      await deliveryService.updateDeliveryStatus(updateRequest);

      this.logger.info('Delivery status updated through service boundary', {
        shipmentId,
        status,
        provider: providerEvent.providerName
      });

    } catch (error) {
      // If status update fails (e.g., invalid transition), log but don't fail the entire process
      this.logger.warn('Failed to update delivery status from provider event', error, {
        shipmentId,
        status,
        provider: providerEvent.providerName,
        reason: error instanceof Error ? error.message : 'Unknown error'
      });

      // Still emit an event for monitoring/alerting
      await eventBus.publish(
        'system',
        'Delivery',
        'DELIVERY_STATUS_UPDATE_FAILED',
        {
          shipmentId,
          requestedStatus: status,
          provider: providerEvent.providerName,
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date()
        }
      );
    }
  }

  /**
   * Get provider statistics
   */
  getProviderStatistics(): {
    totalProviders: number;
    processedEvents: number;
    providers: string[];
  } {
    return {
      totalProviders: this.providers.size,
      processedEvents: this.processedEvents.size,
      providers: Array.from(this.providers.keys())
    };
  }

  /**
   * Simulate delivery provider webhook endpoint
   * This would be called by external delivery providers
   */
  async handleProviderWebhook(
    providerName: string,
    webhookPayload: any,
    signature?: string
  ): Promise<{ success: boolean; message: string }> {
    try {
      // In production, verify webhook signature here
      if (signature) {
        // Verify signature against provider's webhook secret
        this.logger.info('Webhook signature verification would happen here', {
          provider: providerName,
          hasSignature: !!signature
        });
      }

      // Parse webhook payload into standard format
      const providerEvent = this.parseWebhookPayload(providerName, webhookPayload);
      
      // Process the event
      const result = await this.processProviderEvent(providerEvent);
      
      return {
        success: result.success,
        message: result.message
      };

    } catch (error) {
      this.logger.error('Webhook processing failed', error, {
        provider: providerName
      });

      return {
        success: false,
        message: error instanceof Error ? error.message : 'Webhook processing failed'
      };
    }
  }

  /**
   * Parse webhook payload from different providers into standard format
   */
  private parseWebhookPayload(providerName: string, payload: any): DeliveryProviderEvent {
    // This would contain provider-specific parsing logic
    // For now, assume a standard format
    return {
      trackingNumber: payload.tracking_number || payload.trackingNumber,
      status: payload.status || payload.delivery_status,
      location: payload.location || payload.current_location,
      timestamp: new Date(payload.timestamp || payload.updated_at || Date.now()),
      providerName,
      providerEventId: payload.event_id || payload.id || `${providerName}_${Date.now()}`
    };
  }

  /**
   * Clear processed events cache (for testing)
   */
  clearProcessedEvents(): void {
    this.processedEvents.clear();
    this.logger.info('Processed events cache cleared');
  }
}

// Export singleton instance
export const deliveryProviderService = new DeliveryProviderService();