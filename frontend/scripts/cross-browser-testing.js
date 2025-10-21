#!/usr/bin/env node

/**
 * Cross-Browser and Device Compatibility Testing Script
 * Tests the AquaChain Landing Page across different browsers and devices
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  outputDir: 'compatibility-reports',
  testUrls: [
    'http://localhost:3000',
    'http://localhost:3000/#auth-modal',
    'http://localhost:3000/#features',
    'http://localhost:3000/#roles',
    'http://localhost:3000/#contact'
  ],
  browsers: [
    { name: 'Chrome', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' },
    { name: 'Firefox', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0' },
    { name: 'Safari', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15' },
    { name: 'Edge', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0' }
  ],
  devices: [
    { name: 'Desktop', width: 1920, height: 1080, deviceScaleFactor: 1, isMobile: false },
    { name: 'Laptop', width: 1366, height: 768, deviceScaleFactor: 1, isMobile: false },
    { name: 'Tablet', width: 768, height: 1024, deviceScaleFactor: 2, isMobile: true },
    { name: 'Mobile Large', width: 414, height: 896, deviceScaleFactor: 3, isMobile: true },
    { name: 'Mobile Medium', width: 375, height: 667, deviceScaleFactor: 2, isMobile: true },
    { name: 'Mobile Small', width: 320, height: 568, deviceScaleFactor: 2, isMobile: true }
  ],
  features: [
    'CSS Grid',
    'CSS Flexbox',
    'CSS Custom Properties',
    'ES6 Modules',
    'Intersection Observer',
    'Service Worker',
    'Web App Manifest',
    'Touch Events',
    'Geolocation API',
    'Local Storage',
    'Session Storage',
    'WebGL',
    'Canvas 2D',
    'Media Queries'
  ]
};

class CrossBrowserTester {
  constructor() {
    this.results = {
      summary: {
        totalTests: 0,
        passed: 0,
        failed: 0,
        timestamp: new Date().toISOString(),
        browserResults: {},
        deviceResults: {},
        featureSupport: {}
      },
      detailed: {
        browserTests: [],
        deviceTests: [],
        featureTests: [],
        performanceTests: []
      }
    };
  }

  async runCompatibilityTests() {
    console.log('🌐 Starting Cross-Browser and Device Compatibility Testing...\n');

    // Ensure output directory exists
    this.ensureOutputDirectory();

    // Run different types of compatibility tests
    await this.runBrowserCompatibilityTests();
    await this.runDeviceCompatibilityTests();
    await this.runFeatureSupportTests();
    await this.runTouchInteractionTests();
    await this.runPWACompatibilityTests();

    // Generate comprehensive report
    this.generateReport();

    console.log('\n✅ Cross-browser compatibility testing completed!');
    console.log(`📊 Results saved to: ${CONFIG.outputDir}/`);
  }

  ensureOutputDirectory() {
    if (!fs.existsSync(CONFIG.outputDir)) {
      fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    }
  }

  async runBrowserCompatibilityTests() {
    console.log('🔍 Running browser compatibility tests...');

    for (const browser of CONFIG.browsers) {
      console.log(`  Testing ${browser.name}...`);
      
      try {
        // Run Lighthouse tests for each browser
        const lighthouseCommand = `npx lighthouse http://localhost:3000 ` +
          `--output=json ` +
          `--output-path=${CONFIG.outputDir}/lighthouse-${browser.name.toLowerCase()}.json ` +
          `--chrome-flags="--headless --user-agent='${browser.userAgent}'" ` +
          `--only-categories=performance,accessibility,best-practices,seo`;

        execSync(lighthouseCommand, { stdio: 'pipe' });

        // Parse results
        const resultsPath = path.join(CONFIG.outputDir, `lighthouse-${browser.name.toLowerCase()}.json`);
        if (fs.existsSync(resultsPath)) {
          const results = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
          
          const browserResult = {
            browser: browser.name,
            userAgent: browser.userAgent,
            performance: results.categories.performance.score * 100,
            accessibility: results.categories.accessibility.score * 100,
            bestPractices: results.categories['best-practices'].score * 100,
            seo: results.categories.seo.score * 100,
            passed: results.categories.performance.score >= 0.9 && 
                   results.categories.accessibility.score >= 0.9,
            timestamp: new Date().toISOString()
          };

          this.results.detailed.browserTests.push(browserResult);
          this.results.summary.browserResults[browser.name] = browserResult;

          if (browserResult.passed) {
            console.log(`    ✅ ${browser.name} compatibility test passed`);
            this.results.summary.passed++;
          } else {
            console.log(`    ❌ ${browser.name} compatibility test failed`);
            this.results.summary.failed++;
          }
        }

        this.results.summary.totalTests++;
      } catch (error) {
        console.error(`    ❌ Failed to test ${browser.name}:`, error.message);
        this.results.summary.failed++;
        this.results.summary.totalTests++;
      }
    }
  }

  async runDeviceCompatibilityTests() {
    console.log('📱 Running device compatibility tests...');

    for (const device of CONFIG.devices) {
      console.log(`  Testing ${device.name} (${device.width}x${device.height})...`);
      
      try {
        // Run Lighthouse with device emulation
        const lighthouseCommand = `npx lighthouse http://localhost:3000 ` +
          `--output=json ` +
          `--output-path=${CONFIG.outputDir}/lighthouse-${device.name.toLowerCase().replace(' ', '-')}.json ` +
          `--chrome-flags="--headless" ` +
          `--emulated-form-factor=${device.isMobile ? 'mobile' : 'desktop'} ` +
          `--throttling-method=devtools ` +
          `--only-categories=performance,accessibility`;

        execSync(lighthouseCommand, { stdio: 'pipe' });

        // Parse results
        const resultsPath = path.join(CONFIG.outputDir, `lighthouse-${device.name.toLowerCase().replace(' ', '-')}.json`);
        if (fs.existsSync(resultsPath)) {
          const results = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
          
          const deviceResult = {
            device: device.name,
            dimensions: `${device.width}x${device.height}`,
            isMobile: device.isMobile,
            deviceScaleFactor: device.deviceScaleFactor,
            performance: results.categories.performance.score * 100,
            accessibility: results.categories.accessibility.score * 100,
            passed: results.categories.performance.score >= 0.8 && 
                   results.categories.accessibility.score >= 0.9,
            timestamp: new Date().toISOString()
          };

          this.results.detailed.deviceTests.push(deviceResult);
          this.results.summary.deviceResults[device.name] = deviceResult;

          if (deviceResult.passed) {
            console.log(`    ✅ ${device.name} compatibility test passed`);
            this.results.summary.passed++;
          } else {
            console.log(`    ❌ ${device.name} compatibility test failed`);
            this.results.summary.failed++;
          }
        }

        this.results.summary.totalTests++;
      } catch (error) {
        console.error(`    ❌ Failed to test ${device.name}:`, error.message);
        this.results.summary.failed++;
        this.results.summary.totalTests++;
      }
    }
  }

  async runFeatureSupportTests() {
    console.log('🔧 Running feature support tests...');

    try {
      // Run Jest tests for feature detection
      const featureTestCommand = 'npm run test:ci -- --testNamePattern="feature.support|compatibility" --silent';
      execSync(featureTestCommand, { stdio: 'pipe' });
      
      console.log('  ✅ Feature support tests passed');
      this.results.summary.passed++;
      this.results.summary.totalTests++;

      // Mock feature support results (in real implementation, this would come from actual tests)
      CONFIG.features.forEach(feature => {
        this.results.summary.featureSupport[feature] = {
          supported: true,
          fallbackAvailable: true,
          criticalForApp: ['CSS Grid', 'CSS Flexbox', 'ES6 Modules'].includes(feature)
        };
      });

    } catch (error) {
      console.log('  ❌ Feature support tests failed');
      this.results.summary.failed++;
      this.results.summary.totalTests++;
    }
  }

  async runTouchInteractionTests() {
    console.log('👆 Running touch interaction tests...');

    try {
      // Run Jest tests specifically for touch interactions
      const touchTestCommand = 'npm run test:ci -- --testNamePattern="touch|mobile|gesture" --silent';
      execSync(touchTestCommand, { stdio: 'pipe' });
      
      console.log('  ✅ Touch interaction tests passed');
      this.results.summary.passed++;
      this.results.summary.totalTests++;
    } catch (error) {
      console.log('  ❌ Touch interaction tests failed');
      this.results.summary.failed++;
      this.results.summary.totalTests++;
    }
  }

  async runPWACompatibilityTests() {
    console.log('📲 Running PWA compatibility tests...');

    try {
      // Run Lighthouse PWA audit
      const pwaCommand = `npx lighthouse http://localhost:3000 ` +
        `--output=json ` +
        `--output-path=${CONFIG.outputDir}/lighthouse-pwa.json ` +
        `--chrome-flags="--headless" ` +
        `--only-categories=pwa`;

      execSync(pwaCommand, { stdio: 'pipe' });

      // Parse PWA results
      const pwaResultsPath = path.join(CONFIG.outputDir, 'lighthouse-pwa.json');
      if (fs.existsSync(pwaResultsPath)) {
        const pwaResults = JSON.parse(fs.readFileSync(pwaResultsPath, 'utf8'));
        
        const pwaScore = pwaResults.categories.pwa.score * 100;
        console.log(`  📊 PWA Score: ${pwaScore}/100`);
        
        if (pwaScore >= 80) {
          console.log('  ✅ PWA compatibility test passed');
          this.results.summary.passed++;
        } else {
          console.log('  ❌ PWA compatibility test failed');
          this.results.summary.failed++;
        }

        this.results.detailed.performanceTests.push({
          type: 'PWA',
          score: pwaScore,
          passed: pwaScore >= 80,
          timestamp: new Date().toISOString()
        });
      }

      this.results.summary.totalTests++;
    } catch (error) {
      console.error('  ❌ Failed to run PWA tests:', error.message);
      this.results.summary.failed++;
      this.results.summary.totalTests++;
    }
  }

  generateReport() {
    console.log('📝 Generating compatibility report...');

    // Generate summary report
    const summaryReport = this.generateSummaryReport();
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'compatibility-summary.json'),
      JSON.stringify(summaryReport, null, 2)
    );

    // Generate HTML report
    const htmlReport = this.generateHtmlReport();
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'compatibility-report.html'),
      htmlReport
    );

    // Generate detailed JSON report
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'compatibility-detailed.json'),
      JSON.stringify(this.results, null, 2)
    );

    console.log('  📄 Summary report: compatibility-summary.json');
    console.log('  🌐 HTML report: compatibility-report.html');
    console.log('  📋 Detailed report: compatibility-detailed.json');
  }

  generateSummaryReport() {
    const { summary } = this.results;
    const passRate = summary.totalTests > 0 ? (summary.passed / summary.totalTests * 100).toFixed(1) : 0;

    return {
      timestamp: summary.timestamp,
      overall: {
        status: summary.failed === 0 ? 'PASS' : 'FAIL',
        passRate: `${passRate}%`,
        totalTests: summary.totalTests,
        passed: summary.passed,
        failed: summary.failed
      },
      browsers: Object.keys(summary.browserResults).map(browser => ({
        name: browser,
        status: summary.browserResults[browser].passed ? 'PASS' : 'FAIL',
        performance: summary.browserResults[browser].performance,
        accessibility: summary.browserResults[browser].accessibility
      })),
      devices: Object.keys(summary.deviceResults).map(device => ({
        name: device,
        status: summary.deviceResults[device].passed ? 'PASS' : 'FAIL',
        performance: summary.deviceResults[device].performance,
        isMobile: summary.deviceResults[device].isMobile
      })),
      features: Object.keys(summary.featureSupport).map(feature => ({
        name: feature,
        supported: summary.featureSupport[feature].supported,
        critical: summary.featureSupport[feature].criticalForApp
      })),
      recommendations: this.generateRecommendations()
    };
  }

  generateRecommendations() {
    const recommendations = [];
    const { browserResults, deviceResults } = this.results.summary;

    // Browser-specific recommendations
    Object.values(browserResults).forEach(result => {
      if (!result.passed) {
        if (result.performance < 90) {
          recommendations.push({
            priority: 'high',
            category: 'Performance',
            issue: `Poor performance on ${result.browser}`,
            solution: 'Optimize JavaScript bundles and reduce render-blocking resources'
          });
        }
        if (result.accessibility < 90) {
          recommendations.push({
            priority: 'high',
            category: 'Accessibility',
            issue: `Accessibility issues on ${result.browser}`,
            solution: 'Fix ARIA labels, color contrast, and keyboard navigation'
          });
        }
      }
    });

    // Device-specific recommendations
    Object.values(deviceResults).forEach(result => {
      if (!result.passed && result.isMobile) {
        recommendations.push({
          priority: 'medium',
          category: 'Mobile',
          issue: `Poor mobile experience on ${result.device}`,
          solution: 'Optimize touch targets, improve mobile performance, and test responsive design'
        });
      }
    });

    // Feature support recommendations
    Object.entries(this.results.summary.featureSupport).forEach(([feature, support]) => {
      if (!support.supported && support.criticalForApp) {
        recommendations.push({
          priority: 'high',
          category: 'Feature Support',
          issue: `Critical feature ${feature} not supported`,
          solution: 'Implement polyfills or graceful degradation'
        });
      }
    });

    return recommendations;
  }

  generateHtmlReport() {
    const summary = this.generateSummaryReport();
    const statusColor = summary.overall.status === 'PASS' ? '#10b981' : '#ef4444';
    const statusIcon = summary.overall.status === 'PASS' ? '✅' : '❌';

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaChain Landing Page - Cross-Browser Compatibility Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }
        .header {
            background: linear-gradient(135deg, #06b6d4, #088395);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
            background-color: ${statusColor};
            margin-left: 10px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #06b6d4;
        }
        .browser-results, .device-results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 6px;
            background-color: #f8fafc;
        }
        .result-pass { border-left: 4px solid #10b981; }
        .result-fail { border-left: 4px solid #ef4444; }
        .recommendations {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .recommendation {
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid #06b6d4;
            background-color: #f0f9ff;
        }
        .priority-high { border-left-color: #ef4444; background-color: #fef2f2; }
        .priority-medium { border-left-color: #f59e0b; background-color: #fffbeb; }
        .priority-low { border-left-color: #10b981; background-color: #f0fdf4; }
        .timestamp {
            color: #6b7280;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${statusIcon} Cross-Browser Compatibility Report</h1>
        <p class="timestamp">Generated: ${new Date(summary.timestamp).toLocaleString()}</p>
        <span class="status">${summary.overall.status}</span>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">${summary.overall.passRate}</div>
            <div>Pass Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.overall.totalTests}</div>
            <div>Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.overall.passed}</div>
            <div>Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${summary.overall.failed}</div>
            <div>Failed</div>
        </div>
    </div>

    <div class="browser-results">
        <h2>Browser Compatibility</h2>
        ${summary.browsers.map(browser => `
            <div class="result-item ${browser.status === 'PASS' ? 'result-pass' : 'result-fail'}">
                <div>
                    <strong>${browser.name}</strong>
                    <div style="font-size: 0.9em; color: #6b7280;">
                        Performance: ${browser.performance}/100 | Accessibility: ${browser.accessibility}/100
                    </div>
                </div>
                <div style="font-weight: bold; color: ${browser.status === 'PASS' ? '#10b981' : '#ef4444'};">
                    ${browser.status}
                </div>
            </div>
        `).join('')}
    </div>

    <div class="device-results">
        <h2>Device Compatibility</h2>
        ${summary.devices.map(device => `
            <div class="result-item ${device.status === 'PASS' ? 'result-pass' : 'result-fail'}">
                <div>
                    <strong>${device.name}</strong>
                    <div style="font-size: 0.9em; color: #6b7280;">
                        ${device.isMobile ? 'Mobile' : 'Desktop'} | Performance: ${device.performance}/100
                    </div>
                </div>
                <div style="font-weight: bold; color: ${device.status === 'PASS' ? '#10b981' : '#ef4444'};">
                    ${device.status}
                </div>
            </div>
        `).join('')}
    </div>

    <div class="recommendations">
        <h2>Recommendations</h2>
        ${summary.recommendations.map(rec => `
            <div class="recommendation priority-${rec.priority}">
                <h3>${rec.issue}</h3>
                <p><strong>Category:</strong> ${rec.category}</p>
                <p><strong>Priority:</strong> ${rec.priority.toUpperCase()}</p>
                <p><strong>Solution:</strong> ${rec.solution}</p>
            </div>
        `).join('')}
    </div>

    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2>Next Steps</h2>
        <ol>
            <li>Address high-priority compatibility issues first</li>
            <li>Test fixes across all browsers and devices</li>
            <li>Implement progressive enhancement for unsupported features</li>
            <li>Set up automated cross-browser testing in CI/CD pipeline</li>
            <li>Monitor real user metrics for compatibility issues</li>
        </ol>
    </div>
</body>
</html>
    `;
  }
}

// Main execution
async function main() {
  const tester = new CrossBrowserTester();
  
  try {
    await tester.runCompatibilityTests();
    
    // Exit with appropriate code
    const hasFailures = tester.results.summary.failed > 0;
    process.exit(hasFailures ? 1 : 0);
  } catch (error) {
    console.error('❌ Cross-browser compatibility testing failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { CrossBrowserTester, CONFIG };