/**
 * AWS Authentication Helper
 * 
 * This script helps you authenticate with the AWS Cognito API
 * Run this in the browser console after the frontend loads
 */

console.log('🔐 AWS Authentication Helper');
console.log('============================\n');

const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

// Function to test API connectivity
async function testAPIConnectivity() {
  console.log('🌐 Testing API connectivity...');
  
  try {
    const response = await fetch(`${API_ENDPOINT}/health`);
    console.log(`📡 API Status: ${response.status}`);
    
    if (response.status === 403) {
      console.log('✅ API is accessible but requires authentication');
      return true;
    } else if (response.status === 200) {
      const data = await response.json();
      console.log('✅ API is accessible:', data);
      return true;
    } else {
      console.log('⚠️ Unexpected response:', response.status);
      return false;
    }
  } catch (error) {
    console.error('❌ API connectivity test failed:', error);
    return false;
  }
}

// Function to authenticate with email/password
async function authenticateUser(email, password) {
  console.log(`🔑 Attempting to authenticate: ${email}`);
  
  try {
    // Try the main auth endpoint
    let response = await fetch(`${API_ENDPOINT}/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password
      }),
    });

    // If not found, try alternative endpoint
    if (response.status === 404) {
      console.log('🔄 Trying alternative auth endpoint...');
      response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        }),
      });
    }

    const data = await response.json();
    
    if (response.ok && data.token) {
      console.log('✅ Authentication successful!');
      localStorage.setItem('aquachain_token', data.token);
      console.log('💾 Token stored in localStorage');
      console.log('🔄 Please refresh the page to use the new token');
      return data;
    } else {
      console.error('❌ Authentication failed:', data);
      return null;
    }
  } catch (error) {
    console.error('❌ Authentication error:', error);
    return null;
  }
}

// Function to test authenticated API call
async function testAuthenticatedCall() {
  const token = localStorage.getItem('aquachain_token');
  
  if (!token) {
    console.log('❌ No token found. Please authenticate first.');
    return;
  }
  
  console.log('🧪 Testing authenticated API call...');
  
  try {
    const response = await fetch(`${API_ENDPOINT}/devices`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ Authenticated API call successful:', data);
    } else {
      console.error('❌ Authenticated API call failed:', data);
    }
  } catch (error) {
    console.error('❌ API call error:', error);
  }
}

// Helper function to clear tokens and start fresh
function clearTokens() {
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('authToken');
  console.log('🧹 Tokens cleared. Refresh the page to start fresh.');
}

// Export functions to global scope for easy use
window.testAPIConnectivity = testAPIConnectivity;
window.authenticateUser = authenticateUser;
window.testAuthenticatedCall = testAuthenticatedCall;
window.clearTokens = clearTokens;

console.log('📚 Available functions:');
console.log('  • testAPIConnectivity() - Test if API is reachable');
console.log('  • authenticateUser(email, password) - Login with credentials');
console.log('  • testAuthenticatedCall() - Test API with stored token');
console.log('  • clearTokens() - Clear stored tokens');
console.log('\n💡 Example usage:');
console.log('  await authenticateUser("your-email@example.com", "your-password")');

// Auto-test connectivity
testAPIConnectivity();