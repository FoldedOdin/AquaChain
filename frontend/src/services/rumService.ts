/**
 * Real User Monitoring (RUM) Service
 * Collects and reports real user performance data
 */

import { Metric } from 'web-vitals';

interface RUMConfig {
  apiEndpoint?: string;
  batchSize?: number;
  flushInterval?: number;
  enableLocalStorage?: boolean;
  enableBeacon?: boolean;
}

interface UserSession {
  sessionId: string;
  userId?: string;
  timestamp: number;
  userAgent: string;
  url: string;
  referrer: string;
  viewport: {
    width: number;
    height: number;
  };
  connection?: {
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
  };
  deviceInfo: {
    isMobile: boolean;
    isTablet: boolean;
    isDesktop: boolean;
    platform: string;
  };
}

interface PerformanceEvent {
  sessionId: string;
  timestamp: number;
  type: 'web-vital' | 'navigation' | 'resource' | 'user-interaction' | 'error';
  data: any;
}

class RUMService {
  private config: Required<RUMConfig>;
  private session: UserSession;
  private eventQueue: PerformanceEvent[] = [];
  private flushTimer?: NodeJS.Timeout;

  constructor(config: RUMConfig = {}) {
    this.config = {
      apiEndpoint: config.apiEndpoint || '/api/rum',
      batchSize: config.batchSize || 10,
      flushInterval: config.flushInterval || 30000, // 30 seconds
      enableLocalStorage: config.enableLocalStorage ?? true,
      enableBeacon: config.enableBeacon ?? true
    };

    this.session = this.initializeSession();
    this.setupEventListeners();
    this.startFlushTimer();
  }

  private initializeSession(): UserSession {
    const sessionId = this.generateSessionId();
    const connection = this.getConnectionInfo();
    const deviceInfo = this.getDeviceInfo();

    return {
      sessionId,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      referrer: document.referrer,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      connection,
      deviceInfo
    };
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2)}`;
  }

  private getConnectionInfo() {
    const connection = (navigator as any).connection || 
                      (navigator as any).mozConnection || 
                      (navigator as any).webkitConnection;
    
    if (!connection) return undefined;

    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt
    };
  }

  private getDeviceInfo() {
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobile = /mobile|android|iphone|ipad|phone/i.test(userAgent);
    const isTablet = /tablet|ipad/i.test(userAgent) && !isMobile;
    const isDesktop = !isMobile && !isTablet;

    return {
      isMobile,
      isTablet,
      isDesktop,
      platform: navigator.platform
    };
  }

  private setupEventListeners() {
    // Web Vitals monitoring
    if (typeof window !== 'undefined') {
      import('web-vitals').then((webVitals) => {
        const handleMetric = (metric: Metric) => {
          this.recordWebVital(metric);
        };

        webVitals.getCLS(handleMetric);
        webVitals.getFID(handleMetric);
        webVitals.getFCP(handleMetric);
        webVitals.getLCP(handleMetric);
        webVitals.getTTFB(handleMetric);
        
        // onINP might not be available in older versions
        if ('onINP' in webVitals) {
          (webVitals as any).onINP(handleMetric);
        }
      });
    }

    // Navigation timing
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.recordNavigationTiming();
      }, 0);
    });

    // Resource timing
    this.observeResourceTiming();

    // User interactions
    this.observeUserInteractions();

    // Errors
    this.observeErrors();

    // Page visibility changes
    document.addEventListener('visibilitychange', () => {
      this.recordEvent('user-interaction', {
        type: 'visibility-change',
        hidden: document.hidden,
        timestamp: Date.now()
      });
    });

    // Before unload - flush remaining events
    window.addEventListener('beforeunload', () => {
      this.flush(true);
    });
  }

  private recordWebVital(metric: Metric) {
    this.recordEvent('web-vital', {
      name: metric.name,
      value: metric.value,
      delta: metric.delta,
      id: metric.id,
      rating: this.getMetricRating(metric)
    });
  }

  private getMetricRating(metric: Metric): 'good' | 'needs-improvement' | 'poor' {
    const thresholds: Record<string, { good: number; needsImprovement: number }> = {
      LCP: { good: 2500, needsImprovement: 4000 },
      FID: { good: 100, needsImprovement: 300 },
      CLS: { good: 0.1, needsImprovement: 0.25 },
      FCP: { good: 1800, needsImprovement: 3000 },
      TTFB: { good: 800, needsImprovement: 1800 }
    };

    const threshold = thresholds[metric.name];
    if (!threshold) return 'good';

    if (metric.value <= threshold.good) return 'good';
    if (metric.value <= threshold.needsImprovement) return 'needs-improvement';
    return 'poor';
  }

  private recordNavigationTiming() {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (!navigation) return;

    this.recordEvent('navigation', {
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      domInteractive: navigation.domInteractive - navigation.fetchStart,
      redirectTime: navigation.redirectEnd - navigation.redirectStart,
      dnsTime: navigation.domainLookupEnd - navigation.domainLookupStart,
      connectTime: navigation.connectEnd - navigation.connectStart,
      requestTime: navigation.responseStart - navigation.requestStart,
      responseTime: navigation.responseEnd - navigation.responseStart,
      renderTime: navigation.domComplete - navigation.responseEnd
    });
  }

  private observeResourceTiming() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'resource') {
          const resource = entry as PerformanceResourceTiming;
          
          // Only track significant resources
          if (resource.transferSize > 10000 || resource.duration > 100) {
            this.recordEvent('resource', {
              name: resource.name,
              type: this.getResourceType(resource.name),
              duration: resource.duration,
              transferSize: resource.transferSize,
              encodedBodySize: resource.encodedBodySize,
              decodedBodySize: resource.decodedBodySize
            });
          }
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
  }

  private getResourceType(url: string): string {
    if (url.match(/\.(js|jsx|ts|tsx)$/)) return 'script';
    if (url.match(/\.(css|scss|sass)$/)) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg|avif)$/)) return 'image';
    if (url.match(/\.(woff|woff2|ttf|otf)$/)) return 'font';
    if (url.match(/\.(mp4|webm|ogg|mp3|wav)$/)) return 'media';
    return 'other';
  }

  private observeUserInteractions() {
    const interactionTypes = ['click', 'scroll', 'keydown', 'touchstart'];
    
    interactionTypes.forEach(type => {
      document.addEventListener(type, (event) => {
        // Throttle interaction recording
        if (Math.random() > 0.1) return; // Sample 10% of interactions
        
        this.recordEvent('user-interaction', {
          type,
          target: (event.target as Element)?.tagName?.toLowerCase(),
          timestamp: Date.now()
        });
      }, { passive: true });
    });
  }

  private observeErrors() {
    // JavaScript errors
    window.addEventListener('error', (event) => {
      this.recordEvent('error', {
        type: 'javascript',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      });
    });

    // Promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.recordEvent('error', {
        type: 'promise-rejection',
        reason: event.reason?.toString(),
        stack: event.reason?.stack
      });
    });
  }

  private recordEvent(type: PerformanceEvent['type'], data: any) {
    const event: PerformanceEvent = {
      sessionId: this.session.sessionId,
      timestamp: Date.now(),
      type,
      data
    };

    this.eventQueue.push(event);

    // Auto-flush if queue is full
    if (this.eventQueue.length >= this.config.batchSize) {
      this.flush();
    }

    // Store in localStorage for debugging
    if (this.config.enableLocalStorage && process.env.NODE_ENV === 'development') {
      const stored = JSON.parse(localStorage.getItem('aquachain_rum') || '[]');
      stored.push(event);
      localStorage.setItem('aquachain_rum', JSON.stringify(stored.slice(-100))); // Keep last 100 events
    }
  }

  private startFlushTimer() {
    this.flushTimer = setInterval(() => {
      if (this.eventQueue.length > 0) {
        this.flush();
      }
    }, this.config.flushInterval);
  }

  private async flush(useBeacon = false) {
    if (this.eventQueue.length === 0) return;

    const payload = {
      session: this.session,
      events: [...this.eventQueue]
    };

    this.eventQueue = [];

    try {
      if (useBeacon && this.config.enableBeacon && 'sendBeacon' in navigator) {
        // Use sendBeacon for reliable delivery during page unload
        navigator.sendBeacon(
          this.config.apiEndpoint,
          JSON.stringify(payload)
        );
      } else {
        // Use fetch for normal operation
        const response = await fetch(this.config.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        // If we get a 404, it means the backend isn't running - fail silently in development
        if (response.status === 404 && process.env.NODE_ENV === 'development') {
          console.warn('RUM: Development server not running. Start with: npm run dev-server');
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }
    } catch (error) {
      // Only log warnings in development, fail silently in production for network errors
      if (process.env.NODE_ENV === 'development') {
        console.warn('RUM: Backend not available, analytics disabled:', error);
      }
      
      // Re-queue events on failure (up to a limit) only for non-404 errors
      if (payload.events.length < 50 && !(error as any)?.message?.includes('404')) {
        this.eventQueue.unshift(...payload.events);
      }
    }
  }

  // Public methods
  public setUserId(userId: string) {
    this.session.userId = userId;
  }

  public recordCustomEvent(name: string, data: any) {
    this.recordEvent('user-interaction', {
      type: 'custom',
      name,
      data
    });
  }

  public getSessionId(): string {
    return this.session.sessionId;
  }

  public destroy() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush(true);
  }
}

// Singleton instance
let rumInstance: RUMService | null = null;

export const initializeRUM = (config?: RUMConfig): RUMService => {
  if (!rumInstance && typeof window !== 'undefined') {
    rumInstance = new RUMService(config);
  }
  return rumInstance!;
};

export const getRUM = (): RUMService | null => rumInstance;

export default RUMService;