# Analytics and A/B Testing Services

This directory contains comprehensive analytics tracking and A/B testing services for the AquaChain Landing Page.

## Overview

The analytics system provides:
- **AWS Pinpoint Integration**: User behavior tracking and segmentation
- **Google Analytics 4**: Marketing insights and conversion tracking
- **Conversion Tracking**: User journey mapping and funnel analysis
- **A/B Testing Framework**: Continuous optimization with statistical significance testing

## Services

### 1. Analytics Service (`analyticsService.ts`)

AWS Pinpoint integration for comprehensive user behavior tracking.

**Features:**
- Event tracking with custom attributes and metrics
- User segmentation and personalization
- Session management and user journey tracking
- Automatic device type and traffic source detection
- Offline event queuing and batch processing

**Usage:**
```typescript
import analyticsService from './services/analyticsService';

// Initialize
await analyticsService.initialize({
  applicationId: 'your-pinpoint-app-id',
  region: 'us-east-1'
});

// Track events
await analyticsService.trackEvent({
  eventType: 'button_click',
  attributes: { button_id: 'get-started' }
});

// Track page views
await analyticsService.trackPageView('Landing Page');

// Set user attributes
analyticsService.setUserAttributes({
  userId: 'user123',
  role: 'consumer',
  deviceType: 'desktop'
});
```

### 2. Google Analytics Service (`googleAnalyticsService.ts`)

Google Analytics 4 integration for marketing insights and conversion tracking.

**Features:**
- Enhanced ecommerce tracking
- Custom dimensions and metrics
- Conversion goals and funnel analysis
- Audience segmentation
- Campaign attribution tracking

**Usage:**
```typescript
import googleAnalyticsService from './services/googleAnalyticsService';

// Initialize
await googleAnalyticsService.initialize('G-XXXXXXXXXX');

// Track conversions
googleAnalyticsService.trackConversion('signup', 10);

// Track form submissions
googleAnalyticsService.trackFormSubmission('contact', 'contact', true);

// Set user properties
googleAnalyticsService.setUserProperties({
  user_role: 'consumer',
  device_type: 'mobile'
});
```

### 3. Conversion Tracking Service (`conversionTrackingService.ts`)

Advanced user journey mapping and conversion funnel analysis.

**Features:**
- Real-time user journey tracking
- Conversion funnel analysis with drop-off points
- Session recording and replay data
- Form abandonment tracking
- Statistical funnel analysis

**Usage:**
```typescript
import conversionTrackingService from './services/conversionTrackingService';

// Track journey steps
conversionTrackingService.trackJourneyStep(
  'hero_cta_click',
  'Hero CTA Clicked',
  window.location.href
);

// Track conversions
conversionTrackingService.trackConversion('signup', 10, {
  source: 'hero_section'
});

// Get funnel analysis
const analysis = conversionTrackingService.getFunnelAnalysis();
```

### 4. A/B Testing Service (`abTestingService.ts`)

Comprehensive A/B testing framework with statistical significance testing.

**Features:**
- Multi-variant testing support
- Statistical significance calculation
- User segmentation and targeting
- Automatic traffic allocation
- Real-time results tracking

**Usage:**
```typescript
import abTestingService from './services/abTestingService';

// Initialize
await abTestingService.initialize();

// Get variant for user
const variant = abTestingService.getVariant('hero_messaging_test');

// Track conversion
abTestingService.trackConversion('hero_messaging_test', 'signup');

// Get test results
const results = abTestingService.getTestResults('hero_messaging_test');
```

## React Hooks

### Analytics Hooks

#### `useAnalytics()`
Main analytics hook providing access to all tracking methods.

#### `useConversionTracking()`
Specialized hook for conversion tracking and user journey mapping.

#### `useScrollTracking()`
Automatic scroll depth tracking with milestone detection.

#### `useFormTracking(formName)`
Form-specific tracking for field interactions and submissions.

### A/B Testing Hooks

#### `useABTesting()`
Main A/B testing hook for test management.

#### `useABTest(testId)`
Hook for specific A/B test participation and tracking.

#### `useHeroMessagingTest()`
Pre-configured hook for hero section messaging tests.

#### `useCTAButtonTest()`
Pre-configured hook for CTA button optimization tests.

## React Components

### `AnalyticsContext`
React context provider that initializes and manages analytics services.

### `ABTestDashboard`
Admin component for viewing A/B test results and performance metrics.

## Configuration

### Environment Variables

```bash
# AWS Pinpoint
REACT_APP_PINPOINT_APPLICATION_ID=your-pinpoint-app-id
REACT_APP_AWS_ACCESS_KEY_ID=your-access-key-id
REACT_APP_AWS_SECRET_ACCESS_KEY=your-secret-access-key
REACT_APP_AWS_REGION=us-east-1

# Google Analytics 4
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AB_TESTING=true
```

### Analytics Provider Setup

```typescript
import { AnalyticsProvider } from './contexts/AnalyticsContext';

function App() {
  return (
    <AnalyticsProvider
      config={{
        applicationId: process.env.REACT_APP_PINPOINT_APPLICATION_ID,
        region: process.env.REACT_APP_AWS_REGION,
        googleAnalyticsId: process.env.REACT_APP_GA4_MEASUREMENT_ID,
        enableDebugMode: process.env.NODE_ENV === 'development'
      }}
    >
      <YourApp />
    </AnalyticsProvider>
  );
}
```

## Default A/B Tests

The system comes with pre-configured A/B tests:

### 1. Hero Messaging Test
- **Control**: "Real-Time Water Quality You Can Trust"
- **Variant A**: "Protect Your Family with Smart Water Monitoring"
- **Metrics**: Signup conversion, demo views, time on page

### 2. CTA Button Color Test
- **Control**: Blue (#06b6d4)
- **Variant A**: Green (#10b981)
- **Variant B**: Orange (#f97316)
- **Metrics**: Button clicks, signup conversion

## Data Models

### Event Tracking
```typescript
interface AnalyticsEvent {
  eventType: string;
  timestamp?: string;
  attributes?: Record<string, string>;
  metrics?: Record<string, number>;
  sessionId?: string;
  userId?: string;
}
```

### User Journey
```typescript
interface JourneyStep {
  stepId: string;
  stepName: string;
  timestamp: string;
  pageUrl: string;
  timeSpent: number;
  scrollDepth?: number;
}
```

### A/B Test Configuration
```typescript
interface ABTest {
  testId: string;
  testName: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  variants: ABTestVariant[];
  targetMetrics: string[];
  statisticalSignificance: {
    confidenceLevel: number;
    minimumSampleSize: number;
    minimumDetectableEffect: number;
  };
}
```

## Privacy and Compliance

- **GDPR Compliance**: User consent management for analytics tracking
- **Data Anonymization**: IP address anonymization in Google Analytics
- **Cookie Management**: Proper cookie consent and management
- **Data Retention**: Configurable data retention policies

## Performance Considerations

- **Lazy Loading**: Analytics scripts loaded asynchronously
- **Batch Processing**: Events batched for efficient API calls
- **Error Handling**: Graceful degradation when analytics fail
- **Offline Support**: Event queuing for offline scenarios

## Testing

The analytics system includes comprehensive testing:

```bash
# Run analytics tests
npm run test -- --testNamePattern="analytics|tracking|ab-test"

# Run specific service tests
npm run test -- src/services/analyticsService.test.ts
```

## Monitoring and Debugging

### Debug Mode
Enable debug mode in development:
```typescript
const config = {
  enableDebugMode: process.env.NODE_ENV === 'development'
};
```

### Console Logging
All services provide detailed console logging in debug mode for troubleshooting.

### Error Tracking
Analytics errors are tracked and reported without breaking the user experience.

## Best Practices

1. **Event Naming**: Use consistent, descriptive event names
2. **Attribute Consistency**: Maintain consistent attribute naming across events
3. **Performance**: Avoid tracking too many events that could impact performance
4. **Privacy**: Always respect user privacy preferences and consent
5. **Testing**: Test analytics implementation thoroughly before production deployment

## Support

For questions or issues with the analytics implementation, refer to:
- AWS Pinpoint Documentation
- Google Analytics 4 Documentation
- Internal development team documentation