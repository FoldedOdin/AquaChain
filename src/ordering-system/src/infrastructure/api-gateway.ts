/**
 * API Gateway Infrastructure
 * Provides routing, middleware, and API versioning for the ordering system
 */

import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import { Logger } from './logger';
import { ApiResponse, ErrorResponse } from '../types/entities';

export interface ApiGatewayConfig {
  port: number;
  corsOrigins: string[];
  rateLimitWindowMs: number;
  rateLimitMaxRequests: number;
  enableRequestLogging: boolean;
  apiVersion: string;
}

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: 'consumer' | 'admin' | 'technician';
  };
  correlationId: string;
}

export class ApiGateway {
  private app: express.Application;
  private logger: Logger;
  private config: ApiGatewayConfig;
  private requestCounts: Map<string, { count: number; resetTime: number }> = new Map();

  constructor(config: Partial<ApiGatewayConfig> = {}) {
    this.config = {
      port: 3003,
      corsOrigins: ['http://localhost:3000', 'http://localhost:3001'],
      rateLimitWindowMs: 15 * 60 * 1000, // 15 minutes
      rateLimitMaxRequests: 100,
      enableRequestLogging: true,
      apiVersion: 'v1',
      ...config
    };

    this.app = express();
    this.logger = new Logger('ApiGateway');
    this.setupMiddleware();
    this.setupErrorHandling();
  }

  /**
   * Setup middleware stack
   */
  private setupMiddleware(): void {
    // CORS configuration
    this.app.use(cors({
      origin: this.config.corsOrigins,
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Correlation-ID']
    }));

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Correlation ID middleware
    this.app.use((req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      this.correlationIdMiddleware(req, res, next);
    });

    // Request logging middleware
    if (this.config.enableRequestLogging) {
      this.app.use((req: AuthenticatedRequest, res: Response, next: NextFunction) => {
        this.requestLoggingMiddleware(req, res, next);
      });
    }

    // Rate limiting middleware
    this.app.use((req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      this.rateLimitMiddleware(req, res, next);
    });

    // Health check endpoint
    this.app.get('/health', (req: AuthenticatedRequest, res: Response) => {
      this.healthCheck(req, res);
    });
    this.app.get('/api/health', (req: AuthenticatedRequest, res: Response) => {
      this.healthCheck(req, res);
    });
  }

  /**
   * Correlation ID middleware
   */
  private correlationIdMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    req.correlationId = req.headers['x-correlation-id'] as string || uuidv4();
    res.setHeader('X-Correlation-ID', req.correlationId);
    next();
  }

  /**
   * Request logging middleware
   */
  private requestLoggingMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    const startTime = Date.now();
    
    // Log request
    this.logger.info(`${req.method} ${req.path}`, {
      correlationId: req.correlationId,
      userAgent: req.headers['user-agent'],
      ip: req.ip,
      userId: req.user?.id
    });

    // Log response
    const originalSend = res.send;
    res.send = function(data) {
      const duration = Date.now() - startTime;
      
      const logger = new Logger('ApiGateway', { correlationId: req.correlationId });
      logger.performance(`${req.method} ${req.path}`, duration, {
        statusCode: res.statusCode,
        responseSize: Buffer.byteLength(data)
      });

      return originalSend.call(this, data);
    };

    next();
  }

  /**
   * Rate limiting middleware
   */
  private rateLimitMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    const clientId = req.ip || 'unknown';
    const now = Date.now();
    const windowStart = now - this.config.rateLimitWindowMs;

    // Clean up old entries
    for (const [key, data] of this.requestCounts.entries()) {
      if (data.resetTime < windowStart) {
        this.requestCounts.delete(key);
      }
    }

    // Check current client
    const clientData = this.requestCounts.get(clientId);
    
    if (!clientData) {
      this.requestCounts.set(clientId, { count: 1, resetTime: now });
    } else if (clientData.resetTime < windowStart) {
      this.requestCounts.set(clientId, { count: 1, resetTime: now });
    } else {
      clientData.count++;
      
      if (clientData.count > this.config.rateLimitMaxRequests) {
        return this.sendErrorResponse(res, {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: true
        }, 429);
      }
    }

    // Set rate limit headers
    res.setHeader('X-RateLimit-Limit', this.config.rateLimitMaxRequests);
    res.setHeader('X-RateLimit-Remaining', Math.max(0, this.config.rateLimitMaxRequests - (clientData?.count || 1)));
    res.setHeader('X-RateLimit-Reset', Math.ceil((now + this.config.rateLimitWindowMs) / 1000));

    next();
  }

  /**
   * Authentication middleware
   */
  authenticationMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return this.sendErrorResponse(res, {
        code: 'AUTHENTICATION_REQUIRED',
        message: 'Authentication required',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 401);
    }

    // Extract token for validation
    const token = authHeader.substring(7);
    
    // TODO: Implement proper JWT validation
    // For now, use simple token validation from existing system
    try {
      // This would integrate with the existing token validation
      // const decoded = jwt.verify(token, process.env.JWT_SECRET);
      // req.user = decoded;
      // const user = validateToken(token);
      // req.user = user;
      
      // Temporary mock user for development
      req.user = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'consumer'
      };
      
      next();
    } catch (error) {
      return this.sendErrorResponse(res, {
        code: 'INVALID_TOKEN',
        message: 'Invalid or expired token',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 401);
    }
  }

  /**
   * Authorization middleware
   */
  authorizationMiddleware(allowedRoles: string[]) {
    return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
      if (!req.user) {
        return this.sendErrorResponse(res, {
          code: 'AUTHENTICATION_REQUIRED',
          message: 'Authentication required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 401);
      }

      if (!allowedRoles.includes(req.user.role)) {
        return this.sendErrorResponse(res, {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Insufficient permissions',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 403);
      }

      next();
    };
  }

  /**
   * Setup error handling
   */
  private setupErrorHandling(): void {
    // 404 handler
    this.app.use('*', (req: AuthenticatedRequest, res: Response) => {
      this.sendErrorResponse(res, {
        code: 'ENDPOINT_NOT_FOUND',
        message: `Endpoint not found: ${req.method} ${req.originalUrl}`,
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    });

    // Global error handler
    this.app.use((error: Error, req: AuthenticatedRequest, res: Response, _next: NextFunction) => {
      this.logger.error('Unhandled error', error, {
        correlationId: req.correlationId,
        path: req.path,
        method: req.method
      });

      this.sendErrorResponse(res, {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected error occurred',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined,
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    });
  }

  /**
   * Health check endpoint
   */
  private healthCheck(req: AuthenticatedRequest, res: Response): void {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: this.config.apiVersion,
      uptime: process.uptime(),
      correlationId: req.correlationId
    };

    this.sendSuccessResponse(res, health);
  }

  /**
   * Send success response
   */
  sendSuccessResponse<T>(res: Response, data: T, statusCode: number = 200): void {
    const response: ApiResponse<T> = {
      success: true,
      data,
      metadata: {
        timestamp: new Date(),
        version: this.config.apiVersion,
        correlationId: res.getHeader('X-Correlation-ID') as string
      }
    };

    res.status(statusCode).json(response);
  }

  /**
   * Send error response
   */
  sendErrorResponse(res: Response, error: ErrorResponse, statusCode: number = 400): void {
    const response: ApiResponse = {
      success: false,
      error,
      metadata: {
        timestamp: new Date(),
        version: this.config.apiVersion,
        correlationId: res.getHeader('X-Correlation-ID') as string
      }
    };

    res.status(statusCode).json(response);
  }

  /**
   * Register route handlers
   */
  registerRoutes(basePath: string, router: express.Router): void {
    this.app.use(`/api/${this.config.apiVersion}${basePath}`, router);
    this.logger.info(`Routes registered: /api/${this.config.apiVersion}${basePath}`);
  }

  /**
   * Start the server
   */
  start(): Promise<void> {
    return new Promise((resolve) => {
      this.app.listen(this.config.port, () => {
        this.logger.info(`API Gateway started on port ${this.config.port}`);
        this.logger.info(`API Version: ${this.config.apiVersion}`);
        this.logger.info(`Health check: http://localhost:${this.config.port}/health`);
        resolve();
      });
    });
  }

  /**
   * Get Express app instance
   */
  getApp(): express.Application {
    return this.app;
  }
}

// Export singleton instance
export const apiGateway = new ApiGateway();