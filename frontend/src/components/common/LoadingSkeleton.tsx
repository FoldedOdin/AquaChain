/**
 * LoadingSkeleton Component
 * 
 * Placeholder component displayed during data loading with shimmer animation.
 * Provides visual feedback while content is being fetched.
 * 
 * Features:
 * - Shimmer animation effect
 * - Multiple shape variants (text, card, circle, rectangle)
 * - Configurable count for multiple skeletons
 * - Dark mode support
 * - Accessible with ARIA labels
 * 
 * @module LoadingSkeleton
 */

import React from "react";

/**
 * Skeleton shape variants
 */
export type SkeletonVariant = "text" | "card" | "circle" | "rectangle";

/**
 * LoadingSkeleton Props
 */
export interface LoadingSkeletonProps {
  /** Number of skeleton elements to render */
  count?: number;
  /** Shape variant */
  variant?: SkeletonVariant;
  /** Custom width (CSS value) */
  width?: string;
  /** Custom height (CSS value) */
  height?: string;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show shimmer animation */
  animate?: boolean;
}

/**
 * Get variant-specific classes
 */
function getVariantClasses(variant: SkeletonVariant): {
  container: string;
  defaultWidth: string;
  defaultHeight: string;
} {
  switch (variant) {
    case "text":
      return {
        container: "rounded",
        defaultWidth: "100%",
        defaultHeight: "1rem",
      };
    case "circle":
      return {
        container: "rounded-full",
        defaultWidth: "3rem",
        defaultHeight: "3rem",
      };
    case "rectangle":
      return {
        container: "rounded-lg",
        defaultWidth: "100%",
        defaultHeight: "8rem",
      };
    case "card":
    default:
      return {
        container: "rounded-lg",
        defaultWidth: "100%",
        defaultHeight: "12rem",
      };
  }
}

/**
 * Single Skeleton Element
 */
const SkeletonElement: React.FC<Omit<LoadingSkeletonProps, "count">> = ({
  variant = "card",
  width,
  height,
  className = "",
  animate = true,
}) => {
  const variantClasses = getVariantClasses(variant);

  return (
    <div
      className={`
        ${variantClasses.container}
        bg-gray-200 dark:bg-gray-700
        ${animate ? "animate-pulse" : ""}
        ${className}
      `}
      style={{
        width: width || variantClasses.defaultWidth,
        height: height || variantClasses.defaultHeight,
      }}
      role="status"
      aria-label="Loading content"
      aria-live="polite"
    >
      {/* Shimmer effect overlay */}
      {animate && (
        <div
          className="
            w-full h-full
            bg-gradient-to-r
            from-transparent
            via-white/20 dark:via-white/10
            to-transparent
            animate-shimmer
          "
          style={{
            backgroundSize: "200% 100%",
            animation: "shimmer 2s infinite",
          }}
        />
      )}
    </div>
  );
};

/**
 * LoadingSkeleton Component
 * 
 * Displays loading placeholder(s) with shimmer animation.
 * Supports multiple variants and configurable count.
 * 
 * @example
 * ```tsx
 * // Single card skeleton
 * <LoadingSkeleton />
 * 
 * // Multiple text skeletons
 * <LoadingSkeleton variant="text" count={3} />
 * 
 * // Circle avatar skeleton
 * <LoadingSkeleton variant="circle" width="4rem" height="4rem" />
 * 
 * // Custom rectangle
 * <LoadingSkeleton variant="rectangle" width="100%" height="200px" />
 * 
 * // Without animation
 * <LoadingSkeleton animate={false} />
 * ```
 */
export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 1,
  variant = "card",
  width,
  height,
  className = "",
  animate = true,
}) => {
  // Render multiple skeletons if count > 1
  if (count > 1) {
    return (
      <div className="space-y-4" role="status" aria-label="Loading content">
        {Array.from({ length: count }).map((_, index) => (
          <SkeletonElement
            key={index}
            variant={variant}
            width={width}
            height={height}
            className={className}
            animate={animate}
          />
        ))}
      </div>
    );
  }

  // Render single skeleton
  return (
    <SkeletonElement
      variant={variant}
      width={width}
      height={height}
      className={className}
      animate={animate}
    />
  );
};

/**
 * Predefined skeleton layouts for common use cases
 */

/**
 * Card Skeleton
 * 
 * Skeleton for card-like content with header and body
 */
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = "" }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
    <div className="space-y-4">
      {/* Header */}
      <LoadingSkeleton variant="text" width="60%" height="1.5rem" />
      {/* Body lines */}
      <LoadingSkeleton variant="text" width="100%" height="1rem" />
      <LoadingSkeleton variant="text" width="90%" height="1rem" />
      <LoadingSkeleton variant="text" width="80%" height="1rem" />
    </div>
  </div>
);

/**
 * Table Row Skeleton
 * 
 * Skeleton for table row with multiple columns
 */
export const TableRowSkeleton: React.FC<{ columns?: number; className?: string }> = ({
  columns = 5,
  className = "",
}) => (
  <div className={`flex items-center gap-4 py-3 ${className}`}>
    {Array.from({ length: columns }).map((_, index) => (
      <LoadingSkeleton
        key={index}
        variant="text"
        width={index === 0 ? "20%" : "15%"}
        height="1rem"
      />
    ))}
  </div>
);

/**
 * Chart Skeleton
 * 
 * Skeleton for chart/graph content
 */
export const ChartSkeleton: React.FC<{ className?: string }> = ({ className = "" }) => (
  <div className={`space-y-3 ${className}`}>
    {/* Chart title */}
    <LoadingSkeleton variant="text" width="40%" height="1.25rem" />
    {/* Chart area */}
    <LoadingSkeleton variant="rectangle" width="100%" height="200px" />
  </div>
);

/**
 * KPI Card Skeleton
 * 
 * Skeleton for KPI metric card
 */
export const KPICardSkeleton: React.FC<{ className?: string }> = ({ className = "" }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
    <div className="space-y-3">
      {/* Label */}
      <LoadingSkeleton variant="text" width="60%" height="0.875rem" />
      {/* Value */}
      <LoadingSkeleton variant="text" width="40%" height="2rem" />
      {/* Trend */}
      <LoadingSkeleton variant="text" width="30%" height="0.75rem" />
    </div>
  </div>
);

export default LoadingSkeleton;
