/**
 * Common UI Components
 * 
 * Reusable components used across the AquaChain dashboard.
 * 
 * @module components/common
 */

export { StatusBadge } from "./StatusBadge";
export type { StatusBadgeProps, DeviceStatus, UserStatus, AlertSeverity, Status, BadgeSize } from "./StatusBadge";

export { MockDataBadge } from "./MockDataBadge";
export type { MockDataBadgeProps } from "./MockDataBadge";

export {
  LoadingSkeleton,
  CardSkeleton,
  TableRowSkeleton,
  ChartSkeleton,
  KPICardSkeleton,
} from "./LoadingSkeleton";
export type { LoadingSkeletonProps, SkeletonVariant } from "./LoadingSkeleton";

export {
  AutoRefreshIndicator,
  CompactAutoRefreshIndicator,
} from "./AutoRefreshIndicator";
export type { AutoRefreshIndicatorProps } from "./AutoRefreshIndicator";

export {
  DarkModeToggle,
  DarkModeButton,
  DarkModeMenuItem,
} from "./DarkModeToggle";
export type { DarkModeToggleProps } from "./DarkModeToggle";
