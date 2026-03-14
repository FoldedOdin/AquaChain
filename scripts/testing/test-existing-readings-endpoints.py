#!/usr/bin/env python3
"""
Test existing readings endpoints with proper authentication
"""

import boto3
import json
import requests

def get_auth_token():
    """Get a valid auth token"""
    try:
        print(f"🔐 Getting auth token...")
        
        login_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin"
        
        login_data = {
            "email": "leninat259@gmail.com",
            "password": "AquaChain2024!"
        }
        
        response = requests.post(login_url, json=login_data, timeout=10)
        
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('token')
            
            if token:
                print(f"   ✅ Got token: {token[:20]}...")
                return token
            else:
                print(f"   ❌ No token in response: {result}")
                return None
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
        
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def test_endpoints_with_auth(token):
    """Test various endpoints with authentication"""
    try:
        print(f"\n🧪 Testing endpoints with authentication...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        # Test various endpoints that might have readings
        test_endpoints = [
            "/api/devices/ESP32-001",
            "/api/devices/ESP32-001/readings", 
            "/api/devices/ESP32-001/latest",
            "/api/v1/readings/ESP32-001/latest",
            "/api/v1/readings/ESP32-001/history",
            "/api/v1/devices/ESP32-001",
            "/api/v1/devices/ESP32-001/readings",
            "/api/water-quality/latest",
            "/water-quality"
        ]
        
        working_endpoints = []
        
        for endpoint in test_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n   🔍 Testing: {endpoint}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ SUCCESS! Response: {response.text[:200]}")
                    working_endpoints.append(endpoint)
                    
                    # Try to parse JSON
                    try:
                        data = response.json()
                        print(f"     📊 Data type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"     📋 Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            print(f"     📋 Array length: {len(data)}")
                    except:
                        pass
                        
                elif response.status_code == 404:
                    print(f"     ❌ Not found")
                elif response.status_code in [401, 403]:
                    print(f"     🔒 Auth issue: {response.text[:100]}")
                else:
                    print(f"     ⚠️ Other error: {response.text[:100]}")
                
            except Exception as e:
                print(f"     ❌ Request error: {e}")
        
        return working_endpoints
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return []

def check_dynamodb_directly():
    """Check DynamoDB directly to see what data we have"""
    try:
        print(f"\n🔍 Checking DynamoDB for ESP32-001 data...")
        
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        readings_table = dynamodb.Table('AquaChain-Readings')
        
        # Get current month partition
        from datetime import datetime
        now = datetime.utcnow()
        device_month = f"ESP32-001_{now.strftime('%Y-%m')}"
        
        print(f"   Querying partition: {device_month}")
        
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Latest first
            Limit=5
        )
        
        readings = response['Items']
        print(f"   Found {len(readings)} recent readings")
        
        if readings:
            latest = readings[0]
            print(f"   📊 Latest reading:")
            print(f"     Timestamp: {latest.get('timestamp')}")
            print(f"     pH: {latest.get('pH')}")
            print(f"     Temperature: {latest.get('temperature')}")
            print(f"     TDS: {latest.get('tds')}")
            print(f"     Turbidity: {latest.get('turbidity')}")
            
            return latest
        else:
            print(f"   ❌ No readings found")
            return None
        
    except Exception as e:
        print(f"❌ Error checking DynamoDB: {e}")
        return None

def main():
    print("🧪 Testing Existing Readings Endpoints")
    print("=" * 40)
    
    # Step 1: Get auth token
    print("\n1. Getting authentication token...")
    token = get_auth_token()
    
    if not token:
        print("❌ Could not get auth token, cannot test endpoints")
        return
    
    # Step 2: Test endpoints with auth
    print("\n2. Testing endpoints with authentication...")
    working_endpoints = test_endpoints_with_auth(token)
    
    # Step 3: Check DynamoDB directly
    print("\n3. Checking DynamoDB directly...")
    latest_reading = check_dynamodb_directly()
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Auth Token: {'✅' if token else '❌'}")
    print(f"   Working Endpoints: {len(working_endpoints)}")
    
    if working_endpoints:
        print(f"   ✅ Found working endpoints:")
        for endpoint in working_endpoints:
            print(f"     - {endpoint}")
    else:
        print(f"   ❌ No working endpoints found")
    
    print(f"   DynamoDB Data: {'✅' if latest_reading else '❌'}")
    
    if working_endpoints:
        print(f"\n💡 Recommendation:")
        print(f"   Update frontend to use: {working_endpoints[0]}")
        print(f"   This endpoint is already working and has data!")
    elif latest_reading:
        print(f"\n💡 Recommendation:")
        print(f"   Data exists in DynamoDB but no API endpoint is working")
        print(f"   Need to create or fix the readings API endpoint")
    else:
        print(f"\n💡 Recommendation:")
        print(f"   No data in DynamoDB and no working endpoints")
        print(f"   Need to fix both data ingestion and API endpoints")

if __name__ == "__main__":
    main()