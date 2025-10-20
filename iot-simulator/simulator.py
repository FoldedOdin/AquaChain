#!/usr/bin/env python3
"""
AquaChain IoT Simulator
Main entry point for simulating ESP32 water quality devices

Usage:
    python simulator.py                    # Run with default config
    python simulator.py --devices 5       # Simulate 5 devices
    python simulator.py --scenario contamination  # Force contamination scenario
    python simulator.py --real            # Use real devices (when available)
"""

import asyncio
import json
import argparse
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

# Rich console for better output
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import our device interfaces
from src.device_interface import DeviceManager
from src.simulated_device import SimulatedDeviceFactory
from src.real_device import RealDeviceFactory

# Load environment variables
load_dotenv()

console = Console()


class AquaChainSimulator:
    """Main simulator class that manages device lifecycle"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.device_manager = DeviceManager()
        self.config = self._load_configuration()
        self.is_running = False
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from JSON files"""
        try:
            # Load device configuration
            with open(self.config_path / "devices.json", 'r') as f:
                device_config = json.load(f)
            
            # Load AWS configuration
            with open(self.config_path / "aws_config.json", 'r') as f:
                aws_config = json.load(f)
            
            # Override with environment variables if available
            if os.getenv('AWS_IOT_ENDPOINT'):
                aws_config['aws']['iot_endpoint'] = os.getenv('AWS_IOT_ENDPOINT')
            
            if os.getenv('AWS_REGION'):
                aws_config['aws']['region'] = os.getenv('AWS_REGION')
            
            return {**device_config, **aws_config}
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load configuration: {e}[/red]")
            sys.exit(1)
    
    def create_devices(self, use_real_devices: bool = False, device_count: int = None) -> List:
        """Create simulated or real devices based on configuration"""
        devices = []
        
        # Filter enabled devices
        enabled_devices = [d for d in self.config['devices'] if d.get('enabled', True)]
        
        # Limit device count if specified
        if device_count:
            enabled_devices = enabled_devices[:device_count]
        
        for device_config in enabled_devices:
            try:
                if use_real_devices:
                    # Create real ESP32 device
                    device = RealDeviceFactory.create_from_config(
                        device_config, self.config
                    )
                    console.print(f"[blue]🔧 Created real device: {device.device_id}[/blue]")
                else:
                    # Create simulated device
                    device = SimulatedDeviceFactory.create_from_config(
                        device_config, 
                        self.config['sensorProfiles'],
                        self.config
                    )
                    console.print(f"[green]🤖 Created simulated device: {device.device_id}[/green]")
                
                devices.append(device)
                self.device_manager.add_device(device)
                
            except Exception as e:
                console.print(f"[red]❌ Failed to create device {device_config['deviceId']}: {e}[/red]")
        
        return devices
    
    async def initialize_devices(self) -> bool:
        """Initialize all devices"""
        console.print("[yellow]🔄 Initializing devices...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing devices...", total=None)
            
            success = await self.device_manager.initialize_all()
            
            progress.update(task, completed=True)
        
        if success:
            console.print("[green]✅ All devices initialized successfully[/green]")
        else:
            console.print("[red]❌ Some devices failed to initialize[/red]")
        
        return success
    
    async def start_simulation(self):
        """Start the main simulation loop"""
        self.is_running = True
        
        # Display startup information
        self._display_startup_info()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            console.print("[green]🚀 Starting data collection...[/green]")
            
            # Start data collection with live status display
            await self._run_with_status_display()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️  Received shutdown signal[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Simulation error: {e}[/red]")
        finally:
            await self.shutdown()
    
    async def _run_with_status_display(self):
        """Run simulation with live status display"""
        
        def create_status_table():
            """Create status table for live display"""
            table = Table(title="AquaChain Device Status")
            table.add_column("Device ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Last Reading", style="yellow")
            table.add_column("Scenario", style="magenta")
            
            for device in self.device_manager.devices.values():
                status = "🟢 Online" if device.is_online else "🔴 Offline"
                last_reading = device.last_reading_time.strftime("%H:%M:%S") if device.last_reading_time else "Never"
                scenario = getattr(device, 'scenario_state', 'N/A')
                
                table.add_row(device.device_id, status, last_reading, scenario)
            
            return table
        
        # Start data collection in background
        interval = self.config.get('timing', {}).get('readingInterval', 30)
        collection_task = asyncio.create_task(
            self.device_manager.start_data_collection(interval)
        )
        
        # Live status display
        with Live(create_status_table(), refresh_per_second=1, console=console) as live:
            while self.is_running:
                live.update(create_status_table())
                await asyncio.sleep(1)
        
        # Cancel collection task
        collection_task.cancel()
        try:
            await collection_task
        except asyncio.CancelledError:
            pass
    
    def _display_startup_info(self):
        """Display startup information"""
        device_count = len(self.device_manager.devices)
        interval = self.config.get('timing', {}).get('readingInterval', 30)
        
        info_panel = Panel(
            f"""
[bold green]AquaChain IoT Simulator Started[/bold green]

📊 Devices: {device_count}
⏱️  Reading Interval: {interval} seconds
🌐 AWS Region: {self.config['aws']['region']}
📡 IoT Endpoint: {self.config['aws']['iot_endpoint']}

[yellow]Press Ctrl+C to stop simulation[/yellow]
            """,
            title="Simulation Info",
            border_style="green"
        )
        
        console.print(info_panel)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.is_running = False
    
    async def shutdown(self):
        """Graceful shutdown"""
        console.print("[yellow]🔄 Shutting down simulator...[/yellow]")
        
        await self.device_manager.shutdown_all()
        
        console.print("[green]✅ Simulator shutdown complete[/green]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AquaChain IoT Device Simulator")
    parser.add_argument("--config", default="config", help="Configuration directory path")
    parser.add_argument("--devices", type=int, help="Number of devices to simulate")
    parser.add_argument("--real", action="store_true", help="Use real ESP32 devices instead of simulation")
    parser.add_argument("--scenario", choices=["normal", "contamination", "sensor_fault"], 
                       help="Force specific scenario for all devices")
    parser.add_argument("--interval", type=int, default=30, help="Reading interval in seconds")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = AquaChainSimulator(args.config)
    
    # Override configuration with command line arguments
    if args.scenario:
        # Force specific scenario
        for scenario_name in simulator.config.get('scenarios', {}):
            if scenario_name == args.scenario:
                simulator.config['scenarios'][scenario_name]['probability'] = 1.0
            else:
                simulator.config['scenarios'][scenario_name]['probability'] = 0.0
    
    if args.interval:
        simulator.config.setdefault('timing', {})['readingInterval'] = args.interval
    
    async def run_simulator():
        """Async wrapper for running simulator"""
        try:
            # Create devices
            devices = simulator.create_devices(
                use_real_devices=args.real,
                device_count=args.devices
            )
            
            if not devices:
                console.print("[red]❌ No devices created. Check configuration.[/red]")
                return
            
            # Initialize devices
            if not await simulator.initialize_devices():
                console.print("[red]❌ Device initialization failed[/red]")
                return
            
            # Start simulation
            await simulator.start_simulation()
            
        except Exception as e:
            console.print(f"[red]❌ Simulator error: {e}[/red]")
            import traceback
            traceback.print_exc()
    
    # Run the simulator
    try:
        asyncio.run(run_simulator())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")


if __name__ == "__main__":
    main()