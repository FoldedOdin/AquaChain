/**
 * Test script to verify cancel order endpoints are working
 */

const http = require('http');

// Test configuration
const BASE_URL = 'http://localhost:3002';
const TEST_ORDER_ID = 'ord_1768654588029_lvyicswcg'; // From the terminal log

// Mock tokens (these would be real tokens in actual testing)
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
        try {
          const parsedBody = JSON.parse(body);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: parsedBody
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: body
          });
        }
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
 * Test endpoint
 */
async function testEndpoint(name, method, path, headers = {}, data = null) {
  console.log(`\n🧪 Testing: ${name}`);
  console.log(`   ${method} ${path}`);

  try {
    const options = {
      hostname: 'localhost',
      port: 3002,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const response = await makeRequest(options, data);
    
    console.log(`   Status: ${response.statusCode}`);
    
    if (response.statusCode === 404) {
      console.log(`   ❌ ENDPOINT NOT FOUND`);
      return false;
    } else if (response.statusCode === 401) {
      console.log(`   ⚠️  AUTHENTICATION REQUIRED (endpoint exists)`);
      return true;
    } else if (response.statusCode === 403) {
      console.log(`   ⚠️  AUTHORIZATION REQUIRED (endpoint exists)`);
      return true;
    } else if (response.statusCode === 400) {
      console.log(`   ⚠️  BAD REQUEST (endpoint exists, validation error)`);
      console.log(`   Message: ${response.body.error || response.body.message || 'Unknown error'}`);
      return true;
    } else if (response.statusCode >= 200 && response.statusCode < 300) {
      console.log(`   ✅ SUCCESS`);
      console.log(`   Message: ${response.body.message || 'Success'}`);
      return true;
    } else {
      console.log(`   ⚠️  OTHER RESPONSE (${response.statusCode})`);
      console.log(`   Message: ${response.body.error || response.body.message || 'Unknown'}`);
      return true;
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log(`   ❌ SERVER NOT RUNNING`);
      return null;
    } else {
      console.log(`   ❌ ERROR: ${error.message}`);
      return false;
    }
  }
}

/**
 * Main test function
 */
async function testCancelEndpoints() {
  console.log('🚀 Testing Cancel Order Endpoints');
  console.log('=================================');
  
  const tests = [
    {
      name: 'Health Check',
      method: 'GET',
      path: '/api/health'
    },
    {
      name: 'Consumer Cancel Order (PUT)',
      method: 'PUT',
      path: `/api/orders/${TEST_ORDER_ID}/cancel`,
      headers: { 'Authorization': CONSUMER_TOKEN },
      data: { reason: 'Test cancellation' }
    },
    {
      name: 'Admin Cancel Order (PUT)',
      method: 'PUT', 
      path: `/api/admin/orders/${TEST_ORDER_ID}/cancel`,
      headers: { 'Authorization': ADMIN_TOKEN },
      data: { reason: 'Admin test cancellation' }
    },
    {
      name: 'Legacy DELETE Endpoint',
      method: 'DELETE',
      path: `/api/orders/${TEST_ORDER_ID}`,
      headers: { 'Authorization': CONSUMER_TOKEN }
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
    console.log('❌ Development server is not running on port 3002');
    console.log('\nTo start the server:');
    console.log('cd frontend && npm run start:full');
  } else {
    console.log(`✅ Endpoints found: ${endpointsFound}`);
    console.log(`❌ Endpoints missing: ${endpointsMissing}`);
    
    if (endpointsMissing === 0) {
      console.log('\n🎉 SUCCESS: All cancel order endpoints are accessible!');
      console.log('The frontend should now be able to cancel orders without "endpoint not found" errors.');
    } else {
      console.log('\n⚠️  Some endpoints are still missing.');
      console.log('Please check if the development server restarted properly.');
    }
  }

  console.log('\n📝 Next Steps:');
  console.log('1. Test cancellation in the actual frontend UI');
  console.log('2. Check that orders are properly marked as cancelled');
  console.log('3. Verify audit trail is being logged');
  console.log('4. Test both consumer and admin cancellation flows');
}

// Run tests
testCancelEndpoints().catch(console.error);