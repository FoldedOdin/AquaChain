/**
 * Audit and Monitoring Service
 * Provides comprehensive audit logging and system monitoring
 * Implements Requirements 6.4, 8.5, 9.3, 9.6 - Audit logging and monitoring
 */

import { v4 as uuidv4 } from 'uuid';
import { AuditLogEntry } from '../types/entities';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';

export interface AuditEvent {
  entityType: string;
  entityId: string;
  action: string;
  performedBy: string;
  timestamp: Date;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  metadata?: Record<string, any>;
  correlationId?: string;
}

export interface SystemMetrics {
  timestamp: Date;
  cpu?: number;
  memory?: number;
  activeConnections?: number;
  requestsPerMinute?: number;
  errorRate?: number;
  responseTime?: number;
}

export interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  details?: Record<string, any>;
  timestamp: Date;
}

export interface MonitoringAlert {
  id: string;
  type: 'performance' | 'error' | 'security' | 'business';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details: Record<string, any>;
  timestamp: Date;
  resolved: boolean;
  resolvedAt?: Date;
}

/**
 * Audit and Monitoring Service
 * Handles audit trails, system monitoring, and alerting
 */
export class AuditMonitoringService {
  private logger: Logger;
  private metrics: SystemMetrics[] = [];
  private alerts: MonitoringAlert[] = [];
  private healthChecks: Map<string, HealthCheckResult> = new Map();
  private retentionDays = 90;

  constructor() {
    this.logger = new Logger('AuditMonitoringService');
    this.setupEventHandlers();
    this.startPeriodicTasks();
  }

  /**
   * Setup event handlers for automatic audit logging
   */
  private setupEventHandlers(): void {
    // Listen to all domain events for audit trail
    const auditableEvents = [
      'ORDER_CREATED', 'ORDER_APPROVED', 'ORDER_COMPLETED', 'ORDER_CANCELLED',
      'PAYMENT_COMPLETED', 'PAYMENT_FAILED', 'COD_CONVERSION_COMPLETED',
      'SHIPMENT_CREATED', 'DELIVERY_STATUS_UPDATED', 'DELIVERY_COMPLETED',
      'INSTALLATION_REQUESTED', 'INSTALLATION_SCHEDULED', 'INSTALLATION_COMPLETED'
    ];

    auditableEvents.forEach(eventType => {
      eventBus.subscribe(eventType, async (event) => {
        await this.auditDomainEvent(eventType, event);
      });
    });

    // Listen for system events
    eventBus.subscribe('OPERATION_FAILED_AFTER_RETRIES', async (event) => {
      await this.createAlert('error', 'high', 'Operation failed after retries', event);
    });

    this.logger.info('Audit and monitoring event handlers registered');
  }

  /**
   * Start periodic monitoring tasks
   */
  private startPeriodicTasks(): void {
    // Collect system metrics every minute
    setInterval(() => {
      this.collectSystemMetrics();
    }, 60000);

    // Perform health checks every 5 minutes
    setInterval(() => {
      this.performHealthChecks();
    }, 300000);

    // Clean up old data every hour
    setInterval(() => {
      this.cleanupOldData();
    }, 3600000);

    this.logger.info('Periodic monitoring tasks started');
  }

  /**
   * Log audit event for critical operations
   * Implements Requirements 6.4, 8.5, 9.6
   */
  async auditEvent(auditEvent: AuditEvent): Promise<AuditLogEntry> {
    const auditEntry: AuditLogEntry = {
      id: uuidv4(),
      entityType: auditEvent.entityType,
      entityId: auditEvent.entityId,
      action: auditEvent.action,
      performedBy: auditEvent.performedBy,
      timestamp: auditEvent.timestamp,
      oldValues: auditEvent.oldValues,
      newValues: auditEvent.newValues,
      metadata: {
        correlationId: auditEvent.correlationId,
        ...auditEvent.metadata
      }
    };

    // Store in database
    const createdEntry = database.create<AuditLogEntry>('auditLog', auditEntry);

    // Log for immediate visibility
    this.logger.audit(auditEvent.action, auditEvent.entityType, auditEvent.entityId, {
      performedBy: auditEvent.performedBy,
      correlationId: auditEvent.correlationId,
      hasOldValues: !!auditEvent.oldValues,
      hasNewValues: !!auditEvent.newValues
    });

    return createdEntry;
  }

  /**
   * Audit domain events automatically
   */
  private async auditDomainEvent(eventType: string, eventData: any): Promise<void> {
    try {
      const auditEvent: AuditEvent = {
        entityType: this.getEntityTypeFromEvent(eventType),
        entityId: eventData.orderId || eventData.paymentId || eventData.shipmentId || eventData.installationId,
        action: eventType,
        performedBy: eventData.performedBy || eventData.approvedBy || eventData.technicianId || 'system',
        timestamp: new Date(),
        newValues: eventData,
        correlationId: eventData.correlationId
      };

      await this.auditEvent(auditEvent);

    } catch (error) {
      this.logger.error('Failed to audit domain event', error, {
        eventType,
        eventData: JSON.stringify(eventData)
      });
    }
  }

  /**
   * Get entity type from event type
   */
  private getEntityTypeFromEvent(eventType: string): string {
    if (eventType.startsWith('ORDER_')) return 'Order';
    if (eventType.startsWith('PAYMENT_') || eventType.startsWith('COD_')) return 'Payment';
    if (eventType.startsWith('SHIPMENT_') || eventType.startsWith('DELIVERY_')) return 'Delivery';
    if (eventType.startsWith('INSTALLATION_')) return 'Installation';
    return 'System';
  }

  /**
   * Collect system metrics
   */
  private async collectSystemMetrics(): Promise<void> {
    try {
      const metrics: SystemMetrics = {
        timestamp: new Date(),
        // In a real system, these would be actual system metrics
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        activeConnections: Math.floor(Math.random() * 1000),
        requestsPerMinute: Math.floor(Math.random() * 10000),
        errorRate: Math.random() * 5,
        responseTime: Math.random() * 1000
      };

      this.metrics.push(metrics);

      // Keep only last 24 hours of metrics
      const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);
      this.metrics = this.metrics.filter(m => m.timestamp > cutoff);

      // Check for alerts
      await this.checkMetricAlerts(metrics);

    } catch (error) {
      this.logger.error('Failed to collect system metrics', error);
    }
  }

  /**
   * Check metrics for alert conditions
   */
  private async checkMetricAlerts(metrics: SystemMetrics): Promise<void> {
    // High CPU alert
    if (metrics.cpu && metrics.cpu > 90) {
      await this.createAlert('performance', 'high', 'High CPU usage detected', {
        cpu: metrics.cpu,
        threshold: 90
      });
    }

    // High memory alert
    if (metrics.memory && metrics.memory > 85) {
      await this.createAlert('performance', 'medium', 'High memory usage detected', {
        memory: metrics.memory,
        threshold: 85
      });
    }

    // High error rate alert
    if (metrics.errorRate && metrics.errorRate > 10) {
      await this.createAlert('error', 'critical', 'High error rate detected', {
        errorRate: metrics.errorRate,
        threshold: 10
      });
    }

    // Slow response time alert
    if (metrics.responseTime && metrics.responseTime > 5000) {
      await this.createAlert('performance', 'medium', 'Slow response time detected', {
        responseTime: metrics.responseTime,
        threshold: 5000
      });
    }
  }

  /**
   * Perform health checks on all services
   */
  private async performHealthChecks(): Promise<void> {
    const services = ['database', 'eventBus', 'paymentService', 'deliveryService'];

    for (const service of services) {
      try {
        const startTime = Date.now();
        const result = await this.checkServiceHealth(service);
        const responseTime = Date.now() - startTime;

        const healthCheck: HealthCheckResult = {
          service,
          status: result.healthy ? 'healthy' : 'unhealthy',
          responseTime,
          details: result.details,
          timestamp: new Date()
        };

        this.healthChecks.set(service, healthCheck);

        if (!result.healthy) {
          await this.createAlert('error', 'high', `Service ${service} is unhealthy`, {
            service,
            details: result.details,
            responseTime
          });
        }

      } catch (error) {
        const healthCheck: HealthCheckResult = {
          service,
          status: 'unhealthy',
          responseTime: 0,
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
          timestamp: new Date()
        };

        this.healthChecks.set(service, healthCheck);

        await this.createAlert('error', 'critical', `Service ${service} health check failed`, {
          service,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  }

  /**
   * Check health of individual service
   */
  private async checkServiceHealth(service: string): Promise<{ healthy: boolean; details?: any }> {
    switch (service) {
      case 'database':
        try {
          const stats = database.getStatistics();
          return { healthy: true, details: stats };
        } catch (error) {
          return { healthy: false, details: { error: error instanceof Error ? error.message : 'Unknown error' } };
        }

      case 'eventBus':
        try {
          const stats = eventBus.getStatistics();
          return { healthy: true, details: stats };
        } catch (error) {
          return { healthy: false, details: { error: error instanceof Error ? error.message : 'Unknown error' } };
        }

      default:
        return { healthy: true, details: { message: 'No specific health check implemented' } };
    }
  }

  /**
   * Create monitoring alert
   */
  async createAlert(
    type: MonitoringAlert['type'],
    severity: MonitoringAlert['severity'],
    message: string,
    details: Record<string, any>
  ): Promise<MonitoringAlert> {
    const alert: MonitoringAlert = {
      id: uuidv4(),
      type,
      severity,
      message,
      details,
      timestamp: new Date(),
      resolved: false
    };

    this.alerts.push(alert);

    // Log alert
    this.logger.warn('Monitoring alert created', {
      alertId: alert.id,
      type,
      severity,
      message,
      details
    });

    // Emit alert event
    await eventBus.publish(
      'system',
      'Order',
      'MONITORING_ALERT_CREATED',
      alert
    );

    return alert;
  }

  /**
   * Resolve monitoring alert
   */
  async resolveAlert(alertId: string, resolvedBy: string): Promise<boolean> {
    const alert = this.alerts.find(a => a.id === alertId);
    if (!alert) {
      return false;
    }

    alert.resolved = true;
    alert.resolvedAt = new Date();

    this.logger.info('Monitoring alert resolved', {
      alertId,
      resolvedBy,
      resolvedAt: alert.resolvedAt
    });

    return true;
  }

  /**
   * Get audit trail for entity
   */
  async getAuditTrail(entityType: string, entityId: string): Promise<AuditLogEntry[]> {
    return database.findWhere<AuditLogEntry>('auditLog', 
      entry => entry.entityType === entityType && entry.entityId === entityId
    ).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Get audit trail for user actions
   */
  async getUserAuditTrail(userId: string, limit: number = 100): Promise<AuditLogEntry[]> {
    return database.findWhere<AuditLogEntry>('auditLog', 
      entry => entry.performedBy === userId
    )
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, limit);
  }

  /**
   * Get system metrics for time range
   */
  getSystemMetrics(startTime: Date, endTime: Date): SystemMetrics[] {
    return this.metrics.filter(m => 
      m.timestamp >= startTime && m.timestamp <= endTime
    );
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(): MonitoringAlert[] {
    return this.alerts.filter(a => !a.resolved);
  }

  /**
   * Get health check results
   */
  getHealthCheckResults(): Record<string, HealthCheckResult> {
    const results: Record<string, HealthCheckResult> = {};
    for (const [service, result] of this.healthChecks.entries()) {
      results[service] = result;
    }
    return results;
  }

  /**
   * Get monitoring statistics
   */
  getMonitoringStatistics(): {
    auditEntries: number;
    activeAlerts: number;
    totalAlerts: number;
    healthyServices: number;
    totalServices: number;
    metricsCollected: number;
  } {
    const auditEntries = database.findAll<AuditLogEntry>('auditLog').length;
    const activeAlerts = this.getActiveAlerts().length;
    const healthyServices = Array.from(this.healthChecks.values())
      .filter(h => h.status === 'healthy').length;

    return {
      auditEntries,
      activeAlerts,
      totalAlerts: this.alerts.length,
      healthyServices,
      totalServices: this.healthChecks.size,
      metricsCollected: this.metrics.length
    };
  }

  /**
   * Clean up old data based on retention policy
   */
  private cleanupOldData(): void {
    const cutoffDate = new Date(Date.now() - this.retentionDays * 24 * 60 * 60 * 1000);

    // Clean up old metrics
    this.metrics = this.metrics.filter(m => m.timestamp > cutoffDate);

    // Clean up old resolved alerts
    this.alerts = this.alerts.filter(a => 
      !a.resolved || (a.resolvedAt && a.resolvedAt > cutoffDate)
    );

    this.logger.info('Old monitoring data cleaned up', {
      cutoffDate,
      retentionDays: this.retentionDays
    });
  }

  /**
   * Export audit data for compliance
   */
  async exportAuditData(startDate: Date, endDate: Date): Promise<{
    auditEntries: AuditLogEntry[];
    exportedAt: Date;
    totalEntries: number;
  }> {
    const auditEntries = database.findWhere<AuditLogEntry>('auditLog', 
      entry => entry.timestamp >= startDate && entry.timestamp <= endDate
    );

    this.logger.info('Audit data exported', {
      startDate,
      endDate,
      totalEntries: auditEntries.length
    });

    return {
      auditEntries,
      exportedAt: new Date(),
      totalEntries: auditEntries.length
    };
  }
}

// Export singleton instance
export const auditMonitoringService = new AuditMonitoringService();