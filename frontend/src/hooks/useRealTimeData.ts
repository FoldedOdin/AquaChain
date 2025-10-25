/**
 * Real-time Data Hook
 * Manages real-time data fetching and WebSocket connections
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dataService } from '../services/dataService';
import { WaterQualityReading, Alert, DeviceStatus } from '../types';

interface UseRealTimeDataOptions {
  enableRealTime?: boolean;
  refreshInterval?: number;
  autoReconnect?: boolean;
}

interface RealTimeData {
  waterQuality: WaterQualityReading[];
  latestReading: WaterQualityReading | null;
  devices: DeviceStatus[];
  alerts: Alert[];
  stats: {
    totalDevices: number;
    activeDevices: number;
    criticalAlerts: number;
    averageWQI: number;
    totalUsers: number;
    pendingRequests: number;
  };
  isLoading: boolean;
  isConnected: boolean;
  lastUpdated: Date | null;
  error: string | null;
}

export const useRealTimeData = (options: UseRealTimeDataOptions = {}) => {
  const {
    enableRealTime = true,
    refreshInterval = 30000, // 30 seconds
    autoReconnect = true,
  } = options;

  const [data, setData] = useState<RealTimeData>({
    waterQuality: [],
    latestReading: null,
    devices: [],
    alerts: [],
    stats: {
      totalDevices: 0,
      activeDevices: 0,
      criticalAlerts: 0,
      averageWQI: 0,
      totalUsers: 0,
      pendingRequests: 0,
    },
    isLoading: true,
    isConnected: false,
    lastUpdated: null,
    error: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlerRef = useRef<((data: any) => void) | null>(null);

  // Fetch all data from API
  const fetchData = useCallback(async () => {
    try {
      setData(prev => ({ ...prev, isLoading: true, error: null }));

      const [
        waterQuality,
        latestReading,
        devices,
        alerts,
        stats
      ] = await Promise.all([
        dataService.getWaterQualityData('24h'),
        dataService.getLatestWaterQuality(),
        dataService.getDevices(),
        dataService.getAlerts(20),
        dataService.getDashboardStats(),
      ]);

      setData(prev => ({
        ...prev,
        waterQuality: waterQuality || [],
        latestReading: latestReading || null,
        devices: devices || [],
        alerts: alerts || [],
        stats: stats || {
          totalDevices: 0,
          activeDevices: 0,
          criticalAlerts: 0,
          averageWQI: 0,
          totalUsers: 0,
          pendingRequests: 0,
        },
        isLoading: false,
        lastUpdated: new Date(),
        error: null,
      }));

    } catch (error) {
      console.error('Failed to fetch data:', error);
      setData(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load data from server',
      }));
    }
  }, []);

  // Handle real-time updates via WebSocket
  const handleRealTimeUpdate = useCallback((update: any) => {
    setData(prev => {
      const newData = { ...prev };

      switch (update.type) {
        case 'water_quality':
          if (update.data) {
            newData.latestReading = update.data;
            newData.waterQuality = [update.data, ...prev.waterQuality.slice(0, 99)];
          }
          break;

        case 'device_status':
          if (update.data) {
            const deviceIndex = prev.devices.findIndex(d => d.id === update.data.id);
            if (deviceIndex >= 0) {
              newData.devices = [...prev.devices];
              newData.devices[deviceIndex] = update.data;
            } else {
              newData.devices = [update.data, ...prev.devices];
            }
          }
          break;

        case 'alert':
          if (update.data) {
            newData.alerts = [update.data, ...prev.alerts.slice(0, 19)];
          }
          break;

        case 'stats':
          if (update.data) {
            newData.stats = { ...prev.stats, ...update.data };
          }
          break;

        default:
          console.log('Unknown update type:', update.type);
      }

      newData.lastUpdated = new Date();
      return newData;
    });
  }, []);

  // Setup WebSocket connection using WebSocketService
  const setupWebSocket = useCallback(() => {
    if (!enableRealTime) return;

    try {
      // Import websocketService dynamically to avoid circular dependencies
      import('../services/websocketService').then(({ websocketService }) => {
        websocketService.connect('real-time-data', handleRealTimeUpdate);
        
        // Poll connection status
        const statusInterval = setInterval(() => {
          const status = websocketService.getConnectionStatus('real-time-data');
          setData(prev => ({
            ...prev,
            isConnected: status?.isConnected || false
          }));
        }, 1000);

        // Store interval for cleanup
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
        intervalRef.current = statusInterval;
      });

      messageHandlerRef.current = handleRealTimeUpdate;
    } catch (error) {
      console.warn('Failed to setup WebSocket:', error);
    }
  }, [enableRealTime, handleRealTimeUpdate]);

  // Setup polling fallback
  const setupPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(fetchData, refreshInterval);
  }, [fetchData, refreshInterval]);

  // Initialize data fetching
  useEffect(() => {
    fetchData();
    
    if (enableRealTime) {
      setupWebSocket();
    } else {
      setupPolling();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      
      // Disconnect from WebSocket
      if (enableRealTime && messageHandlerRef.current) {
        import('../services/websocketService').then(({ websocketService }) => {
          websocketService.disconnect('real-time-data', messageHandlerRef.current!);
        });
      }
    };
  }, [fetchData, setupWebSocket, setupPolling, enableRealTime]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  // Connect/disconnect functions
  const connect = useCallback(() => {
    if (enableRealTime) {
      setupWebSocket();
    }
  }, [enableRealTime, setupWebSocket]);

  const disconnect = useCallback(() => {
    if (messageHandlerRef.current) {
      import('../services/websocketService').then(({ websocketService }) => {
        websocketService.disconnect('real-time-data', messageHandlerRef.current!);
      });
    }
    setData(prev => ({ ...prev, isConnected: false }));
  }, []);

  return {
    ...data,
    refresh,
    connect,
    disconnect,
  };
};