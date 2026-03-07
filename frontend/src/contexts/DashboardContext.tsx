/**
 * Dashboard Context
 * 
 * Provides global state management for the Admin Global Monitoring Dashboard.
 * Manages theme, refresh settings, user role, and notification history.
 * 
 * Features:
 * - Configuration persistence in localStorage
 * - Auto-refresh timer with configurable interval (30/60/120 seconds)
 * - Notification history management (last 50 notifications)
 * - Theme management (light/dark mode)
 * 
 * @module DashboardContext
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import {
  DashboardConfig,
  DashboardContextValue,
  UserRole,
  Notification,
} from "../types/dashboard";

/**
 * Default dashboard configuration
 */
const DEFAULT_CONFIG: DashboardConfig = {
  refreshInterval: 30, // 30 seconds
  theme: "light",
  visibleComponents: [
    "globalKPIBar",
    "systemHealthDashboard",
    "alertManagementPanel",
    "deviceFleetTable",
    "mlInsightPanel",
    "quickActionsPanel",
    "mapVisualization",
    "userManagementTable",
    "systemLogsViewer",
  ],
  filterPresets: [],
};

/**
 * Dashboard Context
 */
const DashboardContext = createContext<DashboardContextValue | null>(null);

/**
 * Dashboard Provider Props
 */
interface DashboardProviderProps {
  userRole?: UserRole;
  userId?: string;
  children: ReactNode;
}

/**
 * Dashboard Provider Component
 * 
 * Provides dashboard state and configuration to all child components.
 * Handles auto-refresh timer, localStorage persistence, and notification management.
 */
export const DashboardProvider: React.FC<DashboardProviderProps> = ({
  userRole = "Admin" as UserRole,
  userId = "default-user",
  children,
}) => {
  // Load config from localStorage
  const [config, setConfig] = useState<DashboardConfig>(() => {
    try {
      const saved = localStorage.getItem("dashboardConfig");
      if (saved) {
        const parsed = JSON.parse(saved);
        // Validate parsed config has required fields
        if (
          typeof parsed.refreshInterval === "number" &&
          typeof parsed.theme === "string" &&
          Array.isArray(parsed.visibleComponents) &&
          Array.isArray(parsed.filterPresets)
        ) {
          return parsed;
        }
      }
    } catch (error) {
      console.error("Failed to load dashboard config from localStorage:", error);
    }
    return DEFAULT_CONFIG;
  });

  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [lastRefreshTimestamp, setLastRefreshTimestamp] = useState(new Date());
  const [notificationHistory, setNotificationHistory] = useState<Notification[]>([]);

  /**
   * Update dashboard configuration
   */
  const updateConfig = useCallback((updates: Partial<DashboardConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = useCallback(() => {
    setAutoRefreshEnabled((prev) => !prev);
  }, []);

  /**
   * Trigger manual refresh
   */
  const triggerManualRefresh = useCallback(() => {
    setLastRefreshTimestamp(new Date());
  }, []);

  /**
   * Add notification to history
   */
  const addNotification = useCallback(
    (notification: Omit<Notification, "id" | "timestamp" | "read">) => {
      const newNotification: Notification = {
        id: `NOTIF-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        read: false,
        ...notification,
      };

      setNotificationHistory((prev) => {
        // Keep only last 50 notifications
        const updated = [newNotification, ...prev].slice(0, 50);
        return updated;
      });
    },
    []
  );

  /**
   * Persist config changes to localStorage
   */
  useEffect(() => {
    try {
      localStorage.setItem("dashboardConfig", JSON.stringify(config));
    } catch (error) {
      console.error("Failed to save dashboard config to localStorage:", error);
    }
  }, [config]);

  /**
   * Auto-refresh timer
   */
  useEffect(() => {
    if (!autoRefreshEnabled) return;

    const interval = setInterval(() => {
      setLastRefreshTimestamp(new Date());
    }, config.refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, config.refreshInterval]);

  /**
   * Context value
   */
  const value: DashboardContextValue = {
    config,
    updateConfig,
    autoRefreshEnabled,
    toggleAutoRefresh,
    lastRefreshTimestamp,
    triggerManualRefresh,
    userRole,
    userId,
    notificationHistory,
    addNotification,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

/**
 * Custom hook to use Dashboard Context
 * 
 * @throws Error if used outside DashboardProvider
 * @returns DashboardContextValue
 */
export const useDashboard = (): DashboardContextValue => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within DashboardProvider");
  }
  return context;
};
