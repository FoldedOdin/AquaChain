/**
 * Admin Workflow Service
 * Manages admin approval workflow with proper authorization and event emission
 * Implements Requirements 2.2, 2.3
 */

import { orderService } from './order-service';
import { Order } from '../types/entities';
import { Logger } from '../infrastructure/logger';
import { eventBus } from '../infrastructure/event-bus';

export interface AdminApprovalRequest {
  orderId: string;
  adminId: string;
  adminEmail: string;
  quoteAmount: number;
  notes?: string;
}

export interface AdminApprovalResult {
  order: Order;
  approved: boolean;
  message: string;
  timestamp: Date;
}

export interface AdminCancellationRequest {
  orderId: string;
  adminId: string;
  adminEmail: string;
  reason: string;
  notifyConsumer: boolean;
  refundAmount: number;
}

export interface AdminCancellationResult {
  order: Order;
  cancelled: boolean;
  message: string;
  timestamp: Date;
  refundAmount: number;
  consumerNotified: boolean;
}

/**
 * Admin Workflow Service
 * Handles admin-specific operations with proper authorization
 */
export class AdminWorkflowService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('AdminWorkflowService');
  }

  /**
   * Process admin approval for an order
   * Implements Requirements 2.2, 2.3 - Admin approval is mandatory before shipment
   */
  async processOrderApproval(request: AdminApprovalRequest): Promise<AdminApprovalResult> {
    this.logger.info('Processing admin approval', {
      orderId: request.orderId,
      adminId: request.adminId,
      quoteAmount: request.quoteAmount
    });

    try {
      // Validate admin approval request
      this.validateApprovalRequest(request);

      // Get current order
      const currentOrder = await orderService.getOrder(request.orderId);
      if (!currentOrder) {
        throw new Error(`Order not found: ${request.orderId}`);
      }

      // Verify order is in correct state for approval
      if (currentOrder.status !== 'PENDING') {
        throw new Error(
          `Order ${request.orderId} cannot be approved. Current status: ${currentOrder.status}. ` +
          'Only PENDING orders can be approved.'
        );
      }

      // Approve the order using order service
      const approvedOrder = await orderService.approveOrder({
        orderId: request.orderId,
        approvedBy: request.adminId,
        quoteAmount: request.quoteAmount
      });

      // Log admin action for audit trail
      this.logger.audit('ORDER_APPROVED', 'Order', request.orderId, {
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        quoteAmount: request.quoteAmount,
        notes: request.notes,
        previousStatus: currentOrder.status,
        newStatus: approvedOrder.status
      });

      // Create admin workflow event for tracking
      await this.emitAdminWorkflowEvent('ADMIN_APPROVAL_COMPLETED', {
        orderId: request.orderId,
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        action: 'APPROVE',
        quoteAmount: request.quoteAmount,
        notes: request.notes,
        timestamp: new Date()
      });

      const result: AdminApprovalResult = {
        order: approvedOrder,
        approved: true,
        message: `Order ${request.orderId} approved successfully with quote amount ₹${request.quoteAmount}`,
        timestamp: new Date()
      };

      this.logger.business('Admin approval completed', {
        orderId: request.orderId,
        adminId: request.adminId,
        quoteAmount: request.quoteAmount,
        result: 'SUCCESS'
      });

      return result;

    } catch (error) {
      this.logger.error('Admin approval failed', error, {
        orderId: request.orderId,
        adminId: request.adminId
      });

      // Log failed approval attempt
      this.logger.audit('ORDER_APPROVAL_FAILED', 'Order', request.orderId, {
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      });

      // Emit failure event
      await this.emitAdminWorkflowEvent('ADMIN_APPROVAL_FAILED', {
        orderId: request.orderId,
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        action: 'APPROVE',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      });

      throw error;
    }
  }

  /**
   * Get orders pending admin approval
   */
  async getPendingApprovals(): Promise<Order[]> {
    this.logger.info('Retrieving orders pending approval');

    const pendingOrders = await orderService.getOrdersByStatus('PENDING');
    
    this.logger.info(`Found ${pendingOrders.length} orders pending approval`);
    
    return pendingOrders;
  }

  /**
   * Get admin approval statistics
   */
  async getApprovalStatistics(adminId?: string): Promise<{
    totalPending: number;
    totalApproved: number;
    totalCancelled: number;
    averageApprovalTime?: number;
    adminSpecificApprovals?: number;
  }> {
    const allOrders = await orderService.getAllOrders();
    
    const baseStats = {
      totalPending: allOrders.filter(o => o.status === 'PENDING').length,
      totalApproved: allOrders.filter(o => o.status === 'APPROVED').length,
      totalCancelled: allOrders.filter(o => o.status === 'CANCELLED').length
    };

    // Add admin-specific approvals if adminId is provided
    const adminSpecificApprovals = adminId ? 
      allOrders.filter(o => o.approvedBy === adminId).length : undefined;

    // Calculate average approval time for approved orders
    const approvedOrders = allOrders.filter(o => o.status === 'APPROVED' && o.createdAt && o.approvedAt);
    let averageApprovalTime: number | undefined;
    
    if (approvedOrders.length > 0) {
      const totalApprovalTime = approvedOrders.reduce((sum, order) => {
        const approvalTime = new Date(order.approvedAt!).getTime() - new Date(order.createdAt).getTime();
        return sum + approvalTime;
      }, 0);
      
      averageApprovalTime = Math.round(totalApprovalTime / approvedOrders.length / (1000 * 60)); // in minutes
    }

    // Build result object with proper optional properties
    const result: {
      totalPending: number;
      totalApproved: number;
      totalCancelled: number;
      averageApprovalTime?: number;
      adminSpecificApprovals?: number;
    } = {
      ...baseStats
    };

    if (averageApprovalTime !== undefined) {
      result.averageApprovalTime = averageApprovalTime;
    }

    if (adminSpecificApprovals !== undefined) {
      result.adminSpecificApprovals = adminSpecificApprovals;
    }

    return result;
  }

  /**
   * Validate admin approval request
   */
  private validateApprovalRequest(request: AdminApprovalRequest): void {
    const errors: string[] = [];

    if (!request.orderId?.trim()) {
      errors.push('Order ID is required');
    }

    if (!request.adminId?.trim()) {
      errors.push('Admin ID is required');
    }

    if (!request.adminEmail?.trim()) {
      errors.push('Admin email is required');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(request.adminEmail)) {
      errors.push('Valid admin email is required');
    }

    if (!request.quoteAmount || request.quoteAmount <= 0) {
      errors.push('Quote amount must be a positive number');
    }

    // Business rule: Quote amount should be reasonable (between ₹1,000 and ₹50,000)
    if (request.quoteAmount && (request.quoteAmount < 1000 || request.quoteAmount > 50000)) {
      errors.push('Quote amount must be between ₹1,000 and ₹50,000');
    }

    if (errors.length > 0) {
      throw new Error(`Admin approval validation failed: ${errors.join(', ')}`);
    }
  }

  /**
   * Emit admin workflow event for tracking and monitoring
   */
  private async emitAdminWorkflowEvent(eventType: string, eventData: any): Promise<void> {
    try {
      await eventBus.publish(
        eventData.orderId,
        'Order',
        eventType,
        eventData
      );
    } catch (error) {
      this.logger.error('Failed to emit admin workflow event', error, {
        eventType,
        orderId: eventData.orderId
      });
      // Don't throw - this is a non-critical operation
    }
  }

  /**
   * Check if admin has permission to approve orders
   * This would integrate with a proper RBAC system in production
   */
  validateAdminPermissions(adminId: string, adminRole: string): boolean {
    // For now, simple role check
    const allowedRoles = ['admin', 'super_admin', 'order_manager'];
    
    if (!allowedRoles.includes(adminRole)) {
      this.logger.security('Unauthorized approval attempt', 'medium', {
        adminId,
        adminRole,
        requiredRoles: allowedRoles
      });
      return false;
    }

    return true;
  }

  /**
   * Get approval workflow status for an order
   */
  async getApprovalWorkflowStatus(orderId: string): Promise<{
    orderId: string;
    currentStatus: string;
    canBeApproved: boolean;
    approvalHistory: any[];
    nextActions: string[];
  }> {
    const order = await orderService.getOrder(orderId);
    
    if (!order) {
      throw new Error(`Order not found: ${orderId}`);
    }

    const canBeApproved = order.status === 'PENDING';
    const nextActions: string[] = [];

    if (canBeApproved) {
      nextActions.push('APPROVE', 'CANCEL');
    } else if (order.status === 'APPROVED') {
      nextActions.push('COMPLETE', 'CANCEL');
    }

    return {
      orderId,
      currentStatus: order.status,
      canBeApproved,
      approvalHistory: [], // Would be populated from audit logs in production
      nextActions
    };
  }

  /**
   * Get order for approval (used by admin routes)
   */
  async getOrderForApproval(orderId: string): Promise<Order | null> {
    this.logger.info('Getting order for approval', { orderId });
    
    try {
      const order = await orderService.getOrder(orderId);
      
      if (order) {
        this.logger.info('Order retrieved for approval', {
          orderId,
          status: order.status,
          consumerId: order.consumerId
        });
      } else {
        this.logger.warn('Order not found for approval', { orderId });
      }
      
      return order;
    } catch (error) {
      this.logger.error('Failed to get order for approval', error, { orderId });
      throw error;
    }
  }

  /**
   * Process admin order cancellation
   * Handles cancellation with admin-specific context and notifications
   */
  async processOrderCancellation(request: AdminCancellationRequest): Promise<AdminCancellationResult> {
    this.logger.info('Processing admin order cancellation', {
      orderId: request.orderId,
      adminId: request.adminId,
      reason: request.reason,
      refundAmount: request.refundAmount
    });

    try {
      // Validate admin cancellation request
      this.validateCancellationRequest(request);

      // Get current order
      const currentOrder = await orderService.getOrder(request.orderId);
      if (!currentOrder) {
        throw new Error(`Order not found: ${request.orderId}`);
      }

      // Verify order can be cancelled
      if (currentOrder.status === 'CANCELLED') {
        throw new Error(`Order ${request.orderId} is already cancelled`);
      }

      if (currentOrder.status === 'COMPLETED') {
        throw new Error(
          `Order ${request.orderId} is completed and cannot be cancelled. ` +
          'Please contact support for refund processing.'
        );
      }

      // Cancel the order using order service with admin flag
      const cancelledOrder = await orderService.cancelOrder(
        request.orderId,
        request.adminId,
        `Admin cancellation: ${request.reason}`,
        true // isAdmin flag
      );

      // Log admin action for audit trail
      this.logger.audit('ORDER_CANCELLED_BY_ADMIN', 'Order', request.orderId, {
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        reason: request.reason,
        refundAmount: request.refundAmount,
        notifyConsumer: request.notifyConsumer,
        previousStatus: currentOrder.status,
        newStatus: cancelledOrder.status
      });

      // Create admin workflow event for tracking
      await this.emitAdminWorkflowEvent('ADMIN_CANCELLATION_COMPLETED', {
        orderId: request.orderId,
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        action: 'CANCEL',
        reason: request.reason,
        refundAmount: request.refundAmount,
        notifyConsumer: request.notifyConsumer,
        timestamp: new Date()
      });

      // Handle consumer notification (would integrate with notification service in production)
      let consumerNotified = false;
      if (request.notifyConsumer) {
        try {
          await this.notifyConsumerOfCancellation(currentOrder, request);
          consumerNotified = true;
          this.logger.info('Consumer notified of cancellation', {
            orderId: request.orderId,
            consumerId: currentOrder.consumerId
          });
        } catch (notificationError) {
          this.logger.error('Failed to notify consumer of cancellation', notificationError, {
            orderId: request.orderId,
            consumerId: currentOrder.consumerId
          });
          // Don't fail the cancellation if notification fails
        }
      }

      const result: AdminCancellationResult = {
        order: cancelledOrder,
        cancelled: true,
        message: `Order ${request.orderId} cancelled successfully by admin`,
        timestamp: new Date(),
        refundAmount: request.refundAmount,
        consumerNotified
      };

      this.logger.business('Admin cancellation completed', {
        orderId: request.orderId,
        adminId: request.adminId,
        refundAmount: request.refundAmount,
        consumerNotified,
        result: 'SUCCESS'
      });

      return result;

    } catch (error) {
      this.logger.error('Admin cancellation failed', error, {
        orderId: request.orderId,
        adminId: request.adminId
      });

      // Log failed cancellation attempt
      this.logger.audit('ORDER_CANCELLATION_FAILED', 'Order', request.orderId, {
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      });

      // Emit failure event
      await this.emitAdminWorkflowEvent('ADMIN_CANCELLATION_FAILED', {
        orderId: request.orderId,
        adminId: request.adminId,
        adminEmail: request.adminEmail,
        action: 'CANCEL',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      });

      throw error;
    }
  }

  /**
   * Validate admin cancellation request
   */
  private validateCancellationRequest(request: AdminCancellationRequest): void {
    const errors: string[] = [];

    if (!request.orderId?.trim()) {
      errors.push('Order ID is required');
    }

    if (!request.adminId?.trim()) {
      errors.push('Admin ID is required');
    }

    if (!request.adminEmail?.trim()) {
      errors.push('Admin email is required');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(request.adminEmail)) {
      errors.push('Valid admin email is required');
    }

    if (!request.reason?.trim()) {
      errors.push('Cancellation reason is required');
    } else if (request.reason.trim().length < 10) {
      errors.push('Cancellation reason must be at least 10 characters');
    }

    if (request.refundAmount < 0) {
      errors.push('Refund amount cannot be negative');
    }

    // Business rule: Refund amount should not exceed reasonable limits
    if (request.refundAmount > 100000) {
      errors.push('Refund amount exceeds maximum limit of ₹1,00,000');
    }

    if (errors.length > 0) {
      throw new Error(`Admin cancellation validation failed: ${errors.join(', ')}`);
    }
  }

  /**
   * Notify consumer of order cancellation
   * This would integrate with a proper notification service in production
   */
  private async notifyConsumerOfCancellation(order: Order, request: AdminCancellationRequest): Promise<void> {
    // In production, this would send email/SMS to consumer
    this.logger.info('Sending cancellation notification to consumer', {
      orderId: order.id,
      consumerId: order.consumerId,
      adminId: request.adminId,
      reason: request.reason,
      refundAmount: request.refundAmount
    });

    // Simulate notification service call
    // await notificationService.sendCancellationNotification({
    //   consumerId: order.consumerId,
    //   orderId: order.id,
    //   reason: request.reason,
    //   refundAmount: request.refundAmount,
    //   supportContact: 'support@aquachain.com'
    // });

    // For now, just log the notification
    this.logger.business('Consumer cancellation notification sent', {
      orderId: order.id,
      consumerId: order.consumerId,
      notificationType: 'ORDER_CANCELLED_BY_ADMIN'
    });
  }
}

// Export singleton instance
export const adminWorkflowService = new AdminWorkflowService();