import { PinpointClient, PutEventsCommand, PutEventsRequest } from '@aws-sdk/client-pinpoint';

// Analytics event types
export interface AnalyticsEvent {
  eventType: string;
  timestamp?: string;
  attributes?: Record<string, string>;
  metrics?: Record<string, number>;
  sessionId?: string;
  userId?: string;
  userRole?: string;
  deviceType?: string;
  source?: string;
}

// User attributes for segmentation
export interface UserAttributes {
  userId: string;
  email?: string;
  role: 'consumer' | 'technician' | 'admin';
  deviceType: 'mobile' | 'tablet' | 'desktop';
  userAgent: string;
  location?: {
    country?: string;
    region?: string;
    city?: string;
  };
  preferences?: {
    theme?: string;
    language?: string;
    reducedMotion?: boolean;
  };
}

// Session information
export interface SessionInfo {
  sessionId: string;
  startTime: string;
  duration?: number;
  pageViews: number;
  interactions: number;
  source: 'direct' | 'organic' | 'referral' | 'social' | 'email' | 'paid';
  campaign?: string;
  medium?: string;
}

// Configuration interface
interface AnalyticsConfig {
  applicationId: string;
  region: string;
  mockMode?: boolean;
  credentials?: {
    accessKeyId: string;
    secretAccessKey: string;
  };
  enableDebugMode?: boolean;
  batchSize?: number;
  flushInterval?: number;
}

class AnalyticsService {
  private pinpointClient: PinpointClient | null = null;
  private config: AnalyticsConfig | null = null;
  private eventQueue: AnalyticsEvent[] = [];
  private sessionInfo: SessionInfo | null = null;
  private userAttributes: UserAttributes | null = null;
  private flushTimer: NodeJS.Timeout | null = null;
  private isInitialized = false;

  /**
   * Initialize the analytics service with AWS Pinpoint
   */
  async initialize(config: AnalyticsConfig): Promise<void> {
    try {
      this.config = {
        batchSize: 10,
        flushInterval: 30000, // 30 seconds
        enableDebugMode: process.env.NODE_ENV === 'development',
        ...config
      };

      // Check if running in mock mode or credentials are missing
      if (this.config.mockMode || !this.config.credentials || !this.config.credentials.accessKeyId) {
        if (this.config.enableDebugMode) {
          console.log('Analytics service: Running in mock mode (development)');
        }
        // Initialize session even in mock mode
        await this.startSession();
        this.setupAutoFlush();
        this.isInitialized = true;
        return;
      }

      // Initialize Pinpoint client
      this.pinpointClient = new PinpointClient({
        region: this.config.region,
        credentials: this.config.credentials
      });

      // Start session
      await this.startSession();

      // Set up automatic flushing
      this.setupAutoFlush();

      this.isInitialized = true;

      if (this.config.enableDebugMode) {
        console.log('Analytics service initialized with Pinpoint');
      }
    } catch (error) {
      console.error('Failed to initialize analytics service:', error);
      // Don't throw error, allow app to continue without analytics
      this.isInitialized = true;
    }
  }

  /**
   * Track a custom event
   */
  async trackEvent(event: AnalyticsEvent): Promise<void> {
    if (!this.isInitialized) {
      console.warn('Analytics service not initialized');
      return;
    }

    try {
      // Enrich event with session and user data
      const enrichedEvent: AnalyticsEvent = {
        ...event,
        timestamp: event.timestamp || new Date().toISOString(),
        sessionId: event.sessionId || this.sessionInfo?.sessionId,
        userId: event.userId || this.userAttributes?.userId,
        userRole: event.userRole || this.userAttributes?.role,
        deviceType: event.deviceType || this.userAttributes?.deviceType,
        attributes: {
          ...event.attributes,
          source: event.source || this.sessionInfo?.source || 'direct',
          userAgent: this.userAttributes?.userAgent || navigator.userAgent,
          ...(this.sessionInfo?.campaign && { campaign: this.sessionInfo.campaign }),
          ...(this.sessionInfo?.medium && { medium: this.sessionInfo.medium })
        }
      };

      // Add to queue
      this.eventQueue.push(enrichedEvent);

      // Update session interaction count
      if (this.sessionInfo) {
        this.sessionInfo.interactions++;
      }

      // Flush if batch size reached
      if (this.eventQueue.length >= (this.config?.batchSize || 10)) {
        await this.flush();
      }

      if (this.config?.enableDebugMode) {
        console.log('Event tracked:', enrichedEvent);
      }
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  /**
   * Track page view
   */
  async trackPageView(pageName: string, additionalAttributes?: Record<string, string>): Promise<void> {
    await this.trackEvent({
      eventType: 'page_view',
      attributes: {
        page_name: pageName,
        page_url: window.location.href,
        page_path: window.location.pathname,
        referrer: document.referrer,
        ...additionalAttributes
      },
      metrics: {
        page_load_time: performance.now()
      }
    });

    // Update session page view count
    if (this.sessionInfo) {
      this.sessionInfo.pageViews++;
    }
  }

  /**
   * Track user interaction
   */
  async trackInteraction(
    elementType: string,
    elementId: string,
    action: string,
    additionalAttributes?: Record<string, string>
  ): Promise<void> {
    await this.trackEvent({
      eventType: 'user_interaction',
      attributes: {
        element_type: elementType,
        element_id: elementId,
        action: action,
        page_url: window.location.href,
        ...additionalAttributes
      }
    });
  }

  /**
   * Track conversion event
   */
  async trackConversion(
    conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
    value?: number,
    additionalAttributes?: Record<string, string>
  ): Promise<void> {
    await this.trackEvent({
      eventType: 'conversion',
      attributes: {
        conversion_type: conversionType,
        page_url: window.location.href,
        ...additionalAttributes
      },
      metrics: {
        ...(value && { conversion_value: value }),
        session_duration: this.getSessionDuration()
      }
    });
  }

  /**
   * Set user attributes for segmentation
   */
  setUserAttributes(attributes: UserAttributes): void {
    this.userAttributes = {
      ...this.userAttributes,
      ...attributes
    };

    if (this.config?.enableDebugMode) {
      console.log('User attributes updated:', this.userAttributes);
    }
  }

  /**
   * Update user role
   */
  setUserRole(role: 'consumer' | 'technician' | 'admin'): void {
    if (this.userAttributes) {
      this.userAttributes.role = role;
    }
  }

  /**
   * Start a new session
   */
  private async startSession(): Promise<void> {
    const sessionId = this.generateSessionId();
    const source = this.detectTrafficSource();

    this.sessionInfo = {
      sessionId,
      startTime: new Date().toISOString(),
      pageViews: 0,
      interactions: 0,
      source: source.source,
      campaign: source.campaign,
      medium: source.medium
    };

    // Detect device type and user agent
    const deviceType = this.detectDeviceType();
    this.userAttributes = {
      userId: this.userAttributes?.userId || this.generateUserId(),
      role: this.userAttributes?.role || 'consumer',
      deviceType,
      userAgent: navigator.userAgent,
      ...this.userAttributes
    };

    await this.trackEvent({
      eventType: 'session_start',
      attributes: {
        session_id: sessionId,
        traffic_source: source.source,
        ...(source.campaign && { campaign: source.campaign }),
        ...(source.medium && { medium: source.medium })
      }
    });
  }

  /**
   * End current session
   */
  async endSession(): Promise<void> {
    if (!this.sessionInfo) return;

    const duration = this.getSessionDuration();

    await this.trackEvent({
      eventType: 'session_end',
      attributes: {
        session_id: this.sessionInfo.sessionId
      },
      metrics: {
        session_duration: duration,
        page_views: this.sessionInfo.pageViews,
        interactions: this.sessionInfo.interactions
      }
    });

    // Flush remaining events
    await this.flush();

    this.sessionInfo = null;
  }

  /**
   * Flush events to Pinpoint
   */
  private async flush(): Promise<void> {
    if (!this.pinpointClient || !this.config || this.eventQueue.length === 0) {
      // If no Pinpoint client, just log events in debug mode and clear queue
      if (this.config?.enableDebugMode && this.eventQueue.length > 0) {
        console.log('Analytics (Mock Mode): Would flush events:', this.eventQueue);
        this.eventQueue.length = 0; // Clear the queue
      }
      return;
    }

    const events = this.eventQueue.splice(0, this.config.batchSize || 10);

    try {
      
      // Convert events to Pinpoint format
      const pinpointEvents: any = {};
      
      events.forEach((event, index) => {
        const eventId = `${event.sessionId || 'unknown'}_${Date.now()}_${index}`;
        
        pinpointEvents[eventId] = {
          EventType: event.eventType,
          Timestamp: event.timestamp,
          Attributes: event.attributes || {},
          Metrics: event.metrics || {},
          Session: this.sessionInfo ? {
            Id: this.sessionInfo.sessionId,
            StartTimestamp: this.sessionInfo.startTime,
            Duration: this.getSessionDuration()
          } : undefined
        };
      });

      const putEventsRequest: PutEventsRequest = {
        ApplicationId: this.config.applicationId,
        EventsRequest: {
          BatchItem: {
            [this.userAttributes?.userId || 'anonymous']: {
              Endpoint: {
                ChannelType: 'CUSTOM',
                Address: this.userAttributes?.email || 'anonymous',
                Attributes: {
                  role: [this.userAttributes?.role || 'unknown'],
                  deviceType: [this.userAttributes?.deviceType || 'unknown']
                },
                User: {
                  UserId: this.userAttributes?.userId,
                  UserAttributes: {
                    email: [this.userAttributes?.email || ''],
                    role: [this.userAttributes?.role || '']
                  }
                }
              },
              Events: pinpointEvents
            }
          }
        }
      };

      const command = new PutEventsCommand(putEventsRequest);
      await this.pinpointClient.send(command);

      if (this.config.enableDebugMode) {
        console.log(`Flushed ${events.length} events to Pinpoint`);
      }
    } catch (error) {
      console.error('Failed to flush events to Pinpoint:', error);
      // Re-add events to queue for retry (events variable is available in this scope)
      this.eventQueue.unshift(...events);
    }
  }

  /**
   * Set up automatic flushing
   */
  private setupAutoFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(async () => {
      await this.flush();
    }, this.config?.flushInterval || 30000);

    // Flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flush();
      this.endSession();
    });
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate unique user ID
   */
  private generateUserId(): string {
    let userId = localStorage.getItem('aquachain_user_id');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('aquachain_user_id', userId);
    }
    return userId;
  }

  /**
   * Detect device type
   */
  private detectDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    const userAgent = navigator.userAgent;
    
    if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
      return 'tablet';
    }
    
    if (/mobile|iphone|ipod|android|blackberry|opera|mini|windows\sce|palm|smartphone|iemobile/i.test(userAgent)) {
      return 'mobile';
    }
    
    return 'desktop';
  }

  /**
   * Detect traffic source
   */
  private detectTrafficSource(): { source: 'direct' | 'organic' | 'referral' | 'social' | 'email' | 'paid'; campaign?: string; medium?: string } {
    const urlParams = new URLSearchParams(window.location.search);
    const referrer = document.referrer;

    // Check for UTM parameters
    const utmSource = urlParams.get('utm_source');
    const utmCampaign = urlParams.get('utm_campaign');
    const utmMedium = urlParams.get('utm_medium');

    if (utmSource) {
      // Map UTM source to our traffic source types
      let mappedSource: 'direct' | 'organic' | 'referral' | 'social' | 'email' | 'paid' = 'referral';
      
      if (['google', 'bing', 'yahoo', 'duckduckgo'].includes(utmSource.toLowerCase())) {
        mappedSource = 'organic';
      } else if (['facebook', 'twitter', 'linkedin', 'instagram', 'youtube'].includes(utmSource.toLowerCase())) {
        mappedSource = 'social';
      } else if (utmSource.toLowerCase().includes('email') || utmSource.toLowerCase().includes('newsletter')) {
        mappedSource = 'email';
      } else if (utmMedium?.toLowerCase().includes('paid') || utmMedium?.toLowerCase().includes('cpc')) {
        mappedSource = 'paid';
      }
      
      return {
        source: mappedSource,
        campaign: utmCampaign || undefined,
        medium: utmMedium || undefined
      };
    }

    // Check referrer
    if (referrer) {
      if (referrer.includes('google.com')) return { source: 'organic' };
      if (referrer.includes('facebook.com')) return { source: 'social' };
      if (referrer.includes('twitter.com')) return { source: 'social' };
      if (referrer.includes('linkedin.com')) return { source: 'social' };
      return { source: 'referral' };
    }

    return { source: 'direct' };
  }

  /**
   * Get current session duration in seconds
   */
  private getSessionDuration(): number {
    if (!this.sessionInfo) return 0;
    
    const startTime = new Date(this.sessionInfo.startTime).getTime();
    const currentTime = Date.now();
    return Math.floor((currentTime - startTime) / 1000);
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }

    this.flush();
    this.endSession();
    this.isInitialized = false;
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService();
export default analyticsService;