# ESP32 to AWS IoT Core Setup Guide

This guide walks you through setting up ESP32 devices to connect to AWS IoT Core for the AquaChain water quality monitoring system.

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [AWS IoT Core Setup](#aws-iot-core-setup)
3. [ESP32 Firmware Setup](#esp32-firmware-setup)
4. [Device Provisioning](#device-provisioning)
5. [Testing Connection](#testing-connection)
6. [Troubleshooting](#troubleshooting)

## Hardware Requirements

### ESP32 Development Board
- **Recommended**: ESP32 DevKit V1 or ESP32-WROOM-32
- **Minimum**: 4MB Flash, 520KB RAM
- **WiFi**: 802.11 b/g/n support required

### Water Quality Sensors
```
Required Sensors:
├── pH Sensor (Analog)          → Pin A0
├── Turbidity Sensor (I2C)     → SDA: Pin 21, SCL: Pin 22
├── TDS Sensor (Analog)         → Pin A1
├── DHT22 (Temperature/Humidity) → Pin 4
└── GPS Module (Optional)       → RX: Pin 16, TX: Pin 17
```

### Additional Components
- **Power Supply**: 5V/2A adapter or battery pack
- **Breadboard/PCB**: For sensor connections
- **Resistors**: 10kΩ pull-up resistors for I2C
- **Capacitors**: 100µF for power filtering
- **Enclosure**: Waterproof case for outdoor deployment

## AWS IoT Core Setup

### Step 1: Create IoT Thing

```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure AWS credentials
aws configure

# Create IoT Thing
aws iot create-thing --thing-name "AquaChain-Device-001"

# Create IoT Thing Type (optional but recommended)
aws iot create-thing-type \
  --thing-type-name "AquaChainWaterSensor" \
  --thing-type-description "Water quality monitoring device"

# Associate thing with thing type
aws iot update-thing \
  --thing-name "AquaChain-Device-001" \
  --thing-type-name "AquaChainWaterSensor"
```

### Step 2: Generate Device Certificates

```bash
# Create certificate and keys
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile device-certificate.pem \
  --public-key-outfile device-public-key.pem \
  --private-key-outfile device-private-key.pem

# Note: Save the certificate ARN from the output
```

### Step 3: Create IoT Policy

Create policy file `aquachain-device-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": "arn:aws:iot:us-east-1:*:client/AquaChain-Device-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:*:topic/aquachain/+/data",
        "arn:aws:iot:us-east-1:*:topic/aquachain/+/status",
        "arn:aws:iot:us-east-1:*:topic/aquachain/+/diagnostics"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:*:topicfilter/aquachain/+/commands",
        "arn:aws:iot:us-east-1:*:topicfilter/aquachain/+/config"
      ]
    }
  ]
}
```

Apply the policy:
```bash
# Create the policy
aws iot create-policy \
  --policy-name "AquaChainDevicePolicy" \
  --policy-document file://aquachain-device-policy.json

# Attach policy to certificate (use ARN from step 2)
aws iot attach-policy \
  --policy-name "AquaChainDevicePolicy" \
  --target "arn:aws:iot:us-east-1:123456789012:cert/certificate-id"

# Attach certificate to thing
aws iot attach-thing-principal \
  --thing-name "AquaChain-Device-001" \
  --principal "arn:aws:iot:us-east-1:123456789012:cert/certificate-id"
```

### Step 4: Get IoT Endpoint

```bash
# Get your IoT endpoint
aws iot describe-endpoint --endpoint-type iot:Data-ATS

# Output example: a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com
```

## ESP32 Firmware Setup

### Step 1: Install Arduino IDE and Libraries

1. **Install Arduino IDE** (version 1.8.19 or later)
2. **Add ESP32 Board Support**:
   - File → Preferences
   - Add to Additional Board Manager URLs:
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install

3. **Install Required Libraries**:
   ```
   Library Manager (Ctrl+Shift+I):
   ├── WiFi (built-in)
   ├── ArduinoJson (by Benoit Blanchon)
   ├── PubSubClient (by Nick O'Leary)
   ├── DHT sensor library (by Adafruit)
   ├── OneWire (by Jim Studt)
   └── WiFiClientSecure (built-in)
   ```

### Step 2: Create Main Firmware File

Create `aquachain-device.ino`:

```cpp
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>

// Device Configuration
#define DEVICE_ID "AquaChain-Device-001"
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// AWS IoT Configuration
const char* AWS_IOT_ENDPOINT = "a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com";
const int AWS_IOT_PORT = 8883;

// Sensor Pin Definitions
#define PH_SENSOR_PIN A0
#define TDS_SENSOR_PIN A3
#define DHT_PIN 4
#define DHT_TYPE DHT22

// Sensor Objects
DHT dht(DHT_PIN, DHT_TYPE);

// WiFi and MQTT Clients
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

// Timing
unsigned long lastSensorReading = 0;
const unsigned long SENSOR_INTERVAL = 30000; // 30 seconds

// Device certificates (will be loaded from SPIFFS)
extern const char* device_certificate;
extern const char* device_private_key;
extern const char* root_ca;

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  dht.begin();
  Wire.begin();
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize MQTT
  setupMQTT();
  
  Serial.println("AquaChain Device Ready!");
}

void loop() {
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Read and publish sensor data
  if (millis() - lastSensorReading > SENSOR_INTERVAL) {
    readAndPublishSensorData();
    lastSensorReading = millis();
  }
  
  delay(1000);
}

void setupWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("WiFi connected! IP: ");
  Serial.println(WiFi.localIP());
}

void setupMQTT() {
  // Configure WiFiClientSecure
  wifiClient.setCACert(root_ca);
  wifiClient.setCertificate(device_certificate);
  wifiClient.setPrivateKey(device_private_key);
  
  // Configure MQTT client
  mqttClient.setServer(AWS_IOT_ENDPOINT, AWS_IOT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  // Connect to MQTT
  reconnectMQTT();
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (mqttClient.connect(DEVICE_ID)) {
      Serial.println("connected");
      
      // Subscribe to command topics
      String commandTopic = "aquachain/" + String(DEVICE_ID) + "/commands";
      mqttClient.subscribe(commandTopic.c_str());
      
      // Publish connection status
      publishStatus("online");
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("Received command: " + message);
  
  // Parse and handle commands
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  String command = doc["command"];
  if (command == "calibrate") {
    calibrateSensors();
  } else if (command == "restart") {
    ESP.restart();
  }
}

void readAndPublishSensorData() {
  // Read sensors
  float ph = readPHSensor();
  float turbidity = readTurbiditySensor();
  float tds = readTDSSensor();
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Check for sensor errors
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT sensor error!");
    return;
  }
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["deviceId"] = DEVICE_ID;
  doc["timestamp"] = getTimestamp();
  
  // Location (hardcoded for now, could use GPS)
  doc["location"]["latitude"] = 37.7749;
  doc["location"]["longitude"] = -122.4194;
  
  // Sensor readings
  doc["readings"]["pH"] = ph;
  doc["readings"]["turbidity"] = turbidity;
  doc["readings"]["tds"] = tds;
  doc["readings"]["temperature"] = temperature;
  doc["readings"]["humidity"] = humidity;
  
  // Calculate Water Quality Index (simplified)
  doc["wqi"] = calculateWQI(ph, turbidity, tds);
  
  // Diagnostics
  doc["diagnostics"]["batteryLevel"] = getBatteryLevel();
  doc["diagnostics"]["signalStrength"] = WiFi.RSSI();
  doc["diagnostics"]["sensorStatus"] = "operational";
  
  // Publish to AWS IoT
  String topic = "aquachain/" + String(DEVICE_ID) + "/data";
  String payload;
  serializeJson(doc, payload);
  
  if (mqttClient.publish(topic.c_str(), payload.c_str())) {
    Serial.println("Data published successfully");
  } else {
    Serial.println("Failed to publish data");
  }
}

float readPHSensor() {
  int rawValue = analogRead(PH_SENSOR_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to pH (calibration required)
  // This is a simplified conversion - real sensors need calibration
  float ph = 7.0 + ((2.5 - voltage) / 0.18);
  
  return constrain(ph, 0.0, 14.0);
}

float readTurbiditySensor() {
  // Simplified turbidity reading
  // Real implementation would use I2C sensor
  int rawValue = analogRead(A2);
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert to NTU (Nephelometric Turbidity Units)
  float turbidity = (voltage - 2.5) * 1000;
  
  return max(0.0f, turbidity);
}

float readTDSSensor() {
  int rawValue = analogRead(TDS_SENSOR_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to TDS (Total Dissolved Solids) in ppm
  float tds = (voltage * 1000) / 2.0;
  
  return max(0.0f, tds);
}

float calculateWQI(float ph, float turbidity, float tds) {
  // Simplified Water Quality Index calculation
  float phScore = (ph >= 6.5 && ph <= 8.5) ? 100 : 50;
  float turbidityScore = (turbidity < 5) ? 100 : (turbidity < 25) ? 75 : 25;
  float tdsScore = (tds < 500) ? 100 : (tds < 1000) ? 75 : 25;
  
  return (phScore + turbidityScore + tdsScore) / 3.0;
}

float getBatteryLevel() {
  // Read battery voltage (if connected to analog pin)
  // This is a placeholder - implement based on your power setup
  return 85.0; // Percentage
}

String getTimestamp() {
  // In production, sync with NTP server
  return String(millis());
}

void publishStatus(String status) {
  DynamicJsonDocument doc(256);
  doc["deviceId"] = DEVICE_ID;
  doc["status"] = status;
  doc["timestamp"] = getTimestamp();
  doc["firmwareVersion"] = "1.0.0";
  
  String topic = "aquachain/" + String(DEVICE_ID) + "/status";
  String payload;
  serializeJson(doc, payload);
  
  mqttClient.publish(topic.c_str(), payload.c_str());
}

void calibrateSensors() {
  Serial.println("Calibrating sensors...");
  // Implement sensor calibration routines
  publishStatus("calibrating");
  delay(5000); // Simulate calibration time
  publishStatus("online");
}
```

### Step 3: Add Certificate Files

Create `certificates.h`:

```cpp
#ifndef CERTIFICATES_H
#define CERTIFICATES_H

// Amazon Root CA 1
const char* root_ca = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIuJruydjsw2hUwsOBYy7n6Klf+z/qH8F4zTMITTMBmR
TqhFk0FhFLPgraGxVp+5iYaAoucbAurcxO0kn6+bW+2E4UXfQHI6A+1xzU52sMpT
1tJg6+6ATyQFLEFHmMP7DslHZfi7t8n8F5Z1kI4zI2FKsAHcEFbAD5lIGe7aHgSl
nDqBHJp7v9s0u3Slxs4T7ex2Ks2cHwNbuuTqNiHqYSK1dM0T+HdybqZSayaVNhqx
RGTBtb9HI79Oj/BqVqth1S9K
-----END CERTIFICATE-----
)EOF";

// Device Certificate (replace with your actual certificate)
const char* device_certificate = R"EOF(
-----BEGIN CERTIFICATE-----
[PASTE YOUR DEVICE CERTIFICATE HERE]
-----END CERTIFICATE-----
)EOF";

// Device Private Key (replace with your actual private key)
const char* device_private_key = R"EOF(
-----BEGIN RSA PRIVATE KEY-----
[PASTE YOUR DEVICE PRIVATE KEY HERE]
-----END RSA PRIVATE KEY-----
)EOF";

#endif
```

### Step 4: Upload Firmware

1. **Connect ESP32** to computer via USB
2. **Select Board**: Tools → Board → ESP32 Dev Module
3. **Select Port**: Tools → Port → (your ESP32 port)
4. **Configure Settings**:
   - Upload Speed: 921600
   - CPU Frequency: 240MHz
   - Flash Size: 4MB
   - Partition Scheme: Default 4MB with spiffs

5. **Upload**: Click Upload button or Ctrl+U

## Device Provisioning

### Automated Provisioning Script

Create `provision-device.py`:

```python
#!/usr/bin/env python3
"""
ESP32 Device Provisioning Script for AquaChain
"""

import boto3
import json
import sys
from pathlib import Path

def provision_device(device_id, region='us-east-1'):
    """Provision a new ESP32 device in AWS IoT Core"""
    
    iot_client = boto3.client('iot', region_name=region)
    
    try:
        # Create IoT Thing
        print(f"Creating IoT Thing: {device_id}")
        iot_client.create_thing(thingName=device_id)
        
        # Create certificate
        print("Creating device certificate...")
        cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
        
        certificate_arn = cert_response['certificateArn']
        certificate_pem = cert_response['certificatePem']
        private_key = cert_response['keyPair']['PrivateKey']
        
        # Save certificates to files
        cert_dir = Path('certificates')
        cert_dir.mkdir(exist_ok=True)
        
        with open(cert_dir / f'{device_id}-certificate.pem', 'w') as f:
            f.write(certificate_pem)
        
        with open(cert_dir / f'{device_id}-private-key.pem', 'w') as f:
            f.write(private_key)
        
        # Attach policy to certificate
        print("Attaching policy to certificate...")
        iot_client.attach_policy(
            policyName='AquaChainDevicePolicy',
            target=certificate_arn
        )
        
        # Attach certificate to thing
        print("Attaching certificate to thing...")
        iot_client.attach_thing_principal(
            thingName=device_id,
            principal=certificate_arn
        )
        
        # Get IoT endpoint
        endpoint_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
        iot_endpoint = endpoint_response['endpointAddress']
        
        # Generate Arduino header file
        generate_arduino_config(device_id, certificate_pem, private_key, iot_endpoint)
        
        print(f"✅ Device {device_id} provisioned successfully!")
        print(f"📁 Certificates saved to: certificates/")
        print(f"🔧 Arduino config generated: {device_id}_config.h")
        print(f"🌐 IoT Endpoint: {iot_endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error provisioning device: {e}")
        return False

def generate_arduino_config(device_id, certificate, private_key, endpoint):
    """Generate Arduino configuration header file"""
    
    config_content = f'''
#ifndef DEVICE_CONFIG_H
#define DEVICE_CONFIG_H

// Device Configuration
#define DEVICE_ID "{device_id}"
#define AWS_IOT_ENDPOINT "{endpoint}"

// WiFi Configuration (update these)
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Device Certificate
const char* device_certificate = R"EOF(
{certificate})EOF";

// Device Private Key
const char* device_private_key = R"EOF(
{private_key})EOF";

// Amazon Root CA 1
const char* root_ca = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIuJruydjsw2hUwsOBYy7n6Klf+z/qH8F4zTMITTMBmR
TqhFk0FhFLPgraGxVp+5iYaAoucbAurcxO0kn6+bW+2E4UXfQHI6A+1xzU52sMpT
1tJg6+6ATyQFLEFHmMP7DslHZfi7t8n8F5Z1kI4zI2FKsAHcEFbAD5lIGe7aHgSl
nDqBHJp7v9s0u3Slxs4T7ex2Ks2cHwNbuuTqNiHqYSK1dM0T+HdybqZSayaVNhqx
RGTBtb9HI79Oj/BqVqth1S9K
-----END CERTIFICATE-----
)EOF";

#endif
'''
    
    with open(f'{device_id}_config.h', 'w') as f:
        f.write(config_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python provision-device.py <device-id>")
        print("Example: python provision-device.py AquaChain-Device-001")
        sys.exit(1)
    
    device_id = sys.argv[1]
    provision_device(device_id)
```

### Usage:
```bash
# Install dependencies
pip install boto3

# Provision device
python provision-device.py AquaChain-Device-001

# This creates:
# - certificates/AquaChain-Device-001-certificate.pem
# - certificates/AquaChain-Device-001-private-key.pem  
# - AquaChain-Device-001_config.h (for Arduino)
```

## Testing Connection

### Step 1: Monitor MQTT Messages

```bash
# Subscribe to device topics
aws iot-data subscribe-to-topic \
  --topic-name "aquachain/AquaChain-Device-001/data" \
  --region us-east-1

# Or use MQTT client
mosquitto_sub -h a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com \
  -p 8883 \
  --cafile AmazonRootCA1.pem \
  --cert device-certificate.pem \
  --key device-private-key.pem \
  -t "aquachain/+/data"
```

### Step 2: Verify Data Flow

Expected MQTT message format:
```json
{
  "deviceId": "AquaChain-Device-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "readings": {
    "pH": 7.2,
    "turbidity": 2.1,
    "tds": 150.5,
    "temperature": 22.3,
    "humidity": 65.2
  },
  "wqi": 85.7,
  "diagnostics": {
    "batteryLevel": 87.5,
    "signalStrength": -45,
    "sensorStatus": "operational"
  }
}
```

## Troubleshooting

### Common Issues

#### 1. WiFi Connection Failed
```cpp
// Add to setup() for debugging
WiFi.onEvent([](WiFiEvent_t event) {
  Serial.printf("WiFi Event: %d\n", event);
});
```

#### 2. MQTT Connection Failed
- **Check certificates**: Ensure they're properly formatted
- **Verify policy**: Make sure device has publish/subscribe permissions
- **Check endpoint**: Verify IoT endpoint URL is correct

#### 3. Certificate Issues
```bash
# Validate certificate
openssl x509 -in device-certificate.pem -text -noout

# Check private key
openssl rsa -in device-private-key.pem -check
```

#### 4. Sensor Reading Errors
- **Check wiring**: Verify all connections
- **Power supply**: Ensure stable 3.3V/5V supply
- **Calibration**: Sensors may need calibration

### Debug Commands

```cpp
// Add to firmware for debugging
void printSystemInfo() {
  Serial.println("=== System Info ===");
  Serial.printf("Device ID: %s\n", DEVICE_ID);
  Serial.printf("WiFi Status: %d\n", WiFi.status());
  Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
  Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("Uptime: %lu ms\n", millis());
}
```

### AWS IoT Logs

Enable CloudWatch logging for AWS IoT:
```bash
# Enable logging
aws iot set-v2-logging-options \
  --role-arn "arn:aws:iam::123456789012:role/IoTLogsRole" \
  --default-log-level INFO

# View logs in CloudWatch
aws logs describe-log-groups --log-group-name-prefix "AWSIoT"
```

## Production Considerations

### Security Best Practices
- **Rotate certificates** regularly
- **Use secure boot** on ESP32
- **Encrypt flash storage**
- **Implement OTA updates** securely

### Power Management
- **Deep sleep** between readings
- **Battery monitoring** and low-power alerts
- **Solar charging** for remote deployments

### Reliability
- **Watchdog timers** for automatic recovery
- **Local data buffering** for offline periods
- **Redundant sensors** for critical measurements

### Scalability
- **Device fleet management** with AWS IoT Device Management
- **Bulk provisioning** for large deployments
- **Automated firmware updates** via AWS IoT Jobs

This guide provides everything needed to connect ESP32 devices to AWS IoT Core for the AquaChain system. The devices will seamlessly integrate with the existing Lambda functions and frontend dashboard.