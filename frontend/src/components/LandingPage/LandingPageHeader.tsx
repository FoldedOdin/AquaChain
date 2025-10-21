import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ResponsiveContainer from './ResponsiveContainer';

interface LandingPageHeaderProps {
  onGetStartedClick: () => void;
  onViewDashboardsClick: () => void;
}

/**
 * Landing page header with AquaChain branding and navigation
 * Features responsive navigation menu with mobile hamburger
 * Implements smooth scroll navigation and accessibility features
 */
const LandingPageHeader: React.FC<LandingPageHeaderProps> = ({
  onGetStartedClick,
  onViewDashboardsClick
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  // Handle scroll effect for header background
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Smooth scroll to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
    setIsMobileMenuOpen(false);
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  };

  return (
    <>
      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-skip-link bg-aqua-500 text-white px-4 py-2 rounded-md font-medium"
      >
        Skip to main content
      </a>

      <motion.header
        className={`
          fixed top-0 left-0 right-0 z-sticky transition-all duration-300
          ${isScrolled 
            ? 'bg-slate-900/95 backdrop-blur-md shadow-lg border-b border-aqua-500/20' 
            : 'bg-transparent'
          }
        `}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <ResponsiveContainer size="xl" padding="md">
          <nav className="flex items-center justify-between h-16 lg:h-20" role="navigation" aria-label="Main navigation">
            {/* Logo and Brand */}
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              {/* Animated Logo Icon */}
              <div className="relative">
                <motion.div
                  className="w-10 h-10 lg:w-12 lg:h-12 bg-gradient-to-br from-aqua-400 to-aqua-600 rounded-full flex items-center justify-center shadow-glow"
                  animate={{ 
                    boxShadow: [
                      '0 0 20px rgba(6, 182, 212, 0.5)',
                      '0 0 30px rgba(6, 182, 212, 0.7)',
                      '0 0 20px rgba(6, 182, 212, 0.5)'
                    ]
                  }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <svg
                    className="w-6 h-6 lg:w-7 lg:h-7 text-white"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                  </svg>
                </motion.div>
                
                {/* Floating droplet animation */}
                <motion.div
                  className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full"
                  animate={{ 
                    y: [-2, -6, -2],
                    opacity: [0.7, 1, 0.7]
                  }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                />
              </div>

              {/* Brand Text */}
              <div className="flex flex-col">
                <h1 className="text-xl lg:text-2xl font-display font-bold text-white">
                  AquaChain
                </h1>
                <p className="text-xs lg:text-sm text-aqua-200 font-medium hidden sm:block">
                  Water Quality Monitoring
                </p>
              </div>
            </motion.div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <nav className="flex items-center space-x-6" role="navigation" aria-label="Primary navigation">
                <button
                  onClick={() => scrollToSection('features')}
                  onKeyDown={(e) => handleKeyDown(e, () => scrollToSection('features'))}
                  className="text-white hover:text-aqua-300 transition-colors duration-200 font-medium focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent rounded-md px-2 py-1"
                  aria-label="Navigate to features section"
                >
                  Features
                </button>
                <button
                  onClick={() => scrollToSection('roles')}
                  onKeyDown={(e) => handleKeyDown(e, () => scrollToSection('roles'))}
                  className="text-white hover:text-aqua-300 transition-colors duration-200 font-medium focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent rounded-md px-2 py-1"
                  aria-label="Navigate to user roles section"
                >
                  For You
                </button>
                <button
                  onClick={() => scrollToSection('contact')}
                  onKeyDown={(e) => handleKeyDown(e, () => scrollToSection('contact'))}
                  className="text-white hover:text-aqua-300 transition-colors duration-200 font-medium focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent rounded-md px-2 py-1"
                  aria-label="Navigate to contact section"
                >
                  Contact
                </button>
              </nav>

              {/* CTA Buttons */}
              <div className="flex items-center space-x-4">
                <motion.button
                  onClick={onViewDashboardsClick}
                  className="text-aqua-300 hover:text-white transition-colors duration-200 font-medium focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent rounded-md px-3 py-2"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="View demonstration dashboards"
                >
                  View Demo
                </motion.button>
                <motion.button
                  onClick={onGetStartedClick}
                  className="bg-gradient-to-r from-aqua-500 to-aqua-600 hover:from-aqua-600 hover:to-aqua-700 text-white font-semibold px-6 py-2.5 rounded-full transition-all duration-200 shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Get started with AquaChain"
                >
                  Get Started
                </motion.button>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-white hover:text-aqua-300 hover:bg-white/10 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </nav>
        </ResponsiveContainer>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              id="mobile-menu"
              className="md:hidden bg-slate-900/98 backdrop-blur-md border-t border-aqua-500/20"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
            >
              <ResponsiveContainer size="xl" padding="md">
                <div className="py-4 space-y-4">
                  {/* Mobile Navigation Links */}
                  <nav className="space-y-2" role="navigation" aria-label="Mobile navigation">
                    <button
                      onClick={() => scrollToSection('features')}
                      className="block w-full text-left text-white hover:text-aqua-300 transition-colors duration-200 font-medium py-2 px-3 rounded-md hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                      aria-label="Navigate to features section"
                    >
                      Features
                    </button>
                    <button
                      onClick={() => scrollToSection('roles')}
                      className="block w-full text-left text-white hover:text-aqua-300 transition-colors duration-200 font-medium py-2 px-3 rounded-md hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                      aria-label="Navigate to user roles section"
                    >
                      For You
                    </button>
                    <button
                      onClick={() => scrollToSection('contact')}
                      className="block w-full text-left text-white hover:text-aqua-300 transition-colors duration-200 font-medium py-2 px-3 rounded-md hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                      aria-label="Navigate to contact section"
                    >
                      Contact
                    </button>
                  </nav>

                  {/* Mobile CTA Buttons */}
                  <div className="pt-4 border-t border-aqua-500/20 space-y-3">
                    <motion.button
                      onClick={onViewDashboardsClick}
                      className="block w-full text-center text-aqua-300 hover:text-white transition-colors duration-200 font-medium py-3 px-4 rounded-md border border-aqua-500/30 hover:bg-aqua-500/10 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                      whileTap={{ scale: 0.98 }}
                      aria-label="View demonstration dashboards"
                    >
                      View Demo
                    </motion.button>
                    <motion.button
                      onClick={onGetStartedClick}
                      className="block w-full text-center bg-gradient-to-r from-aqua-500 to-aqua-600 hover:from-aqua-600 hover:to-aqua-700 text-white font-semibold py-3 px-4 rounded-md transition-all duration-200 shadow-lg focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent"
                      whileTap={{ scale: 0.98 }}
                      aria-label="Get started with AquaChain"
                    >
                      Get Started
                    </motion.button>
                  </div>
                </div>
              </ResponsiveContainer>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.header>
    </>
  );
};

export default LandingPageHeader;