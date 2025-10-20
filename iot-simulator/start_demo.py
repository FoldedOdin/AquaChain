#!/usr/bin/env python3
"""
Quick Start Script for AquaChain Demo
Simplified entry point for demonstrations
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

def show_welcome():
    """Show welcome message"""
    welcome_panel = Panel(
        """
[bold cyan]🌊 Welcome to AquaChain IoT Simulator[/bold cyan]

This simulator demonstrates the complete AquaChain water quality monitoring system
without requiring physical ESP32 hardware.

[green]What this demo shows:[/green]
• Real-time water quality data processing
• ML-powered anomaly detection
• Critical alert notifications (SMS, email, push)
• Technician service assignment
• Tamper-evident ledger with hash chaining
• Mobile-first dashboard interfaces

[yellow]Demo Scenarios Available:[/yellow]
• Normal operation with realistic sensor variations
• Water contamination events triggering alerts
• Sensor malfunction detection
• Load testing with 1000+ concurrent devices
        """,
        title="AquaChain Demo",
        border_style="blue"
    )
    
    console.print(welcome_panel)

def check_setup():
    """Check if setup is complete"""
    required_files = [
        "config/devices.json",
        "config/aws_config.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        console.print(f"[red]❌ Missing configuration files: {', '.join(missing_files)}[/red]")
        console.print("[yellow]💡 Run setup first: python scripts/setup.py[/yellow]")
        return False
    
    return True

async def run_quick_demo():
    """Run a quick demonstration"""
    console.print("[green]🚀 Starting Quick Demo...[/green]")
    
    try:
        # Import simulator components
        from simulator import AquaChainSimulator
        
        # Create and configure simulator
        simulator = AquaChainSimulator()
        
        # Create 3 demo devices
        devices = simulator.create_devices(use_real_devices=False, device_count=3)
        
        if not devices:
            console.print("[red]❌ Failed to create demo devices[/red]")
            return
        
        console.print(f"[green]✅ Created {len(devices)} demo devices[/green]")
        
        # Initialize devices
        if not await simulator.initialize_devices():
            console.print("[red]❌ Failed to initialize devices[/red]")
            return
        
        console.print("[green]✅ Devices initialized successfully[/green]")
        
        # Run demo scenarios
        console.print("\n[cyan]🎭 Running Demo Scenarios...[/cyan]")
        
        # Normal operation for 30 seconds
        console.print("[green]📊 Scenario 1: Normal Operation (30 seconds)[/green]")
        
        # Start data collection task
        collection_task = asyncio.create_task(
            simulator.device_manager.start_data_collection(interval_seconds=5)
        )
        
        # Let it run for 30 seconds
        await asyncio.sleep(30)
        
        # Stop collection
        collection_task.cancel()
        
        console.print("[green]✅ Demo completed successfully![/green]")
        
        # Show next steps
        next_steps_panel = Panel(
            """
[bold green]🎉 Demo Complete![/bold green]

[cyan]What just happened:[/cyan]
• 3 simulated ESP32 devices sent water quality data
• Data was processed through the AquaChain pipeline
• ML inference calculated Water Quality Index (WQI)
• Readings were stored in tamper-evident ledger

[yellow]Next Steps:[/yellow]
• Run full simulator: [bold]python simulator.py[/bold]
• Interactive demo control: [bold]python scripts/demo_controller.py[/bold]
• Check AWS IoT Core for received messages
• View DynamoDB tables for stored data
• Test alert notifications with critical scenarios

[green]Ready for Real Hardware?[/green]
When you have ESP32 devices, just run:
[bold]python simulator.py --real[/bold]
            """,
            title="Demo Results",
            border_style="green"
        )
        
        console.print(next_steps_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Demo failed: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            await simulator.shutdown()
        except:
            pass

def main():
    """Main entry point"""
    show_welcome()
    
    if not check_setup():
        if Confirm.ask("Run setup now?"):
            os.system("python scripts/setup.py --create-certs")
        else:
            console.print("[yellow]👋 Setup required before running demo[/yellow]")
            return
    
    demo_type = Prompt.ask(
        "Choose demo type",
        choices=["quick", "full", "interactive"],
        default="quick"
    )
    
    if demo_type == "quick":
        console.print("[cyan]🏃 Running 30-second quick demo...[/cyan]")
        asyncio.run(run_quick_demo())
    
    elif demo_type == "full":
        console.print("[cyan]🔄 Starting full simulator...[/cyan]")
        os.system("python simulator.py")
    
    elif demo_type == "interactive":
        console.print("[cyan]🎮 Starting interactive demo controller...[/cyan]")
        os.system("python scripts/demo_controller.py")

if __name__ == "__main__":
    main()