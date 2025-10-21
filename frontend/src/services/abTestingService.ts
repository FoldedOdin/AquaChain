// A/B Testing Framework for continuous optimization
import analyticsService from './analyticsService';
import googleAnalyticsService from './googleAnalyticsService';
import conversionTrackingService from './conversionTrackingService';

// A/B Test configuration
export interface ABTest {
  testId: string;
  testName: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  startDate: string;
  endDate?: string;
  trafficAllocation: number; // Percentage of users to include in test (0-100)
  variants: ABTestVariant[];
  targetMetrics: string[];
  segmentationRules?: SegmentationRule[];
  statisticalSignificance: {
    confidenceLevel: number; // e.g., 95
    minimumSampleSize: number;
    minimumDetectableEffect: number; // Minimum % change to detect
  };
}

// A/B Test variant
export interface ABTestVariant {
  variantId: string;
  variantName: string;
  description: string;
  trafficWeight: number; // Percentage of test traffic (should sum to 100 across variants)
  isControl: boolean;
  configuration: Record<string, any>; // Variant-specific configuration
}

// Segmentation rules for targeting
export interface SegmentationRule {
  attribute: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'not_in';
  value: any;
}

// Test result data
export interface ABTestResult {
  testId: string;
  variantId: string;
  variantName: string;
  participants: number;
  conversions: number;
  conversionRate: number;
  confidence: number;
  statisticalSignificance: boolean;
  metrics: Record<string, number>;
  startDate: string;
  endDate?: string;
}

// User assignment
export interface UserAssignment {
  userId: string;
  testId: string;
  variantId: string;
  assignmentDate: string;
  sessionId?: string;
}

// Statistical test result
export interface StatisticalTestResult {
  pValue: number;
  confidence: number;
  isSignificant: boolean;
  effect: number; // Percentage change
  confidenceInterval: {
    lower: number;
    upper: number;
  };
}

class ABTestingService {
  private activeTests: Map<string, ABTest> = new Map();
  private userAssignments: Map<string, UserAssignment[]> = new Map();
  private testResults: Map<string, ABTestResult[]> = new Map();
  private userId: string | null = null;
  private isInitialized = false;

  /**
   * Initialize A/B testing service
   */
  async initialize(userId?: string): Promise<void> {
    try {
      this.userId = userId || this.generateUserId();
      
      // Load active tests (in production, this would come from a backend)
      await this.loadActiveTests();
      
      // Load user assignments
      await this.loadUserAssignments();
      
      this.isInitialized = true;
      
      console.log('A/B Testing service initialized for user:', this.userId);
    } catch (error) {
      console.error('Failed to initialize A/B testing service:', error);
      throw error;
    }
  }

  /**
   * Create a new A/B test
   */
  createTest(testConfig: Omit<ABTest, 'testId'>): ABTest {
    const testId = this.generateTestId();
    const test: ABTest = {
      testId,
      ...testConfig
    };

    // Validate test configuration
    this.validateTestConfig(test);

    this.activeTests.set(testId, test);
    this.saveTestConfig(test);

    return test;
  }

  /**
   * Get variant for a user in a specific test
   */
  getVariant(testId: string): ABTestVariant | null {
    if (!this.isInitialized || !this.userId) {
      return null;
    }

    const test = this.activeTests.get(testId);
    if (!test || test.status !== 'active') {
      return null;
    }

    // Check if user is already assigned to this test
    const existingAssignment = this.getUserAssignment(testId);
    if (existingAssignment) {
      const variant = test.variants.find(v => v.variantId === existingAssignment.variantId);
      return variant || null;
    }

    // Check if user should be included in test
    if (!this.shouldIncludeUser(test)) {
      return null;
    }

    // Assign user to variant
    const variant = this.assignUserToVariant(test);
    if (variant) {
      this.trackVariantAssignment(testId, variant);
    }

    return variant;
  }

  /**
   * Track conversion for A/B test
   */
  trackConversion(
    testId: string,
    conversionType: string,
    value?: number,
    additionalAttributes?: Record<string, any>
  ): void {
    if (!this.isInitialized || !this.userId) return;

    const assignment = this.getUserAssignment(testId);
    if (!assignment) return;

    const test = this.activeTests.get(testId);
    if (!test) return;

    // Track conversion in analytics
    this.trackTestEvent('ab_test_conversion', {
      test_id: testId,
      test_name: test.testName,
      variant_id: assignment.variantId,
      variant_name: test.variants.find(v => v.variantId === assignment.variantId)?.variantName || 'unknown',
      conversion_type: conversionType,
      conversion_value: value || 0,
      ...additionalAttributes
    });

    // Update test results
    this.updateTestResults(testId, assignment.variantId, 'conversion', value);
  }

  /**
   * Track custom metric for A/B test
   */
  trackMetric(
    testId: string,
    metricName: string,
    value: number,
    additionalAttributes?: Record<string, any>
  ): void {
    if (!this.isInitialized || !this.userId) return;

    const assignment = this.getUserAssignment(testId);
    if (!assignment) return;

    const test = this.activeTests.get(testId);
    if (!test) return;

    // Track metric in analytics
    this.trackTestEvent('ab_test_metric', {
      test_id: testId,
      test_name: test.testName,
      variant_id: assignment.variantId,
      variant_name: test.variants.find(v => v.variantId === assignment.variantId)?.variantName || 'unknown',
      metric_name: metricName,
      metric_value: value,
      ...additionalAttributes
    });

    // Update test results
    this.updateTestResults(testId, assignment.variantId, metricName, value);
  }

  /**
   * Get test results with statistical analysis
   */
  getTestResults(testId: string): ABTestResult[] | null {
    const results = this.testResults.get(testId);
    if (!results) return null;

    // Calculate statistical significance
    return results.map(result => ({
      ...result,
      ...this.calculateStatisticalSignificance(testId, result.variantId)
    }));
  }

  /**
   * Get all active tests for current user
   */
  getActiveTests(): ABTest[] {
    return Array.from(this.activeTests.values()).filter(test => test.status === 'active');
  }

  /**
   * Get user's test assignments
   */
  getUserAssignments(): UserAssignment[] {
    if (!this.userId) return [];
    return this.userAssignments.get(this.userId) || [];
  }

  /**
   * End a test and calculate final results
   */
  endTest(testId: string): ABTestResult[] | null {
    const test = this.activeTests.get(testId);
    if (!test) return null;

    test.status = 'completed';
    test.endDate = new Date().toISOString();

    const results = this.getTestResults(testId);
    
    // Track test completion
    this.trackTestEvent('ab_test_completed', {
      test_id: testId,
      test_name: test.testName,
      duration_days: this.calculateTestDuration(test),
      total_participants: results?.reduce((sum, r) => sum + r.participants, 0) || 0
    });

    return results;
  }

  /**
   * Load active tests from storage/backend
   */
  private async loadActiveTests(): Promise<void> {
    try {
      // In production, this would fetch from backend
      // For demo, load from localStorage or use default tests
      const storedTests = localStorage.getItem('aquachain_ab_tests');
      
      if (storedTests) {
        const tests: ABTest[] = JSON.parse(storedTests);
        tests.forEach(test => {
          this.activeTests.set(test.testId, test);
        });
      } else {
        // Create default tests for demo
        this.createDefaultTests();
      }
    } catch (error) {
      console.warn('Failed to load A/B tests:', error);
      this.createDefaultTests();
    }
  }

  /**
   * Create default A/B tests for demo
   */
  private createDefaultTests(): void {
    // Hero messaging test
    const heroTest = this.createTest({
      testName: 'Hero Messaging Optimization',
      description: 'Test different hero section messaging to improve conversion rates',
      status: 'active',
      startDate: new Date().toISOString(),
      trafficAllocation: 100,
      variants: [
        {
          variantId: 'hero_control',
          variantName: 'Control - Original',
          description: 'Original hero messaging',
          trafficWeight: 50,
          isControl: true,
          configuration: {
            headline: 'Real-Time Water Quality You Can Trust',
            subheadline: 'Monitor your water quality with IoT sensors and blockchain-verified data',
            ctaText: 'Get Started'
          }
        },
        {
          variantId: 'hero_variant_a',
          variantName: 'Variant A - Benefit Focused',
          description: 'Focus on health benefits',
          trafficWeight: 50,
          isControl: false,
          configuration: {
            headline: 'Protect Your Family with Smart Water Monitoring',
            subheadline: 'Get instant alerts about water quality issues before they affect your health',
            ctaText: 'Protect My Family'
          }
        }
      ],
      targetMetrics: ['signup_conversion', 'demo_view', 'time_on_page'],
      statisticalSignificance: {
        confidenceLevel: 95,
        minimumSampleSize: 100,
        minimumDetectableEffect: 10
      }
    });

    // CTA button test
    const ctaTest = this.createTest({
      testName: 'CTA Button Color Test',
      description: 'Test different CTA button colors for better click-through rates',
      status: 'active',
      startDate: new Date().toISOString(),
      trafficAllocation: 80,
      variants: [
        {
          variantId: 'cta_blue',
          variantName: 'Blue CTA',
          description: 'Original blue CTA button',
          trafficWeight: 33.33,
          isControl: true,
          configuration: {
            buttonColor: '#06b6d4',
            buttonHoverColor: '#0891b2'
          }
        },
        {
          variantId: 'cta_green',
          variantName: 'Green CTA',
          description: 'Green CTA button',
          trafficWeight: 33.33,
          isControl: false,
          configuration: {
            buttonColor: '#10b981',
            buttonHoverColor: '#059669'
          }
        },
        {
          variantId: 'cta_orange',
          variantName: 'Orange CTA',
          description: 'Orange CTA button',
          trafficWeight: 33.34,
          isControl: false,
          configuration: {
            buttonColor: '#f97316',
            buttonHoverColor: '#ea580c'
          }
        }
      ],
      targetMetrics: ['button_click', 'signup_conversion'],
      statisticalSignificance: {
        confidenceLevel: 95,
        minimumSampleSize: 150,
        minimumDetectableEffect: 15
      }
    });
  }

  /**
   * Load user assignments from storage
   */
  private async loadUserAssignments(): Promise<void> {
    try {
      const storedAssignments = localStorage.getItem('aquachain_ab_assignments');
      if (storedAssignments) {
        const assignments: Record<string, UserAssignment[]> = JSON.parse(storedAssignments);
        Object.entries(assignments).forEach(([userId, userAssignments]) => {
          this.userAssignments.set(userId, userAssignments);
        });
      }
    } catch (error) {
      console.warn('Failed to load user assignments:', error);
    }
  }

  /**
   * Check if user should be included in test
   */
  private shouldIncludeUser(test: ABTest): boolean {
    // Check traffic allocation
    const hash = this.hashUserId(this.userId!, test.testId);
    const trafficThreshold = test.trafficAllocation / 100;
    
    if (hash > trafficThreshold) {
      return false;
    }

    // Check segmentation rules
    if (test.segmentationRules) {
      return this.evaluateSegmentationRules(test.segmentationRules);
    }

    return true;
  }

  /**
   * Assign user to variant based on traffic weights
   */
  private assignUserToVariant(test: ABTest): ABTestVariant | null {
    const hash = this.hashUserId(this.userId!, test.testId + '_variant');
    let cumulativeWeight = 0;

    for (const variant of test.variants) {
      cumulativeWeight += variant.trafficWeight / 100;
      if (hash <= cumulativeWeight) {
        // Create assignment
        const assignment: UserAssignment = {
          userId: this.userId!,
          testId: test.testId,
          variantId: variant.variantId,
          assignmentDate: new Date().toISOString()
        };

        // Store assignment
        const userAssignments = this.userAssignments.get(this.userId!) || [];
        userAssignments.push(assignment);
        this.userAssignments.set(this.userId!, userAssignments);
        this.saveUserAssignments();

        return variant;
      }
    }

    return null;
  }

  /**
   * Get existing user assignment for test
   */
  private getUserAssignment(testId: string): UserAssignment | null {
    if (!this.userId) return null;
    
    const assignments = this.userAssignments.get(this.userId) || [];
    return assignments.find(a => a.testId === testId) || null;
  }

  /**
   * Track variant assignment
   */
  private trackVariantAssignment(testId: string, variant: ABTestVariant): void {
    const test = this.activeTests.get(testId);
    if (!test) return;

    this.trackTestEvent('ab_test_assignment', {
      test_id: testId,
      test_name: test.testName,
      variant_id: variant.variantId,
      variant_name: variant.variantName,
      is_control: variant.isControl
    });

    // Initialize test results if not exists
    if (!this.testResults.has(testId)) {
      this.testResults.set(testId, test.variants.map(v => ({
        testId,
        variantId: v.variantId,
        variantName: v.variantName,
        participants: 0,
        conversions: 0,
        conversionRate: 0,
        confidence: 0,
        statisticalSignificance: false,
        metrics: {},
        startDate: test.startDate
      })));
    }

    // Update participant count
    this.updateTestResults(testId, variant.variantId, 'participant');
  }

  /**
   * Update test results
   */
  private updateTestResults(
    testId: string,
    variantId: string,
    metricType: string,
    value?: number
  ): void {
    const results = this.testResults.get(testId);
    if (!results) return;

    const variantResult = results.find(r => r.variantId === variantId);
    if (!variantResult) return;

    switch (metricType) {
      case 'participant':
        variantResult.participants++;
        break;
      case 'conversion':
        variantResult.conversions++;
        variantResult.conversionRate = (variantResult.conversions / variantResult.participants) * 100;
        break;
      default:
        variantResult.metrics[metricType] = (variantResult.metrics[metricType] || 0) + (value || 1);
        break;
    }

    // Save results
    this.saveTestResults(testId, results);
  }

  /**
   * Calculate statistical significance
   */
  private calculateStatisticalSignificance(testId: string, variantId: string): Partial<ABTestResult> {
    const results = this.testResults.get(testId);
    const test = this.activeTests.get(testId);
    
    if (!results || !test) {
      return { confidence: 0, statisticalSignificance: false };
    }

    const controlResult = results.find(r => 
      test.variants.find(v => v.variantId === r.variantId)?.isControl
    );
    const variantResult = results.find(r => r.variantId === variantId);

    if (!controlResult || !variantResult || controlResult === variantResult) {
      return { confidence: 0, statisticalSignificance: false };
    }

    // Simple statistical test (in production, use proper statistical libraries)
    const controlRate = controlResult.conversionRate / 100;
    const variantRate = variantResult.conversionRate / 100;
    
    const pooledRate = (controlResult.conversions + variantResult.conversions) / 
                      (controlResult.participants + variantResult.participants);
    
    const standardError = Math.sqrt(
      pooledRate * (1 - pooledRate) * 
      (1 / controlResult.participants + 1 / variantResult.participants)
    );

    const zScore = Math.abs(variantRate - controlRate) / standardError;
    const pValue = 2 * (1 - this.normalCDF(Math.abs(zScore)));
    const confidence = (1 - pValue) * 100;
    const isSignificant = confidence >= test.statisticalSignificance.confidenceLevel;

    return {
      confidence: Math.round(confidence * 100) / 100,
      statisticalSignificance: isSignificant
    };
  }

  /**
   * Utility methods
   */
  private validateTestConfig(test: ABTest): void {
    if (test.variants.length < 2) {
      throw new Error('Test must have at least 2 variants');
    }

    const totalWeight = test.variants.reduce((sum, v) => sum + v.trafficWeight, 0);
    if (Math.abs(totalWeight - 100) > 0.01) {
      throw new Error('Variant traffic weights must sum to 100');
    }

    const controlVariants = test.variants.filter(v => v.isControl);
    if (controlVariants.length !== 1) {
      throw new Error('Test must have exactly one control variant');
    }
  }

  private hashUserId(userId: string, seed: string): number {
    let hash = 0;
    const str = userId + seed;
    
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash) / Math.pow(2, 31);
  }

  private evaluateSegmentationRules(rules: SegmentationRule[]): boolean {
    // Simplified segmentation evaluation
    // In production, this would evaluate against user attributes
    return true;
  }

  private normalCDF(x: number): number {
    // Approximation of normal cumulative distribution function
    return 0.5 * (1 + this.erf(x / Math.sqrt(2)));
  }

  private erf(x: number): number {
    // Approximation of error function
    const a1 =  0.254829592;
    const a2 = -0.284496736;
    const a3 =  1.421413741;
    const a4 = -1.453152027;
    const a5 =  1.061405429;
    const p  =  0.3275911;

    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
  }

  private trackTestEvent(eventType: string, attributes: Record<string, any>): void {
    // Track in analytics services
    analyticsService.trackEvent({
      eventType,
      attributes: Object.fromEntries(
        Object.entries(attributes).map(([key, value]) => [key, String(value)])
      )
    });

    if (googleAnalyticsService.isReady()) {
      googleAnalyticsService.trackEvent(eventType, attributes);
    }

    // Track in conversion service
    conversionTrackingService.trackJourneyStep(
      eventType,
      `A/B Test: ${eventType}`,
      window.location.href,
      undefined,
      attributes
    );
  }

  private generateTestId(): string {
    return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateUserId(): string {
    let userId = localStorage.getItem('aquachain_user_id');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('aquachain_user_id', userId);
    }
    return userId;
  }

  private calculateTestDuration(test: ABTest): number {
    const start = new Date(test.startDate);
    const end = test.endDate ? new Date(test.endDate) : new Date();
    return Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  }

  private saveTestConfig(test: ABTest): void {
    try {
      const tests = Array.from(this.activeTests.values());
      localStorage.setItem('aquachain_ab_tests', JSON.stringify(tests));
    } catch (error) {
      console.warn('Failed to save test config:', error);
    }
  }

  private saveUserAssignments(): void {
    try {
      const assignments = Object.fromEntries(this.userAssignments);
      localStorage.setItem('aquachain_ab_assignments', JSON.stringify(assignments));
    } catch (error) {
      console.warn('Failed to save user assignments:', error);
    }
  }

  private saveTestResults(testId: string, results: ABTestResult[]): void {
    try {
      const allResults = Object.fromEntries(this.testResults);
      localStorage.setItem('aquachain_ab_results', JSON.stringify(allResults));
    } catch (error) {
      console.warn('Failed to save test results:', error);
    }
  }
}

// Export singleton instance
export const abTestingService = new ABTestingService();
export default abTestingService;