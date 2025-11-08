import { useCallback, useEffect, useRef } from 'react';
import conversionTrackingService, { FunnelAnalysis, UserSession } from '../services/conversionTrackingService';
import { useAnalytics } from '../contexts/AnalyticsContext';

// Hook for conversion tracking
export const useConversionTracking = () => {
  const { trackConversion: analyticsTrackConversion } = useAnalytics();
  const lastScrollDepth = useRef(0);

  // Track conversion with both services
  const trackConversion = useCallback(
    (
      conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
      value?: number,
      additionalAttributes?: Record<string, any>
    ) => {
      // Track in conversion service (includes journey mapping)
      conversionTrackingService.trackConversion(conversionType, value, additionalAttributes);
      
      // Track in analytics service (AWS Pinpoint + GA4)
      analyticsTrackConversion(conversionType, value?.toString(), additionalAttributes);
    },
    [analyticsTrackConversion]
  );

  // Track page view with journey context
  const trackPageView = useCallback((pageName: string, additionalAttributes?: Record<string, any>) => {
    conversionTrackingService.trackPageView(pageName, additionalAttributes);
  }, []);

  // Track user interaction with journey context
  const trackInteraction = useCallback(
    (
      elementType: string,
      elementId: string,
      action: string,
      additionalAttributes?: Record<string, any>
    ) => {
      conversionTrackingService.trackInteraction(elementType, elementId, action, additionalAttributes);
    },
    []
  );

  // Track form interactions
  const trackFormInteraction = useCallback(
    (
      formName: string,
      action: 'focus' | 'input' | 'submit' | 'error' | 'success',
      fieldName?: string,
      additionalData?: Record<string, any>
    ) => {
      conversionTrackingService.trackFormInteraction(formName, action, fieldName, additionalData);
    },
    []
  );

  // Get funnel analysis
  const getFunnelAnalysis = useCallback((): FunnelAnalysis => {
    return conversionTrackingService.getFunnelAnalysis();
  }, []);

  // Get user journey
  const getUserJourney = useCallback((): UserSession | null => {
    return conversionTrackingService.getUserJourney();
  }, []);

  return {
    trackConversion,
    trackPageView,
    trackInteraction,
    trackFormInteraction,
    getFunnelAnalysis,
    getUserJourney
  };
};

// Hook for automatic scroll tracking
export const useScrollTracking = () => {
  const scrollDepthRef = useRef(0);
  const milestonesRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = Math.round((scrollTop / docHeight) * 100);

      scrollDepthRef.current = scrollPercent;

      // Track milestones
      const milestone = Math.floor(scrollPercent / 25) * 25;
      if (milestone > 0 && !milestonesRef.current.has(milestone)) {
        milestonesRef.current.add(milestone);
        conversionTrackingService.trackScrollDepth(scrollPercent);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return { scrollDepth: scrollDepthRef.current };
};

// Hook for form tracking
export const useFormTracking = (formName: string) => {
  const { trackFormInteraction } = useConversionTracking();

  const trackFieldFocus = useCallback(
    (fieldName: string) => {
      trackFormInteraction(formName, 'focus', fieldName);
    },
    [formName, trackFormInteraction]
  );

  const trackFieldInput = useCallback(
    (fieldName: string, value?: string) => {
      trackFormInteraction(formName, 'input', fieldName, {
        field_value_length: value?.length || 0,
        has_value: Boolean(value)
      });
    },
    [formName, trackFormInteraction]
  );

  const trackFormSubmit = useCallback(
    (success: boolean, errorMessage?: string) => {
      trackFormInteraction(formName, success ? 'success' : 'error', undefined, {
        success,
        error_message: errorMessage
      });
    },
    [formName, trackFormInteraction]
  );

  const trackFormValidation = useCallback(
    (fieldName: string, isValid: boolean, errorMessage?: string) => {
      trackFormInteraction(formName, 'input', fieldName, {
        validation_passed: isValid,
        validation_error: errorMessage
      });
    },
    [formName, trackFormInteraction]
  );

  return {
    trackFieldFocus,
    trackFieldInput,
    trackFormSubmit,
    trackFormValidation
  };
};

// Hook for button/CTA tracking
export const useCTATracking = () => {
  const { trackInteraction } = useConversionTracking();

  const trackCTAClick = useCallback(
    (ctaName: string, ctaType: 'primary' | 'secondary' | 'tertiary', additionalData?: Record<string, any>) => {
      trackInteraction('button', ctaName, 'click', {
        cta_type: ctaType,
        cta_position: additionalData?.position || 'unknown',
        ...additionalData
      });
    },
    [trackInteraction]
  );

  const trackCTAHover = useCallback(
    (ctaName: string, ctaType: 'primary' | 'secondary' | 'tertiary') => {
      trackInteraction('button', ctaName, 'hover', {
        cta_type: ctaType
      });
    },
    [trackInteraction]
  );

  return {
    trackCTAClick,
    trackCTAHover
  };
};

// Hook for section visibility tracking
export const useSectionTracking = (sectionName: string) => {
  const sectionRef = useRef<HTMLElement>(null);
  const { trackInteraction } = useConversionTracking();
  const hasTrackedView = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasTrackedView.current) {
            hasTrackedView.current = true;
            trackInteraction('section', sectionName, 'view', {
              intersection_ratio: entry.intersectionRatio,
              viewport_position: entry.boundingClientRect.top
            });
          }
        });
      },
      {
        threshold: 0.5, // Track when 50% of section is visible
        rootMargin: '0px 0px -10% 0px' // Trigger slightly before section is fully visible
      }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [sectionName, trackInteraction]);

  return { sectionRef };
};

// Hook for A/B test tracking (will be used in next subtask)
export const useABTestTracking = () => {
  const { trackInteraction } = useConversionTracking();

  const trackVariantView = useCallback(
    (testName: string, variantName: string) => {
      trackInteraction('ab_test', testName, 'variant_view', {
        test_name: testName,
        variant_name: variantName
      });
    },
    [trackInteraction]
  );

  const trackVariantConversion = useCallback(
    (testName: string, variantName: string, conversionType: string) => {
      trackInteraction('ab_test', testName, 'variant_conversion', {
        test_name: testName,
        variant_name: variantName,
        conversion_type: conversionType
      });
    },
    [trackInteraction]
  );

  return {
    trackVariantView,
    trackVariantConversion
  };
};

export default useConversionTracking;