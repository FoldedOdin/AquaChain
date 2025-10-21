// AquaChain Landing Page Service Worker
// Implements cache-first strategy for static assets and network-first for API calls

const CACHE_NAME = 'aquachain-landing-v1.0.1';
const OFFLINE_CACHE = 'aquachain-offline-v1.0.1';
const API_CACHE = 'aquachain-api-v1.0.1';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/offline.html'
];

// API endpoints that should use network-first strategy
const API_ENDPOINTS = [
  '/api/auth',
  '/api/demo',
  '/api/contact',
  'https://cognito-idp.us-east-1.amazonaws.com',
  'https://accounts.google.com'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS.filter(url => url !== '/offline.html'));
      }),
      
      // Cache offline page separately
      caches.open(OFFLINE_CACHE).then((cache) => {
        console.log('[SW] Caching offline page');
        return cache.add('/offline.html');
      })
    ]).then(() => {
      console.log('[SW] Installation complete');
      // Force activation of new service worker
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches that don't match current version
          if (cacheName !== CACHE_NAME && 
              cacheName !== OFFLINE_CACHE && 
              cacheName !== API_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Activation complete');
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // API requests - Network first with cache fallback
  if (isApiRequest(request.url)) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }
  
  // Static assets - Cache first with network fallback
  if (isStaticAsset(request.url)) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }
  
  // Navigation requests - Cache first with offline fallback
  if (request.mode === 'navigate') {
    event.respondWith(navigationStrategy(request));
    return;
  }
  
  // Default - Network first
  event.respondWith(networkFirstStrategy(request));
});

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }
    
    console.log('[SW] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache-first strategy failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/offline.html');
      return offlineResponse || new Response('Offline', { status: 503 });
    }
    
    return new Response('Network Error', { status: 503 });
  }
}

// Network-first strategy for API calls
async function networkFirstStrategy(request) {
  try {
    console.log('[SW] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    // Cache successful API responses (except auth endpoints)
    if (networkResponse.status === 200 && !isAuthEndpoint(request.url)) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving stale data from cache:', request.url);
      return cachedResponse;
    }
    
    console.error('[SW] Network-first strategy failed:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Network unavailable', 
        offline: true,
        timestamp: Date.now()
      }), 
      { 
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Navigation strategy for page requests
async function navigationStrategy(request) {
  try {
    // Try network first for navigation
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('[SW] Navigation network failed, trying cache');
    
    // Try to serve cached version of the page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Try to serve cached index.html for SPA routing
    const indexResponse = await caches.match('/');
    if (indexResponse) {
      return indexResponse;
    }
    
    // Fallback to offline page
    const offlineResponse = await caches.match('/offline.html');
    return offlineResponse || new Response('Offline', { status: 503 });
  }
}

// Helper functions
function isApiRequest(url) {
  return API_ENDPOINTS.some(endpoint => url.includes(endpoint)) ||
         url.includes('/api/') ||
         url.includes('amazonaws.com') ||
         url.includes('google.com/oauth');
}

function isStaticAsset(url) {
  return url.includes('/static/') ||
         url.includes('.js') ||
         url.includes('.css') ||
         url.includes('.png') ||
         url.includes('.jpg') ||
         url.includes('.ico') ||
         url.includes('.woff') ||
         url.includes('.woff2');
}

function isAuthEndpoint(url) {
  return url.includes('/auth/') ||
         url.includes('cognito-idp') ||
         url.includes('oauth');
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'offline-analytics') {
    event.waitUntil(syncOfflineAnalytics());
  }
  
  if (event.tag === 'offline-forms') {
    event.waitUntil(syncOfflineForms());
  }
});

// Sync offline analytics events
async function syncOfflineAnalytics() {
  try {
    const cache = await caches.open('offline-queue');
    const requests = await cache.keys();
    
    for (const request of requests) {
      if (request.url.includes('analytics')) {
        try {
          await fetch(request);
          await cache.delete(request);
          console.log('[SW] Synced offline analytics event');
        } catch (error) {
          console.log('[SW] Failed to sync analytics event:', error);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Analytics sync failed:', error);
  }
}

// Sync offline form submissions
async function syncOfflineForms() {
  try {
    const cache = await caches.open('offline-queue');
    const requests = await cache.keys();
    
    for (const request of requests) {
      if (request.url.includes('contact') || request.url.includes('signup')) {
        try {
          await fetch(request);
          await cache.delete(request);
          console.log('[SW] Synced offline form submission');
        } catch (error) {
          console.log('[SW] Failed to sync form submission:', error);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Form sync failed:', error);
  }
}

// Handle push notifications (for future features)
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New AquaChain notification',
    icon: '/logo192.png',
    badge: '/favicon.ico',
    vibrate: [200, 100, 200],
    data: {
      url: '/'
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
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('AquaChain', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url || '/')
    );
  }
});

// Cache versioning and update mechanism
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[SW] Received skip waiting message');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({
      type: 'VERSION',
      version: CACHE_NAME
    });
  }
});