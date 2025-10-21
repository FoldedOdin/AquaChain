import React from 'react';
import { motion } from 'framer-motion';
import ResponsiveContainer from './ResponsiveContainer';

interface LandingPageFooterProps {
  onContactClick?: () => void;
}

/**
 * Landing page footer with company information and links
 * Features responsive layout for different screen sizes
 * Includes accessibility compliance and keyboard navigation
 */
const LandingPageFooter: React.FC<LandingPageFooterProps> = ({ onContactClick }) => {
  // Smooth scroll to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  };

  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 border-t border-aqua-500/20 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/95 to-transparent" />
      <div className="absolute inset-0 bg-underwater-pattern opacity-10" />

      <ResponsiveContainer size="xl" padding="lg">
        <div className="relative z-base py-12 lg:py-16">
          {/* Main Footer Content */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
            {/* Company Information */}
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                {/* Logo and Brand */}
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-br from-aqua-400 to-aqua-600 rounded-full flex items-center justify-center shadow-glow">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-display font-bold text-white">AquaChain</h2>
                    <p className="text-sm text-aqua-200">Water Quality Monitoring</p>
                  </div>
                </div>

                <p className="text-gray-300 text-sm lg:text-base leading-relaxed mb-6 max-w-md">
                  Real-time water quality monitoring with tamper-evident IoT sensors and AI-powered insights.
                  Ensuring safe water for communities worldwide.
                </p>

                {/* Contact Information */}
                <div className="space-y-3">
                  <div className="flex items-center space-x-3 text-gray-300">
                    <svg className="w-5 h-5 text-aqua-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                    </svg>
                    <span className="text-sm">Ernakulam, KL, IN</span>
                  </div>
                  <div className="flex items-center space-x-3 text-gray-300">
                    <svg className="w-5 h-5 text-aqua-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                    </svg>
                    <a
                      href="mailto:info@aquachain.com"
                      className="text-sm hover:text-aqua-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded"
                      aria-label="Send email to AquaChain"
                    >
                      info@aquachain.io
                    </a>
                  </div>
                  <div className="flex items-center space-x-3 text-gray-300">
                    <svg className="w-5 h-5 text-aqua-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z" />
                    </svg>
                    <a
                      href="tel:+1-555-AQUA-CHAIN"
                      className="text-sm hover:text-aqua-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded"
                      aria-label="Call AquaChain support"
                    >
                      +91 2345678901
                    </a>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Quick Links */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
            >
              <h3 className="text-white font-semibold text-lg mb-6">Quick Links</h3>
              <nav className="space-y-3" role="navigation" aria-label="Footer navigation">
                <button
                  onClick={() => scrollToSection('features')}
                  onKeyDown={(e) => handleKeyDown(e, () => scrollToSection('features'))}
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="Navigate to features section"
                >
                  Features
                </button>
                <button
                  onClick={() => scrollToSection('roles')}
                  onKeyDown={(e) => handleKeyDown(e, () => scrollToSection('roles'))}
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="Navigate to user roles section"
                >
                  For You
                </button>
                <button
                  onClick={onContactClick || (() => scrollToSection('contact'))}
                  onKeyDown={(e) => handleKeyDown(e, onContactClick || (() => scrollToSection('contact')))}
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="Navigate to contact section"
                >
                  Contact
                </button>
                <a
                  href="/privacy"
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="View privacy policy"
                >
                  Privacy Policy
                </a>
                <a
                  href="/terms"
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="View terms of service"
                >
                  Terms of Service
                </a>
              </nav>
            </motion.div>

            {/* Social Links & Resources */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <h3 className="text-white font-semibold text-lg mb-6">Connect</h3>

              {/* Social Media Links */}
              <div className="flex space-x-4 mb-6">
                <a
                  href="https://twitter.com/aquachain"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-slate-800 hover:bg-aqua-600 rounded-full flex items-center justify-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                  aria-label="Follow AquaChain on Twitter"
                >
                  <svg className="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                  </svg>
                </a>
                <a
                  href="https://linkedin.com/company/aquachain"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-slate-800 hover:bg-aqua-600 rounded-full flex items-center justify-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                  aria-label="Follow AquaChain on LinkedIn"
                >
                  <svg className="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                  </svg>
                </a>
                <a
                  href="https://github.com/aquachain"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-slate-800 hover:bg-aqua-600 rounded-full flex items-center justify-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                  aria-label="View AquaChain on GitHub"
                >
                  <svg className="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                </a>
              </div>

              {/* Additional Resources */}
              <div className="space-y-3">
                <a
                  href="/docs"
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="View documentation"
                >
                  Documentation
                </a>
                <a
                  href="/support"
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="Get support"
                >
                  Support Center
                </a>
                <a
                  href="/status"
                  className="block text-gray-300 hover:text-aqua-300 transition-colors duration-200 text-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded px-1 py-1"
                  aria-label="Check system status"
                >
                  System Status
                </a>
              </div>
            </motion.div>
          </div>

          {/* Bottom Bar */}
          <motion.div
            className="mt-12 pt-8 border-t border-aqua-500/20"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            viewport={{ once: true }}
          >
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-6 text-sm text-gray-400">
                <p>&copy; {currentYear} AquaChain. All rights reserved.</p>
                <div className="flex items-center space-x-4">
                  <span className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    <span>System Operational</span>
                  </span>
                  <span>99.8% Uptime</span>
                </div>
              </div>

              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>Built with</span>
                <div className="flex items-center space-x-1">
                  <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                  </svg>
                  <span>for clean water</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </ResponsiveContainer>
    </footer>
  );
};

export default LandingPageFooter;