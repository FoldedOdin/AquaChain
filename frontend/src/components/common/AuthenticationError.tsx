import React from 'react';
import { ExclamationTriangleIcon, KeyIcon } from '@heroicons/react/24/outline';

interface AuthenticationErrorProps {
  onRetry?: () => void;
  onLogin?: () => void;
}

/**
 * AuthenticationError Component
 * 
 * Shows a helpful error message when API calls fail due to authentication issues.
 * Provides clear guidance on how to resolve the problem.
 */
const AuthenticationError: React.FC<AuthenticationErrorProps> = ({ onRetry, onLogin }) => {
  const token = localStorage.getItem('aquachain_token');
  const isDevelopmentToken = token && token.startsWith('dev-token-');
  
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 max-w-2xl mx-auto">
      <div className="flex items-start space-x-3">
        <ExclamationTriangleIcon className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-amber-900 mb-2">
            Authentication Issue Detected
          </h3>
          
          {!token ? (
            <>
              <p className="text-amber-800 mb-4">
                No authentication token found. Please log in to access your dashboard.
              </p>
              <div className="flex space-x-3">
                {onLogin && (
                  <button
                    onClick={onLogin}
                    className="flex items-center space-x-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
                  >
                    <KeyIcon className="w-4 h-4" />
                    <span>Log In</span>
                  </button>
                )}
              </div>
            </>
          ) : isDevelopmentToken ? (
            <>
              <p className="text-amber-800 mb-4">
                You're using a development token with a production API. This causes authentication failures 
                and "API error: undefined" messages.
              </p>
              <div className="bg-amber-100 border border-amber-300 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-amber-900 mb-2">Quick Solutions:</h4>
                <ul className="text-sm text-amber-800 space-y-1">
                  <li>• Log out and log back in with proper credentials</li>
                  <li>• Use mock data for development (switch to MockDataService)</li>
                  <li>• Set up proper AWS Cognito authentication</li>
                </ul>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    localStorage.removeItem('aquachain_token');
                    localStorage.removeItem('authToken');
                    window.location.reload();
                  }}
                  className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
                >
                  Clear Tokens & Reload
                </button>
                {onRetry && (
                  <button
                    onClick={onRetry}
                    className="px-4 py-2 border border-amber-600 text-amber-600 rounded-lg hover:bg-amber-50 transition"
                  >
                    Retry
                  </button>
                )}
              </div>
            </>
          ) : (
            <>
              <p className="text-amber-800 mb-4">
                Authentication token appears invalid or expired. Please try logging in again.
              </p>
              <div className="flex space-x-3">
                {onLogin && (
                  <button
                    onClick={onLogin}
                    className="flex items-center space-x-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
                  >
                    <KeyIcon className="w-4 h-4" />
                    <span>Log In Again</span>
                  </button>
                )}
                {onRetry && (
                  <button
                    onClick={onRetry}
                    className="px-4 py-2 border border-amber-600 text-amber-600 rounded-lg hover:bg-amber-50 transition"
                  >
                    Retry
                  </button>
                )}
              </div>
            </>
          )}
          
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-900">
              <strong>For Developers:</strong> Check the browser console for detailed error messages. 
              The issue is typically caused by using development tokens with production APIs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthenticationError;