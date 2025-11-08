// Graceful Degradation Utilities
// Provides fallbacks and reduced functionality for offline scenarios

import React from 'react';
import { offlineQueueService } from '../services/offlineQueueService';

interface FeatureFlags {
  enableAnimations: boolean;
  enableParallax: boolean;
  enableWebGL: boolean;
  enableServiceWorker: boolean;
  enableBackgroundSync: boolean;
  enablePushNotifications: boolean;
}

interface OfflineCapabilities {
  canViewContent: boolean;
  canSubmitForms: boolean;
  canTrackAnalytics: boolean;
  canAuthenticate: boolean;
  canLoadImages: boolean;
}

class GracefulDegradationManager {
  private featureFlags: FeatureFlags;
  private offlineCapabilities: OfflineCapabilities;
  private isOnline: boolean = navigator.onLine;

  constructor() {
    this.featureFlags = this.detectFeatures();
    this.offlineCapabilities = this.getOfflineCapabilities();
    this.setupEventListeners();
  }

  private detectFeatures(): FeatureFlags {
    return {
      enableAnimations: this.supportsAnimations() && !this.prefersReducedMotion(),
      enableParallax: this.supportsIntersectionObserver(),
      enableWebGL: this.supportsWebGL(),
      enableServiceWorker: 'serviceWorker' in navigator,
      enableBackgroundSync: this.supportsBackgroundSync(),
      enablePushNotifications: this.supportsPushNotifications()
    };
  }

  private getOfflineCapabilities(): OfflineCapabilities {
    return {
      canViewContent: true, // Static content always available
      canSubmitForms: this.featureFlags.enableServiceWorker, // Can queue for later
      canTrackAnalytics: this.featureFlags.enableServiceWorker, // Can queue for later
      canAuthenticate: false, // Requires network
      canLoadImages: false // Requires network (unless cached)
    };
  }

  private setupEventListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnlineStateChange();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOfflineStateChange();
    });
  }

  private handleOnlineStateChange(): void {
    console.log('Back online - restoring full functionality');
    
    // Process offline queue
    if (this.featureFlags.enableServiceWorker) {
      offlineQueueService.processQueue();
    }

    // Dispatch custom event for components to react
    window.dispatchEvent(new CustomEvent('graceful-degradation-online', {
      detail: { capabilities: this.getOnlineCapabilities() }
    }));
  }

  private handleOfflineStateChange(): void {
    console.log('Gone offline - enabling graceful degradation');
    
    // Dispatch custom event for components to react
    window.dispatchEvent(new CustomEvent('graceful-degradation-offline', {
      detail: { capabilities: this.offlineCapabilities }
    }));
  }

  private getOnlineCapabilities(): OfflineCapabilities {
    return {
      canViewContent: true,
      canSubmitForms: true,
      canTrackAnalytics: true,
      canAuthenticate: true,
      canLoadImages: true
    };
  }

  // Feature detection methods
  private supportsAnimations(): boolean {
    return CSS.supports('animation', 'none');
  }

  private prefersReducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  private supportsIntersectionObserver(): boolean {
    return 'IntersectionObserver' in window;
  }

  private supportsWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
    } catch (e) {
      return false;
    }
  }

  private supportsBackgroundSync(): boolean {
    return 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype;
  }

  private supportsPushNotifications(): boolean {
    return 'serviceWorker' in navigator && 'PushManager' in window;
  }

  // Public API
  public getFeatureFlags(): FeatureFlags {
    return { ...this.featureFlags };
  }

  public getCapabilities(): OfflineCapabilities {
    return this.isOnline ? this.getOnlineCapabilities() : { ...this.offlineCapabilities };
  }

  public isFeatureEnabled(feature: keyof FeatureFlags): boolean {
    return this.featureFlags[feature];
  }

  public canUseFeature(capability: keyof OfflineCapabilities): boolean {
    const capabilities = this.getCapabilities();
    return capabilities[capability];
  }

  public isOnlineMode(): boolean {
    return this.isOnline;
  }

  // Graceful API wrappers
  public async makeRequest(
    url: string,
    options: RequestInit = {},
    fallbackData?: any
  ): Promise<Response | null> {
    if (!this.isOnline) {
      console.log('Offline - queuing request for later:', url);
      
      if (this.featureFlags.enableServiceWorker && options.method !== 'GET') {
        await offlineQueueService.queueRequest(
          url,
          options.method || 'GET',
          (options.headers as Record<string, string>) || {},
          options.body,
          'api'
        );
      }
      
      if (fallbackData) {
        return new Response(JSON.stringify(fallbackData), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      return null;
    }

    try {
      return await fetch(url, options);
    } catch (error) {
      console.error('Network request failed:', error);
      
      if (fallbackData) {
        return new Response(JSON.stringify(fallbackData), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      return null;
    }
  }

  public async submitForm(
    formType: 'contact' | 'signup' | 'newsletter',
    formData: Record<string, any>
  ): Promise<{ success: boolean; queued?: boolean; message: string }> {
    if (!this.isOnline) {
      if (this.canUseFeature('canSubmitForms')) {
        await offlineQueueService.queueFormSubmission(formType, formData);
        return {
          success: true,
          queued: true,
          message: 'Form submitted! We\'ll process it when you\'re back online.'
        };
      } else {
        return {
          success: false,
          message: 'Unable to submit form while offline. Please try again when connected.'
        };
      }
    }

    // Online submission logic would go here
    return {
      success: true,
      message: 'Form submitted successfully!'
    };
  }

  public async trackEvent(
    eventType: string,
    eventData: Record<string, any>,
    userId?: string
  ): Promise<void> {
    if (!this.isOnline) {
      if (this.canUseFeature('canTrackAnalytics')) {
        await offlineQueueService.queueAnalyticsEvent(eventType, eventData, userId);
        console.log('Analytics event queued for offline sync:', eventType);
      }
      return;
    }

    // Online analytics tracking would go here
    console.log('Tracking event:', eventType, eventData);
  }

  // Image loading with fallbacks
  public getImageSrc(src: string, fallbackSrc?: string): string {
    if (!this.isOnline && !this.canUseFeature('canLoadImages')) {
      return fallbackSrc || '/images/placeholder.svg';
    }
    return src;
  }

  // Animation control based on capabilities
  public shouldEnableAnimation(animationType: 'basic' | 'parallax' | 'webgl'): boolean {
    if (!this.isOnline) {
      // Disable heavy animations when offline to save battery
      return animationType === 'basic' && this.featureFlags.enableAnimations;
    }

    switch (animationType) {
      case 'basic':
        return this.featureFlags.enableAnimations;
      case 'parallax':
        return this.featureFlags.enableParallax;
      case 'webgl':
        return this.featureFlags.enableWebGL;
      default:
        return false;
    }
  }

  // Content loading strategies
  public getContentLoadingStrategy(): 'eager' | 'lazy' | 'minimal' {
    if (!this.isOnline) {
      return 'minimal'; // Load only essential content
    }
    
    // Check connection quality if available
    const connection = (navigator as any).connection;
    if (connection) {
      if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
        return 'minimal';
      } else if (connection.effectiveType === '3g') {
        return 'lazy';
      }
    }
    
    return 'eager';
  }
}

// Singleton instance
export const gracefulDegradationManager = new GracefulDegradationManager();

// React hook for graceful degradation
export function useGracefulDegradation() {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);
  const [capabilities, setCapabilities] = React.useState(
    gracefulDegradationManager.getCapabilities()
  );

  React.useEffect(() => {
    const handleOnline = (event: CustomEvent) => {
      setIsOnline(true);
      setCapabilities(event.detail.capabilities);
    };

    const handleOffline = (event: CustomEvent) => {
      setIsOnline(false);
      setCapabilities(event.detail.capabilities);
    };

    window.addEventListener('graceful-degradation-online', handleOnline as EventListener);
    window.addEventListener('graceful-degradation-offline', handleOffline as EventListener);

    return () => {
      window.removeEventListener('graceful-degradation-online', handleOnline as EventListener);
      window.removeEventListener('graceful-degradation-offline', handleOffline as EventListener);
    };
  }, []);

  return {
    isOnline,
    capabilities,
    featureFlags: gracefulDegradationManager.getFeatureFlags(),
    canUseFeature: (feature: keyof OfflineCapabilities) => capabilities[feature],
    isFeatureEnabled: (feature: keyof FeatureFlags) => 
      gracefulDegradationManager.isFeatureEnabled(feature),
    shouldEnableAnimation: (type: 'basic' | 'parallax' | 'webgl') =>
      gracefulDegradationManager.shouldEnableAnimation(type),
    getContentLoadingStrategy: () => gracefulDegradationManager.getContentLoadingStrategy(),
    makeRequest: gracefulDegradationManager.makeRequest.bind(gracefulDegradationManager),
    submitForm: gracefulDegradationManager.submitForm.bind(gracefulDegradationManager),
    trackEvent: gracefulDegradationManager.trackEvent.bind(gracefulDegradationManager)
  };
}

