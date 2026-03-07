/**
 * AlertManagementPanel Component
 * 
 * Displays and manages active alerts with filtering, sorting, and action capabilities.
 * Shows alert count badges, severity filters, and auto-refreshes every 30 seconds.
 * 
 * Features:
 * - Alert list sorted by severity (Critical first) then timestamp (newest first)
 * - Alert count badges (Total, Critical, Warning)
 * - Severity filter buttons (All, Critical, Warning, Safe)
 * - Auto-refresh every 30 seconds via DashboardContext
 * - Acknowledge button to remove alerts
 * - Assign Technician button with modal
 * - Toast notifications for Critical alerts
 * - Empty state when no alerts active
 * - Mock Data badge
 * - Dark mode support
 * 
 * @module AlertManagementPanel
 */

import React, { useState, useEffect, useMemo } from "react";
import { CheckCircle } from "lucide-react";
import { toast } from "react-toastify";
import { Alert, AlertCounts } from "../../types/alert";
import { AlertSeverity } from "../../types/dashboard";
import { useDashboard } from "../../contexts/DashboardContext";
import { MockDataService } from "../../services/mockDataService";
import { AlertCard } from "./AlertCard";
import { MockDataBadge } from "../common/MockDataBadge";

/**
 * Sort alerts by severity (Critical > Warning > Safe) then by timestamp (newest first)
 */
function sortAlerts(alerts: Alert[]): Alert[] {
  const severityOrder: Record<AlertSeverity, number> = {
    Critical: 0,
    Warning: 1,
    Safe: 2,
  };

  return [...alerts].sort((a, b) => {
    // First sort by severity
    const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
    if (severityDiff !== 0) return severityDiff;

    // Then sort by timestamp (newest first)
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
}

/**
 * Calculate alert counts by severity
 */
function calculateAlertCounts(alerts: Alert[]): AlertCounts {
  return {
    total: alerts.length,
    critical: alerts.filter((a) => a.severity === "Critical").length,
    warning: alerts.filter((a) => a.severity === "Warning").length,
    safe: alerts.filter((a) => a.severity === "Safe").length,
  };
}

/**
 * AlertManagementPanel Component
 * 
 * Main panel for managing alerts. Displays alerts in a list with filtering
 * and action capabilities. Integrates with notification system for Critical alerts.
 * 
 * @example
 * ```tsx
 * <AlertManagementPanel />
 * ```
 */
export const AlertManagementPanel: React.FC = () => {
  const { lastRefreshTimestamp, addNotification } = useDashboard();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | "All">("All");
  const [previousCriticalAlertIds, setPreviousCriticalAlertIds] = useState<Set<string>>(new Set());

  /**
   * Fetch alerts and check for new critical alerts
   */
  useEffect(() => {
    const allAlerts = MockDataService.getAlerts();

    // Check for new critical alerts (not in previous set)
    const newCriticalAlerts = allAlerts.filter(
      (alert) =>
        alert.severity === "Critical" && !previousCriticalAlertIds.has(alert.alertId)
    );

    // Show toast notifications for new critical alerts
    newCriticalAlerts.forEach((alert) => {
      toast.error(`Critical Alert: ${alert.issue} (${alert.deviceId})`, {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
      });

      // Add to notification history
      addNotification({
        type: "error",
        message: `Critical Alert: ${alert.issue} (${alert.deviceId})`,
      });
    });

    // Update previous critical alert IDs
    const currentCriticalIds = new Set(
      allAlerts.filter((a) => a.severity === "Critical").map((a) => a.alertId)
    );
    setPreviousCriticalAlertIds(currentCriticalIds);

    // Sort alerts before setting state
    const sortedAlerts = sortAlerts(allAlerts);
    setAlerts(sortedAlerts);
  }, [lastRefreshTimestamp, addNotification, previousCriticalAlertIds]);

  /**
   * Filter alerts by severity
   */
  const filteredAlerts = useMemo(() => {
    if (severityFilter === "All") return alerts;
    return alerts.filter((alert) => alert.severity === severityFilter);
  }, [alerts, severityFilter]);

  /**
   * Calculate alert counts
   */
  const alertCounts = useMemo(() => calculateAlertCounts(alerts), [alerts]);

  /**
   * Handle alert acknowledgment
   */
  const handleAcknowledge = (alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.alertId !== alertId));
    toast.success("Alert acknowledged", {
      position: "top-right",
      autoClose: 3000,
    });
  };

  /**
   * Handle technician assignment
   */
  const handleAssignTechnician = (alertId: string, technicianId: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.alertId === alertId ? { ...a, assignedTechnician: technicianId } : a
      )
    );
    toast.success("Technician assigned successfully", {
      position: "top-right",
      autoClose: 3000,
    });
  };

  /**
   * Get filter button classes
   */
  const getFilterButtonClasses = (filter: AlertSeverity | "All") => {
    const isActive = severityFilter === filter;
    const baseClasses = "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors duration-200";

    if (isActive) {
      switch (filter) {
        case "Critical":
          return `${baseClasses} bg-red-600 text-white`;
        case "Warning":
          return `${baseClasses} bg-yellow-600 text-white`;
        case "Safe":
          return `${baseClasses} bg-green-600 text-white`;
        case "All":
        default:
          return `${baseClasses} bg-blue-600 text-white`;
      }
    }

    return `${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Alert Management
        </h2>
        <MockDataBadge />
      </div>

      {/* Alert Count Badges */}
      <div className="flex items-center gap-4 mb-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Total:</span>
          <span className="px-2.5 py-1 bg-gray-100 dark:bg-gray-700 rounded-md text-sm font-semibold text-gray-900 dark:text-white">
            {alertCounts.total}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Critical:</span>
          <span className="px-2.5 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md text-sm font-semibold">
            {alertCounts.critical}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Warning:</span>
          <span className="px-2.5 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-md text-sm font-semibold">
            {alertCounts.warning}
          </span>
        </div>
      </div>

      {/* Severity Filter Buttons */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button
          onClick={() => setSeverityFilter("All")}
          className={getFilterButtonClasses("All")}
          aria-label="Show all alerts"
          aria-pressed={severityFilter === "All"}
        >
          All
        </button>
        <button
          onClick={() => setSeverityFilter("Critical")}
          className={getFilterButtonClasses("Critical")}
          aria-label="Show critical alerts only"
          aria-pressed={severityFilter === "Critical"}
        >
          Critical
        </button>
        <button
          onClick={() => setSeverityFilter("Warning")}
          className={getFilterButtonClasses("Warning")}
          aria-label="Show warning alerts only"
          aria-pressed={severityFilter === "Warning"}
        >
          Warning
        </button>
        <button
          onClick={() => setSeverityFilter("Safe")}
          className={getFilterButtonClasses("Safe")}
          aria-label="Show safe alerts only"
          aria-pressed={severityFilter === "Safe"}
        >
          Safe
        </button>
      </div>

      {/* Alert List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {filteredAlerts.length === 0 ? (
          // Empty State
          <div className="text-center py-12">
            <CheckCircle
              size={64}
              className="mx-auto mb-4 text-green-500 dark:text-green-400 opacity-50"
            />
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-1">
              No active alerts
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {severityFilter === "All"
                ? "All systems are operating normally"
                : `No ${severityFilter.toLowerCase()} alerts at this time`}
            </p>
          </div>
        ) : (
          // Alert Cards
          filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.alertId}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onAssignTechnician={handleAssignTechnician}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default AlertManagementPanel;
