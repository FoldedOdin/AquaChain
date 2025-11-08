import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HomeIcon,
  SparklesIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

interface ScrollNavigationProps {
  className?: string;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  sectionId: string;
}

/**
 * Scroll Navigation Component
 * Provides smooth scrolling navigation between page sections
 * Includes scroll progress indicator and keyboard navigation support
 */
const ScrollNavigation: React.FC<ScrollNavigationProps> = ({ className = '' }) => {
  const [activeSection, setActiveSection] = useState('hero');
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const navigationItems: NavigationItem[] = [
    { id: 'hero', label: 'Home', icon: HomeIcon, sectionId: 'hero' },
    { id: 'features', label: 'Features', icon: SparklesIcon, sectionId: 'features' },
    { id: 'roles', label: 'Roles', icon: UserGroupIcon, sectionId: 'roles' },
    { id: 'contact', label: 'Contact', icon: ChatBubbleLeftRightIcon, sectionId: 'contact' }
  ];

  // Calculate scroll progress and active section
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (scrollTop / docHeight) * 100;
      
      setScrollProgress(progress);
      setIsVisible(scrollTop > 300);

      // Determine active section
      const sections = navigationItems.map(item => ({
        id: item.id,
        element: document.getElementById(item.sectionId)
      }));

      let currentSection = 'hero';
      
      for (const section of sections) {
        if (section.element) {
          const rect = section.element.getBoundingClientRect();
          const isInView = rect.top <= window.innerHeight / 2 && rect.bottom >= window.innerHeight / 2;
          
          if (isInView) {
            currentSection = section.id;
            break;
          }
        }
      }

      setActiveSection(currentSection);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Initial call

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Smooth scroll to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      const headerOffset = 80; // Account for fixed header
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  // Scroll to top
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent, sectionId: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      scrollToSection(sectionId);
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 50 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className={`fixed right-6 top-1/2 transform -translate-y-1/2 z-40 ${className}`}
          role="navigation"
          aria-label="Page sections"
        >
          {/* Progress Indicator */}
          <div className="absolute -left-8 top-0 bottom-0 w-1 bg-slate-700/50 rounded-full overflow-hidden">
            <motion.div
              className="w-full bg-gradient-to-b from-aqua-500 to-emerald-400 rounded-full"
              style={{ height: `${scrollProgress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>

          {/* Navigation Items */}
          <div className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-2 space-y-2">
            {navigationItems.map((item) => (
              <motion.button
                key={item.id}
                onClick={() => scrollToSection(item.sectionId)}
                onKeyDown={(e) => handleKeyDown(e, item.sectionId)}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className={`
                  relative group w-12 h-12 rounded-xl flex items-center justify-center
                  transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-aqua-500/50
                  ${activeSection === item.id
                    ? 'bg-aqua-600 text-white shadow-lg shadow-aqua-500/25'
                    : 'text-gray-400 hover:text-white hover:bg-slate-700/50'
                  }
                `}
                aria-label={`Navigate to ${item.label} section`}
                title={item.label}
              >
                <item.icon className="w-5 h-5" />
                
                {/* Tooltip */}
                <div className="
                  absolute right-full mr-3 px-3 py-2 bg-slate-900 text-white text-sm
                  rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200
                  pointer-events-none whitespace-nowrap
                ">
                  {item.label}
                  <div className="absolute left-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-l-slate-900" />
                </div>
              </motion.button>
            ))}

            {/* Scroll to Top Button */}
            <div className="border-t border-slate-700/50 pt-2 mt-2">
              <motion.button
                onClick={scrollToTop}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="
                  relative group w-12 h-12 rounded-xl flex items-center justify-center
                  text-gray-400 hover:text-white hover:bg-slate-700/50
                  transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-aqua-500/50
                "
                aria-label="Scroll to top"
                title="Back to Top"
              >
                <ChevronUpIcon className="w-5 h-5" />
                
                {/* Tooltip */}
                <div className="
                  absolute right-full mr-3 px-3 py-2 bg-slate-900 text-white text-sm
                  rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200
                  pointer-events-none whitespace-nowrap
                ">
                  Back to Top
                  <div className="absolute left-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-l-slate-900" />
                </div>
              </motion.button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ScrollNavigation;