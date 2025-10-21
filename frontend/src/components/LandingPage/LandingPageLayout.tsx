import React, { ReactNode } from 'react';

interface LandingPageLayoutProps {
  children: ReactNode;
}

/**
 * Main layout container for the AquaChain Landing Page
 * Implements mobile-first responsive design with CSS Grid and Flexbox
 * Supports responsive breakpoints: mobile (320px+), tablet (768px+), desktop (1024px+), wide (1440px+)
 */
const LandingPageLayout: React.FC<LandingPageLayoutProps> = ({ children }) => {
  return (
    <div className="landing-page-layout">
      {/* Main container with responsive grid */}
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-cyan-900 relative overflow-hidden">
        {/* Background underwater effects container */}
        <div className="absolute inset-0 bg-underwater-pattern opacity-20" />
        
        {/* Main content grid */}
        <div className="relative z-base grid grid-rows-[auto_1fr_auto] min-h-screen">
          {children}
        </div>
      </div>
    </div>
  );
};

export default LandingPageLayout;