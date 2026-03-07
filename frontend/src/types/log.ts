/**
 * Log Type Definitions
 * Type definitions for system logs
 */

import { LogLevel, LogSource } from "./dashboard";

/**
 * Log Entry
 */
export interface LogEntry {
  logId: string;
  timestamp: Date;
  source: LogSource;
  level: LogLevel;
  message: string;
  deviceId?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

/**
 * Log Filter Options
 */
export interface LogFilters {
  search: string;
  source: LogSource | "All";
  level: LogLevel | "All";
}

/**
 * Log Export Options
 */
export interface LogExportOptions {
  format: "JSON" | "CSV";
  dateRange: {
    start: Date;
    end: Date;
  };
  filters: LogFilters;
}
