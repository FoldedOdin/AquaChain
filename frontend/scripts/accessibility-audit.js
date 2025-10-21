#!/usr/bin/env node

/**
 * Comprehensive Accessibility Audit Script
 * Runs automated accessibility tests using axe-core and generates detailed reports
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  buildDir: 'build',
  outputDir: 'accessibility-reports',
  testUrls: [
    'http://localhost:3000',
    'http://localhost:3000/#auth-modal',
    'http://localhost:3000/#features',
    'http://localhost:3000/#roles',
    'http://localhost:3000/#contact'
  ],
  axeConfig: {
    rules: {
      'color-contrast': { enabled: true },
      'focus-order-semantics': { enabled: true },
      'aria-allowed-attr': { enabled: true },
      'aria-required-attr': { enabled: true },
      'heading-order': { enabled: true },
      'landmark-one-main': { enabled: true },
      'image-alt': { enabled: true },
      'label': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'bypass': { enabled: true },
      'page-has-heading-one': { enabled: true },
      'region': { enabled: true }
    },
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice']
  }
};

class AccessibilityAuditor {
  constructor() {
    this.results = {
      summary: {
        totalTests: 0,
        passed: 0,
        failed: 0,
        violations: [],
        timestamp: new Date().toISOString()
      },
      detailed: {}
    };
  }

  async runAudit() {
    console.log('🔍 Starting Accessibility Audit...\n');

    // Ensure output directory exists
    this.ensureOutputDirectory();

    // Run different types of accessibility tests
    await this.runAxeCoreTests();
    await this.runLighthouseA11yTests();
    await this.runKeyboardNavigationTests();
    await this.runScreenReaderTests();

    // Generate comprehensive report
    this.generateReport();

    console.log('\n✅ Accessibility audit completed!');
    console.log(`📊 Results saved to: ${CONFIG.outputDir}/`);
  }

  ensureOutputDirectory() {
    if (!fs.existsSync(CONFIG.outputDir)) {
      fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    }
  }

  async runAxeCoreTests() {
    console.log('🔧 Running axe-core accessibility tests...');

    try {
      // Build the application first
      console.log('  Building application...');
      execSync('npm run build', { stdio: 'inherit' });

      // Run axe-core CLI tests
      console.log('  Running axe-core CLI...');
      const axeCommand = `npx @axe-core/cli ${CONFIG.buildDir} --save ${CONFIG.outputDir}/axe-results.json --reporter json`;
      
      try {
        execSync(axeCommand, { stdio: 'pipe' });
        console.log('  ✅ axe-core tests passed');
        this.results.summary.passed++;
      } catch (error) {
        console.log('  ❌ axe-core tests found violations');
        this.results.summary.failed++;
        
        // Parse axe results if available
        const axeResultsPath = path.join(CONFIG.outputDir, 'axe-results.json');
        if (fs.existsSync(axeResultsPath)) {
          const axeResults = JSON.parse(fs.readFileSync(axeResultsPath, 'utf8'));
          this.results.detailed.axeCore = axeResults;
          
          if (axeResults.violations) {
            this.results.summary.violations.push(...axeResults.violations);
          }
        }
      }

      this.results.summary.totalTests++;
    } catch (error) {
      console.error('  ❌ Failed to run axe-core tests:', error.message);
      this.results.summary.failed++;
    }
  }

  async runLighthouseA11yTests() {
    console.log('🚨 Running Lighthouse accessibility tests...');

    try {
      // Run Lighthouse with accessibility focus
      const lighthouseCommand = `npx lighthouse http://localhost:3000 --only-categories=accessibility --output=json --output-path=${CONFIG.outputDir}/lighthouse-a11y.json --chrome-flags="--headless"`;
      
      execSync(lighthouseCommand, { stdio: 'pipe' });
      
      // Parse Lighthouse results
      const lighthouseResultsPath = path.join(CONFIG.outputDir, 'lighthouse-a11y.json');
      if (fs.existsSync(lighthouseResultsPath)) {
        const lighthouseResults = JSON.parse(fs.readFileSync(lighthouseResultsPath, 'utf8'));
        this.results.detailed.lighthouse = lighthouseResults;
        
        const a11yScore = lighthouseResults.categories.accessibility.score * 100;
        console.log(`  📊 Accessibility Score: ${a11yScore}/100`);
        
        if (a11yScore >= 90) {
          console.log('  ✅ Lighthouse accessibility tests passed');
          this.results.summary.passed++;
        } else {
          console.log('  ❌ Lighthouse accessibility score below threshold');
          this.results.summary.failed++;
        }
      }

      this.results.summary.totalTests++;
    } catch (error) {
      console.error('  ❌ Failed to run Lighthouse tests:', error.message);
      this.results.summary.failed++;
    }
  }

  async runKeyboardNavigationTests() {
    console.log('⌨️  Running keyboard navigation tests...');

    try {
      // Run Jest tests specifically for keyboard navigation
      const keyboardTestCommand = 'npm run test:ci -- --testNamePattern="keyboard|navigation|focus" --silent';
      execSync(keyboardTestCommand, { stdio: 'pipe' });
      
      console.log('  ✅ Keyboard navigation tests passed');
      this.results.summary.passed++;
      this.results.summary.totalTests++;
    } catch (error) {
      console.log('  ❌ Keyboard navigation tests failed');
      this.results.summary.failed++;
      this.results.summary.totalTests++;
    }
  }

  async runScreenReaderTests() {
    console.log('🔊 Running screen reader compatibility tests...');

    try {
      // Run Jest tests specifically for screen reader compatibility
      const screenReaderTestCommand = 'npm run test:ci -- --testNamePattern="screen.reader|aria|semantic" --silent';
      execSync(screenReaderTestCommand, { stdio: 'pipe' });
      
      console.log('  ✅ Screen reader tests passed');
      this.results.summary.passed++;
      this.results.summary.totalTests++;
    } catch (error) {
      console.log('  ❌ Screen reader tests failed');
      this.results.summary.failed++;
      this.results.summary.totalTests++;
    }
  }

  generateReport() {
    console.log('📝 Generating accessibility report...');

    // Generate summary report
    const summaryReport = this.generateSummaryReport();
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'accessibility-summary.json'),
      JSON.stringify(summaryReport, null, 2)
    );

    // Generate HTML report
    const htmlReport = this.generateHtmlReport();
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'accessibility-report.html'),
      htmlReport
    );

    // Generate detailed JSON report
    fs.writeFileSync(
      path.join(CONFIG.outputDir, 'accessibility-detailed.json'),
      JSON.stringify(this.results, null, 2)
    );

    console.log('  📄 Summary report: accessibility-summary.json');
    console.log('  🌐 HTML report: accessibility-report.html');
    console.log('  📋 Detailed report: accessibility-detailed.json');
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
      violations: {
        total: summary.violations.length,
        critical: summary.violations.filter(v => v.impact === 'critical').length,
        serious: summary.violations.filter(v => v.impact === 'serious').length,
        moderate: summary.violations.filter(v => v.impact === 'moderate').length,
        minor: summary.violations.filter(v => v.impact === 'minor').length
      },
      recommendations: this.generateRecommendations()
    };
  }

  generateRecommendations() {
    const recommendations = [];
    const { violations } = this.results.summary;

    // Analyze violations and generate recommendations
    const violationTypes = violations.reduce((acc, violation) => {
      acc[violation.id] = (acc[violation.id] || 0) + 1;
      return acc;
    }, {});

    Object.entries(violationTypes).forEach(([ruleId, count]) => {
      switch (ruleId) {
        case 'color-contrast':
          recommendations.push({
            priority: 'high',
            issue: 'Color contrast violations',
            count,
            solution: 'Ensure text has sufficient contrast ratio (4.5:1 for normal text, 3:1 for large text)'
          });
          break;
        case 'keyboard-navigation':
          recommendations.push({
            priority: 'high',
            issue: 'Keyboard navigation issues',
            count,
            solution: 'Ensure all interactive elements are keyboard accessible with proper focus indicators'
          });
          break;
        case 'aria-required-attr':
          recommendations.push({
            priority: 'medium',
            issue: 'Missing required ARIA attributes',
            count,
            solution: 'Add required ARIA attributes to interactive elements'
          });
          break;
        case 'image-alt':
          recommendations.push({
            priority: 'medium',
            issue: 'Missing alt text for images',
            count,
            solution: 'Add descriptive alt text to all images'
          });
          break;
        default:
          recommendations.push({
            priority: 'low',
            issue: `${ruleId} violations`,
            count,
            solution: 'Review and fix accessibility violations'
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
    <title>AquaChain Landing Page - Accessibility Report</title>
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
        .violations {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .violation-item {
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #ef4444;
            background-color: #fef2f2;
        }
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
        <h1>${statusIcon} AquaChain Landing Page - Accessibility Report</h1>
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

    <div class="violations">
        <h2>Violations Summary</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" style="color: #dc2626;">${summary.violations.critical}</div>
                <div>Critical</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #ea580c;">${summary.violations.serious}</div>
                <div>Serious</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #d97706;">${summary.violations.moderate}</div>
                <div>Moderate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #65a30d;">${summary.violations.minor}</div>
                <div>Minor</div>
            </div>
        </div>
    </div>

    <div class="recommendations">
        <h2>Recommendations</h2>
        ${summary.recommendations.map(rec => `
            <div class="recommendation priority-${rec.priority}">
                <h3>${rec.issue} (${rec.count} occurrences)</h3>
                <p><strong>Priority:</strong> ${rec.priority.toUpperCase()}</p>
                <p><strong>Solution:</strong> ${rec.solution}</p>
            </div>
        `).join('')}
    </div>

    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2>Next Steps</h2>
        <ol>
            <li>Review detailed violation reports in the JSON files</li>
            <li>Fix critical and serious violations first</li>
            <li>Test fixes with screen readers and keyboard navigation</li>
            <li>Re-run accessibility audit to verify improvements</li>
            <li>Consider manual testing with users who have disabilities</li>
        </ol>
    </div>
</body>
</html>
    `;
  }
}

// Main execution
async function main() {
  const auditor = new AccessibilityAuditor();
  
  try {
    await auditor.runAudit();
    
    // Exit with appropriate code
    const hasFailures = auditor.results.summary.failed > 0;
    process.exit(hasFailures ? 1 : 0);
  } catch (error) {
    console.error('❌ Accessibility audit failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { AccessibilityAuditor, CONFIG };