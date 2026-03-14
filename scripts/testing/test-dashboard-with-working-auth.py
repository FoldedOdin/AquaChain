#!/usr/bin/env python3
"""
Test Dashboard Data Flow with Working Authentication
"""

import boto3
import json
import requests
from datetime import datetime

def get_cognito_token():
    """Get a valid Cognito token for testing"""
    
    # Use the admin user we created
    email = "admin@aquachain.com"
    password = "AdminPassword123!"
    
    print(f"🔐 Getting Cognito token for: {email}")
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    
    # Get user pool ID
    user_pools = cognito_client.list_user_pools(MaxResults=10)
    aquachain_pool = None
    
    for pool in user_pools['UserPools']:
        if 'aquachain' in pool['Name'].lower():
            aquachain_pool = pool
            break
    
    if not aquachain_pool:
        print("❌ AquaChain user pool not found")
        return None
    
    user_pool_id = aquachain_pool['Id']
    print(f"📋 User Pool ID: {user_pool_id}")
    
    # Get user pool clients
    clients = cognito_client.list_user_pool_clients(
        UserPoolId=user_pool_id,
        MaxResults=10
    )
    
    if not clients['UserPoolClients']:
        print("❌ No user pool clients found")
        return None
    
    client_id = clients['UserPoolClients'][0]['ClientId']
    print(f"📋 Client ID: {client_id}")
    
    try:
        # Authenticate user
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        if 'AuthenticationResult' in response:
            access_token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            
            print("✅ Authentication successful!")
            return {
                'access_token': access_token,
                'id_token': id_token
            }
        else:
            print(f"❌ Authentication failed: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None

def test_api_with_auth(tokens):
    """Test API endpoints with valid authentication"""
    
    if not tokens:
        print("❌ No valid tokens available")
        return False
    
    print(f"\n🧪 Testing API with authentication")
    print("=" * 50)
    
    # API Gateway URL
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    
    headers = {
        'Authorization': f"Bearer {tokens['id_token']}",
        'Content-Type': 'application/json'
    }
    
    # Test latest reading endpoint
    endpoint = f"{api_url}/api/v1/readings/ESP32-001/latest"
    
    try:
        print(f"📍 Testing: {endpoint}")
        
        response = requests.get(endpoint, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"📦 Response: {json.dumps(data, indent=2)}")
            
            if data.get('success') and data.get('reading'):
                reading = data['reading']
                print(f"\n📊 Reading Data:")
                print(f"   Timestamp: {reading.get('timestamp', 'N/A')}")
                print(f"   pH: {reading.get('pH', 'N/A')}")
                print(f"   Temperature: {reading.get('temperature', 'N/A')}")
                print(f"   WQI: {reading.get('qualityScore', reading.get('wqi', 'N/A'))}")
                return True
            else:
                print(f"❌ No reading data in response")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_device_status_api(tokens):
    """Test device status API"""
    
    if not tokens:
        return False
    
    print(f"\n🧪 Testing Device Status API")
    print("=" * 50)
    
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    
    headers = {
        'Authorization': f"Bearer {tokens['id_token']}",
        'Content-Type': 'application/json'
    }
    
    # Test device status endpoint
    endpoint = f"{api_url}/api/v1/devices"
    
    try:
        print(f"📍 Testing: {endpoint}")
        
        response = requests.get(endpoint, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Device API call successful!")
            print(f"📦 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Device API call failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing device API: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Dashboard Authentication Test")
    print("=" * 60)
    
    # Get authentication tokens
    tokens = get_cognito_token()
    
    if tokens:
        # Test readings API
        readings_work = test_api_with_auth(tokens)
        
        # Test device status API
        device_work = test_device_status_api(tokens)
        
        # Summary
        print(f"\n📋 SUMMARY")
        print("=" * 50)
        print(f"✅ Authentication: {'Success' if tokens else 'Failed'}")
        print(f"✅ Readings API: {'Working' if readings_work else 'Failed'}")
        print(f"✅ Device API: {'Working' if device_work else 'Failed'}")
        
        if readings_work:
            print("\n🎉 API is working with proper authentication!")
            print("💡 The issue is likely in the frontend authentication flow.")
            print("🔧 Check:")
            print("   1. Frontend Cognito configuration")
            print("   2. User pool client settings")
            print("   3. Frontend token handling")
        else:
            print("\n🔧 API still not working - check backend configuration")
    else:
        print("\n❌ Could not get authentication tokens")
        print("🔧 Check Cognito user pool configuration")

if __name__ == "__main__":
    main()