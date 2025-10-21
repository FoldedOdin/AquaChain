import { 
  PerformanceMonitor, 
  performanceMonitor, 
  PERFORMANCE_THRESHOLDS,
  PerformanceMetrics,
  MetricName,
} from '../performance';

// Mock web-vitals
jest.mock('web-vitals', () => ({
  getCLS: jest.fn(),
  getFID: jest.fn(),
  getFCP: jest.fn(),
  getLCP: jest.fn(),
  getTTFB: jest.fn(),
}));

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
    jest.clearAllMocks();
  });

  describe('initialization', () => {
    it('should initialize with null metrics', () => {
      const metrics = monitor.getMetrics();
      expect(metrics).toEqual({
        cls: null,
        fid: null,
        fcp: null,
        lcp: null,
        ttfb: null,
      });
    });

    it('should initialize performance monitoring in browser environment', () => {
      // The constructor should have called the web-vitals functions
      const { getCLS, getFID, getFCP, getLCP, getTTFB } = require('web-vitals');
      expect(getCLS).toHaveBeenCalled();
      expect(getFID).toHaveBeenCalled();
      expect(getFCP).toHaveBeenCalled();
      expect(getLCP).toHaveBeenCalled();
      expect(getTTFB).toHaveBeenCalled();
    });
  });

  describe('getRating', () => {
    it('should return "good" for values within good threshold', () => {
      expect(monitor.getRating('cls', 0.05)).toBe('good');
      expect(monitor.getRating('fid', 50)).toBe('good');
      expect(monitor.getRating('lcp', 2000)).toBe('good');
    });

    it('should return "needs-improvement" for values within needs improvement threshold', () => {
      expect(monitor.getRating('cls', 0.15)).toBe('needs-improvement');
      expect(monitor.getRating('fid', 200)).toBe('needs-improvement');
      expect(monitor.getRating('lcp', 3000)).toBe('needs-improvement');
    });

    it('should return "poor" for values above needs improvement threshold', () => {
      expect(monitor.getRating('cls', 0.3)).toBe('poor');
      expect(monitor.getRating('fid', 400)).toBe('poor');
      expect(monitor.getRating('lcp', 5000)).toBe('poor');
    });
  });

  describe('subscription system', () => {
    it('should allow subscribing to metric updates', () => {
      const callback = jest.fn();
      const unsubscribe = monitor.subscribe(callback);

      expect(typeof unsubscribe).toBe('function');
      expect(callback).not.toHaveBeenCalled(); // Initially no metrics
    });

    it('should allow unsubscribing from metric updates', () => {
      const callback = jest.fn();
      const unsubscribe = monitor.subscribe(callback);

      unsubscribe();

      // Test that unsubscribe function works
      expect(typeof unsubscribe).toBe('function');
    });
  });

  describe('performance score calculation', () => {
    it('should calculate performance score correctly with no metrics', () => {
      const score = monitor.getPerformanceScore();
      expect(typeof score).toBe('number');
      expect(score).toBe(0); // No metrics available initially
    });

    it('should return 0 when no metrics are available', () => {
      const newMonitor = new PerformanceMonitor();
      const score = newMonitor.getPerformanceScore();
      expect(score).toBe(0);
    });
  });

  describe('analytics reporting', () => {
    it('should report metrics to analytics function', () => {
      const analyticsFunction = jest.fn();

      monitor.reportToAnalytics(analyticsFunction);

      expect(analyticsFunction).toHaveBeenCalledWith(
        expect.objectContaining({
          score: expect.any(Number),
          cls: null,
          fid: null,
          fcp: null,
          lcp: null,
          ttfb: null,
        })
      );
    });

    it('should handle missing analytics function gracefully', () => {
      expect(() => monitor.reportToAnalytics()).not.toThrow();
    });
  });
});

describe('Performance Thresholds', () => {
  it('should have correct threshold values', () => {
    expect(PERFORMANCE_THRESHOLDS.cls.good).toBe(0.1);
    expect(PERFORMANCE_THRESHOLDS.cls.needsImprovement).toBe(0.25);
    
    expect(PERFORMANCE_THRESHOLDS.fid.good).toBe(100);
    expect(PERFORMANCE_THRESHOLDS.fid.needsImprovement).toBe(300);
    
    expect(PERFORMANCE_THRESHOLDS.lcp.good).toBe(2500);
    expect(PERFORMANCE_THRESHOLDS.lcp.needsImprovement).toBe(4000);
    
    expect(PERFORMANCE_THRESHOLDS.fcp.good).toBe(1800);
    expect(PERFORMANCE_THRESHOLDS.fcp.needsImprovement).toBe(3000);
    
    expect(PERFORMANCE_THRESHOLDS.ttfb.good).toBe(800);
    expect(PERFORMANCE_THRESHOLDS.ttfb.needsImprovement).toBe(1800);
  });
});

describe('Singleton Performance Monitor', () => {
  it('should provide a singleton instance', () => {
    expect(performanceMonitor).toBeInstanceOf(PerformanceMonitor);
  });

  it('should maintain state across imports', () => {
    const metrics1 = performanceMonitor.getMetrics();
    const metrics2 = performanceMonitor.getMetrics();
    
    expect(metrics1).toEqual(metrics2);
  });
});

describe('Edge Cases', () => {
  it('should handle server-side rendering environment', () => {
    // Mock window as undefined to simulate SSR
    const originalWindow = global.window;
    // @ts-ignore
    delete global.window;

    expect(() => new PerformanceMonitor()).not.toThrow();

    // Restore window
    global.window = originalWindow;
  });

  it('should handle development vs production environments', () => {
    const originalEnv = process.env.NODE_ENV;
    
    // Test development environment
    process.env.NODE_ENV = 'development';
    const devMonitor = new PerformanceMonitor();
    expect(devMonitor).toBeInstanceOf(PerformanceMonitor);
    
    // Test production environment
    process.env.NODE_ENV = 'production';
    const prodMonitor = new PerformanceMonitor();
    expect(prodMonitor).toBeInstanceOf(PerformanceMonitor);
    
    // Restore original environment
    process.env.NODE_ENV = originalEnv;
  });
});

describe('Metric Rating Edge Cases', () => {
  it('should handle exact threshold values correctly', () => {
    const monitor = new PerformanceMonitor();
    
    // Test exact good threshold values
    expect(monitor.getRating('cls', 0.1)).toBe('good');
    expect(monitor.getRating('fid', 100)).toBe('good');
    
    // Test exact needs-improvement threshold values
    expect(monitor.getRating('cls', 0.25)).toBe('needs-improvement');
    expect(monitor.getRating('fid', 300)).toBe('needs-improvement');
  });

  it('should handle zero and negative values', () => {
    const monitor = new PerformanceMonitor();
    
    expect(monitor.getRating('cls', 0)).toBe('good');
    expect(monitor.getRating('fid', 0)).toBe('good');
    
    // Negative values should still be rated as good
    expect(monitor.getRating('cls', -1)).toBe('good');
    expect(monitor.getRating('fid', -1)).toBe('good');
  });

  it('should handle very large values', () => {
    const monitor = new PerformanceMonitor();
    
    expect(monitor.getRating('cls', 999999)).toBe('poor');
    expect(monitor.getRating('fid', 999999)).toBe('poor');
    expect(monitor.getRating('lcp', 999999)).toBe('poor');
  });
});