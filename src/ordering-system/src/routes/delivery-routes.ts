/**
 * Delivery API Routes
 * Provides REST endpoints for delivery management and tracking
 */

import { Router } from 'express';
import { deliveryService, CreateShipmentRequest, UpdateDeliveryStatusRequest } from '../services/delivery-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('DeliveryRoutes');

/**
 * Create shipment (Admin only)
 * POST /api/v1/deliveries/create-shipment
 */
router.post('/create-shipment',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { orderId, address, carrier, estimatedDelivery } = req.body;

      if (!orderId || !address) {
        return apiGateway.sendErrorResponse(res, {
          code: 'MISSING_REQUIRED_FIELDS',
          message: 'Order ID and address are required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const createRequest: CreateShipmentRequest = {
        orderId,
        address,
        carrier,
        estimatedDelivery: estimatedDelivery ? new Date(estimatedDelivery) : undefined
      };

      const delivery = await deliveryService.initiateShipment(createRequest);

      logger.info('Shipment created via API', {
        orderId,
        shipmentId: delivery.shipmentId,
        trackingNumber: delivery.trackingNumber,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, delivery, 201);
    } catch (error) {
      logger.error('Failed to create shipment', error, {
        correlationId: req.correlationId,
        userId: req.user?.id,
        orderId: req.body.orderId
      });

      apiGateway.sendErrorResponse(res, {
        code: 'SHIPMENT_CREATION_FAILED',
        message: error instanceof Error ? error.message : 'Failed to create shipment',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Update delivery status (Admin/Delivery Partner)
 * PUT /api/v1/deliveries/:shipmentId/status
 */
router.put('/:shipmentId/status',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { shipmentId } = req.params;
      const { status, location, notes } = req.body;

      if (!status) {
        return apiGateway.sendErrorResponse(res, {
          code: 'MISSING_STATUS',
          message: 'Status is required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const validStatuses = ['PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'];
      if (!validStatuses.includes(status.toUpperCase())) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_STATUS',
          message: `Invalid status. Valid statuses: ${validStatuses.join(', ')}`,
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const updateRequest: UpdateDeliveryStatusRequest = {
        shipmentId,
        status: status.toUpperCase(),
        location,
        notes
      };

      const delivery = await deliveryService.updateDeliveryStatus(updateRequest);

      logger.info('Delivery status updated via API', {
        shipmentId,
        status: status.toUpperCase(),
        location,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, delivery);
    } catch (error) {
      logger.error('Failed to update delivery status', error, {
        correlationId: req.correlationId,
        shipmentId: req.params.shipmentId,
        status: req.body.status
      });

      apiGateway.sendErrorResponse(res, {
        code: 'STATUS_UPDATE_FAILED',
        message: error instanceof Error ? error.message : 'Failed to update delivery status',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Get tracking information
 * GET /api/v1/deliveries/:shipmentId/tracking
 */
router.get('/:shipmentId/tracking', async (req: AuthenticatedRequest, res) => {
  try {
    const { shipmentId } = req.params;

    const trackingInfo = await deliveryService.getTrackingInfo(shipmentId);

    if (!trackingInfo) {
      return apiGateway.sendErrorResponse(res, {
        code: 'SHIPMENT_NOT_FOUND',
        message: 'Shipment not found',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    }

    apiGateway.sendSuccessResponse(res, trackingInfo);
  } catch (error) {
    logger.error('Failed to get tracking info', error, {
      correlationId: req.correlationId,
      shipmentId: req.params.shipmentId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'TRACKING_RETRIEVAL_FAILED',
      message: 'Failed to retrieve tracking information',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get delivery by order ID
 * GET /api/v1/deliveries/order/:orderId
 */
router.get('/order/:orderId', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;

    const delivery = await deliveryService.getDeliveryByOrderId(orderId);

    if (!delivery) {
      return apiGateway.sendErrorResponse(res, {
        code: 'DELIVERY_NOT_FOUND',
        message: 'No delivery found for this order',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    }

    apiGateway.sendSuccessResponse(res, delivery);
  } catch (error) {
    logger.error('Failed to get delivery by order ID', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'DELIVERY_RETRIEVAL_FAILED',
      message: 'Failed to retrieve delivery information',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get all deliveries (Admin only)
 * GET /api/v1/deliveries
 */
router.get('/',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { status } = req.query;

      let deliveries;
      if (status) {
        const validStatuses = ['PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'];
        if (!validStatuses.includes(status.toString().toUpperCase())) {
          return apiGateway.sendErrorResponse(res, {
            code: 'INVALID_STATUS_FILTER',
            message: `Invalid status filter. Valid statuses: ${validStatuses.join(', ')}`,
            timestamp: new Date(),
            correlationId: req.correlationId,
            retryable: false
          }, 400);
        }

        deliveries = await deliveryService.getDeliveriesByStatus(status.toString().toUpperCase() as any);
      } else {
        deliveries = await deliveryService.getAllDeliveries();
      }

      apiGateway.sendSuccessResponse(res, {
        deliveries,
        count: deliveries.length,
        filter: status ? { status: status.toString().toUpperCase() } : null
      });
    } catch (error) {
      logger.error('Failed to get deliveries', error, {
        correlationId: req.correlationId,
        status: req.query.status
      });

      apiGateway.sendErrorResponse(res, {
        code: 'DELIVERIES_RETRIEVAL_FAILED',
        message: 'Failed to retrieve deliveries',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Cancel delivery (Admin only)
 * PUT /api/v1/deliveries/:shipmentId/cancel
 */
router.put('/:shipmentId/cancel',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { shipmentId } = req.params;
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

      const delivery = await deliveryService.cancelDelivery(shipmentId, reason);

      logger.info('Delivery cancelled via API', {
        shipmentId,
        reason,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, delivery);
    } catch (error) {
      logger.error('Failed to cancel delivery', error, {
        correlationId: req.correlationId,
        shipmentId: req.params.shipmentId,
        reason: req.body.reason
      });

      apiGateway.sendErrorResponse(res, {
        code: 'DELIVERY_CANCELLATION_FAILED',
        message: error instanceof Error ? error.message : 'Failed to cancel delivery',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Get delivery statistics (Admin only)
 * GET /api/v1/deliveries/statistics
 */
router.get('/statistics',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const statistics = await deliveryService.getDeliveryStatistics();

      apiGateway.sendSuccessResponse(res, {
        statistics,
        generatedAt: new Date()
      });
    } catch (error) {
      logger.error('Failed to get delivery statistics', error, {
        correlationId: req.correlationId
      });

      apiGateway.sendErrorResponse(res, {
        code: 'STATISTICS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve delivery statistics',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

export default router;