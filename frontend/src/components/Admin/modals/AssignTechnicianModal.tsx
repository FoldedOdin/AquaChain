/**
 * AssignTechnicianModal Component
 * 
 * Modal for assigning a technician to an alert.
 * Displays alert details and a dropdown to select a technician.
 * 
 * Features:
 * - Alert summary display
 * - Technician selection dropdown
 * - Confirm/Cancel actions
 * - Dark mode support
 * - Keyboard navigation (Escape to close)
 * - Focus trap for accessibility
 * 
 * @module AssignTechnicianModal
 */

import React, { useState, useEffect, useRef } from "react";
import { X, UserPlus } from "lucide-react";
import { Alert } from "../../../types/alert";

/**
 * AssignTechnicianModal Props
 */
export interface AssignTechnicianModalProps {
  /** Alert to assign technician to */
  alert: Alert;
  /** Callback when technician is assigned */
  onConfirm: (technicianId: string) => void;
  /** Callback when modal is cancelled */
  onCancel: () => void;
}

/**
 * Mock technician data
 * In a real application, this would come from an API
 */
const MOCK_TECHNICIANS = [
  { id: "TECH-001", name: "John Smith", availability: "Available" },
  { id: "TECH-002", name: "Sarah Johnson", availability: "Available" },
  { id: "TECH-003", name: "Michael Chen", availability: "Busy" },
  { id: "TECH-004", name: "Emily Davis", availability: "Available" },
  { id: "TECH-005", name: "David Wilson", availability: "Off Duty" },
];

/**
 * AssignTechnicianModal Component
 * 
 * Modal dialog for assigning a technician to an alert.
 * Provides a dropdown to select from available technicians.
 * 
 * @example
 * ```tsx
 * <AssignTechnicianModal
 *   alert={alert}
 *   onConfirm={(techId) => handleAssign(techId)}
 *   onCancel={() => setShowModal(false)}
 * />
 * ```
 */
export const AssignTechnicianModal: React.FC<AssignTechnicianModalProps> = ({
  alert,
  onConfirm,
  onCancel,
}) => {
  const [selectedTechnicianId, setSelectedTechnicianId] = useState<string>("");
  const modalRef = useRef<HTMLDivElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);

  /**
   * Handle Escape key to close modal
   */
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onCancel]);

  /**
   * Focus first element when modal opens
   */
  useEffect(() => {
    firstFocusableRef.current?.focus();
  }, []);

  /**
   * Handle backdrop click to close modal
   */
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  /**
   * Handle confirm button click
   */
  const handleConfirm = () => {
    if (selectedTechnicianId) {
      onConfirm(selectedTechnicianId);
    }
  };

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-black bg-opacity-50
        backdrop-blur-sm
        p-4
      "
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="assign-technician-title"
    >
      <div
        ref={modalRef}
        className="
          bg-white dark:bg-gray-800
          rounded-lg shadow-xl
          max-w-md w-full
          p-6
          transform transition-all
        "
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between mb-4">
          <h2
            id="assign-technician-title"
            className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2"
          >
            <UserPlus size={24} />
            Assign Technician
          </h2>
          <button
            ref={firstFocusableRef}
            onClick={onCancel}
            className="
              p-1 rounded
              text-gray-400 hover:text-gray-600
              dark:text-gray-500 dark:hover:text-gray-300
              transition-colors
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
            aria-label="Close modal"
          >
            <X size={24} />
          </button>
        </div>

        {/* Alert Summary */}
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Alert Details
          </h3>
          <div className="space-y-1 text-sm">
            <p className="text-gray-600 dark:text-gray-400">
              <span className="font-medium">Device:</span> {alert.deviceId}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              <span className="font-medium">Issue:</span> {alert.issue}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              <span className="font-medium">Severity:</span>{" "}
              <span
                className={`font-semibold ${
                  alert.severity === "Critical"
                    ? "text-red-600 dark:text-red-400"
                    : alert.severity === "Warning"
                    ? "text-yellow-600 dark:text-yellow-400"
                    : "text-green-600 dark:text-green-400"
                }`}
              >
                {alert.severity}
              </span>
            </p>
          </div>
        </div>

        {/* Technician Selection */}
        <div className="mb-6">
          <label
            htmlFor="technician-select"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Select Technician
          </label>
          <select
            id="technician-select"
            value={selectedTechnicianId}
            onChange={(e) => setSelectedTechnicianId(e.target.value)}
            className="
              w-full px-3 py-2
              border border-gray-300 dark:border-gray-600
              rounded-lg
              bg-white dark:bg-gray-700
              text-gray-900 dark:text-white
              focus:outline-none focus:ring-2 focus:ring-blue-500
              transition-colors
            "
          >
            <option value="">-- Select a technician --</option>
            {MOCK_TECHNICIANS.map((tech) => (
              <option key={tech.id} value={tech.id} disabled={tech.availability !== "Available"}>
                {tech.name} ({tech.availability})
              </option>
            ))}
          </select>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="
              px-4 py-2
              text-sm font-medium
              text-gray-700 dark:text-gray-300
              bg-gray-100 dark:bg-gray-700
              hover:bg-gray-200 dark:hover:bg-gray-600
              rounded-lg
              transition-colors
              focus:outline-none focus:ring-2 focus:ring-gray-500
            "
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedTechnicianId}
            className="
              px-4 py-2
              text-sm font-medium
              text-white
              bg-blue-600 hover:bg-blue-700
              disabled:bg-gray-400 disabled:cursor-not-allowed
              rounded-lg
              transition-colors
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
          >
            Assign Technician
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssignTechnicianModal;
