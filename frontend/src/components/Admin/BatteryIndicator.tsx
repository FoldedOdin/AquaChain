/**
 * Battery Indicator Component
 * Displays battery level with color coding
 * 
 * Color coding:
 * - Green: >50% (High)
 * - Yellow: 20-50% (Medium)
 * - Red: <20% (Low)
 */

import React from "react";
import { Battery, BatteryLow, BatteryMedium } from "lucide-react";

interface BatteryIndicatorProps {
  level: number; // 0-100
}

const BatteryIndicator: React.FC<BatteryIndicatorProps> = ({ level }) => {
  const getBatteryColor = () => {
    if (level > 50) return "text-green-600 dark:text-green-400";
    if (level >= 20) return "text-yellow-600 dark:text-yellow-400";
    return "text-red-600 dark:text-red-400";
  };

  const getBatteryIcon = () => {
    if (level > 50) return <Battery size={16} />;
    if (level >= 20) return <BatteryMedium size={16} />;
    return <BatteryLow size={16} />;
  };

  const getBatteryLabel = () => {
    if (level > 50) return "High";
    if (level >= 20) return "Medium";
    return "Low";
  };

  return (
    <div className="flex items-center gap-2">
      <span className={getBatteryColor()} aria-hidden="true">
        {getBatteryIcon()}
      </span>
      <span className="text-sm text-gray-900 dark:text-white">
        {level}%
      </span>
      <span className="sr-only">
        Battery level: {level}% ({getBatteryLabel()})
      </span>
    </div>
  );
};

export default BatteryIndicator;
