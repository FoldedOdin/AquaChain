/**
 * Test Real Authentication
 * 
 * Run this in browser console to test real authentication
 * You'll need valid credentials for this to work
 */

console.log('🔧 Testing Real Authentication...\n');

const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

async function testRealAuth() {
  // First, let's remove mock data flag and clear old tokens
  localStorage.removeItem('REACT_APP_USE_MOCK_DATA');
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('authToken');
  
  console.log('🧹 Cleared mock data flag and old tokens');
  
  // Test the auth endpoint structure
  console.log('📡 Testing auth endpoint...');
  
  try {
    // Test with a dummy request to see the response structure
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpassword123'
      }),
    });

    console.log('📊 Response status:', response.status);
    
    if (response.status === 404) {
      console.log('❌ Auth endpoint not found at /api/auth/signin');
      console.log('💡 Trying alternative endpoint /auth/signin...');
      
      // Try alternative endpoint
      const altResponse = await fetch(`${API_ENDPOINT}/auth/signin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'testpassword123'
        }),
      });
      
      console.log('📊 Alternative endpoint status:', altResponse.status);
      
      if (altResponse.status !== 404) {
        console.log('✅ Found auth endpoint at /auth/signin');
        const data = await altResponse.json();
        console.log('📦 Response structure:', data);
      }
    } else {
      console.log('✅ Auth endpoint found at /api/auth/signin');
      const data = await response.json();
      console.log('📦 Response structure:', data);
      
      if (data.error && data.error.includes('Invalid email or password')) {
        console.log('✅ Endpoint is working (expected error for dummy credentials)');
      }
    }
    
  } catch (error) {
    console.error('❌ Auth endpoint test failed:', error);
  }
}

async function promptForCredentials() {
  console.log('\n🔐 To test with real credentials:');
  console.log('1. Make sure you have a valid AquaChain account');
  console.log('2. Run this function with your credentials:');
  console.log('');
  console.log('async function loginWithCredentials(email, password) {');
  console.log('  const response = await fetch("https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin", {');
  console.log('    method: "POST",');
  console.log('    headers: { "Content-Type": "application/json" },');
  console.log('    body: JSON.stringify({ email, password })');
  console.log('  });');
  console.log('  const data = await response.json();');
  console.log('  console.log("Login result:", data);');
  console.log('  if (data.token) {');
  console.log('    localStorage.setItem("aquachain_token", data.token);');
  console.log('    console.log("✅ Token stored! Refresh the page.");');
  console.log('  }');
  console.log('}');
  console.log('');
  console.log('// Then call: loginWithCredentials("your-email@example.com", "your-password")');
}

// Run the test
testRealAuth();
promptForCredentials();

console.log('\n📚 If the auth endpoint is not found, the Lambda function may not be deployed correctly.');
console.log('📚 Check the API Gateway configuration and Lambda function deployment.');