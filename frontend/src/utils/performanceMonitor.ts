/**
 * Performance Monitor for AquaChain Landing Page
 * Implements performance budget monitoring and Core Web Vitals tracking
 */

// Performance budget interface from design specification
export interface PerformanceBudget {
  // Largest Contentful Paint
  LCP: {
    good: number;        // < 2.5s
    needsImprovement: number; // 2.5s - 4s
    poor: number;        // > 4s
  };
  
  // First Input Delay
  FID: {
    good: number;        // < 100ms
    needsImprovement: number; // 100ms - 300ms
    poor: number;        // > 300ms
  };
  
  // Cumulative Layout Shift
  CLS: {
    good: number;        // < 0.1
    needsImprovement: number; // 0.1 - 0.25
    poor: number;        // > 0.25
  };
  
  // Custom Metrics
  timeToInteractive: number;    // < 3s
  firstContentfulPaint: number; // < 1.5s
  totalBlockingTime: number;    // < 200ms
}

export interface PerformanceMetrics {
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  animationFrameRate: number;
  memoryUsage: number;
  timeToInteractive?: number;
  totalBlockingTime?: number;
}

export interface PerformanceReport {
  metrics: PerformanceMetrics;
  violations: PerformanceViolation[];
  score: number;
}

export interface PerformanceViolation {
  metric: string;
  value: number;
  threshold: number;
  severity: 'good' | 'needs-improvement' | 'poor';
  recommendation: string;
}

// Default performance budget based on design specification
const DEFAULT_PERFORMANCE_BUDGET: PerformanceBudget = {
  LCP: {
    good: 2500,
    needsImprovement: 4000,
    poor: Infinity
  },
  FID: {
    good: 100,
    needsImprovement: 300,
    poor: Infinity
  },
  CLS: {
    good: 0.1,
    needsImprovement: 0.25,
    poor: Infinity
  },
  timeToInteractive: 3000,
  firstContentfulPaint: 1500,
  totalBlockingTime: 200
};

export class PerformanceMonitor {
  private budget: PerformanceBudget;
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];
  private animationFrameTimes: number[] = [];
  private isMonitoring = false;

  constructor(budget: PerformanceBudget = DEFAULT_PERFORMANCE_BUDGET) {
    this.budget = budget;
    this.setupPerformanceObservers();
  }

  public start(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.collectInitialMetrics();
    this.startObservers();
  }

  public stop(): void {
    this.isMonitoring = false;
    this.stopObservers();
  }

  public checkBudget(): PerformanceReport {
    const metrics = this.collectMetrics();
    const violations = this.findViolations(metrics);
    const score = this.calculateScore(metrics);

    if (violations.length > 0) {
      this.alertDevelopers(violations);
    }

    return {
      metrics,
      violations,
      score
    };
  }

  public recordAnimationFrame(frameTime: number): void {
    this.animationFrameTimes.push(frameTime);
    
    // Keep only last 60 frames for FPS calculation
    if (this.animationFrameTimes.length > 60) {
      this.animationFrameTimes.shift();
    }

    // Calculate current FPS
    const avgFrameTime = this.animationFrameTimes.reduce((a, b) => a + b, 0) / this.animationFrameTimes.length;
    this.metrics.animationFrameRate = 1000 / avgFrameTime;
  }

  private setupPerformanceObservers(): void {
    // Largest Contentful Paint Observer
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as PerformanceEntry & { startTime: number };
        this.metrics.largestContentfulPaint = lastEntry.startTime;
      });

      // First Contentful Paint Observer
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.firstContentfulPaint = entry.startTime;
          }
        });
      });

      // Cumulative Layout Shift Observer
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.metrics.cumulativeLayoutShift = clsValue;
      });

      // First Input Delay Observer
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
        });
      });

      this.observers = [lcpObserver, fcpObserver, clsObserver, fidObserver];
    }
  }

  private startObservers(): void {
    if (!('PerformanceObserver' in window)) return;

    try {
      this.observers[0]?.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers[1]?.observe({ entryTypes: ['paint'] });
      this.observers[2]?.observe({ entryTypes: ['layout-shift'] });
      this.observers[3]?.observe({ entryTypes: ['first-input'] });
    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }
  }

  private stopObservers(): void {
    this.observers.forEach(observer => {
      try {
        observer.disconnect();
      } catch (error) {
        console.warn('Error disconnecting performance observer:', error);
      }
    });
  }

  private collectInitialMetrics(): void {
    // Navigation timing
    if ('performance' in window && window.performance.timing) {
      const timing = window.performance.timing;
      this.metrics.pageLoadTime = timing.loadEventEnd - timing.navigationStart;
    }

    // Memory usage (if available)
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.metrics.memoryUsage = memory.usedJSHeapSize;
    }
  }

  private collectMetrics(): PerformanceMetrics {
    return {
      pageLoadTime: this.metrics.pageLoadTime || 0,
      firstContentfulPaint: this.metrics.firstContentfulPaint || 0,
      largestContentfulPaint: this.metrics.largestContentfulPaint || 0,
      cumulativeLayoutShift: this.metrics.cumulativeLayoutShift || 0,
      firstInputDelay: this.metrics.firstInputDelay || 0,
      animationFrameRate: this.metrics.animationFrameRate || 60,
      memoryUsage: this.metrics.memoryUsage || 0,
      timeToInteractive: this.metrics.timeToInteractive,
      totalBlockingTime: this.metrics.totalBlockingTime
    };
  }

  private findViolations(metrics: PerformanceMetrics): PerformanceViolation[] {
    const violations: PerformanceViolation[] = [];

    // Check LCP
    if (metrics.largestContentfulPaint > this.budget.LCP.poor) {
      violations.push({
        metric: 'Largest Contentful Paint',
        value: metrics.largestContentfulPaint,
        threshold: this.budget.LCP.good,
        severity: 'poor',
        recommendation: 'Optimize images, reduce server response time, eliminate render-blocking resources'
      });
    } else if (metrics.largestContentfulPaint > this.budget.LCP.needsImprovement) {
      violations.push({
        metric: 'Largest Contentful Paint',
        value: metrics.largestContentfulPaint,
        threshold: this.budget.LCP.good,
        severity: 'needs-improvement',
        recommendation: 'Consider optimizing critical rendering path and resource loading'
      });
    }

    // Check FID
    if (metrics.firstInputDelay > this.budget.FID.poor) {
      violations.push({
        metric: 'First Input Delay',
        value: metrics.firstInputDelay,
        threshold: this.budget.FID.good,
        severity: 'poor',
        recommendation: 'Reduce JavaScript execution time, split long tasks, use web workers'
      });
    } else if (metrics.firstInputDelay > this.budget.FID.needsImprovement) {
      violations.push({
        metric: 'First Input Delay',
        value: metrics.firstInputDelay,
        threshold: this.budget.FID.good,
        severity: 'needs-improvement',
        recommendation: 'Optimize JavaScript execution and reduce main thread blocking'
      });
    }

    // Check CLS
    if (metrics.cumulativeLayoutShift > this.budget.CLS.poor) {
      violations.push({
        metric: 'Cumulative Layout Shift',
        value: metrics.cumulativeLayoutShift,
        threshold: this.budget.CLS.good,
        severity: 'poor',
        recommendation: 'Set size attributes on images and videos, avoid inserting content above existing content'
      });
    } else if (metrics.cumulativeLayoutShift > this.budget.CLS.needsImprovement) {
      violations.push({
        metric: 'Cumulative Layout Shift',
        value: metrics.cumulativeLayoutShift,
        threshold: this.budget.CLS.good,
        severity: 'needs-improvement',
        recommendation: 'Reserve space for dynamic content and optimize font loading'
      });
    }

    // Check FCP
    if (metrics.firstContentfulPaint > this.budget.firstContentfulPaint) {
      violations.push({
        metric: 'First Contentful Paint',
        value: metrics.firstContentfulPaint,
        threshold: this.budget.firstContentfulPaint,
        severity: 'needs-improvement',
        recommendation: 'Optimize critical rendering path and reduce server response time'
      });
    }

    // Check animation frame rate
    if (metrics.animationFrameRate < 30) {
      violations.push({
        metric: 'Animation Frame Rate',
        value: metrics.animationFrameRate,
        threshold: 60,
        severity: 'poor',
        recommendation: 'Optimize animations, reduce animation complexity, use CSS transforms'
      });
    } else if (metrics.animationFrameRate < 50) {
      violations.push({
        metric: 'Animation Frame Rate',
        value: metrics.animationFrameRate,
        threshold: 60,
        severity: 'needs-improvement',
        recommendation: 'Consider reducing animation complexity for better performance'
      });
    }

    return violations;
  }

  private calculateScore(metrics: PerformanceMetrics): number {
    let score = 100;

    // Deduct points for each violation
    if (metrics.largestContentfulPaint > this.budget.LCP.good) {
      score -= 20;
    }
    if (metrics.firstInputDelay > this.budget.FID.good) {
      score -= 20;
    }
    if (metrics.cumulativeLayoutShift > this.budget.CLS.good) {
      score -= 20;
    }
    if (metrics.firstContentfulPaint > this.budget.firstContentfulPaint) {
      score -= 15;
    }
    if (metrics.animationFrameRate < 50) {
      score -= 15;
    }

    return Math.max(0, score);
  }

  private alertDevelopers(violations: PerformanceViolation[]): void {
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Performance Budget Violations');
      violations.forEach(violation => {
        console.warn(
          `${violation.metric}: ${violation.value.toFixed(2)}ms (threshold: ${violation.threshold}ms)`,
          `\nRecommendation: ${violation.recommendation}`
        );
      });
      console.groupEnd();
    }

    // In production, send to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Send violations to analytics/monitoring service
      violations.forEach(violation => {
        // This would integrate with your monitoring service
        console.info('Performance violation logged:', violation);
      });
    }
  }

  public getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  public updateBudget(newBudget: Partial<PerformanceBudget>): void {
    this.budget = { ...this.budget, ...newBudget };
  }
}

export default PerformanceMonitor;