/*
 * AquaChain ESP32 Water Quality Monitor
 * 
 * This firmware connects ESP32 devices to AWS IoT Core for real-time
 * water quality monitoring. It reads multiple sensors and publishes
 * data using the same MQTT protocol as the Python simulator.
 * 
 * Hardware Requirements:
 * - ESP32 DevKit V1 or compatible
 * - pH sensor (analog)
 * - Turbidity sensor (I2C or analog)
 * - TDS sensor (analog)
 * - DHT22 temperature/humidity sensor
 * - Optional: GPS module
 * 
 * Author: AquaChain Team
 * Version: 1.0.0
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <EEPROM.h>
#include <esp_system.h>
#include <esp_wifi.h>

// Include device-specific configuration
#include "config.h"
#include "sensors.h"
#include "wifi_manager.h"
#include "mqtt_client.h"
#include "ota_update.h"

// Global objects
DHT dht(DHT_PIN, DHT_TYPE);
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);
WiFiManager wifiManager;
MQTTManager mqttManager(mqttClient, wifiClient);
SensorManager sensorManager;
OTAUpdateHandler otaHandler;

// Timing variables
unsigned long lastSensorReading = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastWiFiCheck = 0;
unsigned long bootTime = 0;

// Device state
bool deviceOnline = false;
int reconnectAttempts = 0;
String deviceStatus = "initializing";

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println();
  Serial.println("========================================");
  Serial.println("    AquaChain Water Quality Monitor    ");
  Serial.println("           ESP32 Firmware v1.0         ");
  Serial.println("========================================");
  
  bootTime = millis();
  
  // Initialize EEPROM for configuration storage
  EEPROM.begin(512);
  
  // Initialize sensors
  Serial.println("Initializing sensors...");
  sensorManager.begin();
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  
  // Initialize WiFi
  Serial.println("Initializing WiFi...");
  wifiManager.begin();
  
  // Initialize MQTT
  Serial.println("Initializing MQTT...");
  mqttManager.begin();
  
  // Initialize OTA handler
  Serial.println("Initializing OTA handler...");
  otaHandler.begin(FIRMWARE_VERSION);
  otaHandler.validateFirmware();  // Validate firmware after boot
  
  // Set up watchdog timer
  esp_task_wdt_init(WDT_TIMEOUT, true);
  esp_task_wdt_add(NULL);
  
  Serial.println("Device initialization complete!");
  Serial.printf("Device ID: %s\n", DEVICE_ID);
  Serial.printf("Firmware Version: %s\n", FIRMWARE_VERSION);
  
  deviceStatus = "online";
  publishDeviceStatus();
}

void loop() {
  // Reset watchdog timer
  esp_task_wdt_reset();
  
  // Check WiFi connection
  if (millis() - lastWiFiCheck > WIFI_CHECK_INTERVAL) {
    checkWiFiConnection();
    lastWiFiCheck = millis();
  }
  
  // Maintain MQTT connection
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      reconnectMQTT();
    } else {
      mqttClient.loop();
      deviceOnline = true;
      reconnectAttempts = 0;
    }
  } else {
    deviceOnline = false;
  }
  
  // Read and publish sensor data
  if (millis() - lastSensorReading > SENSOR_READING_INTERVAL) {
    if (deviceOnline) {
      readAndPublishSensorData();
    } else {
      // Store data locally when offline
      storeSensorDataLocally();
    }
    lastSensorReading = millis();
  }
  
  // Send heartbeat
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    if (deviceOnline) {
      publishHeartbeat();
    }
    lastHeartbeat = millis();
  }
  
  // Handle low power mode
  if (ENABLE_POWER_SAVING) {
    enterLightSleep();
  } else {
    delay(1000);
  }
}

void checkWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, attempting reconnection...");
    deviceStatus = "reconnecting";
    wifiManager.reconnect();
  }
}

void reconnectMQTT() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    Serial.println("Max reconnection attempts reached, restarting device...");
    ESP.restart();
  }
  
  Serial.printf("Attempting MQTT connection (attempt %d/%d)...", 
                reconnectAttempts + 1, MAX_RECONNECT_ATTEMPTS);
  
  if (mqttManager.connect()) {
    Serial.println("connected");
    reconnectAttempts = 0;
    deviceStatus = "online";
    publishDeviceStatus();
    
    // Subscribe to command topics
    subscribeToCommands();
    
    // Publish any stored offline data
    publishStoredData();
    
  } else {
    Serial.printf("failed, rc=%d retrying in %d seconds\n", 
                  mqttClient.state(), MQTT_RECONNECT_DELAY / 1000);
    reconnectAttempts++;
    delay(MQTT_RECONNECT_DELAY);
  }
}

void readAndPublishSensorData() {
  Serial.println("Reading sensors...");
  
  // Read all sensors
  SensorReadings readings = sensorManager.readAllSensors();
  
  // Read DHT22
  readings.temperature = dht.readTemperature();
  // Validate readings
  if (isnan(readings.temperature)) {
    Serial.println("DHT22 sensor error!");
    readings.temperature = -999;
    readings.humidity = -999;
  }
  
  // Calculate Water Quality Index
  float wqi = calculateWQI(readings);
  
  // Determine anomaly type
  String anomalyType = detectAnomalies(readings);
  
  // Create JSON payload
  DynamicJsonDocument doc(2048);
  doc["deviceId"] = DEVICE_ID;
  doc["timestamp"] = getISO8601Timestamp();
  
  // Location data
  JsonObject location = doc.createNestedObject("location");
  location["latitude"] = DEVICE_LATITUDE;
  location["longitude"] = DEVICE_LONGITUDE;
  
  // Sensor readings
  JsonObject sensorData = doc.createNestedObject("readings");
  sensorData["pH"] = readings.ph;
  sensorData["turbidity"] = readings.turbidity;
  sensorData["tds"] = readings.tds;
  sensorData["temperature"] = readings.temperature;
  // Water Quality Index
  doc["wqi"] = wqi;
  doc["anomalyType"] = anomalyType;
  
  // Diagnostics
  JsonObject diagnostics = doc.createNestedObject("diagnostics");
  diagnostics["batteryLevel"] = getBatteryLevel();
  diagnostics["signalStrength"] = WiFi.RSSI();
  diagnostics["sensorStatus"] = sensorManager.getStatus();
  diagnostics["uptime"] = millis() - bootTime;
  diagnostics["freeHeap"] = ESP.getFreeHeap();
  diagnostics["firmwareVersion"] = FIRMWARE_VERSION;
  
  // Publish to AWS IoT
  String topic = "aquachain/" + String(DEVICE_ID) + "/data";
  String payload;
  serializeJson(doc, payload);
  
  if (mqttClient.publish(topic.c_str(), payload.c_str())) {
    Serial.println("✓ Sensor data published successfully");
    Serial.printf("WQI: %.1f, pH: %.2f, Turbidity: %.2f NTU, TDS: %.1f ppm\n", 
                  wqi, readings.ph, readings.turbidity, readings.tds);
  } else {
    Serial.println("✗ Failed to publish sensor data");
  }
}

void storeSensorDataLocally() {
  // Store data in EEPROM or SPIFFS when offline
  Serial.println("Storing sensor data locally (offline mode)");
  // Implementation would depend on storage strategy
}

void publishStoredData() {
  // Publish any data stored while offline
  Serial.println("Publishing stored offline data...");
  // Implementation would retrieve and publish stored data
}

void publishDeviceStatus() {
  DynamicJsonDocument doc(512);
  doc["deviceId"] = DEVICE_ID;
  doc["status"] = deviceStatus;
  doc["timestamp"] = getISO8601Timestamp();
  doc["firmwareVersion"] = FIRMWARE_VERSION;
  doc["uptime"] = millis() - bootTime;
  doc["wifiRSSI"] = WiFi.RSSI();
  doc["freeHeap"] = ESP.getFreeHeap();
  
  String topic = "aquachain/" + String(DEVICE_ID) + "/status";
  String payload;
  serializeJson(doc, payload);
  
  mqttClient.publish(topic.c_str(), payload.c_str());
}

void publishHeartbeat() {
  DynamicJsonDocument doc(256);
  doc["deviceId"] = DEVICE_ID;
  doc["type"] = "heartbeat";
  doc["timestamp"] = getISO8601Timestamp();
  doc["uptime"] = millis() - bootTime;
  
  String topic = "aquachain/" + String(DEVICE_ID) + "/heartbeat";
  String payload;
  serializeJson(doc, payload);
  
  mqttClient.publish(topic.c_str(), payload.c_str());
}

void subscribeToCommands() {
  String commandTopic = "aquachain/" + String(DEVICE_ID) + "/commands";
  String configTopic = "aquachain/" + String(DEVICE_ID) + "/config";
  String jobTopic = "$aws/things/" + String(DEVICE_ID) + "/jobs/notify";
  
  mqttClient.subscribe(commandTopic.c_str());
  mqttClient.subscribe(configTopic.c_str());
  mqttClient.subscribe(jobTopic.c_str());
  
  Serial.println("Subscribed to command and job topics");
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("Received message on topic: %s\n", topic);
  Serial.printf("Message: %s\n", message.c_str());
  
  // Parse JSON command
  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.printf("JSON parsing failed: %s\n", error.c_str());
    return;
  }
  
  // Check if this is an IoT Job notification
  String topicStr = String(topic);
  if (topicStr.indexOf("/jobs/notify") >= 0) {
    handleJobNotification(doc);
    return;
  }
  
  // Handle regular commands
  String command = doc["command"];
  handleCommand(command, doc);
}

void handleJobNotification(DynamicJsonDocument& jobDoc) {
  Serial.println("Received IoT Job notification");
  
  if (!jobDoc.containsKey("jobs") || !jobDoc["jobs"].containsKey("IN_PROGRESS")) {
    Serial.println("No in-progress jobs");
    return;
  }
  
  JsonArray jobs = jobDoc["jobs"]["IN_PROGRESS"].as<JsonArray>();
  
  for (JsonObject job : jobs) {
    String jobId = job["jobId"];
    
    Serial.printf("Processing job: %s\n", jobId.c_str());
    
    // Get job document
    String jobTopic = "$aws/things/" + String(DEVICE_ID) + "/jobs/" + jobId + "/get";
    mqttClient.publish(jobTopic.c_str(), "{}");
    
    // Subscribe to job document response
    String responseTopic = "$aws/things/" + String(DEVICE_ID) + "/jobs/" + jobId + "/get/accepted";
    mqttClient.subscribe(responseTopic.c_str());
    
    // Wait for job document
    delay(1000);
    
    // Process job (this would be handled in a separate callback in production)
    // For now, we'll handle it inline
    if (job.containsKey("document")) {
      JsonObject document = job["document"];
      String operation = document["operation"];
      
      if (operation == "firmware_update" || operation == "firmware_rollback") {
        handleCommand(operation, document);
        
        // Update job status
        updateJobStatus(jobId, "SUCCEEDED");
      }
    }
  }
}

void updateJobStatus(String jobId, String status) {
  DynamicJsonDocument doc(256);
  doc["status"] = status;
  doc["statusDetails"] = {};
  
  String topic = "$aws/things/" + String(DEVICE_ID) + "/jobs/" + jobId + "/update";
  String payload;
  serializeJson(doc, payload);
  
  mqttClient.publish(topic.c_str(), payload.c_str());
  
  Serial.printf("Updated job %s status to: %s\n", jobId.c_str(), status.c_str());
}

void handleCommand(String command, DynamicJsonDocument& params) {
  Serial.printf("Executing command: %s\n", command.c_str());
  
  if (command == "calibrate") {
    calibrateSensors();
  } else if (command == "restart") {
    Serial.println("Restarting device...");
    delay(1000);
    ESP.restart();
  } else if (command == "update_config") {
    updateConfiguration(params);
  } else if (command == "get_diagnostics") {
    publishDiagnostics();
  } else if (command == "factory_reset") {
    factoryReset();
  } else if (command == "firmware_update") {
    handleFirmwareUpdate(params);
  } else if (command == "firmware_rollback") {
    handleFirmwareRollback();
  } else {
    Serial.printf("Unknown command: %s\n", command.c_str());
  }
}

void handleFirmwareUpdate(DynamicJsonDocument& params) {
  Serial.println("Processing firmware update request...");
  
  if (!params.containsKey("firmware_version") || 
      !params.containsKey("firmware_url") ||
      !params.containsKey("checksum")) {
    Serial.println("Missing required firmware update parameters");
    otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "failed", "Missing parameters");
    return;
  }
  
  String version = params["firmware_version"];
  String url = params["firmware_url"];
  String checksum = params["checksum"];
  int size = params["firmware_size"] | 0;
  
  // Report update started
  otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "in_progress");
  
  // Perform update
  bool success = otaHandler.performUpdate(url, checksum, size);
  
  if (success) {
    otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "success");
    // Device will reboot automatically
  } else {
    otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "failed", "Update failed");
  }
}

void handleFirmwareRollback() {
  Serial.println("Processing firmware rollback request...");
  
  otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "rollback_in_progress");
  
  bool success = otaHandler.rollbackToPrevious();
  
  if (!success) {
    otaHandler.reportUpdateStatus(mqttClient, DEVICE_ID, "rollback_failed", "No previous partition");
  }
  // If successful, device will reboot
}

void calibrateSensors() {
  Serial.println("Starting sensor calibration...");
  deviceStatus = "calibrating";
  publishDeviceStatus();
  
  sensorManager.calibrate();
  
  deviceStatus = "online";
  publishDeviceStatus();
  Serial.println("Sensor calibration complete");
}

void updateConfiguration(DynamicJsonDocument& config) {
  Serial.println("Updating device configuration...");
  
  if (config.containsKey("sensorInterval")) {
    // Update sensor reading interval
    int newInterval = config["sensorInterval"];
    if (newInterval >= 10000 && newInterval <= 300000) { // 10s to 5min
      // Save to EEPROM
      Serial.printf("Updated sensor interval to %d ms\n", newInterval);
    }
  }
  
  if (config.containsKey("powerSaving")) {
    bool enablePowerSaving = config["powerSaving"];
    // Update power saving mode
    Serial.printf("Power saving mode: %s\n", enablePowerSaving ? "enabled" : "disabled");
  }
}

void publishDiagnostics() {
  DynamicJsonDocument doc(1024);
  doc["deviceId"] = DEVICE_ID;
  doc["type"] = "diagnostics";
  doc["timestamp"] = getISO8601Timestamp();
  
  // System diagnostics
  JsonObject system = doc.createNestedObject("system");
  system["uptime"] = millis() - bootTime;
  system["freeHeap"] = ESP.getFreeHeap();
  system["cpuFreq"] = ESP.getCpuFreqMHz();
  system["flashSize"] = ESP.getFlashChipSize();
  system["firmwareVersion"] = FIRMWARE_VERSION;
  
  // WiFi diagnostics
  JsonObject wifi = doc.createNestedObject("wifi");
  wifi["ssid"] = WiFi.SSID();
  wifi["rssi"] = WiFi.RSSI();
  wifi["ip"] = WiFi.localIP().toString();
  wifi["mac"] = WiFi.macAddress();
  
  // Sensor diagnostics
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["status"] = sensorManager.getStatus();
  sensors["lastCalibration"] = sensorManager.getLastCalibrationTime();
  
  String topic = "aquachain/" + String(DEVICE_ID) + "/diagnostics";
  String payload;
  serializeJson(doc, payload);
  
  mqttClient.publish(topic.c_str(), payload.c_str());
}

void factoryReset() {
  Serial.println("Performing factory reset...");
  
  // Clear EEPROM
  for (int i = 0; i < 512; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
  
  // Reset WiFi settings
  WiFi.disconnect(true);
  
  Serial.println("Factory reset complete. Restarting...");
  delay(2000);
  ESP.restart();
}

float calculateWQI(SensorReadings& readings) {
  // Simplified Water Quality Index calculation
  float phScore = 0, turbidityScore = 0, tdsScore = 0;
  
  // pH scoring (optimal range: 6.5-8.5)
  if (readings.ph >= 6.5 && readings.ph <= 8.5) {
    phScore = 100;
  } else if (readings.ph >= 6.0 && readings.ph <= 9.0) {
    phScore = 75;
  } else if (readings.ph >= 5.5 && readings.ph <= 9.5) {
    phScore = 50;
  } else {
    phScore = 25;
  }
  
  // Turbidity scoring (lower is better)
  if (readings.turbidity < 1.0) {
    turbidityScore = 100;
  } else if (readings.turbidity < 5.0) {
    turbidityScore = 75;
  } else if (readings.turbidity < 25.0) {
    turbidityScore = 50;
  } else {
    turbidityScore = 25;
  }
  
  // TDS scoring (optimal range: 50-500 ppm)
  if (readings.tds >= 50 && readings.tds <= 500) {
    tdsScore = 100;
  } else if (readings.tds >= 30 && readings.tds <= 1000) {
    tdsScore = 75;
  } else if (readings.tds >= 10 && readings.tds <= 1500) {
    tdsScore = 50;
  } else {
    tdsScore = 25;
  }
  
  // Calculate weighted average
  return (phScore * 0.4 + turbidityScore * 0.3 + tdsScore * 0.3);
}

String detectAnomalies(SensorReadings& readings) {
  // Check for sensor faults
  if (readings.ph < 0 || readings.ph > 14 || 
      readings.turbidity < 0 || readings.tds < 0) {
    return "sensor_fault";
  }
  
  // Check for contamination indicators
  if (readings.ph < 5.0 || readings.ph > 10.0 || 
      readings.turbidity > 50.0 || readings.tds > 2000) {
    return "contamination";
  }
  
  return "normal";
}

float getBatteryLevel() {
  // Read battery voltage if connected
  #ifdef BATTERY_PIN
    int rawValue = analogRead(BATTERY_PIN);
    float voltage = rawValue * (3.3 / 4095.0) * BATTERY_VOLTAGE_DIVIDER;
    
    // Convert voltage to percentage (adjust based on battery type)
    float percentage = ((voltage - BATTERY_MIN_VOLTAGE) / 
                       (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)) * 100.0;
    
    return constrain(percentage, 0.0, 100.0);
  #else
    return 100.0; // No battery monitoring
  #endif
}

String getISO8601Timestamp() {
  // In production, sync with NTP server
  // For now, return milliseconds since boot
  unsigned long currentTime = millis();
  return String(currentTime);
}

void enterLightSleep() {
  // Enter light sleep to save power
  esp_sleep_enable_timer_wakeup(LIGHT_SLEEP_DURATION * 1000);
  esp_light_sleep_start();
}

// Set MQTT callback
void setupMQTTCallback() {
  mqttClient.setCallback(mqttCallback);
}