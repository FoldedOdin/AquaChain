import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
  isActive?: boolean;
}

interface AppLikeNavigationProps {
  className?: string;
  onNavigate?: (item: NavigationItem) => void;
}

export const AppLikeNavigation: React.FC<AppLikeNavigationProps> = ({
  className = '',
  onNavigate
}) => {
  const [activeItem, setActiveItem] = useState('home');
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Navigation items for AquaChain
  const navigationItems: NavigationItem[] = [
    {
      id: 'home',
      label: 'Home',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
      ),
      href: '/'
    },
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
        </svg>
      ),
      href: '/dashboard',
      badge: 3 // Example: 3 new alerts
    },
    {
      id: 'devices',
      label: 'Devices',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
        </svg>
      ),
      href: '/devices'
    },
    {
      id: 'alerts',
      label: 'Alerts',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
        </svg>
      ),
      href: '/alerts',
      badge: 2 // Example: 2 active alerts
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
        </svg>
      ),
      href: '/profile'
    }
  ];

  // Hide/show navigation on scroll (mobile app-like behavior)
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down - hide navigation
        setIsVisible(false);
      } else {
        // Scrolling up - show navigation
        setIsVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Set active item based on current path
  useEffect(() => {
    const currentPath = window.location.pathname;
    const activeNavItem = navigationItems.find(item => 
      item.href === currentPath || (item.href !== '/' && currentPath.startsWith(item.href))
    );
    
    if (activeNavItem) {
      setActiveItem(activeNavItem.id);
    }
  }, []);

  const handleItemClick = (item: NavigationItem) => {
    setActiveItem(item.id);
    
    if (onNavigate) {
      onNavigate(item);
    } else {
      // Default navigation behavior
      window.location.href = item.href;
    }
  };

  // Only show in PWA mode or mobile
  const isPWA = window.matchMedia('(display-mode: standalone)').matches;
  const isMobile = window.innerWidth <= 768;
  
  // Temporarily disable app navigation in development to debug routing
  if (process.env.NODE_ENV === 'development') {
    return null;
  }
  
  if (!isPWA && !isMobile) {
    return null;
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.nav
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className={`fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 ${className}`}
          style={{
            paddingBottom: 'env(safe-area-inset-bottom)',
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.1)'
          }}
        >
          <div className="flex items-center justify-around px-2 py-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleItemClick(item)}
                className={`relative flex flex-col items-center justify-center p-2 rounded-lg transition-all duration-200 min-w-0 flex-1 ${
                  activeItem === item.id
                    ? 'text-aqua-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {/* Icon with badge */}
                <div className="relative mb-1">
                  <motion.div
                    animate={{
                      scale: activeItem === item.id ? 1.1 : 1,
                      color: activeItem === item.id ? '#06b6d4' : '#6b7280'
                    }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  >
                    {item.icon}
                  </motion.div>
                  
                  {/* Badge */}
                  {item.badge && item.badge > 0 && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center font-medium"
                    >
                      {item.badge > 99 ? '99+' : item.badge}
                    </motion.div>
                  )}
                </div>
                
                {/* Label */}
                <span className={`text-xs font-medium truncate max-w-full ${
                  activeItem === item.id ? 'text-aqua-600' : 'text-gray-500'
                }`}>
                  {item.label}
                </span>
                
                {/* Active indicator */}
                {activeItem === item.id && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute -top-1 left-1/2 w-1 h-1 bg-aqua-500 rounded-full"
                    style={{ transform: 'translateX(-50%)' }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </div>
        </motion.nav>
      )}
    </AnimatePresence>
  );
};

// Hook for app-like navigation state
export const useAppNavigation = () => {
  const [activeRoute, setActiveRoute] = useState('/');
  const [navigationHistory, setNavigationHistory] = useState<string[]>(['/']);

  const navigate = React.useCallback((path: string) => {
    setActiveRoute(path);
    setNavigationHistory(prev => [...prev, path]);
    
    // Update browser history
    window.history.pushState(null, '', path);
  }, []);

  const goBack = React.useCallback(() => {
    if (navigationHistory.length > 1) {
      const newHistory = navigationHistory.slice(0, -1);
      const previousRoute = newHistory[newHistory.length - 1];
      
      setNavigationHistory(newHistory);
      setActiveRoute(previousRoute);
      
      window.history.back();
    }
  }, [navigationHistory]);

  const canGoBack = navigationHistory.length > 1;

  return {
    activeRoute,
    navigate,
    goBack,
    canGoBack,
    navigationHistory
  };
};

// App-like header component
export const AppHeader: React.FC<{
  title: string;
  showBackButton?: boolean;
  onBack?: () => void;
  rightAction?: React.ReactNode;
  className?: string;
}> = ({ title, showBackButton = false, onBack, rightAction, className = '' }) => {
  const isPWA = window.matchMedia('(display-mode: standalone)').matches;
  
  if (!isPWA) {
    return null;
  }

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 ${className}`}
      style={{
        paddingTop: 'env(safe-area-inset-top)',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
      }}
    >
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left side - Back button or logo */}
        <div className="flex items-center">
          {showBackButton ? (
            <button
              onClick={onBack}
              className="p-2 -ml-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          ) : (
            <div className="w-8 h-8 bg-gradient-to-r from-aqua-500 to-teal-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">🌊</span>
            </div>
          )}
        </div>

        {/* Center - Title */}
        <h1 className="text-lg font-semibold text-gray-900 truncate mx-4">
          {title}
        </h1>

        {/* Right side - Action button */}
        <div className="flex items-center">
          {rightAction || <div className="w-8" />}
        </div>
      </div>
    </header>
  );
};

