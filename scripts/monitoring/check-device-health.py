#!/usr/bin/env python3
"""
Monitor ESP32 Connection Health

Checks if device is publishing data regularly and reports health status.
"""

import boto3
import sys
from datetime import datetime, timezone

def check_device_health(device_id='ESP32-001', table_name='AquaChain-Readings-dev'):
    """Check if device is publishing data regularly"""
    
    print("=" * 60)
    print("ESP32 Device Health Check")
    print("=" * 60)
    print()
    
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    try:
        # Query for most recent reading
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='deviceId = :did',
            ExpressionAttributeValues={':did': {'S': device_id}},
            Limit=1,
            ScanIndexForward=False
        )
        
        if not response['Items']:
            print(f"❌ No data found for device: {device_id}")
            print()
            print("Possible causes:")
            print("- Device not connected")
            print("- Device not publishing")
            print("- IoT Rule not triggering Lambda")
            print("- Lambda not writing to DynamoDB")
            return False
        
        # Parse last reading
        last_reading = response['Items'][0]
        timestamp_str = last_reading['timestamp']['S']
        
        # Parse ISO 8601 timestamp
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        last_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        age_seconds = (now - last_time).total_seconds()
        
        # Get sensor readings
        readings = last_reading.get('readings', {}).get('M', {})
        ph = readings.get('pH', {}).get('N', 'N/A')
        temp = readings.get('temperature', {}).get('N', 'N/A')
        tds = readings.get('tds', {}).get('N', 'N/A')
        turbidity = readings.get('turbidity', {}).get('N', 'N/A')
        
        # Get diagnostics
        diagnostics = last_reading.get('diagnostics', {}).get('M', {})
        signal = diagnostics.get('signalStrength', {}).get('N', 'N/A')
        
        # Display results
        print(f"Device ID: {device_id}")
        print(f"Last Reading: {last_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Data Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)")
        print()
        
        print("Sensor Readings:")
        print(f"  pH: {ph}")
        print(f"  Temperature: {temp}°C")
        print(f"  TDS: {tds} ppm")
        print(f"  Turbidity: {turbidity} NTU")
        print()
        
        print("Diagnostics:")
        print(f"  WiFi Signal: {signal} dBm")
        print()
        
        # Health assessment
        print("=" * 60)
        if age_seconds < 60:
            print("✅ HEALTHY - Device is publishing data regularly")
            print("   Status: Excellent")
            return True
        elif age_seconds < 120:
            print("✅ HEALTHY - Recent data received")
            print("   Status: Good")
            return True
        elif age_seconds < 300:
            print("⚠️ WARNING - Data is getting old")
            print("   Status: Check device connection")
            print()
            print("   Recommendations:")
            print("   - Check ESP32 serial monitor")
            print("   - Verify WiFi connection")
            print("   - Check for reconnect messages")
            return True
        else:
            print("❌ CRITICAL - Device appears offline")
            print("   Status: No recent data")
            print()
            print("   Troubleshooting steps:")
            print("   1. Check ESP32 power and serial output")
            print("   2. Verify WiFi connectivity")
            print("   3. Check AWS IoT connection status")
            print("   4. Run: python scripts/diagnostics/pre-upload-checklist.py")
            return False
            
    except Exception as e:
        print(f"❌ Error checking device health: {e}")
        return False

def check_publish_rate(device_id='ESP32-001', table_name='AquaChain-Readings-dev', minutes=10):
    """Check how many readings were published in last N minutes"""
    
    print()
    print("=" * 60)
    print(f"Publish Rate Analysis (Last {minutes} minutes)")
    print("=" * 60)
    print()
    
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    try:
        # Calculate time range
        now = datetime.now(timezone.utc)
        start_time = now.timestamp() - (minutes * 60)
        
        # Query readings in time range
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='deviceId = :did AND #ts >= :start',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':did': {'S': device_id},
                ':start': {'S': datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat()}
            },
            ScanIndexForward=False
        )
        
        count = len(response['Items'])
        expected = minutes * 2  # 30-second interval = 2 per minute
        success_rate = (count / expected * 100) if expected > 0 else 0
        
        print(f"Readings received: {count}")
        print(f"Expected readings: {expected} (30-second interval)")
        print(f"Success rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 95:
            print("✅ Excellent publish rate")
        elif success_rate >= 80:
            print("⚠️ Good publish rate, some missed readings")
        elif success_rate >= 50:
            print("⚠️ Poor publish rate, connection issues likely")
        else:
            print("❌ Critical publish rate, device mostly offline")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Error checking publish rate: {e}")
        return False

def main():
    """Main function"""
    
    device_id = 'ESP32-001'
    
    # Check basic health
    health_ok = check_device_health(device_id)
    
    # Check publish rate if device is healthy
    if health_ok:
        rate_ok = check_publish_rate(device_id, minutes=10)
    else:
        rate_ok = False
    
    print()
    print("=" * 60)
    
    if health_ok and rate_ok:
        print("✅ Overall Status: HEALTHY")
        print()
        print("Device is operating normally.")
        return 0
    elif health_ok:
        print("⚠️ Overall Status: DEGRADED")
        print()
        print("Device is connected but missing some publishes.")
        print("Check WiFi signal strength and network stability.")
        return 1
    else:
        print("❌ Overall Status: OFFLINE")
        print()
        print("Device is not publishing data.")
        print("Check device power, WiFi, and AWS IoT connection.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
