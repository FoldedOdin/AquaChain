/**
 * Real-Time Updates Hook
 * Manages WebSocket subscriptions for real-time data updates
 * Uses WebSocketService for connection pooling and automatic reconnection
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { websocketService } from '../services/websocketService';
import { useNotifications } from '../contexts/NotificationContext';

interface RealTimeUpdate {
  type: string;
  data: any;
  timestamp: string;
}

interface UseRealTimeUpdatesOptions {
  autoConnect?: boolean;
}

interface UseRealTimeUpdatesReturn {
  updates: RealTimeUpdate[];
  latestUpdate: RealTimeUpdate | null;
  isConnected: boolean;
  error: Error | null;
  reconnectAttempts: number;
  connect: () => void;
  disconnect: () => void;
  clearUpdates: () => void;
}

/**
 * Custom hook for managing WebSocket subscriptions to real-time updates
 * @param subscriptionTopic - The topic to subscribe to (e.g., 'admin-alerts', 'device-updates')
 * @param options - Configuration options for the WebSocket connection
 * @returns Real-time updates, connection state, and control functions
 */
export function useRealTimeUpdates(
  subscriptionTopic: string,
  options: UseRealTimeUpdatesOptions = {}
): UseRealTimeUpdatesReturn {
  const {
    autoConnect = true
  } = options;

  const [updates, setUpdates] = useState<RealTimeUpdate[]>([]);
  const [latestUpdate, setLatestUpdate] = useState<RealTimeUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const statusCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlerRef = useRef<((data: any) => void) | null>(null);
  const { addNotification } = useNotifications();

  const handleUpdate = useCallback((update: any) => {
    // Handle connection error messages
    if (update.type === 'connection_error') {
      setError(new Error(update.message));
      setIsConnected(false);
      
      // Show user notification
      addNotification({
        type: 'error',
        title: 'Connection Lost',
        message: `Unable to maintain connection to ${update.topic}. ${update.message}`,
        duration: 0 // Don't auto-dismiss
      });
      
      return;
    }

    const realTimeUpdate: RealTimeUpdate = {
      type: update.type || 'unknown',
      data: update.data,
      timestamp: update.timestamp || new Date().toISOString()
    };

    setLatestUpdate(realTimeUpdate);
    setUpdates(prev => [realTimeUpdate, ...prev.slice(0, 99)]); // Keep last 100 updates
    setError(null); // Clear any previous errors on successful message
  }, [addNotification]);

  // Store the handler reference so we can disconnect properly
  useEffect(() => {
    messageHandlerRef.current = handleUpdate;
  }, [handleUpdate]);

  const connect = useCallback(() => {
    setError(null);
    websocketService.connect(subscriptionTopic, handleUpdate);

    // Start polling connection status
    if (statusCheckIntervalRef.current) {
      clearInterval(statusCheckIntervalRef.current);
    }

    statusCheckIntervalRef.current = setInterval(() => {
      const status = websocketService.getConnectionStatus(subscriptionTopic);
      if (status) {
        setIsConnected(status.isConnected);
        setReconnectAttempts(status.reconnectAttempts);
      } else {
        setIsConnected(false);
        setReconnectAttempts(0);
      }
    }, 1000);
  }, [subscriptionTopic, handleUpdate]);

  const disconnect = useCallback(() => {
    if (statusCheckIntervalRef.current) {
      clearInterval(statusCheckIntervalRef.current);
      statusCheckIntervalRef.current = null;
    }

    if (messageHandlerRef.current) {
      websocketService.disconnect(subscriptionTopic, messageHandlerRef.current);
    }

    setIsConnected(false);
    setReconnectAttempts(0);
  }, [subscriptionTopic]);

  const clearUpdates = useCallback(() => {
    setUpdates([]);
    setLatestUpdate(null);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    updates,
    latestUpdate,
    isConnected,
    error,
    reconnectAttempts,
    connect,
    disconnect,
    clearUpdates
  };
}
