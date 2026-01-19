/**
 * Consumer Dashboard API Routes
 * Provides endpoints for consumer dashboard with payment options and installation requests
 * Implements Requirements 3.1, 5.1
 */

import { Router } from 'express';
import { orderService } from '../services/order-service';
import { paymentService } from '../services/payment-service';
import { deliveryService } from '../services/delivery-service';
import { installationService } from '../services/installation-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('ConsumerDashboardRoutes');

/**
 * Consumer Dashboard Data Interface
 */
interface DashboardOrderData {
  order: any;
  payment: any;
  delivery: any;
  installation: any;
  availableActions: {
    canPayOnline: boolean;
    canRequestInstallation: boolean;
    canCancelOrder: boolean;
  };
}

/**
 * Get consumer dashboard with order status and available actions
 * GET /api/v1/consumer/dashboard
 * Implements Requirements 3.1, 5.1 - Order status display with payment options
 */
router.get('/dashboard', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const consumerId = req.user!.id;
    
    // Get consumer's orders
    const orders = await orderService.getOrdersByConsumer(consumerId);
    
    // Build dashboard data for each order
    const dashboardData: DashboardOrderData[] = [];
    
    for (const order of orders) {
      // Get payment information
      const payment = await paymentService.getPaymentByOrderId(order.id);
      
      // Get delivery information
      const delivery = await deliveryService.getDeliveryByOrderId(order.id);
      
      // Get installation information
      const installation = await installationService.getInstallationByOrderId(order.id);
      
      // Determine available actions based on current state
      const availableActions = {
        canPayOnline: false,
        canRequestInstallation: false,
        canCancelOrder: false
      };
      
      // Check if "Pay Online Now" option should be available (Requirement 3.1)
      // Available when: delivery status is OUT_FOR_DELIVERY AND payment method is COD
      if (delivery && 
          delivery.status === 'OUT_FOR_DELIVERY' && 
          payment && 
          payment.paymentMethod === 'COD' && 
          payment.status === 'COD_PENDING') {
        availableActions.canPayOnline = true;
      }
      
      // Check if "Request Technician Installation" should be available (Requirement 5.1)
      // Available when: delivery status is DELIVERED AND installation is NOT_REQUESTED or null
      if (delivery && 
          delivery.status === 'DELIVERED' && 
          (!installation || installation.status === 'NOT_REQUESTED')) {
        availableActions.canRequestInstallation = true;
      }
      
      // Check if order can be cancelled
      if (order.status === 'PENDING') {
        availableActions.canCancelOrder = true;
      }
      
      dashboardData.push({
        order,
        payment,
        delivery,
        installation,
        availableActions
      });
    }
    
    // Sort orders by creation date (newest first)
    dashboardData.sort((a, b) => 
      new Date(b.order.createdAt).getTime() - new Date(a.order.createdAt).getTime()
    );
    
    logger.info('Consumer dashboard data retrieved', {
      consumerId,
      orderCount: dashboardData.length,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, {
      orders: dashboardData,
      summary: {
        totalOrders: dashboardData.length,
        pendingOrders: dashboardData.filter(d => d.order.status === 'PENDING').length,
        approvedOrders: dashboardData.filter(d => d.order.status === 'APPROVED').length,
        completedOrders: dashboardData.filter(d => d.order.status === 'COMPLETED').length,
        ordersWithPaymentOption: dashboardData.filter(d => d.availableActions.canPayOnline).length,
        ordersWithInstallationOption: dashboardData.filter(d => d.availableActions.canRequestInstallation).length
      }
    });
    
  } catch (error) {
    logger.error('Failed to get consumer dashboard', error, {
      correlationId: req.correlationId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'DASHBOARD_RETRIEVAL_FAILED',
      message: 'Failed to retrieve dashboard data',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get detailed order status for a specific order
 * GET /api/v1/consumer/orders/:orderId/status
 */
router.get('/orders/:orderId/status', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const consumerId = req.user!.id;
    
    // Get order and verify ownership
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
    
    if (order.consumerId !== consumerId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'Access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }
    
    // Get related data
    const payment = await paymentService.getPaymentByOrderId(orderId);
    const delivery = await deliveryService.getDeliveryByOrderId(orderId);
    const installation = await installationService.getInstallationByOrderId(orderId);
    
    // Get tracking info if delivery exists
    let trackingInfo = null;
    if (delivery) {
      trackingInfo = await deliveryService.getTrackingInfo(delivery.shipmentId);
    }
    
    // Determine current stage and next steps
    const currentStage = determineCurrentStage(order, payment, delivery, installation);
    const nextSteps = determineNextSteps(order, payment, delivery, installation);
    
    const statusData = {
      order,
      payment,
      delivery,
      installation,
      trackingInfo,
      currentStage,
      nextSteps,
      timeline: buildOrderTimeline(order, payment, delivery, installation)
    };
    
    logger.info('Order status retrieved', {
      orderId,
      consumerId,
      currentStage,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, statusData);
    
  } catch (error) {
    logger.error('Failed to get order status', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'ORDER_STATUS_RETRIEVAL_FAILED',
      message: 'Failed to retrieve order status',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Initiate COD to Online Payment conversion
 * POST /api/v1/consumer/orders/:orderId/pay-online
 * Implements Requirement 3.1 - "Pay Online Now" option for OUT_FOR_DELIVERY COD orders
 */
router.post('/orders/:orderId/pay-online', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const consumerId = req.user!.id;
    
    // Get order and verify ownership
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
    
    if (order.consumerId !== consumerId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'Access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }
    
    // Verify that COD to online conversion is allowed
    const delivery = await deliveryService.getDeliveryByOrderId(orderId);
    const payment = await paymentService.getPaymentByOrderId(orderId);
    
    if (!delivery || delivery.status !== 'OUT_FOR_DELIVERY') {
      return apiGateway.sendErrorResponse(res, {
        code: 'CONVERSION_NOT_ALLOWED',
        message: 'COD to online conversion is only available when order is out for delivery',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
    
    if (!payment || payment.paymentMethod !== 'COD' || payment.status !== 'COD_PENDING') {
      return apiGateway.sendErrorResponse(res, {
        code: 'CONVERSION_NOT_ALLOWED',
        message: 'Order is not eligible for COD to online conversion',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
    
    // Initiate COD to online conversion
    const conversionResult = await paymentService.convertCODToOnline(orderId);
    
    logger.info('COD to online conversion initiated', {
      orderId,
      consumerId,
      razorpayOrderId: conversionResult.razorpayOrder.id,
      amount: conversionResult.razorpayOrder.amount,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, {
      message: 'COD to online conversion initiated',
      razorpayOrder: conversionResult.razorpayOrder,
      payment: conversionResult.payment
    });
    
  } catch (error) {
    logger.error('Failed to initiate COD to online conversion', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'COD_CONVERSION_FAILED',
      message: error instanceof Error ? error.message : 'Failed to initiate COD to online conversion',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Request technician installation
 * POST /api/v1/consumer/orders/:orderId/request-installation
 * Implements Requirement 5.1 - "Request Technician Installation" for delivered orders
 */
router.post('/orders/:orderId/request-installation', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const consumerId = req.user!.id;
    const { preferredDate, notes } = req.body;
    
    // Get order and verify ownership
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
    
    if (order.consumerId !== consumerId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'Access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }
    
    // Verify that installation request is allowed
    const delivery = await deliveryService.getDeliveryByOrderId(orderId);
    
    if (!delivery || delivery.status !== 'DELIVERED') {
      return apiGateway.sendErrorResponse(res, {
        code: 'INSTALLATION_NOT_ALLOWED',
        message: 'Installation can only be requested after successful delivery',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
    
    // Parse preferred date if provided
    let parsedPreferredDate: Date | undefined;
    if (preferredDate) {
      parsedPreferredDate = new Date(preferredDate);
      if (isNaN(parsedPreferredDate.getTime())) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_DATE',
          message: 'Invalid preferred date format',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }
    }
    
    // Request installation
    const installation = await installationService.requestInstallation({
      orderId,
      consumerId,
      preferredDate: parsedPreferredDate,
      notes
    });
    
    logger.info('Installation requested by consumer', {
      orderId,
      consumerId,
      installationId: installation.id,
      preferredDate: parsedPreferredDate,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, {
      message: 'Installation request submitted successfully',
      installation,
      nextSteps: [
        'Your installation request has been received',
        'A technician will be assigned within 24 hours',
        'You will receive a confirmation with scheduled date and time',
        'The technician will contact you before the visit'
      ]
    }, 201);
    
  } catch (error) {
    logger.error('Failed to request installation', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'INSTALLATION_REQUEST_FAILED',
      message: error instanceof Error ? error.message : 'Failed to request installation',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Cancel order (Consumer)
 * PUT /api/v1/consumer/orders/:orderId/cancel
 * Allows consumers to cancel their own pending orders
 */
router.put('/orders/:orderId/cancel', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const { reason } = req.body;
    const consumerId = req.user!.id;
    
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
    
    // Get order and verify ownership
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
    
    if (order.consumerId !== consumerId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'You can only cancel your own orders',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }
    
    // Check if order can be cancelled (only PENDING orders can be cancelled by consumers)
    if (order.status !== 'PENDING') {
      return apiGateway.sendErrorResponse(res, {
        code: 'CANCELLATION_NOT_ALLOWED',
        message: 'Only pending orders can be cancelled. Please contact support for approved orders.',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
    
    // Cancel the order
    const cancelledOrder = await orderService.cancelOrder(orderId, consumerId, reason);
    
    logger.info('Order cancelled by consumer', {
      orderId,
      consumerId,
      reason,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, {
      message: 'Order cancelled successfully',
      order: cancelledOrder,
      refundInfo: {
        message: 'If you made an online payment, refund will be processed within 5-7 business days',
        supportContact: 'support@aquachain.com'
      }
    });
    
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
});

/**
 * Get available technicians for installation scheduling
 * GET /api/v1/consumer/orders/:orderId/available-technicians
 */
router.get('/orders/:orderId/available-technicians', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;
    const { date } = req.query;
    const consumerId = req.user!.id;
    
    // Verify order ownership
    const order = await orderService.getOrder(orderId);
    if (!order || order.consumerId !== consumerId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'ORDER_NOT_FOUND',
        message: 'Order not found or access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    }
    
    // Parse date
    const requestedDate = date ? new Date(date as string) : new Date();
    if (isNaN(requestedDate.getTime())) {
      return apiGateway.sendErrorResponse(res, {
        code: 'INVALID_DATE',
        message: 'Invalid date format',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
    
    // Get available technicians
    const availableTechnicians = await installationService.getAvailableTechnicians(requestedDate);
    
    logger.info('Available technicians retrieved', {
      orderId,
      consumerId,
      requestedDate,
      technicianCount: availableTechnicians.length,
      correlationId: req.correlationId
    });
    
    apiGateway.sendSuccessResponse(res, {
      date: requestedDate,
      availableTechnicians: availableTechnicians.map(tech => ({
        id: tech.id,
        name: tech.name,
        rating: tech.rating,
        completedInstallations: tech.completedInstallations,
        skills: tech.skills
      }))
    });
    
  } catch (error) {
    logger.error('Failed to get available technicians', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'TECHNICIANS_RETRIEVAL_FAILED',
      message: 'Failed to retrieve available technicians',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Helper method to determine current stage of order
 */
function determineCurrentStage(order: any, payment: any, delivery: any, installation: any): string {
  if (installation && installation.status === 'COMPLETED') {
    return 'INSTALLATION_COMPLETED';
  }
  
  if (installation && installation.status === 'SCHEDULED') {
    return 'INSTALLATION_SCHEDULED';
  }
  
  if (installation && installation.status === 'REQUESTED') {
    return 'INSTALLATION_REQUESTED';
  }
  
  if (delivery && delivery.status === 'DELIVERED') {
    return 'DELIVERED';
  }
  
  if (delivery && delivery.status === 'OUT_FOR_DELIVERY') {
    return 'OUT_FOR_DELIVERY';
  }
  
  if (delivery && delivery.status === 'SHIPPED') {
    return 'SHIPPED';
  }
  
  if (delivery && delivery.status === 'PREPARING') {
    return 'PREPARING_SHIPMENT';
  }
  
  if (order.status === 'APPROVED') {
    return 'APPROVED';
  }
  
  if (order.status === 'PENDING') {
    return 'PENDING_APPROVAL';
  }
  
  return 'UNKNOWN';
}

/**
 * Helper method to determine next steps for consumer
 */
function determineNextSteps(order: any, payment: any, delivery: any, installation: any): string[] {
  const steps: string[] = [];
  
  if (order.status === 'PENDING') {
    steps.push('Waiting for admin approval');
    steps.push('You will be notified once your order is approved');
  } else if (order.status === 'APPROVED' && (!delivery || delivery.status === 'PREPARING')) {
    steps.push('Your order is being prepared for shipment');
    steps.push('You will receive tracking information once shipped');
  } else if (delivery && delivery.status === 'SHIPPED') {
    steps.push('Your order is on the way');
    steps.push('Track your package using the tracking number provided');
  } else if (delivery && delivery.status === 'OUT_FOR_DELIVERY') {
    steps.push('Your order is out for delivery');
    if (payment && payment.paymentMethod === 'COD' && payment.status === 'COD_PENDING') {
      steps.push('You can pay online now to avoid cash handling');
    }
    steps.push('Prepare to receive your package');
  } else if (delivery && delivery.status === 'DELIVERED') {
    if (!installation || installation.status === 'NOT_REQUESTED') {
      steps.push('Your order has been delivered');
      steps.push('You can now request technician installation');
    } else if (installation.status === 'REQUESTED') {
      steps.push('Installation request received');
      steps.push('A technician will be assigned within 24 hours');
    } else if (installation.status === 'SCHEDULED') {
      steps.push('Installation scheduled');
      steps.push('Technician will contact you before the visit');
    }
  } else if (installation && installation.status === 'COMPLETED') {
    steps.push('Installation completed successfully');
    steps.push('Your AquaChain device is now active');
    steps.push('You can monitor water quality through the app');
  }
  
  return steps;
}

/**
 * Helper method to build order timeline
 */
function buildOrderTimeline(order: any, payment: any, delivery: any, installation: any): any[] {
  const timeline: any[] = [];
  
  // Order created
  timeline.push({
    stage: 'ORDER_CREATED',
    timestamp: order.createdAt,
    title: 'Order Placed',
    description: `Order for ${order.deviceType} placed successfully`,
    status: 'completed'
  });
  
  // Order approved
  if (order.approvedAt) {
    timeline.push({
      stage: 'ORDER_APPROVED',
      timestamp: order.approvedAt,
      title: 'Order Approved',
      description: `Order approved by admin with quote amount ₹${order.quoteAmount}`,
      status: 'completed'
    });
  } else if (order.status === 'PENDING') {
    timeline.push({
      stage: 'ORDER_APPROVAL',
      timestamp: null,
      title: 'Pending Approval',
      description: 'Waiting for admin approval',
      status: 'pending'
    });
  }
  
  // Shipment stages
  if (delivery) {
    if (delivery.status === 'PREPARING' || delivery.shippedAt || delivery.deliveredAt) {
      timeline.push({
        stage: 'SHIPMENT_PREPARING',
        timestamp: delivery.id, // Using creation time
        title: 'Preparing Shipment',
        description: 'Order is being prepared for shipment',
        status: delivery.status === 'PREPARING' ? 'current' : 'completed'
      });
    }
    
    if (delivery.shippedAt) {
      timeline.push({
        stage: 'SHIPPED',
        timestamp: delivery.shippedAt,
        title: 'Shipped',
        description: `Package shipped via ${delivery.carrier}. Tracking: ${delivery.trackingNumber}`,
        status: delivery.status === 'SHIPPED' ? 'current' : 'completed'
      });
    }
    
    if (delivery.status === 'OUT_FOR_DELIVERY') {
      timeline.push({
        stage: 'OUT_FOR_DELIVERY',
        timestamp: new Date(), // Would be actual timestamp in production
        title: 'Out for Delivery',
        description: 'Package is out for delivery',
        status: 'current'
      });
    }
    
    if (delivery.deliveredAt) {
      timeline.push({
        stage: 'DELIVERED',
        timestamp: delivery.deliveredAt,
        title: 'Delivered',
        description: 'Package delivered successfully',
        status: 'completed'
      });
    }
  }
  
  // Installation stages
  if (installation) {
    if (installation.requestedAt) {
      timeline.push({
        stage: 'INSTALLATION_REQUESTED',
        timestamp: installation.requestedAt,
        title: 'Installation Requested',
        description: 'Technician installation requested',
        status: installation.status === 'REQUESTED' ? 'current' : 'completed'
      });
    }
    
    if (installation.scheduledAt) {
      timeline.push({
        stage: 'INSTALLATION_SCHEDULED',
        timestamp: installation.scheduledAt,
        title: 'Installation Scheduled',
        description: `Installation scheduled for ${installation.scheduledDate}`,
        status: installation.status === 'SCHEDULED' ? 'current' : 'completed'
      });
    }
    
    if (installation.completedAt) {
      timeline.push({
        stage: 'INSTALLATION_COMPLETED',
        timestamp: installation.completedAt,
        title: 'Installation Completed',
        description: 'Device installed and activated successfully',
        status: 'completed'
      });
    }
  }
  
  return timeline.sort((a, b) => {
    if (!a.timestamp) return 1;
    if (!b.timestamp) return -1;
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });
}

export default router;