/**
 * StatusBadge Component
 * 
 * Reusable badge component for displaying status with color coding.
 * Supports device status, user status, alert severity, and custom statuses.
 * 
 * Features:
 * - Color-coded status indicators
 * - Optional icon display
 * - Size variants (sm, md, lg)
 * - Dark mode support
 * - Accessible with ARIA labels
 * 
 * @module StatusBadge
 */

import React from "react";
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  Minus,
  Activity,
  User,
  Shield
} from "lucide-react";

/**
 * Status types
 */
export type DeviceStatus = "Online" | "Warning" | "Offline";
export type UserStatus = "Active" | "Inactive";
export type AlertSeverity = "Critical" | "Warning" | "Safe";
export type Status = DeviceStatus | UserStatus | AlertSeverity | string;

/**
 * Badge size variants
 */
export type BadgeSize = "sm" | "md" | "lg";

/**
 * StatusBadge Props
 */
export interface StatusBadgeProps {
  /** Status value to display */
  status: Status;
  /** Badge size variant */
  size?: BadgeSize;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Custom icon to display (overrides default) */
  icon?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** ARIA label for accessibility */
  ariaLabel?: string;
}

/**
 * Get status configuration (color, icon, label)
 */
function getStatusConfig(status: Status): {
  color: string;
  bgColor: string;
  icon: React.ReactNode;
  label: string;
} {
  const statusLower = status.toLowerCase();

  // Device Status
  if (statusLower === "online") {
    return {
      color: "text-green-700 dark:text-green-400",
      bgColor: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700",
      icon: <CheckCircle />,
      label: "Online",
    };
  }
  
  if (statusLower === "warning") {
    return {
      color: "text-yellow-700 dark:text-yellow-400",
      bgColor: "bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700",
      icon: <AlertTriangle />,
      label: "Warning",
    };
  }
  
  if (statusLower === "offline") {
    return {
      color: "text-red-700 dark:text-red-400",
      bgColor: "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700",
      icon: <XCircle />,
      label: "Offline",
    };
  }

  // User Status
  if (statusLower === "active") {
    return {
      color: "text-green-700 dark:text-green-400",
      bgColor: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700",
      icon: <Activity />,
      label: "Active",
    };
  }
  
  if (statusLower === "inactive") {
    return {
      color: "text-gray-700 dark:text-gray-400",
      bgColor: "bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700",
      icon: <Minus />,
      label: "Inactive",
    };
  }

  // Alert Severity
  if (statusLower === "critical") {
    return {
      color: "text-red-700 dark:text-red-400",
      bgColor: "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700",
      icon: <AlertTriangle />,
      label: "Critical",
    };
  }
  
  if (statusLower === "safe") {
    return {
      color: "text-green-700 dark:text-green-400",
      bgColor: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700",
      icon: <Shield />,
      label: "Safe",
    };
  }

  // Default/Unknown status
  return {
    color: "text-gray-700 dark:text-gray-400",
    bgColor: "bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700",
    icon: <Clock />,
    label: status,
  };
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
 * StatusBadge Component
 * 
 * Displays a color-coded status badge with optional icon.
 * Automatically determines color scheme based on status value.
 * 
 * @example
 * ```tsx
 * // Device status
 * <StatusBadge status="Online" />
 * 
 * // Alert severity
 * <StatusBadge status="Critical" size="lg" />
 * 
 * // User status without icon
 * <StatusBadge status="Active" showIcon={false} />
 * 
 * // Custom icon
 * <StatusBadge status="Processing" icon={<Loader />} />
 * ```
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "md",
  showIcon = true,
  icon: customIcon,
  className = "",
  ariaLabel,
}) => {
  const config = getStatusConfig(status);
  const sizeClasses = getSizeClasses(size);

  const IconComponent = customIcon || (
    React.cloneElement(config.icon as React.ReactElement, {
      size: sizeClasses.icon,
    })
  );

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
      aria-label={ariaLabel || `Status: ${config.label}`}
    >
      {showIcon && IconComponent}
      <span>{config.label}</span>
    </span>
  );
};

export default StatusBadge;
