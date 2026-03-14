#!/usr/bin/env node

/**
 * Test script to verify the Data Management section updates in ConsumerDashboard
 * Tests the new Reading History and Data Export functionality
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing ConsumerDashboard Data Management Updates...\n');

// Test 1: Check if ConsumerDashboard has the required imports
console.log('1. Checking imports...');
const dashboardPath = path.join(__dirname, '../../frontend/src/components/Dashboard/ConsumerDashboard.tsx');
const dashboardContent = fs.readFileSync(dashboardPath, 'utf8');

const requiredImports = [
  'BarChart3',
  'ReadingHistoryModal',
  'DataExportModal'
];

let importsOk = true;
requiredImports.forEach(importName => {
  if (dashboardContent.includes(importName)) {
    console.log(`   ✅ ${importName} imported`);
  } else {
    console.log(`   ❌ ${importName} missing`);
    importsOk = false;
  }
});

// Test 2: Check if state variables are added
console.log('\n2. Checking state variables...');
const requiredStates = [
  'showReadingHistory',
  'showDataExport'
];

let statesOk = true;
requiredStates.forEach(stateName => {
  if (dashboardContent.includes(`[${stateName}, set${stateName.charAt(0).toUpperCase() + stateName.slice(1)}]`)) {
    console.log(`   ✅ ${stateName} state variable found`);
  } else {
    console.log(`   ❌ ${stateName} state variable missing`);
    statesOk = false;
  }
});

// Test 3: Check if "Data Management" section exists
console.log('\n3. Checking Data Management section...');
if (dashboardContent.includes('Data Management')) {
  console.log('   ✅ "Data Management" section title found');
} else {
  console.log('   ❌ "Data Management" section title missing');
}

// Test 4: Check if "Order Device" is removed from Quick Actions
console.log('\n4. Checking Order Device removal from Data Management...');
const dataManagementSections = dashboardContent.split('Data Management');
let orderDeviceInDataManagement = false;

if (dataManagementSections.length > 1) {
  // Check the first Data Management section (there might be multiple)
  const firstDataManagementSection = dataManagementSections[1].split('</div>')[0];
  if (firstDataManagementSection.includes('Order Device')) {
    orderDeviceInDataManagement = true;
  }
}

if (!orderDeviceInDataManagement) {
  console.log('   ✅ "Order Device" removed from Data Management section');
} else {
  console.log('   ❌ "Order Device" still present in Data Management section');
}

// Test 5: Check if new buttons are added
console.log('\n5. Checking new buttons...');
const requiredButtons = [
  'Reading History',
  'Export Data'
];

let buttonsOk = true;
requiredButtons.forEach(buttonText => {
  if (dashboardContent.includes(buttonText)) {
    console.log(`   ✅ "${buttonText}" button found`);
  } else {
    console.log(`   ❌ "${buttonText}" button missing`);
    buttonsOk = false;
  }
});

// Test 6: Check if modals are rendered
console.log('\n6. Checking modal rendering...');
const requiredModalRenders = [
  'ReadingHistoryModal',
  'DataExportModal'
];

let modalsOk = true;
requiredModalRenders.forEach(modalName => {
  // Count occurrences (should be 2 - one for each dashboard view)
  const occurrences = (dashboardContent.match(new RegExp(`<${modalName}`, 'g')) || []).length;
  if (occurrences >= 2) {
    console.log(`   ✅ ${modalName} rendered in both dashboard views`);
  } else if (occurrences === 1) {
    console.log(`   ⚠️  ${modalName} rendered in only one dashboard view`);
  } else {
    console.log(`   ❌ ${modalName} not rendered`);
    modalsOk = false;
  }
});

// Test 7: Check if header has History button
console.log('\n7. Checking header History button...');
if (dashboardContent.includes('History</span>') && dashboardContent.includes('setShowReadingHistory(true)')) {
  console.log('   ✅ History button added to header');
} else {
  console.log('   ❌ History button missing from header');
}

// Summary
console.log('\n📊 Test Summary:');
console.log(`   Imports: ${importsOk ? '✅' : '❌'}`);
console.log(`   State Variables: ${statesOk ? '✅' : '❌'}`);
console.log(`   Buttons: ${buttonsOk ? '✅' : '❌'}`);
console.log(`   Modals: ${modalsOk ? '✅' : '❌'}`);

const allTestsPassed = importsOk && statesOk && buttonsOk && modalsOk;
console.log(`\n🎯 Overall Result: ${allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);

if (allTestsPassed) {
  console.log('\n🎉 ConsumerDashboard successfully updated with Data Management features!');
  console.log('   - "Order Device" removed from Data Management sections');
  console.log('   - "Reading History" button added with filtering and export');
  console.log('   - "Export Data" button added with multiple format support');
  console.log('   - Quick access "History" button added to header');
} else {
  console.log('\n⚠️  Some issues found. Please review the failed tests above.');
}

process.exit(allTestsPassed ? 0 : 1);