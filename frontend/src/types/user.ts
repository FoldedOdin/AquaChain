/**
 * User Type Definitions
 * Type definitions for user management
 */

import { UserRole, UserStatus } from "./dashboard";

/**
 * User
 */
export interface User {
  userId: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  lastLogin: Date;
  createdAt: Date;
  devices?: string[]; // Array of device IDs
}

/**
 * User Filter Options
 */
export interface UserFilters {
  search: string;
  role: UserRole | "All";
  status: UserStatus | "All";
}

/**
 * User Action Types
 */
export type UserAction = "changeRole" | "disable" | "resetPassword";

/**
 * Role Change Data
 */
export interface RoleChangeData {
  userId: string;
  newRole: UserRole;
  reason?: string;
}

/**
 * Password Reset Data
 */
export interface PasswordResetData {
  userId: string;
  email: string;
}
