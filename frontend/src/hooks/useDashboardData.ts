/**
 * Dashboard Data Hook with React Query
 * ✅ Automatic caching, deduplication, and background refetching
 * ✅ Optimized for role-based dashboards
 */

import { useQuery } from '@tanstack/react-query';
import { getSystemHealthMetrics, getDeviceFleetStatus, getPerformanceMetrics, getAlertAnalytics } from '../services/adminService';
import { technicianService } from '../services/technicianService';
import { dataService } from '../services/dataService';
import { queryKeys } from '../lib/react-query';

export type UserRole = 'admin' | 'technician' | 'consumer';

interface AdminDashboardData {
  healthMetrics: any;
  deviceFleet: any[];
  performanceMetrics: any[];
  alertAnalytics: any;
}

interface TechnicianDashboardData {
  tasks: any[];
  selectedTask: any | null;
}

interface ConsumerDashboardData {
  currentReading: any;
  alerts: any[];
  devices: any[];
  stats: any;
}

type DashboardData = AdminDashboardData | TechnicianDashboardData | ConsumerDashboardData;

/**
 * Custom hook for fetching dashboard data based on user role
 * ✅ Uses React Query for automatic caching and refetching
 * ✅ Deduplicates requests across components
 * ✅ Automatic retry on failure
 * 
 * @param userRole - The role of the current user (admin, technician, consumer)
 * @returns Dashboard data, loading state, error state, and refetch function
 */
export function useDashboardData(userRole: UserRole) {
  return useQuery({
    queryKey: queryKeys.dashboard.stats(userRole),
    queryFn: async (): Promise<DashboardData> => {
      switch (userRole) {
        case 'admin':
          const [health, fleet, performance, alerts] = await Promise.all([
            getSystemHealthMetrics(),
            getDeviceFleetStatus(),
            getPerformanceMetrics('24h'),
            getAlertAnalytics(7)
          ]);
          return {
            healthMetrics: health,
            deviceFleet: fleet,
            performanceMetrics: performance,
            alertAnalytics: alerts
          };

        case 'technician':
          const tasks = await technicianService.getAssignedTasks();
          return {
            tasks,
            selectedTask: tasks.length > 0 ? tasks[0] : null
          };

        case 'consumer':
          const [reading, consumerAlerts, devices, stats] = await Promise.all([
            dataService.getLatestWaterQuality(),
            dataService.getAlerts(20),
            dataService.getDevices(),
            dataService.getDashboardStats()
          ]);
          return {
            currentReading: reading,
            alerts: consumerAlerts,
            devices,
            stats
          };

        default:
          throw new Error(`Unknown user role: ${userRole}`);
      }
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
