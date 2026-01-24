/**
 * Main Entry Point for AquaChain Ordering System
 * Event-Driven Architecture Implementation
 */

import { orderingSystemApp } from './app';
import { logger } from './infrastructure/logger';

async function startOrderingSystem(): Promise<void> {
  try {
    logger.info('Starting AquaChain Ordering System...');

    // Initialize and start the complete application
    await orderingSystemApp.start();

    // Setup graceful shutdown
    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);

    logger.info('AquaChain Ordering System started successfully');
    
  } catch (error) {
    logger.error('Failed to start ordering system', error);
    process.exit(1);
  }
}

async function gracefulShutdown(): Promise<void> {
  logger.info('Shutting down AquaChain Ordering System...');
  
  try {
    // Shutdown the complete application
    await orderingSystemApp.shutdown();
    
    logger.info('Graceful shutdown completed');
    process.exit(0);
  } catch (error) {
    logger.error('Error during shutdown', error);
    process.exit(1);
  }
}

// Start the system if this file is run directly
if (require.main === module) {
  startOrderingSystem();
}

export { orderingSystemApp };