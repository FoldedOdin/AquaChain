/**
 * Performance Monitoring Service
 * Tracks Core Web Vitals and page load performance
 */

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

interface WebVitalsThresholds {
  good: number;
  needsImprovement: number;
}

// Core Web Vitals thresholds (in milliseconds or score)
const THRESHOLDS: Record<string, WebVitalsThresholds> = {
  FCP: { good: 1800, needsImprovement: 3000 },      // First Contentful Paint
  LCP: { good: 2500, needsImprovement: 4000 },      // Largest Contentful Paint
  FID: { good: 100, needsImprovement: 300 },        // First Input Delay
  CLS: { good: 0.1, needsImprovement: 0.25 },       // Cumulative Layout Shift
  TTFB: { good: 800, needsImprovement: 1800 },      // Time to First Byte
  INP: { good: 200, needsImprovement: 500 },        // Interaction to Next Paint
};

const PAGE_LOAD_THRESHOLD = 3000; // 3 seconds

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeMonitoring();
  }

  /**
   * Initialize performance monitoring
   */
  private initializeMonitoring(): void {
    if (typeof window === 'undefined') return;

    // Monitor page load time
    this.monitorPageLoad();

    // Monitor Core Web Vitals
    this.monitorWebVitals();

    // Monitor long tasks
    this.monitorLongTasks();
  }

  /**
   * Monitor page load performance
   */
  private monitorPageLoad(): void {
    if (window.performance && window.performance.timing) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const timing = window.performance.timing;
          const loadTime = timing.loadEventEnd - timing.navigationStart;

          if (loadTime > PAGE_LOAD_THRESHOLD) {
            console.warn(
              `⚠️ Page load time exceeded threshold: ${loadTime}ms (threshold: ${PAGE_LOAD_THRESHOLD}ms)`
            );
          }

          this.recordMetric({
            name: 'page-load',
            value: loadTime,
            rating: this.getRating(loadTime, { good: 2000, needsImprovement: 3000 }),
            timestamp: Date.now(),
          });
        }, 0);
      });
    }
  }

  /**
   * Monitor Core Web Vitals using PerformanceObserver
   */
  private monitorWebVitals(): void {
    // Largest Contentful Paint (LCP)
    this.observeMetric('largest-contentful-paint', (entry: any) => {
      const value = entry.renderTime || entry.loadTime;
      this.recordMetric({
        name: 'LCP',
        value,
        rating: this.getRating(value, THRESHOLDS.LCP),
        timestamp: Date.now(),
      });
    });

    // First Input Delay (FID)
    this.observeMetric('first-input', (entry: any) => {
      const value = entry.processingStart - entry.startTime;
      this.recordMetric({
        name: 'FID',
        value,
        rating: this.getRating(value, THRESHOLDS.FID),
        timestamp: Date.now(),
      });
    });

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    this.observeMetric('layout-shift', (entry: any) => {
      if (!entry.hadRecentInput) {
        clsValue += entry.value;
        this.recordMetric({
          name: 'CLS',
          value: clsValue,
          rating: this.getRating(clsValue, THRESHOLDS.CLS),
          timestamp: Date.now(),
        });
      }
    });

    // First Contentful Paint (FCP)
    this.observeMetric('paint', (entry: any) => {
      if (entry.name === 'first-contentful-paint') {
        this.recordMetric({
          name: 'FCP',
          value: entry.startTime,
          rating: this.getRating(entry.startTime, THRESHOLDS.FCP),
          timestamp: Date.now(),
        });
      }
    });

    // Navigation Timing (TTFB)
    if (window.performance && window.performance.getEntriesByType) {
      const navEntries = window.performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
      if (navEntries.length > 0) {
        const ttfb = navEntries[0].responseStart - navEntries[0].requestStart;
        this.recordMetric({
          name: 'TTFB',
          value: ttfb,
          rating: this.getRating(ttfb, THRESHOLDS.TTFB),
          timestamp: Date.now(),
        });
      }
    }
  }

  /**
   * Monitor long tasks that block the main thread
   */
  private monitorLongTasks(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              console.warn(
                `⚠️ Long task detected: ${entry.duration.toFixed(2)}ms`,
                entry
              );
            }
          }
        });

        observer.observe({ entryTypes: ['longtask'] });
        this.observers.push(observer);
      } catch (e) {
        // longtask observer not supported
      }
    }
  }

  /**
   * Observe a specific performance metric
   */
  private observeMetric(
    entryType: string,
    callback: (entry: PerformanceEntry) => void
  ): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            callback(entry);
          }
        });

        observer.observe({ entryTypes: [entryType], buffered: true });
        this.observers.push(observer);
      } catch (e) {
        // Observer not supported
      }
    }
  }

  /**
   * Record a performance metric
   */
  private recordMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);

    // Log poor performance
    if (metric.rating === 'poor') {
      console.warn(
        `⚠️ Poor ${metric.name} performance: ${metric.value.toFixed(2)}ms`,
        metric
      );
    }

    // Send to analytics (if configured)
    this.sendToAnalytics(metric);
  }

  /**
   * Get performance rating based on thresholds
   */
  private getRating(
    value: number,
    thresholds: WebVitalsThresholds
  ): 'good' | 'needs-improvement' | 'poor' {
    if (value <= thresholds.good) return 'good';
    if (value <= thresholds.needsImprovement) return 'needs-improvement';
    return 'poor';
  }

  /**
   * Send metric to analytics service
   */
  private sendToAnalytics(metric: PerformanceMetric): void {
    // Send to Google Analytics, CloudWatch, or custom analytics service
    if (window.gtag) {
      window.gtag('event', 'web_vitals', {
        event_category: 'Performance',
        event_label: metric.name,
        value: Math.round(metric.value),
        metric_rating: metric.rating,
        non_interaction: true,
      });
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`📊 ${metric.name}:`, {
        value: `${metric.value.toFixed(2)}ms`,
        rating: metric.rating,
      });
    }
  }

  /**
   * Get all recorded metrics
   */
  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Get metrics by name
   */
  public getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter((m) => m.name === name);
  }

  /**
   * Get latest metric by name
   */
  public getLatestMetric(name: string): PerformanceMetric | undefined {
    const metrics = this.getMetricsByName(name);
    return metrics[metrics.length - 1];
  }

  /**
   * Clear all metrics
   */
  public clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Disconnect all observers
   */
  public disconnect(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
  }

  /**
   * Measure custom performance mark
   */
  public mark(name: string): void {
    if (window.performance && window.performance.mark) {
      window.performance.mark(name);
    }
  }

  /**
   * Measure time between two marks
   */
  public measure(name: string, startMark: string, endMark: string): number | null {
    if (window.performance && window.performance.measure) {
      try {
        window.performance.measure(name, startMark, endMark);
        const measures = window.performance.getEntriesByName(name, 'measure');
        if (measures.length > 0) {
          const duration = measures[measures.length - 1].duration;
          this.recordMetric({
            name: `custom-${name}`,
            value: duration,
            rating: this.getRating(duration, { good: 100, needsImprovement: 300 }),
            timestamp: Date.now(),
          });
          return duration;
        }
      } catch (e) {
        console.error('Error measuring performance:', e);
      }
    }
    return null;
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Export for use in components
export default performanceMonitor;
