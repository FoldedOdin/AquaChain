/*
 * AquaChain WiFi Management
 * 
 * Handles WiFi connection, reconnection, and configuration
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <EEPROM.h>
#include "config.h"

class WiFiManager {
private:
  int reconnectAttempts;
  unsigned long lastConnectionAttempt;
  bool isConnected;
  String savedSSID;
  String savedPassword;
  
public:
  WiFiManager();
  
  // Initialization and connection
  bool begin();
  bool connect();
  bool reconnect();
  
  // Status functions
  bool isWiFiConnected();
  int getSignalStrength();
  String getIPAddress();
  String getMACAddress();
  String getSSID();
  
  // Configuration
  void saveCredentials(String ssid, String password);
  void loadCredentials();
  void clearCredentials();
  
  // Event handlers
  void onConnected();
  void onDisconnected();
  void onGotIP();
};

// Implementation

WiFiManager::WiFiManager() {
  reconnectAttempts = 0;
  lastConnectionAttempt = 0;
  isConnected = false;
}

bool WiFiManager::begin() {
  Serial.println("Initializing WiFi...");
  
  // Load saved credentials
  loadCredentials();
  
  // Set WiFi mode
  WiFi.mode(WIFI_STA);
  
  // Set up event handlers
  WiFi.onEvent([this](WiFiEvent_t event, WiFiEventInfo_t info) {
    switch (event) {
      case ARDUINO_EVENT_WIFI_STA_CONNECTED:
        Serial.println("WiFi connected");
        this->onConnected();
        break;
        
      case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
        Serial.println("WiFi disconnected");
        this->onDisconnected();
        break;
        
      case ARDUINO_EVENT_WIFI_STA_GOT_IP:
        Serial.printf("Got IP address: %s\n", WiFi.localIP().toString().c_str());
        this->onGotIP();
        break;
        
      default:
        break;
    }
  });
  
  // Attempt initial connection
  return connect();
}

bool WiFiManager::connect() {
  if (savedSSID.length() == 0) {
    Serial.println("No WiFi credentials saved, using default");
    savedSSID = WIFI_SSID;
    savedPassword = WIFI_PASSWORD;
  }
  
  Serial.printf("Connecting to WiFi: %s\n", savedSSID.c_str());
  
  WiFi.begin(savedSSID.c_str(), savedPassword.c_str());
  
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_TIMEOUT) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.printf("✓ WiFi connected successfully\n");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Signal Strength: %d dBm\n", WiFi.RSSI());
    
    isConnected = true;
    reconnectAttempts = 0;
    return true;
  } else {
    Serial.println();
    Serial.println("✗ WiFi connection failed");
    isConnected = false;
    reconnectAttempts++;
    return false;
  }
}

bool WiFiManager::reconnect() {
  if (reconnectAttempts >= MAX_WIFI_RECONNECT_ATTEMPTS) {
    Serial.println("Max WiFi reconnection attempts reached");
    return false;
  }
  
  if (millis() - lastConnectionAttempt < 10000) {
    return false; // Don't attempt too frequently
  }
  
  lastConnectionAttempt = millis();
  
  Serial.printf("WiFi reconnection attempt %d/%d\n", 
                reconnectAttempts + 1, MAX_WIFI_RECONNECT_ATTEMPTS);
  
  WiFi.disconnect();
  delay(1000);
  
  return connect();
}

bool WiFiManager::isWiFiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

int WiFiManager::getSignalStrength() {
  return WiFi.RSSI();
}

String WiFiManager::getIPAddress() {
  return WiFi.localIP().toString();
}

String WiFiManager::getMACAddress() {
  return WiFi.macAddress();
}

String WiFiManager::getSSID() {
  return WiFi.SSID();
}

void WiFiManager::saveCredentials(String ssid, String password) {
  // Save to EEPROM (starting at address 100 to avoid sensor calibration data)
  int addr = 100;
  
  // Save SSID length and SSID
  EEPROM.write(addr++, ssid.length());
  for (int i = 0; i < ssid.length(); i++) {
    EEPROM.write(addr++, ssid[i]);
  }
  
  // Save password length and password
  EEPROM.write(addr++, password.length());
  for (int i = 0; i < password.length(); i++) {
    EEPROM.write(addr++, password[i]);
  }
  
  EEPROM.commit();
  
  savedSSID = ssid;
  savedPassword = password;
  
  Serial.println("WiFi credentials saved");
}

void WiFiManager::loadCredentials() {
  int addr = 100;
  
  // Load SSID
  int ssidLength = EEPROM.read(addr++);
  if (ssidLength > 0 && ssidLength < 32) {
    savedSSID = "";
    for (int i = 0; i < ssidLength; i++) {
      savedSSID += char(EEPROM.read(addr++));
    }
  }
  
  // Load password
  int passwordLength = EEPROM.read(addr++);
  if (passwordLength > 0 && passwordLength < 64) {
    savedPassword = "";
    for (int i = 0; i < passwordLength; i++) {
      savedPassword += char(EEPROM.read(addr++));
    }
  }
  
  if (savedSSID.length() > 0) {
    Serial.printf("Loaded WiFi credentials for: %s\n", savedSSID.c_str());
  }
}

void WiFiManager::clearCredentials() {
  // Clear EEPROM WiFi section
  for (int i = 100; i < 200; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
  
  savedSSID = "";
  savedPassword = "";
  
  Serial.println("WiFi credentials cleared");
}

void WiFiManager::onConnected() {
  isConnected = true;
  reconnectAttempts = 0;
}

void WiFiManager::onDisconnected() {
  isConnected = false;
}

void WiFiManager::onGotIP() {
  isConnected = true;
  
  // Save successful credentials
  if (savedSSID.length() > 0 && savedPassword.length() > 0) {
    saveCredentials(savedSSID, savedPassword);
  }
}

#endif // WIFI_MANAGER_H