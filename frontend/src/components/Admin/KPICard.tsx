/**
 * KPICard Component
 * Displays a single KPI metric with icon, value, trend indicator, and animation
 * Requirements: 1.9, 10.13
 */

import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

export interface KPICardProps {
  label: string;
  value: number;
  previousValue?: number;
  icon: React.ReactNode;
  color: "blue" | "green" | "red" | "purple" | "cyan" | "orange";
  unit?: string;
  subtitle?: string;
  precision?: number;
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  previousValue,
  icon,
  color,
  unit,
  subtitle,
  precision = 0,
}) => {
  const trend = previousValue !== undefined ? value - previousValue : 0;

  const colorClasses = {
    blue: "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
    green:
      "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
    red: "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400",
    purple:
      "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
    cyan: "bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400",
    orange:
      "bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400",
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {label}
        </span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>

      <div className="flex items-baseline gap-2">
        <span
          className="text-2xl font-bold text-gray-900 dark:text-white transition-all duration-300"
          aria-live="polite"
        >
          {value.toFixed(precision)}
        </span>
        {unit && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {unit}
          </span>
        )}
      </div>

      {subtitle && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {subtitle}
        </span>
      )}

      {trend !== 0 && (
        <div
          className={`flex items-center gap-1 mt-1 text-xs ${
            trend > 0 ? "text-green-600" : "text-red-600"
          }`}
          aria-label={`Trend: ${trend > 0 ? "up" : "down"} by ${Math.abs(
            trend
          ).toFixed(precision)}`}
        >
          {trend > 0 ? (
            <TrendingUp size={12} aria-hidden="true" />
          ) : (
            <TrendingDown size={12} aria-hidden="true" />
          )}
          <span>{Math.abs(trend).toFixed(precision)}</span>
        </div>
      )}
    </div>
  );
};
