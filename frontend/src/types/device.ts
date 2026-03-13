/**
 * Device Type Definitions
 * Type definitions for IoT devices in the AquaChain system
 */

import { DeviceStatus, ConnectionStatus } from "./dashboard";

/**
 * Geographic Coordinates
 */
export interface Coordinates {
  lat: number;
  lng: number;
}

/**
 * Sensor Readings
 */
export interface SensorReadings {
  pH: number; // 0-14
  turbidity: number; // 0-1000 NTU
  tds: number; // 0-2000 ppm
  temperature: number; // -10-50°C
}

/**
 * Device Metadata
 */
export interface DeviceMetadata {
  firmwareVersion: string;
  batteryLevel: number; // 0-100
  signalStrength: number; // dBm
}

/**
 * Device
 */
export interface Device {
  deviceId: string; // Format: ESP32-XXXXXX
  location: string;
  status: DeviceStatus;
  connectionStatus: ConnectionStatus; // New field for online/offline status
  lastData: Date;
  lastSeen?: Date; // When device last sent data
  battery: number; // 0-100
  coordinates: Coordinates;
  wqi: number; // 0-100
  readings?: SensorReadings;
  metadata?: DeviceMetadata;
}

/**
 * Device Filter Options
 */
export interface DeviceFilters {
  search: string;
  status: DeviceStatus | "All";
  battery: "High" | "Medium" | "Low" | "All";
}

/**
 * Device Action Types
 */
export type DeviceAction = "view" | "restart" | "calibrate" | "disable";

/**
 * Device Registration Form Data
 */
export interface DeviceRegistrationData {
  deviceId: string;
  location: string;
  coordinates: Coordinates;
}
