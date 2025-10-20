#!/usr/bin/env python3
"""
Demo Controller for AquaChain Simulator
Provides interactive control over simulation scenarios for demonstrations
"""

import asyncio
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
import time

console = Console()


class DemoController:
    """Interactive controller for demonstration scenarios"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.iot_client = boto3.client('iot-data', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # Load device configuration
        with open("config/devices.json", 'r') as f:
            self.device_config = json.load(f)
        
        self.devices = [d for d in self.device_config['devices'] if d.get('enabled', True)]
    
    def display_main_menu(self):
        """Display main demo control menu"""
        menu_panel = Panel(
            """
[bold cyan]AquaChain Demo Controller[/bold cyan]

[green]Available Scenarios:[/green]
1. 🟢 Normal Operation - All devices reporting healthy water
2. 🟡 Water Quality Warning - Moderate contamination detected
3. 🔴 Critical Contamination - Severe water quality issues
4. ⚠️  Sensor Malfunction - Device hardware failure
5. 🔧 Service Request Demo - Technician assignment workflow
6. 📊 Load Test - High volume data simulation
7. 📈 Historical Data - Generate past data for trends
8. 🔍 System Status - View current system state

[yellow]Press 'q' to quit[/yellow]
            """,
            title="Demo Control Panel",
            border_style="blue"
        )
        
        console.print(menu_panel)
    
    async def run_interactive_demo(self):
        """Run interactive demo controller"""
        console.print("[bold green]🎮 AquaChain Demo Controller Started[/bold green]\n")
        
        while True:
            self.display_main_menu()
            
            choice = Prompt.ask(
                "Select scenario",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "q"],
                default="8"
            )
            
            if choice == "q":
                console.print("[yellow]👋 Goodbye![/yellow]")
                break
            
            try:
                await self.handle_menu_choice(choice)
            except KeyboardInterrupt:
                console.print("\n[yellow]⏹️  Scenario interrupted[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
            
            if choice != "8":  # Don't pause for status display
                input("\nPress Enter to continue...")
    
    async def handle_menu_choice(self, choice: str):
        """Handle menu selection"""
        scenarios = {
            "1": self.demo_normal_operation,
            "2": self.demo_water_warning,
            "3": self.demo_critical_contamination,
            "4": self.demo_sensor_malfunction,
            "5": self.demo_service_request,
            "6": self.demo_load_test,
            "7": self.demo_historical_data,
            "8": self.show_system_status
        }
        
        await scenarios[choice]()
    
    async def demo_normal_operation(self):
        """Demo normal water quality operation"""
        console.print("[green]🟢 Demonstrating Normal Operation[/green]")
        
        duration = int(Prompt.ask("Duration in seconds", default="60"))
        
        for i in range(duration):
            for device in self.devices:
                data = self.generate_normal_data(device)
                await self.send_device_data(device['deviceId'], data)
            
            console.print(f"[green]📤 Sent normal readings ({i+1}/{duration})[/green]")
            await asyncio.sleep(1)
        
        console.print("[green]✅ Normal operation demo complete[/green]")
    
    async def demo_water_warning(self):
        """Demo water quality warning scenario"""
        console.print("[yellow]🟡 Demonstrating Water Quality Warning[/yellow]")
        
        device_id = self.select_device()
        if not device_id:
            return
        
        device = next(d for d in self.devices if d['deviceId'] == device_id)
        
        # Send warning-level readings
        for i in range(5):
            data = self.generate_warning_data(device)
            await self.send_device_data(device_id, data)
            console.print(f"[yellow]⚠️  Sent warning reading {i+1}/5 for {device_id}[/yellow]")
            await asyncio.sleep(2)
        
        console.print("[yellow]✅ Warning scenario complete[/yellow]")
    
    async def demo_critical_contamination(self):
        """Demo critical contamination event"""
        console.print("[red]🔴 Demonstrating Critical Contamination[/red]")
        
        device_id = self.select_device()
        if not device_id:
            return
        
        device = next(d for d in self.devices if d['deviceId'] == device_id)
        
        console.print(f"[red]🚨 Triggering critical alert for {device_id}[/red]")
        
        # Send critical readings that should trigger alerts
        for i in range(3):
            data = self.generate_critical_data(device)
            await self.send_device_data(device_id, data)
            console.print(f"[red]🚨 Sent critical reading {i+1}/3 - Alert should trigger![/red]")
            await asyncio.sleep(3)
        
        console.print("[red]✅ Critical contamination demo complete[/red]")
        console.print("[cyan]💡 Check your notification channels for alerts![/cyan]")
    
    async def demo_sensor_malfunction(self):
        """Demo sensor malfunction scenario"""
        console.print("[orange1]⚠️  Demonstrating Sensor Malfunction[/orange1]")
        
        device_id = self.select_device()
        if not device_id:
            return
        
        device = next(d for d in self.devices if d['deviceId'] == device_id)
        
        # Send faulty sensor readings
        for i in range(4):
            data = self.generate_faulty_data(device)
            await self.send_device_data(device_id, data)
            console.print(f"[orange1]🔧 Sent faulty reading {i+1}/4 for {device_id}[/orange1]")
            await asyncio.sleep(2)
        
        console.print("[orange1]✅ Sensor malfunction demo complete[/orange1]")
        console.print("[cyan]💡 This should trigger technician assignment![/cyan]")
    
    async def demo_service_request(self):
        """Demo service request workflow"""
        console.print("[blue]🔧 Demonstrating Service Request Workflow[/blue]")
        
        # This would integrate with your service request API
        console.print("[blue]📋 This demo would:[/blue]")
        console.print("  1. Create service request via API")
        console.print("  2. Show technician assignment algorithm")
        console.print("  3. Display ETA calculation")
        console.print("  4. Simulate technician acceptance")
        console.print("  5. Show real-time status updates")
        
        console.print("[yellow]⚠️  Service request API integration needed[/yellow]")
    
    async def demo_load_test(self):
        """Demo high-volume data simulation"""
        console.print("[magenta]📊 Demonstrating Load Test[/magenta]")
        
        device_count = int(Prompt.ask("Number of virtual devices", default="10"))
        duration = int(Prompt.ask("Duration in seconds", default="30"))
        
        console.print(f"[magenta]🚀 Simulating {device_count} devices for {duration} seconds[/magenta]")
        
        # Generate virtual device IDs
        virtual_devices = [
            {
                'deviceId': f'LOAD-TEST-{i:03d}',
                'location': {
                    'latitude': 9.9312 + (i * 0.001),
                    'longitude': 76.2673 + (i * 0.001)
                }
            }
            for i in range(device_count)
        ]
        
        start_time = time.time()
        
        for second in range(duration):
            tasks = []
            for device in virtual_devices:
                data = self.generate_normal_data(device)
                task = self.send_device_data(device['deviceId'], data)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            elapsed = time.time() - start_time
            rate = (second + 1) * device_count / elapsed
            console.print(f"[magenta]📈 Second {second+1}/{duration} - Rate: {rate:.1f} msg/sec[/magenta]")
        
        total_messages = duration * device_count
        total_time = time.time() - start_time
        avg_rate = total_messages / total_time
        
        console.print(f"[green]✅ Load test complete: {total_messages} messages in {total_time:.1f}s (avg: {avg_rate:.1f} msg/sec)[/green]")
    
    async def demo_historical_data(self):
        """Generate historical data for trend analysis"""
        console.print("[cyan]📈 Generating Historical Data[/cyan]")
        
        days = int(Prompt.ask("Days of historical data", default="30"))
        
        console.print(f"[cyan]📊 Generating {days} days of data...[/cyan]")
        
        # This would integrate with your DynamoDB tables
        console.print("[cyan]📋 This demo would:[/cyan]")
        console.print(f"  1. Generate {days * 48 * len(self.devices)} historical readings")
        console.print("  2. Include seasonal variations")
        console.print("  3. Add realistic anomaly events")
        console.print("  4. Store in DynamoDB with proper partitioning")
        
        console.print("[yellow]⚠️  DynamoDB integration needed[/yellow]")
    
    def show_system_status(self):
        """Display current system status"""
        console.print("[blue]🔍 System Status[/blue]")
        
        # Create status table
        table = Table(title="Device Status")
        table.add_column("Device ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Location", style="yellow")
        table.add_column("Profile", style="magenta")
        table.add_column("Status", style="green")
        
        for device in self.devices:
            location = f"{device['location']['latitude']:.4f}, {device['location']['longitude']:.4f}"
            status = "🟢 Enabled" if device.get('enabled', True) else "🔴 Disabled"
            
            table.add_row(
                device['deviceId'],
                device['name'],
                location,
                device['sensorProfile'],
                status
            )
        
        console.print(table)
        
        # Show configuration summary
        config_panel = Panel(
            f"""
[bold]Configuration Summary[/bold]

📊 Total Devices: {len(self.devices)}
🌐 AWS Region: {self.region}
📡 Sensor Profiles: {len(self.device_config.get('sensorProfiles', {}))}
🎭 Scenarios: {len(self.device_config.get('scenarios', {}))}
            """,
            title="System Configuration",
            border_style="blue"
        )
        
        console.print(config_panel)
    
    def select_device(self) -> str:
        """Interactive device selection"""
        if len(self.devices) == 1:
            return self.devices[0]['deviceId']
        
        console.print("[cyan]Select device:[/cyan]")
        for i, device in enumerate(self.devices, 1):
            console.print(f"  {i}. {device['deviceId']} - {device['name']}")
        
        choice = Prompt.ask(
            "Device number",
            choices=[str(i) for i in range(1, len(self.devices) + 1)],
            default="1"
        )
        
        return self.devices[int(choice) - 1]['deviceId']
    
    def generate_normal_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Generate normal water quality data"""
        import random
        
        profile_name = device['sensorProfile']
        profile = self.device_config['sensorProfiles'][profile_name]
        
        return {
            'deviceId': device['deviceId'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'location': device['location'],
            'readings': {
                'pH': round(random.uniform(*profile['pH']['normal']), 2),
                'turbidity': round(random.uniform(*profile['turbidity']['normal']), 2),
                'tds': random.randint(*profile['tds']['normal']),
                'temperature': round(random.uniform(*profile['temperature']['normal']), 1),
                'humidity': round(random.uniform(*profile['humidity']['normal']), 1)
            },
            'diagnostics': {
                'batteryLevel': random.randint(70, 100),
                'signalStrength': random.randint(-70, -40),
                'sensorStatus': 'normal'
            }
        }
    
    def generate_warning_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Generate warning-level water quality data"""
        data = self.generate_normal_data(device)
        
        # Modify readings to warning levels
        data['readings']['pH'] = 6.0  # Low pH
        data['readings']['turbidity'] = 8.0  # High turbidity
        data['readings']['tds'] = 800  # High TDS
        
        return data
    
    def generate_critical_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Generate critical water quality data that should trigger alerts"""
        data = self.generate_normal_data(device)
        
        # Critical levels that should trigger alerts
        data['readings']['pH'] = 4.5  # Very acidic - critical
        data['readings']['turbidity'] = 25.0  # Very high turbidity
        data['readings']['tds'] = 1200  # Very high TDS
        
        return data
    
    def generate_faulty_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data with sensor faults"""
        data = self.generate_normal_data(device)
        
        # Simulate sensor faults
        data['readings']['pH'] = -1.0  # Invalid pH reading
        data['diagnostics']['sensorStatus'] = 'fault'
        
        return data
    
    async def send_device_data(self, device_id: str, data: Dict[str, Any]) -> bool:
        """Send data to AWS IoT Core"""
        try:
            topic = f"aquachain/{device_id}/data"
            payload = json.dumps(data)
            
            self.iot_client.publish(
                topic=topic,
                qos=1,
                payload=payload
            )
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to send data for {device_id}: {e}[/red]")
            return False


def main():
    parser = argparse.ArgumentParser(description="AquaChain Demo Controller")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--scenario", choices=["normal", "warning", "critical", "fault"], 
                       help="Run specific scenario non-interactively")
    parser.add_argument("--device", help="Target device ID for scenario")
    
    args = parser.parse_args()
    
    controller = DemoController(args.region)
    
    if args.scenario:
        # Non-interactive mode
        asyncio.run(controller.run_scenario(args.scenario, args.device))
    else:
        # Interactive mode
        asyncio.run(controller.run_interactive_demo())


if __name__ == "__main__":
    main()