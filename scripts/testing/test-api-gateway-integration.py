#!/usr/bin/env python3
"""
Test API Gateway integration to see if it properly forwards requests to Lambda
"""

import requests
import json

def test_cors_preflight():
    """Test CORS preflight request (no auth needed)"""
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print("🔍 Testing CORS preflight (OPTIONS request)")
    
    try:
        response = requests.options(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ CORS preflight successful")
            return True
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_without_auth():
    """Test endpoint without authentication to see what error we get"""
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print("\n🔍 Testing endpoint without authentication")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Expected 401 Unauthorized (auth is working)")
            return True
        elif response.status_code == 500:
            print("❌ Still getting 500 error - API Gateway issue")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_invalid_endpoint():
    """Test an invalid endpoint to see API Gateway behavior"""
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/invalid"
    
    print("\n🔍 Testing invalid endpoint")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 403:
            print("✅ Expected 403 Forbidden (API Gateway working)")
            return True
        else:
            print(f"⚠️  Status: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API Gateway Integration")
    print("="*40)
    
    cors_ok = test_cors_preflight()
    no_auth_ok = test_without_auth()
    invalid_ok = test_invalid_endpoint()
    
    if cors_ok and no_auth_ok and invalid_ok:
        print("\n✅ API GATEWAY INTEGRATION LOOKS GOOD")
        print("The 500 error should be fixed now!")
    else:
        print("\n❌ API GATEWAY INTEGRATION HAS ISSUES")
        print("There may still be configuration problems")