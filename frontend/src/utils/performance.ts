import { getCLS, getFID, getFCP, getLCP, getTTFB, Metric } from 'web-vitals';

export interface PerformanceMetrics {
  cls: number | null;
  fid: number | null;
  fcp: number | null;
  lcp: number | null;
  ttfb: number | null;
}

export interface PerformanceThresholds {
  cls: { good: number; needsImprovement: number };
  fid: { good: number; needsImprovement: number };
  fcp: { good: number; needsImprovement: number };
  lcp: { good: number; needsImprovement: number };
  ttfb: { good: number; needsImprovement: number };
}

// Core Web Vitals thresholds (in milliseconds, except CLS which is unitless)
export const PERFORMANCE_THRESHOLDS: PerformanceThresholds = {
  cls: { good: 0.1, needsImprovement: 0.25 },
  fid: { good: 100, needsImprovement: 300 },
  fcp: { good: 1800, needsImprovement: 3000 },
  lcp: { good: 2500, needsImprovement: 4000 },
  ttfb: { good: 800, needsImprovement: 1800 },
};

export type MetricName = keyof PerformanceMetrics;
export type PerformanceRating = 'good' | 'needs-improvement' | 'poor';

export class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    cls: null,
    fid: null,
    fcp: null,
    lcp: null,
    ttfb: null,
  };

  private callbacks: Array<(metrics: PerformanceMetrics) => void> = [];

  constructor() {
    this.initializeMetrics();
  }

  private initializeMetrics(): void {
    // Only initialize in browser environment
    if (typeof window === 'undefined') return;

    getCLS(this.handleMetric.bind(this, 'cls'));
    getFID(this.handleMetric.bind(this, 'fid'));
    getFCP(this.handleMetric.bind(this, 'fcp'));
    getLCP(this.handleMetric.bind(this, 'lcp'));
    getTTFB(this.handleMetric.bind(this, 'ttfb'));
  }

  private handleMetric(name: MetricName, metric: Metric): void {
    this.metrics[name] = metric.value;
    this.notifyCallbacks();
    
    // Log performance metrics in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`${name.toUpperCase()}: ${metric.value}`, {
        rating: this.getRating(name, metric.value),
        threshold: PERFORMANCE_THRESHOLDS[name],
      });
    }
  }

  private notifyCallbacks(): void {
    this.callbacks.forEach(callback => callback({ ...this.metrics }));
  }

  public getRating(metricName: MetricName, value: number): PerformanceRating {
    const threshold = PERFORMANCE_THRESHOLDS[metricName];
    
    if (value <= threshold.good) {
      return 'good';
    } else if (value <= threshold.needsImprovement) {
      return 'needs-improvement';
    } else {
      return 'poor';
    }
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public subscribe(callback: (metrics: PerformanceMetrics) => void): () => void {
    this.callbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = this.callbacks.indexOf(callback);
      if (index > -1) {
        this.callbacks.splice(index, 1);
      }
    };
  }

  public getPerformanceScore(): number {
    const metrics = this.getMetrics();
    let totalScore = 0;
    let validMetrics = 0;

    Object.entries(metrics).forEach(([name, value]) => {
      if (value !== null) {
        const rating = this.getRating(name as MetricName, value);
        let score = 0;
        
        switch (rating) {
          case 'good':
            score = 100;
            break;
          case 'needs-improvement':
            score = 50;
            break;
          case 'poor':
            score = 0;
            break;
        }
        
        totalScore += score;
        validMetrics++;
      }
    });

    return validMetrics > 0 ? Math.round(totalScore / validMetrics) : 0;
  }

  public reportToAnalytics(analyticsFunction?: (metrics: PerformanceMetrics & { score: number }) => void): void {
    if (analyticsFunction) {
      const metrics = this.getMetrics();
      const score = this.getPerformanceScore();
      analyticsFunction({ ...metrics, score });
    }
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

// React hook for using performance metrics
export function usePerformanceMetrics(): {
  metrics: PerformanceMetrics;
  score: number;
  getRating: (metricName: MetricName, value: number) => PerformanceRating;
} {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics>(performanceMonitor.getMetrics());

  React.useEffect(() => {
    const unsubscribe = performanceMonitor.subscribe(setMetrics);
    return unsubscribe;
  }, []);

  return {
    metrics,
    score: performanceMonitor.getPerformanceScore(),
    getRating: performanceMonitor.getRating.bind(performanceMonitor),
  };
}

// Import React for the hook
import React from 'react';