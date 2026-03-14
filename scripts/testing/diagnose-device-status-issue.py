#!/usr/bin/env python3
"""
Diagnose device status issue - why device shows offline when it's online
"""

import boto3
import json
from datetime import datetime, timedelta
import pytz

def check_device_status():
    """Check the current status of ESP32-001 device"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Find devices table
        devices_table = None
        for table in dynamodb.tables.all():
            if 'devices' in table.name.lower() and 'aquachain' in table.name.lower():
                devices_table = dynamodb.Table(table.name)
                break
        
        if not devices_table:
            print("❌ No devices table found")
            return
        
        print(f"✅ Found devices table: {devices_table.name}")
        
        # Get ESP32-001 device
        device_id = "ESP32-001"
        
        try:
            response = devices_table.get_item(Key={'deviceId': device_id})
            
            if 'Item' not in response:
                print(f"❌ Device {device_id} not found")
                return
            
            device = response['Item']
            
            print(f"\n📋 Device {device_id} Status:")
            print(f"   Connection Status: {device.get('connectionStatus', 'Not set')}")
            print(f"   Last Seen: {device.get('lastSeen', 'Not set')}")
            print(f"   Status Updated At: {device.get('statusUpdatedAt', 'Not set')}")
            print(f"   Device Status: {device.get('status', 'Not set')}")
            print(f"   Owner: {device.get('ownerId', 'Not set')}")
            print(f"   Location: {device.get('location', 'Not set')}")
            
            # Check if lastSeen is recent
            last_seen = device.get('lastSeen')
            if last_seen:
                try:
                    # Parse timestamp
                    if isinstance(last_seen, str):
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    else:
                        print(f"⚠️ lastSeen is not a string: {type(last_seen)}")
                        return
                    
                    # Calculate time difference
                    now = datetime.now(pytz.UTC)
                    time_diff = now - last_seen_dt
                    
                    print(f"\n⏰ Time Analysis:")
                    print(f"   Last Seen: {last_seen_dt}")
                    print(f"   Current Time: {now}")
                    print(f"   Time Difference: {time_diff}")
                    print(f"   Minutes Ago: {time_diff.total_seconds() / 60:.1f}")
                    
                    # Determine expected status
                    offline_threshold = 5  # minutes
                    if time_diff.total_seconds() <= (offline_threshold * 60):
                        expected_status = 'online'
                    else:
                        expected_status = 'offline'
                    
                    current_status = device.get('connectionStatus', 'unknown')
                    
                    print(f"\n🔍 Status Analysis:")
                    print(f"   Expected Status: {expected_status}")
                    print(f"   Current Status: {current_status}")
                    print(f"   Status Match: {'✅' if expected_status == current_status else '❌'}")
                    
                    if expected_status != current_status:
                        print(f"\n⚠️ STATUS MISMATCH DETECTED!")
                        print(f"   Device should be {expected_status} but shows as {current_status}")
                        
                        # Check when status was last updated
                        status_updated = device.get('statusUpdatedAt')
                        if status_updated:
                            status_dt = datetime.fromisoformat(status_updated.replace('Z', '+00:00'))
                            status_age = now - status_dt
                            print(f"   Status last updated: {status_age.total_seconds() / 60:.1f} minutes ago")
                            
                            if status_age.total_seconds() > 300:  # 5 minutes
                                print(f"   🔧 Status monitor may not be running properly")
                    
                except Exception as e:
                    print(f"❌ Error parsing timestamps: {e}")
            
        except Exception as e:
            print(f"❌ Error getting device: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_recent_readings():
    """Check recent readings from ESP32-001"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        
        # Find readings table
        readings_table = None
        for table in dynamodb.tables.all():
            if 'readings' in table.name.lower() and 'aquachain' in table.name.lower():
                readings_table = dynamodb.Table(table.name)
                break
        
        if not readings_table:
            print("❌ No readings table found")
            return
        
        print(f"\n✅ Found readings table: {readings_table.name}")
        
        # Get recent readings for ESP32-001
        device_id = "ESP32-001"
        
        try:
            # Query recent readings (last 30 minutes)
            now = datetime.now(pytz.UTC)
            thirty_min_ago = now - timedelta(minutes=30)
            
            response = readings_table.query(
                KeyConditionExpression='deviceId = :deviceId AND #ts >= :start_time',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':deviceId': device_id,
                    ':start_time': thirty_min_ago.isoformat() + 'Z'
                },
                ScanIndexForward=False,  # Most recent first
                Limit=10
            )
            
            readings = response.get('Items', [])
            
            print(f"\n📊 Recent Readings (last 30 minutes):")
            print(f"   Found {len(readings)} readings")
            
            if readings:
                print(f"\n   Most Recent Readings:")
                for i, reading in enumerate(readings[:5]):
                    timestamp = reading.get('timestamp', 'Unknown')
                    ph = reading.get('pH', 'N/A')
                    temp = reading.get('temperature', 'N/A')
                    print(f"   {i+1}. {timestamp} - pH: {ph}, Temp: {temp}°C")
                
                # Check if data is being received recently
                latest_reading = readings[0]
                latest_time = datetime.fromisoformat(latest_reading['timestamp'].replace('Z', '+00:00'))
                time_since_latest = now - latest_time
                
                print(f"\n⏰ Latest Reading Analysis:")
                print(f"   Latest Reading: {latest_time}")
                print(f"   Time Since Latest: {time_since_latest.total_seconds() / 60:.1f} minutes ago")
                
                if time_since_latest.total_seconds() <= 300:  # 5 minutes
                    print(f"   ✅ Device is actively sending data!")
                else:
                    print(f"   ⚠️ Device hasn't sent data recently")
            else:
                print(f"   ❌ No recent readings found")
                
        except Exception as e:
            print(f"❌ Error querying readings: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_status_monitor_function():
    """Check if the device status monitor is running"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Find the device status monitor function
        functions = lambda_client.list_functions()
        
        status_monitor_function = None
        for func in functions['Functions']:
            if 'devicestatus' in func['FunctionName'].lower():
                status_monitor_function = func
                break
        
        if not status_monitor_function:
            print("\n❌ Device status monitor function not found")
            return
        
        func_name = status_monitor_function['FunctionName']
        print(f"\n✅ Found status monitor function: {func_name}")
        
        # Check recent invocations
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        log_group = f"/aws/lambda/{func_name}"
        
        try:
            # Get recent log events
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int(one_hour_ago.timestamp() * 1000),
                endTime=int(now.timestamp() * 1000),
                limit=20
            )
            
            events = response.get('events', [])
            
            print(f"\n📋 Recent Status Monitor Activity:")
            print(f"   Found {len(events)} log events in last hour")
            
            if events:
                print(f"\n   Recent Log Messages:")
                for event in events[-5:]:  # Last 5 events
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'].strip()
                    print(f"   {timestamp}: {message}")
            else:
                print(f"   ⚠️ No recent activity - status monitor may not be running")
                
        except Exception as e:
            print(f"⚠️ Could not check logs: {e}")
            
    except Exception as e:
        print(f"❌ Error checking status monitor: {e}")

def trigger_status_monitor():
    """Manually trigger the status monitor function"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Find the device status monitor function
        functions = lambda_client.list_functions()
        
        status_monitor_function = None
        for func in functions['Functions']:
            if 'devicestatus' in func['FunctionName'].lower():
                status_monitor_function = func
                break
        
        if not status_monitor_function:
            print("\n❌ Cannot trigger - status monitor function not found")
            return
        
        func_name = status_monitor_function['FunctionName']
        print(f"\n🔧 Triggering status monitor: {func_name}")
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"✅ Status monitor triggered successfully")
        print(f"📋 Response:")
        print(json.dumps(payload, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error triggering status monitor: {e}")
        return False

def main():
    print("🔍 AquaChain Device Status Diagnosis")
    print("=" * 40)
    
    # Step 1: Check device status in database
    print("\n1. Checking Device Status in Database...")
    check_device_status()
    
    # Step 2: Check recent readings
    print("\n2. Checking Recent Device Readings...")
    check_recent_readings()
    
    # Step 3: Check status monitor function
    print("\n3. Checking Status Monitor Function...")
    check_status_monitor_function()
    
    # Step 4: Trigger status monitor
    print("\n4. Triggering Status Monitor...")
    if trigger_status_monitor():
        print("\n5. Re-checking Device Status After Trigger...")
        import time
        time.sleep(3)  # Wait a bit for update
        check_device_status()
    
    print("\n📋 Diagnosis Complete!")
    print("\nIf device still shows offline after this:")
    print("1. Check if data processing Lambda is updating lastSeen")
    print("2. Verify status monitor CloudWatch rule is enabled")
    print("3. Check for any Lambda function errors")

if __name__ == "__main__":
    main()