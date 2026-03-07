/**
 * useAutoRefresh Hook
 * 
 * Custom hook for managing auto-refresh logic and countdown display.
 * Provides countdown timer and next refresh timestamp calculation.
 * 
 * Features:
 * - Countdown timer to next refresh
 * - Next refresh timestamp calculation
 * - Automatic updates every second
 * - Integration with DashboardContext
 * 
 * @module useAutoRefresh
 */

import { useState, useEffect } from "react";
import { useDashboard } from "../contexts/DashboardContext";

/**
 * Auto-refresh state
 */
interface AutoRefreshState {
  /** Seconds remaining until next refresh */
  secondsUntilRefresh: number;
  /** Timestamp of next refresh */
  nextRefreshTime: Date;
  /** Whether auto-refresh is currently enabled */
  isEnabled: boolean;
  /** Current refresh interval in seconds */
  refreshInterval: number;
}

/**
 * Hook for managing auto-refresh logic
 * 
 * Provides countdown timer and next refresh timestamp.
 * Updates every second to show accurate countdown.
 * 
 * @returns Auto-refresh state with countdown and next refresh time
 * 
 * @example
 * ```tsx
 * const { secondsUntilRefresh, nextRefreshTime, isEnabled } = useAutoRefresh();
 * 
 * return (
 *   <div>
 *     {isEnabled && (
 *       <span>Next refresh in {secondsUntilRefresh}s</span>
 *     )}
 *   </div>
 * );
 * ```
 */
export function useAutoRefresh(): AutoRefreshState {
  const { 
    autoRefreshEnabled, 
    lastRefreshTimestamp, 
    config 
  } = useDashboard();

  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(0);
  const [nextRefreshTime, setNextRefreshTime] = useState(new Date());

  useEffect(() => {
    // Calculate next refresh time
    const nextRefresh = new Date(
      lastRefreshTimestamp.getTime() + config.refreshInterval * 1000
    );
    setNextRefreshTime(nextRefresh);

    // Update countdown every second
    const updateCountdown = () => {
      const now = Date.now();
      const nextRefreshMs = nextRefresh.getTime();
      const remainingMs = Math.max(0, nextRefreshMs - now);
      const remainingSeconds = Math.ceil(remainingMs / 1000);
      setSecondsUntilRefresh(remainingSeconds);
    };

    // Initial update
    updateCountdown();

    // Set up interval for countdown updates
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [lastRefreshTimestamp, config.refreshInterval]);

  return {
    secondsUntilRefresh,
    nextRefreshTime,
    isEnabled: autoRefreshEnabled,
    refreshInterval: config.refreshInterval,
  };
}

/**
 * Format seconds into human-readable time string
 * 
 * @param seconds - Number of seconds
 * @returns Formatted time string (e.g., "2m 30s", "45s")
 * 
 * @example
 * ```tsx
 * formatRefreshTime(150) // "2m 30s"
 * formatRefreshTime(45)  // "45s"
 * ```
 */
export function formatRefreshTime(seconds: number): string {
  if (seconds >= 60) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }
  return `${seconds}s`;
}

/**
 * Hook for managing component-specific auto-refresh
 * 
 * Allows individual components to have their own refresh logic
 * while still respecting the global auto-refresh setting.
 * 
 * @param callback - Function to call on refresh
 * @param enabled - Whether this component's refresh is enabled (default: true)
 * 
 * @example
 * ```tsx
 * useComponentAutoRefresh(() => {
 *   // Fetch component-specific data
 *   fetchData();
 * });
 * ```
 */
export function useComponentAutoRefresh(
  callback: () => void,
  enabled: boolean = true
): void {
  const { lastRefreshTimestamp, autoRefreshEnabled } = useDashboard();

  useEffect(() => {
    if (autoRefreshEnabled && enabled) {
      callback();
    }
  }, [lastRefreshTimestamp, autoRefreshEnabled, enabled, callback]);
}
