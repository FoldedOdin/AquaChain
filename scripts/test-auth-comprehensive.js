/**
 * Comprehensive Authentication Test
 * Tests all aspects of the authentication system
 */

console.log('🧪 Starting comprehensive authentication test...');

const API_BASE = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

// Test 1: Environment Variables
console.log('\n1️⃣ Environment Variables Test');
console.log('REACT_APP_API_ENDPOINT:', process.env.REACT_APP_API_ENDPOINT);
console.log('Expected:', API_BASE);
console.log('Match:', process.env.REACT_APP_API_ENDPOINT === API_BASE ? '✅' : '❌');

// Test 2: Token Storage
console.log('\n2️⃣ Token Storage Test');
const tokens = {
  aquachain_token: localStorage.getItem('aquachain_token'),
  authToken: localStorage.getItem('authToken')
};

Object.entries(tokens).forEach(([key, value]) => {
  if (value) {
    console.log(`${key}: Present (${value.length} chars) - ${value.substring(0, 20)}...`);
    // Check if it looks like a JWT
    const isJWT = value.split('.').length === 3;
    console.log(`  JWT format: ${isJWT ? '✅' : '❌'}`);
  } else {
    console.log(`${key}: ❌ Missing`);
  }
});

// Test 3: API Endpoints
console.log('\n3️⃣ API Endpoints Test');
const endpoints = [
  '/api/devices',
  '/api/alerts',
  '/api/water-quality',
  '/api/dashboard/stats'
];

const token = tokens.aquachain_token || tokens.authToken;

async function testEndpoint(endpoint) {
  try {
    const url = API_BASE + endpoint;
    console.log(`Testing: ${url}`);
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    
    const status = response.status;
    const statusText = response.statusText;
    
    console.log(`  Status: ${status} ${statusText}`);
    
    if (status === 200) {
      console.log('  Result: ✅ Success');
    } else if (status === 401) {
      console.log('  Result: 🔑 Authentication required');
    } else if (status === 403) {
      console.log('  Result: 🚫 Forbidden');
    } else if (status === 404) {
      console.log('  Result: ❌ Not found');
    } else if (status >= 500) {
      console.log('  Result: 🔥 Server error');
    }
    
    const text = await response.text();
    if (text && text.length < 200) {
      console.log(`  Body: ${text}`);
    }
    
  } catch (error) {
    console.log(`  Result: ❌ Network error - ${error.message}`);
  }
}

// Run endpoint tests
(async () => {
  for (const endpoint of endpoints) {
    await testEndpoint(endpoint);
    await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
  }
  
  console.log('\n🎯 Summary:');
  console.log('- If you see 401 errors: Authentication token is missing or invalid');
  console.log('- If you see 404 errors: API Gateway routes are not configured correctly');
  console.log('- If you see network errors: API Gateway is not reachable');
  console.log('- If you see 200 responses: Everything is working correctly!');
})();