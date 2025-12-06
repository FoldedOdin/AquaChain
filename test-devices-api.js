// Quick test script to verify /api/devices endpoint
const fetch = require('node-fetch');

async function testDevicesAPI() {
  try {
    // You need to replace this with an actual token from localStorage
    // Open browser console and run: localStorage.getItem('aquachain_token')
    const token = 'YOUR_TOKEN_HERE';
    
    console.log('Testing /api/devices endpoint...');
    console.log('Token:', token ? 'Present' : 'Missing');
    
    const response = await fetch('http://localhost:3002/api/devices', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('Status:', response.status);
    
    const data = await response.json();
    console.log('Response:', JSON.stringify(data, null, 2));
    
    if (data.success && data.data) {
      console.log('\n✅ SUCCESS! Response has correct format');
      console.log(`Found ${data.data.length} devices`);
      data.data.forEach((device, i) => {
        console.log(`  ${i + 1}. ${device.name || device.device_id} (${device.status})`);
      });
    } else if (data.success && data.devices) {
      console.log('\n❌ ERROR! Response uses old format (devices instead of data)');
    } else {
      console.log('\n❌ ERROR!', data.error || 'Unknown error');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testDevicesAPI();
