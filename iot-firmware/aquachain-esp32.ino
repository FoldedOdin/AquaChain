/*
 AquaChain ESP32 Water Quality Monitor
 Sends sensor data with UNIX EPOCH timestamps
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <time.h>
#include "config.h"

#define TDS_PIN 32
#define TURBIDITY_PIN 33
#define PH_PIN 34
#define TEMP_PIN 27

WiFiClientSecure net;
PubSubClient client(net);

OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

const char* aws_endpoint = AWS_IOT_ENDPOINT;
const char* deviceId = DEVICE_ID;

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

String dataTopic = "aquachain/devices/" + String(deviceId) + "/data";
String telemetryTopic = "aquachain/devices/" + String(deviceId) + "/telemetry";

unsigned long lastPublish = 0;
const unsigned long publishInterval = 30000;

/* Calibration */
float PH_NEUTRAL_VOLTAGE = 2.5;
float PH_SLOPE = -5.7;
float TDS_CALIBRATION_FACTOR = 1.0;

/* NTP */
const char* ntpServer = "pool.ntp.org";

/* ---------- Utility Functions ---------- */

float readVoltage(int pin)
{
  const int samples = 25;
  float sum = 0;

  for (int i = 0; i < samples; i++)
  {
    sum += analogRead(pin);
    delay(2);
  }

  float avg = sum / samples;

  return avg * (3.3 / 4095.0);
}

long getEpochTime()
{
  time_t now;
  time(&now);
  return now;
}
String getISO8601Timestamp()
{
  time_t now;
  time(&now);

  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);

  char buffer[25];

  sprintf(buffer,
          "%04d-%02d-%02dT%02d:%02d:%02dZ",
          timeinfo.tm_year + 1900,
          timeinfo.tm_mon + 1,
          timeinfo.tm_mday,
          timeinfo.tm_hour,
          timeinfo.tm_min,
          timeinfo.tm_sec);

  return String(buffer);
}
/* ---------- Setup ---------- */

void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println("AquaChain ESP32 Starting...");
  Serial.println(deviceId);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  pinMode(PH_PIN, INPUT);
  pinMode(TURBIDITY_PIN, INPUT);
  pinMode(TDS_PIN, INPUT);

  sensors.begin();

  connectWiFi();

  /* Sync NTP time */
  configTime(0, 0, ntpServer);

  Serial.print("Syncing time");

  while (getEpochTime() < 100000)
  {
    Serial.print(".");
    delay(500);
  }

  Serial.println(" synced");

  net.setCACert(AWS_ROOT_CA);
  net.setCertificate(AWS_CERT);
  net.setPrivateKey(AWS_PRIVATE_KEY);

  client.setServer(aws_endpoint, 8883);
  client.setKeepAlive(60);
  client.setSocketTimeout(30);

  connectAWS();

  Serial.println("Calibrating pH...");
  delay(3000);

  PH_NEUTRAL_VOLTAGE = readVoltage(PH_PIN);
}

/* ---------- Loop ---------- */

void loop()
{
  if (!client.connected())
  {
    connectAWS();
  }

  client.loop();

  if (millis() - lastPublish >= publishInterval)
  {
    publishSensorData();
    publishTelemetry();
    lastPublish = millis();
  }
}

/* ---------- Connectivity ---------- */

void connectWiFi()
{
  Serial.print("Connecting WiFi ");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println(" connected");
}

void connectAWS()
{
  Serial.print("Connecting AWS IoT");

  while (!client.connected())
  {
    if (client.connect(deviceId))
    {
      Serial.println(" connected");
    }
    else
    {
      Serial.print(" failed rc=");
      Serial.print(client.state());
      Serial.println(" retrying");
      delay(2000);
    }
  }
}

/* ---------- Publishing ---------- */
void publishSensorData()
{
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);

  float ph = readPH();
  float turbidity = readTurbidity();
  float tds = readTDS(temperature);

  StaticJsonDocument<512> doc;

  doc["deviceId"] = deviceId;
  doc["timestamp"] = getISO8601Timestamp();

  /* Location */
  JsonObject location = doc.createNestedObject("location");
  location["latitude"] = 0.0;
  location["longitude"] = 0.0;

  /* Sensor readings */
  JsonObject readings = doc.createNestedObject("readings");
  readings["pH"] = ph;
  readings["turbidity"] = turbidity;
  readings["tds"] = tds;
  readings["temperature"] = temperature;

  /* Diagnostics */
  JsonObject diagnostics = doc.createNestedObject("diagnostics");
  diagnostics["batteryLevel"] = 100.0;
  diagnostics["signalStrength"] = WiFi.RSSI();
  diagnostics["sensorStatus"] = "normal";

  char buffer[512];

  serializeJson(doc, buffer);

  Serial.println(buffer);
  Serial.print("Publishing to: ");
  Serial.println(dataTopic);

  if (client.connected()) {
    bool published = client.publish(dataTopic.c_str(), buffer);
    
    if (published) {
      Serial.println("✓ Published successfully!");
    } else {
      Serial.println("✗ Publish FAILED!");
      Serial.print("MQTT State: ");
      Serial.println(client.state());
    }
  } else {
    Serial.println("✗ Not connected to MQTT broker!");
    Serial.print("MQTT State: ");
    Serial.println(client.state());
  }
}

void publishTelemetry()
{
  StaticJsonDocument<128> doc;

  doc["deviceId"] = deviceId;
  doc["status"] = "online";
  doc["signal"] = WiFi.RSSI();
  doc["heap"] = ESP.getFreeHeap();
  doc["timestamp"] = getEpochTime();

  char buffer[128];

  serializeJson(doc, buffer);

  client.publish(telemetryTopic.c_str(), buffer);
}

/* ---------- Sensor Reading ---------- */

float readPH()
{
  float voltage = readVoltage(PH_PIN);

  float ph = 7 + ((PH_NEUTRAL_VOLTAGE - voltage) * PH_SLOPE);

  ph = constrain(ph, 0, 14);

  return ph;
}

float readTurbidity()
{
  float voltage = readVoltage(TURBIDITY_PIN);

  float ntu = -1120.4 * voltage * voltage +
               5742.3 * voltage -
               4352.9;

  ntu = constrain(ntu, 0, 3000);

  return ntu;
}

float readTDS(float temperature)
{
  float voltage = readVoltage(TDS_PIN);

  float compensation = 1.0 + 0.02 * (temperature - 25.0);

  float compensatedVoltage = voltage / compensation;

  float tds = (133.42 * pow(compensatedVoltage, 3)
              -255.86 * pow(compensatedVoltage, 2)
              +857.39 * compensatedVoltage) * 0.5;

  tds = tds * TDS_CALIBRATION_FACTOR;

  if (tds < 0) tds = 0;

  return tds;
}