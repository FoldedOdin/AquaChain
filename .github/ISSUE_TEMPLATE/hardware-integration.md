---
name: Hardware Integration
about: Track hardware integration tasks for real ESP32 devices
title: '[HARDWARE] Implement real sensor reading and diagnostics for ESP32 devices'
labels: enhancement, hardware, iot, P3
assignees: ''
---

## Description

Currently, the IoT simulator uses simulated sensor data. For production deployment with physical devices, we need to implement real hardware integration for ESP32 devices.

## Background

The codebase includes placeholder implementations in `iot-simulator/src/real_device.py` with TODO comments indicating where real hardware code should be integrated.

## Tasks

### 1. Real Sensor Reading Implementation

Implement actual sensor reading code for ESP32 hardware:

- [ ] pH sensor reading via analog input with calibration
- [ ] Turbidity sensor reading via I2C interface
- [ ] TDS (Total Dissolved Solids) sensor via analog input
- [ ] Temperature/humidity sensor (DHT22 or similar)
- [ ] Sensor calibration procedures
- [ ] Error handling for sensor failures

**Files to modify:**
- `iot-simulator/src/real_device.py` - `read_sensors()` method

### 2. Hardware Diagnostics Implementation

Implement hardware monitoring and diagnostics:

- [ ] Battery voltage monitoring via ADC
- [ ] WiFi signal strength (RSSI) reading
- [ ] Sensor health checks
- [ ] System uptime tracking
- [ ] Memory usage monitoring
- [ ] Error logging

**Files to modify:**
- `iot-simulator/src/real_device.py` - `get_diagnostics()` method

### 3. ESP32 Firmware Development

Develop C++ firmware for ESP32 devices:

- [ ] Create Arduino/ESP-IDF project structure
- [ ] Implement sensor driver interfaces
- [ ] Add calibration data storage (EEPROM/NVS)
- [ ] Implement MQTT communication
- [ ] Add OTA (Over-The-Air) update support
- [ ] Create firmware build and flash scripts

**New directory:**
- `iot-simulator/esp32-firmware/` (already exists with placeholder)

### 4. Calibration Procedures

Create sensor calibration procedures:

- [ ] pH sensor calibration (3-point calibration)
- [ ] TDS sensor calibration
- [ ] Temperature compensation algorithms
- [ ] Calibration data storage format
- [ ] Calibration UI/tools

### 5. Testing and Validation

- [ ] Unit tests for sensor reading functions
- [ ] Integration tests with real hardware
- [ ] Field testing procedures
- [ ] Performance benchmarking
- [ ] Power consumption analysis

## Technical Requirements

### Hardware Requirements
- ESP32 development board (ESP32-WROOM-32 or similar)
- pH sensor module (e.g., DFRobot Gravity pH sensor)
- Turbidity sensor module
- TDS sensor module
- DHT22 temperature/humidity sensor
- Power supply (battery + solar panel for field deployment)

### Software Requirements
- Arduino IDE or ESP-IDF toolchain
- Python 3.11+ for device interface
- AWS IoT Core certificates
- MQTT client library (paho-mqtt)

### Dependencies
- `paho-mqtt` - MQTT communication
- `asyncio` - Async device operations
- ESP32 Arduino Core or ESP-IDF
- Sensor-specific libraries (pH, turbidity, TDS)

## Implementation Notes

### Current Placeholder Code

The `RealESP32Device` class in `iot-simulator/src/real_device.py` contains:

```python
async def read_sensors(self) -> SensorReading:
    # TODO: Replace with actual sensor reading code
    raise NotImplementedError(
        "Real sensor reading not implemented. "
        "This requires ESP32 firmware with sensor drivers."
    )
```

### Proposed Implementation Approach

1. **Phase 1:** Develop ESP32 firmware with sensor drivers
2. **Phase 2:** Implement Python interface to communicate with firmware
3. **Phase 3:** Add calibration procedures and tools
4. **Phase 4:** Field testing and validation

### Example Sensor Reading (Pseudocode)

```python
async def read_sensors(self) -> SensorReading:
    try:
        # Read pH sensor (analog input with calibration)
        ph_raw = await self._read_analog(pH_PIN)
        ph_value = self._calibrate_ph(ph_raw)
        
        # Read turbidity sensor (I2C)
        turbidity_value = await self._read_i2c_sensor(TURBIDITY_ADDR)
        
        # Read TDS sensor (analog input)
        tds_raw = await self._read_analog(TDS_PIN)
        tds_value = self._calibrate_tds(tds_raw, temperature)
        
        # Read temperature/humidity (DHT22)
        temp_value, humidity_value = await self._read_dht22()
        
        return SensorReading(
            pH=ph_value,
            turbidity=turbidity_value,
            tds=int(tds_value),
            temperature=temp_value,
            humidity=humidity_value
        )
    except Exception as e:
        raise SensorError(f"Failed to read sensors: {e}")
```

## Success Criteria

- [ ] Real ESP32 devices can read all sensor values accurately
- [ ] Sensor readings match calibrated reference values (±5% accuracy)
- [ ] Hardware diagnostics report correct battery and signal levels
- [ ] Devices can run for 24+ hours on battery power
- [ ] MQTT communication is reliable (>99% message delivery)
- [ ] OTA firmware updates work successfully
- [ ] Documentation is complete for hardware setup and calibration

## Priority

**P3 (Low)** - Not required for software-only deployment. The simulator provides complete functionality for development and testing without physical hardware.

## Milestone

**Hardware Integration** (Future - Q2 2026 or later)

## Related Issues

- None yet

## References

- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [AWS IoT Core Device SDK](https://github.com/aws/aws-iot-device-sdk-python-v2)
- [DFRobot pH Sensor](https://wiki.dfrobot.com/Gravity__Analog_pH_Sensor_Meter_Kit_V2_SKU_SEN0161-V2)
- Current implementation: `iot-simulator/src/real_device.py`

## Notes

This is a long-term enhancement that requires physical hardware procurement and firmware development expertise. The current simulator-based approach is sufficient for all software development and testing needs.
