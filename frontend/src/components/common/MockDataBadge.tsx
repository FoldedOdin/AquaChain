/**
 * MockDataBadge Component
 * 
 * Visual indicator that displays "MOCK DATA" to clarify that displayed data is simulated.
 * Used throughout the dashboard to distinguish mock data from real production data.
 * 
 * Features:
 * - Prominent visual styling
 * - Tooltip with explanation
 * - Dark mode support
 * - Accessible with ARIA labels
 * 
 * @module MockDataBadge
 */

import React, { useState } from "react";
import { Info } from "lucide-react";

/**
 * MockDataBadge Props
 */
export interface MockDataBadgeProps {
  /** Additional CSS classes */
  className?: string;
  /** Custom tooltip text */
  tooltipText?: string;
  /** Badge size variant */
  size?: "sm" | "md" | "lg";
}

/**
 * MockDataBadge Component
 * 
 * Displays a "MOCK DATA" indicator badge with tooltip.
 * Helps users understand that data is simulated for demonstration purposes.
 * 
 * @example
 * ```tsx
 * // Default usage
 * <MockDataBadge />
 * 
 * // Small size
 * <MockDataBadge size="sm" />
 * 
 * // Custom tooltip
 * <MockDataBadge tooltipText="This data is generated for testing" />
 * ```
 */
export const MockDataBadge: React.FC<MockDataBadgeProps> = ({
  className = "",
  tooltipText = "This data is simulated for demonstration purposes. No real AWS infrastructure is required.",
  size = "md",
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const sizeClasses = {
    sm: {
      container: "px-2 py-0.5 gap-1",
      text: "text-xs",
      icon: 12,
    },
    md: {
      container: "px-2.5 py-1 gap-1.5",
      text: "text-xs",
      icon: 14,
    },
    lg: {
      container: "px-3 py-1.5 gap-2",
      text: "text-sm",
      icon: 16,
    },
  };

  const classes = sizeClasses[size];

  return (
    <div className="relative inline-block">
      <span
        className={`
          inline-flex items-center
          ${classes.container}
          ${classes.text}
          font-semibold
          rounded-md
          bg-purple-100 dark:bg-purple-900/30
          text-purple-700 dark:text-purple-400
          border border-purple-300 dark:border-purple-700
          transition-colors duration-200
          cursor-help
          ${className}
        `}
        role="status"
        aria-label="Mock data indicator"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        tabIndex={0}
      >
        <Info size={classes.icon} />
        <span>MOCK DATA</span>
      </span>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className="
            absolute z-50 
            bottom-full left-1/2 transform -translate-x-1/2 mb-2
            px-3 py-2
            max-w-xs
            text-xs
            text-white
            bg-gray-900 dark:bg-gray-800
            rounded-lg
            shadow-lg
            pointer-events-none
            whitespace-normal
          "
          role="tooltip"
        >
          {tooltipText}
          {/* Tooltip arrow */}
          <div
            className="
              absolute top-full left-1/2 transform -translate-x-1/2
              w-0 h-0
              border-l-4 border-l-transparent
              border-r-4 border-r-transparent
              border-t-4 border-t-gray-900 dark:border-t-gray-800
            "
          />
        </div>
      )}
    </div>
  );
};

export default MockDataBadge;
