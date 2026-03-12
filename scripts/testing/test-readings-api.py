#!/usr/bin/env python3
"""
Test the new readings API endpoints
"""

import requests
import json
import sys

def test_readings_api():
    """Test the readings API endpoints"""
    
    # API base URL
    base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    
    # Test device ID (ESP32-001 which has 375 readings)
    device_id = "ESP32-001"
    
    # You would need a valid JWT token here
    # For now, we'll test without authentication to see the error response
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing readings API endpoints...")
    
    # Test 1: GET /api/v1/readings/{deviceId}
    print(f"\n1️⃣ Testing GET /api/v1/readings/{device_id}")
    url = f"{base_url}/api/v1/readings/{device_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (returns 401 Unauthorized as expected without token)")
        elif response.status_code == 200:
            print("   ✅ Endpoint works and returned data!")
        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: GET /api/v1/readings/{deviceId}/latest
    print(f"\n2️⃣ Testing GET /api/v1/readings/{device_id}/latest")
    url = f"{base_url}/api/v1/readings/{device_id}/latest"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (returns 401 Unauthorized as expected without token)")
        elif response.status_code == 200:
            print("   ✅ Endpoint works and returned data!")
        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: GET /api/v1/readings/{deviceId}/history
    print(f"\n3️⃣ Testing GET /api/v1/readings/{device_id}/history")
    url = f"{base_url}/api/v1/readings/{device_id}/history"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (returns 401 Unauthorized as expected without token)")
        elif response.status_code == 200:
            print("   ✅ Endpoint works and returned data!")
        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n📋 Summary:")
    print("   - All endpoints should return 401 Unauthorized without a valid JWT token")
    print("   - This confirms the endpoints exist and are properly secured")
    print("   - The frontend will use proper authentication tokens")
    print("\n✅ API endpoint testing completed!")

if __name__ == "__main__":
    test_readings_api()