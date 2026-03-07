/**
 * AlertCard Component
 * 
 * Displays individual alert with device ID, issue description, timestamp, severity badge,
 * and action buttons (Acknowledge, Assign Technician).
 * 
 * Features:
 * - Color-coded severity border
 * - Relative timestamp display
 * - Acknowledge button to remove alert
 * - Assign Technician button with modal
 * - Dark mode support
 * - Accessible with ARIA labels
 * 
 * @module AlertCard
 */

import React, { useState } from "react";
import { Check, UserPlus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Alert } from "../../types/alert";
import { StatusBadge } from "../common/StatusBadge";
import { AssignTechnicianModal } from "./modals/AssignTechnicianModal";

/**
 * AlertCard Props
 */
export interface AlertCardProps {
  /** Alert data to display */
  alert: Alert;
  /** Callback when alert is acknowledged */
  onAcknowledge: (alertId: string) => void;
  /** Callback when technician is assigned */
  onAssignTechnician: (alertId: string, technicianId: string) => void;
}

/**
 * Get severity border color classes
 */
function getSeverityBorderColor(severity: Alert["severity"]): string {
  switch (severity) {
    case "Critical":
      return "border-red-500 bg-red-50 dark:bg-red-900/10";
    case "Warning":
      return "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10";
    case "Safe":
      return "border-green-500 bg-green-50 dark:bg-green-900/10";
    default:
      return "border-gray-500 bg-gray-50 dark:bg-gray-900/10";
  }
}

/**
 * AlertCard Component
 * 
 * Displays an individual alert with severity indicator, device information,
 * issue description, and action buttons.
 * 
 * @example
 * ```tsx
 * <AlertCard
 *   alert={alert}
 *   onAcknowledge={(id) => handleAcknowledge(id)}
 *   onAssignTechnician={(id, techId) => handleAssign(id, techId)}
 * />
 * ```
 */
export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onAssignTechnician,
}) => {
  const [showAssignModal, setShowAssignModal] = useState(false);

  const handleAcknowledge = () => {
    onAcknowledge(alert.alertId);
  };

  const handleAssignConfirm = (technicianId: string) => {
    onAssignTechnician(alert.alertId, technicianId);
    setShowAssignModal(false);
  };

  return (
    <>
      <div
        className={`
          border-l-4 rounded p-4
          ${getSeverityBorderColor(alert.severity)}
          transition-all duration-200
          hover:shadow-md
        `}
        role="article"
        aria-label={`Alert: ${alert.issue}`}
      >
        <div className="flex items-start justify-between gap-4">
          {/* Alert Content */}
          <div className="flex-1 min-w-0">
            {/* Severity Badge and Device ID */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <StatusBadge status={alert.severity} size="sm" />
              <span className="font-mono text-sm text-gray-600 dark:text-gray-400">
                {alert.deviceId}
              </span>
            </div>

            {/* Issue Description */}
            <p className="text-sm text-gray-900 dark:text-white mb-1 font-medium">
              {alert.issue}
            </p>

            {/* Timestamp */}
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
            </p>

            {/* Assigned Technician */}
            {alert.assignedTechnician && (
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 flex items-center gap-1">
                <UserPlus size={12} />
                <span>Assigned to: {alert.assignedTechnician}</span>
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleAcknowledge}
              className="
                p-2
                bg-green-600 hover:bg-green-700
                text-white
                rounded
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                dark:focus:ring-offset-gray-800
              "
              title="Acknowledge alert"
              aria-label="Acknowledge alert"
            >
              <Check size={16} />
            </button>

            <button
              onClick={() => setShowAssignModal(true)}
              className="
                p-2
                bg-blue-600 hover:bg-blue-700
                text-white
                rounded
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                dark:focus:ring-offset-gray-800
              "
              title="Assign technician"
              aria-label="Assign technician to alert"
            >
              <UserPlus size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Assign Technician Modal */}
      {showAssignModal && (
        <AssignTechnicianModal
          alert={alert}
          onConfirm={handleAssignConfirm}
          onCancel={() => setShowAssignModal(false)}
        />
      )}
    </>
  );
};

export default AlertCard;
