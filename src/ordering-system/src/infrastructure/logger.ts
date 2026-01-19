/**
 * Logger Infrastructure
 * Provides structured logging with audit trail capabilities
 */

import * as winston from 'winston';
import { v4 as uuidv4 } from 'uuid';

export interface LogContext {
  correlationId?: string;
  userId?: string;
  orderId?: string;
  paymentId?: string;
  [key: string]: any;
}

export class Logger {
  private winston: winston.Logger;
  private context: LogContext;

  constructor(service: string, context: LogContext = {}) {
    this.context = context;
    
    this.winston = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json(),
        winston.format.printf(({ timestamp, level, message, service: svc, ...meta }) => {
          return JSON.stringify({
            timestamp,
            level,
            service: svc || service,
            message,
            context: this.context,
            ...meta
          });
        })
      ),
      defaultMeta: { service },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({ 
          filename: 'logs/error.log', 
          level: 'error' 
        }),
        new winston.transports.File({ 
          filename: 'logs/combined.log' 
        })
      ]
    });

    // Create logs directory if it doesn't exist
    const fs = require('fs');
    if (!fs.existsSync('logs')) {
      fs.mkdirSync('logs');
    }
  }

  /**
   * Create a child logger with additional context
   */
  child(additionalContext: LogContext): Logger {
    const childLogger = new Logger('', { ...this.context, ...additionalContext });
    childLogger.winston = this.winston.child(additionalContext);
    return childLogger;
  }

  /**
   * Update logger context
   */
  setContext(context: LogContext): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * Log info level message
   */
  info(message: string, meta?: any): void {
    this.winston.info(message, meta);
  }

  /**
   * Log warning level message
   */
  warn(message: string, meta?: any): void {
    this.winston.warn(message, meta);
  }

  /**
   * Log error level message
   */
  error(message: string, error?: Error | any, meta?: any): void {
    if (error instanceof Error) {
      this.winston.error(message, {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack
        },
        ...meta
      });
    } else {
      this.winston.error(message, { error, ...meta });
    }
  }

  /**
   * Log debug level message
   */
  debug(message: string, meta?: any): void {
    this.winston.debug(message, meta);
  }

  /**
   * Log audit trail entry
   */
  audit(action: string, entityType: string, entityId: string, meta?: any): void {
    this.winston.info('AUDIT', {
      audit: true,
      action,
      entityType,
      entityId,
      timestamp: new Date().toISOString(),
      correlationId: this.context.correlationId || uuidv4(),
      ...meta
    });
  }

  /**
   * Log security event
   */
  security(event: string, severity: 'low' | 'medium' | 'high' | 'critical', meta?: any): void {
    this.winston.warn('SECURITY_EVENT', {
      security: true,
      event,
      severity,
      timestamp: new Date().toISOString(),
      correlationId: this.context.correlationId || uuidv4(),
      ...meta
    });
  }

  /**
   * Log performance metric
   */
  performance(operation: string, durationMs: number, meta?: any): void {
    this.winston.info('PERFORMANCE', {
      performance: true,
      operation,
      durationMs,
      timestamp: new Date().toISOString(),
      ...meta
    });
  }

  /**
   * Log business event
   */
  business(event: string, meta?: any): void {
    this.winston.info('BUSINESS_EVENT', {
      business: true,
      event,
      timestamp: new Date().toISOString(),
      correlationId: this.context.correlationId || uuidv4(),
      ...meta
    });
  }
}

// Create default logger instance
export const logger = new Logger('OrderingSystem');