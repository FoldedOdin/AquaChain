/**
 * Consumer Dashboard Tests
 * Tests for consumer dashboard endpoints and functionality
 */

import { orderService } from '../services/order-service';
import { paymentService } from '../services/payment-service';
import { deliveryService } from '../services/delivery-service';
import { installationService } from '../services/installation-service';
import { database } from '../infrastructure/database';
import { initializeSampleData, getSampleConsumerId, getSampleTechnicianId, getSampleDeviceId } from '../infrastructure/sample-data';
import { Device, Technician } from '../types/entities';

describe('Consumer Dashboard', () => {
  let consumerId: string;
  let orderId: string;

  beforeAll(async () => {
    // Clear database and initialize sample data
    database.clearAll();
    initializeSampleData();
    consumerId = getSampleConsumerId();
  });

  beforeEach(async () => {
    // Create a test order for each test
    const order = await orderService.createOrder({
      consumerId,
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Street, Test City, Test State 12345',
      phone: '+91-9876543220'
    });
    orderId = order.id;

    // Create COD payment
    await paymentService.createCODPayment(orderId, 15000);
  });

  describe('Dashboard Data Retrieval', () => {
    test('should retrieve consumer dashboard with order status and available actions', async () => {
      // Get consumer's orders
      const orders = await orderService.getOrdersByConsumer(consumerId);
      expect(orders).toHaveLength(1);
      expect(orders[0].id).toBe(orderId);

      // Get payment information
      const payment = await paymentService.getPaymentByOrderId(orderId);
      expect(payment).toBeTruthy();
      expect(payment!.paymentMethod).toBe('COD');
      expect(payment!.status).toBe('COD_PENDING');

      // Initially no delivery or installation
      const delivery = await deliveryService.getDeliveryByOrderId(orderId);
      const installation = await installationService.getInstallationByOrderId(orderId);
      expect(delivery).toBeNull();
      expect(installation).toBeNull();

      // Available actions should not include pay online or request installation yet
      const canPayOnline = delivery && 
        delivery.status === 'OUT_FOR_DELIVERY' && 
        payment && 
        payment.paymentMethod === 'COD' && 
        payment.status === 'COD_PENDING';
      
      const canRequestInstallation = delivery && 
        delivery.status === 'DELIVERED' && 
        (!installation || installation.status === 'NOT_REQUESTED');

      expect(canPayOnline).toBeFalsy();
      expect(canRequestInstallation).toBeFalsy();
    });

    test('should show "Pay Online Now" option when order is OUT_FOR_DELIVERY with COD', async () => {
      // Approve order first
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      // Create shipment
      const delivery = await deliveryService.initiateShipment({
        orderId,
        address: {
          street: '123 Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '12345',
          country: 'India'
        }
      });

      // Update delivery status to OUT_FOR_DELIVERY
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'OUT_FOR_DELIVERY'
      });

      // Get updated delivery and payment
      const updatedDelivery = await deliveryService.getDeliveryByOrderId(orderId);
      const payment = await paymentService.getPaymentByOrderId(orderId);

      // Check if "Pay Online Now" option should be available
      const canPayOnline = updatedDelivery && 
        updatedDelivery.status === 'OUT_FOR_DELIVERY' && 
        payment && 
        payment.paymentMethod === 'COD' && 
        payment.status === 'COD_PENDING';

      expect(canPayOnline).toBeTruthy();
    });

    test('should show "Request Technician Installation" option when order is DELIVERED', async () => {
      // Approve order and create shipment
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId,
        address: {
          street: '123 Test Street',
          city: 'Test City',
          state: 'Test State',
          postalCode: '12345',
          country: 'India'
        }
      });

      // Update delivery status to DELIVERED
      await deliveryService.updateDeliveryStatus({
        shipmentId: delivery.shipmentId,
        status: 'DELIVERED'
      });

      // Get updated delivery and installation
      const updatedDelivery = await deliveryService.getDeliveryByOrderId(orderId);
      const installation = await installationService.getInstallationByOrderId(orderId);

      // Check if "Request Technician Installation" option should be available
      const canRequestInstallation = updatedDelivery && 
        updatedDelivery.status === 'DELIVERED' && 
        (!installation || installation.status === 'NOT_REQUESTED');

      expect(canRequestInstallation).toBeTruthy();
    });
  });

  describe('COD to Online Payment Conversion', () => {
    test('should successfully convert COD to online payment when OUT_FOR_DELIVERY', async () => {
      // Setup order for conversion
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId,
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
      const conversionResult = await paymentService.convertCODToOnline(orderId);

      expect(conversionResult).toBeTruthy();
      expect(conversionResult.razorpayOrder).toBeTruthy();
      expect(conversionResult.razorpayOrder.amount).toBe(1500000); // 15000 * 100 (paise)
      expect(conversionResult.payment.paymentMethod).toBe('ONLINE');
    });

    test('should fail COD conversion when order is not OUT_FOR_DELIVERY', async () => {
      // Try to convert without proper delivery status
      await expect(paymentService.convertCODToOnline(orderId))
        .rejects.toThrow('Payment order creation failed');
    });
  });

  describe('Installation Request', () => {
    test('should successfully request installation when order is DELIVERED', async () => {
      // Setup delivered order
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId,
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
        status: 'DELIVERED'
      });

      // Request installation
      const installation = await installationService.requestInstallation({
        orderId,
        consumerId,
        preferredDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days from now
      });

      expect(installation).toBeTruthy();
      expect(installation.status).toBe('REQUESTED');
      expect(installation.orderId).toBe(orderId);
      expect(installation.consumerId).toBe(consumerId);
    });

    test('should schedule installation with available technician', async () => {
      // Setup delivered order and request installation
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId,
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
        status: 'DELIVERED'
      });

      const installation = await installationService.requestInstallation({
        orderId,
        consumerId
      });

      // Schedule installation
      const technicianId = getSampleTechnicianId();
      const scheduledDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

      const scheduledInstallation = await installationService.scheduleInstallation({
        installationId: installation.id,
        technicianId,
        scheduledDate
      });

      expect(scheduledInstallation.status).toBe('SCHEDULED');
      expect(scheduledInstallation.technicianId).toBe(technicianId);
      expect(scheduledInstallation.scheduledDate).toEqual(scheduledDate);
    });

    test('should complete installation and transfer device ownership', async () => {
      // Setup and schedule installation
      await orderService.approveOrder({
        orderId,
        approvedBy: 'admin-123',
        quoteAmount: 15000
      });

      const delivery = await deliveryService.initiateShipment({
        orderId,
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
        status: 'DELIVERED'
      });

      const installation = await installationService.requestInstallation({
        orderId,
        consumerId
      });

      const technicianId = getSampleTechnicianId();
      await installationService.scheduleInstallation({
        installationId: installation.id,
        technicianId,
        scheduledDate: new Date()
      });

      // Complete installation
      const deviceId = getSampleDeviceId();
      const completedInstallation = await installationService.completeInstallation({
        installationId: installation.id,
        deviceId,
        calibrationData: { ph: 7.0, tds: 150 }
      });

      expect(completedInstallation.status).toBe('COMPLETED');
      expect(completedInstallation.deviceId).toBe(deviceId);

      // Verify device ownership transfer
      const device = database.findById<Device>('devices', deviceId);
      expect(device).toBeTruthy();
      expect(device!.status).toBe('INSTALLED');
      expect(device!.consumerId).toBe(consumerId);
    });
  });

  describe('Available Technicians', () => {
    test('should return available technicians for a given date', async () => {
      const testDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
      const availableTechnicians = await installationService.getAvailableTechnicians(testDate);

      expect(availableTechnicians.length).toBeGreaterThan(0);
      
      // All returned technicians should be available
      availableTechnicians.forEach(tech => {
        expect(tech.availability).toBe('AVAILABLE');
      });
    });

    test('should filter out busy technicians', async () => {
      const allTechnicians = database.findAll<Technician>('technicians');
      const busyTechnicians = allTechnicians.filter((t: Technician) => t.availability === 'BUSY');
      
      const testDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
      const availableTechnicians = await installationService.getAvailableTechnicians(testDate);

      // Available technicians should not include busy ones
      availableTechnicians.forEach(tech => {
        expect(busyTechnicians.find((bt: Technician) => bt.id === tech.id)).toBeUndefined();
      });
    });
  });
});

/**
 * Run consumer dashboard tests
 */
export async function runConsumerDashboardTests(): Promise<boolean> {
  console.log('🧪 Running Consumer Dashboard Tests...');
  
  try {
    // This would integrate with a proper test runner in production
    // For now, we'll run a simple validation
    
    // Clear database and initialize sample data
    database.clearAll();
    initializeSampleData();
    
    const consumerId = getSampleConsumerId();
    if (!consumerId) {
      throw new Error('No sample consumer found');
    }

    // Test order creation
    const order = await orderService.createOrder({
      consumerId,
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Street, Test City, Test State 12345',
      phone: '+91-9876543220'
    });

    console.log('✅ Order creation test passed');

    // Test COD payment creation
    await paymentService.createCODPayment(order.id, 15000);
    console.log('✅ COD payment creation test passed');

    // Test order approval and delivery flow
    await orderService.approveOrder({
      orderId: order.id,
      approvedBy: 'admin-123',
      quoteAmount: 15000
    });

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

    console.log('✅ Delivery flow test passed');

    // Test COD to online conversion
    await paymentService.convertCODToOnline(order.id);
    console.log('✅ COD to online conversion test passed');

    // Test delivery completion and installation request
    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'DELIVERED'
    });

    const installation = await installationService.requestInstallation({
      orderId: order.id,
      consumerId
    });

    console.log('✅ Installation request test passed');

    // Test technician scheduling
    const technicianId = getSampleTechnicianId();
    if (technicianId) {
      await installationService.scheduleInstallation({
        installationId: installation.id,
        technicianId,
        scheduledDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      });
      console.log('✅ Installation scheduling test passed');
    }

    console.log('🎉 All Consumer Dashboard tests passed!');
    return true;

  } catch (error) {
    console.error('❌ Consumer Dashboard tests failed:', error);
    return false;
  }
}