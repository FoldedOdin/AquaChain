# AquaChain ESP32 Firmware

Complete firmware for ESP32-based water quality monitoring device.

## Hardware Requirements

- ESP32-WROOM-32 development board
- pH sensor (analog output)
- Turbidity sensor (analog output)
- TDS sensor (analog output)
- Temperature sensor (analog output)
- Power supply (5V USB or battery)

## Software Requirements

- Arduino IDE 2.0+ or PlatformIO
- ESP32 board support package
- Required libraries:
  - WiFi (built-in)
  - WiFiClientSecure (built-in)
  - PubSubClient (install via Library Manager)
  - ArduinoJson (install via Library Manager)

## Installation

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
5. Search for "ESP32" and install

### 3. Install Required Libraries
1. Go to Sketch → Include Library → Manage Libraries
2. Install:
   - PubSubClient by Nick O'Leary
   - ArduinoJson by Benoit Blanchon

### 4. Configure Device

Edit `config.h` and replace:

```cpp
#define DEVICE_ID "ESP32-001"  // Unique device ID
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
```

### 5. Add AWS IoT Certificates

1. Go to AWS IoT Core Console
2. Create a new Thing (device)
3. Download certificates:
   - Device certificate
   - Private key
   - Root CA certificate
4. Paste certificate contents into `config.h`

### 6. Upload to ESP32

1. Connect ESP32 via USB
2. Select board: Tools → Board → ESP32 Dev Module
3. Select port: Tools → Port → (your COM port)
4. Click Upload button

## Wiring Diagram

```
ESP32 Pin    →    Sensor
---------         ------
GPIO 34      →    pH sensor output
GPIO 35      →    Turbidity sensor output
GPIO 32      →    TDS sensor output
GPIO 33      →    Temperature sensor output
3.3V         →    Sensor VCC
GND          →    Sensor GND
```

## Testing

### Serial Monitor
1. Open Tools → Serial Monitor
2. Set baud rate to 115200
3. You should see:
   ```
   AquaChain ESP32 Starting...
   Device ID: ESP32-001
   Connecting to WiFi: YourSSID
   WiFi connected!
   IP address: 192.168.1.100
   Connecting to AWS IoT Core...Connected!
   Publishing sensor data:
   {"deviceId":"ESP32-001","timestamp":"2024-01-01T00:01:00Z",...}
   Published successfully!
   ```

### AWS IoT Core Test
1. Go to AWS IoT Core Console
2. Click "Test" in left menu
3. Subscribe to topic: `aquachain/ESP32-001/data`
4. You should see messages every 60 seconds

## Troubleshooting

### WiFi Connection Failed
- Check SSID and password in config.h
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check WiFi signal strength

### AWS IoT Connection Failed
- Verify certificates are correctly pasted
- Check IoT endpoint URL
- Ensure IoT policy allows connect/publish
- Verify device is registered in IoT Core

### No Sensor Readings
- Check sensor wiring
- Verify sensor power supply (3.3V or 5V)
- Calibrate sensors using manufacturer instructions

## Calibration

Each sensor type requires calibration:

### pH Sensor
1. Use pH 7.0 buffer solution
2. Adjust offset in `readPH()` function
3. Use pH 4.0 and 10.0 for slope calibration

### Turbidity Sensor
1. Use distilled water (0 NTU)
2. Use formazin standards (100, 400, 800 NTU)
3. Adjust formula in `readTurbidity()`

### TDS Sensor
1. Use 0 ppm (distilled water)
2. Use calibration solution (1413 μS/cm)
3. Adjust formula in `readTDS()`

### Temperature Sensor
1. Use ice water (0°C)
2. Use boiling water (100°C)
3. Adjust formula in `readTemperature()`

## Data Format

### Sensor Data Topic
`aquachain/{deviceId}/data`

```json
{
  "deviceId": "ESP32-001",
  "timestamp": "2024-01-01T00:01:00Z",
  "readings": {
    "pH": 7.2,
    "turbidity": 3.5,
    "tds": 450,
    "temperature": 22.5
  },
  "location": {
    "latitude": 0.0,
    "longitude": 0.0
  },
  "diagnostics": {
    "batteryLevel": 100,
    "signalStrength": -45,
    "sensorStatus": "normal"
  }
}
```

### Telemetry Topic
`aquachain/{deviceId}/telemetry`

```json
{
  "deviceId": "ESP32-001",
  "timestamp": "2024-01-01T00:01:00Z",
  "status": "online",
  "batteryLevel": 100,
  "signalStrength": -45,
  "freeHeap": 200000,
  "uptime": 3600
}
```

## Power Consumption

- Active (WiFi + sensors): ~160mA @ 3.3V
- Deep sleep: ~10μA @ 3.3V
- Battery life (2000mAh): ~12 hours active, ~8 months sleep

## Security

- TLS 1.2 encryption for all MQTT communication
- Certificate-based device authentication
- No hardcoded credentials in firmware
- Secure boot (optional, requires ESP32 configuration)

## Support

For issues or questions:
1. Check AWS IoT Core logs
2. Check CloudWatch logs for Lambda errors
3. Review device serial output
4. Contact support team

## License

Copyright © 2026 AquaChain. All rights reserved.
