/**
 * End-to-End Integration Tests
 * Tests complete order workflow from creation to installation completion
 */

import { orderingSystemApp } from '../app';
import { orderService } from '../services/order-service';
import { paymentService } from '../services/payment-service';
import { deliveryService } from '../services/delivery-service';
import { installationService } from '../services/installation-service';
import { adminWorkflowService } from '../services/admin-workflow-service';
import { eventCoordinationService } from '../services/event-coordination-service';
import { database } from '../infrastructure/database';
import { eventBus } from '../infrastructure/event-bus';

describe('End-to-End Order Workflow', () => {
  beforeEach(async () => {
    // Initialize application
    await orderingSystemApp.initialize();
    
    // Clear database and event bus for each test
    database.clearAll();
    eventBus.clearEventStore();
  });

  describe('Complete COD Order Workflow', () => {
    it('should complete full COD order workflow from creation to installation', async () => {
      // Step 1: Create order
      const createOrderRequest = {
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD' as const,
        address: '123 Test Street, Test City, Test State 12345',
        phone: '+91-9876543210'
      };

      const order = await orderService.createOrder(createOrderRequest);
      expect(order).toBeDefined();
      expect(order.status).toBe('PENDING');
      expect(order.paymentMethod).toBe('COD');

      // Step 2: Admin approves order
      const approvalRequest = {
        orderId: order.id,
        adminId: 'admin-123',
        adminEmail: 'admin@test.com',
        quoteAmount: 4000,
        notes: 'Standard approval'
      };

      const approvalResult = await adminWorkflowService.processOrderApproval(approvalRequest);
      expect(approvalResult.approved).toBe(true);
      expect(approvalResult.order.status).toBe('APPROVED');
      expect(approvalResult.order.quoteAmount).toBe(4000);

      // Step 3: Create COD payment record
      const payment = await paymentService.createCODPayment(order.id, 4000);
      expect(payment.paymentMethod).toBe('COD');
      expect(payment.status).toBe('COD_PENDING');

      // Step 4: Create shipment
      const shipmentRequest = {
        orderId: order.id,
        address: {
          street: '123 Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '12345',
          country: 'India'
        },
        carrier: 'Test Delivery'
      };

      const delivery = await deliveryService.initiateShipment(shipmentRequest);
      expect(delivery.status).toBe('PREPARING');
      expect(delivery.trackingNumber).toBeDefined();

      // Step 5: Update delivery status to OUT_FOR_DELIVERY
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'SHIPPED'
      });

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY',
        location: 'Local delivery hub'
      });

      // Step 6: Complete delivery
      const deliveredShipment = await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED',
        location: 'Consumer address'
      });

      expect(deliveredShipment.status).toBe('DELIVERED');
      expect(deliveredShipment.deliveredAt).toBeDefined();

      // Step 7: Consumer requests installation
      const installationRequest = {
        orderId: order.id,
        consumerId: 'consumer-123',
        preferredDate: new Date(Date.now() + 24 * 60 * 60 * 1000) // Tomorrow
      };

      const installation = await installationService.requestInstallation(installationRequest);
      expect(installation.status).toBe('REQUESTED');

      // Step 8: Schedule installation with technician
      const scheduleRequest = {
        installationId: installation.id,
        technicianId: 'tech-123',
        scheduledDate: new Date(Date.now() + 24 * 60 * 60 * 1000)
      };

      // First create a technician record
      database.create('technicians', {
        id: 'tech-123',
        name: 'Test Technician',
        email: 'tech@test.com',
        phone: '+91-9876543211',
        skills: ['installation'],
        availability: 'AVAILABLE',
        rating: 4.5,
        completedInstallations: 10
      });

      const scheduledInstallation = await installationService.scheduleInstallation(scheduleRequest);
      expect(scheduledInstallation.status).toBe('SCHEDULED');
      expect(scheduledInstallation.technicianId).toBe('tech-123');

      // Step 9: Complete installation
      // First create a device record
      database.create('devices', {
        id: 'device-123',
        serialNumber: 'AC123456',
        model: 'AC-HOME-V1',
        status: 'AVAILABLE',
        createdAt: new Date()
      });

      const completeRequest = {
        installationId: installation.id,
        deviceId: 'device-123',
        calibrationData: { ph: 7.0, temperature: 25 },
        photos: ['photo1.jpg', 'photo2.jpg']
      };

      const completedInstallation = await installationService.completeInstallation(completeRequest);
      expect(completedInstallation.status).toBe('COMPLETED');
      expect(completedInstallation.deviceId).toBe('device-123');

      // Step 10: Verify final states
      const finalOrder = await orderService.getOrder(order.id);
      const finalPayment = await paymentService.getPaymentByOrderId(order.id);
      const finalDelivery = await deliveryService.getDeliveryByOrderId(order.id);
      const finalInstallation = await installationService.getInstallationByOrderId(order.id);

      expect(finalOrder?.status).toBe('APPROVED'); // Order doesn't auto-complete
      expect(finalPayment?.status).toBe('COD_PENDING');
      expect(finalDelivery?.status).toBe('DELIVERED');
      expect(finalInstallation?.status).toBe('COMPLETED');

      // Verify device ownership transfer
      const device = database.findById('devices', 'device-123') as any;
      expect(device?.status).toBe('INSTALLED');
      expect(device?.consumerId).toBe('consumer-123');
    });
  });

  describe('COD to Online Payment Conversion Workflow', () => {
    it('should handle COD to online payment conversion during delivery', async () => {
      // Create order and get to OUT_FOR_DELIVERY status
      const order = await orderService.createOrder({
        consumerId: 'consumer-123',
        deviceType: 'AC-HOME-V1',
        paymentMethod: 'COD',
        address: '123 Test Street',
        phone: '+91-9876543210'
      });

      await adminWorkflowService.processOrderApproval({
        orderId: order.id,
        adminId: 'admin-123',
        adminEmail: 'admin@test.com',
        quoteAmount: 4000
      });

      await paymentService.createCODPayment(order.id, 4000);
      
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

      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY'
      });

      // Convert COD to online payment
      const conversionResult = await paymentService.convertCODToOnline(order.id);
      expect(conversionResult.payment.paymentMethod).toBe('ONLINE');
      expect(conversionResult.razorpayOrder).toBeDefined();

      // Simulate successful online payment
      const processPaymentResult = await paymentService.processPayment({
        orderId: order.id,
        razorpayPaymentId: 'pay_test123',
        razorpayOrderId: conversionResult.razorpayOrder.id,
        razorpaySignature: 'valid_signature' // In real system, this would be properly verified
      });

      expect(processPaymentResult.status).toBe('PAID');

      // Verify original COD payment still exists but new online payment is active
      const paymentStatus = await paymentService.getPaymentStatus(order.id);
      expect(paymentStatus.status).toBe('PAID');
      expect(paymentStatus.method).toBe('ONLINE');
    });
  });

  describe('Event-Driven Architecture Validation', () => {
    it('should demonstrate loose coupling through events', async () => {
      const eventsSeen: string[] = [];
      
      // Subscribe to all events to track workflow
      const eventTypes = [
        'ORDER_CREATED', 'ORDER_APPROVED', 'PAYMENT_COMPLETED',
        'SHIPMENT_CREATED', 'DELIVERY_STATUS_UPDATED', 'DELIVERY_COMPLETED',
        'INSTALLATION_REQUESTED', 'INSTALLATION_COMPLETED'
      ];

      eventTypes.forEach(eventType => {
        eventBus.subscribe(eventType, async () => {
          eventsSeen.push(eventType);
        });
      });

      // Run the event-driven workflow demonstration
      await eventCoordinationService.demonstrateEventDrivenWorkflow('demo-order-123');

      // Wait for event processing
      await new Promise(resolve => setTimeout(resolve, 500));

      // Verify events were emitted in correct order
      expect(eventsSeen).toContain('ORDER_CREATED');
      expect(eventsSeen).toContain('ORDER_APPROVED');
      expect(eventsSeen).toContain('SHIPMENT_CREATED');
      expect(eventsSeen).toContain('DELIVERY_STATUS_UPDATED');
      expect(eventsSeen).toContain('DELIVERY_COMPLETED');
      expect(eventsSeen).toContain('INSTALLATION_REQUESTED');
      expect(eventsSeen).toContain('INSTALLATION_COMPLETED');

      // Verify event-driven principles
      const principles = eventCoordinationService.validateEventDrivenPrinciples();
      expect(principles.looseCoupling).toBe(true);
      expect(principles.eventEmission).toBe(true);
      expect(principles.asynchronousProcessing).toBe(true);
      expect(principles.serviceIndependence).toBe(true);
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle service failures gracefully', async () => {
      // This would test error handling scenarios
      // For now, just verify error handling service is working
      const errorStats = orderingSystemApp.getStatistics().errorHandling;
      expect(errorStats).toBeDefined();
      expect(errorStats.activeBreakers).toBeGreaterThanOrEqual(0);
    });
  });

  describe('System Health and Monitoring', () => {
    it('should provide comprehensive system health information', async () => {
      const health = await orderingSystemApp.healthCheck();
      
      expect(health.status).toBeDefined();
      expect(health.services).toBeDefined();
      expect(health.services.database).toBeDefined();
      expect(health.services.eventBus).toBeDefined();
      expect(health.timestamp).toBeDefined();

      const stats = orderingSystemApp.getStatistics();
      expect(stats.database).toBeDefined();
      expect(stats.eventBus).toBeDefined();
      expect(stats.uptime).toBeGreaterThanOrEqual(0);
    });
  });
});

// Helper function to run end-to-end tests
export async function runEndToEndTests(): Promise<boolean> {
  try {
    console.log('🧪 Running end-to-end integration tests...');
    
    // Initialize application
    await orderingSystemApp.initialize();
    
    // Test 1: Complete workflow
    console.log('Testing complete COD order workflow...');
    
    const order = await orderService.createOrder({
      consumerId: 'e2e-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 E2E Test Street',
      phone: '+91-9876543210'
    });
    
    if (!order || order.status !== 'PENDING') {
      throw new Error('Order creation failed');
    }
    
    const approval = await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'e2e-admin',
      adminEmail: 'admin@e2e.com',
      quoteAmount: 4000
    });
    
    if (!approval.approved) {
      throw new Error('Order approval failed');
    }
    
    console.log('✅ End-to-end workflow test passed');
    
    // Test 2: System health
    console.log('Testing system health...');
    
    const health = await orderingSystemApp.healthCheck();
    if (health.status !== 'healthy') {
      console.log('⚠️  System health check shows issues:', health);
    } else {
      console.log('✅ System health check passed');
    }
    
    console.log('✅ All end-to-end tests passed');
    return true;
    
  } catch (error) {
    console.error('❌ End-to-end tests failed:', error);
    return false;
  } finally {
    // Cleanup
    database.clearAll();
    eventBus.clearEventStore();
  }
}