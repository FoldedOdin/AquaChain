#!/usr/bin/env node
/**
 * Fix syntax errors caused by missing line breaks
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 Fixing syntax errors in frontend files');

const filesToFix = [
  'frontend/src/contexts/AuthContext.tsx',
  'frontend/src/services/authService.ts',
  'frontend/src/services/dataService.ts'
];

function fixLineBreaks(content) {
  // Fix common patterns where line breaks are missing
  let fixed = content;
  
  // Fix missing line breaks after comments
  fixed = fixed.replace(/\/\/ ([^\/\n]+)([A-Z])/g, '// $1\n$2');
  
  // Fix missing line breaks after semicolons before keywords
  fixed = fixed.replace(/;(\s*)(if|else|try|catch|function|const|let|var|return|throw)/g, ';\n$1$2');
  
  // Fix missing line breaks after closing braces before keywords
  fixed = fixed.replace(/}(\s*)(if|else|try|catch|function|const|let|var|return|throw)/g, '}\n$1$2');
  
  // Fix missing line breaks after opening braces
  fixed = fixed.replace(/{(\s*)([A-Z])/g, '{\n$1$2');
  
  // Fix specific patterns found in the files
  fixed = fixed.replace(/setUser\(userProfile\);(\s*)setIsAuthenticated/g, 'setUser(userProfile);\n$1setIsAuthenticated');
  fixed = fixed.replace(/setIsAuthenticated\(true\);(\s*)\/\/ Fetch/g, 'setIsAuthenticated(true);\n$1// Fetch');
  fixed = fixed.replace(/\/\/ Fetch complete profile from backend in background(\s*)setTimeout/g, '// Fetch complete profile from backend in background\n$1setTimeout');
  fixed = fixed.replace(/if \(profileResult\.success && profileResult\.profile\) {(\s*)\/\/ Update/g, 'if (profileResult.success && profileResult.profile) {\n$1// Update');
  fixed = fixed.replace(/if \(trackResponse\.ok\) {(\s*)} else/g, 'if (trackResponse.ok) {\n$1console.log(\'✅ Login tracked successfully\');\n$1} else');
  fixed = fixed.replace(/try {(\s*)const profileResponse/g, 'try {\n$1const profileResponse');
  
  return fixed;
}

function processFile(filePath) {
  try {
    const fullPath = path.join(__dirname, '../../', filePath);
    
    if (!fs.existsSync(fullPath)) {
      console.log(`⏭️  File not found: ${filePath}`);
      return false;
    }
    
    console.log(`📝 Processing: ${filePath}`);
    
    let content = fs.readFileSync(fullPath, 'utf8');
    const originalContent = content;
    
    content = fixLineBreaks(content);
    
    if (content !== originalContent) {
      fs.writeFileSync(fullPath, content);
      console.log(`✅ Fixed: ${filePath}`);
      return true;
    } else {
      console.log(`⏭️  No changes: ${filePath}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Error processing ${filePath}: ${error.message}`);
    return false;
  }
}

function main() {
  console.log('🔍 Fixing syntax errors in key files...\n');
  
  let fixedCount = 0;
  
  for (const file of filesToFix) {
    if (processFile(file)) {
      fixedCount++;
    }
  }
  
  console.log('\n📋 SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Files processed: ${filesToFix.length}`);
  console.log(`🔧 Files fixed: ${fixedCount}`);
  
  console.log('\n💡 Next step: Try running npm run build');
}

main();