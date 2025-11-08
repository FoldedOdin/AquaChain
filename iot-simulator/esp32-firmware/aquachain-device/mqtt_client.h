/*
 * AquaChain MQTT Client Management
 * 
 * Handles secure MQTT connection to AWS IoT Core
 */

#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "config.h"
#include "certificates.h"

class MQTTManager {
private:
  PubSubClient& mqttClient;
  WiFiClientSecure& wifiClient;
  bool isConnected;
  unsigned long lastConnectionAttempt;
  int reconnectAttempts;
  
public:
  MQTTManager(PubSubClient& client, WiFiClientSecure& wifiSecureClient);
  
  // Initialization and connection
  bool begin();
  bool connect();
  bool reconnect();
  
  // Publishing functions
  bool publishData(String deviceId, String payload);
  bool publishStatus(String deviceId, String status);
  bool publishHeartbeat(String deviceId);
  bool publishDiagnostics(String deviceId, String diagnostics);
  
  // Subscription functions
  bool subscribeToCommands(String deviceId);
  bool subscribeToConfig(String deviceId);
  
  // Status functions
  bool isMQTTConnected();
  int getConnectionState();
  
  // Utility functions
  String getTopicPrefix(String deviceId);
  void handleMessage(char* topic, byte* payload, unsigned int length);
};

// Implementation

MQTTManager::MQTTManager(PubSubClient& client, WiFiClientSecure& wifiSecureClient) 
  : mqttClient(client), wifiClient(wifiSecureClient) {
  isConnected = false;
  lastConnectionAttempt = 0;
  reconnectAttempts = 0;
}

bool MQTTManager::begin() {
  Serial.println("Initializing MQTT client...");
  
  // Configure WiFiClientSecure with certificates
  wifiClient.setCACert(aws_root_ca);
  wifiClient.setCertificate(aws_device_cert);
  wifiClient.setPrivateKey(aws_device_private_key);
  
  // Configure MQTT client
  mqttClient.setServer(AWS_IOT_ENDPOINT, AWS_IOT_PORT);
  mqttClient.setKeepAlive(60);
  mqttClient.setSocketTimeout(30);
  
  // Set buffer size for larger messages
  mqttClient.setBufferSize(2048);
  
  Serial.printf("MQTT server: %s:%d\n", AWS_IOT_ENDPOINT, AWS_IOT_PORT);
  
  return true;
}

bool MQTTManager::connect() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, cannot connect to MQTT");
    return false;
  }
  
  if (millis() - lastConnectionAttempt < 5000) {
    return false; // Don't attempt too frequently
  }
  
  lastConnectionAttempt = millis();
  
  Serial.printf("Connecting to AWS IoT Core as %s...\n", DEVICE_ID);
  
  // Generate unique client ID
  String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);
  
  if (mqttClient.connect(clientId.c_str())) {
    Serial.println("✓ MQTT connected successfully");
    isConnected = true;
    reconnectAttempts = 0;
    
    // Subscribe to command topics
    subscribeToCommands(DEVICE_ID);
    subscribeToConfig(DEVICE_ID);
    
    return true;
  } else {
    Serial.printf("✗ MQTT connection failed, rc=%d\n", mqttClient.state());
    Serial.println("MQTT Error codes:");
    Serial.println("-2: MQTT_CONNECT_FAILED");
    Serial.println("-3: MQTT_CONNECTION_LOST");
    Serial.println("-4: MQTT_CONNECT_BAD_PROTOCOL");
    Serial.println("-5: MQTT_CONNECT_BAD_CLIENT_ID");
    Serial.println("-6: MQTT_CONNECT_UNAVAILABLE");
    Serial.println("-7: MQTT_CONNECT_BAD_CREDENTIALS");
    Serial.println("-8: MQTT_CONNECT_UNAUTHORIZED");
    
    isConnected = false;
    reconnectAttempts++;
    return false;
  }
}

bool MQTTManager::reconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    Serial.println("Max MQTT reconnection attempts reached");
    return false;
  }
  
  return connect();
}

bool MQTTManager::publishData(String deviceId, String payload) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/data";
  
  if (mqttClient.publish(topic.c_str(), payload.c_str())) {
    Serial.printf("✓ Published data to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to publish data to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::publishStatus(String deviceId, String status) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/status";
  
  if (mqttClient.publish(topic.c_str(), status.c_str())) {
    Serial.printf("✓ Published status to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to publish status to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::publishHeartbeat(String deviceId) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/heartbeat";
  String payload = "{\"type\":\"heartbeat\",\"timestamp\":" + String(millis()) + "}";
  
  if (mqttClient.publish(topic.c_str(), payload.c_str())) {
    Serial.printf("✓ Published heartbeat to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to publish heartbeat to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::publishDiagnostics(String deviceId, String diagnostics) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/diagnostics";
  
  if (mqttClient.publish(topic.c_str(), diagnostics.c_str())) {
    Serial.printf("✓ Published diagnostics to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to publish diagnostics to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::subscribeToCommands(String deviceId) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/commands";
  
  if (mqttClient.subscribe(topic.c_str())) {
    Serial.printf("✓ Subscribed to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to subscribe to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::subscribeToConfig(String deviceId) {
  if (!isConnected) {
    return false;
  }
  
  String topic = "aquachain/" + deviceId + "/config";
  
  if (mqttClient.subscribe(topic.c_str())) {
    Serial.printf("✓ Subscribed to %s\n", topic.c_str());
    return true;
  } else {
    Serial.printf("✗ Failed to subscribe to %s\n", topic.c_str());
    return false;
  }
}

bool MQTTManager::isMQTTConnected() {
  return mqttClient.connected();
}

int MQTTManager::getConnectionState() {
  return mqttClient.state();
}

String MQTTManager::getTopicPrefix(String deviceId) {
  return "aquachain/" + deviceId;
}

void MQTTManager::handleMessage(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("Received message on topic: %s\n", topic);
  Serial.printf("Message: %s\n", message.c_str());
  
  // Message handling is implemented in the main sketch
}

#endif // MQTT_CLIENT_H