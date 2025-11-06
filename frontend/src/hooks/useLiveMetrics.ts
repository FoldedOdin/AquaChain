/**
 * Custom Hook for Live Metrics
 * Fetches and manages real-time system metrics
 */

import { useState, useEffect, useCallback } from 'react';
import { metricsService, LiveMetrics } from '../services/metricsService';
import { MetricConfig, METRICS_UPDATE_INTERVAL } from '../config/landingPageMetrics';

interface UseLiveMetricsOptions {
  enabled?: boolean; // Enable/disable live updates
  updateInterval?: number; // Override default update interval
  source?: 'api' | 'cloudwatch' | 'monitoring'; // Data source
}

interface UseLiveMetricsReturn {
  metrics: MetricConfig[] | null;
  rawMetrics: LiveMetrics | null;
  isLoading: boolean;
  error: Error | null;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage live metrics
 * 
 * @param options Configuration options
 * @returns Metrics data and control functions
 * 
 * @example
 * ```tsx
 * const { metrics, isLoading, error, refetch } = useLiveMetrics({
 *   enabled: true,
 *   updateInterval: 60000 // Update every minute
 * });
 * ```
 */
export function useLiveMetrics(
  options: UseLiveMetricsOptions = {}
): UseLiveMetricsReturn {
  const {
    enabled = METRICS_UPDATE_INTERVAL > 0,
    updateInterval = METRICS_UPDATE_INTERVAL,
    source = 'api'
  } = options;

  const [metrics, setMetrics] = useState<MetricConfig[] | null>(null);
  const [rawMetrics, setRawMetrics] = useState<LiveMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  /**
   * Fetch metrics from the selected source
   */
  const fetchMetrics = useCallback(async () => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      let data: LiveMetrics;

      // Fetch from selected source
      switch (source) {
        case 'cloudwatch':
          data = await metricsService.fetchFromCloudWatch();
          break;
        case 'monitoring':
          data = await metricsService.fetchFromMonitoring();
          break;
        case 'api':
        default:
          data = await metricsService.fetchMetrics();
          break;
      }

      // Format metrics for display
      const formattedMetrics = metricsService.formatMetrics(data);

      setRawMetrics(data);
      setMetrics(formattedMetrics);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err as Error);
      console.error('Failed to fetch metrics:', err);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, source]);

  /**
   * Initial fetch and setup interval
   */
  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Initial fetch
    fetchMetrics();

    // Setup interval for updates
    if (updateInterval > 0) {
      const interval = setInterval(fetchMetrics, updateInterval);

      return () => {
        clearInterval(interval);
      };
    }
  }, [enabled, updateInterval, fetchMetrics]);

  /**
   * Manual refetch function
   */
  const refetch = useCallback(async () => {
    await fetchMetrics();
  }, [fetchMetrics]);

  return {
    metrics,
    rawMetrics,
    isLoading,
    error,
    lastUpdated,
    refetch
  };
}

export default useLiveMetrics;
