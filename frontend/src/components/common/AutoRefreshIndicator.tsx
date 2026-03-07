/**
 * AutoRefreshIndicator Component
 * 
 * Visual indicator showing last update timestamp and countdown to next refresh.
 * Provides real-time feedback on dashboard auto-refresh status.
 * 
 * Features:
 * - Last update timestamp display
 * - Countdown timer to next refresh
 * - Circular progress indicator
 * - Pause/resume auto-refresh control
 * - Dark mode support
 * - Accessible with ARIA labels
 * 
 * @module AutoRefreshIndicator
 */

import React, { useState, useEffect } from "react";
import { RefreshCw, Pause, Play } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useDashboard } from "../../contexts/DashboardContext";

/**
 * AutoRefreshIndicator Props
 */
export interface AutoRefreshIndicatorProps {
  /** Additional CSS classes */
  className?: string;
  /** Whether to show pause/play button */
  showControls?: boolean;
  /** Compact mode (smaller size) */
  compact?: boolean;
}

/**
 * AutoRefreshIndicator Component
 * 
 * Displays last update time and countdown to next refresh.
 * Integrates with DashboardContext for refresh state management.
 * 
 * @example
 * ```tsx
 * // Default usage
 * <AutoRefreshIndicator />
 * 
 * // With controls
 * <AutoRefreshIndicator showControls />
 * 
 * // Compact mode
 * <AutoRefreshIndicator compact />
 * ```
 */
export const AutoRefreshIndicator: React.FC<AutoRefreshIndicatorProps> = ({
  className = "",
  showControls = true,
  compact = false,
}) => {
  const {
    lastRefreshTimestamp,
    autoRefreshEnabled,
    toggleAutoRefresh,
    config,
  } = useDashboard();

  const [countdown, setCountdown] = useState(config.refreshInterval);
  const [relativeTime, setRelativeTime] = useState("");

  /**
   * Update countdown timer
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      setCountdown(0);
      return;
    }

    // Calculate seconds since last refresh
    const updateCountdown = () => {
      const now = Date.now();
      const lastRefresh = lastRefreshTimestamp.getTime();
      const elapsed = Math.floor((now - lastRefresh) / 1000);
      const remaining = Math.max(0, config.refreshInterval - elapsed);
      setCountdown(remaining);
    };

    // Update immediately
    updateCountdown();

    // Update every second
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [lastRefreshTimestamp, autoRefreshEnabled, config.refreshInterval]);

  /**
   * Update relative time display
   */
  useEffect(() => {
    const updateRelativeTime = () => {
      setRelativeTime(formatDistanceToNow(lastRefreshTimestamp, { addSuffix: true }));
    };

    // Update immediately
    updateRelativeTime();

    // Update every 10 seconds
    const interval = setInterval(updateRelativeTime, 10000);

    return () => clearInterval(interval);
  }, [lastRefreshTimestamp]);

  /**
   * Calculate progress percentage
   */
  const progressPercentage = autoRefreshEnabled
    ? ((config.refreshInterval - countdown) / config.refreshInterval) * 100
    : 0;

  /**
   * Format countdown display
   */
  const formatCountdown = (seconds: number): string => {
    if (seconds === 0) return "Refreshing...";
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (compact) {
    return (
      <div
        className={`
          inline-flex items-center gap-2
          px-3 py-1.5
          text-xs
          text-gray-600 dark:text-gray-400
          bg-gray-100 dark:bg-gray-800
          rounded-md
          border border-gray-200 dark:border-gray-700
          ${className}
        `}
        role="status"
        aria-label={`Last updated ${relativeTime}. ${
          autoRefreshEnabled ? `Next refresh in ${formatCountdown(countdown)}` : "Auto-refresh paused"
        }`}
      >
        <RefreshCw
          size={14}
          className={autoRefreshEnabled && countdown > 0 ? "animate-spin" : ""}
        />
        <span>{autoRefreshEnabled ? formatCountdown(countdown) : "Paused"}</span>
      </div>
    );
  }

  return (
    <div
      className={`
        inline-flex items-center gap-3
        px-4 py-2
        bg-white dark:bg-gray-800
        rounded-lg
        border border-gray-200 dark:border-gray-700
        shadow-sm
        ${className}
      `}
      role="status"
      aria-label={`Last updated ${relativeTime}. ${
        autoRefreshEnabled ? `Next refresh in ${formatCountdown(countdown)}` : "Auto-refresh paused"
      }`}
    >
      {/* Circular progress indicator */}
      <div className="relative w-10 h-10">
        {/* Background circle */}
        <svg className="w-10 h-10 transform -rotate-90">
          <circle
            cx="20"
            cy="20"
            r="16"
            stroke="currentColor"
            strokeWidth="3"
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />
          {/* Progress circle */}
          {autoRefreshEnabled && (
            <circle
              cx="20"
              cy="20"
              r="16"
              stroke="currentColor"
              strokeWidth="3"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 16}`}
              strokeDashoffset={`${2 * Math.PI * 16 * (1 - progressPercentage / 100)}`}
              className="text-blue-500 dark:text-blue-400 transition-all duration-1000 ease-linear"
              strokeLinecap="round"
            />
          )}
        </svg>
        {/* Icon in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <RefreshCw
            size={16}
            className={`
              text-gray-600 dark:text-gray-400
              ${autoRefreshEnabled && countdown === 0 ? "animate-spin" : ""}
            `}
          />
        </div>
      </div>

      {/* Text content */}
      <div className="flex flex-col">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Last updated {relativeTime}
        </span>
        <span className="text-sm font-medium text-gray-900 dark:text-white">
          {autoRefreshEnabled ? (
            <>Next refresh in {formatCountdown(countdown)}</>
          ) : (
            <>Auto-refresh paused</>
          )}
        </span>
      </div>

      {/* Pause/Play control */}
      {showControls && (
        <button
          onClick={toggleAutoRefresh}
          className="
            p-2
            text-gray-600 dark:text-gray-400
            hover:text-gray-900 dark:hover:text-white
            hover:bg-gray-100 dark:hover:bg-gray-700
            rounded-md
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-blue-500
          "
          aria-label={autoRefreshEnabled ? "Pause auto-refresh" : "Resume auto-refresh"}
          title={autoRefreshEnabled ? "Pause auto-refresh" : "Resume auto-refresh"}
        >
          {autoRefreshEnabled ? <Pause size={18} /> : <Play size={18} />}
        </button>
      )}
    </div>
  );
};

/**
 * Compact Auto Refresh Indicator
 * 
 * Simplified version for use in headers or toolbars
 */
export const CompactAutoRefreshIndicator: React.FC<{
  className?: string;
}> = ({ className = "" }) => {
  return <AutoRefreshIndicator compact className={className} />;
};

export default AutoRefreshIndicator;
