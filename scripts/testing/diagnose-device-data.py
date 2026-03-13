#!/usr/bin/env python3
"""
Diagnose device data issues - check if device exists and has readings
"""

import boto3
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal

def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def check_device_exists(device_id):
    """Check if device exists in devices table"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    # Try different possible table names
    possible_tables = [
        'AquaChain-Devices-dev',
        'AquaChain-Devices',
        'aquachain-devices-dev',
        'aquachain-devices'
    ]
    
    for table_name in possible_tables:
        try:
            table = dynamodb.Table(table_name)
            response = table.get_item(Key={'deviceId': device_id})
            
            if 'Item' in response:
                print(f"✅ Device {device_id} found in table: {table_name}")
                device = convert_decimals(response['Item'])
                print(f"   Device details: {json.dumps(device, indent=2)}")
                return table_name, device
            else:
                print(f"❌ Device {device_id} not found in table: {table_name}")
                
        except Exception as e:
            print(f"❌ Error checking table {table_name}: {e}")
    
    return None, None

def check_readings_exist(device_id):
    """Check if readings exist for device"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    # Try different possible table names
    possible_tables = [
        'AquaChain-Readings-dev',
        'AquaChain-Readings',
        'aquachain-readings-dev',
        'aquachain-readings'
    ]
    
    for table_name in possible_tables:
        try:
            table = dynamodb.Table(table_name)
            
            # Query for recent readings (last 7 days)
            cutoff_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            response = table.query(
                KeyConditionExpression='deviceId = :deviceId AND #ts > :cutoff',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':deviceId': device_id,
                    ':cutoff': cutoff_time
                },
                ScanIndexForward=False,  # Most recent first
                Limit=10
            )
            
            readings = response.get('Items', [])
            if readings:
                print(f"✅ Found {len(readings)} readings in table: {table_name}")
                print(f"   Latest reading: {convert_decimals(readings[0])}")
                return table_name, readings
            else:
                print(f"❌ No recent readings found in table: {table_name}")
                
                # Try to get any readings (no time filter)
                response_all = table.query(
                    KeyConditionExpression='deviceId = :deviceId',
                    ExpressionAttributeValues={':deviceId': device_id},
                    ScanIndexForward=False,
                    Limit=5
                )
                
                all_readings = response_all.get('Items', [])
                if all_readings:
                    print(f"   Found {len(all_readings)} older readings")
                    print(f"   Oldest reading: {convert_decimals(all_readings[0])}")
                    return table_name, all_readings
                
        except Exception as e:
            print(f"❌ Error checking readings table {table_name}: {e}")
    
    return None, []

def list_all_devices():
    """List all devices in the system"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    possible_tables = [
        'AquaChain-Devices-dev',
        'AquaChain-Devices',
        'aquachain-devices-dev',
        'aquachain-devices'
    ]
    
    for table_name in possible_tables:
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Limit=20)  # Get first 20 devices
            
            devices = response.get('Items', [])
            if devices:
                print(f"📋 Devices in table {table_name}:")
                for device in devices:
                    device_data = convert_decimals(device)
                    print(f"   - {device_data.get('deviceId', 'Unknown')} (Owner: {device_data.get('userId', 'Unknown')})")
                return table_name, devices
                
        except Exception as e:
            print(f"❌ Error listing devices from {table_name}: {e}")
    
    return None, []

def check_lambda_environment():
    """Check Lambda environment variables"""
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Check data processing Lambda
    function_names = [
        'aquachain-function-data-processing-dev',
        'AquaChain-Function-DataProcessing-dev',
        'aquachain-data-processing-dev'
    ]
    
    for function_name in function_names:
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            env_vars = response.get('Environment', {}).get('Variables', {})
            
            print(f"📋 Lambda {function_name} environment:")
            for key, value in env_vars.items():
                if 'TABLE' in key:
                    print(f"   {key}: {value}")
            
            return function_name, env_vars
            
        except Exception as e:
            print(f"❌ Error checking Lambda {function_name}: {e}")
    
    return None, {}

def test_api_directly():
    """Test the API directly with authentication"""
    
    print("🧪 Testing API endpoints directly...")
    
    # We'll test without auth first to see the error
    import requests
    
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    device_id = "ESP32-001"
    
    endpoints = [
        f"/api/v1/readings/{device_id}/latest",
        f"/api/v1/readings/{device_id}/history",
        f"/api/v1/readings/{device_id}"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{api_url}{endpoint}", timeout=10)
            print(f"📍 {endpoint}: Status {response.status_code}")
            
            if response.text:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"   Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")

def main():
    """Main diagnostic function"""
    
    device_id = "ESP32-001"  # The device you mentioned
    
    print("🔍 AquaChain Device Data Diagnosis")
    print("=" * 50)
    print(f"Target Device: {device_id}")
    print()
    
    # 1. Check if device exists
    print("1️⃣ Checking if device exists...")
    device_table, device_data = check_device_exists(device_id)
    print()
    
    # 2. Check if readings exist
    print("2️⃣ Checking for device readings...")
    readings_table, readings = check_readings_exist(device_id)
    print()
    
    # 3. List all devices if target not found
    if not device_data:
        print("3️⃣ Listing all devices in system...")
        list_all_devices()
        print()
    
    # 4. Check Lambda configuration
    print("4️⃣ Checking Lambda configuration...")
    lambda_name, env_vars = check_lambda_environment()
    print()
    
    # 5. Test API directly
    print("5️⃣ Testing API endpoints...")
    test_api_directly()
    print()
    
    # Summary
    print("📊 DIAGNOSIS SUMMARY")
    print("=" * 30)
    
    if device_data:
        print(f"✅ Device {device_id} exists")
    else:
        print(f"❌ Device {device_id} not found")
    
    if readings:
        print(f"✅ Found {len(readings)} readings")
    else:
        print(f"❌ No readings found")
    
    if device_table and readings_table:
        print(f"📋 Tables: Devices={device_table}, Readings={readings_table}")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    
    if not device_data:
        print("1. Create the device in the devices table")
        print("2. Check if device registration is working")
    
    if not readings:
        print("1. Check if IoT device is sending data")
        print("2. Verify IoT Core rules are working")
        print("3. Check data processing Lambda logs")
    
    if device_data and not readings:
        print("1. Device exists but no readings - check IoT pipeline")

if __name__ == "__main__":
    main()