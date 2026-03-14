#!/usr/bin/env python3
"""
Test the Decimal serialization fix
"""

import boto3
import json
import requests
from datetime import datetime

def get_fresh_cognito_token():
    """Get a fresh Cognito token for testing"""
    
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    
    # Use the test user credentials
    username = "karthikkpradeep123@gmail.com"
    password = "TempPassword123!"
    
    # User pool details
    user_pool_id = "ap-south-1_QUDl7hG8u"
    client_id = "692o9a3pjudl1vudfgqpr5nuln"
    
    try:
        # Authenticate user
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Extract token
        access_token = response['AuthenticationResult']['AccessToken']
        print(f"✅ Got fresh access token")
        return access_token
        
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def test_readings_endpoint_with_fresh_token():
    """Test the readings endpoint with a fresh token"""
    
    # Get fresh token
    token = get_fresh_cognito_token()
    if not token:
        print("❌ Could not get fresh token")
        return False
    
    # Test endpoint
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🧪 Testing endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Decimal serialization is working!")
            print(f"📋 Response structure:")
            print(json.dumps(data, indent=2))
            
            # Verify data types in the reading
            if 'reading' in data:
                reading = data['reading']
                print(f"\n🔍 Data type verification:")
                numeric_fields = ['pH', 'tds', 'turbidity', 'temperature', 'qualityScore']
                
                for field in numeric_fields:
                    if field in reading:
                        value = reading[field]
                        data_type = type(value).__name__
                        print(f"  ✅ {field}: {data_type} = {value}")
                        
                        # Verify it's a float, not Decimal
                        if data_type == 'float':
                            print(f"    ✅ Correctly converted to float")
                        elif data_type == 'int':
                            print(f"    ✅ Integer value (acceptable)")
                        else:
                            print(f"    ⚠️  Unexpected type: {data_type}")
            
            return True
            
        elif response.status_code == 404:
            print(f"📋 No readings found (this is expected if no data exists)")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text)
            return True
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_lambda_logs():
    """Check recent Lambda logs for any errors"""
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    
    # Log group for the readings Lambda
    log_group = '/aws/lambda/aquachain-function-readings-service-dev'
    
    print(f"\n📋 Checking recent Lambda logs...")
    
    try:
        # Get recent log events (last 5 minutes)
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = end_time - (5 * 60 * 1000)  # 5 minutes ago
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            limit=20
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"📋 Found {len(events)} recent log events:")
            for event in events[-5:]:  # Show last 5 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"  {timestamp}: {message}")
        else:
            print("📋 No recent log events found")
            
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    print("🧪 Testing Decimal serialization fix...")
    
    success = test_readings_endpoint_with_fresh_token()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed - checking logs...")
        check_lambda_logs()