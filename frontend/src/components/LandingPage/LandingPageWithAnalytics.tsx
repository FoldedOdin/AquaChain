import React from 'react';
import { AnalyticsProvider } from '../../contexts/AnalyticsContext';
import LandingPage from './LandingPage';
import { LoginCredentials, SignupData } from './AuthModal';

interface LandingPageWithAnalyticsProps {
  onGetStartedClick?: () => void;
  onViewDashboardsClick: () => void;
  onContactClick?: () => void;
  onTechnicianClick?: () => void;
  onContactFormSubmit?: (data: any) => Promise<void>;
  onLogin?: (credentials: LoginCredentials) => Promise<void>;
  onSignup?: (userData: SignupData) => Promise<void>;
}

/**
 * Landing Page wrapper with analytics providers
 * Provides comprehensive tracking and A/B testing capabilities
 */
const LandingPageWithAnalytics: React.FC<LandingPageWithAnalyticsProps> = (props) => {
  return (
    <AnalyticsProvider
      config={{
        applicationId: process.env.REACT_APP_PINPOINT_APPLICATION_ID,
        region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
        googleAnalyticsId: process.env.REACT_APP_GA4_MEASUREMENT_ID,
        enableDebugMode: process.env.NODE_ENV === 'development'
      }}
    >
      <LandingPage {...props} />
    </AnalyticsProvider>
  );
};

export default LandingPageWithAnalytics;