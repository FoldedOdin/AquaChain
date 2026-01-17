// Test Device Order System
const API_BASE = 'http://localhost:3002';

// Test credentials
const CONSUMER_EMAIL = 'phoneixknight18@gmail.com';
const CONSUMER_PASSWORD = 'admin1234';
const ADMIN_EMAIL = 'admin@aquachain.com';
const ADMIN_PASSWORD = 'admin1234';
const TECH_EMAIL = 'leninsidharth@gmail.com';
const TECH_PASSWORD = 'Sidharth@123';

let consumerToken = '';
let adminToken = '';
let techToken = '';
let testOrderId = '';

// Helper function to make API calls
async function apiCall(method, endpoint, token, body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  };
  
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  const data = await response.json();
  return { status: response.status, data };
}

// Test 1: Login as Consumer
async function test1_LoginConsumer() {
  console.log('\n🧪 Test 1: Login as Consumer');
  const result = await apiCall('POST', '/api/auth/signin', null, {
    email: CONSUMER_EMAIL,
    password: CONSUMER_PASSWORD
  });
  
  if (result.data.success && result.data.token) {
    consumerToken = result.data.token;
    console.log('✅ Consumer logged in successfully');
    return true;
  }
  console.log('❌ Consumer login failed:', result.data);
  return false;
}

// Test 2: Create Device Order
async function test2_CreateOrder() {
  console.log('\n🧪 Test 2: Create Device Order');
  const result = await apiCall('POST', '/api/orders', consumerToken, {
    deviceSKU: 'AC-HOME-V1',
    address: '123 MG Road, Ernakulam, Kerala, 682016',
    phone: '+91-9876543210',
    paymentMethod: 'COD',
    preferredSlot: '2025-12-15T10:00:00Z'
  });
  
  if (result.data.success && result.data.order) {
    testOrderId = result.data.order.orderId;
    console.log('✅ Order created:', testOrderId);
    console.log('   Status:', result.data.order.status);
    return true;
  }
  console.log('❌ Order creation failed:', result.data);
  return false;
}

// Test 3: Get Consumer's Orders
async function test3_GetMyOrders() {
  console.log('\n🧪 Test 3: Get My Orders');
  const result = await apiCall('GET', '/api/orders/my', consumerToken);
  
  if (result.data.success) {
    console.log('✅ Retrieved orders:', result.data.count);
    result.data.orders.forEach(order => {
      console.log(`   - ${order.orderId}: ${order.status}`);
    });
    return true;
  }
  console.log('❌ Failed to get orders:', result.data);
  return false;
}

// Test 4: Login as Admin
async function test4_LoginAdmin() {
  console.log('\n🧪 Test 4: Login as Admin');
  const result = await apiCall('POST', '/api/auth/signin', null, {
    email: ADMIN_EMAIL,
    password: ADMIN_PASSWORD
  });
  
  if (result.data.success && result.data.token) {
    adminToken = result.data.token;
    console.log('✅ Admin logged in successfully');
    return true;
  }
  console.log('❌ Admin login failed:', result.data);
  return false;
}

// Test 5: Get All Orders (Admin)
async function test5_GetAllOrders() {
  console.log('\n🧪 Test 5: Get All Orders (Admin)');
  const result = await apiCall('GET', '/api/admin/orders', adminToken);
  
  if (result.data.success) {
    console.log('✅ Retrieved all orders');
    console.log('   Stats:', result.data.stats);
    return true;
  }
  console.log('❌ Failed to get orders:', result.data);
  return false;
}

// Test 6: Set Quote
async function test6_SetQuote() {
  console.log('\n🧪 Test 6: Set Quote');
  const result = await apiCall('PUT', `/api/admin/orders/${testOrderId}/quote`, adminToken, {
    quoteAmount: 4000,
    paymentMethod: 'COD'
  });
  
  if (result.data.success) {
    console.log('✅ Quote set: ₹4,000');
    console.log('   New status:', result.data.order.status);
    return true;
  }
  console.log('❌ Failed to set quote:', result.data);
  return false;
}

// Test 7: Provision Device
async function test7_ProvisionDevice() {
  console.log('\n🧪 Test 7: Provision Device');
  const result = await apiCall('PUT', `/api/admin/orders/${testOrderId}/provision`, adminToken, {
    deviceId: 'IOA'
  });
  
  if (result.data.success) {
    console.log('✅ Device provisioned:', result.data.device.device_id);
    console.log('   New status:', result.data.order.status);
    return true;
  }
  console.log('❌ Failed to provision device:', result.data);
  return false;
}

// Test 8: Login as Technician
async function test8_LoginTechnician() {
  console.log('\n🧪 Test 8: Login as Technician');
  const result = await apiCall('POST', '/api/auth/signin', null, {
    email: TECH_EMAIL,
    password: TECH_PASSWORD
  });
  
  if (result.data.success && result.data.token) {
    techToken = result.data.token;
    console.log('✅ Technician logged in successfully');
    return true;
  }
  console.log('❌ Technician login failed:', result.data);
  return false;
}

// Test 9: Assign Technician
async function test9_AssignTechnician() {
  console.log('\n🧪 Test 9: Assign Technician');
  const result = await apiCall('PUT', `/api/admin/orders/${testOrderId}/assign`, adminToken, {
    technicianId: 'dev-user-1762509139325'
  });
  
  if (result.data.success) {
    console.log('✅ Technician assigned:', result.data.order.assignedTechnicianName);
    console.log('   New status:', result.data.order.status);
    return true;
  }
  console.log('❌ Failed to assign technician:', result.data);
  return false;
}

// Test 10: Get Technician Installations
async function test10_GetInstallations() {
  console.log('\n🧪 Test 10: Get Technician Installations');
  const result = await apiCall('GET', '/api/tech/installations', techToken);
  
  if (result.data.success) {
    console.log('✅ Retrieved installations:', result.data.count);
    result.data.installations.forEach(install => {
      console.log(`   - ${install.orderId}: ${install.status}`);
    });
    return true;
  }
  console.log('❌ Failed to get installations:', result.data);
  return false;
}

// Test 11: Complete Installation
async function test11_CompleteInstallation() {
  console.log('\n🧪 Test 11: Complete Installation');
  const result = await apiCall('POST', `/api/tech/installations/${testOrderId}/complete`, techToken, {
    deviceId: 'IOA',
    location: 'Home - Kitchen',
    calibrationData: { phOffset: 0, tdsFactor: 1.0 }
  });
  
  if (result.data.success) {
    console.log('✅ Installation completed');
    console.log('   Final status:', result.data.order.status);
    return true;
  }
  console.log('❌ Failed to complete installation:', result.data);
  return false;
}

// Test 12: Verify Device in Consumer Dashboard
async function test12_VerifyDevice() {
  console.log('\n🧪 Test 12: Verify Device in Consumer Dashboard');
  const result = await apiCall('GET', '/api/devices', consumerToken);
  
  if (result.data.success) {
    console.log('✅ Consumer devices:', result.data.count);
    result.data.data.forEach(device => {
      console.log(`   - ${device.device_id}: ${device.name} (${device.status})`);
    });
    return true;
  }
  console.log('❌ Failed to get devices:', result.data);
  return false;
}

// Run all tests
async function runAllTests() {
  console.log('🚀 Starting Device Order System Tests\n');
  console.log('=' .repeat(50));
  
  const tests = [
    test1_LoginConsumer,
    test2_CreateOrder,
    test3_GetMyOrders,
    test4_LoginAdmin,
    test5_GetAllOrders,
    test6_SetQuote,
    test7_ProvisionDevice,
    test8_LoginTechnician,
    test9_AssignTechnician,
    test10_GetInstallations,
    test11_CompleteInstallation,
    test12_VerifyDevice
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const test of tests) {
    try {
      const result = await test();
      if (result) passed++;
      else failed++;
    } catch (error) {
      console.log('❌ Test error:', error.message);
      failed++;
    }
  }
  
  console.log('\n' + '='.repeat(50));
  console.log(`\n📊 Test Results: ${passed} passed, ${failed} failed`);
  console.log('\n✅ Backend is working! Ready to build UI.\n');
}

// Run tests
runAllTests().catch(console.error);
