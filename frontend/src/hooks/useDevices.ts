/**
 * Device Management Hooks with React Query
 * ✅ Automatic caching and background refetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataService } from '../services/dataService';
import { queryKeys, invalidateQueries } from '../lib/react-query';
import { DeviceStatus } from '../types';

/**
 * Fetch all devices
 * ✅ Cached for 1 minute
 * ✅ Refetches every 2 minutes
 */
export function useDevices() {
  return useQuery({
    queryKey: queryKeys.devices.lists(),
    queryFn: () => dataService.getDevices(),
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Refetch every 2 minutes
  });
}

/**
 * Fetch single device by ID
 * ✅ Cached for 30 seconds
 */
export function useDevice(deviceId: string) {
  return useQuery({
    queryKey: queryKeys.devices.detail(deviceId),
    queryFn: () => dataService.getDeviceById(deviceId),
    staleTime: 30000, // 30 seconds
    enabled: !!deviceId, // Only fetch if deviceId is provided
  });
}

/**
 * Mutation for updating device status
 * ✅ Optimistic updates
 * ✅ Automatic cache invalidation
 */
export function useUpdateDeviceStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, status }: { deviceId: string; status: string }) => {
      // This would call an API endpoint
      return Promise.resolve({ deviceId, status });
    },
    onMutate: async ({ deviceId, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.devices.detail(deviceId) });

      // Snapshot previous value
      const previousDevice = queryClient.getQueryData(queryKeys.devices.detail(deviceId));

      // Optimistically update
      queryClient.setQueryData(
        queryKeys.devices.detail(deviceId),
        (old: any) => old ? { ...old, status } : old
      );

      return { previousDevice };
    },
    onError: (err, { deviceId }, context) => {
      // Rollback on error
      if (context?.previousDevice) {
        queryClient.setQueryData(queryKeys.devices.detail(deviceId), context.previousDevice);
      }
    },
    onSuccess: () => {
      // Invalidate devices list
      invalidateQueries.devices();
    },
  });
}
