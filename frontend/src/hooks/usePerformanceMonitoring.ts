/**
 * Performance Monitoring Hook
 * Provides real-time performance monitoring and optimization suggestions
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { PerformanceMonitor } from '../utils/performanceMonitor';

interface PerformanceMetrics {
  lcp?: number;
  fid?: number;
  cls?: number;
  fcp?: number;
  ttfb?: number;
  inp?: number;
}

interface PerformanceState {
  metrics: PerformanceMetrics;
  isLoading: boolean;
  overallScore: number;
  recommendations: string[];
  connectionInfo: {
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
  };
}

interface PerformanceConfig {
  enableRealTimeMonitoring?: boolean;
  enableRecommendations?: boolean;
  enableConnectionMonitoring?: boolean;
  reportingInterval?: number;
}

export const usePerformanceMonitoring = (config: PerformanceConfig = {}) => {
  const {
    enableRealTimeMonitoring = true,
  } = config;

  const [performanceState, setPerformanceState] = useState<PerformanceState>({
    metrics: {},
    isLoading: true,
    overallScore: 0,
    recommendations: [],
    connectionInfo: {},
  });

  // Performance monitor instance
  const performanceMonitorRef = useRef<PerformanceMonitor | null>(null);

  // Initialize performance monitor
  useEffect(() => {
    if (enableRealTimeMonitoring) {
      performanceMonitorRef.current = new PerformanceMonitor();
      performanceMonitorRef.current.start();

      return () => {
        if (performanceMonitorRef.current) {
          performanceMonitorRef.current.stop();
        }
      };
    }
  }, [enableRealTimeMonitoring]);

  // Track layout shift
  const trackLayoutShift = useCallback(() => {
    if (performanceMonitorRef.current) {
      // Layout shift tracking is handled automatically by PerformanceMonitor
      const report = performanceMonitorRef.current.checkBudget();

      setPerformanceState((prev: PerformanceState) => ({
        ...prev,
        overallScore: report.score,
        recommendations: report.violations.map(v => v.recommendation),
      }));
    }
  }, []);

  // Get current performance metrics
  const getMetrics = useCallback(() => {
    if (performanceMonitorRef.current) {
      return performanceMonitorRef.current.getMetrics();
    }
    return {};
  }, []);

  // Check performance budget
  const checkBudget = useCallback(() => {
    if (performanceMonitorRef.current) {
      return performanceMonitorRef.current.checkBudget();
    }
    return null;
  }, []);

  // Legacy functions for backward compatibility
  const measurePerformance = useCallback(() => {
    // Deprecated: use trackLayoutShift instead
    trackLayoutShift();
  }, [trackLayoutShift]);

  const getPerformanceInsights = useCallback(() => {
    // Deprecated: use getMetrics instead
    return getMetrics();
  }, [getMetrics]);

  return {
    ...performanceState,
    trackLayoutShift,
    getMetrics,
    checkBudget,
    measurePerformance,
    getPerformanceInsights,
    performanceMonitor: performanceMonitorRef.current,
  };
};
