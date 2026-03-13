/**
 * Connection Status Badge Component
 * Displays device online/offline/unknown status with appropriate styling
 */

import React from "react";
import { Wifi, WifiOff, HelpCircle } from "lucide-react";
import { ConnectionStatus } from "../../types/dashboard";

interface ConnectionStatusBadgeProps {
  status: ConnectionStatus;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const ConnectionStatusBadge: React.FC<ConnectionStatusBadgeProps> = ({
  status,
  showIcon = true,
  size = "md",
  className = "",
}) => {
  const getStatusConfig = (status: ConnectionStatus) => {
    switch (status) {
      case "online":
        return {
          label: "Online",
          bgColor: "bg-green-100 dark:bg-green-900",
          textColor: "text-green-800 dark:text-green-200",
          borderColor: "border-green-200 dark:border-green-700",
          icon: Wifi,
          pulse: true,
        };
      case "offline":
        return {
          label: "Offline",
          bgColor: "bg-red-100 dark:bg-red-900",
          textColor: "text-red-800 dark:text-red-200",
          borderColor: "border-red-200 dark:border-red-700",
          icon: WifiOff,
          pulse: false,
        };
      case "unknown":
      default:
        return {
          label: "Unknown",
          bgColor: "bg-gray-100 dark:bg-gray-700",
          textColor: "text-gray-800 dark:text-gray-200",
          borderColor: "border-gray-200 dark:border-gray-600",
          icon: HelpCircle,
          pulse: false,
        };
    }
  };

  const getSizeClasses = (size: "sm" | "md" | "lg") => {
    switch (size) {
      case "sm":
        return {
          container: "px-2 py-1 text-xs",
          icon: "w-3 h-3",
        };
      case "lg":
        return {
          container: "px-4 py-2 text-base",
          icon: "w-5 h-5",
        };
      case "md":
      default:
        return {
          container: "px-3 py-1 text-sm",
          icon: "w-4 h-4",
        };
    }
  };

  const config = getStatusConfig(status);
  const sizeClasses = getSizeClasses(size);
  const IconComponent = config.icon;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-medium
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        ${sizeClasses.container}
        ${config.pulse ? "animate-pulse" : ""}
        ${className}
      `}
      title={`Device is ${config.label.toLowerCase()}`}
    >
      {showIcon && (
        <IconComponent 
          className={`${sizeClasses.icon} ${config.pulse ? "animate-pulse" : ""}`}
          aria-hidden="true"
        />
      )}
      <span>{config.label}</span>
    </span>
  );
};

export default ConnectionStatusBadge;