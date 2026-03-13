/**
 * Device Management Hooks
 * ✅ Simple data fetching with React hooks
 */

import { useState, useEffect, useCallback } from 'react';
import { dataService } from '../services/dataService';
import { DeviceStatus } from '../types';

/**
 * Fetch all devices
 */
export function useDevices() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await dataService.getDevices();
      setData(result);
      setError(null);
    } catch (err: any) {
      console.error('useDevices fetchData error:', err);
      setError(err as Error);
      
      // Stop polling on authentication errors to prevent spam
      if (err?.status === 401 || err?.status === 403) {
        console.warn('🛑 Authentication failed - stopping devices polling');
        if (intervalId) {
          clearInterval(intervalId);
          setIntervalId(null);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [intervalId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 120000); // Refetch every 2 minutes
    setIntervalId(interval);

    return () => {
      clearInterval(interval);
      setIntervalId(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Fetch single device by ID
 */
export function useDevice(deviceId: string) {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!deviceId) return;

    try {
      setIsLoading(true);
      const result = await dataService.getDeviceById(deviceId);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]); // Only refetch when deviceId changes

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Mutation for updating device status
 */
export function useUpdateDeviceStatus() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async ({ deviceId, status }: { deviceId: string; status: string }) => {
    try {
      setIsLoading(true);
      setError(null);
      // This would call an API endpoint
      const result = await Promise.resolve({ deviceId, status });
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { mutate, isLoading, error };
}
