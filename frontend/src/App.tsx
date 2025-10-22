import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPageWithAnalytics from './components/LandingPage/LandingPageWithAnalytics';
import './App.css';

function App() {
  // Debug current location (development only)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log('=== APP MOUNTED ===');
      // eslint-disable-next-line no-console
      console.log('Current location:', window.location.href);
      // eslint-disable-next-line no-console
      console.log('Current pathname:', window.location.pathname);
    }
  }, []);

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route
            path="/"
            element={
              <LandingPageWithAnalytics />
            }
          />
          <Route
            path="/dashboard"
            element={
              <div style={{ padding: '20px', backgroundColor: 'lightblue', minHeight: '100vh' }}>
                <h1>Dashboard Page</h1>
                <p>This is the dashboard page.</p>
                <button onClick={() => window.location.href = '/'}>Go to Landing Page</button>
              </div>
            }
          />
          <Route
            path="/dashboard/consumer"
            element={
              <div style={{ padding: '20px', backgroundColor: 'lightgreen', minHeight: '100vh' }}>
                <h1>Consumer Dashboard</h1>
                <p>Water quality monitoring dashboard for consumers.</p>
                <button onClick={() => window.location.href = '/'}>Go to Landing Page</button>
              </div>
            }
          />
          <Route
            path="/dashboard/technician"
            element={
              <div style={{ padding: '20px', backgroundColor: 'lightyellow', minHeight: '100vh' }}>
                <h1>Technician Dashboard</h1>
                <p>Field service dashboard for technicians.</p>
                <button onClick={() => window.location.href = '/'}>Go to Landing Page</button>
              </div>
            }
          />
          <Route
            path="/dashboard/admin"
            element={
              <div style={{ padding: '20px', backgroundColor: 'lightcoral', minHeight: '100vh' }}>
                <h1>Admin Dashboard</h1>
                <p>System management dashboard for administrators.</p>
                <button onClick={() => window.location.href = '/'}>Go to Landing Page</button>
              </div>
            }
          />
          <Route
            path="/auth/callback"
            element={
              <div style={{ padding: '20px', textAlign: 'center', minHeight: '100vh' }}>
                <h1>Authentication Callback</h1>
                <p>Processing authentication...</p>
              </div>
            }
          />
          <Route
            path="/auth/logout"
            element={
              <div style={{ padding: '20px', textAlign: 'center', minHeight: '100vh' }}>
                <h1>Logged Out</h1>
                <p>You have been successfully logged out.</p>
                <button onClick={() => window.location.href = '/'}>Return to Home</button>
              </div>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
