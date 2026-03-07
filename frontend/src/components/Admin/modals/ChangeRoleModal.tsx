/**
 * ChangeRoleModal Component
 * 
 * Modal for changing user role with role selection dropdown.
 * 
 * Features:
 * - Role selection dropdown (Admin, Technician, Consumer)
 * - Current role display
 * - Confirmation and cancel actions
 * - Keyboard navigation (Escape to close)
 * - Focus trap for accessibility
 */

import React, { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";

import { User } from "../../../types/user";
import { UserRole } from "../../../types/dashboard";
import RoleBadge from "../RoleBadge";

interface ChangeRoleModalProps {
  user: User;
  onConfirm: (newRole: UserRole) => void;
  onCancel: () => void;
}

const ChangeRoleModal: React.FC<ChangeRoleModalProps> = ({
  user,
  onConfirm,
  onCancel,
}) => {
  const [selectedRole, setSelectedRole] = useState<UserRole>(user.role);
  const modalRef = useRef<HTMLDivElement>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onCancel]);

  // Focus trap
  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;

    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener("keydown", handleTab);
    firstElement?.focus();

    return () => document.removeEventListener("keydown", handleTab);
  }, []);

  const handleConfirm = () => {
    if (selectedRole !== user.role) {
      onConfirm(selectedRole);
    } else {
      onCancel();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-role-title"
    >
      <div
        ref={modalRef}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2
            id="change-role-title"
            className="text-xl font-semibold text-gray-900 dark:text-white"
          >
            Change User Role
          </h2>
          <button
            onClick={onCancel}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              User
            </label>
            <p className="text-sm text-gray-900 dark:text-white">{user.email}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Current Role
            </label>
            <RoleBadge role={user.role} />
          </div>

          <div>
            <label
              htmlFor="role-select"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              New Role
            </label>
            <select
              id="role-select"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as UserRole)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="Admin">Admin</option>
              <option value="Technician">Technician</option>
              <option value="Consumer">Consumer</option>
            </select>
          </div>

          {selectedRole !== user.role && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                Changing the user's role will affect their permissions and access to system features.
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={selectedRole === user.role}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            Change Role
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChangeRoleModal;
