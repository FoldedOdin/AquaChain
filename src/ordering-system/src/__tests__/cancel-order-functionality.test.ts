/**
 * Cancel Order Functionality Tests
 * Tests both Consumer and Admin cancel order capabilities
 */

import { orderService } from '../services/order-service';
import { adminWorkflowService } from '../services/admin-workflow-service';

describe('Cancel Order Functionality', () => {
  describe('Consumer Cancel Order', () => {
    it('should allow consumer to cancel pending order', async () => {
      // Create a test order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-123',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      });

      expect(testOrder.status).toBe('PENDING');

      // Consumer cancels the order
      const cancelledOrder = await orderService.cancelOrder(
        testOrder.id,
        testOrder.consumerId,
        'Changed my mind about the purchase'
      );

      expect(cancelledOrder.status).toBe('CANCELLED');
      expect(cancelledOrder.cancelReason).toBe('Changed my mind about the purchase');
      expect(cancelledOrder.cancelledAt).toBeDefined();
    });

    it('should prevent consumer from cancelling non-pending orders', async () => {
      // Create and approve an order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-456',
        deviceType: 'AquaChain Basic',
        paymentMethod: 'ONLINE',
        address: '456 Test Street, Test City',
        phone: '+91-9876543211'
      });

      const approvedOrder = await adminWorkflowService.processOrderApproval({
        orderId: testOrder.id,
        adminId: 'admin-123',
        adminEmail: 'admin@aquachain.com',
        quoteAmount: 15000,
        notes: 'Test approval'
      });

      expect(approvedOrder.order.status).toBe('APPROVED');

      // Consumer tries to cancel approved order - should fail
      await expect(
        orderService.cancelOrder(
          testOrder.id,
          testOrder.consumerId,
          'Want to cancel approved order'
        )
      ).rejects.toThrow('Consumers can only cancel pending orders. Current status: APPROVED');
    });

    it('should prevent cancelling already cancelled orders', async () => {
      // Create and cancel an order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-789',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '789 Test Street, Test City',
        phone: '+91-9876543212'
      });

      await orderService.cancelOrder(
        testOrder.id,
        testOrder.consumerId,
        'First cancellation'
      );

      // Try to cancel again - should fail
      await expect(
        orderService.cancelOrder(
          testOrder.id,
          testOrder.consumerId,
          'Second cancellation attempt'
        )
      ).rejects.toThrow('Consumers can only cancel pending orders. Current status: CANCELLED');
    });
  });

  describe('Admin Cancel Order', () => {
    it('should allow admin to cancel pending order', async () => {
      // Create a test order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-admin-1',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '123 Admin Test Street, Test City',
        phone: '+91-9876543213'
      });

      expect(testOrder.status).toBe('PENDING');

      // Admin cancels the order
      const cancellationResult = await adminWorkflowService.processOrderCancellation({
        orderId: testOrder.id,
        adminId: 'admin-123',
        adminEmail: 'admin@aquachain.com',
        reason: 'Inventory shortage - unable to fulfill order',
        notifyConsumer: true,
        refundAmount: 0
      });

      expect(cancellationResult.cancelled).toBe(true);
      expect(cancellationResult.order.status).toBe('CANCELLED');
      expect(cancellationResult.refundAmount).toBe(0);
      expect(cancellationResult.consumerNotified).toBe(true);
      expect(cancellationResult.message).toContain('cancelled successfully by admin');
    });

    it('should allow admin to cancel approved order with refund', async () => {
      // Create and approve an order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-admin-2',
        deviceType: 'AquaChain Basic',
        paymentMethod: 'ONLINE',
        address: '456 Admin Test Street, Test City',
        phone: '+91-9876543214'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: testOrder.id,
        adminId: 'admin-123',
        adminEmail: 'admin@aquachain.com',
        quoteAmount: 15000,
        notes: 'Test approval for cancellation'
      });

      // Admin cancels approved order with refund
      const cancellationResult = await adminWorkflowService.processOrderCancellation({
        orderId: testOrder.id,
        adminId: 'admin-456',
        adminEmail: 'admin2@aquachain.com',
        reason: 'Quality issue detected during preparation',
        notifyConsumer: true,
        refundAmount: 5000
      });

      expect(cancellationResult.cancelled).toBe(true);
      expect(cancellationResult.order.status).toBe('CANCELLED');
      expect(cancellationResult.refundAmount).toBe(5000);
      expect(cancellationResult.consumerNotified).toBe(true);
    });

    it('should prevent admin from cancelling completed orders', async () => {
      // Create, approve, and complete an order
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-admin-3',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '789 Admin Test Street, Test City',
        phone: '+91-9876543215'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: testOrder.id,
        adminId: 'admin-123',
        adminEmail: 'admin@aquachain.com',
        quoteAmount: 20000,
        notes: 'Test approval'
      });

      await orderService.completeOrder(testOrder.id);

      // Admin tries to cancel completed order - should fail
      await expect(
        adminWorkflowService.processOrderCancellation({
          orderId: testOrder.id,
          adminId: 'admin-123',
          adminEmail: 'admin@aquachain.com',
          reason: 'Trying to cancel completed order',
          notifyConsumer: true,
          refundAmount: 0
        })
      ).rejects.toThrow('is completed and cannot be cancelled');
    });

    it('should validate admin cancellation request', async () => {
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-validation',
        deviceType: 'AquaChain Basic',
        paymentMethod: 'COD',
        address: '123 Validation Street, Test City',
        phone: '+91-9876543216'
      });

      // Test missing reason
      await expect(
        adminWorkflowService.processOrderCancellation({
          orderId: testOrder.id,
          adminId: 'admin-123',
          adminEmail: 'admin@aquachain.com',
          reason: '', // Empty reason
          notifyConsumer: true,
          refundAmount: 0
        })
      ).rejects.toThrow('Cancellation reason is required');

      // Test short reason
      await expect(
        adminWorkflowService.processOrderCancellation({
          orderId: testOrder.id,
          adminId: 'admin-123',
          adminEmail: 'admin@aquachain.com',
          reason: 'Short', // Too short
          notifyConsumer: true,
          refundAmount: 0
        })
      ).rejects.toThrow('Cancellation reason must be at least 10 characters');

      // Test negative refund amount
      await expect(
        adminWorkflowService.processOrderCancellation({
          orderId: testOrder.id,
          adminId: 'admin-123',
          adminEmail: 'admin@aquachain.com',
          reason: 'Valid reason for cancellation',
          notifyConsumer: true,
          refundAmount: -100 // Negative amount
        })
      ).rejects.toThrow('Refund amount cannot be negative');

      // Test excessive refund amount
      await expect(
        adminWorkflowService.processOrderCancellation({
          orderId: testOrder.id,
          adminId: 'admin-123',
          adminEmail: 'admin@aquachain.com',
          reason: 'Valid reason for cancellation',
          notifyConsumer: true,
          refundAmount: 200000 // Too high
        })
      ).rejects.toThrow('Refund amount exceeds maximum limit');
    });
  });

  describe('Admin Permissions', () => {
    it('should validate admin permissions correctly', () => {
      // Valid admin roles
      expect(adminWorkflowService.validateAdminPermissions('admin-1', 'admin')).toBe(true);
      expect(adminWorkflowService.validateAdminPermissions('admin-2', 'super_admin')).toBe(true);
      expect(adminWorkflowService.validateAdminPermissions('admin-3', 'order_manager')).toBe(true);

      // Invalid roles
      expect(adminWorkflowService.validateAdminPermissions('user-1', 'user')).toBe(false);
      expect(adminWorkflowService.validateAdminPermissions('guest-1', 'guest')).toBe(false);
      expect(adminWorkflowService.validateAdminPermissions('customer-1', 'customer')).toBe(false);
    });
  });

  describe('Admin Helper Methods', () => {
    it('should get order for approval', async () => {
      const testOrder = await orderService.createOrder({
        consumerId: 'test-consumer-helper',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '123 Helper Test Street, Test City',
        phone: '+91-9876543217'
      });

      const retrievedOrder = await adminWorkflowService.getOrderForApproval(testOrder.id);
      
      expect(retrievedOrder).toBeDefined();
      expect(retrievedOrder!.id).toBe(testOrder.id);
      expect(retrievedOrder!.status).toBe('PENDING');
    });

    it('should return null for non-existent order', async () => {
      const retrievedOrder = await adminWorkflowService.getOrderForApproval('non-existent-id');
      expect(retrievedOrder).toBeNull();
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete consumer workflow', async () => {
      // Consumer creates order
      const order = await orderService.createOrder({
        consumerId: 'integration-consumer-1',
        deviceType: 'AquaChain Pro',
        paymentMethod: 'COD',
        address: '123 Integration Street, Test City',
        phone: '+91-9876543218'
      });

      expect(order.status).toBe('PENDING');

      // Consumer decides to cancel before approval
      const cancelledOrder = await orderService.cancelOrder(
        order.id,
        order.consumerId,
        'Changed requirements - need different model'
      );

      expect(cancelledOrder.status).toBe('CANCELLED');
      expect(cancelledOrder.cancelReason).toBe('Changed requirements - need different model');
    });

    it('should handle complete admin workflow', async () => {
      // Create order
      const order = await orderService.createOrder({
        consumerId: 'integration-consumer-2',
        deviceType: 'AquaChain Basic',
        paymentMethod: 'ONLINE',
        address: '456 Integration Street, Test City',
        phone: '+91-9876543219'
      });

      // Admin approves order
      const approvalResult = await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'integration-admin',
        adminEmail: 'integration@aquachain.com',
        quoteAmount: 12000,
        notes: 'Integration test approval'
      });

      expect(approvalResult.approved).toBe(true);
      expect(approvalResult.order.status).toBe('APPROVED');

      // Admin later cancels due to supply issue
      const cancellationResult = await adminWorkflowService.processOrderCancellation({
        orderId: order.id,
        adminId: 'integration-admin',
        adminEmail: 'integration@aquachain.com',
        reason: 'Supply chain disruption - unable to source components',
        notifyConsumer: true,
        refundAmount: 2000
      });

      expect(cancellationResult.cancelled).toBe(true);
      expect(cancellationResult.order.status).toBe('CANCELLED');
      expect(cancellationResult.refundAmount).toBe(2000);
      expect(cancellationResult.consumerNotified).toBe(true);
    });
  });
});