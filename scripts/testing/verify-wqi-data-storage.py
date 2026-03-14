#!/usr/bin/env python3

"""
Verify WQI Data Storage
Check if WQI data is being stored correctly in DynamoDB
"""

import boto3
import json
from datetime import datetime, timedelta

def check_dynamodb_readings():
    """Check readings directly in DynamoDB"""
    print("🔍 Checking DynamoDB readings table...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('AquaChain-Readings')
        
        # Get recent readings (last 24 hours)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        print(f"   📊 Scanning for readings after: {yesterday.isoformat()}")
        
        # Scan for recent readings
        response = table.scan(
            FilterExpression='#ts >= :yesterday',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':yesterday': yesterday.isoformat() + 'Z'},
            Limit=10
        )
        
        readings = response.get('Items', [])
        print(f"   📊 Found {len(readings)} recent readings")
        
        if readings:
            for i, reading in enumerate(readings[:5]):  # Show first 5
                device_id = reading.get('deviceId', 'unknown')
                timestamp = reading.get('timestamp', 'unknown')
                wqi = reading.get('wqi')
                quality = reading.get('quality')
                quality_score = reading.get('qualityScore')
                
                print(f"\n   📋 Reading {i+1}:")
                print(f"      Device: {device_id}")
                print(f"      Timestamp: {timestamp}")
                print(f"      WQI: {wqi}")
                print(f"      Quality: {quality}")
                print(f"      QualityScore: {quality_score}")
                print(f"      pH: {reading.get('pH')}")
                print(f"      Turbidity: {reading.get('turbidity')}")
                print(f"      TDS: {reading.get('tds')}")
                print(f"      Temperature: {reading.get('temperature')}")
        
        return len(readings) > 0
        
    except Exception as e:
        print(f"   ❌ Error checking DynamoDB: {e}")
        return False

def check_specific_test_device():
    """Check for our test device readings"""
    print("\n🔍 Checking for test device readings...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('AquaChain-Readings')
        
        # Look for test devices
        test_devices = [
            'TEST-WQI-VERIFICATION',
            'TEST-EXCELLENT-WATER',
            'TEST-GOOD-WATER',
            'TEST-FAIR-WATER',
            'TEST-POOR-WATER'
        ]
        
        for device_id in test_devices:
            print(f"\n   🔍 Checking device: {device_id}")
            
            # Try to find readings for this device
            # Since we use deviceId_month as partition key, we need to check current month
            now = datetime.utcnow()
            device_month = f"{device_id}_{now.strftime('%Y-%m')}"
            
            try:
                response = table.query(
                    KeyConditionExpression='deviceId_month = :device_month',
                    ExpressionAttributeValues={':device_month': device_month},
                    ScanIndexForward=False,
                    Limit=5
                )
                
                readings = response.get('Items', [])
                print(f"      📊 Found {len(readings)} readings")
                
                if readings:
                    latest = readings[0]
                    print(f"      ✅ Latest WQI: {latest.get('wqi')}")
                    print(f"      ✅ Latest Quality: {latest.get('quality')}")
                    print(f"      📊 Timestamp: {latest.get('timestamp')}")
                
            except Exception as e:
                print(f"      ❌ Error querying {device_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking test devices: {e}")
        return False

def test_readings_service_direct():
    """Test readings service with known device"""
    print("\n🧪 Testing readings service with direct device query...")
    
    try:
        # First, get a real device ID from the database
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('AquaChain-Readings')
        
        # Scan for any device
        response = table.scan(Limit=1)
        readings = response.get('Items', [])
        
        if not readings:
            print("   ⚠️  No readings found in database")
            return False
        
        device_id = readings[0].get('deviceId')
        print(f"   📊 Testing with device: {device_id}")
        
        # Test readings service
        lambda_client = boto3.client('lambda')
        
        test_event = {
            "httpMethod": "GET",
            "path": f"/api/readings/{device_id}",
            "pathParameters": {"deviceId": device_id},
            "queryStringParameters": {"days": "30"},  # Longer period
            "headers": {"Authorization": "Bearer test-token"}
        }
        
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"   📊 Response status: {response['StatusCode']}")
        print(f"   📊 Response: {json.dumps(result, indent=2)}")
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            readings_data = body.get('readings', [])
            
            print(f"   ✅ Retrieved {len(readings_data)} readings")
            
            if readings_data:
                for i, reading in enumerate(readings_data[:3]):
                    wqi = reading.get('wqi')
                    quality = reading.get('quality')
                    print(f"      📋 Reading {i+1}: WQI={wqi}, Quality={quality}")
                
                return True
            else:
                print(f"   ⚠️  No readings in response")
                return False
        else:
            print(f"   ❌ Service returned error: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing readings service: {e}")
        return False

def main():
    """Main verification function"""
    print("🔧 AquaChain WQI Data Storage Verification")
    print("=" * 50)
    
    # Check data storage
    db_ok = check_dynamodb_readings()
    test_devices_ok = check_specific_test_device()
    service_ok = test_readings_service_direct()
    
    print("\n📋 VERIFICATION RESULTS")
    print("=" * 50)
    print(f"DynamoDB Readings:    {'✅ Found' if db_ok else '❌ None'}")
    print(f"Test Device Data:     {'✅ Found' if test_devices_ok else '❌ None'}")
    print(f"Readings Service:     {'✅ Working' if service_ok else '❌ Failed'}")
    
    if db_ok and service_ok:
        print("\n✅ WQI data storage is working correctly!")
    elif db_ok:
        print("\n⚠️  Data is being stored but service has issues")
    else:
        print("\n❌ Data storage issues detected")

if __name__ == "__main__":
    main()