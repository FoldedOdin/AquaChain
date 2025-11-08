import { useState, useEffect, useCallback } from 'react';
import abTestingService, { ABTest, ABTestVariant, ABTestResult } from '../services/abTestingService';
import { useConversionTracking } from './useConversionTracking';

// Hook for A/B testing
export const useABTesting = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  const { trackInteraction } = useConversionTracking();

  useEffect(() => {
    const initializeABTesting = async () => {
      try {
        await abTestingService.initialize();
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize A/B testing:', error);
        setIsInitialized(false);
      }
    };

    initializeABTesting();
  }, []);

  const getVariant = useCallback((testId: string): ABTestVariant | null => {
    if (!isInitialized) return null;
    return abTestingService.getVariant(testId);
  }, [isInitialized]);

  const trackConversion = useCallback((
    testId: string,
    conversionType: string,
    value?: number,
    additionalAttributes?: Record<string, any>
  ) => {
    if (!isInitialized) return;
    abTestingService.trackConversion(testId, conversionType, value, additionalAttributes);
  }, [isInitialized]);

  const trackMetric = useCallback((
    testId: string,
    metricName: string,
    value: number,
    additionalAttributes?: Record<string, any>
  ) => {
    if (!isInitialized) return;
    abTestingService.trackMetric(testId, metricName, value, additionalAttributes);
  }, [isInitialized]);

  const getTestResults = useCallback((testId: string): ABTestResult[] | null => {
    if (!isInitialized) return null;
    return abTestingService.getTestResults(testId);
  }, [isInitialized]);

  const getActiveTests = useCallback((): ABTest[] => {
    if (!isInitialized) return [];
    return abTestingService.getActiveTests();
  }, [isInitialized]);

  return {
    isInitialized,
    getVariant,
    trackConversion,
    trackMetric,
    getTestResults,
    getActiveTests
  };
};

// Hook for specific A/B test
export const useABTest = (testId: string) => {
  const { isInitialized, getVariant, trackConversion, trackMetric } = useABTesting();
  const [variant, setVariant] = useState<ABTestVariant | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isInitialized) {
      const testVariant = getVariant(testId);
      setVariant(testVariant);
      setIsLoading(false);

      // Track variant view
      if (testVariant) {
        trackMetric(testId, 'variant_view', 1, {
          variant_id: testVariant.variantId,
          variant_name: testVariant.variantName
        });
      }
    }
  }, [isInitialized, testId, getVariant, trackMetric]);

  const trackTestConversion = useCallback((
    conversionType: string,
    value?: number,
    additionalAttributes?: Record<string, any>
  ) => {
    if (variant) {
      trackConversion(testId, conversionType, value, {
        ...additionalAttributes,
        variant_id: variant.variantId,
        variant_name: variant.variantName
      });
    }
  }, [testId, variant, trackConversion]);

  const trackTestMetric = useCallback((
    metricName: string,
    value: number,
    additionalAttributes?: Record<string, any>
  ) => {
    if (variant) {
      trackMetric(testId, metricName, value, {
        ...additionalAttributes,
        variant_id: variant.variantId,
        variant_name: variant.variantName
      });
    }
  }, [testId, variant, trackMetric]);

  return {
    variant,
    isLoading,
    isInTest: variant !== null,
    isControl: variant?.isControl || false,
    variantConfig: variant?.configuration || {},
    trackConversion: trackTestConversion,
    trackMetric: trackTestMetric
  };
};

// Hook for hero messaging A/B test
export const useHeroMessagingTest = () => {
  const { variant, isLoading, isInTest, variantConfig, trackConversion, trackMetric } = useABTest('hero_messaging_test');

  const getHeroContent = () => {
    if (!isInTest) {
      // Default content when not in test
      return {
        headline: 'Real-Time Water Quality You Can Trust',
        subheadline: 'Monitor your water quality with IoT sensors and blockchain-verified data',
        ctaText: 'Get Started'
      };
    }

    return {
      headline: variantConfig.headline || 'Real-Time Water Quality You Can Trust',
      subheadline: variantConfig.subheadline || 'Monitor your water quality with IoT sensors and blockchain-verified data',
      ctaText: variantConfig.ctaText || 'Get Started'
    };
  };

  const trackHeroInteraction = useCallback((action: string, element: string) => {
    trackMetric(`hero_${action}`, 1, { element });
  }, [trackMetric]);

  const trackHeroConversion = useCallback((conversionType: string) => {
    trackConversion(conversionType, undefined, { source: 'hero_section' });
  }, [trackConversion]);

  return {
    isLoading,
    isInTest,
    heroContent: getHeroContent(),
    trackHeroInteraction,
    trackHeroConversion
  };
};

// Hook for CTA button A/B test
export const useCTAButtonTest = () => {
  const { variant, isLoading, isInTest, variantConfig, trackConversion, trackMetric } = useABTest('cta_button_test');

  const getButtonStyles = () => {
    if (!isInTest) {
      // Default styles when not in test
      return {
        backgroundColor: '#06b6d4',
        hoverBackgroundColor: '#0891b2'
      };
    }

    return {
      backgroundColor: variantConfig.buttonColor || '#06b6d4',
      hoverBackgroundColor: variantConfig.buttonHoverColor || '#0891b2'
    };
  };

  const trackButtonClick = useCallback((buttonId: string, buttonText: string) => {
    trackMetric('button_click', 1, { 
      button_id: buttonId,
      button_text: buttonText 
    });
  }, [trackMetric]);

  const trackButtonConversion = useCallback((conversionType: string) => {
    trackConversion(conversionType, undefined, { source: 'cta_button' });
  }, [trackConversion]);

  return {
    isLoading,
    isInTest,
    buttonStyles: getButtonStyles(),
    trackButtonClick,
    trackButtonConversion
  };
};

// Hook for form A/B test
export const useFormABTest = (testId: string) => {
  const { variant, isLoading, isInTest, variantConfig, trackConversion, trackMetric } = useABTest(testId);

  const trackFormStart = useCallback(() => {
    trackMetric('form_start', 1);
  }, [trackMetric]);

  const trackFormField = useCallback((fieldName: string, action: 'focus' | 'blur' | 'change') => {
    trackMetric(`form_field_${action}`, 1, { field_name: fieldName });
  }, [trackMetric]);

  const trackFormSubmit = useCallback((success: boolean, errorMessage?: string) => {
    trackMetric('form_submit', 1, { success, error_message: errorMessage });
    
    if (success) {
      trackConversion('form_completion', undefined, { form_success: true });
    }
  }, [trackMetric, trackConversion]);

  const trackFormAbandonment = useCallback((lastField: string, timeSpent: number) => {
    trackMetric('form_abandonment', 1, { 
      last_field: lastField,
      time_spent: timeSpent 
    });
  }, [trackMetric]);

  return {
    variant,
    isLoading,
    isInTest,
    formConfig: variantConfig,
    trackFormStart,
    trackFormField,
    trackFormSubmit,
    trackFormAbandonment
  };
};

// Hook for pricing A/B test
export const usePricingABTest = () => {
  const { variant, isLoading, isInTest, variantConfig, trackConversion, trackMetric } = useABTest('pricing_test');

  const getPricingConfig = () => {
    if (!isInTest) {
      return {
        showPricing: false,
        priceDisplay: 'hidden',
        freeTrialDays: 30
      };
    }

    return {
      showPricing: variantConfig.showPricing || false,
      priceDisplay: variantConfig.priceDisplay || 'hidden',
      freeTrialDays: variantConfig.freeTrialDays || 30,
      monthlyPrice: variantConfig.monthlyPrice || 29,
      yearlyPrice: variantConfig.yearlyPrice || 290
    };
  };

  const trackPricingView = useCallback(() => {
    trackMetric('pricing_view', 1);
  }, [trackMetric]);

  const trackPricingInteraction = useCallback((action: string, planType?: string) => {
    trackMetric(`pricing_${action}`, 1, { plan_type: planType });
  }, [trackMetric]);

  return {
    isLoading,
    isInTest,
    pricingConfig: getPricingConfig(),
    trackPricingView,
    trackPricingInteraction
  };
};

// Hook for social proof A/B test
export const useSocialProofTest = () => {
  const { variant, isLoading, isInTest, variantConfig, trackMetric } = useABTest('social_proof_test');

  const getSocialProofConfig = () => {
    if (!isInTest) {
      return {
        showTestimonials: true,
        showUserCount: true,
        showTrustBadges: true
      };
    }

    return {
      showTestimonials: variantConfig.showTestimonials !== false,
      showUserCount: variantConfig.showUserCount !== false,
      showTrustBadges: variantConfig.showTrustBadges !== false,
      testimonialStyle: variantConfig.testimonialStyle || 'cards',
      userCountFormat: variantConfig.userCountFormat || 'exact'
    };
  };

  const trackSocialProofView = useCallback((element: string) => {
    trackMetric('social_proof_view', 1, { element });
  }, [trackMetric]);

  const trackSocialProofClick = useCallback((element: string, action: string) => {
    trackMetric('social_proof_click', 1, { element, action });
  }, [trackMetric]);

  return {
    isLoading,
    isInTest,
    socialProofConfig: getSocialProofConfig(),
    trackSocialProofView,
    trackSocialProofClick
  };
};

export default useABTesting;