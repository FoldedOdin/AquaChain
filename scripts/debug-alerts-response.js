/**
 * Debug Alerts API Response
 * Check what the alerts endpoint is actually returning
 */

console.log('🔍 Debugging alerts API response...');

const API_BASE = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

console.log('🔑 Token status:', token ? 'Present' : 'Missing');

// Test the alerts endpoint
fetch(`${API_BASE}/alerts?limit=10`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  }
})
.then(response => {
  console.log(`📡 Response status: ${response.status} ${response.statusText}`);
  return response.text();
})
.then(text => {
  console.log('📥 Raw response text:', text);
  
  // Try to parse as JSON
  try {
    const data = JSON.parse(text);
    console.log('📦 Parsed JSON:', data);
    console.log('📊 Data type:', typeof data);
    console.log('📊 Is array:', Array.isArray(data));
    
    if (data && typeof data === 'object') {
      console.log('🔍 Object keys:', Object.keys(data));
      
      // Check if it has a data property
      if ('data' in data) {
        console.log('📦 data property:', data.data);
        console.log('📊 data.data type:', typeof data.data);
        console.log('📊 data.data is array:', Array.isArray(data.data));
      }
      
      // Check if it has an alerts property
      if ('alerts' in data) {
        console.log('📦 alerts property:', data.alerts);
        console.log('📊 data.alerts type:', typeof data.alerts);
        console.log('📊 data.alerts is array:', Array.isArray(data.alerts));
      }
    }
  } catch (parseError) {
    console.error('❌ JSON parse error:', parseError);
    console.log('📝 Response is not valid JSON');
  }
})
.catch(error => {
  console.error('❌ Request error:', error);
});

console.log('\n🎯 This will help identify:');
console.log('1. What format the alerts API returns');
console.log('2. Whether it returns an array or object');
console.log('3. If there are nested properties like data.alerts');
console.log('4. Any authentication issues');