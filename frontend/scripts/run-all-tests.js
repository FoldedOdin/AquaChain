#!/usr/bin/env node

/**
 * Master Test Execution Script
 * Runs all comprehensive tests and generates consolidated reports
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  outputDir: 'test-reports',
  testSuites: [
    {
      name: 'Unit Tests',
      command: 'npm run test:ci',
      required: true,
      timeout: 300000 // 5 minutes
    },
    {
      name: 'Accessibility Tests',
      command: 'node scripts/accessibility-audit.js',
      required: true,
      timeout: 600000 // 10 minutes
    },
    {
      name: 'Cross-Browser Tests',
      command: 'node scripts/cross-browser-testing.js',
      required: true,
      timeout: 900000 // 15 minutes
    },
    {
      name: 'Performance Tests',
      command: 'node scripts/performance-testing.js',
      required: true,
      timeout: 600000 // 10 minutes
    },
    {
      name: 'Security Tests',
      command: 'node scripts/security-testing.js',
      required: true,
      timeout: 300000 // 5 minutes
    }
  ]
};

class MasterTestRunner {
  constructor() {
    this.results = {
      summary: {
        totalSuites: CONFIG.testSuites.length,
        passed: 0,
        failed: 0,
        skipped: 0,
        startTime: new Date().toISOString(),
        endTime: null,
        duration: 0
      },
      suiteResults: [],
      consolidatedReport: {}
    };
  }

  async runAllTests() {
    console.log('🚀 Starting Comprehensive Test Suite...\n');
    console.log(`Running ${CONFIG.testSuites.length} test suites...\n`);

    const startTime = Date.now();

    // Ensure output directory exists
    this.ensureOutputDirectory();

    // Run each test suite
    for (const suite of CONFIG.testSuites) {
      await this.runTestSuite(suite);
    }

    // Calculate total duration
    const endTime = Date.now();
    this.results.summary.endTime = new Date().toISOString();
    this.results.summary.duration = endTime - startTime;

    // Generate consolidated reports
    await this.generateConsolidatedReports();

    // Display final summary
    this.displayFinalSummary();

    // Exit with appropriate code
    const hasFailures = this.results.summary.failed > 0;
    process.exit(hasFailures ? 1 : 0);
  }

  ensureOutputDirectory() {
    if (!fs.existsSync(CONFIG.outputDir)) {
      fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    }
  }

  async runTestSuite(suite) {
    console.log(`📋 Running ${suite.name}...`);
    
    const suiteResult = {
      name: suite.name,
      command: suite.command,
      required: suite.required,
      status: 'RUNNING',
      startTime: new Date().toISOString(),
      endTime: null,
      duration: 0,
      output: '',
      error: null
    };

    const startTime = Date.now();

    try {
      // Run the test suite with timeout
      const output = execSync(suite.command, {
        encoding: 'utf8',
        timeout: suite.timeout,
        stdio: 'pipe'
      });

      suiteResult.output = output;
      suiteResult.status = 'PASSED';
      this.results.summary.passed++;

      console.log(`  ✅ ${suite.name} passed`);
    } catch (error) {
      suiteResult.error = error.message;
      suiteResult.output = error.stdout || error.stderr || '';
      
      if (suite.required) {
        suiteResult.status = 'FAILED';
        this.results.summary.failed++;
        console.log(`  ❌ ${suite.name} failed`);
        console.log(`     Error: ${error.message}`);
      } else {
        suiteResult.status = 'SKIPPED';
        this.results.summary.skipped++;
        console.log(`  ⚠️  ${suite.name} skipped (optional)`);
      }
    }

    const endTime = Date.now();
    suiteResult.endTime = new Date().toISOString();
    suiteResult.duration = endTime - startTime;

    this.results.suiteResults.push(suiteResult);
    console.log(`     Duration: ${this.formatDuration(suiteResult.duration)}\n`);
  }

  async generateConsolidatedReports() {
    console.log('📊 Generating consolidated reports...');

    try {
      // Collect individual test reports
      const reports = await this.collectIndividualReports();
      
      // Generate consolidated summary
      const consolidatedSummary = this.generateConsolidatedSummary(reports);
      
      // Save consolidated report
      fs.writeFileSync(
        path.join(CONFIG.outputDir, 'consolidated-test-report.json'),
        JSON.stringify({
          summary: this.results.summary,
          suiteResults: this.results.suiteResults,
          consolidatedMetrics: consolidatedSummary,
          timestamp: new Date().toISOString()
        }, null, 2)
      );

      // Generate HTML dashboard
      const htmlDashboard = this.generateHtmlDashboard(consolidatedSummary);
      fs.writeFileSync(
        path.join(CONFIG.outputDir, 'test-dashboard.html'),
        htmlDashboard
      );

      console.log('  📄 Consolidated report: test-reports/consolidated-test-report.json');
      console.log('  🌐 Test dashboard: test-reports/test-dashboard.html');
    } catch (error) {
      console.error('  ❌ Failed to generate consolidated reports:', error.message);
    }
  }

  async collectIndividualReports() {
    const reports = {};

    // Collect accessibility report
    try {
      const accessibilityPath = path.join('accessibility-reports', 'accessibility-summary.json');
      if (fs.existsSync(accessibilityPath)) {
        reports.accessibility = JSON.parse(fs.readFileSync(accessibilityPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not load accessibility report:', error.message);
    }

    // Collect performance report
    try {
      const performancePath = path.join('performance-reports', 'performance-summary.json');
      if (fs.existsSync(performancePath)) {
        reports.performance = JSON.parse(fs.readFileSync(performancePath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not load performance report:', error.message);
    }

    // Collect security report
    try {
      const securityPath = path.join('security-reports', 'security-summary.json');
      if (fs.existsSync(securityPath)) {
        reports.security = JSON.parse(fs.readFileSync(securityPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not load security report:', error.message);
    }

    // Collect compatibility report
    try {
      const compatibilityPath = path.join('compatibility-reports', 'compatibility-summary.json');
      if (fs.existsSync(compatibilityPath)) {
        reports.compatibility = JSON.parse(fs.readFileSync(compatibilityPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not load compatibility report:', error.message);
    }

    return reports;
  }

  generateConsolidatedSummary(reports) {
    const summary = {
      overallStatus: this.results.summary.failed === 0 ? 'PASS' : 'FAIL',
      overallScore: 0,
      categories: {},
      recommendations: [],
      criticalIssues: []
    };

    let totalScore = 0;
    let scoreCount = 0;

    // Process accessibility results
    if (reports.accessibility) {
      const accessibilityScore = parseInt(reports.accessibility.overall.passRate) || 0;
      summary.categories.accessibility = {
        status: reports.accessibility.overall.status,
        score: accessibilityScore,
        violations: reports.accessibility.violations?.total || 0
      };
      totalScore += accessibilityScore;
      scoreCount++;

      if (reports.accessibility.violations?.critical > 0) {
        summary.criticalIssues.push(`${reports.accessibility.violations.critical} critical accessibility violations`);
      }
    }

    // Process performance results
    if (reports.performance) {
      const performanceScore = parseInt(reports.performance.overall.passRate) || 0;
      summary.categories.performance = {
        status: reports.performance.overall.status,
        score: performanceScore,
        coreWebVitals: reports.performance.coreWebVitals
      };
      totalScore += performanceScore;
      scoreCount++;
    }

    // Process security results
    if (reports.security) {
      const securityScore = parseInt(reports.security.overall.securityScore) || 0;
      summary.categories.security = {
        status: reports.security.overall.status,
        score: securityScore,
        vulnerabilities: reports.security.vulnerabilities
      };
      totalScore += securityScore;
      scoreCount++;

      if (reports.security.vulnerabilities?.critical > 0) {
        summary.criticalIssues.push(`${reports.security.vulnerabilities.critical} critical security vulnerabilities`);
      }
    }

    // Process compatibility results
    if (reports.compatibility) {
      const compatibilityScore = parseInt(reports.compatibility.overall.passRate) || 0;
      summary.categories.compatibility = {
        status: reports.compatibility.overall.status,
        score: compatibilityScore,
        browsers: reports.compatibility.browsers?.length || 0,
        devices: reports.compatibility.devices?.length || 0
      };
      totalScore += compatibilityScore;
      scoreCount++;
    }

    // Calculate overall score
    summary.overallScore = scoreCount > 0 ? Math.round(totalScore / scoreCount) : 0;

    // Collect all recommendations
    Object.values(reports).forEach(report => {
      if (report.recommendations) {
        summary.recommendations.push(...report.recommendations);
      }
    });

    // Sort recommendations by priority
    summary.recommendations.sort((a, b) => {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });

    return summary;
  }

  generateHtmlDashboard(consolidatedSummary) {
    const statusColor = consolidatedSummary.overallStatus === 'PASS' ? '#10b981' : '#ef4444';
    const statusIcon = consolidatedSummary.overallStatus === 'PASS' ? '✅' : '❌';
    const scoreColor = consolidatedSummary.overallScore >= 80 ? '#10b981' : 
                      consolidatedSummary.overallScore >= 60 ? '#f59e0b' : '#ef4444';

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaChain Landing Page - Test Dashboard</title>
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
        .overall-score {
            font-size: 4em;
            font-weight: bold;
            color: ${scoreColor};
            margin: 20px 0;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
            font-size: 2.5em;
            font-weight: bold;
            color: #06b6d4;
        }
        .category-results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .category-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .category-score {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .score-excellent { color: #10b981; }
        .score-good { color: #f59e0b; }
        .score-poor { color: #ef4444; }
        .suite-results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .suite-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            background-color: #f8fafc;
        }
        .suite-passed { border-left: 4px solid #10b981; }
        .suite-failed { border-left: 4px solid #ef4444; }
        .suite-skipped { border-left: 4px solid #f59e0b; }
        .critical-issues {
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
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
        .priority-critical { border-left-color: #dc2626; background-color: #fef2f2; }
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
        <h1>${statusIcon} AquaChain Landing Page Test Dashboard</h1>
        <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>
        <div class="overall-score">${consolidatedSummary.overallScore}/100</div>
        <p>Overall Quality Score</p>
        <span class="status">${consolidatedSummary.overallStatus}</span>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">${this.results.summary.totalSuites}</div>
            <div>Test Suites</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${this.results.summary.passed}</div>
            <div>Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${this.results.summary.failed}</div>
            <div>Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${this.formatDuration(this.results.summary.duration)}</div>
            <div>Total Duration</div>
        </div>
    </div>

    ${consolidatedSummary.criticalIssues.length > 0 ? `
    <div class="critical-issues">
        <h2>🚨 Critical Issues</h2>
        <ul>
            ${consolidatedSummary.criticalIssues.map(issue => `<li>${issue}</li>`).join('')}
        </ul>
    </div>
    ` : ''}

    <div class="category-results">
        ${Object.entries(consolidatedSummary.categories).map(([category, data]) => `
            <div class="category-card">
                <h3>${category.charAt(0).toUpperCase() + category.slice(1)}</h3>
                <div class="category-score ${this.getScoreClass(data.score)}">${data.score}/100</div>
                <div>Status: <strong>${data.status}</strong></div>
                ${data.violations !== undefined ? `<div>Violations: ${data.violations}</div>` : ''}
                ${data.vulnerabilities !== undefined ? `<div>Vulnerabilities: ${data.vulnerabilities.total || 0}</div>` : ''}
                ${data.browsers !== undefined ? `<div>Browsers Tested: ${data.browsers}</div>` : ''}
            </div>
        `).join('')}
    </div>

    <div class="suite-results">
        <h2>Test Suite Results</h2>
        ${this.results.suiteResults.map(suite => `
            <div class="suite-item suite-${suite.status.toLowerCase()}">
                <div>
                    <strong>${suite.name}</strong>
                    <div style="font-size: 0.9em; color: #6b7280;">
                        Duration: ${this.formatDuration(suite.duration)}
                        ${suite.required ? '' : ' (Optional)'}
                    </div>
                </div>
                <div style="font-weight: bold; color: ${suite.status === 'PASSED' ? '#10b981' : suite.status === 'FAILED' ? '#ef4444' : '#f59e0b'};">
                    ${suite.status}
                </div>
            </div>
        `).join('')}
    </div>

    <div class="recommendations">
        <h2>Top Recommendations</h2>
        ${consolidatedSummary.recommendations.slice(0, 10).map(rec => `
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
            <li>Address critical issues immediately</li>
            <li>Review failed test suites and fix underlying issues</li>
            <li>Implement high-priority recommendations</li>
            <li>Set up continuous monitoring for quality metrics</li>
            <li>Schedule regular comprehensive test runs</li>
        </ol>
        
        <h3>Individual Reports</h3>
        <ul>
            <li><a href="accessibility-reports/accessibility-report.html">Accessibility Report</a></li>
            <li><a href="performance-reports/performance-report.html">Performance Report</a></li>
            <li><a href="security-reports/security-report.html">Security Report</a></li>
            <li><a href="compatibility-reports/compatibility-report.html">Compatibility Report</a></li>
        </ul>
    </div>
</body>
</html>
    `;
  }

  getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    return 'score-poor';
  }

  displayFinalSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 COMPREHENSIVE TEST SUMMARY');
    console.log('='.repeat(60));
    
    console.log(`\n🎯 Overall Status: ${this.results.summary.failed === 0 ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`⏱️  Total Duration: ${this.formatDuration(this.results.summary.duration)}`);
    console.log(`📋 Test Suites: ${this.results.summary.totalSuites}`);
    console.log(`✅ Passed: ${this.results.summary.passed}`);
    console.log(`❌ Failed: ${this.results.summary.failed}`);
    console.log(`⚠️  Skipped: ${this.results.summary.skipped}`);

    console.log('\n📈 Test Suite Details:');
    this.results.suiteResults.forEach(suite => {
      const statusIcon = suite.status === 'PASSED' ? '✅' : suite.status === 'FAILED' ? '❌' : '⚠️';
      console.log(`  ${statusIcon} ${suite.name}: ${suite.status} (${this.formatDuration(suite.duration)})`);
    });

    console.log('\n📄 Reports Generated:');
    console.log(`  📊 Test Dashboard: ${CONFIG.outputDir}/test-dashboard.html`);
    console.log(`  📋 Consolidated Report: ${CONFIG.outputDir}/consolidated-test-report.json`);
    
    if (this.results.summary.failed > 0) {
      console.log('\n⚠️  Some tests failed. Please review the reports and fix the issues.');
    } else {
      console.log('\n🎉 All tests passed! The AquaChain Landing Page meets quality standards.');
    }
    
    console.log('\n' + '='.repeat(60));
  }

  formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  }
}

// Main execution
async function main() {
  const runner = new MasterTestRunner();
  
  try {
    await runner.runAllTests();
  } catch (error) {
    console.error('❌ Master test runner failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { MasterTestRunner, CONFIG };