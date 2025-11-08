// Google Analytics 4 service for marketing insights
declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

// GA4 event parameters
export interface GA4Event {
  event_name: string;
  event_category?: string;
  event_label?: string;
  value?: number;
  currency?: string;
  custom_parameters?: Record<string, any>;
}

// Enhanced ecommerce parameters
export interface GA4EcommerceEvent {
  transaction_id?: string;
  value?: number;
  currency?: string;
  items?: GA4Item[];
  coupon?: string;
  shipping?: number;
  tax?: number;
}

export interface GA4Item {
  item_id: string;
  item_name: string;
  category: string;
  quantity?: number;
  price?: number;
  currency?: string;
  variant?: string;
}

// User properties for audience segmentation
export interface GA4UserProperties {
  user_role?: 'consumer' | 'technician' | 'admin';
  device_type?: 'mobile' | 'tablet' | 'desktop';
  user_segment?: string;
  subscription_status?: string;
  registration_date?: string;
  last_login?: string;
  preferred_language?: string;
  location_country?: string;
  location_region?: string;
}

// Conversion goals configuration
export interface ConversionGoal {
  name: string;
  event_name: string;
  value?: number;
  currency?: string;
  conditions?: Record<string, any>;
}

class GoogleAnalyticsService {
  private measurementId: string | null = null;
  private isInitialized = false;
  private debugMode = false;
  private conversionGoals: ConversionGoal[] = [];

  /**
   * Initialize Google Analytics 4
   */
  async initialize(measurementId: string, options: { debugMode?: boolean } = {}): Promise<void> {
    try {
      this.measurementId = measurementId;
      this.debugMode = options.debugMode || process.env.NODE_ENV === 'development';

      // Load gtag script
      await this.loadGtagScript();

      // Configure GA4
      window.gtag('config', measurementId, {
        // Enhanced measurement settings
        enhanced_measurement: true,
        page_title: document.title,
        page_location: window.location.href,
        
        // Privacy settings
        anonymize_ip: true,
        allow_google_signals: true,
        allow_ad_personalization_signals: false,
        
        // Custom settings
        custom_map: {
          custom_dimension_1: 'user_role',
          custom_dimension_2: 'device_type',
          custom_dimension_3: 'traffic_source',
          custom_dimension_4: 'user_segment'
        },
        
        // Debug mode
        debug_mode: this.debugMode
      });

      // Set up default conversion goals
      this.setupConversionGoals();

      this.isInitialized = true;

      if (this.debugMode) {
        console.log('Google Analytics 4 initialized:', measurementId);
      }
    } catch (error) {
      console.error('Failed to initialize Google Analytics 4:', error);
      throw error;
    }
  }

  /**
   * Track page view
   */
  trackPageView(pageName: string, additionalParams?: Record<string, any>): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'page_view', {
      page_title: pageName,
      page_location: window.location.href,
      page_referrer: document.referrer,
      ...additionalParams
    });

    if (this.debugMode) {
      console.log('GA4 Page View:', { pageName, ...additionalParams });
    }
  }

  /**
   * Track custom event
   */
  trackEvent(eventName: string, parameters?: Record<string, any>): void {
    if (!this.isInitialized) return;

    window.gtag('event', eventName, {
      event_category: 'engagement',
      event_label: window.location.pathname,
      ...parameters
    });

    if (this.debugMode) {
      console.log('GA4 Event:', { eventName, parameters });
    }
  }

  /**
   * Track conversion event
   */
  trackConversion(
    conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
    value?: number,
    additionalParams?: Record<string, any>
  ): void {
    if (!this.isInitialized) return;

    const conversionGoal = this.conversionGoals.find(goal => 
      goal.name === conversionType
    );

    const eventName = conversionGoal?.event_name || `conversion_${conversionType}`;
    const eventValue = value || conversionGoal?.value || 1;

    window.gtag('event', eventName, {
      event_category: 'conversion',
      event_label: conversionType,
      value: eventValue,
      currency: 'USD',
      conversion_type: conversionType,
      page_location: window.location.href,
      ...additionalParams
    });

    // Also track as a conversion goal
    window.gtag('event', 'conversion', {
      send_to: `${this.measurementId}/${eventName}`,
      value: eventValue,
      currency: 'USD'
    });

    if (this.debugMode) {
      console.log('GA4 Conversion:', { conversionType, eventName, value: eventValue });
    }
  }

  /**
   * Track user interaction
   */
  trackInteraction(
    elementType: string,
    elementId: string,
    action: string,
    additionalParams?: Record<string, any>
  ): void {
    if (!this.isInitialized) return;

    window.gtag('event', action, {
      event_category: 'interaction',
      event_label: `${elementType}_${elementId}`,
      element_type: elementType,
      element_id: elementId,
      page_location: window.location.href,
      ...additionalParams
    });

    if (this.debugMode) {
      console.log('GA4 Interaction:', { elementType, elementId, action });
    }
  }

  /**
   * Track scroll depth
   */
  trackScrollDepth(percentage: number): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'scroll', {
      event_category: 'engagement',
      event_label: `${percentage}%`,
      scroll_depth: percentage,
      page_location: window.location.href
    });
  }

  /**
   * Track form submission
   */
  trackFormSubmission(
    formName: string,
    formType: 'contact' | 'signup' | 'login' | 'newsletter',
    success: boolean,
    additionalParams?: Record<string, any>
  ): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'form_submit', {
      event_category: 'form',
      event_label: formName,
      form_name: formName,
      form_type: formType,
      form_success: success,
      page_location: window.location.href,
      ...additionalParams
    });

    if (success && (formType === 'signup' || formType === 'contact')) {
      this.trackConversion(
        formType === 'signup' ? 'signup' : 'contact_form',
        undefined,
        { form_name: formName }
      );
    }
  }

  /**
   * Track video interaction
   */
  trackVideoInteraction(
    videoTitle: string,
    action: 'play' | 'pause' | 'complete' | 'progress',
    progress?: number
  ): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'video_' + action, {
      event_category: 'video',
      event_label: videoTitle,
      video_title: videoTitle,
      video_current_time: progress,
      page_location: window.location.href
    });
  }

  /**
   * Track file download
   */
  trackDownload(fileName: string, fileType: string): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'file_download', {
      event_category: 'download',
      event_label: fileName,
      file_name: fileName,
      file_extension: fileType,
      page_location: window.location.href
    });
  }

  /**
   * Track outbound link clicks
   */
  trackOutboundLink(url: string, linkText?: string): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'click', {
      event_category: 'outbound',
      event_label: url,
      link_url: url,
      link_text: linkText,
      page_location: window.location.href
    });
  }

  /**
   * Set user properties for audience segmentation
   */
  setUserProperties(properties: GA4UserProperties): void {
    if (!this.isInitialized) return;

    // Set user properties
    Object.entries(properties).forEach(([key, value]) => {
      window.gtag('set', { [key]: value });
    });

    // Set custom dimensions
    const customDimensions: Record<string, any> = {};
    
    if (properties.user_role) {
      customDimensions.custom_dimension_1 = properties.user_role;
    }
    
    if (properties.device_type) {
      customDimensions.custom_dimension_2 = properties.device_type;
    }
    
    if (properties.user_segment) {
      customDimensions.custom_dimension_4 = properties.user_segment;
    }

    if (Object.keys(customDimensions).length > 0) {
      window.gtag('config', this.measurementId!, customDimensions);
    }

    if (this.debugMode) {
      console.log('GA4 User Properties:', properties);
    }
  }

  /**
   * Set user ID for cross-device tracking
   */
  setUserId(userId: string): void {
    if (!this.isInitialized) return;

    window.gtag('config', this.measurementId!, {
      user_id: userId
    });

    if (this.debugMode) {
      console.log('GA4 User ID set:', userId);
    }
  }

  /**
   * Track enhanced ecommerce events
   */
  trackEcommerceEvent(
    eventName: 'purchase' | 'add_to_cart' | 'remove_from_cart' | 'begin_checkout',
    ecommerceData: GA4EcommerceEvent
  ): void {
    if (!this.isInitialized) return;

    window.gtag('event', eventName, {
      currency: ecommerceData.currency || 'USD',
      value: ecommerceData.value || 0,
      transaction_id: ecommerceData.transaction_id,
      items: ecommerceData.items || [],
      coupon: ecommerceData.coupon,
      shipping: ecommerceData.shipping,
      tax: ecommerceData.tax
    });

    if (this.debugMode) {
      console.log('GA4 Ecommerce Event:', { eventName, ecommerceData });
    }
  }

  /**
   * Create audience segments
   */
  createAudience(audienceName: string, conditions: Record<string, any>): void {
    if (!this.isInitialized) return;

    // Set audience membership
    window.gtag('event', 'join_group', {
      group_id: audienceName,
      event_category: 'audience',
      ...conditions
    });

    if (this.debugMode) {
      console.log('GA4 Audience Created:', { audienceName, conditions });
    }
  }

  /**
   * Track campaign attribution
   */
  trackCampaignAttribution(
    source: string,
    medium: string,
    campaign: string,
    content?: string,
    term?: string
  ): void {
    if (!this.isInitialized) return;

    window.gtag('event', 'campaign_details', {
      campaign_source: source,
      campaign_medium: medium,
      campaign_name: campaign,
      campaign_content: content,
      campaign_term: term,
      event_category: 'attribution'
    });

    // Set traffic source custom dimension
    window.gtag('set', { custom_dimension_3: source });
  }

  /**
   * Load gtag script dynamically
   */
  private async loadGtagScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check if gtag is already loaded
      if (typeof window.gtag === 'function') {
        resolve();
        return;
      }

      // Initialize dataLayer
      window.dataLayer = window.dataLayer || [];
      window.gtag = function() {
        window.dataLayer.push(arguments);
      };

      // Set initial timestamp
      window.gtag('js', new Date());

      // Load the script
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${this.measurementId}`;
      
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Analytics script'));
      
      document.head.appendChild(script);
    });
  }

  /**
   * Set up default conversion goals
   */
  private setupConversionGoals(): void {
    this.conversionGoals = [
      {
        name: 'signup',
        event_name: 'sign_up',
        value: 10,
        currency: 'USD'
      },
      {
        name: 'login',
        event_name: 'login',
        value: 5,
        currency: 'USD'
      },
      {
        name: 'demo_view',
        event_name: 'view_demo',
        value: 3,
        currency: 'USD'
      },
      {
        name: 'contact_form',
        event_name: 'generate_lead',
        value: 15,
        currency: 'USD'
      },
      {
        name: 'newsletter_signup',
        event_name: 'newsletter_signup',
        value: 2,
        currency: 'USD'
      }
    ];
  }

  /**
   * Get measurement ID
   */
  getMeasurementId(): string | null {
    return this.measurementId;
  }

  /**
   * Check if initialized
   */
  isReady(): boolean {
    return this.isInitialized;
  }
}

// Export singleton instance
export const googleAnalyticsService = new GoogleAnalyticsService();
export default googleAnalyticsService;