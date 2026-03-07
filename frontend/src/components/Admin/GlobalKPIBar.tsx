/**
 * GlobalKPIBar Component
 * Displays 6 key performance indicators at the top of the dashboard
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10, 12.5
 */

import React, { useEffect, useState } from "react";
import {
  Server,
  Activity,
  AlertTriangle,
  TrendingUp,
  Droplet,
  Clock,
} from "lucide-react";
import { KPICard } from "./KPICard";
import { MockDataBadge } from "../common/MockDataBadge";
import { LoadingSkeleton } from "../common/LoadingSkeleton";
import { useDashboard } from "../../contexts/DashboardContext";
import { MockDataService } from "../../services/mockDataService";
import { KPIMetrics } from "../../types/dashboard";

export const GlobalKPIBar: React.FC = () => {
  const { lastRefreshTimestamp } = useDashboard();
  const [metrics, setMetrics] = useState<KPIMetrics | null>(null);
  const [prevMetrics, setPrevMetrics] = useState<KPIMetrics | null>(null);

  useEffect(() => {
    const newMetrics = MockDataService.getKPIMetrics();
    setPrevMetrics(metrics);
    setMetrics(newMetrics);
  }, [lastRefreshTimestamp]);

  if (!metrics) {
    return (
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <LoadingSkeleton count={6} />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          System Overview
        </h2>
        <MockDataBadge />
      </div>

      <div
        className="grid grid-cols-6 gap-4 lg:grid-cols-3 md:grid-cols-2"
        role="region"
        aria-label="Key Performance Indicators"
      >
        <KPICard
          label="Total Devices"
          value={metrics.totalDevices}
          previousValue={prevMetrics?.totalDevices}
          icon={<Server size={20} aria-hidden="true" />}
          color="blue"
        />
        <KPICard
          label="Active Devices"
          value={metrics.activeDevices}
          previousValue={prevMetrics?.activeDevices}
          icon={<Activity size={20} aria-hidden="true" />}
          color="green"
          subtitle={`${((metrics.activeDevices / metrics.totalDevices) * 100).toFixed(1)}%`}
        />
        <KPICard
          label="Critical Alerts"
          value={metrics.criticalAlerts}
          previousValue={prevMetrics?.criticalAlerts}
          icon={<AlertTriangle size={20} aria-hidden="true" />}
          color="red"
        />
        <KPICard
          label="Data Ingest Rate"
          value={metrics.dataIngestRate}
          previousValue={prevMetrics?.dataIngestRate}
          icon={<TrendingUp size={20} aria-hidden="true" />}
          color="purple"
          unit="msg/min"
        />
        <KPICard
          label="Average WQI"
          value={metrics.averageWQI}
          previousValue={prevMetrics?.averageWQI}
          icon={<Droplet size={20} aria-hidden="true" />}
          color="cyan"
          precision={1}
        />
        <KPICard
          label="System Latency"
          value={metrics.systemLatency}
          previousValue={prevMetrics?.systemLatency}
          icon={<Clock size={20} aria-hidden="true" />}
          color="orange"
          unit="ms"
        />
      </div>
    </div>
  );
};
