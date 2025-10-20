# AquaChain IoT Device Simulator

This simulator mimics ESP32-based water quality sensors and can be easily replaced with real hardware when available.

## Architecture

```
Simulator Layer → Device Interface → AWS IoT Core → AquaChain Backend
```

## Key Features

- **Hardware Abstraction**: Clean interface that real devices can implement
- **Realistic Data**: Generates sensor data with seasonal patterns and anomalies
- **Multiple Scenarios**: Normal operation, contamination events, sensor faults
- **Easy Transition**: Same MQTT topics and data format as real devices
- **Configuration Driven**: JSON config for devices, scenarios, and timing
- **Monitoring**: Built-in metrics and logging for demo purposes

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure AWS credentials
3. Update `config/devices.json` with your device settings
4. Run: `python simulator.py`

## Transitioning to Real Hardware

When you have ESP32 devices:
1. Flash the ESP32 firmware (see `esp32-firmware/` directory)
2. Stop the simulator
3. Real devices will use the same MQTT topics and data format
4. No backend changes required!

## Demo Scenarios

- **Normal Operation**: Realistic water quality readings
- **Contamination Event**: pH drops, turbidity increases
- **Sensor Malfunction**: Invalid readings trigger technician alerts
- **Load Testing**: Simulate 1000+ concurrent devices