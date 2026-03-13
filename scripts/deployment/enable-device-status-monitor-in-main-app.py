#!/usr/bin/env python3
"""
Enable Device Status Monitor in Main CDK App
Uncomments the device status monitor stack in the main CDK app
"""

import os
import sys

def enable_device_status_monitor():
    """Enable device status monitor in main CDK app"""
    
    app_py_path = os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk', 'app.py')
    
    print("🔧 Enabling Device Status Monitor in main CDK app...")
    
    try:
        # Read the current app.py file
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if already enabled
        if 'device_status_monitor_stack = DeviceStatusMonitorStack(' in content:
            print("✅ Device Status Monitor is already enabled in main CDK app")
            return
        
        # Uncomment the device status monitor stack
        updated_content = content.replace(
            '    # TEMPORARILY DISABLED - Deploy separately to avoid breaking existing stacks\n'
            '    # device_status_monitor_stack = DeviceStatusMonitorStack(',
            '    # Device Status Monitor Stack (Device online/offline status monitoring)\n'
            '    device_status_monitor_stack = DeviceStatusMonitorStack('
        )
        
        updated_content = updated_content.replace(
            '    #     app,\n'
            '    #     f"AquaChain-DeviceStatusMonitor-{env_name}",\n'
            '    #     config=config,\n'
            '    #     devices_table=data_stack.devices_table,\n'
            '    #     readings_table=data_stack.readings_table,\n'
            '    #     env=aws_env,\n'
            '    #     description=f"AquaChain Device Status Monitoring - {env_name}"\n'
            '    # )\n'
            '    # device_status_monitor_stack.add_dependency(data_stack)',
            '        app,\n'
            '        f"AquaChain-DeviceStatusMonitor-{env_name}",\n'
            '        config=config,\n'
            '        devices_table=data_stack.devices_table,\n'
            '        readings_table=data_stack.readings_table,\n'
            '        env=aws_env,\n'
            '        description=f"AquaChain Device Status Monitoring - {env_name}"\n'
            '    )\n'
            '    device_status_monitor_stack.add_dependency(data_stack)'
        )
        
        # Write the updated content
        with open(app_py_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Device Status Monitor enabled in main CDK app")
        print("📝 You can now deploy it with: cdk deploy AquaChain-DeviceStatusMonitor-dev")
        
    except Exception as e:
        print(f"❌ Error enabling device status monitor: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🚀 Enable Device Status Monitor in Main CDK App")
    print("=" * 50)
    
    enable_device_status_monitor()
    
    print("\n✅ Operation completed successfully")
    print("\nNext steps:")
    print("1. The device status monitor is now enabled in the main CDK app")
    print("2. You can deploy it as part of the main infrastructure")
    print("3. The standalone deployment will continue to work independently")

if __name__ == "__main__":
    main()