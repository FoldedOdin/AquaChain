#!/usr/bin/env python3
"""
Debug the complete frontend-to-backend flow to identify why readings aren't showing
"""

import boto3
import requests
import json
import base64

def get_id_token_and_decode():
    """Get ID token and decode it to understand the user context"""
    
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    user_pool_id = 'ap-south-1_QUDl7hG8u'
    client_id = '692o9a3pjudl1vudfgqpr5nuln'
    username = 'readingstest@aquachain.com'
    password = 'TestPassword123!'
    
    try:
        auth_response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        id_token = auth_response['AuthenticationResult']['IdToken']
        
        # Decode JWT payload
        def decode_jwt_payload(token):
            try:
                parts = token.split('.')
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)  # Add padding
                decoded = base64.urlsafe_b64decode(payload)
                return json.loads(decoded)
            except Exception as e:
                print(f"Error decoding JWT: {e}")
                return None
        
        payload = decode_jwt_payload(id_token)
        
        print("🔍 ID Token Analysis")
        print("=" * 40)
        print(f"Subject (User ID): {payload.get('sub')}")
        print(f"Email: {payload.get('email')}")
        print(f"Username: {payload.get('cognito:username')}")
        print(f"Token Use: {payload.get('token_use')}")
        print(f"Audience: {payload.get('aud')}")
        print(f"Expires: {payload.get('exp')}")
        
        return id_token, payload
        
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None, None

def test_api_with_different_devices(id_token):
    """Test API with different device IDs to see what works"""
    
    print("\n🧪 Testing API with Different Device IDs")
    print("=" * 50)
    
    device_ids = ['ESP32-001', 'ESP32-002', 'ESP32-ABC123', 'AquaChain-Device-001']
    
    headers = {
        'Authorization': f'Bearer {id_token}',
        'Content-Type': 'application/json'
    }
    
    working_devices = []
    
    for device_id in device_ids:
        print(f"\n🔍 Testing device: {device_id}")
        
        url = f"https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/{device_id}/latest"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ SUCCESS: {data.get('success')}")
                if 'reading' in data:
                    reading = data['reading']
                    print(f"  📊 pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                    print(f"  📅 Timestamp: {reading.get('timestamp')}")
                working_devices.append(device_id)
            elif response.status_code == 404:
                try:
                    error_data = response.json()
                    print(f"  ⚠️  404: {error_data.get('error', 'No readings found')}")
                except:
                    print(f"  ⚠️  404: {response.text}")
            else:
                print(f"  ❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data.get('error', response.text)}")
                except:
                    print(f"  Raw: {response.text}")
                    
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    return working_devices

def simulate_frontend_request(id_token):
    """Simulate exactly what the frontend dataService does"""
    
    print("\n🎭 Simulating Frontend Request")
    print("=" * 40)
    
    # Simulate the exact frontend flow
    device_id = 'ESP32-001'
    endpoint = f'/api/v1/readings/{device_id}/latest'
    api_base_url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev'
    url = f"{api_base_url}{endpoint}"
    
    print(f"URL: {url}")
    print(f"Token: {id_token[:20]}...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {id_token}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code} {response.statusText if hasattr(response, 'statusText') else ''}")
        
        # Get response text first (like frontend does)
        response_text = response.text
        print(f"Raw response: {response_text[:200]}...")
        
        if response.ok:
            # Parse JSON (like frontend does)
            result = response.json()
            print(f"Parsed JSON: {json.dumps(result, indent=2)}")
            
            # Check if response has success field (like frontend does)
            if 'success' in result:
                if result['success']:
                    print("✅ Frontend would extract result.data")
                    data = result.get('data')  # This is what frontend expects
                    reading = result.get('reading')  # This is what API actually returns
                    
                    print(f"result.data: {data}")
                    print(f"result.reading: {reading}")
                    
                    # The frontend expects result.data, but API returns result.reading
                    if data:
                        print("✅ Frontend would get data successfully")
                        return data
                    elif reading:
                        print("⚠️  API returns 'reading' but frontend expects 'data'")
                        return reading
                    else:
                        print("❌ No data or reading in response")
                        return None
                else:
                    print("❌ success=false in response")
                    return None
            else:
                print("✅ Direct data response (no success field)")
                return result
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def check_dynamodb_data():
    """Check what data actually exists in DynamoDB"""
    
    print("\n📊 Checking DynamoDB Data")
    print("=" * 30)
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        readings_table = dynamodb.Table('AquaChain-Readings')
        
        # Query for ESP32-001 data
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': 'ESP32-001_2026-03'
            },
            ScanIndexForward=False,
            Limit=3
        )
        
        print(f"Items found: {len(response['Items'])}")
        
        for i, item in enumerate(response['Items']):
            print(f"  {i+1}. {item['timestamp']} - pH: {item.get('pH')}, Temp: {item.get('temperature')}")
        
        return len(response['Items']) > 0
        
    except Exception as e:
        print(f"❌ Error checking DynamoDB: {e}")
        return False

def main():
    """Run complete frontend-backend flow debug"""
    
    print("🔧 Frontend-Backend Flow Debug")
    print("=" * 60)
    
    # Step 1: Get and analyze token
    id_token, payload = get_id_token_and_decode()
    if not id_token:
        print("❌ Cannot proceed without token")
        return
    
    # Step 2: Check DynamoDB data
    data_exists = check_dynamodb_data()
    
    # Step 3: Test API with different devices
    working_devices = test_api_with_different_devices(id_token)
    
    # Step 4: Simulate frontend request
    frontend_result = simulate_frontend_request(id_token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    print(f"✅ Token: {'Working' if id_token else 'Failed'}")
    print(f"✅ DynamoDB Data: {'Exists' if data_exists else 'Missing'}")
    print(f"✅ Working Devices: {working_devices}")
    print(f"✅ Frontend Simulation: {'Success' if frontend_result else 'Failed'}")
    
    if frontend_result:
        print("\n🎉 FRONTEND SHOULD BE WORKING!")
        print("If readings still don't show, check:")
        print("• Browser console for JavaScript errors")
        print("• Network tab for failed requests")
        print("• localStorage for correct token storage")
        print("• Component state management")
    else:
        print("\n🔍 FRONTEND ISSUES IDENTIFIED:")
        if not data_exists:
            print("• No data in DynamoDB")
        if not working_devices:
            print("• API not returning data for any devices")
        if not frontend_result:
            print("• Frontend request simulation failed")

if __name__ == "__main__":
    main()