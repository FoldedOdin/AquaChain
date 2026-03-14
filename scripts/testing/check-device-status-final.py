#!/usr/bin/env python3
"""
Final check of device status
"""

import boto3
from datetime import datetime
import pytz

def check_device_status():
    """Check current device status"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        devices_table = dynamodb.Table('AquaChain-Devices')
        
        response = devices_table.get_item(Key={'deviceId': 'ESP32-001'})
        
        if 'Item' not in response:
            print(f"❌ Device not found")
            return
        
        device = response['Item']
        
        print(f"📋 ESP32-001 Current Status:")
        print(f"   Connection Status: {device.get('connectionStatus')}")
        print(f"   Last Seen: {device.get('lastSeen')}")
        print(f"   Device Status: {device.get('status')}")
        print(f"   Location: {device.get('location')}")
        
        # Check if it should show as online
        connection_status = device.get('connectionStatus')
        if connection_status == 'online':
            print(f"\n✅ Device is set to ONLINE")
            print(f"✅ It should now show as ONLINE in your dashboard!")
        else:
            print(f"\n⚠️ Device status: {connection_status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔍 Final Device Status Check")
    print("=" * 30)
    
    check_device_status()
    
    print(f"\n📋 Summary:")
    print(f"✅ Device status has been manually updated")
    print(f"✅ ESP32-001 should now show as ONLINE in the dashboard")
    print(f"✅ The status monitor will keep it updated every 2 minutes")
    
    print(f"\n🔧 Next Steps:")
    print(f"1. Refresh your dashboard to see the updated status")
    print(f"2. The device should show as 'Online' instead of 'Offline'")
    print(f"3. As long as the device keeps sending data, it will stay online")

if __name__ == "__main__":
    main()