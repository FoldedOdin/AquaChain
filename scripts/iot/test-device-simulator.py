"""
IoT Device Simulator for Testing
Simulates ESP32 device connecting to AWS IoT Core
"""

import json
import time
import random
import argparse
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


class AquaChainDeviceSimulator:
    """
    Simulates an AquaChain water quality sensor device
    """
    
    def __init__(self, device_id: str, endpoint: str, cert_path: str, 
                 key_path: str, ca_path: str):
        self.device_id = device_id
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.client = None
        self.connected = False
        
    def connect(self):
        """
        Connect to AWS IoT Core
        """
        print(f"Connecting device {self.device_id} to {self.endpoint}...")
        
        # Initialize MQTT client
        self.client = AWSIoTMQTTClient(self.device_id)
        self.client.configureEndpoint(self.endpoint, 8883)
        self.client.configureCredentials(
            self.ca_path,
            self.key_path,
            self.cert_path
        )
        
        # Configure connection
        self.client.configureAutoReconnectBackoffTime(1, 32, 20)
        self.client.configureOfflinePublishQueueing(-1)
        self.client.configureDrainingFrequency(2)
        self.client.configureConnectDisconnectTimeout(10)
        self.client.configureMQTTOperationTimeout(5)
        
        # Connect
        self.client.connect()
        self.connected = True
        print(f"Device {self.device_id} connected successfully")
        
    def disconnect(self):
        """
        Disconnect from AWS IoT Core
        """
        if self.client and self.connected:
            self.client.disconnect()
            self.connected = False
            print(f"Device {self.device_id} disconnected")
    
    def generate_sensor_reading(self) -> dict:
        """
        Generate realistic sensor readings
        """
        # Simulate realistic water quality parameters
        ph = round(random.uniform(6.5, 8.5), 2)
        turbidity = round(random.uniform(0.5, 10.0), 1)
        tds = random.randint(100, 800)
        temperature = round(random.uniform(15.0, 30.0), 1)
        
        return {
            'deviceId': self.device_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'readings': {
                'pH': ph,
                'turbidity': turbidity,
                'tds': tds,
                'temperature': temperature
            },
            'metadata': {
                'firmwareVersion': '2.1.0',
                'batteryLevel': random.randint(70, 100),
                'signalStrength': random.randint(-70, -30)
            }
        }
    
    def publish_sensor_data(self):
        """
        Publish sensor reading to IoT Core
        """
        if not self.connected:
            print("Error: Device not connected")
            return
        
        reading = self.generate_sensor_reading()
        topic = f"aquachain/{self.device_id}/data"
        
        print(f"Publishing to {topic}:")
        print(f"  pH: {reading['readings']['pH']}")
        print(f"  Turbidity: {reading['readings']['turbidity']} NTU")
        print(f"  TDS: {reading['readings']['tds']} ppm")
        print(f"  Temperature: {reading['readings']['temperature']}°C")
        
        self.client.publish(topic, json.dumps(reading), 1)
        print("Published successfully\n")
    
    def publish_telemetry(self):
        """
        Publish device telemetry to IoT Core
        """
        if not self.connected:
            print("Error: Device not connected")
            return
        
        telemetry = {
            'deviceId': self.device_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'batteryLevel': random.randint(70, 100),
            'signalStrength': random.randint(-70, -30),
            'freeMemory': random.randint(40000, 50000),
            'uptime': random.randint(3600, 86400)
        }
        
        topic = f"aquachain/{self.device_id}/telemetry"
        self.client.publish(topic, json.dumps(telemetry), 1)
        print(f"Telemetry published to {topic}")
    
    def subscribe_to_commands(self, callback):
        """
        Subscribe to device command topic
        """
        if not self.connected:
            print("Error: Device not connected")
            return
        
        topic = f"aquachain/{self.device_id}/commands"
        self.client.subscribe(topic, 1, callback)
        print(f"Subscribed to {topic}")
    
    def run_continuous(self, interval: int = 60):
        """
        Run device in continuous mode (send data every interval seconds)
        """
        print(f"Starting continuous mode (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.publish_sensor_data()
                
                # Publish telemetry every 5 readings
                if random.random() < 0.2:
                    self.publish_telemetry()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping device simulator...")
            self.disconnect()


def command_callback(client, userdata, message):
    """
    Callback for received commands
    """
    print(f"\nReceived command on {message.topic}:")
    print(f"  {message.payload.decode('utf-8')}\n")


def main():
    parser = argparse.ArgumentParser(description='AquaChain IoT Device Simulator')
    parser.add_argument('--device-id', required=True, help='Device ID (e.g., ESP32-ABC123)')
    parser.add_argument('--endpoint', required=True, help='IoT Core endpoint')
    parser.add_argument('--cert', required=True, help='Path to device certificate')
    parser.add_argument('--key', required=True, help='Path to private key')
    parser.add_argument('--ca', required=True, help='Path to CA certificate')
    parser.add_argument('--interval', type=int, default=60, help='Publish interval in seconds')
    parser.add_argument('--mode', choices=['continuous', 'single'], default='continuous',
                       help='Run mode: continuous or single publish')
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = AquaChainDeviceSimulator(
        device_id=args.device_id,
        endpoint=args.endpoint,
        cert_path=args.cert,
        key_path=args.key,
        ca_path=args.ca
    )
    
    # Connect to IoT Core
    simulator.connect()
    
    # Subscribe to commands
    simulator.subscribe_to_commands(command_callback)
    
    # Run based on mode
    if args.mode == 'continuous':
        simulator.run_continuous(interval=args.interval)
    else:
        simulator.publish_sensor_data()
        simulator.publish_telemetry()
        time.sleep(2)
        simulator.disconnect()


if __name__ == '__main__':
    main()
