#!/usr/bin/env python3
"""
Check for recent device data and see why lastSeen isn't being updated
"""

import boto3
import json
from datetime import datetime, timedelta
import pytz

def check_readings_table_structure():
    """Check the structure of the readings table"""
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
            return None
        
        print(f"✅ Found readings table: {readings_table.name}")
        
        # Get table description
        table_desc = readings_table.meta.client.describe_table(TableName=readings_table.name)
        
        print(f"\n📋 Table Schema:")
        key_schema = table_desc['Table']['KeySchema']
        for key in key_schema:
            print(f"   {key['KeyType']}: {key['AttributeName']}")
        
        # Check for GSIs
        gsis = table_desc['Table'].get('GlobalSecondaryIndexes', [])
        if gsis:
            print(f"\n📋 Global Secondary Indexes:")
            for gsi in gsis:
                print(f"   {gsi['IndexName']}:")
                for key in gsi['KeySchema']:
                    print(f"     {key['KeyType']}: {key['AttributeName']}")
        
        return readings_table
        
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return None

def scan_recent_readings(readings_table):
    """Scan for recent readings from any device"""
    try:
        print(f"\n🔍 Scanning for recent readings...")
        
        # Get current time
        now = datetime.now(pytz.UTC)
        one_hour_ago = now - timedelta(hours=1)
        
        # Scan with filter for recent readings
        response = readings_table.scan(
            FilterExpression='#ts >= :start_time',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':start_time': one_hour_ago.isoformat() + 'Z'
            },
            Limit=20
        )
        
        readings = response.get('Items', [])
        
        print(f"📊 Found {len(readings)} readings in last hour")
        
        if readings:
            print(f"\n   Recent Readings:")
            for reading in readings[:10]:
                device_id = reading.get('deviceId', 'Unknown')
                timestamp = reading.get('timestamp', 'Unknown')
                ph = reading.get('pH', 'N/A')
                temp = reading.get('temperature', 'N/A')
                print(f"   {device_id} - {timestamp} - pH: {ph}, Temp: {temp}°C")
        
        return readings
        
    except Exception as e:
        print(f"❌ Error scanning readings: {e}")
        return []

def check_esp32_001_readings(readings_table):
    """Try different methods to find ESP32-001 readings"""
    try:
        print(f"\n🔍 Looking for ESP32-001 readings specifically...")
        
        # Method 1: Try direct query (might fail due to key schema)
        try:
            response = readings_table.query(
                KeyConditionExpression='deviceId = :deviceId',
                ExpressionAttributeValues={':deviceId': 'ESP32-001'},
                ScanIndexForward=False,
                Limit=5
            )
            readings = response.get('Items', [])
            print(f"✅ Direct query found {len(readings)} readings")
            return readings
        except Exception as e:
            print(f"⚠️ Direct query failed: {e}")
        
        # Method 2: Try with deviceId_month key
        try:
            # Generate current month key
            now = datetime.now(pytz.UTC)
            month_key = f"ESP32-001_{now.strftime('%Y-%m')}"
            
            response = readings_table.query(
                KeyConditionExpression='deviceId_month = :deviceId_month',
                ExpressionAttributeValues={':deviceId_month': month_key},
                ScanIndexForward=False,
                Limit=5
            )
            readings = response.get('Items', [])
            print(f"✅ Month-based query found {len(readings)} readings")
            return readings
        except Exception as e:
            print(f"⚠️ Month-based query failed: {e}")
        
        # Method 3: Scan with filter
        try:
            response = readings_table.scan(
                FilterExpression='deviceId = :deviceId',
                ExpressionAttributeValues={':deviceId': 'ESP32-001'},
                Limit=10
            )
            readings = response.get('Items', [])
            print(f"✅ Scan found {len(readings)} readings")
            return readings
        except Exception as e:
            print(f"⚠️ Scan failed: {e}")
        
        return []
        
    except Exception as e:
        print(f"❌ Error checking ESP32-001 readings: {e}")
        return []

def check_data_processing_lambda():
    """Check if data processing lambda is working"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Find data processing functions
        functions = lambda_client.list_functions()
        
        data_processing_functions = []
        for func in functions['Functions']:
            func_name = func['FunctionName'].lower()
            if 'data' in func_name and ('processing' in func_name or 'ingestion' in func_name):
                data_processing_functions.append(func)
        
        print(f"\n🔍 Found {len(data_processing_functions)} data processing functions:")
        
        for func in data_processing_functions:
            func_name = func['FunctionName']
            print(f"   📋 {func_name}")
            
            # Check recent logs
            logs_client = boto3.client('logs', region_name='ap-south-1')
            log_group = f"/aws/lambda/{func_name}"
            
            try:
                now = datetime.now()
                one_hour_ago = now - timedelta(hours=1)
                
                response = logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=int(one_hour_ago.timestamp() * 1000),
                    endTime=int(now.timestamp() * 1000),
                    filterPattern='ESP32-001',
                    limit=10
                )
                
                events = response.get('events', [])
                print(f"      Recent ESP32-001 activity: {len(events)} events")
                
                if events:
                    for event in events[-3:]:
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message'].strip()
                        print(f"      {timestamp}: {message}")
                
            except Exception as e:
                print(f"      ⚠️ Could not check logs: {e}")
        
    except Exception as e:
        print(f"❌ Error checking data processing lambda: {e}")

def simulate_device_data():
    """Simulate sending device data to test the pipeline"""
    try:
        print(f"\n🧪 Simulating device data to test pipeline...")
        
        # Find IoT Core endpoint
        iot_client = boto3.client('iot', region_name='ap-south-1')
        
        try:
            endpoint_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
            iot_endpoint = endpoint_response['endpointAddress']
            print(f"✅ IoT Core endpoint: {iot_endpoint}")
        except Exception as e:
            print(f"⚠️ Could not get IoT endpoint: {e}")
            return
        
        # Create test message
        test_message = {
            "deviceId": "ESP32-001",
            "timestamp": datetime.now(pytz.UTC).isoformat() + 'Z',
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            },
            "metadata": {
                "firmwareVersion": "2.1.0",
                "batteryLevel": 85,
                "signalStrength": -45
            }
        }
        
        print(f"📋 Test message:")
        print(json.dumps(test_message, indent=2))
        
        # Publish to IoT Core
        iot_data_client = boto3.client('iot-data', 
                                      endpoint_url=f'https://{iot_endpoint}',
                                      region_name='ap-south-1')
        
        topic = 'aquachain/devices/ESP32-001/data'
        
        response = iot_data_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(test_message)
        )
        
        print(f"✅ Published test message to topic: {topic}")
        print(f"📋 Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error simulating device data: {e}")
        return False

def main():
    print("🔍 Checking Recent Device Data")
    print("=" * 35)
    
    # Step 1: Check readings table structure
    print("\n1. Checking Readings Table Structure...")
    readings_table = check_readings_table_structure()
    
    if not readings_table:
        return
    
    # Step 2: Scan for recent readings
    print("\n2. Scanning for Recent Readings...")
    recent_readings = scan_recent_readings(readings_table)
    
    # Step 3: Look specifically for ESP32-001
    print("\n3. Looking for ESP32-001 Readings...")
    esp32_readings = check_esp32_001_readings(readings_table)
    
    if esp32_readings:
        print(f"\n📊 ESP32-001 Recent Readings:")
        for reading in esp32_readings[:5]:
            timestamp = reading.get('timestamp', 'Unknown')
            ph = reading.get('pH', 'N/A')
            temp = reading.get('temperature', 'N/A')
            print(f"   {timestamp} - pH: {ph}, Temp: {temp}°C")
    else:
        print(f"\n❌ No ESP32-001 readings found")
    
    # Step 4: Check data processing lambda
    print("\n4. Checking Data Processing Lambda...")
    check_data_processing_lambda()
    
    # Step 5: Simulate device data
    print("\n5. Testing Data Pipeline...")
    if simulate_device_data():
        print(f"\n⏳ Waiting 10 seconds for processing...")
        import time
        time.sleep(10)
        
        print(f"\n6. Checking if device status updated...")
        # Re-check device status
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        devices_table = dynamodb.Table('AquaChain-Devices')
        
        try:
            response = devices_table.get_item(Key={'deviceId': 'ESP32-001'})
            if 'Item' in response:
                device = response['Item']
                print(f"📋 Updated Device Status:")
                print(f"   Connection Status: {device.get('connectionStatus', 'Not set')}")
                print(f"   Last Seen: {device.get('lastSeen', 'Not set')}")
                print(f"   Status Updated At: {device.get('statusUpdatedAt', 'Not set')}")
        except Exception as e:
            print(f"❌ Error checking updated status: {e}")
    
    print(f"\n📋 Summary:")
    print(f"If device still shows offline:")
    print(f"1. Data processing Lambda may not be updating lastSeen")
    print(f"2. Device may not be sending data to the correct topic")
    print(f"3. IoT Core rules may not be configured correctly")

if __name__ == "__main__":
    main()