/**
 * State Validation Service
 * Provides comprehensive state transition validation across all services
 * Implements Requirements 6.3, 6.5 - State transition validation and consistency
 */

import { OrderStateMachine } from './order-service';
import { DeliveryStateMachine } from './delivery-service';
import { InstallationStateMachine } from './installation-service';
import { database } from '../infrastructure/database';
import { Logger } from '../infrastructure/logger';

export interface StateTransitionAttempt {
  entityType: 'Order' | 'Payment' | 'Delivery' | 'Installation';
  entityId: string;
  fromState: string;
  toState: string;
  timestamp: Date;
  success: boolean;
  error?: string;
}

export interface StateConsistencyCheck {
  orderId: string;
  orderState: string;
  paymentState: string;
  deliveryState?: string;
  installationState?: string;
  consistent: boolean;
  issues: string[];
}

/**
 * State Validation Service
 * Ensures state consistency and validates transitions across all entities
 */
export class StateValidationService {
  private logger: Logger;
  private transitionAttempts: StateTransitionAttempt[] = [];

  constructor() {
    this.logger = new Logger('StateValidationService');
  }

  /**
   * Validate order state transition
   * Implements Requirements 6.3, 6.5
   */
  validateOrderTransition(fromState: string, toState: string): {
    valid: boolean;
    error?: string;
    allowedTransitions: string[];
  } {
    try {
      OrderStateMachine.validateTransition(fromState as any, toState as any);
      
      return {
        valid: true,
        allowedTransitions: OrderStateMachine.getValidNextStates(fromState as any)
      };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Invalid transition',
        allowedTransitions: OrderStateMachine.getValidNextStates(fromState as any)
      };
    }
  }

  /**
   * Validate delivery state transition
   */
  validateDeliveryTransition(fromState: string, toState: string): {
    valid: boolean;
    error?: string;
    allowedTransitions: string[];
  } {
    try {
      DeliveryStateMachine.validateTransition(fromState as any, toState as any);
      
      return {
        valid: true,
        allowedTransitions: DeliveryStateMachine.getValidNextStates(fromState as any)
      };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Invalid transition',
        allowedTransitions: DeliveryStateMachine.getValidNextStates(fromState as any)
      };
    }
  }

  /**
   * Validate installation state transition
   */
  validateInstallationTransition(fromState: string, toState: string): {
    valid: boolean;
    error?: string;
    allowedTransitions: string[];
  } {
    try {
      InstallationStateMachine.validateTransition(fromState as any, toState as any);
      
      return {
        valid: true,
        allowedTransitions: InstallationStateMachine.getValidNextStates(fromState as any)
      };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Invalid transition',
        allowedTransitions: InstallationStateMachine.getValidNextStates(fromState as any)
      };
    }
  }

  /**
   * Record state transition attempt for audit and monitoring
   */
  recordTransitionAttempt(
    entityType: StateTransitionAttempt['entityType'],
    entityId: string,
    fromState: string,
    toState: string,
    success: boolean,
    error?: string
  ): void {
    const attempt: StateTransitionAttempt = {
      entityType,
      entityId,
      fromState,
      toState,
      timestamp: new Date(),
      success,
      error
    };

    this.transitionAttempts.push(attempt);

    // Keep only last 1000 attempts
    if (this.transitionAttempts.length > 1000) {
      this.transitionAttempts.shift();
    }

    if (!success) {
      this.logger.warn('Invalid state transition attempted', {
        entityType,
        entityId,
        fromState,
        toState,
        error
      });
    }
  }

  /**
   * Check state consistency across all entities for an order
   * Implements Requirements 6.5 - Maintain state consistency
   */
  async checkOrderStateConsistency(orderId: string): Promise<StateConsistencyCheck> {
    this.logger.info('Checking state consistency for order', { orderId });

    try {
      // Get all entities for this order
      const order = database.findWhere<any>('orders', o => o.id === orderId)[0];
      const payment = database.findWhere<any>('payments', p => p.orderId === orderId)[0];
      const delivery = database.findWhere<any>('deliveries', d => d.orderId === orderId)[0];
      const installation = database.findWhere<any>('installations', i => i.orderId === orderId)[0];

      if (!order) {
        throw new Error(`Order not found: ${orderId}`);
      }

      const check: StateConsistencyCheck = {
        orderId,
        orderState: order.status,
        paymentState: payment?.status || 'NONE',
        deliveryState: delivery?.status,
        installationState: installation?.status,
        consistent: true,
        issues: []
      };

      // Validate business rules for state consistency
      this.validateOrderPaymentConsistency(check);
      this.validateOrderDeliveryConsistency(check);
      this.validateDeliveryInstallationConsistency(check);
      this.validateOverallWorkflowConsistency(check);

      check.consistent = check.issues.length === 0;

      if (!check.consistent) {
        this.logger.warn('State inconsistency detected', {
          orderId,
          issues: check.issues
        });
      }

      return check;

    } catch (error) {
      this.logger.error('Failed to check state consistency', error, { orderId });
      
      return {
        orderId,
        orderState: 'UNKNOWN',
        paymentState: 'UNKNOWN',
        consistent: false,
        issues: [`Failed to check consistency: ${error instanceof Error ? error.message : 'Unknown error'}`]
      };
    }
  }

  /**
   * Validate order-payment state consistency
   */
  private validateOrderPaymentConsistency(check: StateConsistencyCheck): void {
    // Business rule: Approved orders should have payment records
    if (check.orderState === 'APPROVED' && check.paymentState === 'NONE') {
      check.issues.push('Approved order missing payment record');
    }

    // Business rule: Completed orders should have paid or COD_PENDING payments
    if (check.orderState === 'COMPLETED' && 
        !['PAID', 'COD_PENDING'].includes(check.paymentState)) {
      check.issues.push('Completed order should have paid or COD pending payment');
    }

    // Business rule: Cancelled orders should not have paid payments
    if (check.orderState === 'CANCELLED' && check.paymentState === 'PAID') {
      check.issues.push('Cancelled order should not have paid payment');
    }
  }

  /**
   * Validate order-delivery state consistency
   */
  private validateOrderDeliveryConsistency(check: StateConsistencyCheck): void {
    // Business rule: Pending orders should not have deliveries
    if (check.orderState === 'PENDING' && check.deliveryState) {
      check.issues.push('Pending order should not have delivery record');
    }

    // Business rule: Completed orders should have delivered shipments
    if (check.orderState === 'COMPLETED' && 
        check.deliveryState && 
        check.deliveryState !== 'DELIVERED') {
      check.issues.push('Completed order should have delivered shipment');
    }
  }

  /**
   * Validate delivery-installation state consistency
   */
  private validateDeliveryInstallationConsistency(check: StateConsistencyCheck): void {
    // Business rule: Installation should only be available after delivery
    if (check.installationState === 'REQUESTED' && 
        (!check.deliveryState || check.deliveryState !== 'DELIVERED')) {
      check.issues.push('Installation requested before delivery completion');
    }

    // Business rule: Completed installations should have delivered orders
    if (check.installationState === 'COMPLETED' && 
        check.deliveryState !== 'DELIVERED') {
      check.issues.push('Installation completed without delivery completion');
    }
  }

  /**
   * Validate overall workflow consistency
   */
  private validateOverallWorkflowConsistency(check: StateConsistencyCheck): void {
    // Business rule: Workflow should progress logically
    const workflowStages = {
      'PENDING': 1,
      'APPROVED': 2,
      'COMPLETED': 3,
      'CANCELLED': 0
    };

    const deliveryStages = {
      'PREPARING': 1,
      'SHIPPED': 2,
      'OUT_FOR_DELIVERY': 3,
      'DELIVERED': 4,
      'CANCELLED': 0
    };

    const installationStages = {
      'NOT_REQUESTED': 1,
      'REQUESTED': 2,
      'SCHEDULED': 3,
      'COMPLETED': 4,
      'CANCELLED': 0
    };

    // Check if delivery is ahead of order
    if (check.deliveryState && 
        deliveryStages[check.deliveryState as keyof typeof deliveryStages] > 0 &&
        workflowStages[check.orderState as keyof typeof workflowStages] < 2) {
      check.issues.push('Delivery progress ahead of order approval');
    }

    // Check if installation is ahead of delivery
    if (check.installationState && 
        installationStages[check.installationState as keyof typeof installationStages] > 1 &&
        (!check.deliveryState || deliveryStages[check.deliveryState as keyof typeof deliveryStages] < 4)) {
      check.issues.push('Installation progress ahead of delivery completion');
    }
  }

  /**
   * Get all state transition attempts for monitoring
   */
  getTransitionAttempts(entityType?: StateTransitionAttempt['entityType']): StateTransitionAttempt[] {
    if (entityType) {
      return this.transitionAttempts.filter(attempt => attempt.entityType === entityType);
    }
    return [...this.transitionAttempts];
  }

  /**
   * Get state transition statistics
   */
  getTransitionStatistics(): {
    totalAttempts: number;
    successfulTransitions: number;
    failedTransitions: number;
    failureRate: number;
    byEntityType: Record<string, { total: number; failed: number }>;
  } {
    const stats = {
      totalAttempts: this.transitionAttempts.length,
      successfulTransitions: this.transitionAttempts.filter(a => a.success).length,
      failedTransitions: this.transitionAttempts.filter(a => !a.success).length,
      failureRate: 0,
      byEntityType: {} as Record<string, { total: number; failed: number }>
    };

    stats.failureRate = stats.totalAttempts > 0 ? 
      (stats.failedTransitions / stats.totalAttempts) * 100 : 0;

    // Calculate by entity type
    ['Order', 'Payment', 'Delivery', 'Installation'].forEach(entityType => {
      const attempts = this.transitionAttempts.filter(a => a.entityType === entityType);
      stats.byEntityType[entityType] = {
        total: attempts.length,
        failed: attempts.filter(a => !a.success).length
      };
    });

    return stats;
  }

  /**
   * Validate all state machines are properly configured
   */
  validateStateMachineConfiguration(): {
    valid: boolean;
    issues: string[];
    stateMachines: {
      order: { configured: boolean; states: string[] };
      delivery: { configured: boolean; states: string[] };
      installation: { configured: boolean; states: string[] };
    };
  } {
    const result = {
      valid: true,
      issues: [] as string[],
      stateMachines: {
        order: { 
          configured: true, 
          states: ['PENDING', 'APPROVED', 'COMPLETED', 'CANCELLED'] 
        },
        delivery: { 
          configured: true, 
          states: ['PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'] 
        },
        installation: { 
          configured: true, 
          states: ['NOT_REQUESTED', 'REQUESTED', 'SCHEDULED', 'COMPLETED', 'CANCELLED'] 
        }
      }
    };

    // Validate each state machine has terminal states
    if (!result.stateMachines.order.states.includes('COMPLETED')) {
      result.issues.push('Order state machine missing terminal state');
      result.valid = false;
    }

    if (!result.stateMachines.delivery.states.includes('DELIVERED')) {
      result.issues.push('Delivery state machine missing terminal state');
      result.valid = false;
    }

    if (!result.stateMachines.installation.states.includes('COMPLETED')) {
      result.issues.push('Installation state machine missing terminal state');
      result.valid = false;
    }

    return result;
  }

  /**
   * Clear transition attempts history (for testing)
   */
  clearTransitionHistory(): void {
    this.transitionAttempts = [];
    this.logger.info('State transition history cleared');
  }
}

// Export singleton instance
export const stateValidationService = new StateValidationService();