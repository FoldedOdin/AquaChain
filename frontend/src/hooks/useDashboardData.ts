/**
 * Dashboard Data Hook
 * Manages data fetching for role-based dashboards
 */

import { useState, useEffect, useCallback } from 'react';
import { getSystemHealthMetrics, getDeviceFleetStatus, getPerformanceMetrics, getAlertAnalytics } from '../services/adminService';
import { technicianService } from '../services/technicianService';
import { dataService } from '../services/dataService';

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

interface UseDashboardDataReturn {
  data: DashboardData | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for fetching dashboard data based on user role
 * @param userRole - The role of the current user (admin, technician, consumer)
 * @returns Dashboard data, loading state, error state, and refetch function
 */
export function useDashboardData(userRole: UserRole): UseDashboardDataReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let dashboardData: DashboardData;

      switch (userRole) {
        case 'admin':
          const [health, fleet, performance, alerts] = await Promise.all([
            getSystemHealthMetrics(),
            getDeviceFleetStatus(),
            getPerformanceMetrics('24h'),
            getAlertAnalytics(7)
          ]);
          dashboardData = {
            healthMetrics: health,
            deviceFleet: fleet,
            performanceMetrics: performance,
            alertAnalytics: alerts
          };
          break;

        case 'technician':
          const tasks = await technicianService.getAssignedTasks();
          dashboardData = {
            tasks,
            selectedTask: tasks.length > 0 ? tasks[0] : null
          };
          break;

        case 'consumer':
          const [reading, consumerAlerts, devices, stats] = await Promise.all([
            dataService.getLatestWaterQuality(),
            dataService.getAlerts(20),
            dataService.getDevices(),
            dataService.getDashboardStats()
          ]);
          dashboardData = {
            currentReading: reading,
            alerts: consumerAlerts,
            devices,
            stats
          };
          break;

        default:
          throw new Error(`Unknown user role: ${userRole}`);
      }

      setData(dashboardData);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError(err instanceof Error ? err : new Error('Failed to load dashboard data'));
    } finally {
      setLoading(false);
    }
  }, [userRole]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
