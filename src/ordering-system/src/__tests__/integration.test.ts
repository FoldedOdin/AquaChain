/**
 * Integration Tests for Core Services
 * Validates that Order and Payment services work correctly together
 */

import { orderService } from '../services/order-service';
import { paymentService } from '../services/payment-service';
import { adminWorkflowService } from '../services/admin-workflow-service';
import { deliveryService } from '../services/delivery-service';
import { installationService } from '../services/installation-service';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';

describe('Core Services Integration', () => {
  beforeEach(() => {
    // Clear database and event bus for each test
    database.clearAll();
    eventBus.clearEventStore();
  });

  describe('Order Service', () => {
    it('should create order with valid payment method', async () => {
      const createRequest = {
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD' as const,
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      };

      const order = await orderService.createOrder(createRequest);

      expect(order).toBeDefined();
      expect(order.id).toBeDefined();
      expect(order.consumerId).toBe(createRequest.consumerId);
      expect(order.paymentMethod).toBe(createRequest.paymentMethod);
      expect(order.status).toBe('PENDING');
    });

    it('should reject order with invalid payment method', async () => {
      const createRequest = {
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'INVALID' as any,
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      };

      await expect(orderService.createOrder(createRequest)).rejects.toThrow('Invalid payment method');
    });

    it('should validate state transitions correctly', async () => {
      // Create order
      const order = await orderService.createOrder({
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      });

      // Approve order
      const approvedOrder = await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'admin-123',
        quoteAmount: 4000
      });

      expect(approvedOrder.status).toBe('APPROVED');
      expect(approvedOrder.quoteAmount).toBe(4000);
      expect(approvedOrder.approvedBy).toBe('admin-123');

      // Complete order
      const completedOrder = await orderService.completeOrder(order.id);
      expect(completedOrder.status).toBe('COMPLETED');

      // Should not be able to approve completed order
      await expect(orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'admin-123',
        quoteAmount: 5000
      })).rejects.toThrow('Invalid state transition');
    });
  });

  describe('Payment Service', () => {
    it('should create COD payment', async () => {
      const payment = await paymentService.createCODPayment('order-123', 4000);

      expect(payment).toBeDefined();
      expect(payment.orderId).toBe('order-123');
      expect(payment.amount).toBe(4000);
      expect(payment.paymentMethod).toBe('COD');
      expect(payment.status).toBe('COD_PENDING');
    });

    it('should get payment status correctly', async () => {
      // Create COD payment
      await paymentService.createCODPayment('order-123', 4000);

      const status = await paymentService.getPaymentStatus('order-123');

      expect(status.status).toBe('COD_PENDING');
      expect(status.method).toBe('COD');
      expect(status.amount).toBe(4000);
      expect(status.canConvertToOnline).toBe(true);
    });
  });

  describe('Admin Workflow Service', () => {
    it('should process order approval correctly', async () => {
      // Create order
      const order = await orderService.createOrder({
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      });

      // Process admin approval
      const result = await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'admin-123',
        adminEmail: 'admin@test.com',
        quoteAmount: 4000,
        notes: 'Test approval'
      });

      expect(result.approved).toBe(true);
      expect(result.order.status).toBe('APPROVED');
      expect(result.order.quoteAmount).toBe(4000);
    });

    it('should validate admin permissions', () => {
      const isValid = adminWorkflowService.validateAdminPermissions('admin-123', 'admin');
      expect(isValid).toBe(true);

      const isInvalid = adminWorkflowService.validateAdminPermissions('user-123', 'consumer');
      expect(isInvalid).toBe(false);
    });
  });

  describe('Event Bus Integration', () => {
    it('should emit events when order is created', async () => {
      let eventReceived = false;
      let receivedEvent: any = null;

      // Subscribe to order created events
      eventBus.subscribe('ORDER_CREATED', (event) => {
        eventReceived = true;
        receivedEvent = event;
      });

      // Create order
      const order = await orderService.createOrder({
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      });

      // Wait for event processing
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(eventReceived).toBe(true);
      expect(receivedEvent).toBeDefined();
      expect(receivedEvent.orderId).toBe(order.id);
      expect(receivedEvent.consumerId).toBe('consumer-123');
    });
  });

  describe('Database Integration', () => {
    it('should persist and retrieve data correctly', async () => {
      // Create order
      const order = await orderService.createOrder({
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '123 Test Street, Test City',
        phone: '+91-9876543210'
      });

      // Retrieve order
      const retrievedOrder = await orderService.getOrder(order.id);

      expect(retrievedOrder).toBeDefined();
      expect(retrievedOrder!.id).toBe(order.id);
      expect(retrievedOrder!.consumerId).toBe(order.consumerId);

      // Get orders by consumer
      const consumerOrders = await orderService.getOrdersByConsumer('consumer-123');
      expect(consumerOrders).toHaveLength(1);
      expect(consumerOrders[0].id).toBe(order.id);
    });

    it('should handle transactions correctly', async () => {
      let transactionExecuted = false;

      await database.transaction(async () => {
        // Create order within transaction
        await orderService.createOrder({
          consumerId: 'consumer-123',
          deviceType: 'AC-HOME-V1',
          paymentMethod: 'COD',
          address: '123 Test Street, Test City',
          phone: '+91-9876543210'
        });

        transactionExecuted = true;
      });

      expect(transactionExecuted).toBe(true);

      // Verify order was created
      const orders = await orderService.getAllOrders();
      expect(orders).toHaveLength(1);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid order creation gracefully', async () => {
      await expect(orderService.createOrder({
        consumerId: '',
        deviceType: '',
        paymentMethod: 'COD',
        address: '',
        phone: ''
      })).rejects.toThrow('Validation failed');
    });

    it('should handle non-existent order operations', async () => {
      await expect(orderService.getOrder('non-existent')).resolves.toBeNull();

      await expect(orderService.approveOrder({
        orderId: 'non-existent',
        approvedBy: 'admin-123',
        quoteAmount: 4000
      })).rejects.toThrow('Order not found');
    });
  });
});

/**
 * Complete Workflow Integration Tests
 * Tests for task 12.2: Complete order-to-delivery-to-installation flow
 */

describe('Complete Workflow Integration Tests', () => {
  beforeEach(() => {
    // Clear database and event bus for each test
    database.clearAll();
    eventBus.clearEventStore();
  });

  describe('Complete Order-to-Delivery-to-Installation Flow', () => {
    it('should complete full workflow from order creation to installation completion', async () => {
      // Step 1: Create order with COD payment method
      const createOrderRequest = {
        consumerId: 'workflow-consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD' as const,
        address: '123 Workflow Test Street, Test City, Test State 12345',
        phone: '+91-9876543210'
      };

      const order = await orderService.createOrder(createOrderRequest);
      expect(order).toBeDefined();
      expect(order.status).toBe('PENDING');
      expect(order.paymentMethod).toBe('COD');

      // Step 2: Admin approves order
      const approvalRequest = {
        orderId: order.id,
        approvedBy: 'workflow-admin-123',
        quoteAmount: 4500
      };

      const approvedOrder = await orderService.approveOrder(approvalRequest);
      expect(approvedOrder.status).toBe('APPROVED');
      expect(approvedOrder.quoteAmount).toBe(4500);

      // Step 3: Create COD payment record
      const payment = await paymentService.createCODPayment(order.id, 4500);
      expect(payment.paymentMethod).toBe('COD');
      expect(payment.status).toBe('COD_PENDING');

      // Step 4: Create shipment and track delivery progress
      const shipmentRequest = {
        orderId: order.id,
        address: {
          street: '123 Workflow Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '12345',
          country: 'India'
        },
        carrier: 'Workflow Test Delivery'
      };

      const delivery = await deliveryService.initiateShipment(shipmentRequest);
      expect(delivery.status).toBe('PREPARING');
      expect(delivery.trackingNumber).toBeDefined();

      // Step 5: Progress through delivery states
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'SHIPPED'
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY',
        location: 'Local delivery hub'
      });

      const deliveredShipment = await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED',
        location: 'Consumer address'
      });

      expect(deliveredShipment.status).toBe('DELIVERED');
      expect(deliveredShipment.deliveredAt).toBeDefined();

      // Step 6: Consumer requests installation (consumer-controlled)
      const installationRequest = {
        orderId: order.id,
        consumerId: 'workflow-consumer-123',
        preferredDate: new Date(Date.now() + 24 * 60 * 60 * 1000) // Tomorrow
      };

      const installation = await installationService.requestInstallation(installationRequest);
      expect(installation.status).toBe('REQUESTED');

      // Step 7: Schedule installation with technician
      // First create a technician record
      database.create('technicians', {
        id: 'workflow-tech-123',
        name: 'Workflow Test Technician',
        email: 'tech@workflow.com',
        phone: '+91-9876543211',
        skills: ['installation'],
        availability: 'AVAILABLE',
        rating: 4.8,
        completedInstallations: 15
      });

      const scheduleRequest = {
        installationId: installation.id,
        technicianId: 'workflow-tech-123',
        scheduledDate: new Date(Date.now() + 24 * 60 * 60 * 1000)
      };

      const scheduledInstallation = await installationService.scheduleInstallation(scheduleRequest);
      expect(scheduledInstallation.status).toBe('SCHEDULED');
      expect(scheduledInstallation.technicianId).toBe('workflow-tech-123');

      // Step 8: Complete installation with device transfer
      // First create a device record
      database.create('devices', {
        id: 'workflow-device-123',
        serialNumber: 'WF123456',
        model: 'AC-HOME-V1',
        status: 'AVAILABLE',
        createdAt: new Date()
      });

      const completeRequest = {
        installationId: installation.id,
        deviceId: 'workflow-device-123',
        calibrationData: { ph: 7.2, temperature: 24, tds: 150 },
        photos: ['install1.jpg', 'install2.jpg', 'calibration.jpg']
      };

      const completedInstallation = await installationService.completeInstallation(completeRequest);
      expect(completedInstallation.status).toBe('COMPLETED');
      expect(completedInstallation.deviceId).toBe('workflow-device-123');

      // Step 9: Verify final states and device ownership transfer
      const finalOrder = await orderService.getOrder(order.id);
      const finalPayment = await paymentService.getPaymentByOrderId(order.id);
      const finalDelivery = await deliveryService.getDeliveryByOrderId(order.id);
      const finalInstallation = await installationService.getInstallationByOrderId(order.id);

      expect(finalOrder?.status).toBe('APPROVED');
      expect(finalPayment?.status).toBe('COD_PENDING');
      expect(finalDelivery?.status).toBe('DELIVERED');
      expect(finalInstallation?.status).toBe('COMPLETED');

      // Verify device ownership transfer (Requirement 5.4)
      const device = database.findById('devices', 'workflow-device-123') as any;
      expect(device?.status).toBe('INSTALLED');
      expect(device?.consumerId).toBe('workflow-consumer-123');
    });

    it('should handle online payment workflow from creation to completion', async () => {
      // Create order with online payment method
      const order = await orderService.createOrder({
        consumerId: 'online-consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'ONLINE',
        address: '456 Online Test Street',
        phone: '+91-9876543211'
      });

      // Admin approves order
      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'online-admin-123',
        quoteAmount: 5000
      });

      // Create online payment order
      const paymentOrderResult = await paymentService.createPaymentOrder({
        orderId: order.id,
        amount: 5000
      });

      expect(paymentOrderResult.payment.paymentMethod).toBe('ONLINE');
      expect(paymentOrderResult.payment.status).toBe('UNPAID');
      expect(paymentOrderResult.razorpayOrder).toBeDefined();

      // Simulate successful payment
      const processPaymentResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_online123',
        razorpayOrderId: paymentOrderResult.razorpayOrder.id,
        razorpaySignature: 'valid_signature'
      });

      expect(processPaymentResult.status).toBe('PAID');

      // Continue with delivery and installation
      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '456 Online Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '54321',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      // Verify payment status
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.status).toBe('PAID');
      expect(paymentStatus.method).toBe('ONLINE');
    });
  });

  describe('COD to Online Payment Conversion End-to-End', () => {
    it('should handle complete COD to online payment conversion workflow', async () => {
      // Step 1: Create COD order and get to OUT_FOR_DELIVERY status
      const order = await orderService.createOrder({
        consumerId: 'conversion-consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '789 Conversion Test Street',
        phone: '+91-9876543212'
      });

      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'conversion-admin-123',
        quoteAmount: 3500
      });

      const codPayment = await paymentService.createCODPayment(order.id, 3500);
      expect(codPayment.paymentMethod).toBe('COD');
      expect(codPayment.status).toBe('COD_PENDING');

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '789 Conversion Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '67890',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'SHIPPED'
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY'
      });

      // Step 2: Verify COD conversion option is available
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.canConvertToOnline).toBe(true);

      // Step 3: Convert COD to online payment
      const conversionResult = await paymentService.convertCODToOnline(order.id);
      expect(conversionResult.payment.paymentMethod).toBe('ONLINE');
      expect(conversionResult.razorpayOrder).toBeDefined();

      // Step 4: Complete online payment
      const processPaymentResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_conversion123',
        razorpayOrderId: conversionResult.razorpayOrder.id,
        razorpaySignature: 'valid_conversion_signature'
      });

      expect(processPaymentResult.status).toBe('PAID');

      // Step 5: Complete delivery
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      // Step 6: Verify final payment status
      const finalPaymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(finalPaymentStatus.status).toBe('PAID');
      expect(finalPaymentStatus.method).toBe('ONLINE');
      expect(finalPaymentStatus.canConvertToOnline).toBe(false);

      // Step 7: Continue with installation to complete workflow
      const installation = await installationService.requestInstallation({
        orderId: order.id,
        consumerId: 'conversion-consumer-123'
      });

      expect(installation.status).toBe('REQUESTED');
    });

    it('should handle failed COD conversion gracefully', async () => {
      // Create COD order
      const order = await orderService.createOrder({
        consumerId: 'failed-conversion-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '999 Failed Test Street',
        phone: '+91-9876543213'
      });

      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'failed-admin',
        quoteAmount: 4000
      });

      await paymentService.createCODPayment(order.id, 4000);

      // Attempt conversion
      const conversionResult = await paymentService.convertCODToOnline(order.id);

      // Simulate failed payment processing
      try {
        await paymentService.processPayment({
          orderId: order.id,
          razorpayPaymentId: 'pay_failed123',
          razorpayOrderId: conversionResult.razorpayOrder.id,
          razorpaySignature: 'invalid_signature'
        });
        
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid payment signature');
      }

      // Verify original COD payment is preserved
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.method).toBe('COD');
      expect(paymentStatus.canConvertToOnline).toBe(true);
    });
  });

  describe('Error Scenarios and Recovery', () => {
    it('should handle invalid state transitions gracefully', async () => {
      const order = await orderService.createOrder({
        consumerId: 'error-consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '111 Error Test Street',
        phone: '+91-9876543214'
      });

      // Try to complete order without approval
      try {
        await orderService.completeOrder(order.id);
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid state transition');
      }

      // Verify order state is unchanged
      const unchangedOrder = await orderService.getOrder(order.id);
      expect(unchangedOrder?.status).toBe('PENDING');
    });

    it('should handle delivery state validation errors', async () => {
      const order = await orderService.createOrder({
        consumerId: 'delivery-error-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '222 Delivery Error Street',
        phone: '+91-9876543215'
      });

      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'delivery-error-admin',
        quoteAmount: 4000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '222 Delivery Error Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '11111',
          country: 'India'
        }
      });

      // Try invalid state transition (PREPARING -> DELIVERED)
      try {
        await deliveryService.updateDeliveryStatus({
          shipmentId: delivery.shipmentId,
          status: 'DELIVERED'
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid delivery state transition');
      }

      // Verify delivery state is unchanged
      const unchangedDelivery = await deliveryService.getDeliveryByOrderId(order.id);
      expect(unchangedDelivery?.status).toBe('PREPARING');
    });

    it('should handle installation request validation errors', async () => {
      // Try to request installation without delivery completion
      try {
        await installationService.requestInstallation({
          orderId: 'non-existent-order',
          consumerId: 'test-consumer'
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
      }

      // Try invalid installation request
      try {
        await installationService.requestInstallation({
          orderId: '',
          consumerId: ''
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('validation failed');
      }
    });

    it('should handle payment processing errors and recovery', async () => {
      const order = await orderService.createOrder({
        consumerId: 'payment-error-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'ONLINE',
        address: '333 Payment Error Street',
        phone: '+91-9876543216'
      });

      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'payment-error-admin',
        quoteAmount: 5000
      });

      const paymentOrderResult = await paymentService.createPaymentOrder({
        orderId: order.id,
        amount: 5000
      });

      // Try payment with invalid signature
      try {
        await paymentService.processPayment({
          orderId: order.id,
          razorpayPaymentId: 'pay_invalid123',
          razorpayOrderId: paymentOrderResult.razorpayOrder.id,
          razorpaySignature: 'completely_invalid_signature'
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid payment signature');
      }

      // Verify payment status remains UNPAID
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.status).toBe('UNPAID');

      // Retry with valid payment
      const retryResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_retry123',
        razorpayOrderId: paymentOrderResult.razorpayOrder.id,
        razorpaySignature: 'valid_retry_signature'
      });

      expect(retryResult.status).toBe('PAID');
    });

    it('should handle concurrent order processing safely', async () => {
      const order = await orderService.createOrder({
        consumerId: 'concurrent-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '444 Concurrent Test Street',
        phone: '+91-9876543217'
      });

      // Simulate concurrent approval attempts
      const approvalPromises = [
        orderService.approveOrder({
          orderId: order.id,
          approvedBy: 'admin-1',
          quoteAmount: 4000
        }),
        orderService.approveOrder({
          orderId: order.id,
          approvedBy: 'admin-2',
          quoteAmount: 4500
        })
      ];

      // One should succeed, one should fail due to optimistic locking
      const results = await Promise.allSettled(approvalPromises);
      
      const successfulResults = results.filter(r => r.status === 'fulfilled');
      const failedResults = results.filter(r => r.status === 'rejected');

      expect(successfulResults.length).toBe(1);
      expect(failedResults.length).toBe(1);

      // Verify final order state is consistent
      const finalOrder = await orderService.getOrder(order.id);
      expect(finalOrder?.status).toBe('APPROVED');
    });

    it('should handle system recovery after failures', async () => {
      // Create order and simulate system failure during processing
      const order = await orderService.createOrder({
        consumerId: 'recovery-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '555 Recovery Test Street',
        phone: '+91-9876543218'
      });

      // Simulate partial processing before failure
      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'recovery-admin',
        quoteAmount: 4000
      });

      await paymentService.createCODPayment(order.id, 4000);

      // Simulate system restart - verify data integrity
      const recoveredOrder = await orderService.getOrder(order.id);
      const recoveredPayment = await paymentService.getPaymentByOrderId(order.id);

      expect(recoveredOrder?.status).toBe('APPROVED');
      expect(recoveredPayment?.status).toBe('COD_PENDING');

      // Continue processing after recovery
      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '555 Recovery Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '55555',
          country: 'India'
        }
      });

      expect(delivery.status).toBe('PREPARING');
    });
  });

  describe('Event-Driven Architecture Validation', () => {
    it('should maintain loose coupling through events', async () => {
      const eventsReceived: string[] = [];

      // Subscribe to all workflow events
      const eventTypes = [
        'ORDER_CREATED', 'ORDER_APPROVED', 'PAYMENT_COMPLETED',
        'SHIPMENT_CREATED', 'DELIVERY_STATUS_UPDATED', 'DELIVERY_COMPLETED',
        'INSTALLATION_REQUESTED', 'INSTALLATION_COMPLETED'
      ];

      eventTypes.forEach(eventType => {
        eventBus.subscribe(eventType, async () => {
          eventsReceived.push(eventType);
        });
      });

      // Execute workflow
      const order = await orderService.createOrder({
        consumerId: 'event-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '666 Event Test Street',
        phone: '+91-9876543219'
      });

      await orderService.approveOrder({
        orderId: order.id,
        approvedBy: 'event-admin',
        quoteAmount: 4000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '666 Event Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '66666',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      // Wait for event processing
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify events were emitted
      expect(eventsReceived).toContain('ORDER_CREATED');
      expect(eventsReceived).toContain('ORDER_APPROVED');
      expect(eventsReceived).toContain('SHIPMENT_CREATED');
      expect(eventsReceived).toContain('DELIVERY_STATUS_UPDATED');
      expect(eventsReceived).toContain('DELIVERY_COMPLETED');
    });
  });
});

// Helper function to run tests
export async function runIntegrationTests(): Promise<boolean> {
  try {
    console.log('🧪 Running comprehensive integration tests...');
    
    // Test 1: Basic order creation
    const order = await orderService.createOrder({
      consumerId: 'test-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Street',
      phone: '+91-9876543210'
    });
    
    if (!order || !order.id) {
      throw new Error('Order creation failed');
    }
    
    // Test 2: Order approval
    const approvedOrder = await orderService.approveOrder({
      orderId: order.id,
      approvedBy: 'test-admin',
      quoteAmount: 4000
    });
    
    if (approvedOrder.status !== 'APPROVED') {
      throw new Error('Order approval failed');
    }
    
    // Test 3: Payment creation
    const payment = await paymentService.createCODPayment(order.id, 4000);
    
    if (!payment || payment.status !== 'COD_PENDING') {
      throw new Error('COD payment creation failed');
    }

    // Test 4: Complete workflow validation
    const delivery = await deliveryService.initiateShipment({
      orderId: order.id,
      address: {
        street: '123 Test Street',
        city: 'Test City',
        state: 'Test State',
        postalCode: '12345',
        country: 'India'
      }
    });

    if (!delivery || delivery.status !== 'PREPARING') {
      throw new Error('Delivery initiation failed');
    }

    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'DELIVERED'
    });

    const installation = await installationService.requestInstallation({
      orderId: order.id,
      consumerId: 'test-consumer'
    });

    if (!installation || installation.status !== 'REQUESTED') {
      throw new Error('Installation request failed');
    }
    
    console.log('✅ All comprehensive integration tests passed');
    return true;
    
  } catch (error) {
    console.error('❌ Integration tests failed:', error);
    return false;
  } finally {
    // Cleanup
    database.clearAll();
    eventBus.clearEventStore();
  }
}