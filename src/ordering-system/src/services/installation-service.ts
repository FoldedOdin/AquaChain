/**
 * Installation Service
 * Manages consumer-controlled installation requests and technician assignments
 * Implements Requirements 5.2, 5.3, 5.4, 5.5
 */

import { v4 as uuidv4 } from 'uuid';
import { Installation, Technician, Device } from '../types/entities';
import { InstallationRequested, InstallationScheduled, InstallationCompleted, InstallationCancelled } from '../types/events';
import { EventTypes } from '../types/events';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';
import { concurrencyService } from './concurrency-service';

export type InstallationStatus = 'NOT_REQUESTED' | 'REQUESTED' | 'SCHEDULED' | 'COMPLETED' | 'CANCELLED';

export interface RequestInstallationRequest {
  orderId: string;
  consumerId: string;
  preferredDate?: Date;
  notes?: string;
}

export interface ScheduleInstallationRequest {
  installationId: string;
  technicianId: string;
  scheduledDate: Date;
  notes?: string;
}

export interface CompleteInstallationRequest {
  installationId: string;
  deviceId: string;
  calibrationData?: any;
  photos?: string[];
  notes?: string;
}

/**
 * Installation State Machine
 * Defines valid state transitions for installation workflow
 */
export class InstallationStateMachine {
  private static readonly VALID_TRANSITIONS: Record<InstallationStatus, InstallationStatus[]> = {
    NOT_REQUESTED: ['REQUESTED'],
    REQUESTED: ['SCHEDULED', 'CANCELLED'],
    SCHEDULED: ['COMPLETED', 'CANCELLED'],
    COMPLETED: [], // Terminal state
    CANCELLED: []  // Terminal state
  };

  /**
   * Check if state transition is valid
   */
  static isValidTransition(from: InstallationStatus, to: InstallationStatus): boolean {
    return this.VALID_TRANSITIONS[from].includes(to);
  }

  /**
   * Get valid next states for current state
   */
  static getValidNextStates(currentState: InstallationStatus): InstallationStatus[] {
    return [...this.VALID_TRANSITIONS[currentState]];
  }

  /**
   * Validate state transition and throw error if invalid
   */
  static validateTransition(from: InstallationStatus, to: InstallationStatus): void {
    if (!this.isValidTransition(from, to)) {
      throw new Error(
        `Invalid installation state transition from ${from} to ${to}. ` +
        `Valid transitions from ${from}: ${this.VALID_TRANSITIONS[from].join(', ')}`
      );
    }
  }
}

/**
 * Installation Service Implementation
 */
export class InstallationService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('InstallationService');
    this.setupEventHandlers();
  }

  /**
   * Setup event handlers for cross-service coordination
   */
  private setupEventHandlers(): void {
    // Listen for delivery completed events to enable installation requests
    eventBus.subscribe('DELIVERY_COMPLETED', async (event) => {
      await this.handleDeliveryCompleted(event);
    });

    this.logger.info('Installation service event handlers registered');
  }

  /**
   * Handle delivery completed event - make installation option available
   */
  private async handleDeliveryCompleted(event: any): Promise<void> {
    try {
      this.logger.info('Delivery completed, installation now available', {
        orderId: event.orderId,
        shipmentId: event.shipmentId
      });

      // Create installation record with version
      const installation: Installation = {
        id: uuidv4(),
        orderId: event.orderId,
        consumerId: '', // Would be populated from order data
        status: 'NOT_REQUESTED',
        version: 1 // Initialize version for optimistic locking
      };

      database.create<Installation>('installations', installation);

      this.logger.business('Installation option enabled', {
        orderId: event.orderId,
        installationId: installation.id
      });

    } catch (error) {
      this.logger.error('Failed to handle delivery completed event', error, {
        orderId: event.orderId
      });
    }
  }

  /**
   * Request technician installation (Consumer-controlled)
   * Implements Requirements 5.2, 5.5 - Consumer controls installation timing
   */
  async requestInstallation(request: RequestInstallationRequest): Promise<Installation> {
    this.logger.info('Processing installation request', {
      orderId: request.orderId,
      consumerId: request.consumerId,
      preferredDate: request.preferredDate
    });

    try {
      // Validate request
      this.validateInstallationRequest(request);

      // Check if installation already exists for this order
      let installation = database.findWhere<Installation>('installations', 
        i => i.orderId === request.orderId
      )[0];

      if (!installation) {
        // Create new installation record with version
        installation = {
          id: uuidv4(),
          orderId: request.orderId,
          consumerId: request.consumerId,
          status: 'NOT_REQUESTED',
          version: 1 // Initialize version for optimistic locking
        };
        installation = database.create<Installation>('installations', installation);
      }

      // Update installation using optimistic locking
      const updatedInstallation = await concurrencyService.withOptimisticLock<Installation>(
        'installations',
        installation.id,
        async (currentInstallation: Installation) => {
          // Validate state transition
          InstallationStateMachine.validateTransition(currentInstallation.status, 'REQUESTED');

          const now = new Date();

          // Create and publish installation requested event
          const installationRequestedEvent: InstallationRequested = {
            orderId: request.orderId,
            consumerId: request.consumerId,
            requestedAt: now,
            preferredDate: request.preferredDate
          };

          await eventBus.publish(
            request.orderId,
            'Installation',
            EventTypes.INSTALLATION_REQUESTED,
            installationRequestedEvent
          );

          this.logger.business('Installation requested by consumer with concurrency control', {
            orderId: request.orderId,
            installationId: currentInstallation.id,
            consumerId: request.consumerId,
            preferredDate: request.preferredDate,
            oldVersion: currentInstallation.version,
            newVersion: currentInstallation.version + 1
          });

          return {
            status: 'REQUESTED',
            requestedAt: now,
            scheduledDate: request.preferredDate
          };
        },
        'requestInstallation'
      );

      return updatedInstallation;

    } catch (error) {
      this.logger.error('Failed to request installation', error, {
        orderId: request.orderId,
        consumerId: request.consumerId
      });
      throw error;
    }
  }

  /**
   * Schedule installation with technician assignment using optimistic locking
   * Implements Requirements 5.3, 9.2 - Assign available technician and update to SCHEDULED
   */
  async scheduleInstallation(request: ScheduleInstallationRequest): Promise<Installation> {
    this.logger.info('Scheduling installation with concurrency control', {
      installationId: request.installationId,
      technicianId: request.technicianId,
      scheduledDate: request.scheduledDate
    });

    // Validate technician availability first (outside the lock)
    const technician = await this.validateTechnicianAvailability(request.technicianId, request.scheduledDate);

    return concurrencyService.withOptimisticLock<Installation>(
      'installations',
      request.installationId,
      async (installation: Installation) => {
        // Validate state transition
        InstallationStateMachine.validateTransition(installation.status, 'SCHEDULED');

        const now = new Date();

        // Create and publish installation scheduled event
        const installationScheduledEvent: InstallationScheduled = {
          orderId: installation.orderId,
          installationId: request.installationId,
          technicianId: request.technicianId,
          scheduledDate: request.scheduledDate,
          scheduledAt: now
        };

        await eventBus.publish(
          installation.orderId,
          'Installation',
          EventTypes.INSTALLATION_SCHEDULED,
          installationScheduledEvent
        );

        this.logger.business('Installation scheduled with concurrency control', {
          orderId: installation.orderId,
          installationId: request.installationId,
          technicianId: request.technicianId,
          technicianName: technician.name,
          scheduledDate: request.scheduledDate,
          oldVersion: installation.version,
          newVersion: installation.version + 1
        });

        return {
          status: 'SCHEDULED',
          technicianId: request.technicianId,
          scheduledAt: now,
          scheduledDate: request.scheduledDate
        };
      },
      'scheduleInstallation'
    );
  }

  /**
   * Complete installation and transfer device ownership using optimistic locking
   * Implements Requirements 5.4, 9.2 - Transfer device ownership and set device status to ACTIVE
   */
  async completeInstallation(request: CompleteInstallationRequest): Promise<Installation> {
    this.logger.info('Completing installation with concurrency control', {
      installationId: request.installationId,
      deviceId: request.deviceId
    });

    // Validate device first (outside the lock)
    const device = await this.validateDeviceForInstallation(request.deviceId);

    return concurrencyService.withOptimisticLock<Installation>(
      'installations',
      request.installationId,
      async (installation: Installation) => {
        // Validate state transition
        InstallationStateMachine.validateTransition(installation.status, 'COMPLETED');

        const now = new Date();

        // Transfer device ownership and set to ACTIVE (Requirement 5.4)
        await this.transferDeviceOwnership(request.deviceId, installation.consumerId);

        // Create and publish installation completed event
        const installationCompletedEvent: InstallationCompleted = {
          orderId: installation.orderId,
          installationId: request.installationId,
          deviceId: request.deviceId,
          technicianId: installation.technicianId!,
          completedAt: now,
          calibrationData: request.calibrationData,
          photos: request.photos
        };

        await eventBus.publish(
          installation.orderId,
          'Installation',
          EventTypes.INSTALLATION_COMPLETED,
          installationCompletedEvent
        );

        this.logger.business('Installation completed with concurrency control', {
          orderId: installation.orderId,
          installationId: request.installationId,
          deviceId: request.deviceId,
          technicianId: installation.technicianId,
          consumerId: installation.consumerId,
          oldVersion: installation.version,
          newVersion: installation.version + 1
        });

        return {
          status: 'COMPLETED',
          deviceId: request.deviceId,
          completedAt: now,
          calibrationData: request.calibrationData,
          photos: request.photos
        };
      },
      'completeInstallation'
    );
  }

  /**
   * Cancel installation
   */
  async cancelInstallation(installationId: string, cancelledBy: string, reason: string): Promise<Installation> {
    this.logger.info('Cancelling installation', {
      installationId,
      cancelledBy,
      reason
    });

    try {
      // Get installation
      const installation = database.findById<Installation>('installations', installationId);
      if (!installation) {
        throw new Error(`Installation not found: ${installationId}`);
      }

      // Validate state transition
      InstallationStateMachine.validateTransition(installation.status, 'CANCELLED');

      // Update installation
      const updatedInstallation = database.update<Installation>('installations', installationId, {
        status: 'CANCELLED',
        cancelledAt: new Date(),
        cancelReason: reason
      });

      if (!updatedInstallation) {
        throw new Error('Failed to cancel installation');
      }

      // Create and publish installation cancelled event
      const installationCancelledEvent: InstallationCancelled = {
        orderId: installation.orderId,
        installationId,
        cancelledBy,
        cancelledAt: new Date(),
        reason
      };

      await eventBus.publish(
        installation.orderId,
        'Installation',
        EventTypes.INSTALLATION_CANCELLED,
        installationCancelledEvent
      );

      this.logger.business('Installation cancelled', {
        orderId: installation.orderId,
        installationId,
        cancelledBy,
        reason
      });

      return updatedInstallation;

    } catch (error) {
      this.logger.error('Failed to cancel installation', error, {
        installationId,
        cancelledBy,
        reason
      });
      throw error;
    }
  }

  /**
   * Get installation by order ID
   */
  async getInstallationByOrderId(orderId: string): Promise<Installation | null> {
    const installations = database.findWhere<Installation>('installations', i => i.orderId === orderId);
    return installations.length > 0 ? installations[0] : null;
  }

  /**
   * Get installations by consumer ID
   */
  async getInstallationsByConsumer(consumerId: string): Promise<Installation[]> {
    return database.findWhere<Installation>('installations', i => i.consumerId === consumerId);
  }

  /**
   * Get installations by technician ID
   */
  async getInstallationsByTechnician(technicianId: string): Promise<Installation[]> {
    return database.findWhere<Installation>('installations', i => i.technicianId === technicianId);
  }

  /**
   * Get installations by status
   */
  async getInstallationsByStatus(status: InstallationStatus): Promise<Installation[]> {
    return database.findWhere<Installation>('installations', i => i.status === status);
  }

  /**
   * Get all installations
   */
  async getAllInstallations(): Promise<Installation[]> {
    return database.findAll<Installation>('installations');
  }

  /**
   * Get available technicians for a given date
   */
  async getAvailableTechnicians(date: Date): Promise<Technician[]> {
    // Get all technicians
    const allTechnicians = database.findAll<Technician>('technicians');
    
    // Filter by availability (simplified logic)
    const availableTechnicians = allTechnicians.filter(tech => {
      // Check if technician is available on the given date
      const scheduledInstallations = database.findWhere<Installation>('installations', 
        i => i.technicianId === tech.id && 
             i.status === 'SCHEDULED' && 
             i.scheduledDate && 
             this.isSameDay(new Date(i.scheduledDate), date)
      );
      
      // Assume technician can handle max 2 installations per day
      return scheduledInstallations.length < 2;
    });

    return availableTechnicians;
  }

  /**
   * Validate installation request
   */
  private validateInstallationRequest(request: RequestInstallationRequest): void {
    const errors: string[] = [];

    if (!request.orderId?.trim()) {
      errors.push('Order ID is required');
    }

    if (!request.consumerId?.trim()) {
      errors.push('Consumer ID is required');
    }

    if (request.preferredDate && request.preferredDate < new Date()) {
      errors.push('Preferred date cannot be in the past');
    }

    if (errors.length > 0) {
      throw new Error(`Installation request validation failed: ${errors.join(', ')}`);
    }
  }

  /**
   * Validate technician availability
   */
  private async validateTechnicianAvailability(technicianId: string, scheduledDate: Date): Promise<Technician> {
    // Get technician
    const technician = database.findById<Technician>('technicians', technicianId);
    if (!technician) {
      throw new Error(`Technician not found: ${technicianId}`);
    }

    if (technician.availability !== 'AVAILABLE') {
      throw new Error(`Technician ${technician.name} is not available`);
    }

    // Check if technician is already scheduled for this date
    const existingInstallations = database.findWhere<Installation>('installations', 
      i => i.technicianId === technicianId && 
           i.status === 'SCHEDULED' && 
           i.scheduledDate && 
           this.isSameDay(new Date(i.scheduledDate), scheduledDate)
    );

    if (existingInstallations.length >= 2) { // Max 2 installations per day
      throw new Error(`Technician ${technician.name} is fully booked on ${scheduledDate.toDateString()}`);
    }

    return technician;
  }

  /**
   * Validate device for installation
   */
  private async validateDeviceForInstallation(deviceId: string): Promise<Device> {
    const device = database.findById<Device>('devices', deviceId);
    if (!device) {
      throw new Error(`Device not found: ${deviceId}`);
    }

    if (device.status !== 'AVAILABLE') {
      throw new Error(`Device ${deviceId} is not available for installation. Status: ${device.status}`);
    }

    return device;
  }

  /**
   * Transfer device ownership to consumer and set status to ACTIVE
   * Implements Requirements 5.4
   */
  private async transferDeviceOwnership(deviceId: string, consumerId: string): Promise<void> {
    const updatedDevice = database.update<Device>('devices', deviceId, {
      status: 'INSTALLED',
      consumerId,
      installedAt: new Date()
    });

    if (!updatedDevice) {
      throw new Error(`Failed to transfer device ownership: ${deviceId}`);
    }

    this.logger.business('Device ownership transferred', {
      deviceId,
      consumerId,
      status: 'INSTALLED'
    });
  }

  /**
   * Check if two dates are the same day
   */
  private isSameDay(date1: Date, date2: Date): boolean {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  }

  /**
   * Get installation statistics
   */
  async getInstallationStatistics(): Promise<{
    totalInstallations: number;
    notRequested: number;
    requested: number;
    scheduled: number;
    completed: number;
    cancelled: number;
    averageCompletionTime?: number;
  }> {
    const allInstallations = await this.getAllInstallations();
    
    const stats = {
      totalInstallations: allInstallations.length,
      notRequested: allInstallations.filter(i => i.status === 'NOT_REQUESTED').length,
      requested: allInstallations.filter(i => i.status === 'REQUESTED').length,
      scheduled: allInstallations.filter(i => i.status === 'SCHEDULED').length,
      completed: allInstallations.filter(i => i.status === 'COMPLETED').length,
      cancelled: allInstallations.filter(i => i.status === 'CANCELLED').length,
      averageCompletionTime: undefined as number | undefined
    };

    // Calculate average completion time for completed installations
    const completedInstallations = allInstallations.filter(i => 
      i.status === 'COMPLETED' && i.requestedAt && i.completedAt
    );

    if (completedInstallations.length > 0) {
      const totalCompletionTime = completedInstallations.reduce((sum, installation) => {
        const completionTime = new Date(installation.completedAt!).getTime() - new Date(installation.requestedAt!).getTime();
        return sum + completionTime;
      }, 0);
      
      stats.averageCompletionTime = Math.round(totalCompletionTime / completedInstallations.length / (1000 * 60 * 60 * 24)); // in days
    }

    return stats;
  }
}

// Export singleton instance
export const installationService = new InstallationService();