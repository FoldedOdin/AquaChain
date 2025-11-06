/**
 * Water Quality Data Hooks
 * ✅ Simple data fetching with React hooks
 */

import { useState, useEffect, useCallback } from 'react';
import { dataService } from '../services/dataService';
import { WaterQualityReading } from '../types';

/**
 * Fetch water quality data for a time range
 */
export function useWaterQualityData(timeRange: string = '24h') {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await dataService.getWaterQualityData(timeRange);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refetch every minute

    return () => {
      clearInterval(interval);
    };
  }, [fetchData]);

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Fetch latest water quality reading
 */
export function useLatestWaterQuality() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await dataService.getLatestWaterQuality();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refetch every 30 seconds

    return () => {
      clearInterval(interval);
    };
  }, [fetchData]);

  return { data, isLoading, error, refetch: fetchData };
}

/**
 * Mutation for submitting manual water quality reading
 */
export function useSubmitWaterQualityReading() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (reading: Partial<WaterQualityReading>) => {
    try {
      setIsLoading(true);
      setError(null);
      // This would call an API endpoint to submit the reading
      await Promise.resolve(reading);
      return reading;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { mutate, isLoading, error };
}
