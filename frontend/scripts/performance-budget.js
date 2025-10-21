/**
 * Performance Budget Monitoring Script
 * Monitors bundle sizes and performance metrics against defined budgets
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Performance budgets configuration
const PERFORMANCE_BUDGETS = {
  // Bundle size budgets (in bytes)
  bundles: {
    'main': 512 * 1024,      // 512KB for main bundle
    'vendor': 1024 * 1024,   // 1MB for vendor bundle
    'total': 2 * 1024 * 1024 // 2MB total JavaScript
  },
  
  // Asset size budgets (in bytes)
  assets: {
    'css': 100 * 1024,       // 100KB for CSS
    'images': 1024 * 1024,   // 1MB for images
    'fonts': 200 * 1024      // 200KB for fonts
  },
  
  // Performance metrics budgets
  metrics: {
    'lcp': 2500,             // Largest Contentful Paint (ms)
    'fid': 100,              // First Input Delay (ms)
    'cls': 0.1,              // Cumulative Layout Shift
    'fcp': 1800,             // First Contentful Paint (ms)
    'tti': 3800,             // Time to Interactive (ms)
    'tbt': 300,              // Total Blocking Time (ms)
    'si': 3000               // Speed Index (ms)
  },
  
  // Network budgets
  network: {
    'requests': 50,          // Maximum number of requests
    'thirdParty': 10         // Maximum third-party requests
  }
};

class PerformanceBudgetMonitor {
  constructor() {
    this.buildDir = path.join(__dirname, '../build');
    this.results = {
      passed: [],
      failed: [],
      warnings: []
    };
  }

  async run() {
    console.log('🔍 Running Performance Budget Analysis...\n');
    
    try {
      // Check if build exists
      if (!fs.existsSync(this.buildDir)) {
        throw new Error('Build directory not found. Run "npm run build" first.');
      }
      
      // Analyze bundle sizes
      await this.analyzeBundleSizes();
      
      // Analyze asset sizes
      await this.analyzeAssetSizes();
      
      // Run Lighthouse analysis
      await this.runLighthouseAnalysis();
      
      // Generate report
      this.generateReport();
      
      // Exit with appropriate code
      process.exit(this.results.failed.length > 0 ? 1 : 0);
      
    } catch (error) {
      console.error('❌ Performance budget analysis failed:', error.message);
      process.exit(1);
    }
  }

  async analyzeBundleSizes() {
    console.log('📦 Analyzing bundle sizes...');
    
    const staticJsDir = path.join(this.buildDir, 'static/js');
    if (!fs.existsSync(staticJsDir)) {
      this.results.failed.push('JavaScript build directory not found');
      return;
    }
    
    const jsFiles = fs.readdirSync(staticJsDir)
      .filter(file => file.endsWith('.js') && !file.endsWith('.map'))
      .map(file => ({
        name: file,
        path: path.join(staticJsDir, file),
        size: fs.statSync(path.join(staticJsDir, file)).size
      }));
    
    // Calculate total JavaScript size
    const totalJsSize = jsFiles.reduce((total, file) => total + file.size, 0);
    
    // Check total bundle budget
    if (totalJsSize > PERFORMANCE_BUDGETS.bundles.total) {
      this.results.failed.push(
        `Total JavaScript size (${this.formatBytes(totalJsSize)}) exceeds budget (${this.formatBytes(PERFORMANCE_BUDGETS.bundles.total)})`
      );
    } else {
      this.results.passed.push(
        `Total JavaScript size: ${this.formatBytes(totalJsSize)} ✅`
      );
    }
    
    // Check individual bundle sizes
    jsFiles.forEach(file => {
      const budgetKey = this.getBundleType(file.name);
      const budget = PERFORMANCE_BUDGETS.bundles[budgetKey];
      
      if (budget && file.size > budget) {
        this.results.failed.push(
          `${file.name} (${this.formatBytes(file.size)}) exceeds ${budgetKey} budget (${this.formatBytes(budget)})`
        );
      }
    });
  }

  async analyzeAssetSizes() {
    console.log('🎨 Analyzing asset sizes...');
    
    // Analyze CSS
    const cssDir = path.join(this.buildDir, 'static/css');
    if (fs.existsSync(cssDir)) {
      const cssSize = this.calculateDirectorySize(cssDir, '.css');
      if (cssSize > PERFORMANCE_BUDGETS.assets.css) {
        this.results.failed.push(
          `CSS size (${this.formatBytes(cssSize)}) exceeds budget (${this.formatBytes(PERFORMANCE_BUDGETS.assets.css)})`
        );
      } else {
        this.results.passed.push(`CSS size: ${this.formatBytes(cssSize)} ✅`);
      }
    }
    
    // Analyze images
    const mediaDir = path.join(this.buildDir, 'static/media');
    if (fs.existsSync(mediaDir)) {
      const imageSize = this.calculateDirectorySize(mediaDir, /\.(jpg|jpeg|png|gif|webp|svg|avif)$/);
      if (imageSize > PERFORMANCE_BUDGETS.assets.images) {
        this.results.failed.push(
          `Image size (${this.formatBytes(imageSize)}) exceeds budget (${this.formatBytes(PERFORMANCE_BUDGETS.assets.images)})`
        );
      } else {
        this.results.passed.push(`Image size: ${this.formatBytes(imageSize)} ✅`);
      }
    }
    
    // Check for font optimization
    const fontFiles = this.findFiles(this.buildDir, /\.(woff|woff2|ttf|otf)$/);
    if (fontFiles.length > 0) {
      const fontSize = fontFiles.reduce((total, file) => total + fs.statSync(file).size, 0);
      if (fontSize > PERFORMANCE_BUDGETS.assets.fonts) {
        this.results.failed.push(
          `Font size (${this.formatBytes(fontSize)}) exceeds budget (${this.formatBytes(PERFORMANCE_BUDGETS.assets.fonts)})`
        );
      } else {
        this.results.passed.push(`Font size: ${this.formatBytes(fontSize)} ✅`);
      }
    }
  }

  async runLighthouseAnalysis() {
    console.log('🚦 Running Lighthouse analysis...');
    
    try {
      // Check if server is running
      const isServerRunning = await this.checkServerRunning();
      if (!isServerRunning) {
        this.results.warnings.push('Development server not running. Skipping Lighthouse analysis.');
        return;
      }
      
      // Run Lighthouse CI
      const lhciResult = execSync('npx lhci autorun --config=lighthouserc.js', {
        cwd: path.dirname(__dirname),
        encoding: 'utf8',
        stdio: 'pipe'
      });
      
      this.results.passed.push('Lighthouse analysis passed ✅');
      
    } catch (error) {
      // Parse Lighthouse errors
      const errorOutput = error.stdout || error.stderr || error.message;
      if (errorOutput.includes('budget')) {
        this.results.failed.push('Lighthouse performance budget exceeded');
      } else {
        this.results.warnings.push(`Lighthouse analysis warning: ${errorOutput.split('\n')[0]}`);
      }
    }
  }

  async checkServerRunning() {
    try {
      const response = await fetch('http://localhost:3000');
      return response.ok;
    } catch {
      return false;
    }
  }

  getBundleType(filename) {
    if (filename.includes('vendor') || filename.includes('chunk')) {
      return 'vendor';
    }
    return 'main';
  }

  calculateDirectorySize(dir, extension) {
    if (!fs.existsSync(dir)) return 0;
    
    const files = fs.readdirSync(dir);
    let totalSize = 0;
    
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        totalSize += this.calculateDirectorySize(filePath, extension);
      } else if (typeof extension === 'string' ? file.endsWith(extension) : extension.test(file)) {
        totalSize += stat.size;
      }
    });
    
    return totalSize;
  }

  findFiles(dir, pattern) {
    const files = [];
    
    if (!fs.existsSync(dir)) return files;
    
    const entries = fs.readdirSync(dir);
    
    entries.forEach(entry => {
      const fullPath = path.join(dir, entry);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.findFiles(fullPath, pattern));
      } else if (pattern.test(entry)) {
        files.push(fullPath);
      }
    });
    
    return files;
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  generateReport() {
    console.log('\n📊 Performance Budget Report');
    console.log('================================\n');
    
    if (this.results.passed.length > 0) {
      console.log('✅ Passed Checks:');
      this.results.passed.forEach(item => console.log(`  ${item}`));
      console.log('');
    }
    
    if (this.results.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      this.results.warnings.forEach(item => console.log(`  ${item}`));
      console.log('');
    }
    
    if (this.results.failed.length > 0) {
      console.log('❌ Failed Checks:');
      this.results.failed.forEach(item => console.log(`  ${item}`));
      console.log('');
      
      console.log('💡 Recommendations:');
      console.log('  - Use code splitting to reduce bundle sizes');
      console.log('  - Optimize images with WebP format and compression');
      console.log('  - Remove unused CSS and JavaScript');
      console.log('  - Use font-display: swap for web fonts');
      console.log('  - Enable gzip/brotli compression');
      console.log('');
    }
    
    const totalChecks = this.results.passed.length + this.results.failed.length;
    const passRate = totalChecks > 0 ? Math.round((this.results.passed.length / totalChecks) * 100) : 0;
    
    console.log(`📈 Overall Score: ${passRate}% (${this.results.passed.length}/${totalChecks} checks passed)`);
    
    if (this.results.failed.length === 0) {
      console.log('🎉 All performance budgets are within limits!');
    } else {
      console.log(`⚠️  ${this.results.failed.length} performance budget(s) exceeded.`);
    }
  }
}

// Run the monitor
if (require.main === module) {
  const monitor = new PerformanceBudgetMonitor();
  monitor.run();
}

module.exports = PerformanceBudgetMonitor;