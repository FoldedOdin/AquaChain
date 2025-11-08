# 🌊 AquaChain IoT Data Specification

**What Data is Collected and How**

---

## 📊 Overview

AquaChain uses **ESP32-based IoT devices** with multiple sensors to monitor water quality in real-time. The system collects **5 key water quality parameters** every 30-60 seconds and sends them to AWS IoT Core for processing.

---

## 🔬 Sensor Data Collected

### Water Quality Sensors (Primary)

These sensors directly measure water quality:

### 1. **pH Level** (Acidity/Alkalinity)
- **What it measures:** Hydrogen ion concentration in water
- **Range:** 0-14 pH
- **Normal range:** 6.5-8.5 pH (drinking water)
- **Sensor:** Analog pH probe
- **Units:** pH units
- **Why it matters:** 
  - pH < 6.5: Acidic water (corrosive, can leach metals)
  - pH > 8.5: Alkaline water (bitter taste, scaling)
  - Sudden changes indicate contamination

**Example readings:**
```json
{
  "pH": 7.2,  // Neutral, safe for drinking
  "pH": 5.8,  // Acidic - ALERT!
  "pH": 9.1   // Alkaline - ALERT!
}
```

---

### 2. **Turbidity** (Water Clarity)
- **What it measures:** Cloudiness or haziness of water
- **Range:** 0-1000 NTU (Nephelometric Turbidity Units)
- **Normal range:** 0.5-5 NTU (drinking water)
- **Sensor:** Optical turbidity sensor
- **Units:** NTU
- **Why it matters:**
  - High turbidity = suspended particles (dirt, bacteria, chemicals)
  - Indicates contamination or sediment
  - Affects water appearance and safety

**Example readings:**
```json
{
  "turbidity": 1.5,   // Clear water
  "turbidity": 15.0,  // Cloudy - ALERT!
  "turbidity": 50.0   // Very cloudy - CRITICAL!
}
```

---

### 3. **TDS** (Total Dissolved Solids)
- **What it measures:** Concentration of dissolved minerals, salts, metals
- **Range:** 0-2000 ppm (parts per million)
- **Normal range:** 50-500 ppm (drinking water)
- **Sensor:** Conductivity-based TDS sensor
- **Units:** ppm or mg/L
- **Why it matters:**
  - Low TDS: Lacks minerals (flat taste)
  - High TDS: Too many dissolved substances (salty, health concerns)
  - Sudden spikes indicate contamination

**Example readings:**
```json
{
  "tds": 150,   // Good mineral content
  "tds": 800,   // High - ALERT!
  "tds": 1500   // Very high - CRITICAL!
}
```

---

### 4. **Temperature**
- **What it measures:** Water temperature
- **Range:** -55°C to 125°C (sensor range)
- **Normal range:** 15-35°C (ambient water)
- **Sensor:** DS18B20 digital temperature sensor
- **Units:** Celsius (°C)
- **Why it matters:**
  - Affects chemical reactions and bacterial growth
  - Sudden changes may indicate industrial discharge
  - Used for WQI calculations

**Example readings:**
```json
{
  "temperature": 22.5,  // Room temperature
  "temperature": 45.0,  // Hot - possible industrial discharge
  "temperature": 5.0    // Cold - unusual
}
```

---

---

## 📡 Data Transmission Format

### MQTT Payload Structure

Devices send data to AWS IoT Core via MQTT protocol:

```json
{
  "device_id": "DEV-DEMO-001",
  "timestamp": "2025-10-31T10:30:00Z",
  "readings": {
    "pH": 7.2,
    "turbidity": 1.5,
    "tds": 150,
    "temperature": 22.5
  },
  "diagnostics": {
    "batteryLevel": 85,
    "signalStrength": -45,
    "sensorStatus": "normal",
    "firmwareVersion": "1.0.0",
    "uptime": 86400
  },
  "location": {
    "latitude": 9.9312,
    "longitude": 76.2673,
    "address": "123 Main St, Kochi, Kerala"
  }
}
```

### MQTT Configuration
- **Protocol:** MQTT over TLS 1.3
- **Topic:** `aquachain/{deviceId}/data`
- **QoS:** 1 (at least once delivery)
- **Frequency:** Every 30-60 seconds
- **Authentication:** X.509 certificates

---

## 🎯 Sensor Profiles

Different deployment scenarios have different normal ranges:

### Residential Profile
```json
{
  "pH": {"min": 6.5, "max": 8.0, "normal": [6.8, 7.4]},
  "turbidity": {"min": 0.1, "max": 5.0, "normal": [0.5, 2.0]},
  "tds": {"min": 50, "max": 500, "normal": [120, 180]},
  "temperature": {"min": 15, "max": 35, "normal": [22, 26]}
}
```

### Community Profile (Wells, Public Taps)
```json
{
  "pH": {"min": 6.0, "max": 8.5, "normal": [6.5, 7.8]},
  "turbidity": {"min": 0.1, "max": 10.0, "normal": [1.0, 3.0]},
  "tds": {"min": 100, "max": 800, "normal": [150, 250]},
  "temperature": {"min": 18, "max": 32, "normal": [20, 28]}
}
```

### Industrial Profile
```json
{
  "pH": {"min": 5.5, "max": 9.0, "normal": [6.0, 8.0]},
  "turbidity": {"min": 0.5, "max": 20.0, "normal": [2.0, 5.0]},
  "tds": {"min": 200, "max": 1500, "normal": [300, 600]},
  "temperature": {"min": 15, "max": 40, "normal": [18, 30]}
}
```

---

## 🤖 Calculated Metrics

### Water Quality Index (WQI)
The system calculates a composite WQI score (0-100) from sensor readings:

```python
# Simplified WQI calculation
pH_score = 100 if 6.5 <= pH <= 8.5 else max(0, 100 - abs(pH - 7.0) * 20)
turbidity_score = max(0, 100 - turbidity * 10)
tds_score = max(0, 100 - max(0, tds - 500) / 10)

WQI = (pH_score + turbidity_score + tds_score) / 3
```

**WQI Interpretation:**
- **90-100:** Excellent water quality
- **70-89:** Good water quality
- **50-69:** Fair water quality
- **25-49:** Poor water quality
- **0-24:** Very poor water quality

### Anomaly Detection
ML model (XGBoost) analyzes readings to detect:
- **Contamination events** (sudden parameter changes)
- **Sensor faults** (impossible readings)
- **Gradual degradation** (trending issues)

**Model accuracy:** 99.74%

---

## 🔧 Hardware Specifications

### ESP32 Device
- **Microcontroller:** ESP32-WROOM-32
- **CPU:** Dual-core Xtensa LX6 @ 240 MHz
- **RAM:** 520 KB SRAM
- **Flash:** 4 MB
- **Connectivity:** Wi-Fi 802.11 b/g/n, Bluetooth 4.2
- **Power:** 3.3V, deep sleep mode < 10µA

### Sensor Connections
```
ESP32 Pin Mapping:
├── GPIO 34 (ADC1_CH6) → pH Sensor (Analog)
├── GPIO 35 (ADC1_CH7) → TDS Sensor (Analog)
├── GPIO 32 (ADC1_CH4) → Turbidity Sensor (Analog)
└── GPIO 4 (1-Wire)    → DS18B20 Temperature Sensor
```

---

## 📈 Data Processing Pipeline

### 1. Device → AWS IoT Core
```
ESP32 Device
  ↓ [MQTT over TLS 1.3]
AWS IoT Core
  ↓ [IoT Rule: SELECT * FROM 'aquachain/+/data']
```

### 2. Data Validation
```
Lambda: Data Validation
  ↓ [Validate schema, sanitize inputs]
  ↓ [Check sensor ranges]
  ↓ [Detect sensor faults]
```

### 3. Processing & Storage
```
Lambda: Data Processing
  ↓ [Calculate WQI]
  ↓ [ML anomaly detection]
  ↓ [User association]
DynamoDB: Readings Table
  ↓ [Store with partition key: user_id#device_id#month]
```

### 4. Real-Time Updates
```
DynamoDB Streams
  ↓ [Change events]
Lambda: Stream Processor
  ↓ [Identify connected clients]
WebSocket API
  ↓ [Push to frontend]
User Dashboard
  ↓ [Live updates every 30-60 seconds]
```

### 5. Alerting
```
Lambda: Alert Detection
  ↓ [Check thresholds]
  ↓ [Generate alerts]
SNS/SES
  ↓ [Send notifications]
User (Email/SMS/Push)
```

---

## 🎭 Simulation Scenarios

The IoT simulator can generate different scenarios for testing:

### 1. Normal Operation (85% probability)
```json
{
  "pH": 7.2,
  "turbidity": 1.5,
  "tds": 150,
  "temperature": 22.5
}
```

### 2. Contamination Event (10% probability)
```json
{
  "pH": 5.1,          // Acidic!
  "turbidity": 25.0,  // Very cloudy!
  "tds": 950,         // High dissolved solids!
  "temperature": 23.0
}
```

### 3. Sensor Fault (5% probability)
```json
{
  "pH": -999,         // Sensor error
  "turbidity": -999,  // Sensor error
  "tds": 150,
  "temperature": 22.5
}
```

---

## 📊 Data Storage

### DynamoDB Schema
```
Table: aquachain-table-readings-dev

Partition Key: deviceId_month (STRING)
  Format: "user_id#device_id#YYYY-MM"
  Example: "user-123#DEV-DEMO-001#2025-10"

Sort Key: timestamp (STRING)
  Format: ISO 8601
  Example: "2025-10-31T10:30:00Z"

Attributes:
  - device_id (STRING)
  - user_id (STRING)
  - readings (MAP)
    - pH (NUMBER)
    - turbidity (NUMBER)
    - tds (NUMBER)
    - temperature (NUMBER)
  - wqi (NUMBER)
  - anomaly_score (NUMBER)
  - alert_level (STRING): "normal" | "warning" | "critical"
  - location (MAP)
  - diagnostics (MAP)
  - ttl (NUMBER): Auto-delete after retention period
```

### Data Retention
- **Hot data (0-90 days):** DynamoDB
- **Warm data (90-365 days):** S3 Infrequent Access
- **Cold data (1-2 years):** S3 Glacier
- **Archive (2-7 years):** S3 Glacier Deep Archive
- **Compliance:** 7-year retention for audit logs

---

## 🔐 Data Security

### In Transit
- ✅ TLS 1.3 encryption (MQTT)
- ✅ X.509 certificate authentication
- ✅ Device-specific topics (isolation)

### At Rest
- ✅ KMS encryption (DynamoDB)
- ✅ KMS encryption (S3)
- ✅ Immutable audit ledger

### Access Control
- ✅ User-level data isolation (partition keys)
- ✅ IAM role-based access
- ✅ API Gateway authentication (Cognito)

---

## 📱 Frontend Display

### Dashboard Widgets
1. **Real-Time Gauge:** Current WQI score
2. **Parameter Cards:** Individual sensor readings
3. **Time-Series Charts:** Historical trends
4. **Alert Panel:** Active warnings/alerts
5. **Device Status:** Online/offline, battery, signal

### Example Dashboard View
```
┌─────────────────────────────────────────┐
│  Water Quality Index: 87 (Good)        │
│  ████████████████░░░░                   │
└─────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬────────┐
│ pH: 7.2  │ Turb: 1.5│ TDS: 150 │ Temp:  │
│ ✅ Normal│ ✅ Normal│ ✅ Normal│ 22.5°C │
└──────────┴──────────┴──────────┴────────┘

📊 Last 24 Hours
[Line chart showing pH, turbidity, TDS trends]

⚠️ Alerts (0 active)
No alerts at this time
```

---

## 🚀 Getting Started with IoT Data

### 1. Provision a Device
```bash
cd iot-simulator
python provision-device-multi-user.py provision \
  --device-id DEV-DEMO-001 \
  --user-id your-cognito-user-id \
  --region us-east-1
```

### 2. Run Simulator
```bash
python simulator.py --devices 3
```

### 3. View Data in Dashboard
```
http://localhost:3000/dashboard
```

### 4. Query Data via API
```bash
curl -H "Authorization: Bearer {JWT}" \
  https://api.aquachain.io/api/v1/readings/DEV-DEMO-001
```

---

## 📚 Additional Resources

- **ESP32 Setup Guide:** `iot-simulator/ESP32_IOT_SETUP_GUIDE.md`
- **Sensor Calibration:** `iot-simulator/esp32-firmware/aquachain-device/sensors.h`
- **API Documentation:** `PROJECT_REPORT.md` (Section 4.3)
- **ML Model Details:** `PROJECT_REPORT.md` (Section 5)

---

## 💡 Key Takeaways

**What IoT Data is Used:**

**Water Quality Sensors:**
1. ✅ **pH** - Water acidity/alkalinity
2. ✅ **Turbidity** - Water clarity
3. ✅ **TDS** - Dissolved solids
4. ✅ **Temperature** - Water temperature

**Why This Data:**
- Comprehensive water quality assessment
- Real-time contamination detection
- Regulatory compliance (WHO/EPA standards)
- Predictive maintenance
- Historical trend analysis

**How It's Used:**
- Calculate Water Quality Index (WQI)
- ML-based anomaly detection
- Real-time alerting
- Compliance reporting
- User dashboards

---

**Last Updated:** October 31, 2025  
**Version:** 1.0
