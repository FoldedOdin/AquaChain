/**
 * Event Bus Infrastructure
 * Provides event-driven communication between services with at-least-once delivery guarantees
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { DomainEvent, OrderingEvent } from '../types/events';
import { Logger } from './logger';

export type EventHandler<T = any> = (event: T) => Promise<void> | void;

export interface EventBusConfig {
  maxRetries: number;
  retryDelayMs: number;
  maxConcurrentHandlers: number;
  enablePersistence: boolean;
}

export class EventBus extends EventEmitter {
  private handlers: Map<string, EventHandler[]> = new Map();
  private eventStore: DomainEvent[] = [];
  private processingQueue: Map<string, DomainEvent> = new Map();
  private retryCount: Map<string, number> = new Map();
  private logger: Logger;
  private config: EventBusConfig;

  constructor(config: Partial<EventBusConfig> = {}) {
    super();
    this.config = {
      maxRetries: 3,
      retryDelayMs: 1000,
      maxConcurrentHandlers: 10,
      enablePersistence: true,
      ...config
    };
    this.logger = new Logger('EventBus');
    this.setMaxListeners(100); // Increase max listeners for high-throughput scenarios
  }

  /**
   * Subscribe to events of a specific type
   */
  subscribe<T extends OrderingEvent>(
    eventType: string,
    handler: EventHandler<T>
  ): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    
    this.handlers.get(eventType)!.push(handler as EventHandler);
    this.logger.info(`Handler subscribed to event type: ${eventType}`);
  }

  /**
   * Unsubscribe from events of a specific type
   */
  unsubscribe(eventType: string, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
        this.logger.info(`Handler unsubscribed from event type: ${eventType}`);
      }
    }
  }

  /**
   * Publish an event to all subscribers
   */
  async publish(
    aggregateId: string,
    aggregateType: DomainEvent['aggregateType'],
    eventType: string,
    eventData: OrderingEvent,
    correlationId?: string
  ): Promise<void> {
    const domainEvent: DomainEvent = {
      id: uuidv4(),
      aggregateId,
      aggregateType,
      eventType,
      eventData,
      version: 1,
      timestamp: new Date(),
      correlationId: correlationId || uuidv4()
    };

    // Store event for persistence and replay
    if (this.config.enablePersistence) {
      this.eventStore.push(domainEvent);
    }

    this.logger.info(`Publishing event: ${eventType} for aggregate: ${aggregateId}`, {
      eventId: domainEvent.id,
      correlationId: domainEvent.correlationId
    });

    // Add to processing queue
    this.processingQueue.set(domainEvent.id, domainEvent);

    try {
      await this.processEvent(domainEvent);
    } catch (error) {
      this.logger.error(`Failed to process event: ${domainEvent.id}`, error);
      await this.handleEventFailure(domainEvent, error as Error);
    }
  }

  /**
   * Process a single event by calling all registered handlers
   */
  private async processEvent(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];
    
    if (handlers.length === 0) {
      this.logger.warn(`No handlers registered for event type: ${event.eventType}`);
      this.processingQueue.delete(event.id);
      return;
    }

    // Process handlers concurrently with limit
    const handlerPromises = handlers.map(async (handler, index) => {
      try {
        await this.executeHandler(handler, event, index);
      } catch (error) {
        this.logger.error(`Handler ${index} failed for event ${event.id}`, error);
        throw error;
      }
    });

    // Wait for all handlers to complete
    await Promise.all(handlerPromises);
    
    // Remove from processing queue on success
    this.processingQueue.delete(event.id);
    this.retryCount.delete(event.id);
    
    this.logger.info(`Event processed successfully: ${event.id}`);
  }

  /**
   * Execute a single event handler with timeout protection
   */
  private async executeHandler(
    handler: EventHandler,
    event: DomainEvent,
    handlerIndex: number
  ): Promise<void> {
    const timeoutMs = 30000; // 30 second timeout
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Handler ${handlerIndex} timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      Promise.resolve(handler(event.eventData))
        .then(() => {
          clearTimeout(timeout);
          resolve();
        })
        .catch((error) => {
          clearTimeout(timeout);
          reject(error);
        });
    });
  }

  /**
   * Handle event processing failures with retry logic
   */
  private async handleEventFailure(event: DomainEvent, error: Error): Promise<void> {
    const currentRetries = this.retryCount.get(event.id) || 0;
    
    if (currentRetries < this.config.maxRetries) {
      this.retryCount.set(event.id, currentRetries + 1);
      
      const delay = this.config.retryDelayMs * Math.pow(2, currentRetries); // Exponential backoff
      
      this.logger.warn(`Retrying event ${event.id} in ${delay}ms (attempt ${currentRetries + 1}/${this.config.maxRetries})`);
      
      setTimeout(async () => {
        try {
          await this.processEvent(event);
        } catch (retryError) {
          await this.handleEventFailure(event, retryError as Error);
        }
      }, delay);
    } else {
      // Max retries exceeded - move to dead letter queue
      this.logger.error(`Event ${event.id} failed after ${this.config.maxRetries} retries`, error);
      this.processingQueue.delete(event.id);
      this.retryCount.delete(event.id);
      
      // Emit failure event for monitoring
      this.emit('event-failed', {
        event,
        error: error.message,
        retries: currentRetries
      });
    }
  }

  /**
   * Get all events for a specific aggregate
   */
  getEventsForAggregate(aggregateId: string): DomainEvent[] {
    return this.eventStore.filter(event => event.aggregateId === aggregateId);
  }

  /**
   * Get all events of a specific type
   */
  getEventsByType(eventType: string): DomainEvent[] {
    return this.eventStore.filter(event => event.eventType === eventType);
  }

  /**
   * Replay events for a specific aggregate (useful for rebuilding state)
   */
  async replayEventsForAggregate(aggregateId: string): Promise<void> {
    const events = this.getEventsForAggregate(aggregateId);
    
    this.logger.info(`Replaying ${events.length} events for aggregate: ${aggregateId}`);
    
    for (const event of events) {
      await this.processEvent(event);
    }
  }

  /**
   * Get event bus statistics
   */
  getStatistics(): {
    totalEvents: number;
    processingQueueSize: number;
    handlerCount: number;
    eventTypes: string[];
  } {
    return {
      totalEvents: this.eventStore.length,
      processingQueueSize: this.processingQueue.size,
      handlerCount: Array.from(this.handlers.values()).reduce((sum, handlers) => sum + handlers.length, 0),
      eventTypes: Array.from(this.handlers.keys())
    };
  }

  /**
   * Clear event store (for testing purposes)
   */
  clearEventStore(): void {
    this.eventStore = [];
    this.processingQueue.clear();
    this.retryCount.clear();
    this.logger.info('Event store cleared');
  }

  /**
   * Graceful shutdown - wait for all events to process
   */
  async shutdown(): Promise<void> {
    this.logger.info('Shutting down event bus...');
    
    // Wait for processing queue to empty
    const maxWaitMs = 30000; // 30 seconds
    const startTime = Date.now();
    
    while (this.processingQueue.size > 0 && (Date.now() - startTime) < maxWaitMs) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    if (this.processingQueue.size > 0) {
      this.logger.warn(`Event bus shutdown with ${this.processingQueue.size} events still processing`);
    } else {
      this.logger.info('Event bus shutdown complete');
    }
  }
}

// Singleton instance for application-wide use
export const eventBus = new EventBus();