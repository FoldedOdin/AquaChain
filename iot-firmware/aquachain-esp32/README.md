# AquaChain ESP32 Firmware

## ⚠️ SECURITY FIRST - READ THIS BEFORE STARTING

This firmware uses a **secrets.h** file for credentials that is **NOT committed to git**. This prevents accidental credential leaks.

### Quick Security Setup

```bash
# 1. Copy the template
cd iot-firmware/aquachain-esp32/aquachain-esp32-improved/
cp secrets.h.template secrets.h

# 2. Edit secrets.h with your actual credentials
# (Use your favorite text editor)

# 3. Verify secrets.h is in .gitignore
git status  # Should NOT show secrets.h
```

## Hardware Requirements

- ESP32-WROOM-32 development board
- pH sensor (analog output, GPIO 35)
- Turbidity sensor (analog output, GPIO 34)
- TDS sensor (analog output, GPIO 34)
- Temperature sensor (analog output, GPIO 32)
- LED indicator (GPIO 2, built-in)
- Power supply (5V USB or battery)

## Software Requirements

- Arduino IDE 2.0+ or PlatformIO
- ESP32 board support package (v2.0.14+)
- Required libraries:
  - WiFi (built-in)
  - WiFiClientSecure (built-in)
  - PubSubClient 2.8.0+ (install via Library Manager)
  - ArduinoJson 6.21.0+ (install via Library Manager)

## Installation Steps

### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

### 2. Add ESP32 Board Support
1. Open Arduino IDE
2. Go to File → Preferences
3. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to Tools → Board → Boards Manager
5. Search for "ESP32" and install version 2.0.14+

### 3. Install Required Libraries
1. Go to Sketch → Include Library → Manage Libraries
2. Install:
   - **PubSubClient** by Nick O'Leary (v2.8.0+)
   - **ArduinoJson** by Benoit Blanchon (v6.21.0+)

### 4. Get AWS IoT Certificates

**Option A: Using AWS Console**
1. Go to AWS IoT Core Console
2. Navigate to: Manage → Things → Create Thing
3. Create a new Thing (e.g., "AquaChain-Device-001")
4. Download certificates:
   - Device certificate (xxx-certificate.pem.crt)
   - Private key (xxx-private.pem.key)
   - Root CA certificate (AmazonRootCA1.pem)

**Option B: Using AWS CLI**
```bash
# Create certificates
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile device.crt \
  --public-key-outfile device.public.key \
  --private-key-outfile device.private.key

# Get IoT endpoint
aws iot describe-endpoint --endpoint-type iot:Data-ATS
```

### 5. Configure secrets.h

```bash
# Copy template
cp secrets.h.template secrets.h

# Edit secrets.h with your credentials
nano secrets.h  # or use any text editor
```

Fill in:
- `WIFI_SSID` - Your WiFi network name
- `WIFI_PASSWORD` - Your WiFi password
- `AWS_IOT_ENDPOINT` - Your AWS IoT endpoint (from step 4)
- `THING_NAME` - Your device name (e.g., "AquaChain-Device-001")
- `AWS_CERT_CA` - Root CA certificate content
- `AWS_CERT_CRT` - Device certificate content
- `AWS_CERT_PRIVATE` - Private key content

**Important:** Copy the ENTIRE certificate including the BEGIN/END lines!

### 6. Upload to ESP32

1. Connect ESP32 via USB
2. Select board: **Tools → Board → ESP32 Dev Module**
3. Select port: **Tools → Port → (your COM port)**
4. Set upload speed: **Tools → Upload Speed → 115200**
5. Click **Upload** button (→)

## Wiring Diagram

```
ESP32 Pin    →    Sensor/Component
---------         ----------------
GPIO 34      →    TDS sensor output
GPIO 35      →    pH sensor output
GPIO 32      →    Temperature sensor output
GPIO 2       →    LED indicator (built-in)
3.3V         →    Sensor VCC
GND          →    Sensor GND
```

## Testing

### 1. Serial Monitor
1. Open **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. Press **EN** button on ESP32 to restart

Expected output:
```
=== AquaChain ESP32 Starting ===
Firmware Version: 2.0 (Improved)
Connecting to WiFi: YourSSID
.....
WiFi connected!
IP Address: 192.168.1.100
Signal Strength: -45 dBm
Attempting MQTT connection to: xxxxx.iot.ap-south-1.amazonaws.com
Thing Name: AquaChain-Device-001
MQTT connected!
Subscribed to command topic
Publishing telemetry: {"device_id":"AquaChain-Device-001",...}
Telemetry published successfully
```

### 2. AWS IoT Core Test
1. Go to **AWS IoT Core Console**
2. Click **MQTT test client** in left menu
3. Subscribe to topic: `aquachain/device/telemetry`
4. You should see messages every 30 seconds

### 3. LED Indicator
- **Solid ON**: Connected to WiFi and MQTT
- **Blinking (2 fast)**: Publishing telemetry successfully
- **Blinking (5 fast)**: Publish failed
- **OFF**: Disconnected

## Troubleshooting

### WiFi Connection Failed
```
Symptoms: "WiFi connection failed! Restarting..."
Solutions:
- Verify WIFI_SSID and WIFI_PASSWORD in secrets.h
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check WiFi signal strength (move closer to router)
- Verify WiFi allows new device connections
```

### MQTT Connection Failed

**Error: MQTT_CONNECT_BAD_CREDENTIALS (rc=4)**
```
Solutions:
- Verify certificates are correctly pasted in secrets.h
- Check for extra spaces or line breaks in certificates
- Ensure certificates include BEGIN/END lines
- Verify certificate is active in AWS IoT Core
```

**Error: MQTT_CONNECT_UNAUTHORIZED (rc=5)**
```
Solutions:
- Check IoT policy allows connect/publish/subscribe
- Verify Thing name matches THING_NAME in secrets.h
- Ensure certificate is attached to Thing
- Run: scripts/diagnostics/check-iot-thing-config.py
```

**Error: MQTT_CONNECTION_TIMEOUT (rc=-4)**
```
Solutions:
- Verify AWS_IOT_ENDPOINT is correct
- Check internet connectivity
- Ensure port 8883 is not blocked by firewall
- Try different WiFi network
```

### No Sensor Readings
```
Symptoms: Readings show 0 or unrealistic values
Solutions:
- Check sensor wiring (VCC, GND, Signal)
- Verify sensor power supply (3.3V or 5V per sensor spec)
- Test sensors individually with multimeter
- Calibrate sensors (see Calibration section)
```

### Device Keeps Restarting
```
Symptoms: "Max reconnect attempts reached. Restarting..."
Solutions:
- Check all connection issues above
- Increase MAX_RECONNECT_ATTEMPTS in firmware
- Verify power supply is stable (use USB power, not battery)
- Check serial monitor for specific error codes
```

## Calibration

### pH Sensor Calibration
```cpp
// In firmware, adjust phCalibration value
// Default: 1.0
// If reading 7.0 shows as 6.5, set to: 7.0/6.5 = 1.077
```

1. Use pH 7.0 buffer solution
2. Note the reading
3. Calculate: `phCalibration = 7.0 / reading`
4. Send calibration command via MQTT (see Commands section)

### TDS Sensor Calibration
```cpp
// In firmware, adjust tdsCalibration value
// Default: 1.0
// If 1413 μS/cm solution shows as 1300, set to: 1413/1300 = 1.087
```

1. Use 1413 μS/cm calibration solution
2. Note the reading
3. Calculate: `tdsCalibration = 1413 / reading`

### Temperature Sensor Calibration
```cpp
// In firmware, adjust tempOffset value
// Default: 0.0
// If reading 25°C shows as 27°C, set to: -2.0
```

1. Use calibrated thermometer
2. Note the difference
3. Set: `tempOffset = actual - reading`

## MQTT Topics

### Device Publishes To:
- `aquachain/device/telemetry` - Sensor readings (every 30s)
- `aquachain/device/status` - Device status (on connect/disconnect)

### Device Subscribes To:
- `aquachain/device/command` - Remote commands

## Commands

Send commands via AWS IoT Core MQTT test client:

### Restart Device
```json
{
  "command": "restart"
}
```

### Update Calibration
```json
{
  "command": "calibrate",
  "tds_cal": 1.087,
  "ph_cal": 1.077,
  "temp_offset": -2.0
}
```

## Data Format

### Telemetry Message
```json
{
  "device_id": "AquaChain-Device-001",
  "timestamp": 123456789,
  "tds": 450.5,
  "ph": 7.2,
  "temperature": 22.5,
  "wifi_rssi": -45
}
```

### Status Message
```json
{
  "device_id": "AquaChain-Device-001",
  "status": "online",
  "uptime": 3600,
  "free_heap": 200000
}
```

## Power Consumption

- **Active (WiFi + MQTT)**: ~160mA @ 3.3V
- **Deep sleep**: ~10μA @ 3.3V (not implemented in v2.0)
- **Battery life (2000mAh)**: ~12 hours continuous operation

## Security Features

✅ **TLS 1.2 encryption** for all MQTT communication
✅ **Certificate-based authentication** (no passwords over network)
✅ **No hardcoded credentials** (uses secrets.h, not committed to git)
✅ **Secure credential storage** (secrets.h in .gitignore)
✅ **Connection retry with backoff** (prevents brute force)
✅ **Automatic restart** after max failures (prevents stuck state)

## Firmware Updates (OTA)

Over-the-air updates are planned for v3.0. Current version requires USB upload.

## Diagnostic Scripts

Run these scripts to verify your setup:

```bash
# Check Thing configuration
python scripts/diagnostics/check-iot-thing-config.py --thing-name AquaChain-Device-001

# Verify certificates
python scripts/diagnostics/verify-thing-certificates.py --thing-name AquaChain-Device-001

# Pre-upload checklist
python scripts/diagnostics/pre-upload-checklist.py
```

## Support

### Documentation
- [IoT Quick Start Guide](../../DOCS/iot/QUICK-START-UPLOAD-FIRMWARE.md)
- [Connection Troubleshooting](../../DOCS/iot/COMPLETE-CONNECTION-FIX-SUMMARY.md)
- [MQTT Error Codes](../../DOCS/iot/MQTT-ERROR-CODES.md)

### Scripts
- `scripts/diagnostics/` - Diagnostic tools
- `scripts/monitoring/` - Health monitoring
- `scripts/deployment/` - Deployment helpers

### Getting Help
1. Check serial monitor output for error codes
2. Run diagnostic scripts
3. Review AWS IoT Core logs
4. Check CloudWatch logs for Lambda errors
5. Consult documentation in DOCS/iot/

## Version History

- **v2.0 (Improved)** - Security hardening, secrets.h, better error handling
- **v1.0** - Initial release

## License

Copyright © 2026 AquaChain. All rights reserved.
