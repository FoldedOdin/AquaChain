import React, { createContext, useContext, useEffect, useState } from 'react';
import { registerSW, ServiceWorkerUpdateManager } from '../utils/serviceWorkerRegistration';
import { pushNotificationService } from '../services/pushNotificationService';
import { offlineQueueService } from '../services/offlineQueueService';
import { gracefulDegradationManager } from '../utils/gracefulDegradation';

interface PWAContextType {
  // Installation
  isInstallable: boolean;
  isInstalled: boolean;
  promptInstall: () => Promise<boolean>;
  
  // Service Worker
  isServiceWorkerReady: boolean;
  updateAvailable: boolean;
  applyUpdate: () => Promise<void>;
  
  // Offline/Online
  isOnline: boolean;
  offlineQueueCount: number;
  
  // Push Notifications
  notificationsSupported: boolean;
  notificationPermission: 'granted' | 'denied' | 'default';
  isSubscribedToNotifications: boolean;
  subscribeToNotifications: () => Promise<boolean>;
  unsubscribeFromNotifications: () => Promise<boolean>;
  
  // PWA Features
  isPWAMode: boolean;
  capabilities: {
    canViewContent: boolean;
    canSubmitForms: boolean;
    canTrackAnalytics: boolean;
    canAuthenticate: boolean;
    canLoadImages: boolean;
  };
}

const PWAContext = createContext<PWAContextType | undefined>(undefined);

interface PWAProviderProps {
  children: React.ReactNode;
}

export const PWAProvider: React.FC<PWAProviderProps> = ({ children }) => {
  // Installation state
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  
  // Service Worker state
  const [isServiceWorkerReady, setIsServiceWorkerReady] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [swUpdateManager] = useState(new ServiceWorkerUpdateManager());
  
  // Network state
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [offlineQueueCount, setOfflineQueueCount] = useState(0);
  
  // Notification state
  const [notificationsSupported, setNotificationsSupported] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<'granted' | 'denied' | 'default'>('default');
  const [isSubscribedToNotifications, setIsSubscribedToNotifications] = useState(false);
  
  // PWA mode detection
  const [isPWAMode, setIsPWAMode] = useState(false);
  const [capabilities, setCapabilities] = useState({
    canViewContent: true,
    canSubmitForms: false,
    canTrackAnalytics: false,
    canAuthenticate: false,
    canLoadImages: false
  });

  useEffect(() => {
    initializePWA();
  }, []);

  const initializePWA = async () => {
    // Check PWA mode
    const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
                  (window.navigator as any).standalone === true;
    setIsPWAMode(isPWA);

    // Temporarily disable Service Worker in development for debugging
    if (process.env.NODE_ENV !== 'development') {
      registerSW({
        onSuccess: (registration) => {
          console.log('Service Worker registered successfully');
          setIsServiceWorkerReady(true);
        },
        onUpdate: (registration) => {
          console.log('Service Worker update available');
          setUpdateAvailable(true);
        },
        onOfflineReady: () => {
          console.log('App ready for offline use');
        }
      });
    }

    // Setup install prompt listener
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    });

    // Check if already installed
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    });

    // Setup network listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Setup SW update listener
    window.addEventListener('sw-update-available', () => {
      setUpdateAvailable(true);
    });

    // Initialize push notifications
    setNotificationsSupported(pushNotificationService.isSupported());
    if (pushNotificationService.isSupported()) {
      const permission = pushNotificationService.getPermissionStatus();
      setNotificationPermission(
        permission.granted ? 'granted' : 
        permission.denied ? 'denied' : 'default'
      );

      // Check subscription status
      pushNotificationService.getSubscription().then((subscription) => {
        setIsSubscribedToNotifications(!!subscription);
      });
    }

    // Initialize capabilities
    updateCapabilities();

    // Update offline queue count
    updateOfflineQueueCount();
  };

  const handleOnline = () => {
    setIsOnline(true);
    updateCapabilities();
    
    // Process offline queue
    offlineQueueService.processQueue().then(() => {
      updateOfflineQueueCount();
    });
  };

  const handleOffline = () => {
    setIsOnline(false);
    updateCapabilities();
  };

  const updateCapabilities = () => {
    const newCapabilities = gracefulDegradationManager.getCapabilities();
    setCapabilities(newCapabilities);
  };

  const updateOfflineQueueCount = async () => {
    try {
      const stats = await offlineQueueService.getQueueStats();
      setOfflineQueueCount(stats.total);
    } catch (error) {
      console.error('Error getting offline queue stats:', error);
    }
  };

  const promptInstall = async (): Promise<boolean> => {
    if (!deferredPrompt) {
      return false;
    }

    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        setIsInstalled(true);
        setIsInstallable(false);
        setDeferredPrompt(null);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error prompting install:', error);
      return false;
    }
  };

  const applyUpdate = async (): Promise<void> => {
    try {
      await swUpdateManager.applyUpdate();
    } catch (error) {
      console.error('Error applying update:', error);
    }
  };

  const subscribeToNotifications = async (): Promise<boolean> => {
    try {
      const subscription = await pushNotificationService.subscribe();
      if (subscription) {
        setIsSubscribedToNotifications(true);
        setNotificationPermission('granted');
        
        // Setup AquaChain-specific notifications
        await pushNotificationService.setupAquaChainNotifications();
        
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error subscribing to notifications:', error);
      return false;
    }
  };

  const unsubscribeFromNotifications = async (): Promise<boolean> => {
    try {
      const success = await pushNotificationService.unsubscribe();
      if (success) {
        setIsSubscribedToNotifications(false);
      }
      return success;
    } catch (error) {
      console.error('Error unsubscribing from notifications:', error);
      return false;
    }
  };

  const contextValue: PWAContextType = {
    // Installation
    isInstallable,
    isInstalled,
    promptInstall,
    
    // Service Worker
    isServiceWorkerReady,
    updateAvailable,
    applyUpdate,
    
    // Offline/Online
    isOnline,
    offlineQueueCount,
    
    // Push Notifications
    notificationsSupported,
    notificationPermission,
    isSubscribedToNotifications,
    subscribeToNotifications,
    unsubscribeFromNotifications,
    
    // PWA Features
    isPWAMode,
    capabilities
  };

  return (
    <PWAContext.Provider value={contextValue}>
      {children}
    </PWAContext.Provider>
  );
};

export const usePWA = (): PWAContextType => {
  const context = useContext(PWAContext);
  if (context === undefined) {
    throw new Error('usePWA must be used within a PWAProvider');
  }
  return context;
};

// PWA Status Component
export const PWAStatus: React.FC<{ className?: string }> = ({ className = '' }) => {
  const {
    isOnline,
    offlineQueueCount,
    updateAvailable,
    applyUpdate,
    isPWAMode
  } = usePWA();

  if (!isPWAMode) {
    return null;
  }

  return (
    <div className={`fixed top-4 right-4 z-50 space-y-2 ${className}`}>
      {/* Offline Queue Status */}
      {!isOnline && offlineQueueCount > 0 && (
        <div className="bg-orange-500 text-white px-3 py-2 rounded-lg shadow-lg text-sm">
          {offlineQueueCount} items queued for sync
        </div>
      )}
      
      {/* Update Available */}
      {updateAvailable && (
        <div className="bg-blue-500 text-white px-3 py-2 rounded-lg shadow-lg text-sm">
          <div className="flex items-center justify-between space-x-2">
            <span>Update available</span>
            <button
              onClick={applyUpdate}
              className="bg-white text-blue-500 px-2 py-1 rounded text-xs font-medium hover:bg-blue-50 transition-colors"
            >
              Update
            </button>
          </div>
        </div>
      )}
      
      {/* Back Online */}
      {isOnline && offlineQueueCount === 0 && (
        <div className="bg-green-500 text-white px-3 py-2 rounded-lg shadow-lg text-sm animate-pulse">
          All synced!
        </div>
      )}
    </div>
  );
};