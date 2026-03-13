#!/usr/bin/env python3
"""
Test the /latest endpoint specifically
"""

import requests
import sys

def test_latest_endpoint():
    """Test the /latest endpoint CORS"""
    
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    endpoint = "/api/v1/readings/ESP32-001/latest"
    
    print("🧪 Testing /latest endpoint CORS")
    print("=" * 40)
    
    # Test OPTIONS (preflight)
    print("🔍 Testing OPTIONS preflight...")
    try:
        response = requests.options(
            f"{api_url}{endpoint}",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization,Content-Type'
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print("CORS Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if response.status_code == 204:
            print("✅ OPTIONS preflight PASSED!")
        else:
            print("❌ OPTIONS preflight FAILED!")
            
    except Exception as e:
        print(f"❌ OPTIONS request failed: {e}")
    
    # Test actual GET request
    print("\n🔍 Testing GET request...")
    try:
        response = requests.get(
            f"{api_url}{endpoint}",
            headers={
                'Origin': 'http://localhost:3000',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print("CORS Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ CORS headers present in GET response!")
        else:
            print("❌ Missing CORS headers in GET response!")
            
    except Exception as e:
        print(f"❌ GET request failed: {e}")

if __name__ == "__main__":
    test_latest_endpoint()