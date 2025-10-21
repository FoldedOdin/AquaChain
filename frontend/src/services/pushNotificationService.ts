// Push Notification Service
// Handles PWA push notification setup and management

import React from 'react';

interface NotificationPermission {
  granted: boolean;
  denied: boolean;
  default: boolean;
}

interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

class PushNotificationService {
  private vapidPublicKey = process.env.REACT_APP_VAPID_PUBLIC_KEY || '';
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;

  constructor() {
    this.init();
  }

  private async init(): Promise<void> {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.ready;
        console.log('Push notification service initialized');
      } catch (error) {
        console.error('Failed to initialize push notification service:', error);
      }
    }
  }

  // Check if push notifications are supported
  public isSupported(): boolean {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  }

  // Get current notification permission status
  public getPermissionStatus(): NotificationPermission {
    if (!this.isSupported()) {
      return { granted: false, denied: true, default: false };
    }

    const permission = Notification.permission;
    return {
      granted: permission === 'granted',
      denied: permission === 'denied',
      default: permission === 'default'
    };
  }

  // Request notification permission
  public async requestPermission(): Promise<boolean> {
    if (!this.isSupported()) {
      console.warn('Push notifications not supported');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      console.log('Notification permission:', permission);
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  // Subscribe to push notifications
  public async subscribe(): Promise<PushSubscriptionData | null> {
    if (!this.serviceWorkerRegistration) {
      console.error('Service worker not ready');
      return null;
    }

    const permissionStatus = this.getPermissionStatus();
    if (!permissionStatus.granted) {
      const granted = await this.requestPermission();
      if (!granted) {
        console.log('Push notification permission denied');
        return null;
      }
    }

    try {
      // Check if already subscribed
      const existingSubscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
      if (existingSubscription) {
        console.log('Already subscribed to push notifications');
        return this.subscriptionToData(existingSubscription);
      }

      // Create new subscription
      const subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
      });

      console.log('Successfully subscribed to push notifications');
      const subscriptionData = this.subscriptionToData(subscription);

      // Send subscription to server
      await this.sendSubscriptionToServer(subscriptionData);

      return subscriptionData;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return null;
    }
  }

  // Unsubscribe from push notifications
  public async unsubscribe(): Promise<boolean> {
    if (!this.serviceWorkerRegistration) {
      return false;
    }

    try {
      const subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
      if (subscription) {
        const success = await subscription.unsubscribe();
        if (success) {
          console.log('Successfully unsubscribed from push notifications');
          // Notify server about unsubscription
          await this.removeSubscriptionFromServer(this.subscriptionToData(subscription));
        }
        return success;
      }
      return true; // Already unsubscribed
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      return false;
    }
  }

  // Get current subscription status
  public async getSubscription(): Promise<PushSubscriptionData | null> {
    if (!this.serviceWorkerRegistration) {
      return null;
    }

    try {
      const subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
      return subscription ? this.subscriptionToData(subscription) : null;
    } catch (error) {
      console.error('Error getting push subscription:', error);
      return null;
    }
  }

  // Show local notification (for testing)
  public async showLocalNotification(
    title: string,
    options: NotificationOptions = {}
  ): Promise<void> {
    if (!this.isSupported()) {
      console.warn('Notifications not supported');
      return;
    }

    const permissionStatus = this.getPermissionStatus();
    if (!permissionStatus.granted) {
      console.warn('Notification permission not granted');
      return;
    }

    try {
      if (this.serviceWorkerRegistration) {
        // Use service worker to show notification
        await this.serviceWorkerRegistration.showNotification(title, {
          icon: '/logo192.png',
          badge: '/favicon.ico',
          vibrate: [200, 100, 200],
          data: {
            url: window.location.origin
          },
          actions: [
            {
              action: 'open',
              title: 'Open AquaChain'
            },
            {
              action: 'close',
              title: 'Close'
            }
          ],
          ...options
        });
      } else {
        // Fallback to regular notification
        new Notification(title, {
          icon: '/logo192.png',
          ...options
        });
      }
    } catch (error) {
      console.error('Error showing notification:', error);
    }
  }

  // Setup notification types for AquaChain
  public async setupAquaChainNotifications(): Promise<void> {
    const subscription = await this.subscribe();
    if (!subscription) {
      return;
    }

    // Configure notification preferences
    const preferences = {
      waterQualityAlerts: true,
      deviceMaintenance: true,
      systemUpdates: false,
      marketingUpdates: false
    };

    try {
      await fetch('/api/notifications/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscription,
          preferences
        })
      });

      console.log('AquaChain notification preferences configured');
    } catch (error) {
      console.error('Error configuring notification preferences:', error);
    }
  }

  // Utility methods
  private subscriptionToData(subscription: PushSubscription): PushSubscriptionData {
    const key = subscription.getKey('p256dh');
    const auth = subscription.getKey('auth');

    return {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: key ? this.arrayBufferToBase64(key) : '',
        auth: auth ? this.arrayBufferToBase64(auth) : ''
      }
    };
  }

  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  private async sendSubscriptionToServer(subscription: PushSubscriptionData): Promise<void> {
    try {
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(subscription)
      });
    } catch (error) {
      console.error('Error sending subscription to server:', error);
    }
  }

  private async removeSubscriptionFromServer(subscription: PushSubscriptionData): Promise<void> {
    try {
      await fetch('/api/notifications/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(subscription)
      });
    } catch (error) {
      console.error('Error removing subscription from server:', error);
    }
  }
}

// Singleton instance
export const pushNotificationService = new PushNotificationService();

// React hook for push notifications
export function usePushNotifications() {
  const [isSupported, setIsSupported] = React.useState(false);
  const [permission, setPermission] = React.useState<NotificationPermission>({
    granted: false,
    denied: false,
    default: true
  });
  const [isSubscribed, setIsSubscribed] = React.useState(false);

  React.useEffect(() => {
    setIsSupported(pushNotificationService.isSupported());
    setPermission(pushNotificationService.getPermissionStatus());

    // Check subscription status
    pushNotificationService.getSubscription().then((subscription) => {
      setIsSubscribed(!!subscription);
    });
  }, []);

  const requestPermission = React.useCallback(async () => {
    const granted = await pushNotificationService.requestPermission();
    setPermission(pushNotificationService.getPermissionStatus());
    return granted;
  }, []);

  const subscribe = React.useCallback(async () => {
    const subscription = await pushNotificationService.subscribe();
    setIsSubscribed(!!subscription);
    return subscription;
  }, []);

  const unsubscribe = React.useCallback(async () => {
    const success = await pushNotificationService.unsubscribe();
    if (success) {
      setIsSubscribed(false);
    }
    return success;
  }, []);

  const showNotification = React.useCallback(
    (title: string, options?: NotificationOptions) => {
      return pushNotificationService.showLocalNotification(title, options);
    },
    []
  );

  return {
    isSupported,
    permission,
    isSubscribed,
    requestPermission,
    subscribe,
    unsubscribe,
    showNotification
  };
}

