/**
 * Code Splitting Utilities
 * Provides React.lazy() wrappers and loading components
 */

import React, { Suspense } from 'react';
import { 
  HeroSkeleton, 
  FeaturesShowcaseSkeleton, 
  RoleSelectionSkeleton, 
  ContactSkeleton,
  PageSkeleton 
} from '../components/Loading/LoadingSkeleton';

/**
 * Higher-order component for lazy loading with custom fallback
 */
export const withLazyLoading = <P extends object>(
  Component: React.ComponentType<P>,
  fallback: React.ReactNode = <PageSkeleton />
) => {
  const LazyComponent = React.forwardRef<any, P>((props, ref) => (
    <Suspense fallback={fallback}>
      <Component {...(props as P)} ref={ref} />
    </Suspense>
  ));

  LazyComponent.displayName = `withLazyLoading(${Component.displayName || Component.name})`;
  
  return LazyComponent;
};

/**
 * Lazy-loaded components with appropriate fallbacks
 */

// Hero Section with skeleton
export const LazyHeroSection = React.lazy(() => 
  import('../components/LandingPage/HeroSection').then(module => ({
    default: withLazyLoading(module.default, <HeroSkeleton />)
  }))
);

// Features Showcase with skeleton
export const LazyFeaturesShowcase = React.lazy(() => 
  import('../components/LandingPage/FeaturesShowcase').then(module => ({
    default: withLazyLoading(module.default, <FeaturesShowcaseSkeleton />)
  }))
);

// Role Selection with skeleton
export const LazyRoleSelectionSection = React.lazy(() => 
  import('../components/LandingPage/RoleSelectionSection').then(module => ({
    default: withLazyLoading(module.default, <RoleSelectionSkeleton />)
  }))
);

// Contact Section with skeleton
export const LazyContactSection = React.lazy(() => 
  import('../components/LandingPage/ContactSection').then(module => ({
    default: withLazyLoading(module.default, <ContactSkeleton />)
  }))
);

// Auth Modal - Note: AuthModal only exports types, not a component
// If you need to lazy load an auth modal component, create one with a default export



/**
 * Route-based lazy loading for main pages
 */
export const LazyDashboard = React.lazy(() => 
  import('../pages/Dashboard')
);

export const LazyTechnicianDashboard = React.lazy(() => 
  import('../pages/TechnicianDashboard')
);

export const LazyAdminDashboard = React.lazy(() => 
  import('../pages/AdminDashboard')
);

/**
 * Preload components for better UX
 */
export const preloadComponent = (importFunction: () => Promise<any>): void => {
  // Preload the component module
  importFunction().catch(() => {
    // Silently fail if preload fails
  });
};

/**
 * Preload critical components on user interaction
 */
export const preloadCriticalComponents = (): void => {
  // Preload auth modal when user hovers over "Get Started" button
  preloadComponent(() => import('../components/LandingPage/AuthModal'));
  
  // Preload dashboard components for authenticated users
  preloadComponent(() => import('../pages/Dashboard'));
};

/**
 * Component for handling loading errors
 */
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export class LazyLoadingErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  { hasError: boolean; error?: Error }
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): { hasError: boolean; error: Error } {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Lazy loading error:', error, errorInfo);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center min-h-[200px] bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-gray-400 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <p className="text-gray-600 text-sm">Failed to load content</p>
              <button 
                onClick={() => window.location.reload()} 
                className="mt-2 text-aqua-500 hover:text-aqua-600 text-sm underline"
              >
                Retry
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

/**
 * Wrapper component for lazy-loaded sections
 */
interface LazySectionProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const LazySection: React.FC<LazySectionProps> = ({ children, fallback }) => {
  return (
    <LazyLoadingErrorBoundary fallback={fallback}>
      <Suspense fallback={fallback || <PageSkeleton />}>
        {children}
      </Suspense>
    </LazyLoadingErrorBoundary>
  );
};