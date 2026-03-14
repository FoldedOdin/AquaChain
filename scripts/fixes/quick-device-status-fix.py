#!/usr/bin/env python3
"""
Quick fix for device status - manually update lastSeen and trigger status monitor
"""

import boto3
from datetime import datetime
import pytz

def update_device_last_seen():
    """Manually update ESP32-001 lastSeen timestamp"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        devices_table = dynamodb.Table('AquaChain-Devices')
        
        # Get current timestamp
        current_time = datetime.now(pytz.UTC).isoformat() + 'Z'
        
        print(f"🔧 Updating ESP32-001 lastSeen to: {current_time}")
        
        # Update device
        response = devices_table.update_item(
            Key={'deviceId': 'ESP32-001'},
            UpdateExpression='SET lastSeen = :ts, connectionStatus = :status, statusUpdatedAt = :status_ts',
            ExpressionAttributeValues={
                ':ts': current_time,
                ':status': 'online',
                ':status_ts': current_time
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_device = response['Attributes']
        
        print(f"✅ Device updated successfully:")
        print(f"   Connection Status: {updated_device.get('connectionStatus')}")
        print(f"   Last Seen: {updated_device.get('lastSeen')}")
        print(f"   Status Updated At: {updated_device.get('statusUpdatedAt')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating device: {e}")
        return False

def main():
    print("🔧 Quick Device Status Fix")
    print("=" * 25)
    
    if update_device_last_seen():
        print(f"\n✅ Device status updated!")
        print(f"\nThe device should now show as 'Online' in the dashboard.")
        print(f"The status monitor will keep it updated as long as data keeps coming.")
    else:
        print(f"\n❌ Failed to update device status")

if __name__ == "__main__":
    main()