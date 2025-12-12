import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPageWithAnalytics from './components/LandingPage/LandingPageWithAnalytics';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import ErrorBoundary from './components/ErrorBoundary';
import performanceMonitor from './services/performanceMonitor';
import GoogleCallbackHandler from './components/Auth/GoogleCallbackHandler';
import './App.css';

// ✅ Lazy load dashboard components for code splitting
const ConsumerDashboard = lazy(() => import('./components/Dashboard/ConsumerDashboard'));
const TechnicianDashboard = lazy(() => import('./components/Dashboard/TechnicianDashboard'));
const AdminDashboard = lazy(() => import('./components/Dashboard/AdminDashboard'));

// ✅ Loading component for Suspense fallback
const DashboardLoadingFallback = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading dashboard...</p>
    </div>
  </div>
);

function App() {
  // Initialize performance monitoring
  useEffect(() => {
    // Mark app initialization
    performanceMonitor.mark('app-init');

    // Debug current location (development only)
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log('=== APP MOUNTED ===');
      // eslint-disable-next-line no-console
      console.log('Current location:', window.location.href);
      // eslint-disable-next-line no-console
      console.log('Current pathname:', window.location.pathname);
    }

    // Cleanup on unmount
    return () => {
      performanceMonitor.disconnect();
    };
  }, []);

  return (
    // ✅ Wrap entire app in Error Boundary
    <ErrorBoundary>
      <AuthProvider>
        <NotificationProvider>
          <Router>
            <div className="App">
              <Routes>
            <Route
              path="/"
              element={<LandingPageWithAnalytics />}
            />
            
            {/* Protected Dashboard Routes with Lazy Loading */}
            <Route
              path="/dashboard/consumer"
              element={
                <ProtectedRoute requiredRole="consumer">
                  <Suspense fallback={<DashboardLoadingFallback />}>
                    <ConsumerDashboard />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/dashboard/technician"
              element={
                <ProtectedRoute requiredRole="technician">
                  <Suspense fallback={<DashboardLoadingFallback />}>
                    <TechnicianDashboard />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/dashboard/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <Suspense fallback={<DashboardLoadingFallback />}>
                    <AdminDashboard />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            {/* Generic dashboard route - redirects based on user role */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
                      <p className="text-gray-600">Redirecting to your dashboard...</p>
                    </div>
                  </div>
                </ProtectedRoute>
              }
            />
            
            {/* Google OAuth callback */}
            <Route
              path="/auth/google/callback"
              element={<GoogleCallbackHandler />}
            />
            
            {/* Authentication callback */}
            <Route
              path="/auth/callback"
              element={
                <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
                    <h1 className="text-xl font-semibold text-gray-900 mb-2">Processing Authentication</h1>
                    <p className="text-gray-600">Please wait while we complete your login...</p>
                  </div>
                </div>
              }
            />
            
            {/* Logout confirmation */}
            <Route
              path="/auth/logout"
              element={
                <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                  <div className="text-center max-w-md mx-auto p-6">
                    <div className="mb-6">
                      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <h1 className="text-2xl font-bold text-gray-900 mb-2">Successfully Logged Out</h1>
                      <p className="text-gray-600 mb-6">You have been safely signed out of your AquaChain account.</p>
                    </div>
                    <button 
                      onClick={() => window.location.href = '/'}
                      className="bg-aqua-600 hover:bg-aqua-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
                    >
                      Return to Home
                    </button>
                  </div>
                </div>
              }
            />

            {/* Catch-all route - redirect to home */}
            <Route
              path="*"
              element={
                <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                  <div className="text-center max-w-md mx-auto p-6">
                    <div className="mb-6">
                      <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                      <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
                      <p className="text-gray-600 mb-6">The page you're looking for doesn't exist or has been moved.</p>
                    </div>
                    <button 
                      onClick={() => window.location.href = '/'}
                      className="bg-aqua-600 hover:bg-aqua-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
                    >
                      Go to Home
                    </button>
                  </div>
                </div>
              }
            />
              </Routes>
            </div>
          </Router>
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
