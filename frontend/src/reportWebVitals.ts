import { ReportHandler, Metric } from 'web-vitals';

/**
 * Enhanced Web Vitals reporting with analytics integration
 */

// Performance thresholds based on Core Web Vitals
const PERFORMANCE_THRESHOLDS = {
  LCP: { good: 2500, needsImprovement: 4000 }, // Largest Contentful Paint
  FID: { good: 100, needsImprovement: 300 },   // First Input Delay
  CLS: { good: 0.1, needsImprovement: 0.25 },  // Cumulative Layout Shift
  FCP: { good: 1800, needsImprovement: 3000 }, // First Contentful Paint
  TTFB: { good: 800, needsImprovement: 1800 }  // Time to First Byte
};

// Performance data storage
interface PerformanceData {
  sessionId: string;
  timestamp: number;
  url: string;
  userAgent: string;
  connectionType?: string;
  metrics: Record<string, Metric>;
}

const performanceData: PerformanceData = {
  sessionId: generateSessionId(),
  timestamp: Date.now(),
  url: window.location.href,
  userAgent: navigator.userAgent,
  connectionType: getConnectionType(),
  metrics: {}
};

function generateSessionId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function getConnectionType(): string | undefined {
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
  return connection?.effectiveType || connection?.type;
}

function getPerformanceRating(metric: Metric): 'good' | 'needs-improvement' | 'poor' {
  const thresholds = PERFORMANCE_THRESHOLDS[metric.name as keyof typeof PERFORMANCE_THRESHOLDS];
  if (!thresholds) return 'good';
  
  if (metric.value <= thresholds.good) return 'good';
  if (metric.value <= thresholds.needsImprovement) return 'needs-improvement';
  return 'poor';
}

function sendToAnalytics(metric: Metric) {
  const rating = getPerformanceRating(metric);
  
  // Store metric
  performanceData.metrics[metric.name] = metric;
  
  // Send to Google Analytics 4 if available
  if (typeof (window as any).gtag !== 'undefined') {
    (window as any).gtag('event', metric.name, {
      event_category: 'Web Vitals',
      event_label: rating,
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      custom_map: {
        metric_id: metric.id,
        metric_value: metric.value,
        metric_delta: metric.delta,
        metric_rating: rating
      }
    });
  }
  
  // Send to AWS Pinpoint if available
  if (typeof window !== 'undefined' && (window as any).AWSPinpoint) {
    (window as any).AWSPinpoint.record({
      name: 'web_vitals_metric',
      attributes: {
        metric_name: metric.name,
        metric_rating: rating,
        session_id: performanceData.sessionId,
        connection_type: performanceData.connectionType || 'unknown'
      },
      metrics: {
        metric_value: metric.value,
        metric_delta: metric.delta
      }
    });
  }
  
  // Console logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Web Vitals] ${metric.name}:`, {
      value: metric.value,
      rating,
      delta: metric.delta,
      id: metric.id
    });
  }
}

function sendPerformanceSummary() {
  const summary = {
    sessionId: performanceData.sessionId,
    timestamp: performanceData.timestamp,
    url: performanceData.url,
    userAgent: performanceData.userAgent,
    connectionType: performanceData.connectionType,
    metrics: Object.values(performanceData.metrics).map(metric => ({
      name: metric.name,
      value: metric.value,
      rating: getPerformanceRating(metric)
    }))
  };
  
  // Send summary to analytics
  if (typeof (window as any).gtag !== 'undefined') {
    (window as any).gtag('event', 'performance_summary', {
      event_category: 'Performance',
      custom_map: summary
    });
  }
  
  // Store in localStorage for debugging
  if (process.env.NODE_ENV === 'development') {
    localStorage.setItem('aquachain_performance', JSON.stringify(summary));
  }
}

const reportWebVitals = (onPerfEntry?: ReportHandler) => {
  const handleMetric = (metric: Metric) => {
    // Send to custom handler if provided
    if (onPerfEntry && typeof onPerfEntry === 'function') {
      onPerfEntry(metric);
    }
    
    // Send to analytics
    sendToAnalytics(metric);
  };

  if (typeof window !== 'undefined') {
    import('web-vitals').then((webVitals) => {
      webVitals.getCLS(handleMetric);
      webVitals.getFID(handleMetric);
      webVitals.getFCP(handleMetric);
      webVitals.getLCP(handleMetric);
      webVitals.getTTFB(handleMetric);
      
      // New metric: Interaction to Next Paint (replacing FID)
      if ('onINP' in webVitals) {
        (webVitals as any).onINP(handleMetric);
      }
    });
    
    // Send summary when page is about to unload
    window.addEventListener('beforeunload', sendPerformanceSummary);
    
    // Send summary after 30 seconds for long sessions
    setTimeout(sendPerformanceSummary, 30000);
  }
};

// Export performance data for debugging
export const getPerformanceData = () => performanceData;

// Export function to manually trigger performance summary
export const sendPerformanceReport = () => sendPerformanceSummary();

// Export thresholds for testing
export const THRESHOLDS = PERFORMANCE_THRESHOLDS;

export default reportWebVitals;
