/**
 * Standalone Test Runner for Complete Workflow Integration Tests
 * Task 12.2: Write integration tests for complete workflows
 */

const { orderService } = require('./src/services/order-service');
const { paymentService } = require('./src/services/payment-service');
const { deliveryService } = require('./src/services/delivery-service');
const { installationService } = require('./src/services/installation-service');
const { adminWorkflowService } = require('./src/services/admin-workflow-service');
const { database } = require('./src/infrastructure/database');
const { eventBus } = require('./src/infrastructure/event-bus');

console.log('🧪 Running Complete Workflow Integration Tests - Task 12.2');
console.log('=========================================================');

async function runCompleteWorkflowTests() {
  let testsPassed = 0;
  let testsFailed = 0;

  // Helper function to run a test
  async function runTest(testName, testFn) {
    try {
      console.log(`\n🔄 Running: ${testName}`);
      
      // Clear database and event bus before each test
      database.clearAll();
      eventBus.clearEventStore();
      
      await testFn();
      console.log(`✅ PASSED: ${testName}`);
      testsPassed++;
    } catch (error) {
      console.error(`❌ FAILED: ${testName}`);
      console.error(`   Error: ${error.message}`);
      testsFailed++;
    }
  }

  // Test 1: Complete COD Order Workflow
  await runTest('Complete COD Order-to-Installation Workflow', async () => {
    // Step 1: Create COD order
    const order = await orderService.createOrder({
      consumerId: 'test-consumer-001',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '123 Test Workflow Street, Test City',
      phone: '+91-9876543210'
    });

    if (!order || order.status !== 'PENDING') {
      throw new Error('Order creation failed');
    }

    // Step 2: Admin approval
    const approvalResult = await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'test-admin-001',
      adminEmail: 'admin@test.com',
      quoteAmount: 4500
    });

    if (!approvalResult.approved || approvalResult.order.status !== 'APPROVED') {
      throw new Error('Order approval failed');
    }

    // Step 3: Create COD payment
    const payment = await paymentService.createCODPayment(order.id, 4500);
    if (payment.status !== 'COD_PENDING') {
      throw new Error('COD payment creation failed');
    }

    // Step 4: Create and progress delivery
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
      throw new Error('Delivery initiation failed');
    }

    // Progress through delivery states
    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'SHIPPED'
    });

    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'OUT_FOR_DELIVERY'
    });

    const deliveredShipment = await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'DELIVERED'
    });

    if (deliveredShipment.status !== 'DELIVERED') {
      throw new Error('Delivery completion failed');
    }

    // Step 5: Consumer requests installation
    const installation = await installationService.requestInstallation({
      orderId: order.id,
      consumerId: 'test-consumer-001'
    });

    if (installation.status !== 'REQUESTED') {
      throw new Error('Installation request failed');
    }

    console.log('   ✓ Complete COD workflow executed successfully');
  });

  // Test 2: COD to Online Payment Conversion
  await runTest('COD to Online Payment Conversion Workflow', async () => {
    // Setup COD order to OUT_FOR_DELIVERY
    const order = await orderService.createOrder({
      consumerId: 'conversion-consumer-001',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '456 Conversion Test Street',
      phone: '+91-9876543211'
    });

    await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'conversion-admin-001',
      adminEmail: 'admin@conversion.test',
      quoteAmount: 3800
    });

    await paymentService.createCODPayment(order.id, 3800);

    const delivery = await deliveryService.initiateShipment({
      orderId: order.id,
      address: {
        street: '456 Conversion Test Street',
        city: 'Test City',
        state: 'Test State',
        postalCode: '45678',
        country: 'India'
      }
    });

    await deliveryService.updateDeliveryStatus({
      shipmentId: delivery.shipmentId,
      status: 'OUT_FOR_DELIVERY'
    });

    // Verify COD conversion option is available
    const paymentStatus = await paymentService.getPaymentStatus(order.id);
    if (!paymentStatus.canConvertToOnline) {
      throw new Error('COD conversion option not available');
    }

    // Convert COD to online payment
    const conversionResult = await paymentService.convertCODToOnline(order.id);
    if (!conversionResult.razorpayOrder) {
      throw new Error('COD conversion failed');
    }

    // Simulate successful online payment
    const processedPayment = await paymentService.processPayment({
      orderId: order.id,
      razorpayPaymentId: 'pay_conversion_test_001',
      razorpayOrderId: conversionResult.razorpayOrder.id,
      razorpaySignature: 'valid_test_signature'
    });

    if (processedPayment.status !== 'PAID') {
      throw new Error('Online payment processing failed');
    }

    // Verify final payment status
    const finalStatus = await paymentService.getPaymentStatus(order.id);
    if (finalStatus.status !== 'PAID' || finalStatus.method !== 'ONLINE') {
      throw new Error('Payment conversion verification failed');
    }

    console.log('   ✓ COD to online conversion executed successfully');
  });

  // Test 3: Online Payment Workflow
  await runTest('Complete Online Payment Workflow', async () => {
    // Create online payment order
    const order = await orderService.createOrder({
      consumerId: 'online-consumer-001',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'ONLINE',
      address: '789 Online Test Street',
      phone: '+91-9876543212'
    });

    await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'online-admin-001',
      adminEmail: 'admin@online.test',
      quoteAmount: 5200
    });

    // Create Razorpay payment order
    const paymentOrderResult = await paymentService.createPaymentOrder({
      orderId: order.id,
      amount: 5200
    });

    if (!paymentOrderResult.razorpayOrder) {
      throw new Error('Razorpay order creation failed');
    }

    // Process payment
    const processedPayment = await paymentService.processPayment({
      orderId: order.id,
      razorpayPaymentId: 'pay_online_test_001',
      razorpayOrderId: paymentOrderResult.razorpayOrder.id,
      razorpaySignature: 'valid_online_signature'
    });

    if (processedPayment.status !== 'PAID') {
      throw new Error('Online payment processing failed');
    }

    console.log('   ✓ Online payment workflow executed successfully');
  });

  // Test 4: Error Handling and Recovery
  await runTest('Error Handling and State Validation', async () => {
    const order = await orderService.createOrder({
      consumerId: 'error-test-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '999 Error Test Street',
      phone: '+91-9876543213'
    });

    // Test invalid state transition
    try {
      await orderService.completeOrder(order.id);
      throw new Error('Should have failed - invalid state transition');
    } catch (error) {
      if (!error.message.includes('Invalid state transition')) {
        throw new Error('Wrong error type for invalid state transition');
      }
    }

    // Test invalid payment processing
    try {
      await paymentService.processPayment({
        orderId: 'non-existent-order',
        razorpayPaymentId: 'invalid',
        razorpayOrderId: 'invalid',
        razorpaySignature: 'invalid'
      });
      throw new Error('Should have failed - invalid payment data');
    } catch (error) {
      // Expected to fail
    }

    // Test validation errors
    try {
      await orderService.createOrder({
        consumerId: '',
        deviceType: '',
        paymentMethod: 'COD',
        address: '',
        phone: 'invalid'
      });
      throw new Error('Should have failed - validation error');
    } catch (error) {
      if (!error.message.includes('Validation failed')) {
        throw new Error('Wrong error type for validation failure');
      }
    }

    console.log('   ✓ Error handling and validation working correctly');
  });

  // Test 5: Event-Driven Architecture
  await runTest('Event-Driven Architecture Validation', async () => {
    const eventsReceived = [];

    // Subscribe to events
    const eventTypes = ['ORDER_CREATED', 'ORDER_APPROVED', 'SHIPMENT_CREATED'];
    eventTypes.forEach(eventType => {
      eventBus.subscribe(eventType, async () => {
        eventsReceived.push(eventType);
      });
    });

    // Execute workflow
    const order = await orderService.createOrder({
      consumerId: 'event-test-consumer',
      deviceType: 'AC-HOME-V1',
      paymentMethod: 'COD',
      address: '888 Event Test Street',
      phone: '+91-9876543214'
    });

    await adminWorkflowService.processOrderApproval({
      orderId: order.id,
      adminId: 'event-admin',
      adminEmail: 'admin@event.test',
      quoteAmount: 4000
    });

    await deliveryService.initiateShipment({
      orderId: order.id,
      address: {
        street: '888 Event Test Street',
        city: 'Test City',
        state: 'Test State',
        postalCode: '88888',
        country: 'India'
      }
    });

    // Wait for event processing
    await new Promise(resolve => setTimeout(resolve, 100));

    // Verify events were emitted
    if (!eventsReceived.includes('ORDER_CREATED')) {
      throw new Error('ORDER_CREATED event not received');
    }
    if (!eventsReceived.includes('ORDER_APPROVED')) {
      throw new Error('ORDER_APPROVED event not received');
    }
    if (!eventsReceived.includes('SHIPMENT_CREATED')) {
      throw new Error('SHIPMENT_CREATED event not received');
    }

    console.log('   ✓ Event-driven architecture working correctly');
  });

  // Test Summary
  console.log('\n📊 Test Results Summary');
  console.log('========================');
  console.log(`✅ Tests Passed: ${testsPassed}`);
  console.log(`❌ Tests Failed: ${testsFailed}`);
  console.log(`📈 Success Rate: ${Math.round((testsPassed / (testsPassed + testsFailed)) * 100)}%`);

  if (testsFailed === 0) {
    console.log('\n🎉 All integration tests passed successfully!');
    console.log('✅ Task 12.2 - Complete workflow integration tests implemented');
    return true;
  } else {
    console.log('\n⚠️  Some tests failed. Please review the errors above.');
    return false;
  }
}

// Run the tests
runCompleteWorkflowTests()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
  });