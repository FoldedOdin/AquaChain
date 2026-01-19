/**
 * Error Handling Service
 * Provides comprehensive error handling with exponential backoff and circuit breaker patterns
 * Implements Requirements 9.4, 9.5 - External service resilience and error handling
 */

import { Logger } from '../infrastructure/logger';
import { eventBus } from '../infrastructure/event-bus';

export interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
  jitterMs?: number;
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeoutMs: number;
  monitoringWindowMs: number;
}

export interface ErrorContext {
  operation: string;
  service: string;
  correlationId?: string;
  metadata?: Record<string, any>;
}

export type CircuitBreakerState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

/**
 * Circuit Breaker Implementation
 * Prevents cascading failures by monitoring service health
 */
export class CircuitBreaker {
  private state: CircuitBreakerState = 'CLOSED';
  private failureCount = 0;
  private lastFailureTime = 0;
  private successCount = 0;
  private logger: Logger;

  constructor(
    private name: string,
    private config: CircuitBreakerConfig
  ) {
    this.logger = new Logger(`CircuitBreaker-${name}`);
  }

  /**
   * Execute operation with circuit breaker protection
   */
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime < this.config.resetTimeoutMs) {
        throw new Error(`Circuit breaker is OPEN for ${this.name}`);
      } else {
        this.state = 'HALF_OPEN';
        this.successCount = 0;
        this.logger.info(`Circuit breaker transitioning to HALF_OPEN`, { service: this.name });
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= 3) { // Require 3 successes to close
        this.state = 'CLOSED';
        this.logger.info(`Circuit breaker CLOSED`, { service: this.name });
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = 'OPEN';
      this.logger.warn(`Circuit breaker OPENED`, { 
        service: this.name, 
        failureCount: this.failureCount 
      });
    }
  }

  getState(): CircuitBreakerState {
    return this.state;
  }

  getStats(): {
    state: CircuitBreakerState;
    failureCount: number;
    successCount: number;
    lastFailureTime: number;
  } {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime
    };
  }
}

/**
 * Error Handling Service
 * Provides retry logic, circuit breakers, and error recovery mechanisms
 */
export class ErrorHandlingService {
  private logger: Logger;
  private circuitBreakers: Map<string, CircuitBreaker> = new Map();
  private defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelayMs: 1000,
    maxDelayMs: 30000,
    backoffMultiplier: 2,
    jitterMs: 100
  };

  constructor() {
    this.logger = new Logger('ErrorHandlingService');
    this.initializeCircuitBreakers();
  }

  /**
   * Initialize circuit breakers for external services
   */
  private initializeCircuitBreakers(): void {
    // Razorpay circuit breaker
    this.circuitBreakers.set('razorpay', new CircuitBreaker('razorpay', {
      failureThreshold: 5,
      resetTimeoutMs: 60000, // 1 minute
      monitoringWindowMs: 300000 // 5 minutes
    }));

    // Delivery provider circuit breaker
    this.circuitBreakers.set('delivery', new CircuitBreaker('delivery', {
      failureThreshold: 3,
      resetTimeoutMs: 30000, // 30 seconds
      monitoringWindowMs: 180000 // 3 minutes
    }));

    // Database circuit breaker
    this.circuitBreakers.set('database', new CircuitBreaker('database', {
      failureThreshold: 10,
      resetTimeoutMs: 10000, // 10 seconds
      monitoringWindowMs: 60000 // 1 minute
    }));

    this.logger.info('Circuit breakers initialized', {
      services: Array.from(this.circuitBreakers.keys())
    });
  }

  /**
   * Execute operation with retry logic and exponential backoff
   * Implements Requirements 9.5 - Exponential backoff for external service failures
   */
  async executeWithRetry<T>(
    operation: () => Promise<T>,
    context: ErrorContext,
    retryConfig?: Partial<RetryConfig>
  ): Promise<T> {
    const config = { ...this.defaultRetryConfig, ...retryConfig };
    let lastError: Error;
    
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const result = await operation();
        
        if (attempt > 0) {
          this.logger.info('Operation succeeded after retry', {
            ...context,
            attempt,
            totalAttempts: attempt + 1
          });
        }
        
        return result;
      } catch (error) {
        lastError = error as Error;
        
        this.logger.warn('Operation failed', {
          ...context,
          attempt: attempt + 1,
          maxAttempts: config.maxRetries + 1,
          error: lastError.message
        });

        // Don't retry on the last attempt
        if (attempt === config.maxRetries) {
          break;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = this.calculateRetryDelay(attempt, config);
        
        this.logger.info('Retrying operation', {
          ...context,
          nextAttempt: attempt + 2,
          delayMs: delay
        });

        await this.sleep(delay);
      }
    }

    // All retries exhausted
    this.logger.error('Operation failed after all retries', {
      ...context,
      totalAttempts: config.maxRetries + 1,
      finalError: lastError!.message
    });

    // Emit failure event for monitoring
    await this.emitFailureEvent(context, lastError!, config.maxRetries + 1);

    throw lastError!;
  }

  /**
   * Execute operation with circuit breaker protection
   */
  async executeWithCircuitBreaker<T>(
    operation: () => Promise<T>,
    serviceName: string,
    context: ErrorContext
  ): Promise<T> {
    const circuitBreaker = this.circuitBreakers.get(serviceName);
    
    if (!circuitBreaker) {
      this.logger.warn('No circuit breaker found for service', { 
        service: serviceName,
        ...context 
      });
      return await operation();
    }

    try {
      return await circuitBreaker.execute(operation);
    } catch (error) {
      this.logger.error('Circuit breaker protected operation failed', {
        service: serviceName,
        circuitState: circuitBreaker.getState(),
        ...context,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Execute operation with both retry and circuit breaker protection
   */
  async executeWithFullProtection<T>(
    operation: () => Promise<T>,
    serviceName: string,
    context: ErrorContext,
    retryConfig?: Partial<RetryConfig>
  ): Promise<T> {
    return await this.executeWithRetry(
      () => this.executeWithCircuitBreaker(operation, serviceName, context),
      context,
      retryConfig
    );
  }

  /**
   * Handle Razorpay API errors with specific retry logic
   */
  async handleRazorpayOperation<T>(
    operation: () => Promise<T>,
    context: ErrorContext
  ): Promise<T> {
    const razorpayRetryConfig: Partial<RetryConfig> = {
      maxRetries: 3,
      baseDelayMs: 2000,
      maxDelayMs: 10000,
      backoffMultiplier: 2
    };

    return await this.executeWithFullProtection(
      operation,
      'razorpay',
      { ...context, service: 'razorpay' },
      razorpayRetryConfig
    );
  }

  /**
   * Handle delivery provider errors with specific retry logic
   */
  async handleDeliveryOperation<T>(
    operation: () => Promise<T>,
    context: ErrorContext
  ): Promise<T> {
    const deliveryRetryConfig: Partial<RetryConfig> = {
      maxRetries: 2,
      baseDelayMs: 1000,
      maxDelayMs: 5000,
      backoffMultiplier: 1.5
    };

    return await this.executeWithFullProtection(
      operation,
      'delivery',
      { ...context, service: 'delivery' },
      deliveryRetryConfig
    );
  }

  /**
   * Handle database operations with retry logic
   */
  async handleDatabaseOperation<T>(
    operation: () => Promise<T>,
    context: ErrorContext
  ): Promise<T> {
    const dbRetryConfig: Partial<RetryConfig> = {
      maxRetries: 5,
      baseDelayMs: 500,
      maxDelayMs: 5000,
      backoffMultiplier: 1.5
    };

    return await this.executeWithFullProtection(
      operation,
      'database',
      { ...context, service: 'database' },
      dbRetryConfig
    );
  }

  /**
   * Create user-friendly error response
   * Implements Requirements 9.5 - Surface non-blocking errors to users
   */
  createUserFriendlyError(
    error: Error,
    context: ErrorContext,
    isRetryable: boolean = true
  ): {
    code: string;
    message: string;
    userMessage: string;
    retryable: boolean;
    timestamp: Date;
    correlationId?: string;
  } {
    let userMessage: string;
    let code: string;

    // Map technical errors to user-friendly messages
    if (error.message.includes('timeout')) {
      code = 'SERVICE_TIMEOUT';
      userMessage = 'The service is temporarily slow. Please try again in a moment.';
    } else if (error.message.includes('network') || error.message.includes('connection')) {
      code = 'NETWORK_ERROR';
      userMessage = 'Network connection issue. Please check your connection and try again.';
    } else if (error.message.includes('rate limit')) {
      code = 'RATE_LIMITED';
      userMessage = 'Too many requests. Please wait a moment before trying again.';
    } else if (error.message.includes('Circuit breaker is OPEN')) {
      code = 'SERVICE_UNAVAILABLE';
      userMessage = 'This service is temporarily unavailable. We\'re working to restore it.';
      isRetryable = false;
    } else if (context.service === 'razorpay') {
      code = 'PAYMENT_SERVICE_ERROR';
      userMessage = 'Payment service is temporarily unavailable. Please try again later.';
    } else if (context.service === 'delivery') {
      code = 'DELIVERY_SERVICE_ERROR';
      userMessage = 'Delivery tracking is temporarily unavailable. Please try again later.';
    } else {
      code = 'GENERAL_ERROR';
      userMessage = 'Something went wrong. Please try again or contact support if the issue persists.';
    }

    return {
      code,
      message: error.message,
      userMessage,
      retryable: isRetryable,
      timestamp: new Date(),
      correlationId: context.correlationId
    };
  }

  /**
   * Calculate retry delay with exponential backoff and jitter
   */
  private calculateRetryDelay(attempt: number, config: RetryConfig): number {
    const exponentialDelay = config.baseDelayMs * Math.pow(config.backoffMultiplier, attempt);
    const jitter = config.jitterMs ? Math.random() * config.jitterMs : 0;
    const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);
    
    return Math.floor(delay);
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Emit failure event for monitoring and alerting
   */
  private async emitFailureEvent(
    context: ErrorContext,
    error: Error,
    totalAttempts: number
  ): Promise<void> {
    try {
      await eventBus.publish(
        'system',
        'Order',
        'OPERATION_FAILED_AFTER_RETRIES',
        {
          operation: context.operation,
          service: context.service,
          error: error.message,
          totalAttempts,
          timestamp: new Date(),
          correlationId: context.correlationId,
          metadata: context.metadata
        }
      );
    } catch (eventError) {
      this.logger.error('Failed to emit failure event', eventError);
    }
  }

  /**
   * Get circuit breaker statistics
   */
  getCircuitBreakerStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    
    for (const [name, breaker] of this.circuitBreakers.entries()) {
      stats[name] = breaker.getStats();
    }
    
    return stats;
  }

  /**
   * Get error handling statistics
   */
  getErrorHandlingStats(): {
    circuitBreakers: Record<string, any>;
    activeBreakers: number;
    openBreakers: number;
  } {
    const circuitBreakerStats = this.getCircuitBreakerStats();
    
    return {
      circuitBreakers: circuitBreakerStats,
      activeBreakers: this.circuitBreakers.size,
      openBreakers: Object.values(circuitBreakerStats).filter(
        (stats: any) => stats.state === 'OPEN'
      ).length
    };
  }

  /**
   * Reset circuit breaker for a service (admin operation)
   */
  resetCircuitBreaker(serviceName: string): boolean {
    const breaker = this.circuitBreakers.get(serviceName);
    if (breaker) {
      // Create new circuit breaker to reset state
      const config = {
        failureThreshold: 5,
        resetTimeoutMs: 60000,
        monitoringWindowMs: 300000
      };
      
      this.circuitBreakers.set(serviceName, new CircuitBreaker(serviceName, config));
      
      this.logger.info('Circuit breaker reset', { service: serviceName });
      return true;
    }
    
    return false;
  }
}

// Export singleton instance
export const errorHandlingService = new ErrorHandlingService();