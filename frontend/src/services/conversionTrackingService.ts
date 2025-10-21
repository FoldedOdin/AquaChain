// Conversion tracking and user journey mapping service
import analyticsService from './analyticsService';
import googleAnalyticsService from './googleAnalyticsService';

// User journey step interface
export interface JourneyStep {
  stepId: string;
  stepName: string;
  timestamp: string;
  pageUrl: string;
  elementInteracted?: string;
  timeSpent: number;
  scrollDepth?: number;
  exitPoint?: boolean;
}

// Conversion funnel stage
export interface FunnelStage {
  stageName: string;
  stageOrder: number;
  requiredActions: string[];
  completionRate?: number;
  averageTimeToComplete?: number;
  dropOffReasons?: string[];
}

// User session data
export interface UserSession {
  sessionId: string;
  userId?: string;
  startTime: string;
  endTime?: string;
  totalDuration?: number;
  pageViews: JourneyStep[];
  interactions: JourneyStep[];
  conversions: ConversionEvent[];
  trafficSource: string;
  deviceType: string;
  userAgent: string;
  exitPage?: string;
  bounced: boolean;
}

// Conversion event
export interface ConversionEvent {
  conversionId: string;
  conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup';
  timestamp: string;
  value?: number;
  funnelStage: string;
  timeToConversion: number;
  touchpoints: string[];
  attributes: Record<string, any>;
}

// Funnel analysis result
export interface FunnelAnalysis {
  totalUsers: number;
  stages: {
    stageName: string;
    users: number;
    conversionRate: number;
    dropOffRate: number;
    averageTime: number;
  }[];
  overallConversionRate: number;
  averageTimeToConvert: number;
  topDropOffPoints: string[];
}

class ConversionTrackingService {
  private currentSession: UserSession | null = null;
  private journeySteps: JourneyStep[] = [];
  private conversionFunnel: FunnelStage[] = [];
  private sessionStartTime: number = 0;
  private lastInteractionTime: number = 0;
  private scrollDepthMilestones: Set<number> = new Set();

  constructor() {
    this.initializeFunnel();
    this.startSession();
    this.setupEventListeners();
  }

  /**
   * Initialize conversion funnel stages
   */
  private initializeFunnel(): void {
    this.conversionFunnel = [
      {
        stageName: 'landing_page_view',
        stageOrder: 1,
        requiredActions: ['page_view']
      },
      {
        stageName: 'hero_engagement',
        stageOrder: 2,
        requiredActions: ['scroll_25', 'button_hover', 'animation_interaction']
      },
      {
        stageName: 'features_exploration',
        stageOrder: 3,
        requiredActions: ['features_scroll', 'feature_card_hover']
      },
      {
        stageName: 'auth_intent',
        stageOrder: 4,
        requiredActions: ['get_started_click', 'auth_modal_open']
      },
      {
        stageName: 'form_engagement',
        stageOrder: 5,
        requiredActions: ['form_focus', 'form_input']
      },
      {
        stageName: 'conversion',
        stageOrder: 6,
        requiredActions: ['signup_complete', 'login_complete']
      }
    ];
  }

  /**
   * Start a new user session
   */
  private startSession(): void {
    const sessionId = this.generateSessionId();
    this.sessionStartTime = Date.now();
    this.lastInteractionTime = this.sessionStartTime;

    this.currentSession = {
      sessionId,
      startTime: new Date().toISOString(),
      pageViews: [],
      interactions: [],
      conversions: [],
      trafficSource: this.detectTrafficSource(),
      deviceType: this.detectDeviceType(),
      userAgent: navigator.userAgent,
      bounced: true // Will be set to false if user interacts
    };

    // Track session start
    this.trackJourneyStep('session_start', 'Session Started', window.location.href);
  }

  /**
   * Track a step in the user journey
   */
  trackJourneyStep(
    stepId: string,
    stepName: string,
    pageUrl: string,
    elementInteracted?: string,
    additionalData?: Record<string, any>
  ): void {
    const now = Date.now();
    const timeSpent = now - this.lastInteractionTime;
    
    const journeyStep: JourneyStep = {
      stepId,
      stepName,
      timestamp: new Date().toISOString(),
      pageUrl,
      elementInteracted,
      timeSpent,
      scrollDepth: this.getCurrentScrollDepth(),
      exitPoint: false
    };

    this.journeySteps.push(journeyStep);
    
    if (this.currentSession) {
      if (stepId.includes('page_view')) {
        this.currentSession.pageViews.push(journeyStep);
      } else {
        this.currentSession.interactions.push(journeyStep);
        this.currentSession.bounced = false; // User interacted
      }
    }

    this.lastInteractionTime = now;

    // Track in analytics services
    this.trackInAnalytics('journey_step', {
      step_id: stepId,
      step_name: stepName,
      time_spent: timeSpent,
      scroll_depth: journeyStep.scrollDepth,
      ...additionalData
    });

    // Check funnel progression
    this.checkFunnelProgression(stepId);
  }

  /**
   * Track conversion event
   */
  trackConversion(
    conversionType: 'signup' | 'login' | 'demo_view' | 'contact_form' | 'newsletter_signup',
    value?: number,
    additionalAttributes?: Record<string, any>
  ): void {
    const conversionId = this.generateConversionId();
    const timeToConversion = Date.now() - this.sessionStartTime;
    const touchpoints = this.journeySteps.map(step => step.stepId);
    const currentStage = this.getCurrentFunnelStage();

    const conversionEvent: ConversionEvent = {
      conversionId,
      conversionType,
      timestamp: new Date().toISOString(),
      value,
      funnelStage: currentStage,
      timeToConversion: Math.floor(timeToConversion / 1000), // Convert to seconds
      touchpoints,
      attributes: {
        session_id: this.currentSession?.sessionId,
        traffic_source: this.currentSession?.trafficSource,
        device_type: this.currentSession?.deviceType,
        total_interactions: this.journeySteps.length,
        pages_visited: this.currentSession?.pageViews.length || 0,
        ...additionalAttributes
      }
    };

    if (this.currentSession) {
      this.currentSession.conversions.push(conversionEvent);
    }

    // Track in analytics services
    this.trackInAnalytics('conversion', {
      conversion_type: conversionType,
      conversion_id: conversionId,
      time_to_conversion: conversionEvent.timeToConversion,
      funnel_stage: currentStage,
      touchpoints_count: touchpoints.length,
      conversion_value: value || 0,
      ...additionalAttributes
    });

    // Track journey step for conversion
    this.trackJourneyStep(
      `conversion_${conversionType}`,
      `Conversion: ${conversionType}`,
      window.location.href,
      undefined,
      { conversion_id: conversionId, value }
    );
  }

  /**
   * Track page view with journey context
   */
  trackPageView(pageName: string, additionalAttributes?: Record<string, any>): void {
    this.trackJourneyStep(
      `page_view_${pageName.toLowerCase().replace(/\s+/g, '_')}`,
      `Page View: ${pageName}`,
      window.location.href,
      undefined,
      additionalAttributes
    );
  }

  /**
   * Track user interaction with journey context
   */
  trackInteraction(
    elementType: string,
    elementId: string,
    action: string,
    additionalAttributes?: Record<string, any>
  ): void {
    this.trackJourneyStep(
      `interaction_${action}_${elementType}`,
      `${action} on ${elementType}`,
      window.location.href,
      `${elementType}#${elementId}`,
      {
        element_type: elementType,
        element_id: elementId,
        action,
        ...additionalAttributes
      }
    );
  }

  /**
   * Track form interactions
   */
  trackFormInteraction(
    formName: string,
    action: 'focus' | 'input' | 'submit' | 'error' | 'success',
    fieldName?: string,
    additionalData?: Record<string, any>
  ): void {
    this.trackJourneyStep(
      `form_${action}_${formName}`,
      `Form ${action}: ${formName}`,
      window.location.href,
      fieldName ? `form[${formName}] field[${fieldName}]` : `form[${formName}]`,
      {
        form_name: formName,
        form_action: action,
        field_name: fieldName,
        ...additionalData
      }
    );
  }

  /**
   * Track scroll depth milestones
   */
  trackScrollDepth(percentage: number): void {
    const milestone = Math.floor(percentage / 25) * 25;
    
    if (milestone > 0 && !this.scrollDepthMilestones.has(milestone)) {
      this.scrollDepthMilestones.add(milestone);
      
      this.trackJourneyStep(
        `scroll_${milestone}`,
        `Scrolled ${milestone}%`,
        window.location.href,
        undefined,
        { scroll_percentage: percentage }
      );
    }
  }

  /**
   * Get current funnel analysis
   */
  getFunnelAnalysis(): FunnelAnalysis {
    // This would typically query stored data
    // For now, return mock analysis based on current session
    const totalUsers = 1; // Current session
    const completedStages = this.getCompletedFunnelStages();
    
    const stages = this.conversionFunnel.map((stage, index) => {
      const isCompleted = completedStages.includes(stage.stageName);
      const users = isCompleted ? 1 : 0;
      const conversionRate = index === 0 ? 100 : (users / totalUsers) * 100;
      const dropOffRate = 100 - conversionRate;
      const averageTime = this.getAverageTimeForStage(stage.stageName);

      return {
        stageName: stage.stageName,
        users,
        conversionRate,
        dropOffRate,
        averageTime
      };
    });

    const conversions = this.currentSession?.conversions.length || 0;
    const overallConversionRate = (conversions / totalUsers) * 100;
    const averageTimeToConvert = conversions > 0 
      ? this.currentSession!.conversions.reduce((sum, conv) => sum + conv.timeToConversion, 0) / conversions
      : 0;

    return {
      totalUsers,
      stages,
      overallConversionRate,
      averageTimeToConvert,
      topDropOffPoints: this.getTopDropOffPoints()
    };
  }

  /**
   * Get user journey summary
   */
  getUserJourney(): UserSession | null {
    return this.currentSession;
  }

  /**
   * End current session
   */
  endSession(): void {
    if (!this.currentSession) return;

    const now = new Date();
    const totalDuration = Date.now() - this.sessionStartTime;

    this.currentSession.endTime = now.toISOString();
    this.currentSession.totalDuration = Math.floor(totalDuration / 1000);
    this.currentSession.exitPage = window.location.href;

    // Mark last step as exit point
    if (this.journeySteps.length > 0) {
      this.journeySteps[this.journeySteps.length - 1].exitPoint = true;
    }

    // Track session end
    this.trackInAnalytics('session_end', {
      session_duration: this.currentSession.totalDuration,
      total_page_views: this.currentSession.pageViews.length,
      total_interactions: this.currentSession.interactions.length,
      total_conversions: this.currentSession.conversions.length,
      bounced: this.currentSession.bounced,
      exit_page: this.currentSession.exitPage
    });

    // Store session data (in a real app, this would go to a database)
    this.storeSessionData(this.currentSession);
  }

  /**
   * Set up event listeners for automatic tracking
   */
  private setupEventListeners(): void {
    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.trackJourneyStep('page_hidden', 'Page Hidden', window.location.href);
      } else {
        this.trackJourneyStep('page_visible', 'Page Visible', window.location.href);
      }
    });

    // Track page unload
    window.addEventListener('beforeunload', () => {
      this.endSession();
    });

    // Track scroll events
    let scrollTimeout: NodeJS.Timeout;
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const scrollPercentage = this.getCurrentScrollDepth();
        this.trackScrollDepth(scrollPercentage);
      }, 100);
    }, { passive: true });

    // Track clicks on external links
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a');
      
      if (link && link.href && !link.href.startsWith(window.location.origin)) {
        this.trackJourneyStep(
          'external_link_click',
          'External Link Click',
          window.location.href,
          link.href,
          { link_text: link.textContent, link_url: link.href }
        );
      }
    });
  }

  /**
   * Check funnel progression
   */
  private checkFunnelProgression(stepId: string): void {
    const currentStage = this.getCurrentFunnelStage();
    const nextStage = this.getNextFunnelStage(currentStage);
    
    if (nextStage) {
      const stageActions = nextStage.requiredActions;
      if (stageActions.some(action => stepId.includes(action))) {
        this.trackInAnalytics('funnel_progression', {
          from_stage: currentStage,
          to_stage: nextStage.stageName,
          step_id: stepId
        });
      }
    }
  }

  /**
   * Get current funnel stage
   */
  private getCurrentFunnelStage(): string {
    const completedStages = this.getCompletedFunnelStages();
    return completedStages[completedStages.length - 1] || 'landing_page_view';
  }

  /**
   * Get completed funnel stages
   */
  private getCompletedFunnelStages(): string[] {
    const completed: string[] = [];
    
    for (const stage of this.conversionFunnel) {
      const hasRequiredActions = stage.requiredActions.some(action =>
        this.journeySteps.some(step => step.stepId.includes(action))
      );
      
      if (hasRequiredActions) {
        completed.push(stage.stageName);
      } else {
        break; // Stop at first incomplete stage
      }
    }
    
    return completed;
  }

  /**
   * Get next funnel stage
   */
  private getNextFunnelStage(currentStage: string): FunnelStage | null {
    const currentIndex = this.conversionFunnel.findIndex(stage => stage.stageName === currentStage);
    return currentIndex >= 0 && currentIndex < this.conversionFunnel.length - 1
      ? this.conversionFunnel[currentIndex + 1]
      : null;
  }

  /**
   * Get average time for funnel stage
   */
  private getAverageTimeForStage(stageName: string): number {
    const stageSteps = this.journeySteps.filter(step => 
      step.stepId.includes(stageName.split('_')[0])
    );
    
    if (stageSteps.length === 0) return 0;
    
    const totalTime = stageSteps.reduce((sum, step) => sum + step.timeSpent, 0);
    return Math.floor(totalTime / stageSteps.length);
  }

  /**
   * Get top drop-off points
   */
  private getTopDropOffPoints(): string[] {
    // In a real implementation, this would analyze historical data
    return ['auth_modal_open', 'form_focus', 'form_submit'];
  }

  /**
   * Track in analytics services
   */
  private trackInAnalytics(eventType: string, attributes: Record<string, any>): void {
    // Track in AWS Pinpoint
    analyticsService.trackEvent({
      eventType,
      attributes: Object.fromEntries(
        Object.entries(attributes).map(([key, value]) => [key, String(value)])
      ),
      sessionId: this.currentSession?.sessionId
    });

    // Track in Google Analytics
    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.trackEvent(eventType, attributes);
    }
  }

  /**
   * Store session data
   */
  private storeSessionData(session: UserSession): void {
    try {
      // Store in localStorage for demo purposes
      // In production, this would be sent to a backend service
      const existingSessions = JSON.parse(localStorage.getItem('aquachain_sessions') || '[]');
      existingSessions.push(session);
      
      // Keep only last 10 sessions to avoid storage bloat
      const recentSessions = existingSessions.slice(-10);
      localStorage.setItem('aquachain_sessions', JSON.stringify(recentSessions));
    } catch (error) {
      console.warn('Failed to store session data:', error);
    }
  }

  /**
   * Utility methods
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateConversionId(): string {
    return `conversion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private detectTrafficSource(): string {
    const referrer = document.referrer;
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('utm_source')) {
      return urlParams.get('utm_source')!;
    }
    
    if (referrer.includes('google.com')) return 'google';
    if (referrer.includes('facebook.com')) return 'facebook';
    if (referrer.includes('twitter.com')) return 'twitter';
    if (referrer) return 'referral';
    
    return 'direct';
  }

  private detectDeviceType(): string {
    const userAgent = navigator.userAgent;
    
    if (/tablet|ipad/i.test(userAgent)) return 'tablet';
    if (/mobile|iphone|android/i.test(userAgent)) return 'mobile';
    
    return 'desktop';
  }

  private getCurrentScrollDepth(): number {
    const scrollTop = window.pageYOffset;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    return Math.round((scrollTop / docHeight) * 100);
  }
}

// Export singleton instance
export const conversionTrackingService = new ConversionTrackingService();
export default conversionTrackingService;