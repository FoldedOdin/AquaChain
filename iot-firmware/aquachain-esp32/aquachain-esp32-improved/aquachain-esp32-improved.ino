/*
 AquaChain ESP32 Water Quality Monitor
 Improved version with better telemetry control
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

/* Publish intervals */
unsigned long lastDataPublish = 0;
unsigned long lastTelemetryPublish = 0;

const unsigned long DATA_INTERVAL = 30000;
const unsigned long TELEMETRY_INTERVAL = 120000;

/* Calibration */
float PH_NEUTRAL_VOLTAGE = 2.5;
float TURBIDITY_CLEAR_VOLTAGE = 2.8;
float TDS_CALIBRATION_FACTOR = 1.0;

/* NTP */
const char* ntpServer = "pool.ntp.org";

/* Message counter */
unsigned long messageCounter = 0;

/* ---------- Utility Functions ---------- */

float readVoltage(int pin)
{
  const int samples = 30;
  float sum = 0;

  for (int i = 0; i < samples; i++)
  {
    sum += analogRead(pin);
    delay(3);
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

  while (WiFi.localIP() == INADDR_NONE)
  {
    delay(100);
  }

  Serial.print("WiFi RSSI: ");
  Serial.println(WiFi.RSSI());

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
  client.setBufferSize(1024);

  connectAWS();

  Serial.println("Calibrating pH...");

  for (int i = 0; i < 30; i++)
  {
    client.loop();
    delay(100);
  }

  PH_NEUTRAL_VOLTAGE = readVoltage(PH_PIN);

  Serial.print("Neutral Voltage (pH 7): ");
  Serial.println(PH_NEUTRAL_VOLTAGE, 3);
}

/* ---------- Loop ---------- */

void loop()
{
  if (!client.connected())
  {
    static unsigned long lastReconnect = 0;

    if (millis() - lastReconnect > 5000)
    {
      connectAWS();
      lastReconnect = millis();
    }
  }

  client.loop();

  if (millis() - lastDataPublish >= DATA_INTERVAL)
  {
    publishSensorData();
    lastDataPublish = millis();
  }

  if (millis() - lastTelemetryPublish >= TELEMETRY_INTERVAL)
  {
    publishTelemetry();
    lastTelemetryPublish = millis();
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

      for (int i = 0; i < 10; i++)
      {
        client.loop();
        delay(100);
      }

      return;
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
  if (!client.connected())
  {
    Serial.println("Not connected, skipping publish");
    return;
  }

  messageCounter++;

  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);

  if (temperature == DEVICE_DISCONNECTED_C || temperature < -50)
  {
    Serial.println("Temperature sensor error");
    temperature = 25.0;
  }

  float ph = readPH();
  float turbidity = readTurbidity();
  float tds = readTDS(temperature);

  StaticJsonDocument<512> doc;

  doc["deviceId"] = deviceId;
  doc["messageId"] = messageCounter;
  doc["timestamp"] = getISO8601Timestamp();

  JsonObject location = doc.createNestedObject("location");
  location["latitude"] = 0.0;
  location["longitude"] = 0.0;

  JsonObject readings = doc.createNestedObject("readings");
  readings["pH"] = ph;
  readings["turbidity"] = turbidity;
  readings["tds"] = tds;
  readings["temperature"] = temperature;

  JsonObject diagnostics = doc.createNestedObject("diagnostics");
  diagnostics["batteryLevel"] = 100.0;
  diagnostics["signalStrength"] = WiFi.RSSI();
  diagnostics["sensorStatus"] = "normal";

  char buffer[512];

  serializeJson(doc, buffer);

  Serial.print("Publish #");
  Serial.println(messageCounter);

  Serial.println(buffer);

  client.publish(dataTopic.c_str(), buffer);
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

  float ph = 7 + ((PH_NEUTRAL_VOLTAGE - voltage) / 0.18);

  ph = constrain(ph, 0, 14);

  return ph;
}

float readTurbidity()
{
  float voltage = readVoltage(TURBIDITY_PIN);

  float turbidity = (TURBIDITY_CLEAR_VOLTAGE - voltage) * 200;

  if (turbidity < 0) turbidity = 0;

  return turbidity;
}

float readTDS(float temperature)
{
  float voltage = readVoltage(TDS_PIN);

  float tds = voltage * 500 * TDS_CALIBRATION_FACTOR;

  if (tds < 0) tds = 0;

  return tds;
}