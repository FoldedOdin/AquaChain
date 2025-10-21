import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import analyticsService, { AnalyticsEvent, UserAttributes } from '../services/analyticsService';
import googleAnalyticsService, { GA4UserProperties } from '../services/googleAnalyticsService';

// Analytics context interface
interface AnalyticsContextType {
  isInitialized: boolean;
  trackEvent: (event: AnalyticsEvent) => Promise<void>;
  trackPageView: (pageName: string, additionalAttributes?: Record<string, string>) => Promise<void>;
  trackInteraction: (
    elementType: string,
    elementId: string,
    action: string,
    additionalAttributes?: Record<string, string>
  ) => Promise<void>;
  trackConversion: (
    conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
    value?: number,
    additionalAttributes?: Record<string, string>
  ) => Promise<void>;
  setUserAttributes: (attributes: UserAttributes) => void;
  setUserRole: (role: 'consumer' | 'technician' | 'admin') => void;
  // Google Analytics specific methods
  trackFormSubmission: (
    formName: string,
    formType: 'contact' | 'signup' | 'login' | 'newsletter',
    success: boolean,
    additionalParams?: Record<string, any>
  ) => void;
  trackOutboundLink: (url: string, linkText?: string) => void;
  setUserId: (userId: string) => void;
}

// Create context
const AnalyticsContext = createContext<AnalyticsContextType | undefined>(undefined);

// Provider props
interface AnalyticsProviderProps {
  children: ReactNode;
  config?: {
    applicationId?: string;
    region?: string;
    enableDebugMode?: boolean;
    googleAnalyticsId?: string;
  };
}

// Analytics provider component
export const AnalyticsProvider: React.FC<AnalyticsProviderProps> = ({ 
  children, 
  config = {} 
}) => {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initializeAnalytics = async () => {
      try {
        // Get configuration from environment variables or props
        const analyticsConfig = {
          applicationId: config.applicationId || process.env.REACT_APP_PINPOINT_APPLICATION_ID || 'default-app-id',
          region: config.region || process.env.REACT_APP_AWS_REGION || 'us-east-1',
          enableDebugMode: config.enableDebugMode ?? process.env.NODE_ENV === 'development',
          credentials: process.env.REACT_APP_AWS_ACCESS_KEY_ID ? {
            accessKeyId: process.env.REACT_APP_AWS_ACCESS_KEY_ID,
            secretAccessKey: process.env.REACT_APP_AWS_SECRET_ACCESS_KEY || ''
          } : undefined
        };

        // Initialize AWS Pinpoint only if analytics is enabled
        const analyticsEnabled = process.env.REACT_APP_ENABLE_ANALYTICS !== 'false';
        if (analyticsEnabled && analyticsConfig.credentials) {
          await analyticsService.initialize(analyticsConfig);
        }

        // Initialize Google Analytics 4
        const googleAnalyticsId = config.googleAnalyticsId || process.env.REACT_APP_GA4_MEASUREMENT_ID;
        if (googleAnalyticsId) {
          await googleAnalyticsService.initialize(googleAnalyticsId, {
            debugMode: config.enableDebugMode ?? process.env.NODE_ENV === 'development'
          });
        }

        setIsInitialized(true);

        // Track initial page view in both services
        const pageViewAttributes = {
          initial_load: 'true',
          user_agent: navigator.userAgent,
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          viewport_size: `${window.innerWidth}x${window.innerHeight}`
        };

        await analyticsService.trackPageView('landing_page', pageViewAttributes);
        
        if (googleAnalyticsService.isReady()) {
          googleAnalyticsService.trackPageView('Landing Page', pageViewAttributes);
        }

        // Set up campaign attribution tracking
        const urlParams = new URLSearchParams(window.location.search);
        const utmSource = urlParams.get('utm_source');
        const utmMedium = urlParams.get('utm_medium');
        const utmCampaign = urlParams.get('utm_campaign');
        const utmContent = urlParams.get('utm_content');
        const utmTerm = urlParams.get('utm_term');

        if (utmSource && utmMedium && utmCampaign && googleAnalyticsService.isReady()) {
          googleAnalyticsService.trackCampaignAttribution(
            utmSource,
            utmMedium,
            utmCampaign,
            utmContent || undefined,
            utmTerm || undefined
          );
        }

      } catch (error) {
        console.error('Failed to initialize analytics:', error);
        // Continue without analytics rather than breaking the app
        setIsInitialized(false);
      }
    };

    initializeAnalytics();

    // Cleanup on unmount
    return () => {
      analyticsService.destroy();
    };
  }, [config]);

  // Enhanced tracking methods that use both services
  const enhancedTrackPageView = async (pageName: string, additionalAttributes?: Record<string, string>) => {
    await analyticsService.trackPageView(pageName, additionalAttributes);
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.trackPageView(pageName, additionalAttributes);
    }
  };

  const enhancedTrackInteraction = async (
    elementType: string,
    elementId: string,
    action: string,
    additionalAttributes?: Record<string, string>
  ) => {
    await analyticsService.trackInteraction(elementType, elementId, action, additionalAttributes);
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.trackInteraction(elementType, elementId, action, additionalAttributes);
    }
  };

  const enhancedTrackConversion = async (
    conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
    value?: number,
    additionalAttributes?: Record<string, string>
  ) => {
    await analyticsService.trackConversion(conversionType, value, additionalAttributes);
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.trackConversion(conversionType, value, additionalAttributes);
    }
  };

  const enhancedSetUserAttributes = (attributes: UserAttributes) => {
    analyticsService.setUserAttributes(attributes);
    
    if (googleAnalyticsService.isReady()) {
      const ga4Properties: GA4UserProperties = {
        user_role: attributes.role,
        device_type: attributes.deviceType,
        preferred_language: attributes.preferences?.language,
        location_country: attributes.location?.country,
        location_region: attributes.location?.region
      };
      googleAnalyticsService.setUserProperties(ga4Properties);
    }
  };

  const enhancedSetUserRole = (role: 'consumer' | 'technician' | 'admin') => {
    analyticsService.setUserRole(role);
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.setUserProperties({ user_role: role });
    }
  };

  const enhancedSetUserId = (userId: string) => {
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.setUserId(userId);
    }
  };

  // Context value
  const contextValue: AnalyticsContextType = {
    isInitialized,
    trackEvent: analyticsService.trackEvent.bind(analyticsService),
    trackPageView: enhancedTrackPageView,
    trackInteraction: enhancedTrackInteraction,
    trackConversion: enhancedTrackConversion,
    setUserAttributes: enhancedSetUserAttributes,
    setUserRole: enhancedSetUserRole,
    trackFormSubmission: googleAnalyticsService.trackFormSubmission.bind(googleAnalyticsService),
    trackOutboundLink: googleAnalyticsService.trackOutboundLink.bind(googleAnalyticsService),
    setUserId: enhancedSetUserId
  };

  return (
    <AnalyticsContext.Provider value={contextValue}>
      {children}
    </AnalyticsContext.Provider>
  );
};

// Custom hook to use analytics
export const useAnalytics = (): AnalyticsContextType => {
  const context = useContext(AnalyticsContext);
  
  if (context === undefined) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  
  return context;
};

// Higher-order component for automatic page view tracking
export const withAnalytics = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  pageName: string
) => {
  const WithAnalyticsComponent: React.FC<P> = (props) => {
    const { trackPageView } = useAnalytics();

    useEffect(() => {
      trackPageView(pageName);
    }, [trackPageView]);

    return <WrappedComponent {...props} />;
  };

  WithAnalyticsComponent.displayName = `withAnalytics(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return WithAnalyticsComponent;
};

// Hook for tracking interactions with automatic element detection
export const useInteractionTracking = () => {
  const { trackInteraction } = useAnalytics();

  const trackClick = (event: React.MouseEvent<HTMLElement>, additionalAttributes?: Record<string, string>) => {
    const element = event.currentTarget;
    const elementType = element.tagName.toLowerCase();
    const elementId = element.id || element.className || 'unknown';
    
    trackInteraction(elementType, elementId, 'click', {
      ...additionalAttributes,
      text_content: element.textContent?.slice(0, 100) || '',
      element_position: `${event.clientX},${event.clientY}`
    });
  };

  const trackHover = (event: React.MouseEvent<HTMLElement>, additionalAttributes?: Record<string, string>) => {
    const element = event.currentTarget;
    const elementType = element.tagName.toLowerCase();
    const elementId = element.id || element.className || 'unknown';
    
    trackInteraction(elementType, elementId, 'hover', additionalAttributes);
  };

  const trackFocus = (event: React.FocusEvent<HTMLElement>, additionalAttributes?: Record<string, string>) => {
    const element = event.currentTarget;
    const elementType = element.tagName.toLowerCase();
    const elementId = element.id || element.className || 'unknown';
    
    trackInteraction(elementType, elementId, 'focus', additionalAttributes);
  };

  return {
    trackClick,
    trackHover,
    trackFocus,
    trackInteraction
  };
};

// Hook for scroll tracking
export const useScrollTracking = () => {
  const { trackEvent } = useAnalytics();
  const [scrollDepth, setScrollDepth] = useState(0);
  const [milestones, setMilestones] = useState<Set<number>>(new Set());

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = Math.round((scrollTop / docHeight) * 100);

      setScrollDepth(scrollPercent);

      // Track scroll milestones (25%, 50%, 75%, 100%)
      const milestone = Math.floor(scrollPercent / 25) * 25;
      if (milestone > 0 && !milestones.has(milestone)) {
        setMilestones(prev => new Set(Array.from(prev).concat([milestone])));
        
        trackEvent({
          eventType: 'scroll_depth',
          attributes: {
            page_url: window.location.href,
            milestone: milestone.toString()
          },
          metrics: {
            scroll_depth: scrollPercent,
            time_to_milestone: performance.now()
          }
        });
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [trackEvent, milestones]);

  return { scrollDepth };
};

export default AnalyticsContext;