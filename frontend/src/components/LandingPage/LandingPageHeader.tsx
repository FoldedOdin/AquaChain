import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import AnimatedLogo from './AnimatedLogo';

interface LandingPageHeaderProps {
  onGetStartedClick: () => void;
  onViewDashboardsClick: () => void;
  className?: string;
}

/**
 * Header component for AquaChain Landing Page
 * Features responsive navigation, animated logo, and accessibility support
 */
const LandingPageHeader: React.FC<LandingPageHeaderProps> = ({
  onGetStartedClick,
  onViewDashboardsClick,
  className = ''
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleNavClick = (action: () => void) => {
    action();
    setIsMobileMenuOpen(false); // Close mobile menu after navigation
  };

  return (
    <motion.header
      className={`relative z-40 ${className}`}
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
    >
      <nav
        className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">

            <span className="ml-3 text-xl font-bold text-white">
              AquaChain
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <button
                onClick={() => handleNavClick(onViewDashboardsClick)}
                className="text-aqua-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-aqua-800"
              >
                View Dashboards
              </button>
              <a
                href="#features"
                className="text-aqua-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-aqua-800"
              >
                Features
              </a>
              <a
                href="#contact"
                className="text-aqua-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-aqua-800"
              >
                Contact
              </a>
              <button
                onClick={() => handleNavClick(onGetStartedClick)}
                className="bg-aqua-500 hover:bg-aqua-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-300 focus:ring-offset-2 focus:ring-offset-aqua-800"
              >
                Get Started
              </button>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-aqua-100 hover:text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-aqua-500"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label="Toggle navigation menu"
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <motion.div
          id="mobile-menu"
          className="md:hidden"
          initial={false}
          animate={{
            height: isMobileMenuOpen ? 'auto' : 0,
            opacity: isMobileMenuOpen ? 1 : 0
          }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          style={{ overflow: 'hidden' }}
        >
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-aqua-800/90 backdrop-blur-sm rounded-lg mt-2">
            <button
              onClick={() => handleNavClick(onViewDashboardsClick)}
              className="text-aqua-100 hover:text-white block px-3 py-2 rounded-md text-base font-medium w-full text-left transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500"
            >
              View Dashboards
            </button>
            <a
              href="#features"
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-aqua-100 hover:text-white block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500"
            >
              Features
            </a>
            <a
              href="#contact"
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-aqua-100 hover:text-white block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500"
            >
              Contact
            </a>
            <button
              onClick={() => handleNavClick(onGetStartedClick)}
              className="bg-aqua-500 hover:bg-aqua-400 text-white block px-3 py-2 rounded-md text-base font-medium w-full text-left transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-300"
            >
              Get Started
            </button>
          </div>
        </motion.div>
      </nav>
    </motion.header>
  );
};

export default LandingPageHeader;