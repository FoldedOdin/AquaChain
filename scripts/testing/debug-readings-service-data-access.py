#!/usr/bin/env python3
"""
Debug the readings service to see if it can access the data correctly
"""

import boto3
import json
from datetime import datetime, timedelta

def test_readings_service_data_access():
    """Test if the readings service can access data correctly"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    readings_table = dynamodb.Table('AquaChain-Readings')
    
    device_id = 'ESP32-001'
    now = datetime.utcnow()
    device_month = f"{device_id}_{now.strftime('%Y-%m')}"
    
    print("🔍 Testing Readings Service Data Access")
    print("="*50)
    print(f"Device ID: {device_id}")
    print(f"Device Month: {device_month}")
    print(f"Current Time: {now.isoformat()}Z")
    
    try:
        # Test 1: Query current month (same as readings service)
        print("\n📊 Test 1: Query Current Month")
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Latest first
            Limit=1
        )
        
        print(f"Items found: {len(response['Items'])}")
        if response['Items']:
            item = response['Items'][0]
            print(f"Latest reading timestamp: {item['timestamp']}")
            print(f"Reading data: pH={item.get('pH')}, temp={item.get('temperature')}")
            print("✅ Current month query successful")
        else:
            print("❌ No items found in current month")
        
        # Test 2: Query previous month (fallback)
        print("\n📊 Test 2: Query Previous Month (Fallback)")
        prev_month = (now.replace(day=1) - timedelta(days=1))
        prev_device_month = f"{device_id}_{prev_month.strftime('%Y-%m')}"
        print(f"Previous month key: {prev_device_month}")
        
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': prev_device_month
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        print(f"Items found in previous month: {len(response['Items'])}")
        if response['Items']:
            item = response['Items'][0]
            print(f"Previous month reading: {item['timestamp']}")
            print("✅ Previous month query successful")
        else:
            print("⚠️  No items found in previous month")
        
        # Test 3: Use GSI to query by deviceId directly
        print("\n📊 Test 3: Query Using DeviceIndex GSI")
        response = readings_table.query(
            IndexName='DeviceIndex',
            KeyConditionExpression='deviceId = :device_id',
            ExpressionAttributeValues={
                ':device_id': device_id
            },
            ScanIndexForward=False,
            Limit=5
        )
        
        print(f"Items found via GSI: {len(response['Items'])}")
        if response['Items']:
            for i, item in enumerate(response['Items']):
                print(f"  {i+1}. {item['timestamp']} - pH={item.get('pH')}")
            print("✅ GSI query successful")
        else:
            print("❌ No items found via GSI")
        
        # Test 4: Check if there's a data type issue
        print("\n📊 Test 4: Check Data Types")
        if response['Items']:
            item = response['Items'][0]
            print("Raw item structure:")
            for key, value in item.items():
                print(f"  {key}: {type(value)} = {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during data access test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lambda_function_directly():
    """Test the Lambda function directly with the same query logic"""
    
    print("\n🧪 Testing Lambda Function Logic Directly")
    print("="*50)
    
    # Simulate the exact logic from readings service
    try:
        import sys
        import os
        
        # Add the lambda directory to path
        lambda_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'readings_service')
        sys.path.insert(0, lambda_path)
        
        # Import the handler
        from handler import get_latest_reading, convert_decimals
        
        # Test the function
        device_id = 'ESP32-001'
        print(f"Calling get_latest_reading('{device_id}')")
        
        reading = get_latest_reading(device_id)
        
        if reading:
            print("✅ get_latest_reading returned data:")
            print(json.dumps(reading, indent=2))
            return True
        else:
            print("❌ get_latest_reading returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda function directly: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Debugging Readings Service Data Access")
    print("="*60)
    
    # Test data access
    data_access_ok = test_readings_service_data_access()
    
    # Test lambda function
    lambda_ok = test_lambda_function_directly()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if data_access_ok:
        print("✅ Data access: Working - Data exists and is queryable")
    else:
        print("❌ Data access: Failed - Cannot access data")
    
    if lambda_ok:
        print("✅ Lambda function: Working - Returns data correctly")
    else:
        print("❌ Lambda function: Failed - Cannot retrieve data")
    
    if data_access_ok and lambda_ok:
        print("\n🎉 DIAGNOSIS: Readings service should be working!")
        print("The issue might be with API Gateway integration or authentication.")
    elif data_access_ok and not lambda_ok:
        print("\n🔍 DIAGNOSIS: Data exists but Lambda function has issues")
        print("Check the Lambda function logic or imports.")
    else:
        print("\n🚨 DIAGNOSIS: Fundamental data access problem")
        print("Check DynamoDB permissions or table structure.")