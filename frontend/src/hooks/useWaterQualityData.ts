/**
 * Water Quality Data Hooks with React Query
 * ✅ Automatic caching, deduplication, and background refetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataService } from '../services/dataService';
import { queryKeys, invalidateQueries } from '../lib/react-query';
import { WaterQualityReading } from '../types';

/**
 * Fetch water quality data for a time range
 * ✅ Cached for 30 seconds
 * ✅ Refetches every minute in background
 * ✅ Automatic retry on failure
 */
export function useWaterQualityData(timeRange: string = '24h') {
  return useQuery({
    queryKey: queryKeys.waterQuality.list(timeRange),
    queryFn: () => dataService.getWaterQualityData(timeRange),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Fetch latest water quality reading
 * ✅ Cached for 10 seconds (more frequent updates)
 * ✅ Refetches every 30 seconds
 */
export function useLatestWaterQuality() {
  return useQuery({
    queryKey: queryKeys.waterQuality.latest(),
    queryFn: () => dataService.getLatestWaterQuality(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
  });
}

/**
 * Mutation for submitting manual water quality reading
 * ✅ Optimistic updates
 * ✅ Automatic cache invalidation on success
 */
export function useSubmitWaterQualityReading() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reading: Partial<WaterQualityReading>) => {
      // This would call an API endpoint to submit the reading
      return Promise.resolve(reading);
    },
    onMutate: async (newReading) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.waterQuality.all });

      // Snapshot previous value
      const previousReadings = queryClient.getQueryData(queryKeys.waterQuality.latest());

      // Optimistically update
      queryClient.setQueryData(queryKeys.waterQuality.latest(), newReading);

      // Return context with snapshot
      return { previousReadings };
    },
    onError: (err, newReading, context) => {
      // Rollback on error
      if (context?.previousReadings) {
        queryClient.setQueryData(queryKeys.waterQuality.latest(), context.previousReadings);
      }
    },
    onSuccess: () => {
      // Invalidate and refetch
      invalidateQueries.waterQuality();
    },
  });
}
