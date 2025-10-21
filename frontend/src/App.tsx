import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnalyticsProvider } from './contexts/AnalyticsContext';
import LandingPage from './components/LandingPage/LandingPage';
import './App.css';

function App() {
  // Debug current location
  React.useEffect(() => {
    console.log('=== APP MOUNTED ===');
    console.log('Current location:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
  }, []);

  return (
    <AnalyticsProvider>
      <Router>
        <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
<LandingPage />
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
        </Routes>
      </div>
    </Router>
    </AnalyticsProvider>
  );
}

export default App;
