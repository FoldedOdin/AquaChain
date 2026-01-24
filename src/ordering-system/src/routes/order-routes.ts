/**
 * Order API Routes
 * Provides REST endpoints for order management
 */

import { Router } from 'express';
import { orderService, CreateOrderRequest, ApproveOrderRequest } from '../services/order-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('OrderRoutes');

/**
 * Create a new order
 * POST /api/v1/orders
 */
router.post('/', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const createRequest: CreateOrderRequest = {
      consumerId: req.user!.id,
      deviceType: req.body.deviceType || 'AC-HOME-V1',
      paymentMethod: req.body.paymentMethod,
      address: req.body.address,
      phone: req.body.phone
    };

    const order = await orderService.createOrder(createRequest);
    
    logger.info('Order created via API', {
      orderId: order.id,
      consumerId: order.consumerId,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, order, 201);
  } catch (error) {
    logger.error('Failed to create order', error, {
      correlationId: req.correlationId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'ORDER_CREATION_FAILED',
      message: error instanceof Error ? error.message : 'Failed to create order',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Get order by ID
 * GET /api/v1/orders/:orderId
 */
router.get('/:orderId', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const order = await orderService.getOrder(orderId);

    if (!order) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ORDER_NOT_FOUND',
        message: 'Order not found',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    }

    // Check if user owns this order or is admin
    if (order.consumerId !== req.user!.id && req.user!.role !== 'admin') {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'Access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }

    apiGateway.sendSuccessResponse(res, order);
  } catch (error) {
    logger.error('Failed to get order', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'ORDER_RETRIEVAL_FAILED',
      message: 'Failed to retrieve order',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get user's orders
 * GET /api/v1/orders
 */
router.get('/', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    let orders;

    if (req.user!.role === 'admin') {
      // Admin can see all orders
      orders = await orderService.getAllOrders();
    } else {
      // Consumer can only see their own orders
      orders = await orderService.getOrdersByConsumer(req.user!.id);
    }

    apiGateway.sendSuccessResponse(res, {
      orders,
      count: orders.length
    });
  } catch (error) {
    logger.error('Failed to get orders', error, {
      correlationId: req.correlationId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'ORDERS_RETRIEVAL_FAILED',
      message: 'Failed to retrieve orders',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Approve order (Admin only)
 * PUT /api/v1/orders/:orderId/approve
 */
router.put('/:orderId/approve', 
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId } = req.params;
      const { quoteAmount } = req.body;

      if (!quoteAmount || quoteAmount <= 0) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_QUOTE_AMOUNT',
          message: 'Quote amount must be a positive number',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const approveRequest: ApproveOrderRequest = {
        orderId,
        approvedBy: req.user!.id,
        quoteAmount
      };

      const order = await orderService.approveOrder(approveRequest);

      logger.info('Order approved via API', {
        orderId: order.id,
        approvedBy: req.user!.id,
        quoteAmount,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, order);
    } catch (error) {
      logger.error('Failed to approve order', error, {
        correlationId: req.correlationId,
        orderId: req.params.orderId,
        userId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'ORDER_APPROVAL_FAILED',
        message: error instanceof Error ? error.message : 'Failed to approve order',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Cancel order (Admin only)
 * PUT /api/v1/orders/:orderId/cancel
 */
router.put('/:orderId/cancel',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId } = req.params;
      const { reason } = req.body;

      if (!reason?.trim()) {
        return apiGateway.sendErrorResponse(res, {
          code: 'CANCEL_REASON_REQUIRED',
          message: 'Cancel reason is required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const order = await orderService.cancelOrder(orderId, req.user!.id, reason);

      logger.info('Order cancelled via API', {
        orderId: order.id,
        cancelledBy: req.user!.id,
        reason,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, order);
    } catch (error) {
      logger.error('Failed to cancel order', error, {
        correlationId: req.correlationId,
        orderId: req.params.orderId,
        userId: req.user?.id
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
 * Get orders by status (Admin only)
 * GET /api/v1/orders/status/:status
 */
router.get('/status/:status',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { status } = req.params;
      
      const validStatuses = ['PENDING', 'APPROVED', 'COMPLETED', 'CANCELLED'];
      if (!validStatuses.includes(status.toUpperCase())) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_STATUS',
          message: `Invalid status. Valid statuses: ${validStatuses.join(', ')}`,
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const orders = await orderService.getOrdersByStatus(status.toUpperCase() as any);

      apiGateway.sendSuccessResponse(res, {
        orders,
        count: orders.length,
        status: status.toUpperCase()
      });
    } catch (error) {
      logger.error('Failed to get orders by status', error, {
        correlationId: req.correlationId,
        status: req.params.status
      });

      apiGateway.sendErrorResponse(res, {
        code: 'ORDERS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve orders by status',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

export default router;