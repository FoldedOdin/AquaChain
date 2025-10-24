/*
 * AquaChain ESP32 Configuration
 * 
 * This file contains all configuration parameters for the ESP32 device.
 * Update these values according to your specific deployment.
 */

#ifndef CONFIG_H
#define CONFIG_H

// Device Information
#define DEVICE_ID "AquaChain-Device-001"
#define FIRMWARE_VERSION "1.0.0"
#define HARDWARE_VERSION "ESP32-v1"

// WiFi Configuration
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define WIFI_TIMEOUT 30000          // 30 seconds
#define WIFI_CHECK_INTERVAL 60000   // Check WiFi every 60 seconds
#define MAX_WIFI_RECONNECT_ATTEMPTS 5

// AWS IoT Configuration
#define AWS_IOT_ENDPOINT "your-endpoint-ats.iot.us-east-1.amazonaws.com"
#define AWS_IOT_PORT 8883
#define MQTT_RECONNECT_DELAY 5000   // 5 seconds
#define MAX_RECONNECT_ATTEMPTS 10

// Device Location (update with actual coordinates)
#define DEVICE_LATITUDE 37.7749
#define DEVICE_LONGITUDE -122.4194

// Sensor Pin Definitions
#define PH_SENSOR_PIN A0
#define TDS_SENSOR_PIN A3
#define TURBIDITY_SENSOR_PIN A6
#define DHT_PIN 4
#define DHT_TYPE DHT22

// I2C Configuration
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define I2C_FREQUENCY 100000

// Optional GPS Module
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
#define GPS_BAUD_RATE 9600

// Battery Monitoring (optional)
#define BATTERY_PIN A7
#define BATTERY_VOLTAGE_DIVIDER 2.0  // Voltage divider ratio
#define BATTERY_MIN_VOLTAGE 3.0      // Minimum battery voltage
#define BATTERY_MAX_VOLTAGE 4.2      // Maximum battery voltage (for Li-ion)

// Timing Configuration
#define SENSOR_READING_INTERVAL 30000   // 30 seconds
#define HEARTBEAT_INTERVAL 300000       // 5 minutes
#define CALIBRATION_INTERVAL 86400000   // 24 hours

// Power Management
#define ENABLE_POWER_SAVING true
#define LIGHT_SLEEP_DURATION 1000       // 1 second light sleep
#define DEEP_SLEEP_DURATION 3600000000  // 1 hour deep sleep (microseconds)

// Watchdog Timer
#define WDT_TIMEOUT 30  // 30 seconds

// Data Storage
#define MAX_OFFLINE_READINGS 100
#define EEPROM_SIZE 512

// Sensor Calibration Values (update after calibration)
#define PH_CALIBRATION_OFFSET 0.0
#define PH_CALIBRATION_SLOPE 1.0
#define TDS_CALIBRATION_FACTOR 0.5
#define TURBIDITY_CALIBRATION_OFFSET 0.0

// Quality Thresholds
#define PH_MIN_NORMAL 6.5
#define PH_MAX_NORMAL 8.5
#define TURBIDITY_MAX_NORMAL 5.0
#define TDS_MAX_NORMAL 500.0

// Error Handling
#define MAX_SENSOR_ERRORS 5
#define SENSOR_ERROR_THRESHOLD 3

// Debug Configuration
#define DEBUG_MODE true
#define SERIAL_BAUD_RATE 115200

// Feature Flags
#define ENABLE_GPS false
#define ENABLE_BATTERY_MONITORING false
#define ENABLE_OTA_UPDATES true
#define ENABLE_LOCAL_STORAGE true

#endif // CONFIG_H