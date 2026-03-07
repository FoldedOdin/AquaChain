/**
 * RoleBadge Component
 * 
 * Displays user role with color coding and icon.
 * Similar to StatusBadge but specifically for user roles.
 * 
 * Features:
 * - Color-coded role indicators (Admin: purple, Technician: blue, Consumer: gray)
 * - Icon display for each role
 * - Size variants (sm, md, lg)
 * - Dark mode support
 * - Accessible with ARIA labels
 */

import React from "react";
import { Shield, Wrench, User } from "lucide-react";
import { UserRole } from "../../types/dashboard";

/**
 * Badge size variants
 */
export type BadgeSize = "sm" | "md" | "lg";

/**
 * RoleBadge Props
 */
export interface RoleBadgeProps {
  /** User role to display */
  role: UserRole;
  /** Badge size variant */
  size?: BadgeSize;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** ARIA label for accessibility */
  ariaLabel?: string;
}

/**
 * Get role configuration (color, icon, label)
 */
function getRoleConfig(role: UserRole): {
  color: string;
  bgColor: string;
  icon: React.ReactNode;
  label: string;
} {
  switch (role) {
    case "Admin":
      return {
        color: "text-purple-700 dark:text-purple-400",
        bgColor: "bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700",
        icon: <Shield />,
        label: "Admin",
      };
    case "Technician":
      return {
        color: "text-blue-700 dark:text-blue-400",
        bgColor: "bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700",
        icon: <Wrench />,
        label: "Technician",
      };
    case "Consumer":
      return {
        color: "text-gray-700 dark:text-gray-400",
        bgColor: "bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700",
        icon: <User />,
        label: "Consumer",
      };
    default:
      return {
        color: "text-gray-700 dark:text-gray-400",
        bgColor: "bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700",
        icon: <User />,
        label: role,
      };
  }
}

/**
 * Get size classes
 */
function getSizeClasses(size: BadgeSize): {
  container: string;
  icon: number;
  text: string;
} {
  switch (size) {
    case "sm":
      return {
        container: "px-2 py-0.5 gap-1",
        icon: 12,
        text: "text-xs",
      };
    case "lg":
      return {
        container: "px-4 py-2 gap-2",
        icon: 20,
        text: "text-base",
      };
    case "md":
    default:
      return {
        container: "px-3 py-1 gap-1.5",
        icon: 16,
        text: "text-sm",
      };
  }
}

/**
 * RoleBadge Component
 * 
 * Displays a color-coded role badge with icon.
 * 
 * @example
 * ```tsx
 * // Admin role
 * <RoleBadge role="Admin" />
 * 
 * // Technician role with large size
 * <RoleBadge role="Technician" size="lg" />
 * 
 * // Consumer role without icon
 * <RoleBadge role="Consumer" showIcon={false} />
 * ```
 */
export const RoleBadge: React.FC<RoleBadgeProps> = ({
  role,
  size = "md",
  showIcon = true,
  className = "",
  ariaLabel,
}) => {
  const config = getRoleConfig(role);
  const sizeClasses = getSizeClasses(size);

  const IconComponent = React.cloneElement(config.icon as React.ReactElement, {
    size: sizeClasses.icon,
  } as any);

  return (
    <span
      className={`
        inline-flex items-center justify-center
        ${sizeClasses.container}
        ${sizeClasses.text}
        font-medium
        rounded-full
        border
        ${config.bgColor}
        ${config.color}
        transition-colors duration-200
        ${className}
      `}
      role="status"
      aria-label={ariaLabel || `Role: ${config.label}`}
    >
      {showIcon && IconComponent}
      <span>{config.label}</span>
    </span>
  );
};

export default RoleBadge;
