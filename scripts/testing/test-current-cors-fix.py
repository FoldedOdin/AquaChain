#!/usr/bin/env python3
"""
Test the current CORS fix to see if it worked.
"""

import requests
import json

def test_endpoint():
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print("🧪 Testing CORS fix...")
    print(f"URL: {url}")
    
    # Test 1: OPTIONS request (preflight)
    print("\n1️⃣ Testing OPTIONS request (CORS preflight)...")
    try:
        response = requests.options(
            url,
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization,Content-Type'
            }
        )
        
        print(f"   Status: {response.status_code}")
        print("   Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"     {header}: {value}")
        
        if response.status_code == 200:
            print("   ✅ OPTIONS request successful")
        else:
            print("   ❌ OPTIONS request failed")
            
    except Exception as e:
        print(f"   ❌ OPTIONS request error: {e}")
    
    # Test 2: GET request without auth
    print("\n2️⃣ Testing GET request without auth...")
    try:
        response = requests.get(
            url,
            headers={
                'Origin': 'http://localhost:3000'
            }
        )
        
        print(f"   Status: {response.status_code}")
        print("   Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"     {header}: {value}")
        
        if 'access-control-allow-origin' in response.headers:
            print("   ✅ CORS headers present")
        else:
            print("   ❌ CORS headers missing")
            
        print(f"   Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"   ❌ GET request error: {e}")
    
    # Test 3: Check if the endpoint exists at all
    print("\n3️⃣ Testing different endpoint paths...")
    
    test_urls = [
        "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/device-readings",
        "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings",
        "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/readings/ESP32-001/latest"
    ]
    
    for test_url in test_urls:
        try:
            response = requests.get(test_url, timeout=5)
            print(f"   {test_url}: {response.status_code}")
            if response.status_code != 404:
                print(f"     Response: {response.text[:100]}...")
        except Exception as e:
            print(f"   {test_url}: Error - {e}")

if __name__ == "__main__":
    test_endpoint()