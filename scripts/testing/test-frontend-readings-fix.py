#!/usr/bin/env python3
"""
Test if the frontend readings fix is working
"""

import requests
import json

def test_frontend_readings_fix():
    """Test the frontend readings fix"""
    try:
        print("🧪 Testing Frontend Readings Fix")
        print("=" * 35)
        
        # Test the exact endpoint the frontend is now using
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        latest_url = f"{base_url}/api/device-readings/ESP32-001/latest"
        
        print(f"\n📊 Testing latest endpoint (what frontend uses):")
        print(f"   URL: {latest_url}")
        
        # Test without auth (since we set it to NONE)
        response = requests.get(latest_url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS!")
            
            try:
                data = response.json()
                print(f"   📋 Raw response: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    reading = data.get('reading', {})
                    print(f"\n   📊 Reading data:")
                    print(f"     pH: {reading.get('pH')}")
                    print(f"     Temperature: {reading.get('temperature')}°C")
                    print(f"     TDS: {reading.get('tds')} ppm")
                    print(f"     Turbidity: {reading.get('turbidity')} NTU")
                    print(f"     Timestamp: {reading.get('timestamp')}")
                    
                    print(f"\n   ✅ This data should appear in the dashboard!")
                    return True
                else:
                    print(f"   ❌ Response indicates failure")
                    return False
                    
            except Exception as parse_error:
                print(f"   ❌ JSON parse error: {parse_error}")
                print(f"   Raw text: {response.text}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing: {e}")
        return False

def check_device_status():
    """Check if device status might be affecting readings display"""
    try:
        print(f"\n🔍 Checking device status...")
        
        # Check if there's a devices endpoint
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        devices_url = f"{base_url}/api/devices"
        
        print(f"   Testing devices endpoint: {devices_url}")
        
        response = requests.get(devices_url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📋 Devices data available")
                if isinstance(data, list):
                    print(f"   📊 Found {len(data)} devices")
                    for device in data[:3]:  # Show first 3
                        device_id = device.get('deviceId', 'Unknown')
                        status = device.get('status', 'Unknown')
                        print(f"     - {device_id}: {status}")
            except:
                print(f"   ⚠️ Could not parse devices response")
        else:
            print(f"   ❌ Devices endpoint error: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error checking device status: {e}")

def main():
    # Test the readings endpoint
    readings_work = test_frontend_readings_fix()
    
    # Check device status
    check_device_status()
    
    print(f"\n" + "=" * 35)
    print(f"DIAGNOSIS:")
    
    if readings_work:
        print(f"✅ The readings API is working correctly")
        print(f"✅ Real sensor data is available (pH, temperature, etc.)")
        print(f"✅ The frontend should be able to fetch this data")
        
        print(f"\n💡 If readings still don't appear in dashboard:")
        print(f"   1. Check browser console for JavaScript errors")
        print(f"   2. Check if authentication is required")
        print(f"   3. Verify the frontend is calling the right endpoint")
        print(f"   4. Try hard refresh (Ctrl+F5) to clear cache")
        
        print(f"\n🔧 Next steps:")
        print(f"   1. Refresh your dashboard")
        print(f"   2. Check browser developer tools (F12)")
        print(f"   3. Look for any error messages in console")
    else:
        print(f"❌ The readings API is not working")
        print(f"   Need to investigate API Gateway configuration")

if __name__ == "__main__":
    main()