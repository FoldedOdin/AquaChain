// Final Authentication Fix - Addresses all token key issues
console.log('🔧 AquaChain Final Authentication Fix');

// Clear all existing tokens to start fresh
localStorage.removeItem('REACT_APP_USE_MOCK_DATA');
localStorage.removeItem('aquachain_token');
localStorage.removeItem('authToken');
localStorage.removeItem('token');

const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

window.loginToAquaChain = async function(email, password) {
  try {
    console.log('🔐 Attempting login...');
    
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    console.log('📡 Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Login failed:', response.status, errorText);
      
      if (response.status === 404) {
        console.error('❌ The /api/auth/signin endpoint does not exist');
        console.log('💡 This system may use Cognito authentication instead');
        console.log('💡 Try using the proper authentication method for this system');
      }
      return;
    }

    const data = await response.json();
    console.log('📦 Response data:', data);

    if (data.token) {
      // Store token with BOTH keys to ensure compatibility
      localStorage.setItem('aquachain_token', data.token);
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('token', data.token); // Add this key too
      
      if (data.user) {
        localStorage.setItem('aquachain_user', JSON.stringify(data.user));
      }
      
      console.log('✅ Login successful! Token stored with multiple keys for compatibility');
      console.log('🔄 Reloading page...');
      window.location.reload();
    } else {
      console.error('❌ Login response missing token:', data);
    }
  } catch (error) {
    console.error('❌ Login error:', error);
  }
};

// Test if the auth endpoint exists
window.testAuthEndpoint = async function() {
  try {
    console.log('🧪 Testing auth endpoint...');
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'OPTIONS'
    });
    console.log('📡 OPTIONS response:', response.status);
    
    if (response.status === 404) {
      console.warn('⚠️ Auth endpoint does not exist');
      console.log('💡 Available endpoints might be:');
      console.log('   - Cognito authentication');
      console.log('   - Different auth path');
      console.log('   - Mock authentication for development');
    } else {
      console.log('✅ Auth endpoint exists');
    }
  } catch (error) {
    console.error('❌ Endpoint test failed:', error);
  }
};

// Check current authentication state
window.checkAuthState = function() {
  console.log('🔍 Current authentication state:');
  console.log('  aquachain_token:', localStorage.getItem('aquachain_token') ? 'Present' : 'Missing');
  console.log('  authToken:', localStorage.getItem('authToken') ? 'Present' : 'Missing');
  console.log('  token:', localStorage.getItem('token') ? 'Present' : 'Missing');
  console.log('  aquachain_user:', localStorage.getItem('aquachain_user') ? 'Present' : 'Missing');
};

// Enable mock data mode as fallback
window.enableMockMode = function() {
  console.log('🎭 Enabling mock data mode...');
  localStorage.setItem('REACT_APP_USE_MOCK_DATA', 'true');
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('authToken');
  localStorage.removeItem('token');
  console.log('✅ Mock mode enabled - page will use fake data');
  window.location.reload();
};

console.log('🎯 Available commands:');
console.log('  loginToAquaChain("email", "password") - Attempt login');
console.log('  testAuthEndpoint() - Test if auth endpoint exists');
console.log('  checkAuthState() - Check current tokens');
console.log('  enableMockMode() - Switch to mock data');
console.log('');
console.log('🚀 First, test the endpoint:');
console.log('  testAuthEndpoint()');