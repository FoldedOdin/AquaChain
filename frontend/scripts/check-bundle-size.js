/**
 * Bundle Size Checker
 * Validates that bundle sizes are within acceptable limits
 */

const fs = require('fs');
const path = require('path');

// Bundle size limits (in KB)
const LIMITS = {
  main: 500,
  vendor: 800,
  total: 1000
};

function getFileSize(filePath) {
  const stats = fs.statSync(filePath);
  return Math.round(stats.size / 1024); // Convert to KB
}

function checkBundleSize() {
  const buildDir = path.join(__dirname, '..', 'build', 'static', 'js');
  
  if (!fs.existsSync(buildDir)) {
    console.error('❌ Build directory not found. Run "npm run build" first.');
    process.exit(1);
  }

  const files = fs.readdirSync(buildDir);
  const jsFiles = files.filter(f => f.endsWith('.js') && !f.endsWith('.map'));

  let totalSize = 0;
  let mainSize = 0;
  let vendorSize = 0;
  let hasErrors = false;

  console.log('\n📦 Bundle Size Report\n');
  console.log('File                                    Size      Limit     Status');
  console.log('─────────────────────────────────────────────────────────────────');

  jsFiles.forEach(file => {
    const filePath = path.join(buildDir, file);
    const size = getFileSize(filePath);
    totalSize += size;

    let limit = null;
    let type = 'chunk';

    if (file.includes('main')) {
      mainSize += size;
      limit = LIMITS.main;
      type = 'main';
    } else if (file.includes('vendor') || file.includes('react') || file.includes('aws')) {
      vendorSize += size;
      limit = LIMITS.vendor;
      type = 'vendor';
    }

    const status = limit && size > limit ? '❌ OVER' : '✅ OK';
    if (limit && size > limit) {
      hasErrors = true;
    }

    const limitStr = limit ? `${limit} KB` : 'N/A';
    const fileName = file.length > 35 ? file.substring(0, 32) + '...' : file;
    
    console.log(
      `${fileName.padEnd(40)} ${String(size + ' KB').padEnd(10)} ${limitStr.padEnd(10)} ${status}`
    );
  });

  console.log('─────────────────────────────────────────────────────────────────');
  console.log(`Total Bundle Size:                      ${totalSize} KB    ${LIMITS.total} KB    ${totalSize > LIMITS.total ? '❌ OVER' : '✅ OK'}`);
  console.log('');

  if (totalSize > LIMITS.total) {
    hasErrors = true;
  }

  // Summary
  console.log('\n📊 Summary\n');
  console.log(`Main Bundle:   ${mainSize} KB / ${LIMITS.main} KB`);
  console.log(`Vendor Bundle: ${vendorSize} KB / ${LIMITS.vendor} KB`);
  console.log(`Total Size:    ${totalSize} KB / ${LIMITS.total} KB`);
  console.log('');

  if (hasErrors) {
    console.error('❌ Bundle size exceeds limits! Consider:');
    console.error('   - Lazy loading more components');
    console.error('   - Removing unused dependencies');
    console.error('   - Using dynamic imports');
    console.error('   - Optimizing images and assets');
    console.error('');
    process.exit(1);
  } else {
    console.log('✅ All bundle sizes are within limits!');
    console.log('');
  }
}

checkBundleSize();
