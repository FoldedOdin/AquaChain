import React from 'react';
import { motion } from 'framer-motion';
import { usePerformanceMonitoring } from '../../hooks/usePerformanceMonitoring';
import { announceToScreenReader } from '../../utils/accessibility';

interface LandingPageLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Main layout container for the AquaChain Landing Page
 * Provides responsive structure, accessibility features, and performance monitoring
 */
const LandingPageLayout: React.FC<LandingPageLayoutProps> = ({ 
  children, 
  className = '' 
}) => {
  const { trackLayoutShift } = usePerformanceMonitoring();

  React.useEffect(() => {
    // Announce page load to screen readers
    announceToScreenReader('AquaChain landing page loaded');
    
    // Track layout stability
    if (trackLayoutShift) {
      trackLayoutShift();
    }
  }, [trackLayoutShift]);

  return (
    <motion.div
      className={`min-h-screen bg-gradient-to-b from-aqua-900 via-aqua-800 to-aqua-700 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      role="main"
      aria-label="AquaChain Landing Page"
    >
      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-white text-aqua-900 px-4 py-2 rounded-md z-50 focus:outline-none focus:ring-2 focus:ring-aqua-500"
      >
        Skip to main content
      </a>

      {/* Main content container */}
      <div 
        id="main-content"
        className="relative overflow-hidden"
        style={{ minHeight: '100vh' }}
      >
        {children}
      </div>

      {/* Screen reader announcements */}
      <div
        id="sr-announcements"
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      />
    </motion.div>
  );
};

export default LandingPageLayout;