#!/usr/bin/env node
/**
 * Test Frontend API Connection
 * This script simulates the frontend API calls to verify the connection works
 */

const https = require('https');
const http = require('http');

// Configuration
const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const DEVICE_ID = 'ESP32-001';

// Test credentials
const TEST_EMAIL = 'admin@aquachain.com';
const TEST_PASSWORD = 'AdminPassword123!';

console.log('🧪 Frontend API Connection Test');
console.log('=' .repeat(60));

/**
 * Make HTTP request
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'AquaChain-Frontend-Test/1.0',
        ...options.headers
      }
    };
    
    const req = client.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: jsonData
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: data
          });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (options.body) {
      req.write(JSON.stringify(options.body));
    }
    
    req.end();
  });
}

/**
 * Test CORS preflight
 */
async function testCORS() {
  console.log('\n🔍 Testing CORS Preflight');
  console.log('-'.repeat(50));
  
  try {
    const endpoint = `${API_BASE_URL}/api/device-readings/${DEVICE_ID}/latest`;
    
    const response = await makeRequest(endpoint, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
      }
    });
    
    console.log(`📊 CORS Status: ${response.status}`);
    console.log(`📋 CORS Headers:`, response.headers);
    
    if (response.status === 204 || response.status === 200) {
      console.log('✅ CORS preflight successful');
      return true;
    } else {
      console.log('❌ CORS preflight failed');
      return false;
    }
  } catch (error) {
    console.log(`❌ CORS test error: ${error.message}`);
    return false;
  }
}

/**
 * Test API without authentication
 */
async function testAPIWithoutAuth() {
  console.log('\n🔍 Testing API without Authentication');
  console.log('-'.repeat(50));
  
  try {
    const endpoint = `${API_BASE_URL}/api/device-readings/${DEVICE_ID}/latest`;
    
    const response = await makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Origin': 'http://localhost:3000'
      }
    });
    
    console.log(`📊 Status: ${response.status}`);
    console.log(`📋 Response:`, response.data);
    
    if (response.status === 401) {
      console.log('✅ Correctly requires authentication');
      return true;
    } else {
      console.log('❌ Unexpected response');
      return false;
    }
  } catch (error) {
    console.log(`❌ API test error: ${error.message}`);
    return false;
  }
}

/**
 * Get Cognito token (simulating frontend auth)
 */
async function getCognitoToken() {
  console.log('\n🔐 Getting Cognito Token');
  console.log('-'.repeat(50));
  
  // This would normally be done through AWS Cognito SDK
  // For now, we'll simulate having a token
  console.log('📋 In a real frontend, this would use AWS Cognito SDK');
  console.log('📋 For testing, we need to implement proper token retrieval');
  
  return null; // Placeholder
}

/**
 * Test API with authentication
 */
async function testAPIWithAuth(token) {
  console.log('\n🔍 Testing API with Authentication');
  console.log('-'.repeat(50));
  
  if (!token) {
    console.log('❌ No token available for testing');
    return false;
  }
  
  try {
    const endpoint = `${API_BASE_URL}/api/device-readings/${DEVICE_ID}/latest`;
    
    const response = await makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Origin': 'http://localhost:3000',
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log(`📊 Status: ${response.status}`);
    console.log(`📋 Response:`, response.data);
    
    if (response.status === 200 && response.data.success) {
      console.log('✅ API call successful with authentication');
      console.log(`📊 Device Data:`, response.data.reading);
      return true;
    } else {
      console.log('❌ API call failed');
      return false;
    }
  } catch (error) {
    console.log(`❌ Authenticated API test error: ${error.message}`);
    return false;
  }
}

/**
 * Test frontend configuration
 */
function testFrontendConfig() {
  console.log('\n🔍 Testing Frontend Configuration');
  console.log('-'.repeat(50));
  
  console.log(`📋 API Base URL: ${API_BASE_URL}`);
  console.log(`📋 Device ID: ${DEVICE_ID}`);
  console.log(`📋 Expected Endpoint: ${API_BASE_URL}/api/device-readings/${DEVICE_ID}/latest`);
  
  // Check if URL is valid
  try {
    new URL(API_BASE_URL);
    console.log('✅ API Base URL is valid');
    return true;
  } catch (error) {
    console.log('❌ API Base URL is invalid');
    return false;
  }
}

/**
 * Main test function
 */
async function main() {
  const results = {
    config: false,
    cors: false,
    noAuth: false,
    withAuth: false
  };
  
  // Test configuration
  results.config = testFrontendConfig();
  
  // Test CORS
  results.cors = await testCORS();
  
  // Test API without auth
  results.noAuth = await testAPIWithoutAuth();
  
  // Get token and test with auth
  const token = await getCognitoToken();
  results.withAuth = await testAPIWithAuth(token);
  
  // Summary
  console.log('\n📋 SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Configuration: ${results.config ? 'Pass' : 'Fail'}`);
  console.log(`✅ CORS: ${results.cors ? 'Pass' : 'Fail'}`);
  console.log(`✅ No Auth (401): ${results.noAuth ? 'Pass' : 'Fail'}`);
  console.log(`✅ With Auth: ${results.withAuth ? 'Pass' : 'Fail (no token)'}`);
  
  if (results.config && results.cors && results.noAuth) {
    console.log('\n🎉 Frontend API connection is ready!');
    console.log('💡 Next steps:');
    console.log('   1. Implement proper Cognito authentication in frontend');
    console.log('   2. Update frontend environment variables');
    console.log('   3. Test with real user login');
  } else {
    console.log('\n🔧 Issues found that need fixing:');
    if (!results.config) console.log('   - Fix API configuration');
    if (!results.cors) console.log('   - Fix CORS configuration');
    if (!results.noAuth) console.log('   - Fix API authentication setup');
  }
}

// Run the test
main().catch(console.error);