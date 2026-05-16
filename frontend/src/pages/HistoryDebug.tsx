import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import dataService from '../services/dataService';

/**
 * Debug page to diagnose reading history issues
 * Shows authentication status, API connectivity, and data fetching
 */
const HistoryDebug = () => {
  const { user, isAuthenticated } = useAuth();
  const [diagnostics, setDiagnostics] = useState<any>({
    authStatus: 'checking',
    tokenStatus: 'checking',
    apiStatus: 'checking',
    dataStatus: 'checking',
    readings: [],
    errors: []
  });

  useEffect(() => {
    runDiagnostics();
  }, []);

  const runDiagnostics = async () => {
    const results: any = {
      authStatus: 'unknown',
      tokenStatus: 'unknown',
      apiStatus: 'unknown',
      dataStatus: 'unknown',
      readings: [],
      errors: []
    };

    // Check 1: Authentication Status
    console.log('🔍 [Debug] Checking authentication...');
    if (isAuthenticated && user) {
      results.authStatus = 'authenticated';
      results.user = {
        email: user.email,
        role: user.role,
        userId: user.userId,
        deviceIds: user.deviceIds
      };
    } else {
      results.authStatus = 'not_authenticated';
      results.errors.push('User is not authenticated');
    }

    // Check 2: Token Status
    console.log('🔍 [Debug] Checking token...');
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    if (token) {
      results.tokenStatus = 'present';
      results.tokenPreview = token.substring(0, 30) + '...';
      results.tokenLength = token.length;
      
      // Check if it's a development token
      if (token.startsWith('dev-token-')) {
        results.tokenType = 'development';
        results.errors.push('Using development token - will not work with production API');
      } else {
        results.tokenType = 'production';
      }
    } else {
      results.tokenStatus = 'missing';
      results.errors.push('No authentication token found in localStorage');
    }

    // Check 3: API Connectivity
    console.log('🔍 [Debug] Testing API connectivity...');
    const deviceId = user?.deviceIds?.[0] || 'ESP32-001';
    try {
      const readings = await dataService.getDeviceReadings(deviceId, 7);
      results.apiStatus = 'connected';
      results.readings = readings;
      results.dataStatus = readings.length > 0 ? 'data_found' : 'no_data';
      
      if (readings.length > 0) {
        results.latestReading = readings[0];
        results.oldestReading = readings[readings.length - 1];
      }
    } catch (error: any) {
      results.apiStatus = 'error';
      results.dataStatus = 'error';
      results.errors.push(`API Error: ${error.message}`);
      
      if (error.status === 401) {
        results.errors.push('Authentication failed - token may be expired or invalid');
      } else if (error.status === 403) {
        results.errors.push('Access forbidden - insufficient permissions');
      } else if (error.status === 404) {
        results.errors.push('API endpoint not found');
      }
    }

    setDiagnostics(results);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'authenticated':
      case 'connected':
      case 'present':
      case 'data_found':
        return 'text-green-600 bg-green-50';
      case 'not_authenticated':
      case 'missing':
      case 'error':
      case 'no_data':
        return 'text-red-600 bg-red-50';
      case 'checking':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          📊 Reading History Diagnostics
        </h1>
        <p className="text-gray-600 mb-6">
          This page helps diagnose why reading history might be empty
        </p>

        {/* Authentication Status */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">1. Authentication Status</h2>
          <div className={`p-4 rounded-lg ${getStatusColor(diagnostics.authStatus)}`}>
            <div className="font-medium">Status: {diagnostics.authStatus}</div>
            {diagnostics.user && (
              <div className="mt-2 text-sm space-y-1">
                <div>Email: {diagnostics.user.email}</div>
                <div>Role: {diagnostics.user.role}</div>
                <div>User ID: {diagnostics.user.userId}</div>
                <div>Devices: {diagnostics.user.deviceIds?.join(', ') || 'None'}</div>
              </div>
            )}
          </div>
        </div>

        {/* Token Status */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">2. Token Status</h2>
          <div className={`p-4 rounded-lg ${getStatusColor(diagnostics.tokenStatus)}`}>
            <div className="font-medium">Status: {diagnostics.tokenStatus}</div>
            {diagnostics.tokenPreview && (
              <div className="mt-2 text-sm space-y-1">
                <div>Preview: {diagnostics.tokenPreview}</div>
                <div>Length: {diagnostics.tokenLength} characters</div>
                <div>Type: {diagnostics.tokenType}</div>
              </div>
            )}
          </div>
        </div>

        {/* API Status */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">3. API Connectivity</h2>
          <div className={`p-4 rounded-lg ${getStatusColor(diagnostics.apiStatus)}`}>
            <div className="font-medium">Status: {diagnostics.apiStatus}</div>
          </div>
        </div>

        {/* Data Status */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">4. Data Status</h2>
          <div className={`p-4 rounded-lg ${getStatusColor(diagnostics.dataStatus)}`}>
            <div className="font-medium">Status: {diagnostics.dataStatus}</div>
            {diagnostics.readings.length > 0 && (
              <div className="mt-2 text-sm space-y-1">
                <div>Total Readings: {diagnostics.readings.length}</div>
                <div>Latest: {diagnostics.latestReading?.timestamp}</div>
                <div>Oldest: {diagnostics.oldestReading?.timestamp}</div>
              </div>
            )}
          </div>
        </div>

        {/* Errors */}
        {diagnostics.errors.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-red-900 mb-3">⚠️ Issues Found</h2>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <ul className="list-disc list-inside space-y-2 text-red-700">
                {diagnostics.errors.map((error: string, index: number) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-4">
          <button
            onClick={runDiagnostics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            🔄 Re-run Diagnostics
          </button>
          <button
            onClick={() => window.location.href = '/history'}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            ← Back to History
          </button>
        </div>
      </div>

      {/* Raw Data */}
      {diagnostics.readings.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">📦 Raw Reading Data</h2>
          <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-xs">
            {JSON.stringify(diagnostics.readings.slice(0, 3), null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default HistoryDebug;
