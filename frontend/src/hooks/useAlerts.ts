/**
 * Alerts Hooks with React Query
 * ✅ Automatic caching and real-time updates
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataService } from '../services/dataService';
import { queryKeys, invalidateQueries } from '../lib/react-query';
import { Alert } from '../types';

/**
 * Fetch alerts
 * ✅ Cached for 20 seconds (alerts need frequent updates)
 * ✅ Refetches every 30 seconds
 */
export function useAlerts(limit: number = 50) {
  return useQuery({
    queryKey: queryKeys.alerts.list(limit),
    queryFn: () => dataService.getAlerts(limit),
    staleTime: 20000, // 20 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Fetch critical alerts only
 * ✅ Cached for 10 seconds (critical alerts need immediate updates)
 * ✅ Refetches every 15 seconds
 */
export function useCriticalAlerts() {
  return useQuery({
    queryKey: queryKeys.alerts.critical(),
    queryFn: () => dataService.getCriticalAlerts(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 15000, // Refetch every 15 seconds
  });
}

/**
 * Mutation for acknowledging an alert
 * ✅ Optimistic updates
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => {
      // This would call an API endpoint
      return Promise.resolve({ alertId, acknowledged: true });
    },
    onMutate: async (alertId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.alerts.all });

      // Snapshot previous value
      const previousAlerts = queryClient.getQueryData(queryKeys.alerts.lists());

      // Optimistically update
      queryClient.setQueryData(
        queryKeys.alerts.lists(),
        (old: Alert[]) => old?.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );

      return { previousAlerts };
    },
    onError: (err, alertId, context) => {
      // Rollback on error
      if (context?.previousAlerts) {
        queryClient.setQueryData(queryKeys.alerts.lists(), context.previousAlerts);
      }
    },
    onSuccess: () => {
      // Invalidate alerts
      invalidateQueries.alerts();
    },
  });
}
