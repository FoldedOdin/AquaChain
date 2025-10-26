import React, { useEffect, useState, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import LandingPageLayout from './LandingPageLayout';
import LandingPageHeader from './LandingPageHeader';
import AnimationEngineComponent from './AnimationEngine';
import LandingPageFooter from './LandingPageFooter';
import HeroSection from './HeroSection';
import ScrollNavigation from './ScrollNavigation';
import SectionTransition from './SectionTransition';
import AuthModalComponent from './AuthModalComponent';
import { LoginCredentials, SignupData } from './AuthModal';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';
import { useConversionTracking, useScrollTracking } from '../../hooks/useConversionTracking';
import { useABTesting } from '../../hooks/useABTesting';
import authService from '../../services/authService';
import { useAuth } from '../../contexts/AuthContext';
import { LazyContent } from '../../utils/lazyLoading';
import { 
  LazyFeaturesShowcase,
  LazyRoleSelectionSection,
  LazyContactSection,
  preloadCriticalComponents
} from '../../utils/codeSplitting';
import { 
  FeaturesShowcaseSkeleton,
  RoleSelectionSkeleton,
  ContactSkeleton
} from '../Loading/LoadingSkeleton';
import { initializeFontOptimization } from '../../utils/fontOptimization';

interface LandingPageProps {
  onGetStartedClick?: () => void;
  onViewDashboardsClick?: () => void;
  onContactClick?: () => void;
  onTechnicianClick?: () => void;
  onContactFormSubmit?: (data: any) => Promise<void>;
  onLogin?: (credentials: LoginCredentials) => Promise<void>;
  onSignup?: (userData: SignupData) => Promise<void>;
}

/**
 * Main AquaChain Landing Page component
 * Implements responsive layout foundation with navigation and smooth scrolling
 * Provides entry point for authentication and user onboarding
 * Includes comprehensive analytics tracking and A/B testing
 */
const LandingPage: React.FC<LandingPageProps> = ({
  onGetStartedClick,
  onViewDashboardsClick,
  onContactClick,
  onTechnicianClick,
  onContactFormSubmit,
  onLogin,
  onSignup
}) => {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'signup'>('login');

  
  // Animation settings based on user preferences and performance
  const [animationSettings] = useState({
    enableParallax: true,
    enableRipples: true,
    enableBubbles: true,
    performanceMode: 'high' as 'high' | 'medium' | 'low'
  });

  // Initialize analytics and tracking hooks
  const { trackConversion, trackPageView, trackInteraction } = useConversionTracking();
  const { isInitialized: isABTestInitialized } = useABTesting();

  // Initialize keyboard navigation
  useKeyboardNavigation({
    enableSectionJumping: true,
    enableModalClose: true,
    enableFocusManagement: true
  });

  // Handle opening auth modal
  const handleGetStartedClick = () => {
    // Track CTA click
    trackInteraction('button', 'get-started', 'click', {
      section: 'hero',
      cta_type: 'primary'
    });

    if (onGetStartedClick) {
      onGetStartedClick();
    } else {
      setAuthModalTab('login');
      setIsAuthModalOpen(true);
    }
  };

  // Handle auth modal close
  const handleAuthModalClose = () => {
    setIsAuthModalOpen(false);
  };

  // Handle login
  const handleLogin = async (credentials: LoginCredentials) => {
    try {
      if (onLogin) {
        await onLogin(credentials);
      } else {
        // Use auth service directly if no custom handler provided
        const result = await authService.signIn(credentials);
        // Redirect based on user role
        window.location.href = result.redirectPath;
      }
      
      // Track successful login conversion
      trackConversion('login', undefined, {
        auth_method: 'email',
        user_role: 'consumer' // This would come from the auth result
      });
      
      setIsAuthModalOpen(false);
    } catch (error) {
      // Track failed login attempt
      trackInteraction('form', 'login', 'error', {
        error_type: 'authentication_failed'
      });
      throw error; // Re-throw to let the form handle the error display
    }
  };

  // Handle signup
  const handleSignup = async (userData: SignupData) => {
    try {
      if (onSignup) {
        await onSignup(userData);
      } else {
        // Use auth service directly if no custom handler provided
        await authService.signUp(userData);
        // Keep modal open to show success message and allow email verification
      }
      
      // Track successful signup conversion
      trackConversion('signup', 10, { // Assign $10 value to signup
        auth_method: 'email',
        user_role: userData.role,
        signup_source: 'landing_page'
      });
      
      // Don't close modal immediately for signup to show success message
    } catch (error) {
      // Track failed signup attempt
      trackInteraction('form', 'signup', 'error', {
        error_type: 'registration_failed',
        user_role: userData.role
      });
      throw error; // Re-throw to let the form handle the error display
    }
  };

  // Handle technician click
  const handleTechnicianClick = () => {
    if (onTechnicianClick) {
      onTechnicianClick();
    } else {
      // Scroll to contact section for technician inquiries
      const contactSection = document.getElementById('contact');
      if (contactSection) {
        contactSection.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  // Handle view dashboards click
  const handleViewDashboardsClick = () => {
    // Track dashboard access
    trackConversion('demo_view', 5, {
      access_source: 'landing_page',
      section: 'hero'
    });

    if (onViewDashboardsClick) {
      onViewDashboardsClick();
    } else {
      // Redirect to login for dashboard access
      setAuthModalTab('login');
      setIsAuthModalOpen(true);
    }
  };
  // Initialize performance optimizations and analytics tracking
  useEffect(() => {
    // Track initial page view
    trackPageView('Landing Page', {
      page_type: 'landing',
      ab_test_initialized: isABTestInitialized.toString()
    });

    // Initialize font optimization
    initializeFontOptimization();
    
    // Preload critical components on interaction
    const preloadTimer = setTimeout(() => {
      preloadCriticalComponents();
    }, 2000);
    
    // Ensure smooth scrolling is enabled
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Handle scroll restoration on page load
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
    
    // Scroll to top on component mount
    window.scrollTo(0, 0);
    
    // Cleanup
    return () => {
      clearTimeout(preloadTimer);
      document.documentElement.style.scrollBehavior = 'auto';
    };
  }, [trackPageView, isABTestInitialized]);

  // Handle keyboard navigation for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Handle Escape key to close any open modals or menus
      if (event.key === 'Escape') {
        // This will be handled by individual components
        return;
      }
      
      // Handle Tab key for focus management
      if (event.key === 'Tab') {
        // Ensure focus is visible
        document.body.classList.add('keyboard-navigation');
      }
    };

    const handleMouseDown = () => {
      // Remove keyboard navigation class when using mouse
      document.body.classList.remove('keyboard-navigation');
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  return (
    <LandingPageLayout>
      <AnimationEngineComponent 
        settings={animationSettings}
        className="min-h-screen"
      >
        {/* Header with Navigation */}
        <LandingPageHeader
          onGetStartedClick={handleGetStartedClick}
          onViewDashboardsClick={handleViewDashboardsClick}
        />

        {/* Main Content Area */}
        <main id="main-content" className="flex-1" role="main">
        {/* Hero Section */}
        <section id="hero">
          <SectionTransition direction="fade" duration={0.8}>
            <HeroSection 
              onGetStartedClick={handleGetStartedClick}
              onViewDashboardsClick={handleViewDashboardsClick}
            />
          </SectionTransition>
        </section>

        {/* Features Showcase - Lazy Loaded */}
        <section id="features">
          <SectionTransition direction="up" delay={0.2}>
            <LazyContent fallback={<FeaturesShowcaseSkeleton />} threshold={0.1} rootMargin="100px">
              <Suspense fallback={<FeaturesShowcaseSkeleton />}>
                <LazyFeaturesShowcase />
              </Suspense>
            </LazyContent>
          </SectionTransition>
        </section>

        {/* Role Selection Section - Lazy Loaded */}
        <section id="roles">
          <SectionTransition direction="up" delay={0.1}>
            <LazyContent fallback={<RoleSelectionSkeleton />} threshold={0.1} rootMargin="100px">
              <Suspense fallback={<RoleSelectionSkeleton />}>
                <LazyRoleSelectionSection
                  onConsumerClick={handleViewDashboardsClick}
                  onTechnicianClick={handleTechnicianClick}
                  onViewDashboardsClick={handleViewDashboardsClick}
                />
              </Suspense>
            </LazyContent>
          </SectionTransition>
        </section>

        {/* Contact Section - Lazy Loaded */}
        <section id="contact">
          <SectionTransition direction="up" delay={0.1}>
            <LazyContent fallback={<ContactSkeleton />} threshold={0.1} rootMargin="100px">
              <Suspense fallback={<ContactSkeleton />}>
                <LazyContactSection onFormSubmit={onContactFormSubmit} />
              </Suspense>
            </LazyContent>
          </SectionTransition>
        </section>
        </main>

        {/* Scroll Navigation */}
        <ScrollNavigation />

        {/* Footer */}
        <LandingPageFooter onContactClick={onContactClick} />
      </AnimationEngineComponent>

      {/* Authentication Modal */}
      <AuthModalComponent
        isOpen={isAuthModalOpen}
        onClose={handleAuthModalClose}
        initialTab={authModalTab}
        onLogin={handleLogin}
        onSignup={handleSignup}
      />
    </LandingPageLayout>
  );
};

export default LandingPage;