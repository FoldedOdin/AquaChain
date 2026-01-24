/**
 * Admin API Routes
 * Provides admin-specific endpoints for order management and approval workflow
 */

import { Router } from 'express';
import { adminWorkflowService, AdminApprovalRequest } from '../services/admin-workflow-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('AdminRoutes');

/**
 * Get orders pending approval
 * GET /api/v1/admin/orders/pending
 */
router.get('/orders/pending',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const pendingOrders = await adminWorkflowService.getPendingApprovals();

      logger.info('Retrieved pending orders for admin', {
        adminId: req.user!.id,
        count: pendingOrders.length,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        orders: pendingOrders,
        count: pendingOrders.length,
        message: `Found ${pendingOrders.length} orders pending approval`
      });
    } catch (error) {
      logger.error('Failed to get pending orders', error, {
        correlationId: req.correlationId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'PENDING_ORDERS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve pending orders',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Process order approval
 * POST /api/v1/admin/orders/:orderId/approve
 */
router.post('/orders/:orderId/approve',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId } = req.params;
      const { quoteAmount, notes } = req.body;

      // Validate admin permissions
      if (!adminWorkflowService.validateAdminPermissions(req.user!.id, req.user!.role)) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INSUFFICIENT_ADMIN_PERMISSIONS',
          message: 'Insufficient permissions for order approval',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 403);
      }

      const approvalRequest: AdminApprovalRequest = {
        orderId,
        adminId: req.user!.id,
        adminEmail: req.user!.email,
        quoteAmount,
        notes
      };

      const result = await adminWorkflowService.processOrderApproval(approvalRequest);

      logger.info('Order approval processed', {
        orderId,
        adminId: req.user!.id,
        quoteAmount,
        approved: result.approved,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, result, 200);
    } catch (error) {
      logger.error('Failed to process order approval', error, {
        correlationId: req.correlationId,
        orderId: req.params.orderId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'ORDER_APPROVAL_FAILED',
        message: error instanceof Error ? error.message : 'Failed to process order approval',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Get approval statistics
 * GET /api/v1/admin/statistics/approvals
 */
router.get('/statistics/approvals',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const includePersonal = req.query.includePersonal === 'true';
      const adminId = includePersonal ? req.user!.id : undefined;

      const statistics = await adminWorkflowService.getApprovalStatistics(adminId);

      logger.info('Retrieved approval statistics', {
        adminId: req.user!.id,
        includePersonal,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        statistics,
        generatedAt: new Date(),
        adminId: includePersonal ? req.user!.id : null
      });
    } catch (error) {
      logger.error('Failed to get approval statistics', error, {
        correlationId: req.correlationId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'STATISTICS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve approval statistics',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Get approval workflow status for an order
 * GET /api/v1/admin/orders/:orderId/workflow-status
 */
router.get('/orders/:orderId/workflow-status',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId } = req.params;
      const workflowStatus = await adminWorkflowService.getApprovalWorkflowStatus(orderId);

      logger.info('Retrieved workflow status', {
        orderId,
        adminId: req.user!.id,
        currentStatus: workflowStatus.currentStatus,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, workflowStatus);
    } catch (error) {
      logger.error('Failed to get workflow status', error, {
        correlationId: req.correlationId,
        orderId: req.params.orderId,
        adminId: req.user?.id
      });

      if (error instanceof Error && error.message.includes('not found')) {
        apiGateway.sendErrorResponse(res, {
          code: 'ORDER_NOT_FOUND',
          message: error.message,
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 404);
      } else {
        apiGateway.sendErrorResponse(res, {
          code: 'WORKFLOW_STATUS_RETRIEVAL_FAILED',
          message: 'Failed to retrieve workflow status',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: true
        }, 500);
      }
    }
  }
);

/**
 * Bulk approve orders
 * POST /api/v1/admin/orders/bulk-approve
 */
router.post('/orders/bulk-approve',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orders, defaultQuoteAmount } = req.body;

      if (!Array.isArray(orders) || orders.length === 0) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_BULK_REQUEST',
          message: 'Orders array is required and must not be empty',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      // Validate admin permissions
      if (!adminWorkflowService.validateAdminPermissions(req.user!.id, req.user!.role)) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INSUFFICIENT_ADMIN_PERMISSIONS',
          message: 'Insufficient permissions for bulk order approval',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 403);
      }

      const results = [];
      const errors = [];

      // Process each order
      for (const orderRequest of orders) {
        try {
          const approvalRequest: AdminApprovalRequest = {
            orderId: orderRequest.orderId,
            adminId: req.user!.id,
            adminEmail: req.user!.email,
            quoteAmount: orderRequest.quoteAmount || defaultQuoteAmount,
            notes: orderRequest.notes || 'Bulk approval'
          };

          const result = await adminWorkflowService.processOrderApproval(approvalRequest);
          results.push({
            orderId: orderRequest.orderId,
            success: true,
            result
          });
        } catch (error) {
          errors.push({
            orderId: orderRequest.orderId,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      }

      logger.info('Bulk approval completed', {
        adminId: req.user!.id,
        totalOrders: orders.length,
        successful: results.length,
        failed: errors.length,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        summary: {
          total: orders.length,
          successful: results.length,
          failed: errors.length
        },
        results,
        errors,
        processedAt: new Date()
      });
    } catch (error) {
      logger.error('Failed to process bulk approval', error, {
        correlationId: req.correlationId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'BULK_APPROVAL_FAILED',
        message: 'Failed to process bulk approval',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Cancel order (Admin)
 * PUT /api/v1/admin/orders/:orderId/cancel
 * Allows admins to cancel orders at any stage with detailed reason
 */
router.put('/orders/:orderId/cancel',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId } = req.params;
      const { reason, notifyConsumer, refundAmount } = req.body;

      // Validate admin permissions
      if (!adminWorkflowService.validateAdminPermissions(req.user!.id, req.user!.role)) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INSUFFICIENT_ADMIN_PERMISSIONS',
          message: 'Insufficient permissions for order cancellation',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 403);
      }

      // Validate cancel reason
      if (!reason?.trim()) {
        return apiGateway.sendErrorResponse(res, {
          code: 'CANCEL_REASON_REQUIRED',
          message: 'Cancel reason is required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      // Get order details for validation
      const order = await adminWorkflowService.getOrderForApproval(orderId);
      if (!order) {
        return apiGateway.sendErrorResponse(res, {
          code: 'ORDER_NOT_FOUND',
          message: 'Order not found',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 404);
      }

      // Check if order can be cancelled
      if (order.status === 'CANCELLED') {
        return apiGateway.sendErrorResponse(res, {
          code: 'ORDER_ALREADY_CANCELLED',
          message: 'Order is already cancelled',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      if (order.status === 'COMPLETED') {
        return apiGateway.sendErrorResponse(res, {
          code: 'CANCELLATION_NOT_ALLOWED',
          message: 'Completed orders cannot be cancelled. Please contact support for refund processing.',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      // Process admin cancellation with additional context
      const cancellationResult = await adminWorkflowService.processOrderCancellation({
        orderId,
        adminId: req.user!.id,
        adminEmail: req.user!.email,
        reason,
        notifyConsumer: notifyConsumer !== false, // Default to true
        refundAmount: refundAmount || 0
      });

      logger.info('Order cancelled by admin', {
        orderId,
        adminId: req.user!.id,
        reason,
        notifyConsumer,
        refundAmount,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        message: 'Order cancelled successfully',
        cancellation: cancellationResult,
        nextSteps: [
          notifyConsumer !== false ? 'Consumer will be notified via email' : 'Consumer notification skipped',
          refundAmount > 0 ? `Refund of ₹${refundAmount} will be processed` : 'No refund amount specified',
          'Order status updated to CANCELLED',
          'Related delivery and installation requests will be cancelled'
        ]
      });

    } catch (error) {
      logger.error('Failed to cancel order', error, {
        correlationId: req.correlationId,
        orderId: req.params.orderId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'ORDER_CANCELLATION_FAILED',
        message: error instanceof Error ? error.message : 'Failed to cancel order',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Bulk cancel orders
 * POST /api/v1/admin/orders/bulk-cancel
 */
router.post('/orders/bulk-cancel',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orders, defaultReason, notifyConsumers } = req.body;

      if (!Array.isArray(orders) || orders.length === 0) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_BULK_REQUEST',
          message: 'Orders array is required and must not be empty',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      // Validate admin permissions
      if (!adminWorkflowService.validateAdminPermissions(req.user!.id, req.user!.role)) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INSUFFICIENT_ADMIN_PERMISSIONS',
          message: 'Insufficient permissions for bulk order cancellation',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 403);
      }

      const results = [];
      const errors = [];

      // Process each order
      for (const orderRequest of orders) {
        try {
          const cancellationResult = await adminWorkflowService.processOrderCancellation({
            orderId: orderRequest.orderId,
            adminId: req.user!.id,
            adminEmail: req.user!.email,
            reason: orderRequest.reason || defaultReason || 'Bulk cancellation',
            notifyConsumer: notifyConsumers !== false,
            refundAmount: orderRequest.refundAmount || 0
          });

          results.push({
            orderId: orderRequest.orderId,
            success: true,
            result: cancellationResult
          });
        } catch (error) {
          errors.push({
            orderId: orderRequest.orderId,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      }

      logger.info('Bulk cancellation completed', {
        adminId: req.user!.id,
        totalOrders: orders.length,
        successful: results.length,
        failed: errors.length,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        summary: {
          total: orders.length,
          successful: results.length,
          failed: errors.length
        },
        results,
        errors,
        processedAt: new Date()
      });

    } catch (error) {
      logger.error('Failed to process bulk cancellation', error, {
        correlationId: req.correlationId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'BULK_CANCELLATION_FAILED',
        message: 'Failed to process bulk cancellation',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

export default router;