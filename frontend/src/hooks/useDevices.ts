/**
 * Device Management Hooks
 * ✅ Simple data fetching with React hooks
 */

import { useState, useEffect, useCallback } from 'react';
import unifiedDataService from '../services/dataServiceSelector';
import { DeviceStatus } from '../types';

/**
 * Fetch all devices
 */
export function useDevices() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await unifiedDataService.getDevices();
      setData(result);
      setError(null);
    } catch (err: any) {
      console.error('useDevices fetchData error:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, []); // Fetch once on mount — real-time updates come via WebSocket

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
      const result = await unifiedDataService.getDeviceById(deviceId);
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
    // eslint-disable-next-line
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
