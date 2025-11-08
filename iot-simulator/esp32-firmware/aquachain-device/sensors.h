/*
 * AquaChain Sensor Management
 * 
 * This file contains sensor reading and calibration functions
 * for water quality monitoring sensors.
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// Sensor reading structure
struct SensorReadings {
  float ph;
  float turbidity;
  float tds;
  float temperature;
  float humidity;
  unsigned long timestamp;
};

class SensorManager {
private:
  int errorCount;
  unsigned long lastCalibration;
  bool sensorsInitialized;
  
  // Calibration values
  float phOffset;
  float phSlope;
  float tdsCalibrationFactor;
  float turbidityOffset;
  
public:
  SensorManager();
  
  // Initialization
  bool begin();
  
  // Sensor reading functions
  SensorReadings readAllSensors();
  float readPHSensor();
  float readTurbiditySensor();
  float readTDSSensor();
  
  // Calibration functions
  void calibrate();
  void calibratePH();
  void calibrateTDS();
  void calibrateTurbidity();
  
  // Status functions
  String getStatus();
  bool isHealthy();
  int getErrorCount();
  unsigned long getLastCalibrationTime();
  
  // Maintenance functions
  void resetErrors();
  void saveCalibration();
  void loadCalibration();
};

// Implementation

SensorManager::SensorManager() {
  errorCount = 0;
  lastCalibration = 0;
  sensorsInitialized = false;
  phOffset = PH_CALIBRATION_OFFSET;
  phSlope = PH_CALIBRATION_SLOPE;
  tdsCalibrationFactor = TDS_CALIBRATION_FACTOR;
  turbidityOffset = TURBIDITY_CALIBRATION_OFFSET;
}

bool SensorManager::begin() {
  Serial.println("Initializing sensors...");
  
  // Initialize analog pins
  pinMode(PH_SENSOR_PIN, INPUT);
  pinMode(TDS_SENSOR_PIN, INPUT);
  pinMode(TURBIDITY_SENSOR_PIN, INPUT);
  
  // Load calibration values from EEPROM
  loadCalibration();
  
  // Test sensor readings
  delay(1000);
  SensorReadings testReadings = readAllSensors();
  
  // Validate sensor readings
  if (testReadings.ph >= 0 && testReadings.ph <= 14 &&
      testReadings.turbidity >= 0 && testReadings.tds >= 0) {
    sensorsInitialized = true;
    Serial.println("✓ Sensors initialized successfully");
    return true;
  } else {
    Serial.println("✗ Sensor initialization failed");
    errorCount++;
    return false;
  }
}

SensorReadings SensorManager::readAllSensors() {
  SensorReadings readings;
  readings.timestamp = millis();
  
  try {
    readings.ph = readPHSensor();
    readings.turbidity = readTurbiditySensor();
    readings.tds = readTDSSensor();
    
    // Validate readings
    if (readings.ph < 0 || readings.ph > 14) {
      errorCount++;
      readings.ph = -999; // Error value
    }
    
    if (readings.turbidity < 0) {
      errorCount++;
      readings.turbidity = -999;
    }
    
    if (readings.tds < 0) {
      errorCount++;
      readings.tds = -999;
    }
    
  } catch (...) {
    Serial.println("Error reading sensors");
    errorCount++;
    readings.ph = -999;
    readings.turbidity = -999;
    readings.tds = -999;
  }
  
  return readings;
}

float SensorManager::readPHSensor() {
  // Read analog value
  int rawValue = analogRead(PH_SENSOR_PIN);
  
  // Convert to voltage (ESP32 ADC: 0-4095 = 0-3.3V)
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to pH using calibration
  // Standard pH probe: 2.5V = pH 7, -59.16mV per pH unit
  float ph = 7.0 + ((2.5 - voltage) / 0.05916);
  
  // Apply calibration
  ph = (ph * phSlope) + phOffset;
  
  // Constrain to valid pH range
  return constrain(ph, 0.0, 14.0);
}

float SensorManager::readTurbiditySensor() {
  // Read analog turbidity sensor
  int rawValue = analogRead(TURBIDITY_SENSOR_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to NTU (Nephelometric Turbidity Units)
  // This conversion depends on your specific sensor
  // Example for analog turbidity sensor:
  float turbidity;
  
  if (voltage < 2.5) {
    turbidity = 3000.0;  // Very high turbidity
  } else {
    turbidity = -1120.4 * voltage * voltage + 5742.3 * voltage - 4352.9;
  }
  
  // Apply calibration offset
  turbidity += turbidityOffset;
  
  // Ensure non-negative
  return max(0.0f, turbidity);
}

float SensorManager::readTDSSensor() {
  // Read TDS sensor
  int rawValue = analogRead(TDS_SENSOR_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to TDS (Total Dissolved Solids) in ppm
  // This conversion depends on your specific sensor
  float tds = (voltage * 1000.0) * tdsCalibrationFactor;
  
  // Ensure non-negative
  return max(0.0f, tds);
}

void SensorManager::calibrate() {
  Serial.println("Starting sensor calibration...");
  
  calibratePH();
  delay(2000);
  
  calibrateTDS();
  delay(2000);
  
  calibrateTurbidity();
  delay(2000);
  
  // Save calibration values
  saveCalibration();
  lastCalibration = millis();
  
  Serial.println("Sensor calibration complete");
}

void SensorManager::calibratePH() {
  Serial.println("pH Calibration:");
  Serial.println("1. Place pH probe in pH 7.0 buffer solution");
  Serial.println("2. Wait 30 seconds for stabilization");
  
  delay(30000); // Wait for stabilization
  
  // Read multiple samples
  float sum = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    int rawValue = analogRead(PH_SENSOR_PIN);
    float voltage = rawValue * (3.3 / 4095.0);
    sum += voltage;
    delay(1000);
  }
  
  float avgVoltage = sum / samples;
  
  // Calculate offset (should be 2.5V for pH 7.0)
  phOffset = 7.0 - ((2.5 - avgVoltage) / 0.05916);
  
  Serial.printf("pH calibration complete. Offset: %.3f\n", phOffset);
}

void SensorManager::calibrateTDS() {
  Serial.println("TDS Calibration:");
  Serial.println("1. Place TDS probe in calibration solution (1413 µS/cm)");
  Serial.println("2. Wait 30 seconds for stabilization");
  
  delay(30000);
  
  // Read multiple samples
  float sum = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    int rawValue = analogRead(TDS_SENSOR_PIN);
    float voltage = rawValue * (3.3 / 4095.0);
    sum += voltage;
    delay(1000);
  }
  
  float avgVoltage = sum / samples;
  
  // Calculate calibration factor for 1413 ppm solution
  tdsCalibrationFactor = 1413.0 / (avgVoltage * 1000.0);
  
  Serial.printf("TDS calibration complete. Factor: %.3f\n", tdsCalibrationFactor);
}

void SensorManager::calibrateTurbidity() {
  Serial.println("Turbidity Calibration:");
  Serial.println("1. Place turbidity sensor in clear water (0 NTU)");
  Serial.println("2. Wait 30 seconds for stabilization");
  
  delay(30000);
  
  // Read multiple samples
  float sum = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    int rawValue = analogRead(TURBIDITY_SENSOR_PIN);
    float voltage = rawValue * (3.3 / 4095.0);
    sum += voltage;
    delay(1000);
  }
  
  float avgVoltage = sum / samples;
  
  // Calculate offset for 0 NTU
  float calculatedTurbidity = -1120.4 * avgVoltage * avgVoltage + 5742.3 * avgVoltage - 4352.9;
  turbidityOffset = -calculatedTurbidity;
  
  Serial.printf("Turbidity calibration complete. Offset: %.3f\n", turbidityOffset);
}

String SensorManager::getStatus() {
  if (!sensorsInitialized) {
    return "not_initialized";
  } else if (errorCount > MAX_SENSOR_ERRORS) {
    return "error";
  } else if (errorCount > 0) {
    return "warning";
  } else {
    return "operational";
  }
}

bool SensorManager::isHealthy() {
  return sensorsInitialized && (errorCount <= SENSOR_ERROR_THRESHOLD);
}

int SensorManager::getErrorCount() {
  return errorCount;
}

unsigned long SensorManager::getLastCalibrationTime() {
  return lastCalibration;
}

void SensorManager::resetErrors() {
  errorCount = 0;
}

void SensorManager::saveCalibration() {
  // Save calibration values to EEPROM
  EEPROM.put(0, phOffset);
  EEPROM.put(4, phSlope);
  EEPROM.put(8, tdsCalibrationFactor);
  EEPROM.put(12, turbidityOffset);
  EEPROM.put(16, lastCalibration);
  EEPROM.commit();
  
  Serial.println("Calibration values saved to EEPROM");
}

void SensorManager::loadCalibration() {
  // Load calibration values from EEPROM
  EEPROM.get(0, phOffset);
  EEPROM.get(4, phSlope);
  EEPROM.get(8, tdsCalibrationFactor);
  EEPROM.get(12, turbidityOffset);
  EEPROM.get(16, lastCalibration);
  
  // Validate loaded values
  if (isnan(phOffset) || phOffset < -5 || phOffset > 5) {
    phOffset = PH_CALIBRATION_OFFSET;
  }
  if (isnan(phSlope) || phSlope < 0.5 || phSlope > 2.0) {
    phSlope = PH_CALIBRATION_SLOPE;
  }
  if (isnan(tdsCalibrationFactor) || tdsCalibrationFactor < 0.1 || tdsCalibrationFactor > 2.0) {
    tdsCalibrationFactor = TDS_CALIBRATION_FACTOR;
  }
  if (isnan(turbidityOffset) || turbidityOffset < -1000 || turbidityOffset > 1000) {
    turbidityOffset = TURBIDITY_CALIBRATION_OFFSET;
  }
  
  Serial.println("Calibration values loaded from EEPROM");
}

#endif // SENSORS_H