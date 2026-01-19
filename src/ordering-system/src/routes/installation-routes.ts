/**
 * Installation API Routes
 * Provides REST endpoints for consumer-controlled installation management
 */

import { Router } from 'express';
import { 
  installationService, 
  RequestInstallationRequest, 
  ScheduleInstallationRequest, 
  CompleteInstallationRequest 
} from '../services/installation-service';
import { apiGateway, AuthenticatedRequest } from '../infrastructure/api-gateway';
import { Logger } from '../infrastructure/logger';

const router = Router();
const logger = new Logger('InstallationRoutes');

/**
 * Request technician installation (Consumer only)
 * POST /api/v1/installations/request
 */
router.post('/request', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId, preferredDate, notes } = req.body;

    if (!orderId) {
      return apiGateway.sendErrorResponse(res, {
        code: 'MISSING_ORDER_ID',
        message: 'Order ID is required',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }

    const requestInstallation: RequestInstallationRequest = {
      orderId,
      consumerId: req.user!.id,
      preferredDate: preferredDate ? new Date(preferredDate) : undefined,
      notes
    };

    const installation = await installationService.requestInstallation(requestInstallation);

    logger.info('Installation requested via API', {
      orderId,
      installationId: installation.id,
      consumerId: req.user!.id,
      preferredDate,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, {
      installation,
      message: 'Installation request submitted successfully'
    }, 201);
  } catch (error) {
    logger.error('Failed to request installation', error, {
      correlationId: req.correlationId,
      userId: req.user?.id,
      orderId: req.body.orderId
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
 * Schedule installation (Admin only)
 * POST /api/v1/installations/:installationId/schedule
 */
router.post('/:installationId/schedule',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { installationId } = req.params;
      const { technicianId, scheduledDate, notes } = req.body;

      if (!technicianId || !scheduledDate) {
        return apiGateway.sendErrorResponse(res, {
          code: 'MISSING_REQUIRED_FIELDS',
          message: 'Technician ID and scheduled date are required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const scheduleRequest: ScheduleInstallationRequest = {
        installationId,
        technicianId,
        scheduledDate: new Date(scheduledDate),
        notes
      };

      const installation = await installationService.scheduleInstallation(scheduleRequest);

      logger.info('Installation scheduled via API', {
        installationId,
        technicianId,
        scheduledDate,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        installation,
        message: 'Installation scheduled successfully'
      });
    } catch (error) {
      logger.error('Failed to schedule installation', error, {
        correlationId: req.correlationId,
        installationId: req.params.installationId,
        technicianId: req.body.technicianId
      });

      apiGateway.sendErrorResponse(res, {
        code: 'INSTALLATION_SCHEDULING_FAILED',
        message: error instanceof Error ? error.message : 'Failed to schedule installation',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Complete installation (Technician only)
 * POST /api/v1/installations/:installationId/complete
 */
router.post('/:installationId/complete',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['technician']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { installationId } = req.params;
      const { deviceId, calibrationData, photos, notes } = req.body;

      if (!deviceId) {
        return apiGateway.sendErrorResponse(res, {
          code: 'MISSING_DEVICE_ID',
          message: 'Device ID is required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const completeRequest: CompleteInstallationRequest = {
        installationId,
        deviceId,
        calibrationData,
        photos,
        notes
      };

      const installation = await installationService.completeInstallation(completeRequest);

      logger.info('Installation completed via API', {
        installationId,
        deviceId,
        technicianId: req.user!.id,
        correlationId: req.correlationId
      });

      apiGateway.sendSuccessResponse(res, {
        installation,
        message: 'Installation completed successfully'
      });
    } catch (error) {
      logger.error('Failed to complete installation', error, {
        correlationId: req.correlationId,
        installationId: req.params.installationId,
        deviceId: req.body.deviceId,
        technicianId: req.user?.id
      });

      apiGateway.sendErrorResponse(res, {
        code: 'INSTALLATION_COMPLETION_FAILED',
        message: error instanceof Error ? error.message : 'Failed to complete installation',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 400);
    }
  }
);

/**
 * Get installation by order ID
 * GET /api/v1/installations/order/:orderId
 */
router.get('/order/:orderId', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { orderId } = req.params;

    const installation = await installationService.getInstallationByOrderId(orderId);

    if (!installation) {
      return apiGateway.sendErrorResponse(res, {
        code: 'INSTALLATION_NOT_FOUND',
        message: 'No installation found for this order',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 404);
    }

    // Check if user has access to this installation
    if (installation.consumerId !== req.user!.id && 
        installation.technicianId !== req.user!.id && 
        req.user!.role !== 'admin') {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'Access denied',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }

    apiGateway.sendSuccessResponse(res, installation);
  } catch (error) {
    logger.error('Failed to get installation by order ID', error, {
      correlationId: req.correlationId,
      orderId: req.params.orderId
    });

    apiGateway.sendErrorResponse(res, {
      code: 'INSTALLATION_RETRIEVAL_FAILED',
      message: 'Failed to retrieve installation information',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get user's installations (Consumer/Technician)
 * GET /api/v1/installations/my
 */
router.get('/my', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    let installations;

    if (req.user!.role === 'consumer') {
      installations = await installationService.getInstallationsByConsumer(req.user!.id);
    } else if (req.user!.role === 'technician') {
      installations = await installationService.getInstallationsByTechnician(req.user!.id);
    } else if (req.user!.role === 'admin') {
      installations = await installationService.getAllInstallations();
    } else {
      return apiGateway.sendErrorResponse(res, {
        code: 'INVALID_USER_ROLE',
        message: 'Invalid user role for this operation',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }

    apiGateway.sendSuccessResponse(res, {
      installations,
      count: installations.length
    });
  } catch (error) {
    logger.error('Failed to get user installations', error, {
      correlationId: req.correlationId,
      userId: req.user?.id,
      userRole: req.user?.role
    });

    apiGateway.sendErrorResponse(res, {
      code: 'INSTALLATIONS_RETRIEVAL_FAILED',
      message: 'Failed to retrieve installations',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: true
    }, 500);
  }
});

/**
 * Get installations by status (Admin only)
 * GET /api/v1/installations/status/:status
 */
router.get('/status/:status',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { status } = req.params;

      const validStatuses = ['NOT_REQUESTED', 'REQUESTED', 'SCHEDULED', 'COMPLETED', 'CANCELLED'];
      if (!validStatuses.includes(status.toUpperCase())) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_STATUS',
          message: `Invalid status. Valid statuses: ${validStatuses.join(', ')}`,
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const installations = await installationService.getInstallationsByStatus(status.toUpperCase() as any);

      apiGateway.sendSuccessResponse(res, {
        installations,
        count: installations.length,
        status: status.toUpperCase()
      });
    } catch (error) {
      logger.error('Failed to get installations by status', error, {
        correlationId: req.correlationId,
        status: req.params.status
      });

      apiGateway.sendErrorResponse(res, {
        code: 'INSTALLATIONS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve installations by status',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Get available technicians for a date (Admin only)
 * GET /api/v1/installations/technicians/available
 */
router.get('/technicians/available',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const { date } = req.query;

      if (!date) {
        return apiGateway.sendErrorResponse(res, {
          code: 'MISSING_DATE',
          message: 'Date parameter is required',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const requestedDate = new Date(date.toString());
      if (isNaN(requestedDate.getTime())) {
        return apiGateway.sendErrorResponse(res, {
          code: 'INVALID_DATE',
          message: 'Invalid date format',
          timestamp: new Date(),
          correlationId: req.correlationId,
          retryable: false
        }, 400);
      }

      const availableTechnicians = await installationService.getAvailableTechnicians(requestedDate);

      apiGateway.sendSuccessResponse(res, {
        technicians: availableTechnicians,
        count: availableTechnicians.length,
        date: requestedDate.toISOString()
      });
    } catch (error) {
      logger.error('Failed to get available technicians', error, {
        correlationId: req.correlationId,
        date: req.query.date
      });

      apiGateway.sendErrorResponse(res, {
        code: 'TECHNICIANS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve available technicians',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

/**
 * Cancel installation (Admin/Consumer)
 * PUT /api/v1/installations/:installationId/cancel
 */
router.put('/:installationId/cancel', apiGateway.authenticationMiddleware, async (req: AuthenticatedRequest, res) => {
  try {
    const { installationId } = req.params;
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

    // Check if user has permission to cancel this installation
    const installation = await installationService.getInstallationByOrderId(req.params.installationId);
    if (installation && 
        installation.consumerId !== req.user!.id && 
        req.user!.role !== 'admin') {
      return apiGateway.sendErrorResponse(res, {
        code: 'ACCESS_DENIED',
        message: 'You can only cancel your own installations',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: false
      }, 403);
    }

    const cancelledInstallation = await installationService.cancelInstallation(
      installationId, 
      req.user!.id, 
      reason
    );

    logger.info('Installation cancelled via API', {
      installationId,
      cancelledBy: req.user!.id,
      reason,
      correlationId: req.correlationId
    });

    apiGateway.sendSuccessResponse(res, {
      installation: cancelledInstallation,
      message: 'Installation cancelled successfully'
    });
  } catch (error) {
    logger.error('Failed to cancel installation', error, {
      correlationId: req.correlationId,
      installationId: req.params.installationId,
      userId: req.user?.id
    });

    apiGateway.sendErrorResponse(res, {
      code: 'INSTALLATION_CANCELLATION_FAILED',
      message: error instanceof Error ? error.message : 'Failed to cancel installation',
      timestamp: new Date(),
      correlationId: req.correlationId,
      retryable: false
    }, 400);
  }
});

/**
 * Get installation statistics (Admin only)
 * GET /api/v1/installations/statistics
 */
router.get('/statistics',
  apiGateway.authenticationMiddleware,
  apiGateway.authorizationMiddleware(['admin']),
  async (req: AuthenticatedRequest, res) => {
    try {
      const statistics = await installationService.getInstallationStatistics();

      apiGateway.sendSuccessResponse(res, {
        statistics,
        generatedAt: new Date()
      });
    } catch (error) {
      logger.error('Failed to get installation statistics', error, {
        correlationId: req.correlationId
      });

      apiGateway.sendErrorResponse(res, {
        code: 'STATISTICS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve installation statistics',
        timestamp: new Date(),
        correlationId: req.correlationId,
        retryable: true
      }, 500);
    }
  }
);

export default router;