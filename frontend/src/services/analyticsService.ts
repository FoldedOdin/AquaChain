/**
 * Analytics Service for tracking user interactions and conversions
 */

type ConversionEvent = 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup' | 'logout' | 'oauth_login';
type UserRole = 'consumer' | 'technician' | 'admin';

interface AnalyticsEvent {
  event: string;
  timestamp: string;
  userId?: string;
  userRole?: UserRole;
  properties?: Record<string, any>;
}

class AnalyticsService {
  private userId: string | null = null;
  private userRole: UserRole | null = null;
  private events: AnalyticsEvent[] = [];

  /**
   * Initialize analytics service
   */
  initialize(): void {
    if (process.env.NODE_ENV === 'development') {
      console.log('Analytics service initialized in development mode');
    }
  }

  /**
   * Set user ID for tracking
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Set user role for tracking
   */
  setUserRole(role: UserRole): void {
    this.userRole = role;
  }

  /**
   * Track conversion events
   */
  async trackConversion(
    event: ConversionEvent,
    userId?: string,
    properties?: Record<string, any>
  ): Promise<void> {
    const analyticsEvent: AnalyticsEvent = {
      event,
      timestamp: new Date().toISOString(),
      userId: userId || this.userId || undefined,
      userRole: this.userRole || undefined,
      properties: {
        ...properties,
        environment: process.env.NODE_ENV,
        url: window.location.href,
        userAgent: navigator.userAgent,
      }
    };

    this.events.push(analyticsEvent);

    if (process.env.NODE_ENV === 'development') {
      console.log('Analytics Event:', analyticsEvent);
    }

    // In production, would send to analytics service (Google Analytics, AWS Pinpoint, etc.)
    if (process.env.NODE_ENV === 'production') {
      await this.sendToAnalyticsService(analyticsEvent);
    }
  }

  /**
   * Track page views
   */
  async trackPageView(page: string, properties?: Record<string, any>): Promise<void> {
    await this.trackConversion('demo_view', undefined, {
      page,
      ...properties
    });
  }

  /**
   * Track custom events
   */
  async trackEvent(eventName: string, properties?: Record<string, any>): Promise<void> {
    const analyticsEvent: AnalyticsEvent = {
      event: eventName,
      timestamp: new Date().toISOString(),
      userId: this.userId || undefined,
      userRole: this.userRole || undefined,
      properties: {
        ...properties,
        environment: process.env.NODE_ENV,
        url: window.location.href,
      }
    };

    this.events.push(analyticsEvent);

    if (process.env.NODE_ENV === 'development') {
      console.log('Custom Event:', analyticsEvent);
    }

    if (process.env.NODE_ENV === 'production') {
      await this.sendToAnalyticsService(analyticsEvent);
    }
  }

  /**
   * Send event to analytics service (production only)
   */
  private async sendToAnalyticsService(event: AnalyticsEvent): Promise<void> {
    try {
      // Example: Send to Google Analytics 4
      if (process.env.REACT_APP_GA4_MEASUREMENT_ID) {
        // Would integrate with gtag here
        console.log('Would send to GA4:', event);
      }

      // Example: Send to AWS Pinpoint
      if (process.env.REACT_APP_PINPOINT_APPLICATION_ID) {
        // Would integrate with AWS Pinpoint here
        console.log('Would send to Pinpoint:', event);
      }

      // Example: Send to custom analytics endpoint
      if (process.env.REACT_APP_API_ENDPOINT) {
        await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/analytics/events`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(event),
        });
      }
    } catch (error) {
      console.warn('Failed to send analytics event:', error);
    }
  }

  /**
   * Get all tracked events (for debugging)
   */
  getEvents(): AnalyticsEvent[] {
    return [...this.events];
  }

  /**
   * Clear all events
   */
  clearEvents(): void {
    this.events = [];
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService();
export default analyticsService;