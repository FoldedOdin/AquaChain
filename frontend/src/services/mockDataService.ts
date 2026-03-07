/**
 * Mock Data Service for Admin Global Monitoring Dashboard
 * 
 * Provides realistic simulated data for all dashboard components with seeded random generation.
 * All data is deterministic based on the seed for reproducibility in testing.
 * 
 * Key Features:
 * - Seeded random number generation (seedrandom library)
 * - Realistic distributions (normal, exponential)
 * - 500 devices, 200 alerts, 100 users, 10,000 logs
 * - Time-series data generation for charts
 * - Sensor reading validation and alert generation
 * 
 * @module mockDataService
 */

import seedrandom from "seedrandom";
import {
  Device,
  SensorReadings,
  Coordinates,
} from "../types/device";
import {
  Alert,
} from "../types/alert";
import {
  User,
} from "../types/user";
import {
  LogEntry,
} from "../types/log";
import {
  KPIMetrics,
  SystemHealthData,
  TimeSeriesDataPoint,
  MLInsightData,
  DeviceStatus,
  AlertSeverity,
  UserRole,
  UserStatus,
  LogLevel,
  LogSource,
  TimeRange,
  ContaminationRisk,
  PredictionTrend,
} from "../types/dashboard";

/**
 * Device marker data for map visualization
 */
export interface DeviceMarkerData {
  deviceId: string;
  location: string;
  coordinates: Coordinates;
  status: DeviceStatus;
  wqi: number;
  lastData: Date;
}

/**
 * City location data for device generation
 */
interface CityLocation {
  name: string;
  lat: number;
  lng: number;
}

/**
 * MockDataService class providing all mock data generation
 */
class MockDataServiceClass {
  private rng: () => number;
  private devices: Device[] = [];
  private alerts: Alert[] = [];
  private users: User[] = [];
  private logs: LogEntry[] = [];
  private seed: string;

  /**
   * Initialize the mock data service with a seed
   * @param seed - Seed for random number generator (default: "aquachain-2024")
   */
  constructor(seed: string = "aquachain-2024") {
    this.seed = seed;
    this.rng = seedrandom(seed);
    this.initializeData();
  }

  /**
   * Initialize all mock data on service creation
   */
  private initializeData(): void {
    this.devices = this.generateDevices(500);
    this.alerts = this.generateAlerts(200);
    this.users = this.generateUsers(100);
    this.logs = this.generateLogs(10000);
  }

  /**
   * Generate mock devices with realistic distributions
   * @param count - Number of devices to generate (default: 500)
   * @returns Array of Device objects
   */
  private generateDevices(count: number): Device[] {
    const devices: Device[] = [];
    const cities: CityLocation[] = [
      { name: "Mumbai", lat: 19.076, lng: 72.8777 },
      { name: "Delhi", lat: 28.7041, lng: 77.1025 },
      { name: "Bangalore", lat: 12.9716, lng: 77.5946 },
      { name: "Hyderabad", lat: 17.385, lng: 78.4867 },
      { name: "Chennai", lat: 13.0827, lng: 80.2707 },
      { name: "Kolkata", lat: 22.5726, lng: 88.3639 },
      { name: "Pune", lat: 18.5204, lng: 73.8567 },
      { name: "Ahmedabad", lat: 23.0225, lng: 72.5714 },
    ];

    for (let i = 0; i < count; i++) {
      const city = cities[Math.floor(this.rng() * cities.length)];
      const statusRoll = this.rng();
      
      // Status distribution: 70% Online, 20% Warning, 10% Offline
      const status: DeviceStatus =
        statusRoll < 0.7 ? "Online" : statusRoll < 0.9 ? "Warning" : "Offline";

      // Battery follows normal distribution (mean=75%, std=15%)
      const battery = Math.max(
        0,
        Math.min(100, Math.round(this.normalRandom(75, 15)))
      );

      // WQI follows normal distribution (mean=78, std=12)
      const wqi = Math.max(
        0,
        Math.min(100, Math.round(this.normalRandom(78, 12)))
      );

      // Last data timestamp based on status
      const lastDataDelay =
        status === "Online"
          ? this.rng() * 120 // 0-120 seconds
          : status === "Warning"
          ? 120 + this.rng() * 480 // 120-600 seconds
          : 600 + this.rng() * 3600; // 600-4200 seconds

      const readings = this.generateSensorReadings();

      devices.push({
        deviceId: `ESP32-${this.generateAlphanumeric(6)}`,
        location: `${city.name} - Zone ${Math.floor(this.rng() * 10) + 1}`,
        status,
        lastData: new Date(Date.now() - lastDataDelay * 1000),
        battery,
        coordinates: {
          lat: city.lat + (this.rng() - 0.5) * 0.5, // ±0.25 degrees
          lng: city.lng + (this.rng() - 0.5) * 0.5,
        },
        wqi,
        readings,
      });
    }

    return devices;
  }

  /**
   * Generate sensor readings with realistic ranges
   * @returns SensorReadings object
   */
  private generateSensorReadings(): SensorReadings {
    return {
      pH: this.normalRandom(7.2, 0.5), // Normal: 6.5-8.5
      turbidity: Math.max(0, this.exponentialRandom(3)), // Low turbidity is common
      tds: this.normalRandom(400, 150), // Normal: 100-800 ppm
      temperature: this.normalRandom(22, 4), // Normal: 15-30°C
    };
  }

  /**
   * Generate alerts based on sensor thresholds
   * @param count - Number of alerts to generate (default: 200)
   * @returns Array of Alert objects
   */
  private generateAlerts(count: number): Alert[] {
    const alerts: Alert[] = [];
    const issueTemplates = [
      { severity: "Critical" as AlertSeverity, template: "pH critically low: {pH}" },
      { severity: "Critical" as AlertSeverity, template: "pH critically high: {pH}" },
      {
        severity: "Critical" as AlertSeverity,
        template: "Turbidity critically high: {turbidity} NTU",
      },
      { severity: "Critical" as AlertSeverity, template: "TDS critically high: {tds} ppm" },
      { severity: "Warning" as AlertSeverity, template: "pH outside normal range: {pH}" },
      { severity: "Warning" as AlertSeverity, template: "Turbidity elevated: {turbidity} NTU" },
      { severity: "Warning" as AlertSeverity, template: "TDS elevated: {tds} ppm" },
      { severity: "Warning" as AlertSeverity, template: "Device battery low: {battery}%" },
    ];

    for (let i = 0; i < count; i++) {
      const device = this.devices[Math.floor(this.rng() * this.devices.length)];
      const issueTemplate =
        issueTemplates[Math.floor(this.rng() * issueTemplates.length)];

      const issue = issueTemplate.template
        .replace("{pH}", device.readings?.pH.toFixed(2) || "N/A")
        .replace("{turbidity}", device.readings?.turbidity.toFixed(1) || "N/A")
        .replace("{tds}", device.readings?.tds.toFixed(0) || "N/A")
        .replace("{battery}", device.battery.toString());

      alerts.push({
        alertId: `ALERT-${this.generateAlphanumeric(8)}`,
        deviceId: device.deviceId,
        issue,
        timestamp: new Date(Date.now() - this.rng() * 86400000), // Last 24 hours
        severity: issueTemplate.severity,
        acknowledged: false,
      });
    }

    // Sort by severity (Critical first) then timestamp (newest first)
    return alerts.sort((a, b) => {
      const severityValues: Record<AlertSeverity, number> = {
        Critical: 3,
        Warning: 2,
        Safe: 1,
      };
      const severityDiff = severityValues[b.severity] - severityValues[a.severity];

      if (severityDiff !== 0) {
        return severityDiff;
      }
      return b.timestamp.getTime() - a.timestamp.getTime();
    });
  }

  /**
   * Generate mock users
   * @param count - Number of users to generate (default: 100)
   * @returns Array of User objects
   */
  private generateUsers(count: number): User[] {
    const users: User[] = [];
    const roles: UserRole[] = ["Admin", "Technician", "Consumer"];
    const roleDistribution = [0.1, 0.3, 0.6]; // 10% Admin, 30% Technician, 60% Consumer

    for (let i = 0; i < count; i++) {
      const roleRoll = this.rng();
      const role: UserRole =
        roleRoll < roleDistribution[0]
          ? "Admin"
          : roleRoll < roleDistribution[0] + roleDistribution[1]
          ? "Technician"
          : "Consumer";

      const statusRoll = this.rng();
      const status: UserStatus = statusRoll < 0.9 ? "Active" : "Inactive";

      users.push({
        userId: `USER-${this.generateAlphanumeric(8)}`,
        email: `user${i}@aquachain.example.com`,
        role,
        lastLogin: new Date(Date.now() - this.rng() * 604800000), // Last 7 days
        status,
        createdAt: new Date(Date.now() - this.rng() * 31536000000), // Last year
      });
    }

    return users;
  }

  /**
   * Generate system logs
   * @param count - Number of log entries to generate (default: 10,000)
   * @returns Array of LogEntry objects
   */
  private generateLogs(count: number): LogEntry[] {
    const logs: LogEntry[] = [];
    const sources: LogSource[] = ["CloudWatch", "IoTCore"];
    const levels: LogLevel[] = ["INFO", "WARNING", "ERROR"];
    const levelDistribution = [0.7, 0.25, 0.05]; // 70% INFO, 25% WARNING, 5% ERROR

    const messageTemplates: Record<LogLevel, string[]> = {
      INFO: [
        "Device {deviceId} connected successfully",
        "Data ingestion completed for {deviceId}",
        "ML model inference completed in {latency}ms",
        "User {userId} logged in",
        "API request processed successfully",
      ],
      WARNING: [
        "Device {deviceId} connection unstable",
        "High latency detected: {latency}ms",
        "Battery low on device {deviceId}: {battery}%",
        "Sensor calibration recommended for {deviceId}",
      ],
      ERROR: [
        "Device {deviceId} connection failed",
        "ML model inference error for {deviceId}",
        "Database write failed for {deviceId}",
        "API request timeout for device {deviceId}",
      ],
    };

    for (let i = 0; i < count; i++) {
      const levelRoll = this.rng();
      const level: LogLevel =
        levelRoll < levelDistribution[0]
          ? "INFO"
          : levelRoll < levelDistribution[0] + levelDistribution[1]
          ? "WARNING"
          : "ERROR";

      const source = sources[Math.floor(this.rng() * sources.length)];
      const device = this.devices[Math.floor(this.rng() * this.devices.length)];

      const templates = messageTemplates[level];
      const template = templates[Math.floor(this.rng() * templates.length)];

      const message = template
        .replace("{deviceId}", device.deviceId)
        .replace("{userId}", `USER-${this.generateAlphanumeric(8)}`)
        .replace("{latency}", Math.floor(this.rng() * 1000).toString())
        .replace("{battery}", device.battery.toString());

      logs.push({
        logId: `LOG-${this.generateAlphanumeric(12)}`,
        timestamp: new Date(Date.now() - this.rng() * 86400000), // Last 24 hours
        source,
        level,
        message,
        deviceId: this.rng() < 0.7 ? device.deviceId : undefined,
      });
    }

    // Sort by timestamp (newest first)
    return logs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Generate time-series data for charts
   * @param timeRange - Time range for data generation
   * @param baseValue - Base value for the metric
   * @param variance - Variance around the base value
   * @param trend - Trend coefficient (positive = increasing, negative = decreasing)
   * @returns Array of TimeSeriesDataPoint objects
   */
  private generateTimeSeriesData(
    timeRange: TimeRange,
    baseValue: number,
    variance: number,
    trend: number = 0
  ): TimeSeriesDataPoint[] {
    const now = Date.now();
    const intervals: Record<
      TimeRange,
      { duration: number; points: number; interval: number }
    > = {
      "1h": { duration: 3600000, points: 60, interval: 60000 },
      "6h": { duration: 21600000, points: 72, interval: 300000 },
      "24h": { duration: 86400000, points: 96, interval: 900000 },
      "7d": { duration: 604800000, points: 168, interval: 3600000 },
    };

    const config = intervals[timeRange];
    const dataPoints: TimeSeriesDataPoint[] = [];

    for (let i = 0; i < config.points; i++) {
      const timestamp = new Date(now - config.duration + i * config.interval);
      const trendValue = trend * (i / config.points);
      const randomVariance = (this.rng() - 0.5) * variance;
      const value = Math.max(0, baseValue + trendValue + randomVariance);

      dataPoints.push({ timestamp, value });
    }

    return dataPoints;
  }

  // ========== Public API Methods ==========

  /**
   * Get KPI metrics for Global KPI Bar
   * @returns KPIMetrics object
   */
  public getKPIMetrics(): KPIMetrics {
    const activeDevices = this.devices.filter((d) => d.status === "Online").length;
    const criticalAlerts = this.alerts.filter((a) => a.severity === "Critical").length;
    const avgWQI =
      this.devices.reduce((sum, d) => sum + d.wqi, 0) / this.devices.length;

    // Data ingest rate calculation:
    // Devices send data every 60 seconds = 1 message per minute per device
    // Add realistic variance (±20%)
    const messagesPerDevicePerMinute = 1;
    const variance = 0.8 + this.rng() * 0.4; // 0.8 to 1.2
    const dataIngestRate = Math.round(
      activeDevices * messagesPerDevicePerMinute * variance
    );

    return {
      totalDevices: this.devices.length,
      activeDevices,
      criticalAlerts,
      dataIngestRate,
      averageWQI: Math.round(avgWQI * 10) / 10,
      systemLatency: Math.round(50 + this.rng() * 150), // 50-200ms
    };
  }

  /**
   * Get system health data for charts
   * @param timeRange - Time range for data generation
   * @returns SystemHealthData object
   */
  public getSystemHealthData(timeRange: TimeRange): SystemHealthData {
    return {
      apiSuccessRate: this.generateTimeSeriesData(timeRange, 99.5, 1, 0),
      deviceConnectivity: {
        online: this.generateTimeSeriesData(timeRange, 350, 20, 0),
        warning: this.generateTimeSeriesData(timeRange, 100, 15, 0),
        offline: this.generateTimeSeriesData(timeRange, 50, 10, 0),
      },
      sensorTrends: {
        pH: this.generateTimeSeriesData(timeRange, 7.2, 0.3, 0),
        turbidity: this.generateTimeSeriesData(timeRange, 3.5, 1.5, 0),
        tds: this.generateTimeSeriesData(timeRange, 400, 50, 0),
        temperature: this.generateTimeSeriesData(timeRange, 22, 3, 0),
      },
      mlAnomalies: this.generateTimeSeriesData(timeRange, 5, 3, 0),
    };
  }

  /**
   * Get all devices
   * @returns Array of Device objects
   */
  public getDevices(): Device[] {
    return this.devices;
  }

  /**
   * Get devices for map visualization
   * @returns Array of DeviceMarkerData objects
   */
  public getDevicesForMap(): DeviceMarkerData[] {
    return this.devices.map((d) => ({
      deviceId: d.deviceId,
      location: d.location,
      coordinates: d.coordinates,
      status: d.status,
      wqi: d.wqi,
      lastData: d.lastData,
    }));
  }

  /**
   * Get all alerts
   * @returns Array of Alert objects
   */
  public getAlerts(): Alert[] {
    return this.alerts;
  }

  /**
   * Get ML insights
   * @returns MLInsightData object
   */
  public getMLInsights(): MLInsightData {
    const riskRoll = this.rng();
    const riskLevel: ContaminationRisk =
      riskRoll < 0.6 ? "Low" : riskRoll < 0.9 ? "Medium" : "High";

    const riskPercentage =
      riskLevel === "Low"
        ? Math.round(this.rng() * 30)
        : riskLevel === "Medium"
        ? Math.round(30 + this.rng() * 40)
        : Math.round(70 + this.rng() * 30);

    const predictionRoll = this.rng();
    const predictionTrend: PredictionTrend =
      predictionRoll < 0.3
        ? "Improving"
        : predictionRoll < 0.8
        ? "Stable"
        : "Declining";

    const anomalyCount = Math.floor(this.rng() * 50);
    const wqiForecast = Math.round(this.normalRandom(78, 10));

    return {
      contaminationRisk: {
        level: riskLevel,
        percentage: riskPercentage,
      },
      anomalyDetection: {
        count: anomalyCount,
        last24Hours: anomalyCount,
      },
      prediction: {
        trend: predictionTrend,
        wqiForecast,
      },
      modelInfo: {
        version: "XGBoost v2.0.3",
        accuracy: 99.74,
        lastTraining: new Date(Date.now() - this.rng() * 604800000), // Last 7 days
      },
    };
  }

  /**
   * Get all users
   * @returns Array of User objects
   */
  public getUsers(): User[] {
    return this.users;
  }

  /**
   * Get all logs
   * @returns Array of LogEntry objects
   */
  public getLogs(): LogEntry[] {
    return this.logs;
  }

  /**
   * Get new logs (for auto-refresh)
   * @param count - Number of new logs to generate
   * @returns Array of LogEntry objects
   */
  public getNewLogs(count: number): LogEntry[] {
    return this.generateLogs(count);
  }

  // ========== Utility Methods ==========

  /**
   * Generate random alphanumeric string
   * @param length - Length of the string
   * @returns Random alphanumeric string
   */
  private generateAlphanumeric(length: number): string {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let result = "";
    for (let i = 0; i < length; i++) {
      result += chars[Math.floor(this.rng() * chars.length)];
    }
    return result;
  }

  /**
   * Generate random number from normal distribution (Box-Muller transform)
   * @param mean - Mean of the distribution
   * @param stdDev - Standard deviation of the distribution
   * @returns Random number from normal distribution
   */
  private normalRandom(mean: number, stdDev: number): number {
    const u1 = this.rng();
    const u2 = this.rng();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return z0 * stdDev + mean;
  }

  /**
   * Generate random number from exponential distribution
   * @param lambda - Rate parameter of the distribution
   * @returns Random number from exponential distribution
   */
  private exponentialRandom(lambda: number): number {
    return -Math.log(1 - this.rng()) / lambda;
  }
}

// Export singleton instance
export const MockDataService = new MockDataServiceClass();

// Export class for testing
export { MockDataServiceClass };
