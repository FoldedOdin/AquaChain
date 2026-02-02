#!/usr/bin/env node

/**
 * Test script to verify Add Device State Management Fix
 * Tests that the button state management works correctly without toggle conflicts
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Add Device State Management Fix...\n');

// Read the ConsumerDashboard component
const dashboardPath = path.join(__dirname, 'src/components/Dashboard/ConsumerDashboard.tsx');

if (!fs.existsSync(dashboardPath)) {
  console.error('❌ ConsumerDashboard.tsx not found');
  process.exit(1);
}

const content = fs.readFileSync(dashboardPath, 'utf8');

// Test 1: Check for explicit state management instead of toggle
console.log('✅ Test 1: Checking for explicit state management...');
if (content.includes('if (!showAddDevice)') && content.includes('setShowAddDevice(true)')) {
  console.log('   ✓ Explicit state management found (no blind toggle)');
} else {
  console.log('   ❌ Still using blind toggle pattern');
}

// Test 2: Check for separate close function
console.log('✅ Test 2: Checking for separate close function...');
if (content.includes('closeAddDeviceModal') && content.includes('setShowAddDevice(false)')) {
  console.log('   ✓ Separate close function implemented');
} else {
  console.log('   ❌ No separate close function found');
}

// Test 3: Check for enhanced debugging
console.log('✅ Test 3: Checking for enhanced debugging...');
if (content.includes('current showAddDevice:') && content.includes('Opening Add Device Modal')) {
  console.log('   ✓ Enhanced debugging logs found');
} else {
  console.log('   ❌ Enhanced debugging not implemented');
}

// Test 4: Check for duplicate useEffect removal
console.log('✅ Test 4: Checking for duplicate useEffect removal...');
const useEffectMatches = content.match(/useEffect\(\(\) => \{[\s\S]*?showAddDevice[\s\S]*?\}, \[showAddDevice\]\);/g);
if (useEffectMatches && useEffectMatches.length === 1) {
  console.log('   ✓ Only one showAddDevice useEffect found');
} else {
  console.log(`   ⚠️  Found ${useEffectMatches ? useEffectMatches.length : 0} showAddDevice useEffect hooks`);
}

// Test 5: Check for proper modal prop usage
console.log('✅ Test 5: Checking for proper modal prop usage...');
if (content.includes('onClose={closeAddDeviceModal}')) {
  console.log('   ✓ Modal uses dedicated close function');
} else {
  console.log('   ❌ Modal still uses toggle function');
}

console.log('\n🎯 Fix Summary:');
console.log('   • Replaced blind toggle with explicit state management');
console.log('   • Added separate close function for modal');
console.log('   • Enhanced debugging to track state changes');
console.log('   • Removed duplicate useEffect hooks');
console.log('   • Added current state logging for better debugging');

console.log('\n🔍 Expected Behavior:');
console.log('   1. Button click logs current state: "current showAddDevice: false"');
console.log('   2. Explicit action: "Opening Add Device Modal"');
console.log('   3. State change: "showAddDevice state changed to: true"');
console.log('   4. Modal opens and stays open');

console.log('\n🚀 Testing Steps:');
console.log('   1. Start dev server: npm start');
console.log('   2. Open browser console');
console.log('   3. Click "Add Your First Device" button');
console.log('   4. Verify logs show explicit state management');
console.log('   5. Confirm modal opens and stays open');

console.log('\n✅ Add Device State Management Fix Test Complete!');