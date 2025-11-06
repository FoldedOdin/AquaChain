# IoT Device Simulation

This folder contains files for **simulating** ESP32 water quality devices without physical hardware.

## Files

- `simulator.py` - Main simulation script
- `simulated_device.py` - Virtual device implementation
- `devices.json` - Configuration for simulated devices
- `aws_config.json` - AWS IoT connection settings

## Usage

From the `iot-simulator` directory:

```bash
# Run simulation with default settings
python simulation/simulator.py

# Simulate 5 devices
python simulation/simulator.py --devices 5

# Force contamination scenario
python simulation/simulator.py --scenario contamination

# Custom reading interval (seconds)
python simulation/simulator.py --interval 60
```

## What It Does

- Creates virtual ESP32 devices
- Generates realistic sensor data (pH, turbidity, TDS, temperature, humidity)
- Sends data to AWS IoT Core via MQTT
- Simulates scenarios: normal, contamination, sensor faults

## Configuration

Edit `devices.json` to add/remove simulated devices.
Edit `aws_config.json` to change AWS region and IoT endpoint.

Or use environment variables in `.env` file (see `../.env.example`).
