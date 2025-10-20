# ESP32 Firmware for AquaChain Devices

This directory contains the ESP32 firmware that implements the same interface as the simulator.

## Hardware Requirements

- ESP32 DevKit (or compatible)
- pH sensor (analog output)
- Turbidity sensor (I2C interface)
- TDS sensor (analog output)
- DHT22 temperature/humidity sensor
- GPS module (optional)
- Battery monitoring circuit

## Firmware Features

- **Same MQTT Protocol**: Uses identical topics and data format as simulator
- **Sensor Drivers**: pH, turbidity, TDS, temperature, humidity
- **WiFi Management**: Auto-reconnect and credential management
- **OTA Updates**: Secure firmware updates via AWS IoT Jobs
- **Certificate Management**: X.509 device certificates
- **Local Buffering**: SQLite for offline data storage
- **Watchdog Timer**: Automatic recovery from crashes

## Installation

1. Install Arduino IDE with ESP32 support
2. Install required libraries (see `libraries.txt`)
3. Configure WiFi credentials in `config.h`
4. Upload firmware to ESP32

## Configuration

```cpp
// config.h
#define WIFI_SSID "your-wifi-network"
#define WIFI_PASSWORD "your-wifi-password"
#define DEVICE_ID "DEV-001"  // Must match AWS IoT device registration
#define AWS_IOT_ENDPOINT "your-endpoint.iot.region.amazonaws.com"

// Sensor pin definitions
#define PH_SENSOR_PIN A0
#define TDS_SENSOR_PIN A1
#define TURBIDITY_SDA_PIN 21
#define TURBIDITY_SCL_PIN 22
#define DHT22_PIN 4
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
```

## Transitioning from Simulator

When you're ready to use real hardware:

1. Flash this firmware to your ESP32 devices
2. Stop the Python simulator
3. Real devices will automatically connect and start sending data
4. No changes needed to your AWS backend!

## Development Status

- [ ] Basic WiFi and MQTT connectivity
- [ ] pH sensor driver
- [ ] Turbidity sensor driver (I2C)
- [ ] TDS sensor driver
- [ ] DHT22 temperature/humidity driver
- [ ] GPS integration
- [ ] Local data buffering
- [ ] OTA update support
- [ ] Certificate provisioning
- [ ] Power management

## File Structure

```
esp32-firmware/
├── aquachain-device/
│   ├── aquachain-device.ino    # Main Arduino sketch
│   ├── config.h                # Configuration
│   ├── sensors.cpp             # Sensor drivers
│   ├── wifi_manager.cpp        # WiFi management
│   ├── mqtt_client.cpp         # MQTT communication
│   ├── data_buffer.cpp         # Local data storage
│   └── ota_updater.cpp         # OTA functionality
├── libraries.txt               # Required Arduino libraries
└── certificates/               # Device certificates (generated)
```

This firmware will implement the exact same `DeviceInterface` behavior as the Python simulator, ensuring seamless transition to real hardware.