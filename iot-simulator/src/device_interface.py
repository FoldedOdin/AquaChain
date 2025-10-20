"""
Device Interface - Abstract base class for both simulated and real devices
This ensures consistent behavior when transitioning from simulator to real hardware
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class SensorReading(BaseModel):
    """Standard sensor reading format used by both simulator and real devices"""
    pH: float
    turbidity: float  # NTU
    tds: int  # ppm
    temperature: float  # Celsius
    humidity: float  # %


class DeviceDiagnostics(BaseModel):
    """Device diagnostic information"""
    batteryLevel: int  # 0-100%
    signalStrength: int  # dBm
    sensorStatus: str  # normal, fault, calibrating
    firmwareVersion: Optional[str] = "1.0.0"
    uptime: Optional[int] = 0  # seconds


class WaterQualityData(BaseModel):
    """Complete water quality data packet - same format for simulator and real devices"""
    deviceId: str
    timestamp: str  # ISO 8601
    location: Dict[str, float]  # latitude, longitude
    readings: SensorReading
    diagnostics: DeviceDiagnostics


class DeviceInterface(ABC):
    """Abstract interface that both simulator and real ESP32 devices implement"""
    
    def __init__(self, device_id: str, location: Dict[str, float]):
        self.device_id = device_id
        self.location = location
        self.is_online = False
        self.last_reading_time: Optional[datetime] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize device (connect to WiFi, calibrate sensors, etc.)"""
        pass
    
    @abstractmethod
    async def read_sensors(self) -> SensorReading:
        """Read all sensor values"""
        pass
    
    @abstractmethod
    async def get_diagnostics(self) -> DeviceDiagnostics:
        """Get device diagnostic information"""
        pass
    
    @abstractmethod
    async def send_data(self, data: WaterQualityData) -> bool:
        """Send data to AWS IoT Core"""
        pass
    
    async def collect_and_send(self) -> bool:
        """Standard data collection and transmission flow"""
        try:
            # Read sensors
            readings = await self.read_sensors()
            diagnostics = await self.get_diagnostics()
            
            # Create data packet
            data = WaterQualityData(
                deviceId=self.device_id,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                location=self.location,
                readings=readings,
                diagnostics=diagnostics
            )
            
            # Send to cloud
            success = await self.send_data(data)
            
            if success:
                self.last_reading_time = datetime.utcnow()
            
            return success
            
        except Exception as e:
            print(f"Error in collect_and_send for {self.device_id}: {e}")
            return False
    
    @abstractmethod
    async def shutdown(self):
        """Clean shutdown of device"""
        pass


class DeviceManager:
    """Manages multiple devices (simulator or real)"""
    
    def __init__(self):
        self.devices: Dict[str, DeviceInterface] = {}
        self.is_running = False
    
    def add_device(self, device: DeviceInterface):
        """Add a device to management"""
        self.devices[device.device_id] = device
    
    async def initialize_all(self) -> bool:
        """Initialize all managed devices"""
        success_count = 0
        for device in self.devices.values():
            if await device.initialize():
                success_count += 1
            else:
                print(f"Failed to initialize device {device.device_id}")
        
        return success_count == len(self.devices)
    
    async def start_data_collection(self, interval_seconds: int = 30):
        """Start continuous data collection from all devices"""
        import asyncio
        
        self.is_running = True
        
        async def device_loop(device: DeviceInterface):
            while self.is_running:
                await device.collect_and_send()
                await asyncio.sleep(interval_seconds)
        
        # Start all device loops concurrently
        tasks = [device_loop(device) for device in self.devices.values()]
        await asyncio.gather(*tasks)
    
    async def shutdown_all(self):
        """Shutdown all devices"""
        self.is_running = False
        for device in self.devices.values():
            await device.shutdown()