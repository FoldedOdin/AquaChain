/**
 * Real-Time Updates Hook
 * Manages WebSocket subscriptions for real-time data updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dataService } from '../services/dataService';

interface RealTimeUpdate {
  type: string;
  data: any;
  timestamp: string;
}

interface UseRealTimeUpdatesOptions {
  autoConnect?: boolean;
  autoReconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

interface UseRealTimeUpdatesReturn {
  updates: RealTimeUpdate[];
  latestUpdate: RealTimeUpdate | null;
  isConnected: boolean;
  error: Error | null;
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
    autoConnect = true,
    autoReconnect = true,
    reconnectDelay = 5000,
    maxReconnectAttempts = 5
  } = options;

  const [updates, setUpdates] = useState<RealTimeUpdate[]>([]);
  const [latestUpdate, setLatestUpdate] = useState<RealTimeUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const handleUpdate = useCallback((update: any) => {
    const realTimeUpdate: RealTimeUpdate = {
      type: update.type || 'unknown',
      data: update.data,
      timestamp: update.timestamp || new Date().toISOString()
    };

    setLatestUpdate(realTimeUpdate);
    setUpdates(prev => [realTimeUpdate, ...prev.slice(0, 99)]); // Keep last 100 updates
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      setError(null);

      // Subscribe to real-time updates
      dataService.subscribeToRealTimeUpdates(handleUpdate)
        .then(ws => {
          if (ws) {
            wsRef.current = ws;

            ws.onopen = () => {
              setIsConnected(true);
              reconnectAttemptsRef.current = 0;
              console.log(`Connected to ${subscriptionTopic}`);
            };

            ws.onclose = () => {
              setIsConnected(false);
              console.log(`Disconnected from ${subscriptionTopic}`);

              // Auto-reconnect if enabled
              if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
                reconnectAttemptsRef.current += 1;
                const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1); // Exponential backoff

                console.log(`Reconnecting to ${subscriptionTopic} (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}) in ${delay}ms`);

                reconnectTimeoutRef.current = setTimeout(() => {
                  connect();
                }, delay);
              } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
                setError(new Error(`Failed to reconnect after ${maxReconnectAttempts} attempts`));
              }
            };

            ws.onerror = (event) => {
              console.error(`WebSocket error on ${subscriptionTopic}:`, event);
              setError(new Error('WebSocket connection error'));
            };
          }
        })
        .catch(err => {
          console.error('Failed to setup WebSocket:', err);
          setError(err instanceof Error ? err : new Error('Failed to connect'));
        });
    } catch (err) {
      console.error('Error connecting to WebSocket:', err);
      setError(err instanceof Error ? err : new Error('Connection failed'));
    }
  }, [subscriptionTopic, handleUpdate, autoReconnect, reconnectDelay, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

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
    connect,
    disconnect,
    clearUpdates
  };
}
