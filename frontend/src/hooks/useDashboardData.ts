/**
 * Dashboard Data Hook
 * ✅ Simple data fetching with React hooks
 * ✅ Optimized for role-based dashboards
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
  recentActivities?: any[];
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
 * 
 * @param userRole - The role of the current user (admin, technician, consumer)
 * @returns Dashboard data, loading state, error state
 */
export function useDashboardData(userRole: UserRole) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      let result: DashboardData;

      switch (userRole) {
        case 'admin':
          const [health, fleet, performance, alerts] = await Promise.all([
            getSystemHealthMetrics(),
            getDeviceFleetStatus(),
            getPerformanceMetrics('24h'),
            getAlertAnalytics(7)
          ]);
          result = {
            healthMetrics: health,
            deviceFleet: fleet,
            performanceMetrics: performance,
            alertAnalytics: alerts
          };
          break;

        case 'technician':
          // Fetch assigned orders from the API
          const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
          const technicianData = await fetch('http://localhost:3002/api/technician/orders', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }).then(res => res.json()).catch(() => ({ orders: [] }));
          
          result = {
            tasks: technicianData.orders || [],
            recentActivities: [],
            selectedTask: technicianData.orders?.length > 0 ? technicianData.orders[0] : null
          };
          break;

        case 'consumer':
          const [reading, consumerAlerts, devices, stats] = await Promise.all([
            dataService.getLatestWaterQuality(),
            dataService.getAlerts(20),
            dataService.getDevices(),
            dataService.getDashboardStats()
          ]);
          result = {
            currentReading: reading,
            alerts: consumerAlerts,
            devices,
            stats
          };
          break;

        default:
          throw new Error(`Unknown user role: ${userRole}`);
      }

      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [userRole]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000); // Refetch every 5 minutes (300 seconds)

    return () => {
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userRole]); // Only refetch when userRole changes

  return { data, isLoading, error, refetch: fetchData };
}
