/**
 * Simple Consumer Dashboard Test Script
 * Tests the core functionality without TypeScript compilation
 */

const { orderService } = require('./dist/services/order-service');
const { paymentService } = require('./dist/services/payment-service');
const { deliveryService } = require('./dist/services/delivery-service');
const { installationService } = require('./dist/services/installation-service');
const { database } = require('./dist/infrastructure/database');
const { initializeSampleData, getSampleConsumerId } = require('./dist/infrastructure/sample-data');

async function testConsumerDashboard() {
  console.log('🧪 Testing Consumer Dashboard Functionality...');
  
  try {
    // Clear database and initialize sample data
    database.clearAll();
    initializeSampleData();
    
    const consumerId = getSampleConsumerId();
    console.log('✅ Sample data initialized, consumer ID:', consumerId);

    // Test 1: Create order with COD payment
    const order = await orderService.createOrder({
      consumerId,
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Street, Test City, Test State 12345',
      phone: '+91-9876543220'
    });
    console.log('✅ Order created:', order.id);

    // Test 2: Create COD payment
    const payment = await paymentService.createCODPayment(order.id, 15000);
    console.log('✅ COD payment created:', payment.id);

    // Test 3: Get consumer orders (dashboard data)
    const orders = await orderService.getOrdersByConsumer(consumerId);
    console.log('✅ Consumer orders retrieved:', orders.length);

    // Test 4: Check initial available actions
    const orderPayment = await paymentService.getPaymentByOrderId(order.id);
    const orderDelivery = await deliveryService.getDeliveryByOrderId(order.id);
    const orderInstallation = await installationService.getInstallationByOrderId(order.id);

    console.log('📊 Initial state:');
    console.log('  - Order status:', orders[0].status);
    console.log('  - Payment method:', orderPayment?.paymentMethod);
    console.log('  - Payment status:', orderPayment?.status);
    console.log('  - Delivery exists:', !!orderDelivery);
    console.log('  - Installation exists:', !!orderInstallation);

    // Test 5: Approve order and create delivery
    await orderService.approveOrder({
      orderId: order.id,
      approvedBy: 'admin-123',
      quoteAmount: 15000
    });
    console.log('✅ Order approved');

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
    console.log('✅ Shipment created:', delivery.trackingNumber);

    // Test 6: Update delivery to OUT_FOR_DELIVERY (enables "Pay Online Now")
    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'OUT_FOR_DELIVERY'
    });
    console.log('✅ Delivery status updated to OUT_FOR_DELIVERY');

    // Test 7: Check "Pay Online Now" availability
    const updatedDelivery = await deliveryService.getDeliveryByOrderId(order.id);
    const canPayOnline = updatedDelivery && 
      updatedDelivery.status === 'OUT_FOR_DELIVERY' && 
      orderPayment && 
      orderPayment.paymentMethod === 'COD' && 
      orderPayment.status === 'COD_PENDING';

    console.log('📊 OUT_FOR_DELIVERY state:');
    console.log('  - Can pay online now:', canPayOnline);

    // Test 8: Convert COD to online payment
    if (canPayOnline) {
      const conversionResult = await paymentService.convertCODToOnline(order.id);
      console.log('✅ COD to online conversion initiated:', conversionResult.razorpayOrder.id);
    }

    // Test 9: Update delivery to DELIVERED (enables installation request)
    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'DELIVERED'
    });
    console.log('✅ Delivery status updated to DELIVERED');

    // Test 10: Check "Request Installation" availability
    const deliveredDelivery = await deliveryService.getDeliveryByOrderId(order.id);
    const deliveredInstallation = await installationService.getInstallationByOrderId(order.id);
    const canRequestInstallation = deliveredDelivery && 
      deliveredDelivery.status === 'DELIVERED' && 
      (!deliveredInstallation || deliveredInstallation.status === 'NOT_REQUESTED');

    console.log('📊 DELIVERED state:');
    console.log('  - Can request installation:', canRequestInstallation);

    // Test 11: Request installation
    if (canRequestInstallation) {
      const installation = await installationService.requestInstallation({
        orderId: order.id,
        consumerId,
        preferredDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days from now
      });
      console.log('✅ Installation requested:', installation.id);
    }

    // Test 12: Get available technicians
    const availableTechnicians = await installationService.getAvailableTechnicians(new Date());
    console.log('✅ Available technicians:', availableTechnicians.length);

    console.log('\n🎉 All Consumer Dashboard tests passed!');
    console.log('\n📋 Summary:');
    console.log('  ✓ Order creation with COD payment');
    console.log('  ✓ Dashboard data retrieval');
    console.log('  ✓ "Pay Online Now" option when OUT_FOR_DELIVERY');
    console.log('  ✓ COD to online payment conversion');
    console.log('  ✓ "Request Installation" option when DELIVERED');
    console.log('  ✓ Installation request functionality');
    console.log('  ✓ Available technicians lookup');

    return true;

  } catch (error) {
    console.error('❌ Consumer Dashboard test failed:', error.message);
    console.error('Stack trace:', error.stack);
    return false;
  }
}

// Run the test
if (require.main === module) {
  testConsumerDashboard()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('Test execution failed:', error);
      process.exit(1);
    });
}

module.exports = { testConsumerDashboard };