#!/usr/bin/env python3
"""
Test the fixed readings endpoint to verify the 500 error is resolved
"""

import requests
import json
import boto3
import sys

def get_fresh_token():
    """Get a fresh Cognito JWT token"""
    try:
        cognito = boto3.client('cognito-idp', region_name='ap-south-1')
        
        # Use the admin user credentials
        response = cognito.admin_initiate_auth(
            UserPoolId='ap-south-1_QUDl7hG8u',
            ClientId='692o9a3pjudl1vudfgqpr5nuln',
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': 'admin@aquachain.com',
                'PASSWORD': 'TempPassword123!'
            }
        )
        
        return response['AuthenticationResult']['AccessToken']
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def test_readings_endpoint():
    """Test the readings endpoint with proper authentication"""
    
    # Get fresh token
    token = get_fresh_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    print("✅ Got authentication token")
    
    # Test the endpoint
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 Testing endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ SUCCESS: Got valid JSON response")
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
                return False
        
        elif response.status_code == 404:
            print("⚠️  404 Not Found - This is expected if no readings exist")
            try:
                data = response.json()
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                return True  # 404 with proper JSON is success
            except json.JSONDecodeError:
                print(f"❌ 404 but invalid JSON: {response.text}")
                return False
        
        elif response.status_code == 500:
            print("❌ STILL GETTING 500 ERROR")
            print(f"Response: {response.text}")
            return False
        
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_with_curl():
    """Also test with curl command for comparison"""
    token = get_fresh_token()
    if not token:
        return
    
    print("\n" + "="*50)
    print("🔧 CURL TEST COMMAND:")
    print("="*50)
    
    curl_command = f'''curl -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" \\
     -v \\
     "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"'''
    
    print(curl_command)
    print("\nRun this command in your terminal to test manually")

if __name__ == "__main__":
    print("🧪 Testing Fixed Readings Endpoint")
    print("="*40)
    
    success = test_readings_endpoint()
    
    if success:
        print("\n✅ ENDPOINT TEST PASSED")
        print("The 500 error has been fixed!")
    else:
        print("\n❌ ENDPOINT TEST FAILED")
        print("The 500 error still exists")
    
    test_with_curl()
    
    sys.exit(0 if success else 1)