/**
 * Browser Console CORS Test
 * Test the alerts endpoint manually to verify CORS fix
 */

console.log('🧪 Testing CORS fix for alerts endpoint...');

const API_BASE = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

// Test 1: Simple OPTIONS request (preflight)
console.log('\n1️⃣ Testing OPTIONS request (preflight)...');
fetch(`${API_BASE}/api/alerts`, {
  method: 'OPTIONS',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  }
})
.then(response => {
  console.log(`OPTIONS Status: ${response.status} ${response.statusText}`);
  console.log('CORS Headers:');
  console.log('  Access-Control-Allow-Origin:', response.headers.get('Access-Control-Allow-Origin'));
  console.log('  Access-Control-Allow-Methods:', response.headers.get('Access-Control-Allow-Methods'));
  console.log('  Access-Control-Allow-Headers:', response.headers.get('Access-Control-Allow-Headers'));
  
  if (response.status === 200) {
    console.log('✅ OPTIONS request successful - CORS preflight should work');
  } else {
    console.log('❌ OPTIONS request failed - CORS preflight will fail');
  }
})
.catch(error => {
  console.log('❌ OPTIONS request error:', error.message);
});

// Test 2: Actual GET request
console.log('\n2️⃣ Testing GET request...');
setTimeout(() => {
  fetch(`${API_BASE}/api/alerts?limit=10`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  })
  .then(response => {
    console.log(`GET Status: ${response.status} ${response.statusText}`);
    
    if (response.status === 200) {
      console.log('✅ GET request successful - alerts endpoint working');
      return response.json();
    } else if (response.status === 401) {
      console.log('🔑 Authentication required - but CORS is working');
      return response.text();
    } else if (response.status === 404) {
      console.log('❌ Endpoint not found - check API Gateway configuration');
      return response.text();
    } else {
      console.log('⚠️ Unexpected status - check server logs');
      return response.text();
    }
  })
  .then(data => {
    console.log('Response data:', data);
  })
  .catch(error => {
    if (error.message.includes('CORS')) {
      console.log('❌ CORS error still present:', error.message);
    } else {
      console.log('❌ Request error:', error.message);
    }
  });
}, 2000);

// Test 3: Check other working endpoints for comparison
console.log('\n3️⃣ Testing working endpoint for comparison...');
setTimeout(() => {
  fetch(`${API_BASE}/api/devices`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  })
  .then(response => {
    console.log(`Devices endpoint status: ${response.status} ${response.statusText}`);
    if (response.status === 200 || response.status === 401) {
      console.log('✅ Devices endpoint CORS working correctly');
    }
  })
  .catch(error => {
    console.log('Devices endpoint error:', error.message);
  });
}, 4000);

console.log('\n🎯 Results will appear above in 2-6 seconds...');
console.log('💡 If OPTIONS returns 200, the CORS fix worked');
console.log('💡 If GET returns 401, authentication is needed but CORS is fixed');
console.log('💡 If GET returns 404, the endpoint needs to be created');