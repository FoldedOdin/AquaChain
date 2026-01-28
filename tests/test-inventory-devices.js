// Test script to verify inventory devices are accessible via API
const http = require('http');

// Admin token from .dev-data.json
const adminToken = 'dev-token-1765187293580-qedtc6q3is';

const options = {
  hostname: 'localhost',
  port: 3002,
  path: '/api/admin/devices',
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  }
};

const req = http.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    console.log('Status Code:', res.statusCode);
    console.log('\nResponse:');
    const response = JSON.parse(data);
    
    if (response.success) {
      console.log(`✅ Total devices: ${response.count}`);
      console.log('\n📦 Unassigned devices (INVENTORY):');
      
      const unassignedDevices = response.devices.filter(d => 
        d.consumerName === 'Unassigned' || !d.consumerName
      );
      
      if (unassignedDevices.length > 0) {
        unassignedDevices.forEach(d => {
          console.log(`   - ${d.device_id} (${d.location}) - Status: ${d.status}`);
        });
        console.log(`\n✅ Found ${unassignedDevices.length} unassigned devices ready for provisioning!`);
      } else {
        console.log('   ❌ No unassigned devices found');
      }
      
      console.log('\n👥 Assigned devices:');
      const assignedDevices = response.devices.filter(d => 
        d.consumerName && d.consumerName !== 'Unassigned'
      );
      assignedDevices.forEach(d => {
        console.log(`   - ${d.device_id} → ${d.consumerName}`);
      });
    } else {
      console.log('❌ Error:', response.error);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Request failed:', error.message);
});

req.end();
