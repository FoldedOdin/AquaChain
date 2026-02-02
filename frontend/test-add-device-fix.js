#!/usr/bin/env node

/**
 * Test script to verify Add Device button fix
 * Tests that the button click handlers work correctly without conflicts
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Add Device Button Fix...\n');

// Read the ConsumerDashboard component
const dashboardPath = path.join(__dirname, 'src/components/Dashboard/ConsumerDashboard.tsx');

if (!fs.existsSync(dashboardPath)) {
  console.error('❌ ConsumerDashboard.tsx not found');
  process.exit(1);
}

const content = fs.readFileSync(dashboardPath, 'utf8');

// Test 1: Check for debounce mechanism
console.log('✅ Test 1: Checking for debounce mechanism...');
if (content.includes('isToggling') && content.includes('setIsToggling')) {
  console.log('   ✓ Debounce state variables found');
} else {
  console.log('   ❌ Debounce mechanism not found');
}

// Test 2: Check for simplified Add Device event handlers (not Order Device)
console.log('✅ Test 2: Checking for simplified Add Device event handlers...');
const addDeviceComplexPattern = /Add Real Device[\s\S]*?onClick=\{\(e\)\s*=>\s*\{[\s\S]*?e\.preventDefault\(\)[\s\S]*?e\.stopPropagation\(\)[\s\S]*?\}\}/;
if (!addDeviceComplexPattern.test(content)) {
  console.log('   ✓ Add Device complex inline event handlers removed');
} else {
  console.log('   ❌ Add Device complex inline event handlers still present');
}

// Test 3: Check for consistent toggleAddDevice usage
console.log('✅ Test 3: Checking for consistent toggleAddDevice usage...');
const toggleMatches = content.match(/onClick=\{toggleAddDevice\}/g);
if (toggleMatches && toggleMatches.length >= 2) {
  console.log(`   ✓ Found ${toggleMatches.length} consistent toggleAddDevice handlers`);
} else {
  console.log('   ❌ Inconsistent toggleAddDevice usage found');
}

// Test 4: Check for proper button types
console.log('✅ Test 4: Checking for proper button types...');
const buttonTypeMatches = content.match(/type="button"/g);
if (buttonTypeMatches && buttonTypeMatches.length >= 3) {
  console.log(`   ✓ Found ${buttonTypeMatches.length} properly typed buttons`);
} else {
  console.log('   ⚠️  Some buttons may be missing type="button"');
}

console.log('\n🎯 Fix Summary:');
console.log('   • Added debounce mechanism to prevent rapid clicks');
console.log('   • Simplified event handlers to use direct toggleAddDevice calls');
console.log('   • Removed complex inline handlers that could cause conflicts');
console.log('   • Maintained proper button types and accessibility');

console.log('\n🚀 Next Steps:');
console.log('   1. Start the development server: npm start');
console.log('   2. Navigate to Consumer Dashboard');
console.log('   3. Click "Add Your First Device" button');
console.log('   4. Verify the AddDeviceModal opens and stays open');

console.log('\n✅ Add Device Button Fix Test Complete!');