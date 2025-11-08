"""
Simulated ESP32 Device - Implements DeviceInterface for development and testing
This provides a software simulation of ESP32 hardware for development purposes
"""

import asyncio
import json
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from .device_interface import (
    DeviceInterface, 
    SensorReading, 
    DeviceDiagnostics, 
    WaterQualityData
)


class SimulatedDevice(DeviceInterface):
    """Simulated ESP32 device that mimics real hardware behavior"""
    
    def __init__(self, device_id: str, location: Dict[str, float], 
                 sensor_profile: Dict[str, Any], config: Dict[str, Any]):
        super().__init__(device_id, location)
        self.sensor_profile = sensor_profile
        self.config = config
        self.iot_client = None
        self.start_time = datetime.utcnow()
        self.scenario_state = "normal"
        self.fault_sensors = set()
        
        # Simulation state
        self.battery_level = random.randint(80, 100)
        self.signal_strength = random.randint(-70, -40)
        self.sensor_drift = {param: random.uniform(-0.1, 0.1) for param in ['pH', 'turbidity', 'tds', 'temperature']}
    
    async def initialize(self) -> bool:
        """Initialize simulated device (mimics ESP32 startup)"""
        try:
            print(f"🔄 Initializing simulated device {self.device_id}...")
            
            # Simulate device startup delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Initialize AWS IoT client
            self.iot_client = boto3.client('iot-data', 
                                         region_name=self.config['aws']['region'])
            
            # Simulate sensor calibration
            print(f"📡 Calibrating sensors for {self.device_id}...")
            await asyncio.sleep(random.uniform(2, 5))
            
            self.is_online = True
            print(f"✅ Device {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize device {self.device_id}: {e}")
            return False
    
    async def read_sensors(self) -> SensorReading:
        """Simulate reading sensors with realistic variations"""
        
        # Determine current scenario
        self._update_scenario()
        
        # Get base readings from sensor profile
        profile = self.sensor_profile
        readings = {}
        
        for param in ['pH', 'turbidity', 'tds', 'temperature']:
            if param in self.fault_sensors:
                # Simulate sensor fault
                readings[param] = -1.0 if param != 'tds' else -1
            else:
                # Normal reading with variations
                normal_range = profile[param]['normal']
                base_value = random.uniform(normal_range[0], normal_range[1])
                
                # Add seasonal variation
                if self.config['simulation']['enable_seasonal_variation']:
                    day_of_year = datetime.utcnow().timetuple().tm_yday
                    seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * day_of_year / 365)
                    base_value *= seasonal_factor
                
                # Add daily patterns
                if self.config['simulation']['enable_daily_patterns']:
                    hour = datetime.utcnow().hour
                    daily_factor = 1 + 0.05 * math.sin(2 * math.pi * hour / 24)
                    base_value *= daily_factor
                
                # Add sensor drift
                base_value += self.sensor_drift[param]
                
                # Apply scenario modifications
                if self.scenario_state == "contamination":
                    modifications = self.config.get('scenarios', {}).get('contamination', {}).get('modifications', {})
                    if param in modifications:
                        mod = modifications[param]
                        base_value = base_value * mod.get('multiply', 1.0) + mod.get('add', 0.0)
                
                # Ensure within sensor limits
                param_limits = profile[param]
                base_value = max(param_limits['min'], min(param_limits['max'], base_value))
                
                # Format appropriately
                if param == 'tds':
                    readings[param] = int(base_value)
                else:
                    readings[param] = round(base_value, 2)
        
        return SensorReading(**readings)
    
    async def get_diagnostics(self) -> DeviceDiagnostics:
        """Get simulated device diagnostics"""
        
        # Simulate battery drain
        uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        self.battery_level = max(10, self.battery_level - int(uptime_hours * 0.5))
        
        # Simulate signal strength variation
        self.signal_strength += random.randint(-5, 5)
        self.signal_strength = max(-90, min(-30, self.signal_strength))
        
        # Determine sensor status
        sensor_status = "fault" if self.fault_sensors else "normal"
        
        return DeviceDiagnostics(
            batteryLevel=self.battery_level,
            signalStrength=self.signal_strength,
            sensorStatus=sensor_status,
            firmwareVersion="SIM-1.0.0",
            uptime=int((datetime.utcnow() - self.start_time).total_seconds())
        )
    
    async def send_data(self, data: WaterQualityData) -> bool:
        """Send data to AWS IoT Core (same as real device)"""
        try:
            topic = self.config['mqtt']['topic_template'].format(deviceId=self.device_id)
            payload = data.model_dump_json()
            
            # This is the same call real devices will make
            response = self.iot_client.publish(
                topic=topic,
                qos=self.config['mqtt']['qos'],
                payload=payload
            )
            
            print(f"📤 {self.device_id}: Sent {self.scenario_state} data (WQI: ~{self._estimate_wqi(data.readings)})")
            return True
            
        except ClientError as e:
            print(f"❌ Failed to send data for {self.device_id}: {e}")
            return False
    
    def _update_scenario(self):
        """Update current scenario based on probabilities"""
        if not self.config['simulation']['enable_random_events']:
            return
        
        scenarios = self.config.get('scenarios', {})
        
        # Random scenario selection based on probabilities
        rand = random.random()
        cumulative_prob = 0
        
        for scenario_name, scenario_config in scenarios.items():
            cumulative_prob += scenario_config['probability']
            if rand <= cumulative_prob:
                if scenario_name != self.scenario_state:
                    print(f"🎭 {self.device_id}: Scenario changed to {scenario_name}")
                    self.scenario_state = scenario_name
                    
                    # Handle sensor faults
                    if scenario_name == "sensor_fault":
                        faulty_readings = scenario_config.get('faultyReadings', [])
                        self.fault_sensors = set(random.sample(faulty_readings, 
                                                             random.randint(1, len(faulty_readings))))
                    else:
                        self.fault_sensors.clear()
                break
    
    def _estimate_wqi(self, readings: SensorReading) -> int:
        """Rough WQI estimation for logging purposes"""
        try:
            # Simple WQI calculation for simulation
            ph_score = 100 if 6.5 <= readings.pH <= 8.5 else max(0, 100 - abs(readings.pH - 7.0) * 20)
            turbidity_score = max(0, 100 - readings.turbidity * 10)
            tds_score = max(0, 100 - max(0, readings.tds - 500) / 10)
            
            wqi = (ph_score + turbidity_score + tds_score) / 3
            return int(wqi)
        except:
            return 50
    
    async def shutdown(self):
        """Shutdown simulated device"""
        print(f"🔌 Shutting down simulated device {self.device_id}")
        self.is_online = False


class SimulatedDeviceFactory:
    """Factory to create simulated devices from configuration"""
    
    @staticmethod
    def create_from_config(device_config: Dict[str, Any], 
                          sensor_profiles: Dict[str, Any],
                          aws_config: Dict[str, Any]) -> SimulatedDevice:
        """Create a simulated device from JSON configuration"""
        
        device_id = device_config['deviceId']
        location = device_config['location']
        profile_name = device_config['sensorProfile']
        sensor_profile = sensor_profiles[profile_name]
        
        return SimulatedDevice(
            device_id=device_id,
            location=location,
            sensor_profile=sensor_profile,
            config=aws_config
        )