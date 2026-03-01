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
          // Fetch assigned service requests from the API
          const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
          const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || '';
          
          // Try to fetch from API, fall back to mock data if Lambda is broken
          let technicianData;
          try {
            const response = await fetch(`${apiEndpoint}/api/v1/service-requests?status=assigned,in_progress`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (response.ok) {
              technicianData = await response.json();
            } else {
              console.warn('Service requests API returned error, using mock data');
              technicianData = { serviceRequests: [] };
            }
          } catch (err) {
            console.error('Failed to fetch technician service requests:', err);
            // Use mock data for now until Lambda is fixed
            technicianData = {
              serviceRequests: [
                {
                  requestId: 'SR-001',
                  deviceId: 'DEV-12345',
                  status: 'assigned',
                  priority: 'high',
                  description: 'Water quality sensor malfunction',
                  location: 'Mumbai, Maharashtra',
                  createdAt: new Date().toISOString(),
                  assignedAt: new Date().toISOString()
                }
              ]
            };
          }
          
          result = {
            tasks: technicianData.serviceRequests || technicianData.data || [],
            recentActivities: [],
            selectedTask: (technicianData.serviceRequests || technicianData.data || []).length > 0 
              ? (technicianData.serviceRequests || technicianData.data)[0] 
              : null
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
    // Polling disabled - use manual refresh button instead
    // This prevents excessive 401 errors when token expires
    // Uncomment below to re-enable polling:
    // const interval = setInterval(fetchData, 300000); // 5 minutes
    // return () => clearInterval(interval);
  }, [userRole]); // Only refetch when userRole changes

  return { data, isLoading, error, refetch: fetchData };
}
