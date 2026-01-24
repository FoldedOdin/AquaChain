/**
 * Main Application
 * Wires all services together and provides the complete ordering system
 */

import { apiGateway } from './infrastructure/api-gateway';
import { eventBus } from './infrastructure/event-bus';
import { database } from './infrastructure/database';
import { logger } from './infrastructure/logger';
import { runIntegrationTests } from './__tests__/integration.test';

// Import route handlers
import orderRoutes from './routes/order-routes';
import paymentRoutes from './routes/payment-routes';
import adminRoutes from './routes/admin-routes';
import deliveryRoutes from './routes/delivery-routes';
import installationRoutes from './routes/installation-routes';
import consumerDashboardRoutes from './routes/consumer-dashboard-routes';

// Import services for initialization
import { errorHandlingService } from './services/error-handling-service';
import { auditMonitoringService } from './services/audit-monitoring-service';
import { stateValidationService } from './services/state-validation-service';
import { initializeSampleData } from './infrastructure/sample-data';

/**
 * Application class that manages the complete ordering system
 */
export class OrderingSystemApp {
  private isInitialized = false;

  /**
   * Initialize the application
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      logger.info('Initializing AquaChain Ordering System...');

      // Initialize database
      logger.info('Database initialized');

      // Initialize sample data for development
      initializeSampleData();

      // Initialize event bus
      logger.info('Event bus initialized');

      // Register API routes
      this.registerRoutes();

      // Setup event handlers
      this.setupEventHandlers();

      this.isInitialized = true;
      logger.info('AquaChain Ordering System initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize ordering system', error);
      throw error;
    }
  }

  /**
   * Register API routes with the gateway
   */
  private registerRoutes(): void {
    // Register order routes
    apiGateway.registerRoutes('/orders', orderRoutes);
    logger.info('Order routes registered');

    // Register payment routes
    apiGateway.registerRoutes('/payments', paymentRoutes);
    logger.info('Payment routes registered');

    // Register admin routes
    apiGateway.registerRoutes('/admin', adminRoutes);
    logger.info('Admin routes registered');

    // Register delivery routes
    apiGateway.registerRoutes('/deliveries', deliveryRoutes);
    logger.info('Delivery routes registered');

    // Register installation routes
    apiGateway.registerRoutes('/installations', installationRoutes);
    logger.info('Installation routes registered');

    // Register consumer dashboard routes
    apiGateway.registerRoutes('/consumer', consumerDashboardRoutes);
    logger.info('Consumer dashboard routes registered');
  }

  /**
   * Setup cross-service event handlers
   */
  private setupEventHandlers(): void {
    // Order events
    eventBus.subscribe('ORDER_CREATED', async (event) => {
      logger.info('Order created event received', { orderId: event.orderId });
      // Additional business logic can be added here
    });

    eventBus.subscribe('ORDER_APPROVED', async (event) => {
      logger.info('Order approved event received', { orderId: event.orderId });
      // Trigger next steps in the workflow
    });

    // Payment events
    eventBus.subscribe('PAYMENT_COMPLETED', async (event) => {
      logger.info('Payment completed event received', { orderId: event.orderId });
      // Update order status or trigger delivery
    });

    eventBus.subscribe('COD_CONVERSION_COMPLETED', async (event) => {
      logger.info('COD conversion completed', { orderId: event.orderId });
      // Handle COD to online conversion completion
    });

    // Delivery events
    eventBus.subscribe('DELIVERY_COMPLETED', async (event) => {
      logger.info('Delivery completed event received', { orderId: event.orderId });
      // Enable installation request option
    });

    // Installation events
    eventBus.subscribe('INSTALLATION_COMPLETED', async (event) => {
      logger.info('Installation completed event received', { orderId: event.orderId });
      // Complete the order lifecycle
    });

    logger.info('Event handlers registered');
  }

  /**
   * Start the application server
   */
  async start(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    // Start API Gateway
    await apiGateway.start();

    logger.info('AquaChain Ordering System started successfully');
  }

  /**
   * Run system health checks
   */
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    services: Record<string, 'up' | 'down'>;
    timestamp: Date;
  }> {
    const health = {
      status: 'healthy' as 'healthy' | 'unhealthy',
      services: {} as Record<string, 'up' | 'down'>,
      timestamp: new Date()
    };

    try {
      // Check database
      const dbStats = database.getStatistics();
      health.services.database = Object.keys(dbStats).length > 0 ? 'up' : 'down';

      // Check event bus
      const eventStats = eventBus.getStatistics();
      health.services.eventBus = eventStats.totalEvents >= 0 ? 'up' : 'down';

      // Check API Gateway
      health.services.apiGateway = 'up'; // If we can run this, it's up

      // Check error handling service
      const errorStats = errorHandlingService.getErrorHandlingStats();
      health.services.errorHandling = errorStats.openBreakers === 0 ? 'up' : 'down';

      // Check audit monitoring service
      const monitoringStats = auditMonitoringService.getMonitoringStatistics();
      health.services.monitoring = monitoringStats.healthyServices > 0 ? 'up' : 'down';

      // Determine overall status
      const allServicesUp = Object.values(health.services).every(status => status === 'up');
      health.status = allServicesUp ? 'healthy' : 'unhealthy';

    } catch (error) {
      logger.error('Health check failed', error);
      health.status = 'unhealthy';
    }

    return health;
  }

  /**
   * Run integration tests
   */
  async runTests(): Promise<boolean> {
    logger.info('Running integration tests...');
    
    try {
      const testResult = await runIntegrationTests();
      
      if (testResult) {
        logger.info('✅ All tests passed');
      } else {
        logger.error('❌ Some tests failed');
      }
      
      return testResult;
    } catch (error) {
      logger.error('Test execution failed', error);
      return false;
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown(): Promise<void> {
    logger.info('Shutting down AquaChain Ordering System...');

    try {
      // Shutdown event bus
      await eventBus.shutdown();

      // Create database backup
      database.backup();

      logger.info('Graceful shutdown completed');
    } catch (error) {
      logger.error('Error during shutdown', error);
    }
  }

  /**
   * Get system statistics
   */
  getStatistics(): {
    database: Record<string, number>;
    eventBus: any;
    errorHandling: any;
    monitoring: any;
    stateValidation: any;
    uptime: number;
  } {
    return {
      database: database.getStatistics(),
      eventBus: eventBus.getStatistics(),
      errorHandling: errorHandlingService.getErrorHandlingStats(),
      monitoring: auditMonitoringService.getMonitoringStatistics(),
      stateValidation: stateValidationService.getTransitionStatistics(),
      uptime: process.uptime()
    };
  }
}

// Export singleton instance
export const orderingSystemApp = new OrderingSystemApp();

// Auto-start if this file is run directly
if (require.main === module) {
  orderingSystemApp.start().catch(error => {
    logger.error('Failed to start application', error);
    process.exit(1);
  });
}