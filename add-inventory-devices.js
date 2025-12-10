// Script to add unassigned devices to inventory
const fs = require('fs');

// Read current data
const data = JSON.parse(fs.readFileSync('.dev-data.json', 'utf8'));

// Initialize INVENTORY if it doesn't exist
if (!data.devices) {
  data.devices = {};
}

if (!data.devices.INVENTORY) {
  data.devices.INVENTORY = [];
}

// Add 5 unassigned devices to inventory
const devicesToAdd = [
  {
    device_id: 'AC-INV-001',
    user_id: 'INVENTORY',
    name: 'AC-INV-001',
    location: 'Warehouse',
    consumerName: 'Unassigned',
    status: 'online',
    created_at: new Date().toISOString(),
    created_by: 'system'
  },
  {
    device_id: 'AC-INV-002',
    user_id: 'INVENTORY',
    name: 'AC-INV-002',
    location: 'Warehouse',
    consumerName: 'Unassigned',
    status: 'online',
    created_at: new Date().toISOString(),
    created_by: 'system'
  },
  {
    device_id: 'AC-INV-003',
    user_id: 'INVENTORY',
    name: 'AC-INV-003',
    location: 'Warehouse',
    consumerName: 'Unassigned',
    status: 'online',
    created_at: new Date().toISOString(),
    created_by: 'system'
  },
  {
    device_id: 'AC-INV-004',
    user_id: 'INVENTORY',
    name: 'AC-INV-004',
    location: 'Warehouse',
    consumerName: 'Unassigned',
    status: 'online',
    created_at: new Date().toISOString(),
    created_by: 'system'
  },
  {
    device_id: 'AC-INV-005',
    user_id: 'INVENTORY',
    name: 'AC-INV-005',
    location: 'Warehouse',
    consumerName: 'Unassigned',
    status: 'online',
    created_at: new Date().toISOString(),
    created_by: 'system'
  }
];

// Add devices to INVENTORY
data.devices.INVENTORY.push(...devicesToAdd);

// Update lastUpdated
data.lastUpdated = new Date().toISOString();

// Write back to file
fs.writeFileSync('.dev-data.json', JSON.stringify(data, null, 2));

console.log('✅ Added 5 unassigned devices to inventory:');
devicesToAdd.forEach(d => console.log(`   - ${d.device_id}`));
console.log('\n📦 Total devices in INVENTORY:', data.devices.INVENTORY.length);
