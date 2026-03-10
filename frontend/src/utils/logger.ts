/**
 * Frontend Logger Utility
 * Provides structured logging for frontend components
 */

export interface LogContext {
  correlationId?: string;
  userId?: string;
  component?: string;
  [key: string]: unknown;
}

class FrontendLogger {
  private context: LogContext = {};

  /**
   * Set logging context
   */
  setContext(context: LogContext): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * Create a child logger with additional context
   */
  child(additionalContext: LogContext): FrontendLogger {
    const childLogger = new FrontendLogger();
    childLogger.context = { ...this.context, ...additionalContext };
    return childLogger;
  }

  /**
   * Log info level message
   */
  info(message: string, meta?: unknown): void {
    console.log(`[INFO] ${message}`, {
      timestamp: new Date().toISOString(),
      context: this.context,
      data: meta
    });
  }

  /**
   * Log warning level message
   */
  warn(message: string, meta?: unknown): void {
    console.warn(`[WARN] ${message}`, {
      timestamp: new Date().toISOString(),
      context: this.context,
      data: meta
    });
  }

  /**
   * Log error level message
   */
  error(message: string, error?: Error | unknown, meta?: unknown): void {
    const errorInfo = error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack
    } : error;

    console.error(`[ERROR] ${message}`, {
      timestamp: new Date().toISOString(),
      context: this.context,
      error: errorInfo,
      data: meta
    });
  }

  /**
   * Log debug level message
   */
  debug(message: string, meta?: unknown): void {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[DEBUG] ${message}`, {
        timestamp: new Date().toISOString(),
        context: this.context,
        data: meta
      });
    }
  }
}

// Create and export default logger instance
export const logger = new FrontendLogger();