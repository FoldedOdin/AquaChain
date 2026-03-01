/**
 * Auth Debug Panel
 * Temporary component to help diagnose authentication issues
 * Remove this in production!
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const AuthDebugPanel: React.FC = () => {
  const { user, isAuthenticated, getAuthToken } = useAuth();
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [showPanel, setShowPanel] = useState(false);

  useEffect(() => {
    const checkToken = async () => {
      const token = await getAuthToken();
      
      if (token) {
        try {
          // Decode JWT token
          const parts = token.split('.');
          if (parts.length === 3) {
            const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
            setTokenInfo({
              tokenType: payload.token_use,
              username: payload.username || payload['cognito:username'],
              email: payload.email,
              exp: new Date(payload.exp * 1000).toLocaleString(),
              iss: payload.iss,
              clientId: payload.client_id || payload.aud,
              isExpired: Date.now() / 1000 > payload.exp,
              tokenLength: token.length
            });
          }
        } catch (error) {
          console.error('Failed to decode token:', error);
        }
      }
    };

    if (isAuthenticated) {
      checkToken();
    }
  }, [isAuthenticated, getAuthToken]);

  if (!showPanel) {
    return (
      <button
        onClick={() => setShowPanel(true)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '10px 15px',
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '12px',
          zIndex: 9999,
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}
      >
        🔍 Auth Debug
      </button>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        width: '400px',
        maxHeight: '600px',
        overflow: 'auto',
        background: 'white',
        border: '2px solid #3b82f6',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
        zIndex: 9999,
        fontSize: '13px',
        fontFamily: 'monospace'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>🔐 Auth Debug Panel</h3>
        <button
          onClick={() => setShowPanel(false)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            color: '#6b7280'
          }}
        >
          ×
        </button>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}>Authentication Status</div>
        <div style={{ padding: '10px', background: isAuthenticated ? '#d1fae5' : '#fee2e2', borderRadius: '6px' }}>
          {isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated'}
        </div>
      </div>

      {user && (
        <div style={{ marginBottom: '15px' }}>
          <div style={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}>User Info</div>
          <div style={{ padding: '10px', background: '#f3f4f6', borderRadius: '6px' }}>
            <div><strong>Email:</strong> {user.email}</div>
            <div><strong>Role:</strong> {user.role}</div>
            <div><strong>User ID:</strong> {user.userId}</div>
          </div>
        </div>
      )}

      {tokenInfo && (
        <div style={{ marginBottom: '15px' }}>
          <div style={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}>Token Info</div>
          <div style={{ padding: '10px', background: tokenInfo.isExpired ? '#fee2e2' : '#f3f4f6', borderRadius: '6px' }}>
            <div><strong>Type:</strong> {tokenInfo.tokenType}</div>
            <div><strong>Username:</strong> {tokenInfo.username}</div>
            <div><strong>Email:</strong> {tokenInfo.email}</div>
            <div><strong>Expires:</strong> {tokenInfo.exp}</div>
            <div><strong>Status:</strong> {tokenInfo.isExpired ? '❌ EXPIRED' : '✅ Valid'}</div>
            <div><strong>Length:</strong> {tokenInfo.tokenLength} chars</div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#6b7280' }}>
              <strong>Issuer:</strong><br />
              {tokenInfo.iss}
            </div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '15px' }}>
        <div style={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}>LocalStorage</div>
        <div style={{ padding: '10px', background: '#f3f4f6', borderRadius: '6px' }}>
          <div>
            <strong>aquachain_token:</strong>{' '}
            {localStorage.getItem('aquachain_token') ? '✅ Present' : '❌ Missing'}
          </div>
          <div>
            <strong>aquachain_user:</strong>{' '}
            {localStorage.getItem('aquachain_user') ? '✅ Present' : '❌ Missing'}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}>Environment</div>
        <div style={{ padding: '10px', background: '#f3f4f6', borderRadius: '6px', fontSize: '11px' }}>
          <div><strong>Auth Mode:</strong> {process.env.REACT_APP_AUTH_MODE || 'Not set'}</div>
          <div><strong>API Endpoint:</strong> {process.env.REACT_APP_API_ENDPOINT || 'Not set'}</div>
          <div><strong>User Pool:</strong> {process.env.REACT_APP_USER_POOL_ID || 'Not set'}</div>
        </div>
      </div>

      <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '15px', padding: '10px', background: '#fef3c7', borderRadius: '6px' }}>
        ⚠️ <strong>Note:</strong> Remove this component in production!
      </div>
    </div>
  );
};

export default AuthDebugPanel;
