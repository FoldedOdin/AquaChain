#!/usr/bin/env python3
"""
Test Device Data Flow with Correct Table Schema
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
readings_table = dynamodb.Table('AquaChain-Readings')
devices_table = dynamodb.Table('AquaChain-Devices')

def check_device_readings():
    """Check if ESP32-001 has readings using correct schema"""
    device_id = "ESP32-001"
    
    print(f"🔍 Checking readings for device: {device_id}")
    print("=" * 50)
    
    # Get current month partition key
    now = datetime.utcnow()
    device_month = f"{device_id}_{now.strftime('%Y-%m')}"
    
    print(f"📅 Current month partition: {device_month}")
    
    try:
        # Query using correct partition key
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Latest first
            Limit=10
        )
        
        readings = response['Items']
        print(f"✅ Found {len(readings)} readings in current month")
        
        if readings:
            print("\n📊 Latest readings:")
            for i, reading in enumerate(readings[:5]):
                timestamp = reading.get('timestamp', 'N/A')
                ph = reading.get('pH', reading.get('readings', {}).get('pH', 'N/A'))
                temp = reading.get('temperature', reading.get('readings', {}).get('temperature', 'N/A'))
                wqi = reading.get('wqi', reading.get('qualityScore', 'N/A'))
                
                print(f"   {i+1}. {timestamp}")
                print(f"      pH: {ph}, Temp: {temp}°C, WQI: {wqi}")
        
        # Also check previous month if current month has few readings
        if len(readings) < 5:
            prev_month = (now.replace(day=1) - timedelta(days=1))
            prev_device_month = f"{device_id}_{prev_month.strftime('%Y-%m')}"
            
            print(f"\n📅 Checking previous month: {prev_device_month}")
            
            prev_response = readings_table.query(
                KeyConditionExpression='deviceId_month = :device_month',
                ExpressionAttributeValues={
                    ':device_month': prev_device_month
                },
                ScanIndexForward=False,
                Limit=5
            )
            
            prev_readings = prev_response['Items']
            print(f"✅ Found {len(prev_readings)} readings in previous month")
            
            readings.extend(prev_readings)
        
        return readings
        
    except Exception as e:
        print(f"❌ Error querying readings: {e}")
        return []

def check_device_status():
    """Check device status in devices table"""
    device_id = "ESP32-001"
    
    print(f"\n🔍 Checking device status: {device_id}")
    print("=" * 50)
    
    try:
        response = devices_table.get_item(
            Key={'deviceId': device_id}
        )
        
        if 'Item' in response:
            device = response['Item']
            print("✅ Device found:")
            print(f"   Status: {device.get('status', 'N/A')}")
            print(f"   Connection: {device.get('connectionStatus', 'N/A')}")
            print(f"   Last Seen: {device.get('lastSeen', 'N/A')}")
            print(f"   Location: {device.get('location', 'N/A')}")
            print(f"   User ID: {device.get('userId', 'N/A')}")
            return device
        else:
            print("❌ Device not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking device: {e}")
        return None

def test_readings_api():
    """Test the readings API endpoint directly"""
    print(f"\n🧪 Testing Readings API")
    print("=" * 50)
    
    import boto3
    
    # Test Lambda function directly
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {
            "deviceId": "ESP32-001"
        },
        "queryStringParameters": None,
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"📊 Lambda Response Status: {result.get('statusCode', 'N/A')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            if body.get('success') and body.get('reading'):
                reading = body['reading']
                print("✅ API returned reading:")
                print(f"   Timestamp: {reading.get('timestamp', 'N/A')}")
                print(f"   pH: {reading.get('pH', 'N/A')}")
                print(f"   Temperature: {reading.get('temperature', 'N/A')}")
                print(f"   WQI: {reading.get('qualityScore', reading.get('wqi', 'N/A'))}")
                return True
            else:
                print(f"❌ API returned no reading: {body}")
        else:
            print(f"❌ API error: {result.get('body', 'Unknown error')}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 AquaChain Device Data Flow Test")
    print("=" * 60)
    
    # Check device status
    device = check_device_status()
    
    # Check readings in database
    readings = check_device_readings()
    
    # Test API endpoint
    api_works = test_readings_api()
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 50)
    print(f"✅ Device exists: {'Yes' if device else 'No'}")
    print(f"✅ Readings in DB: {len(readings) if readings else 0}")
    print(f"✅ API works: {'Yes' if api_works else 'No'}")
    
    if device and readings and api_works:
        print("\n🎉 All components working! Data should appear in dashboard.")
        print("💡 If dashboard still shows 'No Data', check:")
        print("   1. Frontend authentication")
        print("   2. API Gateway CORS configuration")
        print("   3. Frontend API endpoint URLs")
    else:
        print("\n🔧 Issues found:")
        if not device:
            print("   - Device not registered properly")
        if not readings:
            print("   - No readings in database")
        if not api_works:
            print("   - API endpoint not working")

if __name__ == "__main__":
    main()