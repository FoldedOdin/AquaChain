/**
 * Browser Console Fix Script
 * 
 * Copy and paste this entire script into your browser console
 * when you see "API error: Unknown API error" messages.
 */

console.log('🔧 AquaChain API Fix Script Starting...\n');

// Step 1: Check current authentication status
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
console.log('🔑 Authentication Status:');
console.log('   Token present:', !!token);
if (token) {
  console.log('   Token type:', token.startsWith('dev-token-') ? 'Development' : 'Production');
  console.log('   Token preview:', token.substring(0, 20) + '...');
}

// Step 2: Check API endpoint
const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'Unknown';
console.log('🌐 API Endpoint:', apiEndpoint);
console.log('   Is production API:', apiEndpoint.includes('amazonaws.com'));

// Step 3: Diagnose the issue
let issueDetected = false;
let recommendedAction = '';

if (!token) {
  console.log('❌ ISSUE: No authentication token found');
  recommendedAction = 'Please log in to the application';
  issueDetected = true;
} else if (token.startsWith('dev-token-') && apiEndpoint.includes('amazonaws.com')) {
  console.log('❌ ISSUE: Development token with production API');
  recommendedAction = 'Switch to mock data or use proper authentication';
  issueDetected = true;
} else {
  console.log('⚠️  Token appears valid, but API calls are failing');
  recommendedAction = 'Test API connectivity';
}

// Step 4: Test API connectivity
async function testAPI() {
  try {
    console.log('\n📡 Testing API connectivity...');
    const response = await fetch(`${apiEndpoint}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      console.log('✅ API health check passed');
      
      // Test authenticated endpoint
      const devicesResponse = await fetch(`${apiEndpoint}/api/devices`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      console.log('📊 Devices endpoint status:', devicesResponse.status);
      if (!devicesResponse.ok) {
        const errorText = await devicesResponse.text();
        console.log('❌ Devices endpoint error:', errorText);
      }
    } else {
      console.log('❌ API health check failed:', response.status);
    }
  } catch (error) {
    console.log('❌ API connectivity test failed:', error.message);
  }
}

// Step 5: Provide solutions
console.log('\n🔧 RECOMMENDED SOLUTIONS:\n');

if (!token) {
  console.log('1. Log in to the application properly');
  console.log('2. If login fails, check your credentials');
} else if (issueDetected) {
  console.log('1. QUICK FIX - Switch to mock data:');
  console.log('   localStorage.setItem("REACT_APP_USE_MOCK_DATA", "true");');
  console.log('   window.location.reload();');
  console.log('');
  console.log('2. PROPER FIX - Clear tokens and re-login:');
  console.log('   localStorage.removeItem("aquachain_token");');
  console.log('   localStorage.removeItem("authToken");');
  console.log('   window.location.reload();');
  console.log('   // Then log in with proper credentials');
} else {
  console.log('1. Test API connectivity (running automatically...)');
  testAPI();
  console.log('2. Check network connection');
  console.log('3. Verify API Gateway is running');
}

console.log('\n💡 IMMEDIATE ACTION:');
console.log('If you want to continue using the app with sample data:');
console.log('localStorage.setItem("REACT_APP_USE_MOCK_DATA", "true"); window.location.reload();');

console.log('\n📚 For more help, check AUTHENTICATION_FIX.md');

// Auto-run API test if we have a token
if (token && !token.startsWith('dev-token-')) {
  testAPI();
}