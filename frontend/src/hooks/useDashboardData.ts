/**
 * useDashboardData Hook
 * 
 * Custom hook for fetching dashboard data from MockDataService.
 * Automatically refreshes data based on DashboardContext refresh timestamp.
 * 
 * Features:
 * - Automatic data fetching on mount and refresh
 * - Loading state management
 * - Error handling
 * - Type-safe data access
 * 
 * @module useDashboardData
 */

import { useState, useEffect } from "react";
import { useDashboard } from "../contexts/DashboardContext";
import { MockDataService } from "../services/mockDataService";
import {
  KPIMetrics,
  SystemHealthData,
  MLInsightData,
  TimeRange,
} from "../types/dashboard";
import { Device } from "../types/device";
import { Alert } from "../types/alert";
import { User } from "../types/user";
import { LogEntry } from "../types/log";

/**
 * Hook for fetching KPI metrics
 * 
 * @returns Object with metrics data, loading state, and error
 */
export function useKPIMetrics() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<KPIMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const metrics = MockDataService.getKPIMetrics();
      setData(metrics);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch KPI metrics"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching system health data
 * 
 * @param timeRange - Time range for data generation
 * @returns Object with health data, loading state, and error
 */
export function useSystemHealthData(timeRange: TimeRange) {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<SystemHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const healthData = MockDataService.getSystemHealthData(timeRange);
      setData(healthData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch system health data"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp, timeRange]);

  return { data, loading, error };
}

/**
 * Hook for fetching devices
 * 
 * @returns Object with devices data, loading state, and error
 */
export function useDevices() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const devices = MockDataService.getDevices();
      setData(devices);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch devices"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching alerts
 * 
 * @returns Object with alerts data, loading state, and error
 */
export function useAlerts() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const alerts = MockDataService.getAlerts();
      setData(alerts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch alerts"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching ML insights
 * 
 * @returns Object with insights data, loading state, and error
 */
export function useMLInsights() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<MLInsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const insights = MockDataService.getMLInsights();
      setData(insights);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch ML insights"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching users
 * 
 * @returns Object with users data, loading state, and error
 */
export function useUsers() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const users = MockDataService.getUsers();
      setData(users);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch users"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching logs
 * 
 * @returns Object with logs data, loading state, and error
 */
export function useLogs() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const logs = MockDataService.getLogs();
      setData(logs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch logs"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Hook for fetching devices for map visualization
 * 
 * @returns Object with device marker data, loading state, and error
 */
export function useDevicesForMap() {
  const { lastRefreshTimestamp } = useDashboard();
  const [data, setData] = useState<ReturnType<typeof MockDataService.getDevicesForMap>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      setLoading(true);
      const devices = MockDataService.getDevicesForMap();
      setData(devices);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch devices for map"));
    } finally {
      setLoading(false);
    }
  }, [lastRefreshTimestamp]);

  return { data, loading, error };
}

/**
 * Legacy hook for backward compatibility
 * Combines all dashboard data fetching hooks
 * 
 * @deprecated Use individual hooks (useKPIMetrics, useDevices, etc.) instead
 * @returns Object with all dashboard data
 */
export function useDashboardData() {
  const kpiMetrics = useKPIMetrics();
  const devices = useDevices();
  const alerts = useAlerts();
  const users = useUsers();
  const logs = useLogs();
  const mlInsights = useMLInsights();

  return {
    kpiMetrics: kpiMetrics.data,
    devices: devices.data,
    alerts: alerts.data,
    users: users.data,
    logs: logs.data,
    mlInsights: mlInsights.data,
    loading: kpiMetrics.loading || devices.loading || alerts.loading || users.loading || logs.loading || mlInsights.loading,
    error: kpiMetrics.error || devices.error || alerts.error || users.error || logs.error || mlInsights.error,
  };
}
