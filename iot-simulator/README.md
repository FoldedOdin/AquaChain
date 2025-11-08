# AquaChain IoT Device Management

This directory contains everything for both **simulating** and **deploying real** ESP32 water quality sensors.

## Directory Structure

```
iot-simulator/
├── simulation/          # Virtual device simulation (no hardware needed)
│   ├── simulator.py     # Main simulation script
│   ├── simulated_device.py
│   ├── devices.json     # Simulated device config
│   └── aws_config.json  # AWS settings
├── esp32-firmware/      # Arduino code for real ESP32 devices
├── src/                 # Shared device interface
│   ├── device_interface.py  # Common interface
│   └── real_device.py       # Real ESP32 implementation
├── provision-device.py  # Register real devices in AWS IoT
└── config/              # Shared configuration
```

## Two Modes

### 1. Simulation Mode (Development/Testing)
Use virtual devices without physical hardware:
```bash
cd simulation
python simulator.py --devices 5
```
See `simulation/README.md` for details.

### 2. Real Hardware Mode (Production)
Deploy actual ESP32 devices:
1. Flash firmware from `esp32-firmware/`
2. Provision device: `python provision-device.py`
3. See `ESP32_IOT_SETUP_GUIDE.md` for full setup

## Quick Start

**For Simulation:**
```bash
pip install -r requirements.txt
python simulation/simulator.py --devices 3
```

**For Real Devices:**
See `ESP32_IOT_SETUP_GUIDE.md`

## Architecture

```
Simulated/Real Devices → Device Interface → AWS IoT Core → AquaChain Backend
```

Both simulated and real devices use the same MQTT topics and data format, allowing seamless transition.