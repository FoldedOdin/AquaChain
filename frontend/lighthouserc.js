/**
 * Lighthouse CI Configuration
 * Defines performance budgets and CI/CD integration
 */

module.exports = {
  ci: {
    collect: {
      // URLs to test
      url: [
        'http://localhost:3000',
        'http://localhost:3000/#features',
        'http://localhost:3000/#roles',
        'http://localhost:3000/#contact'
      ],
      // Number of runs per URL
      numberOfRuns: 3,
      // Chrome flags for consistent testing
      settings: {
        chromeFlags: '--no-sandbox --disable-dev-shm-usage --disable-gpu --headless',
        // Emulate mobile device
        emulatedFormFactor: 'mobile',
        // Throttling settings
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0
        }
      }
    },
    assert: {
      // Performance budgets
      assertions: {
        // Core Web Vitals thresholds
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        
        // Specific metrics
        'metrics:largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'metrics:first-input-delay': ['error', { maxNumericValue: 100 }],
        'metrics:cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'metrics:first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'metrics:speed-index': ['error', { maxNumericValue: 3000 }],
        'metrics:time-to-interactive': ['error', { maxNumericValue: 3800 }],
        'metrics:total-blocking-time': ['error', { maxNumericValue: 300 }],
        
        // Resource budgets
        'resource-summary:script:size': ['error', { maxNumericValue: 512000 }], // 512KB
        'resource-summary:stylesheet:size': ['error', { maxNumericValue: 102400 }], // 100KB
        'resource-summary:image:size': ['error', { maxNumericValue: 1048576 }], // 1MB
        'resource-summary:font:size': ['error', { maxNumericValue: 204800 }], // 200KB
        'resource-summary:total:size': ['error', { maxNumericValue: 2097152 }], // 2MB
        
        // Network requests
        'resource-summary:total:count': ['error', { maxNumericValue: 50 }],
        'resource-summary:third-party:count': ['error', { maxNumericValue: 10 }],
        
        // Specific audits
        'unused-css-rules': ['error', { maxNumericValue: 20000 }],
        'unused-javascript': ['error', { maxNumericValue: 40000 }],
        'modern-image-formats': 'error',
        'offscreen-images': 'error',
        'render-blocking-resources': 'error',
        'unminified-css': 'error',
        'unminified-javascript': 'error',
        'efficient-animated-content': 'error',
        'duplicated-javascript': 'error',
        'legacy-javascript': 'error'
      }
    },
    upload: {
      // Upload results to Lighthouse CI server (if configured)
      target: 'temporary-public-storage'
    },
    server: {
      // Local server configuration for testing
      port: 9001,
      storage: {
        storageMethod: 'sql',
        sqlDialect: 'sqlite',
        sqlDatabasePath: './lhci.db'
      }
    }
  }
};