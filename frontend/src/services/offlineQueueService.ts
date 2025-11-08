// Offline Queue Service
// Manages offline analytics events and form submissions with background sync

interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  body: string;
  timestamp: number;
  type: 'analytics' | 'form' | 'api';
  retryCount: number;
  maxRetries: number;
}

interface QueuedAnalyticsEvent {
  id: string;
  eventType: string;
  eventData: Record<string, any>;
  timestamp: number;
  userId?: string;
  sessionId: string;
}

interface QueuedFormSubmission {
  id: string;
  formType: 'contact' | 'signup' | 'newsletter';
  formData: Record<string, any>;
  timestamp: number;
  userEmail?: string;
}

class OfflineQueueService {
  private dbName = 'aquachain-offline-queue';
  private dbVersion = 1;
  private db: IDBDatabase | null = null;
  private isInitialized = false;

  constructor() {
    this.initDB();
  }

  private async initDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('Failed to open offline queue database');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isInitialized = true;
        console.log('Offline queue database initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!db.objectStoreNames.contains('requests')) {
          const requestStore = db.createObjectStore('requests', { keyPath: 'id' });
          requestStore.createIndex('type', 'type', { unique: false });
          requestStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('analytics')) {
          const analyticsStore = db.createObjectStore('analytics', { keyPath: 'id' });
          analyticsStore.createIndex('eventType', 'eventType', { unique: false });
          analyticsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('forms')) {
          const formsStore = db.createObjectStore('forms', { keyPath: 'id' });
          formsStore.createIndex('formType', 'formType', { unique: false });
          formsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Queue a network request for later retry
  public async queueRequest(
    url: string,
    method: string,
    headers: Record<string, string>,
    body: any,
    type: 'analytics' | 'form' | 'api' = 'api',
    maxRetries: number = 3
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initDB();
    }

    const request: QueuedRequest = {
      id: this.generateId(),
      url,
      method,
      headers,
      body: JSON.stringify(body),
      timestamp: Date.now(),
      type,
      retryCount: 0,
      maxRetries
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['requests'], 'readwrite');
      const store = transaction.objectStore('requests');
      const addRequest = store.add(request);

      addRequest.onsuccess = () => {
        console.log(`Queued ${type} request for offline sync:`, url);
        resolve();
      };

      addRequest.onerror = () => {
        console.error('Failed to queue request:', addRequest.error);
        reject(addRequest.error);
      };
    });
  }

  // Queue analytics event
  public async queueAnalyticsEvent(
    eventType: string,
    eventData: Record<string, any>,
    userId?: string,
    sessionId?: string
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initDB();
    }

    const event: QueuedAnalyticsEvent = {
      id: this.generateId(),
      eventType,
      eventData,
      timestamp: Date.now(),
      userId,
      sessionId: sessionId || this.getSessionId()
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analytics'], 'readwrite');
      const store = transaction.objectStore('analytics');
      const addRequest = store.add(event);

      addRequest.onsuccess = () => {
        console.log('Queued analytics event for offline sync:', eventType);
        resolve();
      };

      addRequest.onerror = () => {
        console.error('Failed to queue analytics event:', addRequest.error);
        reject(addRequest.error);
      };
    });
  }

  // Queue form submission
  public async queueFormSubmission(
    formType: 'contact' | 'signup' | 'newsletter',
    formData: Record<string, any>,
    userEmail?: string
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initDB();
    }

    const submission: QueuedFormSubmission = {
      id: this.generateId(),
      formType,
      formData,
      timestamp: Date.now(),
      userEmail
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['forms'], 'readwrite');
      const store = transaction.objectStore('forms');
      const addRequest = store.add(submission);

      addRequest.onsuccess = () => {
        console.log('Queued form submission for offline sync:', formType);
        resolve();
      };

      addRequest.onerror = () => {
        console.error('Failed to queue form submission:', addRequest.error);
        reject(addRequest.error);
      };
    });
  }

  // Process queued requests when back online
  public async processQueue(): Promise<void> {
    if (!this.isInitialized || !navigator.onLine) {
      return;
    }

    console.log('Processing offline queue...');

    await Promise.all([
      this.processQueuedRequests(),
      this.processQueuedAnalytics(),
      this.processQueuedForms()
    ]);
  }

  private async processQueuedRequests(): Promise<void> {
    const requests = await this.getAllQueuedRequests();
    
    for (const request of requests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body
        });

        if (response.ok) {
          await this.removeQueuedRequest(request.id);
          console.log('Successfully synced queued request:', request.url);
        } else {
          await this.incrementRetryCount(request.id);
        }
      } catch (error) {
        console.error('Failed to sync queued request:', error);
        await this.incrementRetryCount(request.id);
      }
    }
  }

  private async processQueuedAnalytics(): Promise<void> {
    const events = await this.getAllQueuedAnalytics();
    
    for (const event of events) {
      try {
        // Send to analytics service
        const response = await fetch('/api/analytics/events', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            eventType: event.eventType,
            eventData: event.eventData,
            timestamp: event.timestamp,
            userId: event.userId,
            sessionId: event.sessionId,
            offline: true
          })
        });

        if (response.ok) {
          await this.removeQueuedAnalytics(event.id);
          console.log('Successfully synced analytics event:', event.eventType);
        }
      } catch (error) {
        console.error('Failed to sync analytics event:', error);
      }
    }
  }

  private async processQueuedForms(): Promise<void> {
    const forms = await this.getAllQueuedForms();
    
    for (const form of forms) {
      try {
        const endpoint = this.getFormEndpoint(form.formType);
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            ...form.formData,
            timestamp: form.timestamp,
            offline: true
          })
        });

        if (response.ok) {
          await this.removeQueuedForm(form.id);
          console.log('Successfully synced form submission:', form.formType);
        }
      } catch (error) {
        console.error('Failed to sync form submission:', error);
      }
    }
  }

  private getFormEndpoint(formType: string): string {
    const endpoints = {
      contact: '/api/contact',
      signup: '/api/auth/signup',
      newsletter: '/api/newsletter/subscribe'
    };
    return endpoints[formType as keyof typeof endpoints] || '/api/forms';
  }

  private async getAllQueuedRequests(): Promise<QueuedRequest[]> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['requests'], 'readonly');
      const store = transaction.objectStore('requests');
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  private async getAllQueuedAnalytics(): Promise<QueuedAnalyticsEvent[]> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analytics'], 'readonly');
      const store = transaction.objectStore('analytics');
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  private async getAllQueuedForms(): Promise<QueuedFormSubmission[]> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['forms'], 'readonly');
      const store = transaction.objectStore('forms');
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  private async removeQueuedRequest(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['requests'], 'readwrite');
      const store = transaction.objectStore('requests');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private async removeQueuedAnalytics(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analytics'], 'readwrite');
      const store = transaction.objectStore('analytics');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private async removeQueuedForm(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['forms'], 'readwrite');
      const store = transaction.objectStore('forms');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private async incrementRetryCount(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['requests'], 'readwrite');
      const store = transaction.objectStore('requests');
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const request = getRequest.result;
        if (request) {
          request.retryCount++;
          
          if (request.retryCount >= request.maxRetries) {
            // Remove request if max retries exceeded
            store.delete(id);
            console.log('Removed request after max retries:', request.url);
          } else {
            // Update retry count
            store.put(request);
          }
        }
        resolve();
      };

      getRequest.onerror = () => {
        reject(getRequest.error);
      };
    });
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('aquachain-session-id');
    if (!sessionId) {
      sessionId = this.generateId();
      sessionStorage.setItem('aquachain-session-id', sessionId);
    }
    return sessionId;
  }

  // Get queue statistics
  public async getQueueStats(): Promise<{
    requests: number;
    analytics: number;
    forms: number;
    total: number;
  }> {
    if (!this.isInitialized) {
      await this.initDB();
    }

    const [requests, analytics, forms] = await Promise.all([
      this.getAllQueuedRequests(),
      this.getAllQueuedAnalytics(),
      this.getAllQueuedForms()
    ]);

    return {
      requests: requests.length,
      analytics: analytics.length,
      forms: forms.length,
      total: requests.length + analytics.length + forms.length
    };
  }

  // Clear all queued items (for testing/debugging)
  public async clearQueue(): Promise<void> {
    if (!this.isInitialized) {
      await this.initDB();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['requests', 'analytics', 'forms'], 'readwrite');
      
      const clearRequests = transaction.objectStore('requests').clear();
      const clearAnalytics = transaction.objectStore('analytics').clear();
      const clearForms = transaction.objectStore('forms').clear();

      transaction.oncomplete = () => {
        console.log('Offline queue cleared');
        resolve();
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };
    });
  }
}

// Singleton instance
export const offlineQueueService = new OfflineQueueService();

// Auto-process queue when coming back online
window.addEventListener('online', () => {
  setTimeout(() => {
    offlineQueueService.processQueue();
  }, 1000); // Wait 1 second to ensure connection is stable
});

// Register background sync if supported
if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
  navigator.serviceWorker.ready.then((registration) => {
    // Register sync events
    window.addEventListener('online', () => {
      // Background sync is not available in all browsers
      if ('sync' in registration) {
        (registration as any).sync.register('offline-analytics');
        (registration as any).sync.register('offline-forms');
      }
    });
  });
}