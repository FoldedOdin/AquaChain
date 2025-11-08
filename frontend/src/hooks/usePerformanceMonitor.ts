/**
 * Performance Monitoring Hook
 * Provides performance tracking utilities for React components
 */

import { useEffect, useRef, useCallback } from 'react';
import performanceMonitor from '../services/performanceMonitor';

interface UsePerformanceMonitorOptions {
  /** Component name for tracking */
  componentName: string;
  /** Enable render time tracking */
  trackRenderTime?: boolean;
  /** Enable mount time tracking */
  trackMountTime?: boolean;
  /** Warn if render time exceeds threshold (ms) */
  renderTimeThreshold?: number;
}

interface PerformanceMetrics {
  renderCount: number;
  totalRenderTime: number;
  averageRenderTime: number;
  mountTime: number | null;
}

/**
 * Hook for monitoring component performance
 */
export function usePerformanceMonitor(options: UsePerformanceMonitorOptions) {
  const {
    componentName,
    trackRenderTime = true,
    trackMountTime = true,
    renderTimeThreshold = 16, // 60fps = 16ms per frame
  } = options;

  const renderCountRef = useRef(0);
  const totalRenderTimeRef = useRef(0);
  const mountTimeRef = useRef<number | null>(null);
  const renderStartRef = useRef<number>(0);

  // Track component mount
  useEffect(() => {
    if (trackMountTime) {
      const mountStart = performance.now();
      performanceMonitor.mark(`${componentName}-mount-start`);

      return () => {
        const mountEnd = performance.now();
        performanceMonitor.mark(`${componentName}-mount-end`);
        
        const mountTime = performanceMonitor.measure(
          `${componentName}-mount`,
          `${componentName}-mount-start`,
          `${componentName}-mount-end`
        );

        if (mountTime) {
          mountTimeRef.current = mountTime;
          
          if (process.env.NODE_ENV === 'development') {
            console.log(`📊 ${componentName} mount time: ${mountTime.toFixed(2)}ms`);
          }
        }
      };
    }
  }, [componentName, trackMountTime]);

  // Track render time
  useEffect(() => {
    if (trackRenderTime) {
      const renderEnd = performance.now();
      const renderTime = renderEnd - renderStartRef.current;

      renderCountRef.current += 1;
      totalRenderTimeRef.current += renderTime;

      // Warn if render time exceeds threshold
      if (renderTime > renderTimeThreshold) {
        console.warn(
          `⚠️ ${componentName} render time exceeded threshold: ${renderTime.toFixed(2)}ms (threshold: ${renderTimeThreshold}ms)`
        );
      }

      if (process.env.NODE_ENV === 'development' && renderCountRef.current % 10 === 0) {
        const avgRenderTime = totalRenderTimeRef.current / renderCountRef.current;
        console.log(
          `📊 ${componentName} performance:`,
          `renders: ${renderCountRef.current},`,
          `avg: ${avgRenderTime.toFixed(2)}ms`
        );
      }
    }
  });

  // Mark render start before each render
  if (trackRenderTime) {
    renderStartRef.current = performance.now();
  }

  /**
   * Get current performance metrics
   */
  const getMetrics = useCallback((): PerformanceMetrics => {
    const renderCount = renderCountRef.current;
    const totalRenderTime = totalRenderTimeRef.current;
    const averageRenderTime = renderCount > 0 ? totalRenderTime / renderCount : 0;

    return {
      renderCount,
      totalRenderTime,
      averageRenderTime,
      mountTime: mountTimeRef.current,
    };
  }, []);

  /**
   * Measure a custom operation
   */
  const measureOperation = useCallback(
    (operationName: string, operation: () => void | Promise<void>) => {
      const startMark = `${componentName}-${operationName}-start`;
      const endMark = `${componentName}-${operationName}-end`;

      performanceMonitor.mark(startMark);

      const result = operation();

      if (result instanceof Promise) {
        return result.finally(() => {
          performanceMonitor.mark(endMark);
          performanceMonitor.measure(
            `${componentName}-${operationName}`,
            startMark,
            endMark
          );
        });
      } else {
        performanceMonitor.mark(endMark);
        performanceMonitor.measure(
          `${componentName}-${operationName}`,
          startMark,
          endMark
        );
      }
    },
    [componentName]
  );

  /**
   * Log current metrics
   */
  const logMetrics = useCallback(() => {
    const metrics = getMetrics();
    console.log(`📊 ${componentName} Performance Metrics:`, metrics);
  }, [componentName, getMetrics]);

  return {
    getMetrics,
    measureOperation,
    logMetrics,
  };
}

/**
 * Hook for tracking data fetching performance
 */
export function useDataFetchPerformance(operationName: string) {
  const startTimeRef = useRef<number>(0);

  const startTracking = useCallback(() => {
    startTimeRef.current = performance.now();
    performanceMonitor.mark(`${operationName}-start`);
  }, [operationName]);

  const endTracking = useCallback(() => {
    const endTime = performance.now();
    performanceMonitor.mark(`${operationName}-end`);
    
    const duration = performanceMonitor.measure(
      operationName,
      `${operationName}-start`,
      `${operationName}-end`
    );

    if (duration && duration > 500) {
      console.warn(
        `⚠️ Slow data fetch detected: ${operationName} took ${duration.toFixed(2)}ms`
      );
    }

    return duration;
  }, [operationName]);

  return { startTracking, endTracking };
}
