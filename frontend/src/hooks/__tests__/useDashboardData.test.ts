/**
 * useDashboardData Hook Tests
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useDashboardData } from '../useDashboardData';
import * as adminService from '../../services/adminService';
import { technicianService } from '../../services/technicianService';
import { dataService } from '../../services/dataService';

// Mock the services
jest.mock('../../services/adminService');
jest.mock('../../services/technicianService');
jest.mock('../../services/dataService');

describe('useDashboardData Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Admin Role', () => {
    const mockAdminData = {
      healthMetrics: { cpu: 50, memory: 60 },
      deviceFleet: [{ id: '1', name: 'Device 1' }],
      performanceMetrics: [{ timestamp: '2024-01-01', value: 100 }],
      alertAnalytics: { total: 5, critical: 1 }
    };

    beforeEach(() => {
      (adminService.getSystemHealthMetrics as jest.Mock).mockResolvedValue(mockAdminData.healthMetrics);
      (adminService.getDeviceFleetStatus as jest.Mock).mockResolvedValue(mockAdminData.deviceFleet);
      (adminService.getPerformanceMetrics as jest.Mock).mockResolvedValue(mockAdminData.performanceMetrics);
      (adminService.getAlertAnalytics as jest.Mock).mockResolvedValue(mockAdminData.alertAnalytics);
    });

    it('fetches admin dashboard data on mount', async () => {
      const { result } = renderHook(() => useDashboardData('admin'));

      expect(result.current.loading).toBe(true);
      expect(result.current.data).toBeNull();

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual(mockAdminData);
      expect(result.current.error).toBeNull();
    });

    it('calls all admin service methods', async () => {
      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(adminService.getSystemHealthMetrics).toHaveBeenCalledTimes(1);
      expect(adminService.getDeviceFleetStatus).toHaveBeenCalledTimes(1);
      expect(adminService.getPerformanceMetrics).toHaveBeenCalledWith('24h');
      expect(adminService.getAlertAnalytics).toHaveBeenCalledWith(7);
    });

    it('handles admin data fetch errors', async () => {
      const error = new Error('Failed to fetch admin data');
      (adminService.getSystemHealthMetrics as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toEqual(error);
      expect(result.current.data).toBeNull();
    });
  });

  describe('Technician Role', () => {
    const mockTechnicianData = {
      tasks: [
        { id: '1', title: 'Task 1', status: 'pending' },
        { id: '2', title: 'Task 2', status: 'in_progress' }
      ],
      selectedTask: { id: '1', title: 'Task 1', status: 'pending' }
    };

    beforeEach(() => {
      (technicianService.getAssignedTasks as jest.Mock).mockResolvedValue(mockTechnicianData.tasks);
    });

    it('fetches technician dashboard data on mount', async () => {
      const { result } = renderHook(() => useDashboardData('technician'));

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual(mockTechnicianData);
      expect(result.current.error).toBeNull();
    });

    it('sets selectedTask to first task when tasks exist', async () => {
      const { result } = renderHook(() => useDashboardData('technician'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const data = result.current.data as any;
      expect(data.selectedTask).toEqual(mockTechnicianData.tasks[0]);
    });

    it('sets selectedTask to null when no tasks', async () => {
      (technicianService.getAssignedTasks as jest.Mock).mockResolvedValue([]);

      const { result } = renderHook(() => useDashboardData('technician'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const data = result.current.data as any;
      expect(data.selectedTask).toBeNull();
    });

    it('handles technician data fetch errors', async () => {
      const error = new Error('Failed to fetch tasks');
      (technicianService.getAssignedTasks as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useDashboardData('technician'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('Consumer Role', () => {
    const mockConsumerData = {
      currentReading: { ph: 7.0, temperature: 25 },
      alerts: [{ id: '1', message: 'High pH' }],
      devices: [{ id: '1', name: 'Device 1' }],
      stats: { totalReadings: 100, avgPh: 7.2 }
    };

    beforeEach(() => {
      (dataService.getLatestWaterQuality as jest.Mock).mockResolvedValue(mockConsumerData.currentReading);
      (dataService.getAlerts as jest.Mock).mockResolvedValue(mockConsumerData.alerts);
      (dataService.getDevices as jest.Mock).mockResolvedValue(mockConsumerData.devices);
      (dataService.getDashboardStats as jest.Mock).mockResolvedValue(mockConsumerData.stats);
    });

    it('fetches consumer dashboard data on mount', async () => {
      const { result } = renderHook(() => useDashboardData('consumer'));

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual(mockConsumerData);
      expect(result.current.error).toBeNull();
    });

    it('calls all consumer service methods', async () => {
      const { result } = renderHook(() => useDashboardData('consumer'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(dataService.getLatestWaterQuality).toHaveBeenCalledTimes(1);
      expect(dataService.getAlerts).toHaveBeenCalledWith(20);
      expect(dataService.getDevices).toHaveBeenCalledTimes(1);
      expect(dataService.getDashboardStats).toHaveBeenCalledTimes(1);
    });

    it('handles consumer data fetch errors', async () => {
      const error = new Error('Failed to fetch consumer data');
      (dataService.getLatestWaterQuality as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useDashboardData('consumer'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('Refetch Functionality', () => {
    beforeEach(() => {
      (adminService.getSystemHealthMetrics as jest.Mock).mockResolvedValue({});
      (adminService.getDeviceFleetStatus as jest.Mock).mockResolvedValue([]);
      (adminService.getPerformanceMetrics as jest.Mock).mockResolvedValue([]);
      (adminService.getAlertAnalytics as jest.Mock).mockResolvedValue({});
    });

    it('provides refetch function', async () => {
      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.refetch).toBeDefined();
      expect(typeof result.current.refetch).toBe('function');
    });

    it('refetches data when refetch is called', async () => {
      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(adminService.getSystemHealthMetrics).toHaveBeenCalledTimes(1);

      await result.current.refetch();

      expect(adminService.getSystemHealthMetrics).toHaveBeenCalledTimes(2);
    });

    it('sets loading state during refetch', async () => {
      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const refetchPromise = result.current.refetch();
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await refetchPromise;
    });
  });

  describe('Error Handling', () => {
    it('handles unknown user role', async () => {
      const { result } = renderHook(() => useDashboardData('unknown' as any));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toContain('Unknown user role');
    });

    it('converts non-Error objects to Error', async () => {
      (adminService.getSystemHealthMetrics as jest.Mock).mockRejectedValue('String error');

      const { result } = renderHook(() => useDashboardData('admin'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBeInstanceOf(Error);
      expect(result.current.error?.message).toBe('Failed to load dashboard data');
    });
  });

  describe('Hook Dependencies', () => {
    beforeEach(() => {
      (adminService.getSystemHealthMetrics as jest.Mock).mockResolvedValue({});
      (adminService.getDeviceFleetStatus as jest.Mock).mockResolvedValue([]);
      (adminService.getPerformanceMetrics as jest.Mock).mockResolvedValue([]);
      (adminService.getAlertAnalytics as jest.Mock).mockResolvedValue({});
    });

    it('refetches data when userRole changes', async () => {
      const { result, rerender } = renderHook(
        ({ role }) => useDashboardData(role),
        { initialProps: { role: 'admin' as const } }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(adminService.getSystemHealthMetrics).toHaveBeenCalledTimes(1);

      (technicianService.getAssignedTasks as jest.Mock).mockResolvedValue([]);
      
      rerender({ role: 'technician' as const });

      await waitFor(() => {
        expect(technicianService.getAssignedTasks).toHaveBeenCalled();
      });
    });
  });
});
