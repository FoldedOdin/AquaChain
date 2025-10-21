/**
 * Performance Monitoring Hook
 * Provides real-time performance monitoring and optimization suggestions
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { Metric } from 'web-vitals';

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
    enableRecommendations = true,
    enableConnectionMonitoring = true,
    reportingInterval = 5000
  } = config;

  const [performanceState, setPerformanceState] = useState<PerformanceState>({
    metrics: {},
    isLoading: true,
    overallScore: 0,
    recommendations: [],
    connectionInfo: {}
  });

  const metricsRef = useRef<PerformanceMetrics>({});
  const reportingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate overall performance score
  const calculateOverallScore = useCallback((metrics: PerformanceMetrics): number => {
    const weights = {
      lcp: 0.25,  // Largest Contentful Paint
      fid: 0.25,  // First Input Delay
      cls: 0.25,  // Cumulative Layout Shift
      fcp: 0.15,  // First Contentful Paint
      ttfb: 0.1   // Time to First Byte
    };

    let totalScore = 0;
    let totalWeight = 0;

    Object.entries(weights).forEach(([metric, weight]) => {
      const value = metrics[metric as keyof PerformanceMetrics];
      if (value !== undefined) {
        let score = 100;
        
        switch (metric) {
          case 'lcp':
            score = value <= 2500 ? 100 : value <= 4000 ? 75 : 50;
            break;
          case 'fid':
            score = value <= 100 ? 100 : value <= 300 ? 75 : 50;
            break;
          case 'cls':
            score = value <= 0.1 ? 100 : value <= 0.25 ? 75 : 50;
            break;
          case 'fcp':
            score = value <= 1800 ? 100 : value <= 3000 ? 75 : 50;
            break;
          case 'ttfb':
            score = value <= 800 ? 100 : value <= 1800 ? 75 : 50;
            break;
        }
        
        totalScore += score * weight;
        totalWeight += weight;
      }
    });

    return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0;
  }, []);

  // Generate performance recommendations
  const generateRecommendations = useCallback((metrics: PerformanceMetrics): string[] => {
    const recommendations: string[] = [];

    if (metrics.lcp && metrics.lcp > 2500) {
      recommendations.push('Optimize Largest Contentful Paint by reducing image sizes and improving server response times');
    }

    if (metrics.fid && metrics.fid > 100) {
      recommendations.push('Reduce First Input Delay by minimizing JavaScript execution time');
    }

    if (metrics.cls && metrics.cls > 0.1) {
      recommendations.push('Improve Cumulative Layout Shift by setting dimensions for images and ads');
    }

    if (metrics.fcp && metrics.fcp > 1800) {
      recommendations.push('Speed up First Contentful Paint by optimizing critical rendering path');
    }

    if (metrics.ttfb && metrics.ttfb > 800) {
      recommendations.push('Reduce Time to First Byte by optimizing server response time');
    }

    return recommendations;
  }, []);

  // Get connection information
  const getConnectionInfo = useCallback(() => {
    const connection = (navigator as any).connection || 
                      (navigator as any).mozConnection || 
                      (navigator as any).webkitConnection;
    
    return {
      effectiveType: connection?.effectiveType,
      downlink: connection?.downlink,
      rtt: connection?.rtt
    };
  }, []);

  // Handle metric updates
  const handleMetricUpdate = useCallback((metric: Metric) => {
    metricsRef.current = {
      ...metricsRef.current,
      [metric.name.toLowerCase()]: metric.value
    };

    if (enableRealTimeMonitoring) {
      const newMetrics = { ...metricsRef.current };
      const overallScore = calculateOverallScore(newMetrics);
      const recommendations = enableRecommendations ? generateRecommendations(newMetrics) : [];
      const connectionInfo = enableConnectionMonitoring ? getConnectionInfo() : {};

      setPerformanceState({
        metrics: newMetrics,
        isLoading: false,
        overallScore,
        recommendations,
        connectionInfo
      });
    }
  }, [enableRealTimeMonitoring, enableRecommendations, enableConnectionMonitoring, calculateOverallScore, generateRecommendations, getConnectionInfo]);

  // Initialize performance monitoring
  useEffect(() => {
    if (typeof window === 'undefined') return;

    let cleanup: (() => void)[] = [];

    // Import and setup web-vitals
    import('web-vitals').then((webVitals) => {
      webVitals.getCLS(handleMetricUpdate);
      webVitals.getFID(handleMetricUpdate);
      webVitals.getFCP(handleMetricUpdate);
      webVitals.getLCP(handleMetricUpdate);
      webVitals.getTTFB(handleMetricUpdate);
      if ('onINP' in webVitals) {
        (webVitals as any).onINP(handleMetricUpdate);
      }
    });

    // Setup periodic reporting
    if (reportingInterval > 0) {
      reportingTimerRef.current = setInterval(() => {
        const currentMetrics = { ...metricsRef.current };
        const overallScore = calculateOverallScore(currentMetrics);
        const recommendations = enableRecommendations ? generateRecommendations(currentMetrics) : [];
        const connectionInfo = enableConnectionMonitoring ? getConnectionInfo() : {};

        setPerformanceState(prev => ({
          ...prev,
          metrics: currentMetrics,
          overallScore,
          recommendations,
          connectionInfo
        }));
      }, reportingInterval);

      cleanup.push(() => {
        if (reportingTimerRef.current) {
          clearInterval(reportingTimerRef.current);
        }
      });
    }

    // Monitor connection changes
    if (enableConnectionMonitoring && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      const handleConnectionChange = () => {
        setPerformanceState(prev => ({
          ...prev,
          connectionInfo: getConnectionInfo()
        }));
      };

      connection?.addEventListener('change', handleConnectionChange);
      cleanup.push(() => {
        connection?.removeEventListener('change', handleConnectionChange);
      });
    }

    return () => {
      cleanup.forEach(fn => fn());
    };
  }, [handleMetricUpdate, reportingInterval, enableConnectionMonitoring, enableRecommendations, calculateOverallScore, generateRecommendations, getConnectionInfo]);

  // Manual performance measurement
  const measurePerformance = useCallback(async () => {
    if (typeof window === 'undefined') return;

    const { getCLS, getFID, getFCP, getLCP, getTTFB } = await import('web-vitals');
    
    return new Promise<PerformanceMetrics>((resolve) => {
      const metrics: PerformanceMetrics = {};
      let pendingMetrics = 5;

      const checkComplete = () => {
        pendingMetrics--;
        if (pendingMetrics === 0) {
          resolve(metrics);
        }
      };

      getCLS((metric) => {
        metrics.cls = metric.value;
        checkComplete();
      });

      getFID((metric) => {
        metrics.fid = metric.value;
        checkComplete();
      });

      getFCP((metric) => {
        metrics.fcp = metric.value;
        checkComplete();
      });

      getLCP((metric) => {
        metrics.lcp = metric.value;
        checkComplete();
      });

      getTTFB((metric) => {
        metrics.ttfb = metric.value;
        checkComplete();
      });
    });
  }, []);

  // Get performance insights
  const getPerformanceInsights = useCallback(() => {
    const { metrics, overallScore } = performanceState;
    
    return {
      score: overallScore,
      grade: overallScore >= 90 ? 'A' : overallScore >= 80 ? 'B' : overallScore >= 70 ? 'C' : overallScore >= 60 ? 'D' : 'F',
      coreWebVitals: {
        lcp: {
          value: metrics.lcp,
          status: !metrics.lcp ? 'pending' : metrics.lcp <= 2500 ? 'good' : metrics.lcp <= 4000 ? 'needs-improvement' : 'poor'
        },
        fid: {
          value: metrics.fid,
          status: !metrics.fid ? 'pending' : metrics.fid <= 100 ? 'good' : metrics.fid <= 300 ? 'needs-improvement' : 'poor'
        },
        cls: {
          value: metrics.cls,
          status: !metrics.cls ? 'pending' : metrics.cls <= 0.1 ? 'good' : metrics.cls <= 0.25 ? 'needs-improvement' : 'poor'
        }
      },
      recommendations: performanceState.recommendations
    };
  }, [performanceState]);

  return {
    ...performanceState,
    measurePerformance,
    getPerformanceInsights
  };
};