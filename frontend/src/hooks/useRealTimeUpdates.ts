/**
 * Real-time Updates Hook with Development Mode Support
 * Handles WebSocket connections gracefully in development environments
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import websocketService from '../services/websocketService';

interface UseRealTimeUpdatesOptions {
  autoConnect?: boolean;
  enableInDevelopment?: boolean;
  fallbackPollingInterval?: number;
  /** Delay connection until this is true (e.g. wait for auth token to be available) */
  enabled?: boolean;
}

interface RealTimeUpdate {
  type: string;
  data?: any;
  timestamp?: string;
  topic?: string;
}

export function useRealTimeUpdates(
  topic: string,
  options: UseRealTimeUpdatesOptions = {}
) {
  const {
    autoConnect = true,
    enableInDevelopment = true,
    fallbackPollingInterval = 120000, // 2 minutes
    enabled = true
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [latestUpdate, setLatestUpdate] = useState<RealTimeUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error' | 'development_mode'>('disconnected');
  const [error, setError] = useState<string | null>(null);
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isMountedRef = useRef(false);
  // Latest handler ref — updated every render so stableHandler always delegates
  // to the most current closure without changing its own identity.
  const handleMessageRef = useRef<(data: any) => void>(null as any);
  // Stable subscriber — same object reference for the lifetime of this hook instance.
  // Registered once with websocketService; StrictMode unmount/remount won't create
  // a mismatched reference that bypasses the subscriber removal check.
  const stableHandler = useRef<(data: any) => void>((data) => {
    handleMessageRef.current?.(data);
  }).current;

  // Message handler for WebSocket updates
  const handleMessage = useCallback((data: any) => {
    try {
      // Handle different message types
      if (data.type === 'development_mode' || data.type === 'development_offline') {
        setConnectionStatus('development_mode');
        setIsConnected(false);
        setError('WebSocket server not available in development mode');
        
        if (isDevelopment) {
          // Only log once per session to avoid spam
          if (!sessionStorage.getItem(`websocket-dev-logged-${topic}`)) {
            console.log('🔧 Development Mode: WebSocket unavailable, using mock data');
            sessionStorage.setItem(`websocket-dev-logged-${topic}`, 'true');
          }
        }
        return;
      }

      if (data.type === 'connection_error') {
        setConnectionStatus('error');
        setIsConnected(false);
        setError(data.message || 'Connection failed');
        return;
      }

      // Handle successful connection
      if (data.type === 'connected' || data.type === 'subscribed') {
        setConnectionStatus('connected');
        setIsConnected(true);
        setError(null);
        return;
      }

      // Handle real-time updates
      if (data.type && data.type !== 'pong') {
        const update: RealTimeUpdate = {
          type: data.type,
          data: data.data || data,
          timestamp: data.timestamp || new Date().toISOString(),
          topic: data.topic || topic
        };
        
        setLatestUpdate(update);
        
        if (isDevelopment) {
          console.log('📡 Real-time update received:', update);
        }
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      setError('Failed to process real-time update');
    }
  }, [topic, isDevelopment]);

  // Keep the ref in sync with the latest handler — but the ref itself is stable
  // so websocketService always holds the same function reference.
  handleMessageRef.current = handleMessage;

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enableInDevelopment && isDevelopment) {
      setConnectionStatus('development_mode');
      setIsConnected(false);
      console.log('🔧 Real-time updates disabled in development mode');
      return;
    }

    try {
      setConnectionStatus('connecting');
      setError(null);
      
      websocketService.connect(topic, stableHandler);
      
      // Check connection status after a delay
      setTimeout(() => {
        if (!isMountedRef.current) return;
        const status = websocketService.getConnectionStatus(topic);
        if (status) {
          setIsConnected(status.isConnected);
          setConnectionStatus(status.isConnected ? 'connected' : 'disconnected');
        } else {
          setConnectionStatus('development_mode');
          setIsConnected(false);
        }
      }, 2000);
      
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setConnectionStatus('error');
      setError('Failed to establish real-time connection');
    }
  }, [topic, handleMessage, enableInDevelopment, isDevelopment]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    try {
      websocketService.disconnect(topic, stableHandler);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      setError(null);
      
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    } catch (error) {
      console.error('Failed to disconnect from WebSocket:', error);
    }
  }, [topic, handleMessage]);

  // Auto-connect on mount
  useEffect(() => {
    isMountedRef.current = true;

    if (autoConnect && enabled) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      isMountedRef.current = false;
      disconnect();
    };
    // connect/disconnect are intentionally excluded: including them causes
    // StrictMode to disconnect immediately after connecting on the first render.
    // autoConnect and enabled are the only values that should re-trigger this effect.
    // eslint-disable-next-line
  }, [autoConnect, enabled]);

  // Development mode fallback - simulate updates
  useEffect(() => {
    if (isDevelopment && connectionStatus === 'development_mode' && enableInDevelopment) {
      console.log('🔧 Starting development mode simulation for topic:', topic);
      
      // Simulate periodic updates in development using water_quality type
      // so the dashboard's latestUpdate handler actually processes them
      const interval = setInterval(() => {
        const mockUpdate: RealTimeUpdate = {
          type: 'water_quality',
          data: {
            deviceId: null, // null = applies to whichever device is selected
            timestamp: new Date().toISOString(),
            pH: parseFloat((6.5 + Math.random() * 2).toFixed(2)),
            turbidity: parseFloat((Math.random() * 5).toFixed(2)),
            tds: Math.round(100 + Math.random() * 400),
            temperature: parseFloat((20 + Math.random() * 15).toFixed(1)),
            wqi: Math.round(50 + Math.random() * 50),
            quality: 'Good',
            anomalyType: 'normal',
            sensorFault: false,
          },
          timestamp: new Date().toISOString(),
          topic
        };
        
        setLatestUpdate(mockUpdate);
        console.log('🎭 Dev mode water_quality update:', mockUpdate);
      }, fallbackPollingInterval);

      return () => clearInterval(interval);
    }
  }, [isDevelopment, connectionStatus, enableInDevelopment, topic, fallbackPollingInterval]);

  // Provide connection retry functionality
  const retry = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, 1000);
  }, [connect]);

  // Get detailed connection info
  const getConnectionInfo = useCallback(() => {
    const status = websocketService.getConnectionStatus(topic);
    return {
      topic,
      isConnected,
      connectionStatus,
      error,
      reconnectAttempts: status?.reconnectAttempts || 0,
      subscriberCount: status?.subscriberCount || 0,
      lastConnectedAt: status?.lastConnectedAt,
      isDevelopmentMode: isDevelopment && connectionStatus === 'development_mode'
    };
  }, [topic, isConnected, connectionStatus, error, isDevelopment]);

  return {
    // Connection state
    isConnected,
    connectionStatus,
    error,
    
    // Latest update
    latestUpdate,
    
    // Connection controls
    connect,
    disconnect,
    retry,
    
    // Utilities
    getConnectionInfo,
    
    // Development helpers
    isDevelopmentMode: isDevelopment && connectionStatus === 'development_mode',
    isSimulating: isDevelopment && connectionStatus === 'development_mode' && enableInDevelopment,
    
    // Additional properties for backward compatibility
    reconnectAttempts: getConnectionInfo().reconnectAttempts
  };
}