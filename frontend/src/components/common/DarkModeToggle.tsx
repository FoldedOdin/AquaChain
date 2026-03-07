/**
 * DarkModeToggle Component
 * 
 * Toggle control for switching between light and dark themes.
 * Integrates with DashboardContext for theme persistence in localStorage.
 * 
 * Features:
 * - Smooth toggle animation
 * - Sun/Moon icons
 * - localStorage persistence via DashboardContext
 * - Keyboard accessible
 * - ARIA labels for screen readers
 * - Dark mode colors: backgrounds (#1a1a1a, #2d2d2d, #3d3d3d), text (#ffffff, #b0b0b0, #808080)
 * 
 * @module DarkModeToggle
 */

import React from "react";
import { Sun, Moon } from "lucide-react";
import { useDarkMode } from "../../hooks/useDarkMode";

/**
 * DarkModeToggle Props
 */
export interface DarkModeToggleProps {
  /** Additional CSS classes */
  className?: string;
  /** Show label text */
  showLabel?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

/**
 * Get size-specific classes
 */
function getSizeClasses(size: "sm" | "md" | "lg"): {
  container: string;
  toggle: string;
  icon: number;
  label: string;
} {
  switch (size) {
    case "sm":
      return {
        container: "gap-2",
        toggle: "w-10 h-6",
        icon: 14,
        label: "text-xs",
      };
    case "lg":
      return {
        container: "gap-3",
        toggle: "w-16 h-9",
        icon: 22,
        label: "text-base",
      };
    case "md":
    default:
      return {
        container: "gap-2.5",
        toggle: "w-14 h-7",
        icon: 18,
        label: "text-sm",
      };
  }
}

/**
 * DarkModeToggle Component
 * 
 * Toggle switch for dark mode with smooth animation.
 * Persists theme preference in localStorage via DashboardContext.
 * 
 * Theme Colors:
 * - Dark backgrounds: #1a1a1a (primary), #2d2d2d (secondary), #3d3d3d (tertiary)
 * - Dark text: #ffffff (primary), #b0b0b0 (secondary), #808080 (muted)
 * 
 * @example
 * ```tsx
 * // Default usage
 * <DarkModeToggle />
 * 
 * // With label
 * <DarkModeToggle showLabel />
 * 
 * // Small size
 * <DarkModeToggle size="sm" />
 * 
 * // Large with label
 * <DarkModeToggle size="lg" showLabel />
 * ```
 */
export const DarkModeToggle: React.FC<DarkModeToggleProps> = ({
  className = "",
  showLabel = false,
  size = "md",
}) => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const sizeClasses = getSizeClasses(size);

  return (
    <div
      className={`
        inline-flex items-center
        ${sizeClasses.container}
        ${className}
      `}
    >
      {/* Label (optional) */}
      {showLabel && (
        <span
          className={`
            ${sizeClasses.label}
            font-medium
            text-gray-700 dark:text-gray-300
          `}
        >
          {isDarkMode ? "Dark" : "Light"} Mode
        </span>
      )}

      {/* Toggle switch */}
      <button
        onClick={toggleDarkMode}
        className={`
          relative
          ${sizeClasses.toggle}
          rounded-full
          transition-colors duration-300 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          dark:focus:ring-offset-gray-800
          ${
            isDarkMode
              ? "bg-gray-700 dark:bg-gray-600"
              : "bg-gray-300"
          }
        `}
        role="switch"
        aria-checked={isDarkMode}
        aria-label={`Switch to ${isDarkMode ? "light" : "dark"} mode`}
        title={`Switch to ${isDarkMode ? "light" : "dark"} mode`}
      >
        {/* Toggle circle */}
        <span
          className={`
            absolute
            top-1
            ${size === "sm" ? "left-1" : size === "lg" ? "left-1.5" : "left-1"}
            inline-flex items-center justify-center
            ${size === "sm" ? "w-4 h-4" : size === "lg" ? "w-6 h-6" : "w-5 h-5"}
            rounded-full
            bg-white
            shadow-md
            transform transition-transform duration-300 ease-in-out
            ${
              isDarkMode
                ? size === "sm"
                  ? "translate-x-4"
                  : size === "lg"
                  ? "translate-x-7"
                  : "translate-x-7"
                : "translate-x-0"
            }
          `}
        >
          {/* Icon */}
          {isDarkMode ? (
            <Moon
              size={sizeClasses.icon}
              className="text-gray-700"
              strokeWidth={2.5}
            />
          ) : (
            <Sun
              size={sizeClasses.icon}
              className="text-yellow-500"
              strokeWidth={2.5}
            />
          )}
        </span>
      </button>
    </div>
  );
};

/**
 * DarkModeButton Component
 * 
 * Alternative button-style dark mode toggle
 */
export const DarkModeButton: React.FC<{
  className?: string;
  size?: "sm" | "md" | "lg";
}> = ({ className = "", size = "md" }) => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const sizeClasses = {
    sm: "p-1.5",
    md: "p-2",
    lg: "p-3",
  };

  const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24,
  };

  return (
    <button
      onClick={toggleDarkMode}
      className={`
        ${sizeClasses[size]}
        rounded-lg
        text-gray-600 dark:text-gray-400
        hover:text-gray-900 dark:hover:text-white
        hover:bg-gray-100 dark:hover:bg-gray-700
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-blue-500
        ${className}
      `}
      aria-label={`Switch to ${isDarkMode ? "light" : "dark"} mode`}
      title={`Switch to ${isDarkMode ? "light" : "dark"} mode`}
    >
      {isDarkMode ? (
        <Sun size={iconSizes[size]} />
      ) : (
        <Moon size={iconSizes[size]} />
      )}
    </button>
  );
};

/**
 * DarkModeMenuItem Component
 * 
 * Dark mode toggle for use in dropdown menus
 */
export const DarkModeMenuItem: React.FC<{
  className?: string;
}> = ({ className = "" }) => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  return (
    <button
      onClick={toggleDarkMode}
      className={`
        w-full
        flex items-center justify-between
        px-4 py-2
        text-sm
        text-gray-700 dark:text-gray-300
        hover:bg-gray-100 dark:hover:bg-gray-700
        transition-colors duration-200
        ${className}
      `}
      role="menuitem"
    >
      <span className="flex items-center gap-2">
        {isDarkMode ? <Moon size={16} /> : <Sun size={16} />}
        <span>{isDarkMode ? "Dark" : "Light"} Mode</span>
      </span>
      <span className="text-xs text-gray-500 dark:text-gray-400">
        {isDarkMode ? "On" : "Off"}
      </span>
    </button>
  );
};

export default DarkModeToggle;
