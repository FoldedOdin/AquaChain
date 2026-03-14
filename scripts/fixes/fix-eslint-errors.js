#!/usr/bin/env node
/**
 * Fix Common ESLint Errors in AquaChain Frontend
 * This script fixes the most common and easily fixable ESLint errors
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 Fixing ESLint Errors in AquaChain Frontend');
console.log('=' .repeat(60));

/**
 * Fix redundant await statements
 */
function fixRedundantAwait(content) {
  // Fix "return await" patterns
  const patterns = [
    /return await (\w+\([^)]*\));/g,
    /return await (\w+\.\w+\([^)]*\));/g,
    /return await (\w+\.\w+\.\w+\([^)]*\));/g
  ];
  
  let fixed = content;
  patterns.forEach(pattern => {
    fixed = fixed.replace(pattern, 'return $1;');
  });
  
  return fixed;
}

/**
 * Remove console statements (but keep console.error for error handling)
 */
function removeConsoleStatements(content) {
  // Remove console.log, console.warn, console.info but keep console.error
  const patterns = [
    /\s*console\.log\([^)]*\);\s*\n/g,
    /\s*console\.warn\([^)]*\);\s*\n/g,
    /\s*console\.info\([^)]*\);\s*\n/g,
    /console\.log\([^)]*\);\s*/g,
    /console\.warn\([^)]*\);\s*/g,
    /console\.info\([^)]*\);\s*/g
  ];
  
  let fixed = content;
  patterns.forEach(pattern => {
    fixed = fixed.replace(pattern, '');
  });
  
  return fixed;
}

/**
 * Add return types to simple functions
 */
function addReturnTypes(content) {
  // Add void return type to functions that don't return anything
  let fixed = content;
  
  // Pattern for functions that likely return void
  const voidPatterns = [
    /(const \w+ = \([^)]*\)) => {[^}]*(?:setState|set\w+|console\.|return;)[^}]*}/g,
    /(const handle\w+ = \([^)]*\)) => {/g,
    /(const on\w+ = \([^)]*\)) => {/g
  ];
  
  voidPatterns.forEach(pattern => {
    fixed = fixed.replace(pattern, (match, funcDef) => {
      if (!funcDef.includes(': ')) {
        return match.replace(funcDef, funcDef + ': void');
      }
      return match;
    });
  });
  
  return fixed;
}

/**
 * Remove unused variables by prefixing with underscore
 */
function fixUnusedVariables(content) {
  let fixed = content;
  
  // Common unused variable patterns
  const patterns = [
    { 
      regex: /(\w+) is defined but never used/g,
      fix: (match, varName) => `_${varName}`
    }
  ];
  
  // This is a simple approach - in practice, you'd need to parse the actual ESLint output
  // For now, let's fix some common cases manually
  
  // Fix unused parameters in function signatures
  fixed = fixed.replace(/\((\w+): [^,)]+\) =>/g, (match, param) => {
    // Check if parameter is used in the function body (simple check)
    const functionStart = fixed.indexOf(match);
    const functionBody = fixed.substring(functionStart, functionStart + 500);
    if (!functionBody.includes(param) || functionBody.split(param).length <= 2) {
      return match.replace(param, `_${param}`);
    }
    return match;
  });
  
  return fixed;
}

/**
 * Fix unnecessary escape characters in regex
 */
function fixUnnecessaryEscapes(content) {
  let fixed = content;
  
  // Fix common unnecessary escapes in regex
  fixed = fixed.replace(/\\\+/g, '+');
  fixed = fixed.replace(/\\\(/g, '(');
  fixed = fixed.replace(/\\\)/g, ')');
  
  return fixed;
}

/**
 * Process a single file
 */
function processFile(filePath) {
  try {
    console.log(`📝 Processing: ${filePath}`);
    
    let content = fs.readFileSync(filePath, 'utf8');
    const originalContent = content;
    
    // Apply fixes
    content = fixRedundantAwait(content);
    content = removeConsoleStatements(content);
    content = addReturnTypes(content);
    content = fixUnusedVariables(content);
    content = fixUnnecessaryEscapes(content);
    
    // Only write if content changed
    if (content !== originalContent) {
      fs.writeFileSync(filePath, content);
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

/**
 * Get all TypeScript files in frontend/src
 */
function getTypeScriptFiles(dir) {
  const files = [];
  
  function walkDir(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        // Skip node_modules and build directories
        if (!['node_modules', 'build', 'dist', '.git'].includes(item)) {
          walkDir(fullPath);
        }
      } else if (item.endsWith('.ts') || item.endsWith('.tsx')) {
        files.push(fullPath);
      }
    }
  }
  
  walkDir(dir);
  return files;
}

/**
 * Main function
 */
function main() {
  const frontendSrcDir = path.join(__dirname, '../../frontend/src');
  
  if (!fs.existsSync(frontendSrcDir)) {
    console.log('❌ Frontend src directory not found');
    return;
  }
  
  console.log(`🔍 Scanning for TypeScript files in: ${frontendSrcDir}`);
  
  const tsFiles = getTypeScriptFiles(frontendSrcDir);
  console.log(`📋 Found ${tsFiles.length} TypeScript files`);
  
  let fixedCount = 0;
  
  // Process specific files that have the most errors
  const priorityFiles = [
    'frontend/src/services/dataServiceSelector.ts',
    'frontend/src/services/dataService.ts',
    'frontend/src/components/LandingPage/ContactForm.tsx',
    'frontend/src/contexts/AuthContext.tsx',
    'frontend/src/services/authService.ts'
  ];
  
  console.log('\n🎯 Processing priority files first...');
  
  for (const file of priorityFiles) {
    const fullPath = path.join(__dirname, '../../', file);
    if (fs.existsSync(fullPath)) {
      if (processFile(fullPath)) {
        fixedCount++;
      }
    }
  }
  
  console.log('\n📊 Processing remaining files...');
  
  // Process remaining files (limit to avoid overwhelming output)
  const remainingFiles = tsFiles
    .filter(file => !priorityFiles.some(pf => file.includes(pf.replace('frontend/src/', ''))))
    .slice(0, 20); // Process first 20 remaining files
  
  for (const file of remainingFiles) {
    if (processFile(file)) {
      fixedCount++;
    }
  }
  
  console.log('\n📋 SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Files processed: ${priorityFiles.length + remainingFiles.length}`);
  console.log(`🔧 Files fixed: ${fixedCount}`);
  console.log(`📁 Total TypeScript files: ${tsFiles.length}`);
  
  console.log('\n💡 Next steps:');
  console.log('1. Run the frontend development server to see remaining errors');
  console.log('2. For complex issues (long functions, high complexity), manual refactoring is needed');
  console.log('3. Consider breaking large components into smaller ones');
  console.log('4. Add proper TypeScript return types to remaining functions');
  
  console.log('\n🔄 To continue fixing:');
  console.log('   cd frontend && npm start');
}

main();