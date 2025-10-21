import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './styles/animations.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { initializeRUM } from './services/rumService';

// Debug initial state
console.log('=== INITIAL DEBUG INFO ===');
console.log('Initial URL:', window.location.href);
console.log('Initial pathname:', window.location.pathname);
console.log('Initial search:', window.location.search);
console.log('Initial hash:', window.location.hash);
console.log('Document referrer:', document.referrer);
console.log('History length:', window.history.length);

// Force URL to root if it's trying to go to dashboard in development
if (process.env.NODE_ENV === 'development' && window.location.pathname === '/dashboard') {
  console.log('DETECTED DASHBOARD REDIRECT - FORCING BACK TO ROOT');
  window.history.replaceState(null, '', '/');
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Clear service worker cache in development to ensure fresh routing
if (process.env.NODE_ENV === 'development' && 'serviceWorker' in navigator) {
  console.log('Clearing service worker cache for fresh routing...');
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (const registration of registrations) {
      console.log('Unregistering service worker:', registration);
      registration.unregister();
    }
  });

  // Clear all caches
  if ('caches' in window) {
    caches.keys().then(function (names) {
      console.log('Clearing caches:', names);
      for (const name of names) {
        caches.delete(name);
      }
    });
  }

  // Clear localStorage that might contain routing info
  localStorage.removeItem('aquachain_rum');
  sessionStorage.clear();
}

// Initialize Real User Monitoring
const rum = initializeRUM({
  apiEndpoint: process.env.REACT_APP_RUM_ENDPOINT || '/api/rum',
  batchSize: 10,
  flushInterval: 30000,
  enableLocalStorage: process.env.NODE_ENV === 'development',
  enableBeacon: true
});

// Enhanced Web Vitals reporting with analytics integration
reportWebVitals((metric) => {
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.log('[Web Vitals]', metric);
  }

  // Send to RUM service
  if (rum) {
    rum.recordCustomEvent('web-vital', {
      name: metric.name,
      value: metric.value,
      delta: metric.delta,
      id: metric.id
    });
  }
});
