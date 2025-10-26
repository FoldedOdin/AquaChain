/**
 * React Query Configuration
 * ✅ Centralized data fetching with caching, retries, and deduplication
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

/**
 * Create Query Client with optimized defaults
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // ✅ Cache data for 5 minutes
      staleTime: 5 * 60 * 1000,
      
      // ✅ Keep unused data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      
      // ✅ Retry failed requests 3 times with exponential backoff
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // ✅ Refetch on window focus (user returns to tab)
      refetchOnWindowFocus: true,
      
      // ✅ Refetch on reconnect (network restored)
      refetchOnReconnect: true,
      
      // ✅ Don't refetch on mount if data is fresh
      refetchOnMount: false,
      
      // ✅ Network mode - fail fast if offline
      networkMode: 'online',
    },
    mutations: {
      // ✅ Retry mutations once
      retry: 1,
      retryDelay: 1000,
      
      // ✅ Network mode for mutations
      networkMode: 'online',
    },
  },
});

/**
 * Query Keys Factory
 * ✅ Centralized query key management for cache invalidation
 */
export const queryKeys = {
  // Water Quality
  waterQuality: {
    all: ['waterQuality'] as const,
    lists: () => [...queryKeys.waterQuality.all, 'list'] as const,
    list: (timeRange: string) => [...queryKeys.waterQuality.lists(), timeRange] as const,
    details: () => [...queryKeys.waterQuality.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.waterQuality.details(), id] as const,
    latest: () => [...queryKeys.waterQuality.all, 'latest'] as const,
  },
  
  // Devices
  devices: {
    all: ['devices'] as const,
    lists: () => [...queryKeys.devices.all, 'list'] as const,
    list: (filters?: any) => [...queryKeys.devices.lists(), filters] as const,
    details: () => [...queryKeys.devices.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.devices.details(), id] as const,
  },
  
  // Alerts
  alerts: {
    all: ['alerts'] as const,
    lists: () => [...queryKeys.alerts.all, 'list'] as const,
    list: (limit?: number) => [...queryKeys.alerts.lists(), limit] as const,
    critical: () => [...queryKeys.alerts.all, 'critical'] as const,
  },
  
  // Service Requests
  serviceRequests: {
    all: ['serviceRequests'] as const,
    lists: () => [...queryKeys.serviceRequests.all, 'list'] as const,
    list: (filters?: any) => [...queryKeys.serviceRequests.lists(), filters] as const,
    details: () => [...queryKeys.serviceRequests.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.serviceRequests.details(), id] as const,
  },
  
  // Dashboard
  dashboard: {
    all: ['dashboard'] as const,
    stats: (role: string) => [...queryKeys.dashboard.all, 'stats', role] as const,
  },
  
  // Admin
  admin: {
    all: ['admin'] as const,
    health: () => [...queryKeys.admin.all, 'health'] as const,
    fleet: () => [...queryKeys.admin.all, 'fleet'] as const,
    performance: (timeRange: string) => [...queryKeys.admin.all, 'performance', timeRange] as const,
    analytics: (days: number) => [...queryKeys.admin.all, 'analytics', days] as const,
  },
  
  // Technician
  technician: {
    all: ['technician'] as const,
    tasks: () => [...queryKeys.technician.all, 'tasks'] as const,
    task: (id: string) => [...queryKeys.technician.all, 'task', id] as const,
  },
};

/**
 * Cache Invalidation Helpers
 */
export const invalidateQueries = {
  // Invalidate all water quality data
  waterQuality: () => queryClient.invalidateQueries({ queryKey: queryKeys.waterQuality.all }),
  
  // Invalidate specific water quality data
  waterQualityByRange: (timeRange: string) => 
    queryClient.invalidateQueries({ queryKey: queryKeys.waterQuality.list(timeRange) }),
  
  // Invalidate all devices
  devices: () => queryClient.invalidateQueries({ queryKey: queryKeys.devices.all }),
  
  // Invalidate specific device
  device: (id: string) => 
    queryClient.invalidateQueries({ queryKey: queryKeys.devices.detail(id) }),
  
  // Invalidate all alerts
  alerts: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts.all }),
  
  // Invalidate dashboard data
  dashboard: (role: string) => 
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats(role) }),
  
  // Invalidate everything (use sparingly)
  all: () => queryClient.invalidateQueries(),
};

/**
 * Prefetch Helpers
 * ✅ Prefetch data before user navigates to improve perceived performance
 */
export const prefetchQueries = {
  waterQuality: async (timeRange: string, fetcher: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.waterQuality.list(timeRange),
      queryFn: fetcher,
    });
  },
  
  devices: async (fetcher: () => Promise<any>) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.devices.lists(),
      queryFn: fetcher,
    });
  },
};

/**
 * Optimistic Update Helpers
 */
export const optimisticUpdates = {
  // Update device status optimistically
  updateDeviceStatus: (deviceId: string, newStatus: string) => {
    queryClient.setQueryData(
      queryKeys.devices.detail(deviceId),
      (old: any) => old ? { ...old, status: newStatus } : old
    );
  },
  
  // Add new alert optimistically
  addAlert: (newAlert: any) => {
    queryClient.setQueryData(
      queryKeys.alerts.lists(),
      (old: any[]) => old ? [newAlert, ...old] : [newAlert]
    );
  },
};

export { QueryClientProvider, ReactQueryDevtools };
