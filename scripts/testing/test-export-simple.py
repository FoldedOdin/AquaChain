#!/usr/bin/env python3
"""
Simple test of the new comprehensive export functionality
"""

import requests
import json
from datetime import datetime

def test_export():
    """Test the export endpoint with a simple request"""
    print("🧪 Testing Comprehensive Export")
    print("=" * 40)
    
    # Use the API Gateway endpoint
    api_base = "https://946twwm7kf.execute-api.ap-south-1.amazonaws.com/dev"
    device_id = "ESP32-001"
    export_url = f"{api_base}/devices/{device_id}/readings/export"
    
    # Test without authentication first to see the structure
    print(f"📡 Testing: {export_url}")
    
    params = {
        'days': 7,
        'format': 'json'
    }
    
    try:
        response = requests.get(export_url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Export successful!")
            
            # Show the structure
            print(f"\n📊 Export Structure:")
            for key in data.keys():
                if isinstance(data[key], dict):
                    print(f"   {key}: {len(data[key])} fields")
                elif isinstance(data[key], list):
                    print(f"   {key}: {len(data[key])} items")
                else:
                    print(f"   {key}: {type(data[key])}")
            
            # Show sample data if available
            if 'sensorData' in data and data['sensorData']:
                print(f"\n📈 Sample Reading:")
                sample = data['sensorData'][0]
                for key, value in sample.items():
                    print(f"   {key}: {value}")
            
        elif response.status_code == 401:
            print("🔐 Authentication required - this is expected")
            print("✅ Export endpoint is working (needs auth)")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_export()