/**
 * UserActions Component
 * 
 * Action buttons for user management table.
 * Provides Change Role, Disable User, and Reset Password actions.
 * 
 * Features:
 * - Change Role modal with role selection
 * - Disable User confirmation modal
 * - Reset Password confirmation modal
 * - Toast notifications for actions
 * - Keyboard navigation support
 */

import React, { useState } from "react";
import { UserCog, UserX, KeyRound } from "lucide-react";
import { toast } from "react-toastify";

import { User } from "../../types/user";
import { UserRole } from "../../types/dashboard";
import ChangeRoleModal from "./modals/ChangeRoleModal";
import ConfirmationModal from "./modals/ConfirmationModal";

interface UserActionsProps {
  user: User;
}

const UserActions: React.FC<UserActionsProps> = ({ user }) => {
  const [showChangeRoleModal, setShowChangeRoleModal] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);

  // Handle change role
  const handleChangeRole = (newRole: UserRole) => {
    // Simulate role change
    toast.success(`User role changed to ${newRole} for ${user.email}`);
    setShowChangeRoleModal(false);
  };

  // Handle disable user
  const handleDisableUser = () => {
    // Simulate user disable
    toast.warning(`User ${user.email} has been disabled`);
    setShowDisableModal(false);
  };

  // Handle reset password
  const handleResetPassword = () => {
    // Simulate password reset
    toast.info(`Password reset email sent to ${user.email}`);
    setShowResetPasswordModal(false);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowChangeRoleModal(true)}
          className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
          title="Change Role"
          aria-label={`Change role for ${user.email}`}
        >
          <UserCog size={18} />
        </button>

        <button
          onClick={() => setShowDisableModal(true)}
          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
          title="Disable User"
          aria-label={`Disable ${user.email}`}
          disabled={user.status === "Inactive"}
        >
          <UserX size={18} />
        </button>

        <button
          onClick={() => setShowResetPasswordModal(true)}
          className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded transition-colors"
          title="Reset Password"
          aria-label={`Reset password for ${user.email}`}
        >
          <KeyRound size={18} />
        </button>
      </div>

      {/* Change Role Modal */}
      {showChangeRoleModal && (
        <ChangeRoleModal
          user={user}
          onConfirm={handleChangeRole}
          onCancel={() => setShowChangeRoleModal(false)}
        />
      )}

      {/* Disable User Modal */}
      {showDisableModal && (
        <ConfirmationModal
          title="Disable User"
          message={`Are you sure you want to disable ${user.email}? The user will no longer be able to access the system.`}
          confirmLabel="Disable User"
          confirmVariant="danger"
          onConfirm={handleDisableUser}
          onCancel={() => setShowDisableModal(false)}
        />
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && (
        <ConfirmationModal
          title="Reset Password"
          message={`A password reset email will be sent to ${user.email}. The user will need to follow the link in the email to set a new password.`}
          confirmLabel="Send Reset Email"
          confirmVariant="warning"
          onConfirm={handleResetPassword}
          onCancel={() => setShowResetPasswordModal(false)}
        />
      )}
    </>
  );
};

export default UserActions;
