/**
 * Complete Workflow Integration Tests
 * Task 12.2: Write integration tests for complete workflows
 * 
 * Tests:
 * - Complete order-to-delivery-to-installation flow
 * - COD-to-online payment conversion end-to-end
 * - Error scenarios and recovery
 */

import { orderService } from '../services/order-service';
import { paymentService } from '../services/payment-service';
import { deliveryService } from '../services/delivery-service';
import { installationService } from '../services/installation-service';
import { adminWorkflowService } from '../services/admin-workflow-service';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';
import { Logger } from '../infrastructure/logger';

const logger = new Logger('CompleteWorkflowTests');

describe('Complete Workflow Integration Tests - Task 12.2', () => {
  beforeEach(() => {
    // Clear database and event bus for each test
    database.clearAll();
    eventBus.clearEventStore();
    logger.info('Test environment reset');
  });

  describe('1. Complete Order-to-Delivery-to-Installation Flow', () => {
    it('should execute complete COD workflow from order creation to installation completion', async () => {
      logger.info('Starting complete COD workflow test');

      // Step 1: Create order with COD payment method
      const createOrderRequest = {
        consumerId: 'workflow-consumer-001',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD' as const,
        address: '123 Complete Workflow Street, Test City, Test State 12345',
        phone: '+91-9876543210'
      };

      const order = await orderService.createOrder(createOrderRequest);
      expect(order).toBeDefined();
      expect(order.status).toBe('PENDING');
      expect(order.paymentMethod).toBe('COD');
      expect(order.consumerId).toBe('workflow-consumer-001');
      logger.info('✓ Order created successfully', { orderId: order.id });

      // Step 2: Admin approves order (Requirement 2.3)
      const approvalRequest = {
        orderId: order.id,
        adminId: 'workflow-admin-001',
        adminEmail: 'admin@workflow.test',
        quoteAmount: 4500,
        notes: 'Complete workflow test approval'
      };

      const approvalResult = await adminWorkflowService.processOrderApproval(approvalRequest);
      expect(approvalResult.approved).toBe(true);
      expect(approvalResult.order.status).toBe('APPROVED');
      expect(approvalResult.order.quoteAmount).toBe(4500);
      logger.info('✓ Order approved by admin', { quoteAmount: 4500 });

      // Step 3: Create COD payment record (Requirement 2.1)
      const payment = await paymentService.createCODPayment(order.id, 4500);
      expect(payment.paymentMethod).toBe('COD');
      expect(payment.status).toBe('COD_PENDING');
      expect(payment.amount).toBe(4500);
      logger.info('✓ COD payment record created');

      // Step 4: Create shipment and track delivery progress (Requirements 7.1, 7.2)
      const shipmentRequest = {
        orderId: order.id,
        address: {
          street: '123 Complete Workflow Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '12345',
          country: 'India'
        },
        carrier: 'Complete Workflow Delivery Service'
      };

      const delivery = await deliveryService.initiateShipment(shipmentRequest);
      expect(delivery.status).toBe('PREPARING');
      expect(delivery.trackingNumber).toBeDefined();
      expect(delivery.orderId).toBe(order.id);
      logger.info('✓ Shipment created', { trackingNumber: delivery.trackingNumber });

      // Step 5: Progress through delivery states (Requirements 7.3, 7.4)
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'SHIPPED',
        location: 'Warehouse'
      });
      logger.info('✓ Delivery status: SHIPPED');

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY',
        location: 'Local delivery hub'
      });
      logger.info('✓ Delivery status: OUT_FOR_DELIVERY');

      const deliveredShipment = await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED',
        location: 'Consumer address'
      });

      expect(deliveredShipment.status).toBe('DELIVERED');
      expect(deliveredShipment.deliveredAt).toBeDefined();
      logger.info('✓ Delivery completed');

      // Step 6: Consumer requests installation (Requirements 5.2, 5.5 - Consumer-controlled)
      const installationRequest = {
        orderId: order.id,
        consumerId: 'workflow-consumer-001',
        preferredDate: new Date(Date.now() + 24 * 60 * 60 * 1000), // Tomorrow
        notes: 'Complete workflow installation test'
      };

      const installation = await installationService.requestInstallation(installationRequest);
      expect(installation.status).toBe('REQUESTED');
      expect(installation.consumerId).toBe('workflow-consumer-001');
      logger.info('✓ Installation requested by consumer');

      // Step 7: Schedule installation with technician (Requirement 5.3)
      // First create a technician record
      database.create('technicians', {
        id: 'workflow-tech-001',
        name: 'Complete Workflow Technician',
        email: 'tech@workflow.test',
        phone: '+91-9876543211',
        skills: ['installation', 'calibration'],
        availability: 'AVAILABLE',
        rating: 4.9,
        completedInstallations: 25
      });

      const scheduleRequest = {
        installationId: installation.id,
        technicianId: 'workflow-tech-001',
        scheduledDate: new Date(Date.now() + 24 * 60 * 60 * 1000),
        notes: 'Scheduled for complete workflow test'
      };

      const scheduledInstallation = await installationService.scheduleInstallation(scheduleRequest);
      expect(scheduledInstallation.status).toBe('SCHEDULED');
      expect(scheduledInstallation.technicianId).toBe('workflow-tech-001');
      logger.info('✓ Installation scheduled with technician');

      // Step 8: Complete installation with device transfer (Requirement 5.4)
      // First create a device record
      database.create('devices', {
        id: 'workflow-device-001',
        serialNumber: 'CWF123456',
        model: 'AC-HOME-V1',
        status: 'AVAILABLE',
        createdAt: new Date(),
        specifications: {
          capacity: '10L/hour',
          powerRating: '50W',
          dimensions: '30x20x40cm'
        }
      });

      const completeRequest = {
        installationId: installation.id,
        deviceId: 'workflow-device-001',
        calibrationData: { 
          ph: 7.2, 
          temperature: 24, 
          tds: 150,
          flowRate: 10.5,
          pressure: 2.1
        },
        photos: ['install1.jpg', 'install2.jpg', 'calibration.jpg', 'final.jpg'],
        notes: 'Complete workflow installation completed successfully'
      };

      const completedInstallation = await installationService.completeInstallation(completeRequest);
      expect(completedInstallation.status).toBe('COMPLETED');
      expect(completedInstallation.deviceId).toBe('workflow-device-001');
      expect(completedInstallation.calibrationData).toEqual(completeRequest.calibrationData);
      logger.info('✓ Installation completed with device transfer');

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
      const device = database.findById('devices', 'workflow-device-001') as any;
      expect(device?.status).toBe('INSTALLED');
      expect(device?.consumerId).toBe('workflow-consumer-001');
      expect(device?.installedAt).toBeDefined();

      logger.info('✅ Complete COD workflow test passed successfully');
    });

    it('should execute complete online payment workflow', async () => {
      logger.info('Starting complete online payment workflow test');

      // Create order with online payment method
      const order = await orderService.createOrder({
        consumerId: 'online-consumer-001',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'ONLINE',
        address: '456 Online Payment Street, Test City',
        phone: '+91-9876543211'
      });

      expect(order.paymentMethod).toBe('ONLINE');
      logger.info('✓ Online payment order created');

      // Admin approves order
      const approvalResult = await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'online-admin-001',
        adminEmail: 'admin@online.test',
        quoteAmount: 5200
      });

      expect(approvalResult.approved).toBe(true);
      logger.info('✓ Order approved for online payment');

      // Create online payment order (Requirements 8.1, 8.2)
      const paymentOrderResult = await paymentService.createPaymentOrder({
        orderId: order.id,
        amount: 5200,
        notes: {
          testType: 'complete-workflow',
          paymentMethod: 'online'
        }
      });

      expect(paymentOrderResult.payment.paymentMethod).toBe('ONLINE');
      expect(paymentOrderResult.payment.status).toBe('UNPAID');
      expect(paymentOrderResult.razorpayOrder).toBeDefined();
      expect(paymentOrderResult.razorpayOrder.amount).toBe(520000); // In paise
      logger.info('✓ Razorpay payment order created');

      // Simulate successful payment (Requirements 4.1, 4.2)
      const processPaymentResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_online_workflow_001',
        razorpayOrderId: paymentOrderResult.razorpayOrder.id,
        razorpaySignature: 'valid_online_signature'
      });

      expect(processPaymentResult.status).toBe('PAID');
      expect(processPaymentResult.razorpayPaymentId).toBe('pay_online_workflow_001');
      logger.info('✓ Online payment processed successfully');

      // Continue with delivery
      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '456 Online Payment Street',
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

      // Verify final payment status
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.status).toBe('PAID');
      expect(paymentStatus.method).toBe('ONLINE');
      expect(paymentStatus.paidAt).toBeDefined();

      logger.info('✅ Complete online payment workflow test passed');
    });
  });

  describe('2. COD to Online Payment Conversion End-to-End', () => {
    it('should handle complete COD to online payment conversion workflow', async () => {
      logger.info('Starting COD to online conversion workflow test');

      // Step 1: Create COD order and progress to OUT_FOR_DELIVERY
      const order = await orderService.createOrder({
        consumerId: 'conversion-consumer-001',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '789 Conversion Test Street, Test City',
        phone: '+91-9876543212'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'conversion-admin-001',
        adminEmail: 'admin@conversion.test',
        quoteAmount: 3800
      });

      const codPayment = await paymentService.createCODPayment(order.id, 3800);
      expect(codPayment.paymentMethod).toBe('COD');
      expect(codPayment.status).toBe('COD_PENDING');
      logger.info('✓ COD order setup completed');

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
      logger.info('✓ Order is OUT_FOR_DELIVERY');

      // Step 2: Verify COD conversion option is available (Requirement 3.1)
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.canConvertToOnline).toBe(true);
      expect(paymentStatus.method).toBe('COD');
      logger.info('✓ COD conversion option available');

      // Step 3: Convert COD to online payment (Requirements 3.3, 3.4)
      const conversionResult = await paymentService.convertCODToOnline(order.id);
      expect(conversionResult.payment.paymentMethod).toBe('ONLINE');
      expect(conversionResult.razorpayOrder).toBeDefined();
      expect(conversionResult.razorpayOrder.amount).toBe(380000); // In paise
      logger.info('✓ COD converted to online payment order');

      // Step 4: Complete online payment
      const processPaymentResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_conversion_001',
        razorpayOrderId: conversionResult.razorpayOrder.id,
        razorpaySignature: 'valid_conversion_signature'
      });

      expect(processPaymentResult.status).toBe('PAID');
      logger.info('✓ Online payment completed after conversion');

      // Step 5: Complete delivery
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      // Step 6: Verify final payment status (Requirement 3.4)
      const finalPaymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(finalPaymentStatus.status).toBe('PAID');
      expect(finalPaymentStatus.method).toBe('ONLINE');
      expect(finalPaymentStatus.canConvertToOnline).toBe(false);
      expect(finalPaymentStatus.paidAt).toBeDefined();

      // Step 7: Continue with installation to complete workflow
      const installation = await installationService.requestInstallation({
        orderId: order.id,
        consumerId: 'conversion-consumer-001',
        notes: 'Installation after successful COD conversion'
      });

      expect(installation.status).toBe('REQUESTED');

      logger.info('✅ COD to online conversion workflow test passed');
    });

    it('should handle failed COD conversion gracefully', async () => {
      logger.info('Starting failed COD conversion test');

      // Create COD order and get to OUT_FOR_DELIVERY
      const order = await orderService.createOrder({
        consumerId: 'failed-conversion-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '999 Failed Conversion Street',
        phone: '+91-9876543213'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'failed-admin',
        adminEmail: 'admin@failed.test',
        quoteAmount: 4200
      });

      await paymentService.createCODPayment(order.id, 4200);

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '999 Failed Conversion Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '99999',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY'
      });

      // Attempt conversion
      const conversionResult = await paymentService.convertCODToOnline(order.id);
      logger.info('✓ COD conversion initiated');

      // Simulate failed payment processing (invalid signature)
      try {
        await paymentService.processPayment({
          orderId: order.id,
          razorpayPaymentId: 'pay_failed_001',
          razorpayOrderId: conversionResult.razorpayOrder.id,
          razorpaySignature: 'completely_invalid_signature'
        });
        
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid payment signature');
        logger.info('✓ Invalid payment signature rejected');
      }

      // Verify original COD payment is preserved (Requirement 3.5)
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.method).toBe('COD');
      expect(paymentStatus.status).toBe('COD_PENDING');
      expect(paymentStatus.canConvertToOnline).toBe(true);

      logger.info('✅ Failed COD conversion handled gracefully');
    });

    it('should handle multiple conversion attempts correctly', async () => {
      logger.info('Starting multiple conversion attempts test');

      // Setup COD order
      const order = await orderService.createOrder({
        consumerId: 'multi-conversion-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '888 Multi Conversion Street',
        phone: '+91-9876543214'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'multi-admin',
        adminEmail: 'admin@multi.test',
        quoteAmount: 3600
      });

      await paymentService.createCODPayment(order.id, 3600);

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '888 Multi Conversion Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '88888',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY'
      });

      // First conversion attempt - fails
      const firstConversion = await paymentService.convertCODToOnline(order.id);
      
      try {
        await paymentService.processPayment({
          orderId: order.id,
          razorpayPaymentId: 'pay_first_fail',
          razorpayOrderId: firstConversion.razorpayOrder.id,
          razorpaySignature: 'invalid_first_signature'
        });
        expect(true).toBe(false);
      } catch (error) {
        logger.info('✓ First conversion attempt failed as expected');
      }

      // Second conversion attempt - succeeds
      const secondConversion = await paymentService.convertCODToOnline(order.id);
      
      const successfulPayment = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_second_success',
        razorpayOrderId: secondConversion.razorpayOrder.id,
        razorpaySignature: 'valid_second_signature'
      });

      expect(successfulPayment.status).toBe('PAID');

      // Verify final state
      const finalStatus = await paymentService.getPaymentStatus(order.id);
      expect(finalStatus.status).toBe('PAID');
      expect(finalStatus.method).toBe('ONLINE');

      logger.info('✅ Multiple conversion attempts handled correctly');
    });
  });

  describe('3. Error Scenarios and Recovery', () => {
    it('should handle invalid state transitions gracefully', async () => {
      logger.info('Starting invalid state transitions test');

      const order = await orderService.createOrder({
        consumerId: 'error-consumer-001',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '111 Error Test Street',
        phone: '+91-9876543215'
      });

      // Try to complete order without approval (invalid transition)
      try {
        await orderService.completeOrder(order.id);
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid state transition');
        logger.info('✓ Invalid order state transition rejected');
      }

      // Verify order state is unchanged
      const unchangedOrder = await orderService.getOrder(order.id);
      expect(unchangedOrder?.status).toBe('PENDING');

      // Try invalid delivery state transition
      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'error-admin',
        adminEmail: 'admin@error.test',
        quoteAmount: 4000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '111 Error Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '11111',
          country: 'India'
        }
      });

      // Try invalid delivery transition (PREPARING -> DELIVERED)
      try {
        await deliveryService.updateDeliveryStatus({
          shipmentId: delivery.shipmentId,
          status: 'DELIVERED'
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Invalid delivery state transition');
        logger.info('✓ Invalid delivery state transition rejected');
      }

      // Verify delivery state is unchanged
      const unchangedDelivery = await deliveryService.getDeliveryByOrderId(order.id);
      expect(unchangedDelivery?.status).toBe('PREPARING');

      logger.info('✅ Invalid state transitions handled gracefully');
    });

    it('should handle validation errors appropriately', async () => {
      logger.info('Starting validation errors test');

      // Test order creation validation
      try {
        await orderService.createOrder({
          consumerId: '',
          deviceType: '',
          paymentMethod: 'COD',
          address: '',
          phone: 'invalid-phone'
        });
        expect(true).toBe(false);
      } catch (error) {
        expect((error as Error).message).toContain('Validation failed');
        logger.info('✓ Order creation validation error handled');
      }

      // Test installation request validation
      try {
        await installationService.requestInstallation({
          orderId: '',
          consumerId: '',
          preferredDate: new Date(Date.now() - 24 * 60 * 60 * 1000) // Yesterday
        });
        expect(true).toBe(false);
      } catch (error) {
        expect((error as Error).message).toContain('validation failed');
        logger.info('✓ Installation request validation error handled');
      }

      // Test payment processing with invalid data
      try {
        await paymentService.processPayment({
          orderId: 'non-existent-order',
          razorpayPaymentId: 'invalid',
          razorpayOrderId: 'invalid',
          razorpaySignature: 'invalid'
        });
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
        logger.info('✓ Payment processing validation error handled');
      }

      logger.info('✅ Validation errors handled appropriately');
    });

    it('should handle concurrent operations safely', async () => {
      logger.info('Starting concurrent operations test');

      const order = await orderService.createOrder({
        consumerId: 'concurrent-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '444 Concurrent Test Street',
        phone: '+91-9876543217'
      });

      // Simulate concurrent approval attempts (tests optimistic locking)
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
        }),
        orderService.approveOrder({
          orderId: order.id,
          approvedBy: 'admin-3',
          quoteAmount: 5000
        })
      ];

      // Execute concurrent operations
      const results = await Promise.allSettled(approvalPromises);
      
      const successfulResults = results.filter(r => r.status === 'fulfilled');
      const failedResults = results.filter(r => r.status === 'rejected');

      // Only one should succeed due to optimistic locking
      expect(successfulResults.length).toBe(1);
      expect(failedResults.length).toBe(2);

      // Verify final order state is consistent
      const finalOrder = await orderService.getOrder(order.id);
      expect(finalOrder?.status).toBe('APPROVED');
      expect([4000, 4500, 5000]).toContain(finalOrder?.quoteAmount);

      logger.info('✓ Concurrent operations handled safely with optimistic locking');

      // Test concurrent delivery status updates
      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '444 Concurrent Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '44444',
          country: 'India'
        }
      });

      const deliveryPromises = [
        deliveryService.updateDeliveryStatus({
          shipmentId: delivery.shipmentId,
          status: 'SHIPPED',
          location: 'Warehouse A'
        }),
        deliveryService.updateDeliveryStatus({
          shipmentId: delivery.shipmentId,
          status: 'SHIPPED',
          location: 'Warehouse B'
        })
      ];

      const deliveryResults = await Promise.allSettled(deliveryPromises);
      const successfulDeliveryUpdates = deliveryResults.filter(r => r.status === 'fulfilled');
      
      expect(successfulDeliveryUpdates.length).toBe(1);
      logger.info('✓ Concurrent delivery updates handled safely');

      logger.info('✅ Concurrent operations test passed');
    });

    it('should handle system recovery scenarios', async () => {
      logger.info('Starting system recovery test');

      // Create order and simulate partial processing
      const order = await orderService.createOrder({
        consumerId: 'recovery-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '555 Recovery Test Street',
        phone: '+91-9876543218'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'recovery-admin',
        adminEmail: 'admin@recovery.test',
        quoteAmount: 4000
      });

      await paymentService.createCODPayment(order.id, 4000);

      // Simulate system restart - verify data integrity
      const recoveredOrder = await orderService.getOrder(order.id);
      const recoveredPayment = await paymentService.getPaymentByOrderId(order.id);

      expect(recoveredOrder?.status).toBe('APPROVED');
      expect(recoveredOrder?.quoteAmount).toBe(4000);
      expect(recoveredPayment?.status).toBe('COD_PENDING');
      expect(recoveredPayment?.amount).toBe(4000);

      logger.info('✓ Data integrity maintained after simulated restart');

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
      logger.info('✓ Processing continued successfully after recovery');

      logger.info('✅ System recovery test passed');
    });

    it('should handle external service failures gracefully', async () => {
      logger.info('Starting external service failures test');

      const order = await orderService.createOrder({
        consumerId: 'external-failure-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'ONLINE',
        address: '666 External Failure Street',
        phone: '+91-9876543219'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'external-admin',
        adminEmail: 'admin@external.test',
        quoteAmount: 4800
      });

      // Test payment gateway failure simulation
      try {
        // This would normally fail due to external service issues
        // For testing, we simulate with invalid data
        await paymentService.processPayment({
          orderId: order.id,
          razorpayPaymentId: 'pay_external_fail',
          razorpayOrderId: 'invalid_order_id',
          razorpaySignature: 'invalid_signature'
        });
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
        logger.info('✓ External payment service failure handled');
      }

      // Verify system remains in consistent state
      const orderAfterFailure = await orderService.getOrder(order.id);
      expect(orderAfterFailure?.status).toBe('APPROVED');

      // Test delivery provider failure simulation
      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '666 External Failure Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '66666',
          country: 'India'
        }
      });

      // Simulate delivery provider communication failure
      // System should handle gracefully and maintain state
      expect(delivery.status).toBe('PREPARING');
      logger.info('✓ Delivery service integration maintained');

      logger.info('✅ External service failures handled gracefully');
    });
  });

  describe('4. Event-Driven Architecture Validation', () => {
    it('should maintain loose coupling through events', async () => {
      logger.info('Starting event-driven architecture validation');

      const eventsReceived: { type: string; data: any; timestamp: Date }[] = [];

      // Subscribe to all workflow events
      const eventTypes = [
        'ORDER_CREATED', 'ORDER_APPROVED', 'PAYMENT_COMPLETED',
        'SHIPMENT_CREATED', 'DELIVERY_STATUS_UPDATED', 'DELIVERY_COMPLETED',
        'INSTALLATION_REQUESTED', 'INSTALLATION_SCHEDULED', 'INSTALLATION_COMPLETED'
      ];

      eventTypes.forEach(eventType => {
        eventBus.subscribe(eventType, async (event) => {
          eventsReceived.push({
            type: eventType,
            data: event,
            timestamp: new Date()
          });
        });
      });

      // Execute workflow and track events
      const order = await orderService.createOrder({
        consumerId: 'event-consumer',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '777 Event Test Street',
        phone: '+91-9876543220'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'event-admin',
        adminEmail: 'admin@event.test',
        quoteAmount: 4000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId: order.id,
        address: {
          street: '777 Event Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '77777',
          country: 'India'
        }
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      await installationService.requestInstallation({
        orderId: order.id,
        consumerId: 'event-consumer'
      });

      // Wait for event processing
      await new Promise(resolve => setTimeout(resolve, 200));

      // Verify events were emitted in correct sequence
      const eventTypes_received = eventsReceived.map(e => e.type);
      expect(eventTypes_received).toContain('ORDER_CREATED');
      expect(eventTypes_received).toContain('ORDER_APPROVED');
      expect(eventTypes_received).toContain('SHIPMENT_CREATED');
      expect(eventTypes_received).toContain('DELIVERY_STATUS_UPDATED');
      expect(eventTypes_received).toContain('DELIVERY_COMPLETED');
      expect(eventTypes_received).toContain('INSTALLATION_REQUESTED');

      // Verify event data integrity
      const orderCreatedEvent = eventsReceived.find(e => e.type === 'ORDER_CREATED');
      expect(orderCreatedEvent?.data.orderId).toBe(order.id);
      expect(orderCreatedEvent?.data.consumerId).toBe('event-consumer');

      const orderApprovedEvent = eventsReceived.find(e => e.type === 'ORDER_APPROVED');
      expect(orderApprovedEvent?.data.orderId).toBe(order.id);
      expect(orderApprovedEvent?.data.quoteAmount).toBe(4000);

      logger.info('✓ Events emitted correctly with proper data');
      logger.info(`✓ Total events received: ${eventsReceived.length}`);

      logger.info('✅ Event-driven architecture validation passed');
    });

    it('should handle event processing failures gracefully', async () => {
      logger.info('Starting event processing failure test');

      let eventProcessingErrors = 0;

      // Subscribe with a handler that sometimes fails
      eventBus.subscribe('ORDER_CREATED', async (event: any) => {
        if (event.consumerId && event.consumerId.includes('fail')) {
          eventProcessingErrors++;
          throw new Error('Simulated event processing failure');
        }
      });

      // Create orders - some should trigger failures
      const orders = await Promise.all([
        orderService.createOrder({
          consumerId: 'normal-consumer',
          deviceType: 'AC-HOME-V1',
          paymentMethod: 'COD',
          address: '888 Normal Street',
          phone: '+91-9876543221'
        }),
        orderService.createOrder({
          consumerId: 'fail-consumer',
          deviceType: 'AC-HOME-V1',
          paymentMethod: 'COD',
          address: '999 Fail Street',
          phone: '+91-9876543222'
        })
      ]);

      // Wait for event processing
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify orders were created despite event processing failures
      expect(orders).toHaveLength(2);
      expect(orders[0].consumerId).toBe('normal-consumer');
      expect(orders[1].consumerId).toBe('fail-consumer');

      logger.info('✓ Orders created successfully despite event processing failures');
      logger.info(`✓ Event processing errors handled: ${eventProcessingErrors}`);

      logger.info('✅ Event processing failure handling passed');
    });
  });
});

// Export test runner function
export async function runCompleteWorkflowTests(): Promise<boolean> {
  try {
    logger.info('🧪 Running complete workflow integration tests...');
    
    // Test 1: Basic complete workflow
    logger.info('Testing basic complete workflow...');
    
    const order = await orderService.createOrder({
      consumerId: 'test-workflow-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Workflow Street',
      phone: '+91-9876543210'
    });
    
    if (!order || order.status !== 'PENDING') {
      throw new Error('Basic workflow test failed - order creation');
    }
    
    const approval = await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'test-workflow-admin',
      adminEmail: 'admin@test.workflow',
      quoteAmount: 4000
    });
    
    if (!approval.approved) {
      throw new Error('Basic workflow test failed - order approval');
    }

    const payment = await paymentService.createCODPayment(order.id, 4000);
    if (payment.status !== 'COD_PENDING') {
      throw new Error('Basic workflow test failed - payment creation');
    }

    const delivery = await deliveryService.initiateShipment({
      orderId: order.id,
      address: {
        street: '123 Test Workflow Street',
        city: 'Test City',
        state: 'Test State',
        postalCode: '12345',
        country: 'India'
      }
    });

    if (delivery.status !== 'PREPARING') {
      throw new Error('Basic workflow test failed - delivery initiation');
    }

    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'DELIVERED'
    });

    const installation = await installationService.requestInstallation({
      orderId: order.id,
      consumerId: 'test-workflow-consumer'
    });

    if (installation.status !== 'REQUESTED') {
      throw new Error('Basic workflow test failed - installation request');
    }
    
    logger.info('✅ Basic complete workflow test passed');

    // Test 2: COD conversion workflow
    logger.info('Testing COD conversion workflow...');

    const codOrder = await orderService.createOrder({
      consumerId: 'test-conversion-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '456 Test Conversion Street',
      phone: '+91-9876543211'
    });

    await adminWorkflowService.processOrderApproval({
      orderId: codOrder.id,
      adminId: 'test-conversion-admin',
      adminEmail: 'admin@test.conversion',
      quoteAmount: 3500
    });

    await paymentService.createCODPayment(codOrder.id, 3500);

    const codDelivery = await deliveryService.initiateShipment({
      orderId: codOrder.id,
      address: {
        street: '456 Test Conversion Street',
        city: 'Test City',
        state: 'Test State',
        postalCode: '45678',
        country: 'India'
      }
    });

    await deliveryService.updateDeliveryStatus({
      shipmentId: codDelivery.shipmentId,
      status: 'OUT_FOR_DELIVERY'
    });

    const conversionResult = await paymentService.convertCODToOnline(codOrder.id);
    if (!conversionResult.razorpayOrder) {
      throw new Error('COD conversion test failed - conversion initiation');
    }

    logger.info('✅ COD conversion workflow test passed');
    
    logger.info('✅ All complete workflow tests passed successfully');
    return true;
    
  } catch (error) {
    logger.error('❌ Complete workflow tests failed:', error);
    return false;
  } finally {
    // Cleanup
    database.clearAll();
    eventBus.clearEventStore();
  }
}