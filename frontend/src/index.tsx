import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './styles/animations.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';

// Debug initial state (development only)
if (process.env.NODE_ENV === 'development') {
  // eslint-disable-next-line no-console
  console.log('=== INITIAL DEBUG INFO ===');
  // eslint-disable-next-line no-console
  console.log('Initial URL:', window.location.href);
  // eslint-disable-next-line no-console
  console.log('Initial pathname:', window.location.pathname);
  // eslint-disable-next-line no-console
  console.log('Initial search:', window.location.search);
  // eslint-disable-next-line no-console
  console.log('Initial hash:', window.location.hash);
  // eslint-disable-next-line no-console
  console.log('Document referrer:', document.referrer);
  // eslint-disable-next-line no-console
  console.log('History length:', window.history.length);

  // Force URL to root if it's trying to go to dashboard in development
  if (window.location.pathname === '/dashboard') {
    // eslint-disable-next-line no-console
    console.log('DETECTED DASHBOARD REDIRECT - FORCING BACK TO ROOT');
    window.history.replaceState(null, '', '/');
  }
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);

// Clear service worker cache in development to ensure fresh routing
if (process.env.NODE_ENV === 'development' && 'serviceWorker' in navigator) {
  // eslint-disable-next-line no-console
  console.log('Clearing service worker cache for fresh routing...');
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (const registration of registrations) {
      // eslint-disable-next-line no-console
      console.log('Unregistering service worker:', registration);
      registration.unregister();
    }
  });

  // Clear all caches
  if ('caches' in window) {
    caches.keys().then(function (names) {
      // eslint-disable-next-line no-console
      console.log('Clearing caches:', names);
      for (const name of names) {
        caches.delete(name);
      }
    });
  }

  // Clear localStorage that might contain routing info
  sessionStorage.clear();
}
