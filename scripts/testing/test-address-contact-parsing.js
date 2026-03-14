#!/usr/bin/env node
/**
 * Test Address and Contact Info Parsing
 * 
 * This script tests the parsing logic for address and contact info
 * to ensure the frontend will display the information correctly.
 */

// Sample data from the database
const sampleOrder = {
  orderId: 'ord_1773176454115',
  deliveryAddress: '{"street": "73/1276", "city": "Ernakulam", "state": "Kerala", "pincode": "682012", "country": "India", "landmark": "Just before reaching the Church", "coordinates": {"latitude": 9.9312, "longitude": 76.2673}}',
  contactInfo: '{"name": "Karthik K Pradeep", "phone": "+918547613649", "email": "karthikkpradeep123@gmail.com"}',
  address: '', // Legacy field
  phone: ''    // Legacy field
};

// Helper functions (same as in frontend)
const parseDeliveryAddress = (deliveryAddress) => {
  if (!deliveryAddress) return null;
  try {
    return JSON.parse(deliveryAddress);
  } catch (e) {
    console.warn('Failed to parse delivery address:', e);
    return null;
  }
};

const parseContactInfo = (contactInfo) => {
  if (!contactInfo) return null;
  try {
    return JSON.parse(contactInfo);
  } catch (e) {
    console.warn('Failed to parse contact info:', e);
    return null;
  }
};

const getDisplayAddress = (order) => {
  // Try deliveryAddress first (JSON string)
  const deliveryAddr = parseDeliveryAddress(order.deliveryAddress);
  if (deliveryAddr) {
    const parts = [
      deliveryAddr.street,
      deliveryAddr.city,
      deliveryAddr.state,
      deliveryAddr.pincode
    ].filter(Boolean);
    return parts.join(', ');
  }
  
  // Fallback to address field
  if (typeof order.address === 'string' && order.address) {
    return order.address;
  }
  
  return 'Address not available';
};

const getDisplayPhone = (order) => {
  // Try contactInfo first (JSON string)
  const contactInfo = parseContactInfo(order.contactInfo);
  if (contactInfo && contactInfo.phone) {
    return contactInfo.phone;
  }
  
  // Fallback to phone field
  if (order.phone) {
    return order.phone;
  }
  
  return 'Phone not available';
};

const getContactName = (order) => {
  const contactInfo = parseContactInfo(order.contactInfo);
  if (contactInfo && contactInfo.name) {
    return contactInfo.name;
  }
  return 'Customer';
};

// Test the parsing functions
console.log('🧪 Testing Address and Contact Info Parsing');
console.log('=' .repeat(50));

console.log('\n📋 Sample Order Data:');
console.log('Order ID:', sampleOrder.orderId);
console.log('Delivery Address (JSON):', sampleOrder.deliveryAddress);
console.log('Contact Info (JSON):', sampleOrder.contactInfo);

console.log('\n🔍 Parsing Results:');

// Test address parsing
const parsedAddress = parseDeliveryAddress(sampleOrder.deliveryAddress);
console.log('Parsed Address Object:', parsedAddress);
console.log('Display Address:', getDisplayAddress(sampleOrder));

// Test contact info parsing
const parsedContact = parseContactInfo(sampleOrder.contactInfo);
console.log('Parsed Contact Object:', parsedContact);
console.log('Display Phone:', getDisplayPhone(sampleOrder));
console.log('Contact Name:', getContactName(sampleOrder));

console.log('\n🎯 Frontend Display Preview:');
console.log('=' .repeat(50));
console.log('Installation Details:');
console.log('  Address:', getDisplayAddress(sampleOrder));
console.log('  Contact Phone:', getDisplayPhone(sampleOrder));
console.log('  Contact Name:', getContactName(sampleOrder));

// Test with missing data
console.log('\n🧪 Testing with Missing Data:');
const emptyOrder = {
  orderId: 'test-empty',
  deliveryAddress: null,
  contactInfo: null,
  address: '',
  phone: ''
};

console.log('Empty Order Display:');
console.log('  Address:', getDisplayAddress(emptyOrder));
console.log('  Contact Phone:', getDisplayPhone(emptyOrder));
console.log('  Contact Name:', getContactName(emptyOrder));

// Test with malformed JSON
console.log('\n🧪 Testing with Malformed JSON:');
const malformedOrder = {
  orderId: 'test-malformed',
  deliveryAddress: '{"street": "123 Main St", "city": "Test City"', // Missing closing brace
  contactInfo: '{"name": "Test User", "phone": "+1234567890"}',
  address: 'Fallback Address',
  phone: '+0987654321'
};

console.log('Malformed JSON Order Display:');
console.log('  Address:', getDisplayAddress(malformedOrder));
console.log('  Contact Phone:', getDisplayPhone(malformedOrder));
console.log('  Contact Name:', getContactName(malformedOrder));

console.log('\n✅ Testing Complete!');
console.log('The frontend should now display address and contact information correctly.');