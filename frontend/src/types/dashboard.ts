/**
 * Dashboard Type Definitions
 * Type definitions for the Admin Global Monitoring Dashboard
 */

export type TimeRange = "1h" | "6h" | "24h" | "7d";

export type DeviceStatus = "Online" | "Warning" | "Offline";

export type AlertSeverity = "Critical" | "Warning" | "Safe";

export type UserRole = "Admin" | "Technician" | "Consumer";

export type UserStatus = "Active" | "Inactive";

export type LogLevel = "INFO" | "WARNING" | "ERROR";

export type LogSource = "CloudWatch" | "IoTCore";

export type ContaminationRisk = "Low" | "Medium" | "High";

export type PredictionTrend = "Improving" | "Stable" | "Declining";

export type Theme = "light" | "dark";

export type ExportFormat = "JSON" | "CSV";

/**
 * Dashboard Configuration
 */
export interface DashboardConfig {
  refreshInterval: number; // 10-300 seconds
  theme: Theme;
  visibleComponents: string[];
  filterPresets: FilterPreset[];
}

/**
 * Filter Preset for saving filter states
 */
export interface FilterPreset {
  id: string;
  name: string;
  filters: Record<string, any>;
}

/**
 * KPI Metrics displayed in Global KPI Bar
 */
export interface KPIMetrics {
  totalDevices: number;
  activeDevices: number;
  criticalAlerts: number;
  dataIngestRate: number; // messages per minute
  averageWQI: number;
  systemLatency: number; // milliseconds
}

/**
 * Time-series data point for charts
 */
export interface TimeSeriesDataPoint {
  timestamp: Date;
  value: number;
}

/**
 * System Health Data for charts
 */
export interface SystemHealthData {
  apiSuccessRate: TimeSeriesDataPoint[];
  deviceConnectivity: {
    online: TimeSeriesDataPoint[];
    warning: TimeSeriesDataPoint[];
    offline: TimeSeriesDataPoint[];
  };
  sensorTrends: {
    pH: TimeSeriesDataPoint[];
    turbidity: TimeSeriesDataPoint[];
    tds: TimeSeriesDataPoint[];
    temperature: TimeSeriesDataPoint[];
  };
  mlAnomalies: TimeSeriesDataPoint[];
}

/**
 * ML Insight Data
 */
export interface MLInsightData {
  contaminationRisk: {
    level: ContaminationRisk;
    percentage: number;
  };
  anomalyDetection: {
    count: number;
    last24Hours: number;
  };
  prediction: {
    trend: PredictionTrend;
    wqiForecast: number;
  };
  modelInfo: {
    version: string;
    accuracy: number;
    lastTraining: Date;
  };
}

/**
 * Notification
 */
export interface Notification {
  id: string;
  type: "success" | "warning" | "error" | "info";
  message: string;
  timestamp: Date;
  read: boolean;
}

/**
 * Dashboard Context Value
 */
export interface DashboardContextValue {
  config: DashboardConfig;
  updateConfig: (updates: Partial<DashboardConfig>) => void;
  
  autoRefreshEnabled: boolean;
  toggleAutoRefresh: () => void;
  
  lastRefreshTimestamp: Date;
  triggerManualRefresh: () => void;
  
  userRole: UserRole;
  userId: string;
  
  notificationHistory: Notification[];
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
}
