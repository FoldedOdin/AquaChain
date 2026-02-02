#!/usr/bin/env node
/**
 * Quick TypeScript Error Fixes
 * Addresses compilation errors in various components
 */

const fs = require('fs');
const path = require('path');

const fixes = [
  // Fix OrderStatusTracker.tsx - error type issue
  {
    file: 'src/components/Dashboard/OrderStatusTracker.tsx',
    search: 'cause: error',
    replace: 'cause: error ? new Error(error) : undefined'
  },
  
  // Fix AdminDashboard.tsx - timestamp safety
  {
    file: 'src/pages/AdminDashboard.tsx',
    search: 'Latest update: {new Date(latestUpdate.timestamp).toLocaleTimeString()}',
    replace: 'Latest update: {new Date(latestUpdate.timestamp || new Date()).toLocaleTimeString()}'
  },
  
  // Fix Dashboard.tsx - timestamp safety
  {
    file: 'src/pages/Dashboard.tsx',
    search: 'Latest update: {new Date(latestUpdate.timestamp).toLocaleTimeString()}',
    replace: 'Latest update: {new Date(latestUpdate.timestamp || new Date()).toLocaleTimeString()}'
  }
];

function applyFix(fix) {
  const filePath = path.join(__dirname, fix.file);
  
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️ File not found: ${fix.file}`);
    return false;
  }
  
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    
    if (content.includes(fix.search)) {
      content = content.replace(fix.search, fix.replace);
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✅ Fixed: ${fix.file}`);
      return true;
    } else {
      console.log(`⚠️ Pattern not found in: ${fix.file}`);
      return false;
    }
  } catch (error) {
    console.error(`❌ Error fixing ${fix.file}:`, error.message);
    return false;
  }
}

function main() {
  console.log('🔧 Applying TypeScript Error Fixes');
  console.log('=' * 40);
  
  let fixedCount = 0;
  
  fixes.forEach(fix => {
    if (applyFix(fix)) {
      fixedCount++;
    }
  });
  
  console.log(`\n📊 Summary: ${fixedCount}/${fixes.length} fixes applied`);
  
  if (fixedCount === fixes.length) {
    console.log('🎉 All TypeScript errors should be resolved!');
    console.log('\n🚀 Next steps:');
    console.log('1. Restart your development server');
    console.log('2. Check that compilation succeeds');
    console.log('3. Test WebSocket functionality');
  } else {
    console.log('⚠️ Some fixes may need manual attention');
  }
}

if (require.main === module) {
  main();
}

module.exports = { applyFix, fixes };