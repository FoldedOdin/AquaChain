/**
 * Alert Type Definitions
 * Type definitions for water quality alerts
 */

import { AlertSeverity } from "./dashboard";

/**
 * Alert
 */
export interface Alert {
  alertId: string;
  deviceId: string;
  issue: string;
  timestamp: Date;
  severity: AlertSeverity;
  acknowledged: boolean;
  assignedTechnician?: string;
  sensorValues?: {
    pH?: number;
    turbidity?: number;
    tds?: number;
    temperature?: number;
  };
}

/**
 * Alert Filter Options
 */
export interface AlertFilters {
  severity: AlertSeverity | "All";
}

/**
 * Alert Count Badges
 */
export interface AlertCounts {
  total: number;
  critical: number;
  warning: number;
  safe: number;
}

/**
 * Test Alert Configuration
 */
export interface TestAlertConfig {
  deviceId: string;
  severity: AlertSeverity;
  issue: string;
}

/**
 * Technician Assignment Data
 */
export interface TechnicianAssignment {
  alertId: string;
  technicianId: string;
  technicianName: string;
}
