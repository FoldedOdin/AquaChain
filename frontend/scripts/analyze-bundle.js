/**
 * Bundle Analysis Script
 * Analyzes webpack bundle size and provides optimization recommendations
 */

const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const fs = require('fs');
const path = require('path');

// Check if build directory exists
const buildDir = path.join(__dirname, '../build');
if (!fs.existsSync(buildDir)) {
  console.error('Build directory not found. Please run "npm run build" first.');
  process.exit(1);
}

// Find JS files in build directory
const staticJsDir = path.join(buildDir, 'static/js');
const jsFiles = fs.readdirSync(staticJsDir)
  .filter(file => file.endsWith('.js') && !file.endsWith('.map'))
  .map(file => path.join(staticJsDir, file));

if (jsFiles.length === 0) {
  console.error('No JavaScript files found in build directory.');
  process.exit(1);
}

console.log('Analyzing bundle...');
console.log('JavaScript files found:');
jsFiles.forEach(file => {
  const stats = fs.statSync(file);
  const sizeKB = (stats.size / 1024).toFixed(2);
  console.log(`  ${path.basename(file)}: ${sizeKB} KB`);
});

// Calculate total bundle size
const totalSize = jsFiles.reduce((total, file) => {
  return total + fs.statSync(file).size;
}, 0);

const totalSizeKB = (totalSize / 1024).toFixed(2);
const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);

console.log(`\nTotal JavaScript bundle size: ${totalSizeKB} KB (${totalSizeMB} MB)`);

// Performance recommendations
console.log('\n=== Performance Recommendations ===');

if (totalSize > 1024 * 1024) { // > 1MB
  console.log('⚠️  Bundle size is large (>1MB). Consider:');
  console.log('   - Code splitting with React.lazy()');
  console.log('   - Tree shaking unused dependencies');
  console.log('   - Dynamic imports for non-critical code');
} else if (totalSize > 512 * 1024) { // > 512KB
  console.log('⚡ Bundle size is moderate (>512KB). Consider:');
  console.log('   - Lazy loading non-critical components');
  console.log('   - Analyzing large dependencies');
} else {
  console.log('✅ Bundle size is good (<512KB)');
}

// Check for common large dependencies
const packageJson = require('../package.json');
const largeDependencies = [
  'moment',
  'lodash',
  'rxjs',
  'aws-sdk',
  '@aws-sdk',
  'recharts'
];

const foundLargeDeps = largeDependencies.filter(dep => 
  packageJson.dependencies[dep] || 
  Object.keys(packageJson.dependencies).some(key => key.startsWith(dep))
);

if (foundLargeDeps.length > 0) {
  console.log('\n📦 Large dependencies detected:');
  foundLargeDeps.forEach(dep => {
    console.log(`   - ${dep} (consider alternatives or tree shaking)`);
  });
}

// CSS analysis
const cssDir = path.join(buildDir, 'static/css');
if (fs.existsSync(cssDir)) {
  const cssFiles = fs.readdirSync(cssDir)
    .filter(file => file.endsWith('.css'))
    .map(file => path.join(cssDir, file));
  
  const totalCssSize = cssFiles.reduce((total, file) => {
    return total + fs.statSync(file).size;
  }, 0);
  
  const totalCssSizeKB = (totalCssSize / 1024).toFixed(2);
  console.log(`\nTotal CSS size: ${totalCssSizeKB} KB`);
  
  if (totalCssSize > 100 * 1024) { // > 100KB
    console.log('⚠️  CSS size is large. Consider:');
    console.log('   - Purging unused CSS with PurgeCSS');
    console.log('   - Critical CSS extraction');
    console.log('   - CSS minification');
  }
}

console.log('\n=== Bundle Analysis Complete ===');
console.log('For detailed analysis, run: npm run build:analyze');