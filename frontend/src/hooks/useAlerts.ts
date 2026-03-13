/**
 * Alerts Hooks
 * ✅ Simple data fetching with React hooks
 */

import { useState, useEffect, useCallback } from 'react';
import { dataService } from '../services/dataService';
import { Alert } from '../types';

/**
 * Fetch alerts
 */
export function useAlerts(limit: number = 50) {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await dataService.getAlerts(limit);
      setData(result);
      setError(null);
    } catch (err: any) {
      console.error('useAlerts fetchData error:', err);
      setError(err as Error);
      
      // Stop polling on authentication errors to prevent spam
      if (err?.status === 401 || err?.status === 403) {
        console.warn('🛑 Authentication failed - stopping alerts polling');
        if (intervalId) {
          clearInterval(intervalId);
          setIntervalId(null);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [limit, intervalId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refetch every 30 seconds
    setIntervalId(interval);

    return () => {
      clearInterval(interval);
      setIntervalId(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit]); // Only refetch when limit changes

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Fetch critical alerts only
 */
export function useCriticalAlerts() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await dataService.getCriticalAlerts();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err as Error);
      
      // Stop polling on authentication errors to prevent spam
      if (err?.status === 401 || err?.status === 403) {
        console.warn('🛑 Authentication failed - stopping critical alerts polling');
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
    const interval = setInterval(fetchData, 15000); // Refetch every 15 seconds
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
 * Mutation for acknowledging an alert
 */
export function useAcknowledgeAlert() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (alertId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      // This would call an API endpoint
      const result = await Promise.resolve({ alertId, acknowledged: true });
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
