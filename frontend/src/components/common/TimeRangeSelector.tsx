import React from "react";
import { TimeRange } from "../../types/dashboard";

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (timeRange: TimeRange) => void;
}

/**
 * TimeRangeSelector Component
 * 
 * Allows users to select time range for charts: 1h, 6h, 24h, 7d
 * 
 * Requirements: 2.6, 2.7
 */
const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  value,
  onChange,
}) => {
  const options: { value: TimeRange; label: string }[] = [
    { value: "1h", label: "1 Hour" },
    { value: "6h", label: "6 Hours" },
    { value: "24h", label: "24 Hours" },
    { value: "7d", label: "7 Days" },
  ];

  return (
    <div
      className="flex items-center gap-2"
      role="group"
      aria-label="Time range selector"
    >
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`px-3 py-1 text-sm rounded transition-colors ${
            value === option.value
              ? "bg-blue-600 text-white"
              : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
          }`}
          aria-pressed={value === option.value}
          aria-label={`Select ${option.label} time range`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
};

export default TimeRangeSelector;
