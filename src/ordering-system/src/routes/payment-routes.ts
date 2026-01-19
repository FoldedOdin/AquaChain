/**
 * Payment API Routes
 * Provides REST endpoints for payment processing and Razorpay integration
 */

import { Router } from 'express';
import { paymentService, CreatePaymentOrderRequest, ProcessPaymentRequest } from '../services/payment-service';
import { webhookService } from '../services/webhook-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('PaymentRoutes');

/**
 * Create payment order
 * POST /api/v1/payments/create-order
 */
router.post('/create-order', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId, amount, currency, notes } = req.body;

    if (!orderId || !amount) {
      return apiGateway.sendErrorResponse(res, {
        code: 'MISSING_REQUIRED_FIELDS',
        message: 'Order ID and amount are required',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }

    if (amount <= 0) {
      return apiGateway.sendErrorResponse(res, {
        code: 'INVALID_AMOUNT',
        message: 'Amount must be positive',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }

    const createRequest: CreatePaymentOrderRequest = {
      orderId,
      amount,
      currency,
      notes: {
        userId: req.user!.id,
        ...notes
      }
    };

    const result = await paymentService.createPaymentOrder(createRequest);

    logger.info('Payment order created via API', {
      paymentId: result.payment.id,
      orderId,
      amount,
      razorpayOrderId: result.razorpayOrder.id,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, {
      payment: result.payment,
      razorpayOrder: {
        id: result.razorpayOrder.id,
        amount: result.razorpayOrder.amount,
        currency: result.razorpayOrder.currency,
        receipt: result.razorpayOrder.receipt
      }
    }, 201);
  } catch (error) {
    logger.error('Failed to create payment order', error, {
      correlationId: req.correlationId,
      userId: req.user?.id,
      orderId: req.body.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'PAYMENT_ORDER_CREATION_FAILED',
      message: error instanceof Error ? error.message : 'Failed to create payment order',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Process payment completion
 * POST /api/v1/payments/process
 */
router.post('/process', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId, razorpayPaymentId, razorpayOrderId, razorpaySignature } = req.body;

    if (!orderId || !razorpayPaymentId || !razorpayOrderId || !razorpaySignature) {
      return apiGateway.sendErrorResponse(res, {
        code: 'MISSING_PAYMENT_DETAILS',
        message: 'All payment details are required',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }

    const processRequest: ProcessPaymentRequest = {
      orderId,
      razorpayPaymentId,
      razorpayOrderId,
      razorpaySignature
    };

    const payment = await paymentService.processPayment(processRequest);

    logger.info('Payment processed via API', {
      paymentId: payment.id,
      orderId,
      razorpayPaymentId,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, {
      payment,
      message: 'Payment processed successfully'
    });
  } catch (error) {
    logger.error('Failed to process payment', error, {
      correlationId: req.correlationId,
      userId: req.user?.id,
      orderId: req.body.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'PAYMENT_PROCESSING_FAILED',
      message: error instanceof Error ? error.message : 'Failed to process payment',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Convert COD to online payment
 * POST /api/v1/payments/:orderId/convert-cod
 */
router.post('/:orderId/convert-cod', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;

    const result = await paymentService.convertCODToOnline(orderId);

    logger.info('COD conversion initiated via API', {
      orderId,
      newPaymentId: result.payment.id,
      razorpayOrderId: result.razorpayOrder.id,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, {
      payment: result.payment,
      razorpayOrder: {
        id: result.razorpayOrder.id,
        amount: result.razorpayOrder.amount,
        currency: result.razorpayOrder.currency,
        receipt: result.razorpayOrder.receipt
      },
      message: 'COD conversion initiated successfully'
    });
  } catch (error) {
    logger.error('Failed to convert COD payment', error, {
      correlationId: req.correlationId,
      userId: req.user?.id,
      orderId: req.params.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'COD_CONVERSION_FAILED',
      message: error instanceof Error ? error.message : 'Failed to convert COD payment',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Get payment status
 * GET /api/v1/payments/:orderId/status
 */
router.get('/:orderId/status', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;

    const paymentStatus = await paymentService.getPaymentStatus(orderId);

    apiGateway.sendSuccessResponse(res, {
      orderId,
      ...paymentStatus
    });
  } catch (error) {
    logger.error('Failed to get payment status', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'PAYMENT_STATUS_RETRIEVAL_FAILED',
      message: 'Failed to retrieve payment status',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Razorpay webhook endpoint
 * POST /api/v1/payments/webhook
 */
router.post('/webhook', async (req, res) => {
  try {
    const signature = req.headers['x-razorpay-signature'] as string;
    const payload = JSON.stringify(req.body);
    const headers = req.headers as Record<string, string>;

    if (!signature) {
      logger.security('Webhook received without signature', 'high', {
        sourceIP: req.ip,
        userAgent: req.headers['user-agent']
      });

      return res.status(400).json({
        success: false,
        error: 'Missing webhook signature'
      });
    }

    const result = await webhookService.processWebhook(payload, signature, headers);

    if (result.success) {
      logger.info('Webhook processed successfully', {
        eventId: result.eventId,
        processed: result.processed,
        duplicate: result.duplicate
      });

      res.status(200).json({
        success: true,
        message: result.message,
        eventId: result.eventId
      });
    } else {
      logger.error('Webhook processing failed', new Error(result.message), {
        eventId: result.eventId
      });

      res.status(400).json({
        success: false,
        error: result.message,
        eventId: result.eventId
      });
    }
  } catch (error) {
    logger.error('Webhook endpoint error', error, {
      sourceIP: req.ip,
      userAgent: req.headers['user-agent']
    });

    res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
});

/**
 * Get payment statistics (Admin only)
 * GET /api/v1/payments/statistics
 */
router.get('/statistics',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const paymentStats = await paymentService.getPaymentStatistics();
      const webhookStats = webhookService.getWebhookStatistics();

      apiGateway.sendSuccessResponse(res, {
        payments: paymentStats,
        webhooks: webhookStats,
        generatedAt: new Date()
      });
    } catch (error) {
      logger.error('Failed to get payment statistics', error, {
        correlationId: req.correlationId,
        adminId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'STATISTICS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve payment statistics',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

export default router;