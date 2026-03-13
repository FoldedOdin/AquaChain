#!/usr/bin/env python3
"""
Test the API with GSI queries to verify the fix is working
"""

import boto3
import json
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

def test_gsi_query_directly():
    """Test querying the readings table using the DeviceIndex GSI"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('AquaChain-Readings')
    
    device_id = "ESP32-001"
    
    print(f"🧪 Testing DeviceIndex GSI query for device: {device_id}")
    
    try:
        # Test 1: Get latest reading using GSI
        response = table.query(
            IndexName='DeviceIndex',
            KeyConditionExpression='deviceId = :deviceId',
            ExpressionAttributeValues={':deviceId': device_id},
            ScanIndexForward=False,  # Most recent first
            Limit=1
        )
        
        readings = response.get('Items', [])
        if readings:
            latest = convert_decimals(readings[0])
            print(f"✅ Latest reading via GSI: {json.dumps(latest, indent=2)}")
        else:
            print(f"❌ No readings found via GSI")
        
        # Test 2: Get historical readings (last 7 days)
        cutoff_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response_history = table.query(
            IndexName='DeviceIndex',
            KeyConditionExpression='deviceId = :deviceId AND #ts > :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':deviceId': device_id,
                ':cutoff': cutoff_time
            },
            ScanIndexForward=False,  # Most recent first
            Limit=10
        )
        
        history = response_history.get('Items', [])
        print(f"✅ Found {len(history)} readings in last 7 days via GSI")
        
        if history:
            print(f"   Most recent: {convert_decimals(history[0])['timestamp']}")
            print(f"   Oldest: {convert_decimals(history[-1])['timestamp']}")
        
        return readings, history
        
    except Exception as e:
        print(f"❌ Error testing GSI query: {e}")
        return [], []

def simulate_api_handler_logic():
    """Simulate the exact logic used in the API handler"""
    
    print(f"\n🔧 Simulating API handler logic...")
    
    # This mimics the _get_latest_reading function
    def _get_device_recent_readings(device_id, limit=5):
        try:
            dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
            table = dynamodb.Table('AquaChain-Readings')
            
            response = table.query(
                IndexName='DeviceIndex',
                KeyConditionExpression='deviceId = :deviceId',
                ExpressionAttributeValues={':deviceId': device_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error in _get_device_recent_readings: {e}")
            return []
    
    def _get_latest_reading(device_id):
        try:
            readings = _get_device_recent_readings(device_id, limit=1)
            if readings:
                return convert_decimals(readings[0])
            return None
        except Exception as e:
            print(f"Error in _get_latest_reading: {e}")
            return None
    
    # Test the functions
    device_id = "ESP32-001"
    
    latest = _get_latest_reading(device_id)
    if latest:
        print(f"✅ API handler logic works - latest reading: {latest['timestamp']}")
        return True
    else:
        print(f"❌ API handler logic failed - no reading returned")
        return False

def test_lambda_function_directly():
    """Test the Lambda function directly"""
    
    print(f"\n🚀 Testing Lambda function directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Create a test event for the latest reading endpoint
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "queryStringParameters": {},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0",  # The user ID from device data
                    "email": "test@example.com"
                }
            }
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-data-processing-dev',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        print(f"✅ Lambda response: {json.dumps(payload, indent=2)}")
        
        return payload
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return None

def main():
    """Main test function"""
    
    print("🧪 Testing API with GSI Queries")
    print("=" * 40)
    
    # Test 1: Direct GSI query
    print("1️⃣ Testing direct GSI queries...")
    latest, history = test_gsi_query_directly()
    print()
    
    # Test 2: Simulate API handler logic
    print("2️⃣ Testing API handler logic simulation...")
    handler_works = simulate_api_handler_logic()
    print()
    
    # Test 3: Test Lambda function directly
    print("3️⃣ Testing Lambda function directly...")
    lambda_result = test_lambda_function_directly()
    print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 20)
    
    if latest:
        print("✅ GSI queries work")
    else:
        print("❌ GSI queries failed")
    
    if handler_works:
        print("✅ API handler logic works")
    else:
        print("❌ API handler logic failed")
    
    if lambda_result and lambda_result.get('statusCode') == 200:
        print("✅ Lambda function works")
    else:
        print("❌ Lambda function failed")
        if lambda_result:
            print(f"   Status: {lambda_result.get('statusCode')}")
            print(f"   Body: {lambda_result.get('body', 'No body')}")

if __name__ == "__main__":
    main()