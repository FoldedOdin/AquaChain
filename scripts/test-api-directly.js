/**
 * Direct API Test Script
 * Run this in the browser console to test API connectivity
 */

console.log('🔧 Testing API connectivity...');

const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

console.log('🔑 Token status:', token ? 'Present' : 'Missing');
if (token) {
  console.log('🔑 Token type:', token.startsWith('dev-token-') ? 'Development' : 'Production');
  console.log('🔑 Token preview:', token.substring(0, 20) + '...');
}

// Test the devices endpoint
async function testDevicesAPI() {
  try {
    console.log('📡 Testing /api/devices endpoint...');
    
    const response = await fetch(`${API_BASE_URL}/api/devices`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });

    console.log('📊 Response status:', response.status);
    console.log('📊 Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      console.error('❌ Request failed');
      
      // Try to get response body
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        console.error('❌ Error data:', errorData);
      } else {
        const errorText = await response.text();
        console.error('❌ Error text:', errorText);
      }
    } else {
      const data = await response.json();
      console.log('✅ Success! Response data:', data);
    }
  } catch (error) {
    console.error('❌ Network error:', error);
  }
}

// Test the health endpoint
async function testHealthAPI() {
  try {
    console.log('📡 Testing /api/health endpoint...');
    
    const response = await fetch(`${API_BASE_URL}/api/health`, {
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
      console.error('❌ Health check failed');
    }
  } catch (error) {
    console.error('❌ Health check network error:', error);
  }
}

// Run tests
testHealthAPI();
testDevicesAPI();

console.log('🔧 Test completed. Check the results above.');