// Immediate Error Spam Fix - Stops the polling and provides clear debugging
console.log('🛑 Stopping Error Spam Immediately');

// 1. Clear all intervals to stop the polling
let intervalId = 1;
while (intervalId < 10000) {
  clearInterval(intervalId);
  intervalId++;
}
console.log('✅ Cleared all intervals to stop polling');

// 2. Clear all timeouts
let timeoutId = 1;
while (timeoutId < 10000) {
  clearTimeout(timeoutId);
  timeoutId++;
}
console.log('✅ Cleared all timeouts');

// 3. Check current authentication state
console.log('🔍 Current Authentication State:');
const tokens = {
  'aquachain_token': localStorage.getItem('aquachain_token'),
  'authToken': localStorage.getItem('authToken'),
  'token': localStorage.getItem('token')
};

Object.entries(tokens).forEach(([key, value]) => {
  if (value) {
    console.log(`  ${key}: ${value.substring(0, 20)}...`);
  } else {
    console.log(`  ${key}: Missing`);
  }
});

// 4. Test the actual API endpoint that's failing
const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

window.testFailingEndpoint = async function() {
  console.log('🧪 Testing the failing alerts endpoint...');
  
  const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken') || localStorage.getItem('token');
  
  try {
    const response = await fetch(`${API_ENDPOINT}/alerts?limit=50`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    
    console.log('📡 Response status:', response.status);
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      
      if (response.status === 401) {
        console.log('💡 This is an authentication error');
        console.log('💡 The token is either missing, invalid, or expired');
      } else if (response.status === 404) {
        console.log('💡 The /alerts endpoint does not exist');
        console.log('💡 Available endpoints might be different');
      } else if (response.status === 403) {
        console.log('💡 Access forbidden - insufficient permissions');
      }
    } else {
      const data = await response.json();
      console.log('✅ Success! Response data:', data);
    }
  } catch (error) {
    console.error('❌ Network error:', error);
  }
};

// 5. Enable mock mode to stop all API calls
window.enableMockMode = function() {
  console.log('🎭 Enabling mock data mode to stop all API calls...');
  localStorage.setItem('REACT_APP_USE_MOCK_DATA', 'true');
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('authToken');
  localStorage.removeItem('token');
  console.log('✅ Mock mode enabled - reloading page...');
  window.location.reload();
};

// 6. Check if mock mode is available
const mockDataFlag = localStorage.getItem('REACT_APP_USE_MOCK_DATA');
console.log('🎭 Mock data mode:', mockDataFlag || 'Disabled');

console.log('');
console.log('🎯 Next steps:');
console.log('1. testFailingEndpoint() - See what the real error is');
console.log('2. enableMockMode() - Switch to fake data to stop errors');
console.log('');
console.log('🚨 Error spam should now be stopped!');

// 7. Override console.error temporarily to reduce noise
const originalConsoleError = console.error;
let errorCount = 0;
console.error = function(...args) {
  errorCount++;
  if (errorCount <= 5) {
    originalConsoleError.apply(console, args);
  } else if (errorCount === 6) {
    originalConsoleError('🔇 Suppressing further console errors to reduce noise...');
  }
};

// Restore console.error after 30 seconds
setTimeout(() => {
  console.error = originalConsoleError;
  console.log('🔊 Console error logging restored');
}, 30000);