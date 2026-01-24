/**
 * Verification script for cancel order endpoint fix
 * Tests that endpoints are accessible (not returning 404)
 */

const http = require('http');

// Test configuration
const BASE_URL = 'http://localhost:3003';
const TEST_ORDER_ID = 'test-order-123';

// Mock authentication token (for testing)
const CONSUMER_TOKEN = 'Bearer mock-consumer-token';
const ADMIN_TOKEN = 'Bearer mock-admin-token';

/**
 * Make HTTP request
 */
function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: body
        });
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

/**
 * Test endpoint accessibility
 */
async function testEndpoint(name, method, path, headers = {}, data = null) {
  console.log(`\n🧪 Testing: ${name}`);
  console.log(`   ${method} ${path}`);

  try {
    const options = {
      hostname: 'localhost',
      port: 3003,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const response = await makeRequest(options, data);
    
    if (response.statusCode === 404) {
      console.log(`   ❌ ENDPOINT NOT FOUND (404)`);
      return false;
    } else if (response.statusCode === 401) {
      console.log(`   ✅ ENDPOINT EXISTS (401 - Authentication required)`);
      return true;
    } else if (response.statusCode === 403) {
      console.log(`   ✅ ENDPOINT EXISTS (403 - Authorization required)`);
      return true;
    } else if (response.statusCode === 400) {
      console.log(`   ✅ ENDPOINT EXISTS (400 - Bad request - validation error)`);
      return true;
    } else {
      console.log(`   ✅ ENDPOINT EXISTS (${response.statusCode})`);
      return true;
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log(`   ⚠️  SERVER NOT RUNNING (Connection refused)`);
      return null; // Server not running
    } else {
      console.log(`   ❌ ERROR: ${error.message}`);
      return false;
    }
  }
}

/**
 * Main verification function
 */
async function verifyEndpoints() {
  console.log('🚀 Verifying Cancel Order Endpoint Fix');
  console.log('=====================================');
  
  const tests = [
    {
      name: 'Consumer Cancel Order',
      method: 'PUT',
      path: `/api/v1/consumer/orders/${TEST_ORDER_ID}/cancel`,
      headers: { 'Authorization': CONSUMER_TOKEN },
      data: { reason: 'Test cancellation' }
    },
    {
      name: 'Admin Cancel Order',
      method: 'PUT', 
      path: `/api/v1/admin/orders/${TEST_ORDER_ID}/cancel`,
      headers: { 'Authorization': ADMIN_TOKEN },
      data: { reason: 'Admin test cancellation' }
    },
    {
      name: 'Admin Bulk Cancel',
      method: 'POST',
      path: '/api/v1/admin/orders/bulk-cancel',
      headers: { 'Authorization': ADMIN_TOKEN },
      data: { 
        orders: [{ orderId: TEST_ORDER_ID, reason: 'Bulk test' }],
        defaultReason: 'Bulk cancellation test'
      }
    },
    {
      name: 'Health Check',
      method: 'GET',
      path: '/health'
    },
    {
      name: 'API Health Check',
      method: 'GET',
      path: '/api/health'
    }
  ];

  let serverRunning = true;
  let endpointsFound = 0;
  let endpointsMissing = 0;

  for (const test of tests) {
    const result = await testEndpoint(
      test.name,
      test.method,
      test.path,
      test.headers,
      test.data
    );

    if (result === null) {
      serverRunning = false;
      break;
    } else if (result === true) {
      endpointsFound++;
    } else {
      endpointsMissing++;
    }
  }

  console.log('\n📊 Results Summary');
  console.log('==================');

  if (!serverRunning) {
    console.log('❌ Server is not running');
    console.log('\nTo start the server:');
    console.log('1. npm run build');
    console.log('2. npm start');
    console.log('   OR');
    console.log('   npm run dev (for development)');
  } else {
    console.log(`✅ Endpoints found: ${endpointsFound}`);
    console.log(`❌ Endpoints missing: ${endpointsMissing}`);
    
    if (endpointsMissing === 0) {
      console.log('\n🎉 SUCCESS: All cancel order endpoints are accessible!');
      console.log('The endpoint registration fix is working correctly.');
    } else {
      console.log('\n⚠️  Some endpoints are still missing.');
      console.log('Please check the server logs for route registration.');
    }
  }

  console.log('\n📝 Next Steps:');
  console.log('- Test with real authentication tokens');
  console.log('- Test with valid order IDs');
  console.log('- Verify business logic works correctly');
  console.log('- Check database operations');
}

// Run verification
verifyEndpoints().catch(console.error);