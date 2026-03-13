/**
 * Test Backend Authentication
 * 
 * Run this in browser console to test the backend authentication API
 */

console.log('🔧 Testing Backend Authentication API...\n');

const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

async function testAuthAPI() {
  try {
    console.log('📡 Testing /api/auth/signin endpoint...');
    
    // Test with dummy credentials first to see the response structure
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpassword'
      }),
    });

    console.log('📊 Response status:', response.status);
    console.log('📊 Response headers:', Object.fromEntries(response.headers.entries()));

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('📦 Response data:', data);
      
      if (data.token) {
        console.log('✅ Token found in response');
        console.log('🔑 Token preview:', data.token.substring(0, 50) + '...');
      } else {
        console.log('❌ No token in response');
      }
    } else {
      const text = await response.text();
      console.log('📦 Response text:', text);
    }

  } catch (error) {
    console.error('❌ API test failed:', error);
  }
}

async function testHealthAPI() {
  try {
    console.log('📡 Testing /api/health endpoint...');
    
    const response = await fetch(`${API_ENDPOINT}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('📊 Health response status:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Health check passed:', data);
    } else {
      const text = await response.text();
      console.error('❌ Health check failed:', text);
    }
  } catch (error) {
    console.error('❌ Health check network error:', error);
  }
}

// Check if auth endpoint exists
async function checkAuthEndpoint() {
  try {
    console.log('📡 Checking if /api/auth/signin endpoint exists...');
    
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'OPTIONS', // CORS preflight
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('📊 OPTIONS response status:', response.status);
    
    if (response.status === 404) {
      console.log('❌ Auth endpoint does not exist');
      console.log('💡 The backend may not have authentication endpoints deployed');
    } else {
      console.log('✅ Auth endpoint exists');
    }
  } catch (error) {
    console.error('❌ Endpoint check failed:', error);
  }
}

console.log('🔧 Running authentication tests...\n');
testHealthAPI();
checkAuthEndpoint();
testAuthAPI();

console.log('\n📚 If you see 404 errors, the backend authentication service may not be deployed.');
console.log('📚 Check if the Lambda functions for authentication are properly deployed.');