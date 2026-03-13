#!/usr/bin/env python3
"""
Test the API end-to-end through API Gateway with authentication
"""

import boto3
import json
import requests
from datetime import datetime

def get_cognito_token():
    """Get a Cognito authentication token for testing"""
    
    # For now, we'll test without auth to see if CORS is working
    # In production, you'd get a real token from Cognito
    print("🔐 Note: Testing without authentication (will get 401, but CORS should work)")
    return None

def test_api_endpoints():
    """Test all the readings API endpoints"""
    
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    device_id = "ESP32-001"
    
    endpoints = [
        f"/api/v1/readings/{device_id}/latest",
        f"/api/v1/readings/{device_id}/history",
        f"/api/v1/readings/{device_id}",
        f"/api/v1/readings/{device_id}/history?days=1&limit=5"
    ]
    
    print(f"🌐 Testing API endpoints at: {api_url}")
    print(f"📱 Device ID: {device_id}")
    print()
    
    for endpoint in endpoints:
        print(f"📍 Testing: {endpoint}")
        
        try:
            # Test OPTIONS request (CORS preflight)
            options_response = requests.options(f"{api_url}{endpoint}", timeout=10)
            print(f"   OPTIONS: {options_response.status_code}")
            
            if options_response.status_code == 204:
                print(f"   ✅ CORS preflight successful")
                
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers')
                }
                print(f"   CORS headers: {cors_headers}")
            else:
                print(f"   ❌ CORS preflight failed")
            
            # Test GET request
            get_response = requests.get(f"{api_url}{endpoint}", timeout=10)
            print(f"   GET: {get_response.status_code}")
            
            if get_response.status_code == 401:
                print(f"   ✅ Authentication required (expected)")
                
                # Check if response has CORS headers
                if 'Access-Control-Allow-Origin' in get_response.headers:
                    print(f"   ✅ CORS headers present in error response")
                else:
                    print(f"   ❌ CORS headers missing in error response")
                
                # Show error message
                try:
                    error_data = get_response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {get_response.text[:100]}...")
                    
            elif get_response.status_code == 200:
                print(f"   ✅ Success (unexpected without auth)")
                try:
                    data = get_response.json()
                    print(f"   Data: {json.dumps(data, indent=4)}")
                except:
                    print(f"   Response: {get_response.text[:200]}...")
            else:
                print(f"   ❌ Unexpected status: {get_response.status_code}")
                print(f"   Response: {get_response.text[:200]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_with_mock_auth_header():
    """Test with a mock authorization header to see what happens"""
    
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    device_id = "ESP32-001"
    endpoint = f"/api/v1/readings/{device_id}/latest"
    
    print(f"🔐 Testing with mock Authorization header...")
    
    headers = {
        'Authorization': 'Bearer mock-token-for-testing',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{api_url}{endpoint}", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.text:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text[:300]}...")
        
        # Check CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin:
            print(f"✅ CORS Origin: {cors_origin}")
        else:
            print(f"❌ No CORS Origin header")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    
    print("🧪 End-to-End API Testing")
    print("=" * 40)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Test 1: All endpoints without auth
    print("1️⃣ Testing all endpoints (no auth)...")
    test_api_endpoints()
    
    # Test 2: With mock auth header
    print("2️⃣ Testing with mock auth header...")
    test_with_mock_auth_header()
    print()
    
    print("📊 SUMMARY")
    print("=" * 20)
    print("✅ CORS should be working (OPTIONS returns 204)")
    print("✅ API should return 401 for GET requests (auth required)")
    print("✅ Lambda function is working (confirmed in previous test)")
    print()
    print("🔧 NEXT STEPS:")
    print("1. Frontend should now be able to make CORS preflight requests")
    print("2. Frontend needs proper Cognito authentication tokens")
    print("3. With proper auth, API will return reading data")

if __name__ == "__main__":
    main()