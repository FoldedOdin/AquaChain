/**
 * Test the correct alerts endpoint
 * The endpoint is /alerts (not /api/alerts)
 */

console.log('🧪 Testing correct alerts endpoint...');

const API_BASE = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

console.log('🔑 Token status:', token ? 'Present' : 'Missing');

// Test the correct endpoint: /alerts
const correctEndpoint = `${API_BASE}/alerts?limit=10`;
console.log('🎯 Testing:', correctEndpoint);

fetch(correctEndpoint, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  }
})
.then(response => {
  console.log(`✅ Response status: ${response.status} ${response.statusText}`);
  
  if (response.status === 200) {
    console.log('🎉 SUCCESS! Alerts endpoint is working');
    return response.json();
  } else if (response.status === 401) {
    console.log('🔑 Authentication required - but endpoint is reachable');
    return response.text();
  } else if (response.status === 404) {
    console.log('❌ Endpoint not found');
    return response.text();
  } else {
    console.log('⚠️ Unexpected status');
    return response.text();
  }
})
.then(data => {
  console.log('📦 Response data:', data);
})
.catch(error => {
  if (error.message.includes('CORS')) {
    console.log('❌ CORS error still present:', error.message);
  } else {
    console.log('❌ Request error:', error.message);
  }
});

// Also test the wrong endpoint for comparison
setTimeout(() => {
  console.log('\n🔍 Testing wrong endpoint for comparison...');
  const wrongEndpoint = `${API_BASE}/api/alerts?limit=10`;
  console.log('❌ Testing:', wrongEndpoint);
  
  fetch(wrongEndpoint, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  })
  .then(response => {
    console.log(`Wrong endpoint status: ${response.status} ${response.statusText}`);
  })
  .catch(error => {
    console.log('Wrong endpoint error (expected):', error.message);
  });
}, 2000);

console.log('\n🎯 Expected results:');
console.log('✅ /alerts should return 200 (success) or 401 (auth needed)');
console.log('❌ /api/alerts should fail with CORS or 404 error');