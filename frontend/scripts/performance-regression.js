/**
 * Performance Regression Detection Script
 * Compares current performance metrics with baseline to detect regressions
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Regression thresholds (percentage increase that triggers alert)
const REGRESSION_THRESHOLDS = {
  bundleSize: 10,      // 10% increase in bundle size
  lcp: 15,             // 15% increase in LCP
  fid: 20,             // 20% increase in FID
  cls: 25,             // 25% increase in CLS
  fcp: 15,             // 15% increase in FCP
  tti: 20,             // 20% increase in TTI
  tbt: 25,             // 25% increase in TBT
  si: 15               // 15% increase in Speed Index
};

class PerformanceRegressionDetector {
  constructor() {
    this.baselineFile = path.join(__dirname, '../performance-baseline.json');
    this.currentMetrics = {};
    this.baselineMetrics = {};
    this.regressions = [];
    this.improvements = [];
  }

  async run() {
    console.log('🔍 Running Performance Regression Detection...\n');
    
    try {
      // Collect current metrics
      await this.collectCurrentMetrics();
      
      // Load baseline metrics
      this.loadBaselineMetrics();
      
      // Compare metrics
      this.compareMetrics();
      
      // Generate report
      this.generateReport();
      
      // Update baseline if no regressions
      if (this.regressions.length === 0) {
        this.updateBaseline();
      }
      
      // Exit with appropriate code
      process.exit(this.regressions.length > 0 ? 1 : 0);
      
    } catch (error) {
      console.error('❌ Performance regression detection failed:', error.message);
      process.exit(1);
    }
  }

  async collectCurrentMetrics() {
    console.log('📊 Collecting current performance metrics...');
    
    // Collect bundle size metrics
    this.currentMetrics.bundleSize = this.getBundleSize();
    
    // Collect Lighthouse metrics (if server is running)
    try {
      const lighthouseMetrics = await this.getLighthouseMetrics();
      this.currentMetrics = { ...this.currentMetrics, ...lighthouseMetrics };
    } catch (error) {
      console.warn('⚠️  Could not collect Lighthouse metrics:', error.message);
    }
    
    console.log('Current metrics collected ✅');
  }

  getBundleSize() {
    const buildDir = path.join(__dirname, '../build');
    const staticJsDir = path.join(buildDir, 'static/js');
    
    if (!fs.existsSync(staticJsDir)) {
      throw new Error('Build directory not found. Run "npm run build" first.');
    }
    
    const jsFiles = fs.readdirSync(staticJsDir)
      .filter(file => file.endsWith('.js') && !file.endsWith('.map'))
      .map(file => fs.statSync(path.join(staticJsDir, file)).size);
    
    return jsFiles.reduce((total, size) => total + size, 0);
  }

  async getLighthouseMetrics() {
    // Check if server is running
    const isServerRunning = await this.checkServerRunning();
    if (!isServerRunning) {
      throw new Error('Development server not running');
    }
    
    // Run Lighthouse programmatically
    const lighthouse = require('lighthouse');
    const chromeLauncher = require('chrome-launcher');
    
    const chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--no-sandbox', '--disable-gpu']
    });
    
    try {
      const options = {
        logLevel: 'error',
        output: 'json',
        onlyCategories: ['performance'],
        port: chrome.port
      };
      
      const runnerResult = await lighthouse('http://localhost:3000', options);
      const metrics = runnerResult.lhr.audits;
      
      return {
        lcp: metrics['largest-contentful-paint'].numericValue,
        fid: metrics['max-potential-fid'].numericValue,
        cls: metrics['cumulative-layout-shift'].numericValue,
        fcp: metrics['first-contentful-paint'].numericValue,
        tti: metrics['interactive'].numericValue,
        tbt: metrics['total-blocking-time'].numericValue,
        si: metrics['speed-index'].numericValue
      };
    } finally {
      await chrome.kill();
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

  loadBaselineMetrics() {
    if (fs.existsSync(this.baselineFile)) {
      const baselineData = fs.readFileSync(this.baselineFile, 'utf8');
      this.baselineMetrics = JSON.parse(baselineData);
      console.log('📈 Baseline metrics loaded');
    } else {
      console.log('📝 No baseline found, creating new baseline');
      this.baselineMetrics = {};
    }
  }

  compareMetrics() {
    console.log('🔄 Comparing metrics with baseline...');
    
    Object.keys(this.currentMetrics).forEach(metric => {
      const currentValue = this.currentMetrics[metric];
      const baselineValue = this.baselineMetrics[metric];
      
      if (baselineValue === undefined) {
        console.log(`📝 New metric: ${metric} = ${this.formatMetric(metric, currentValue)}`);
        return;
      }
      
      const percentageChange = ((currentValue - baselineValue) / baselineValue) * 100;
      const threshold = REGRESSION_THRESHOLDS[metric] || 10;
      
      if (percentageChange > threshold) {
        this.regressions.push({
          metric,
          current: currentValue,
          baseline: baselineValue,
          change: percentageChange,
          threshold
        });
      } else if (percentageChange < -5) { // 5% improvement threshold
        this.improvements.push({
          metric,
          current: currentValue,
          baseline: baselineValue,
          change: percentageChange
        });
      }
    });
  }

  generateReport() {
    console.log('\n📊 Performance Regression Report');
    console.log('==================================\n');
    
    if (this.improvements.length > 0) {
      console.log('🚀 Performance Improvements:');
      this.improvements.forEach(item => {
        console.log(`  ${item.metric}: ${this.formatMetric(item.metric, item.baseline)} → ${this.formatMetric(item.metric, item.current)} (${item.change.toFixed(1)}% better)`);
      });
      console.log('');
    }
    
    if (this.regressions.length > 0) {
      console.log('⚠️  Performance Regressions Detected:');
      this.regressions.forEach(item => {
        console.log(`  ${item.metric}: ${this.formatMetric(item.metric, item.baseline)} → ${this.formatMetric(item.metric, item.current)} (+${item.change.toFixed(1)}%, threshold: ${item.threshold}%)`);
      });
      console.log('');
      
      console.log('💡 Regression Analysis:');
      this.regressions.forEach(item => {
        console.log(`  ${item.metric}: ${this.getRecommendation(item.metric)}`);
      });
      console.log('');
    }
    
    if (this.regressions.length === 0 && this.improvements.length === 0) {
      console.log('✅ No significant performance changes detected');
    }
    
    // Summary
    const totalMetrics = Object.keys(this.currentMetrics).length;
    const regressedMetrics = this.regressions.length;
    const improvedMetrics = this.improvements.length;
    const stableMetrics = totalMetrics - regressedMetrics - improvedMetrics;
    
    console.log(`📈 Summary: ${improvedMetrics} improved, ${stableMetrics} stable, ${regressedMetrics} regressed`);
    
    if (this.regressions.length > 0) {
      console.log(`❌ ${this.regressions.length} performance regression(s) detected!`);
      console.log('Consider reverting recent changes or optimizing the affected areas.');
    } else {
      console.log('🎉 No performance regressions detected!');
    }
  }

  getRecommendation(metric) {
    const recommendations = {
      bundleSize: 'Check for new dependencies or unused code. Use bundle analyzer.',
      lcp: 'Optimize images, reduce server response time, or improve critical rendering path.',
      fid: 'Reduce JavaScript execution time and break up long tasks.',
      cls: 'Set dimensions for images and ads, avoid inserting content above existing content.',
      fcp: 'Optimize critical rendering path and reduce render-blocking resources.',
      tti: 'Reduce JavaScript execution time and optimize third-party scripts.',
      tbt: 'Break up long tasks and optimize JavaScript execution.',
      si: 'Optimize above-the-fold content and reduce render-blocking resources.'
    };
    
    return recommendations[metric] || 'Review recent changes that might affect this metric.';
  }

  formatMetric(metric, value) {
    if (metric === 'bundleSize') {
      return this.formatBytes(value);
    } else if (metric === 'cls') {
      return value.toFixed(3);
    } else {
      return `${Math.round(value)}ms`;
    }
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  updateBaseline() {
    const baselineData = {
      ...this.currentMetrics,
      timestamp: new Date().toISOString(),
      version: this.getVersion()
    };
    
    fs.writeFileSync(this.baselineFile, JSON.stringify(baselineData, null, 2));
    console.log('📝 Baseline updated with current metrics');
  }

  getVersion() {
    try {
      const packageJson = require('../package.json');
      return packageJson.version;
    } catch {
      return 'unknown';
    }
  }
}

// Run the detector
if (require.main === module) {
  const detector = new PerformanceRegressionDetector();
  detector.run();
}

module.exports = PerformanceRegressionDetector;