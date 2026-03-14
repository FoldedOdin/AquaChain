#!/usr/bin/env python3
"""
Test current endpoints status
"""

import requests
import json

def test_current_endpoints():
    """Test current endpoints status"""
    try:
        print("Testing Current Endpoints Status")
        print("=" * 35)
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        # Test the endpoints we know about
        endpoints = [
            ("Original Latest (should fail)", f"{base_url}/api/v1/readings/ESP32-001/latest"),
            ("Original History (should fail)", f"{base_url}/api/v1/readings/ESP32-001/history"),
            ("New Latest (should work)", f"{base_url}/api/device-readings/ESP32-001/latest"),
            ("New History (might fail)", f"{base_url}/api/device-readings/ESP32-001/history")
        ]
        
        working_endpoints = []
        
        for name, url in endpoints:
            print(f"\n{name}:")
            print(f"  URL: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  Result: SUCCESS!")
                    working_endpoints.append(url)
                    
                    try:
                        data = response.json()
                        if data.get('success'):
                            if 'reading' in data:
                                reading = data['reading']
                                print(f"    pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                            elif 'readings' in data:
                                readings = data['readings']
                                print(f"    Found {len(readings)} readings")
                    except:
                        pass
                        
                elif response.status_code == 403:
                    print(f"  Result: FORBIDDEN (endpoint exists but no auth/integration)")
                elif response.status_code == 404:
                    print(f"  Result: NOT FOUND (endpoint doesn't exist)")
                else:
                    print(f"  Result: ERROR ({response.status_code})")
                    print(f"  Message: {response.text[:100]}")
                
            except Exception as e:
                print(f"  Result: REQUEST ERROR - {e}")
        
        print(f"\n" + "=" * 35)
        print(f"SUMMARY:")
        print(f"Working endpoints: {len(working_endpoints)}")
        
        for url in working_endpoints:
            print(f"  - {url}")
        
        if len(working_endpoints) >= 1:
            print(f"\nGOOD NEWS: At least one endpoint is working!")
            print(f"The CORS issue is partially resolved.")
            
            if len(working_endpoints) == 1:
                print(f"\nNEXT STEP: Create the missing history endpoint")
            else:
                print(f"\nSUCCESS: Both endpoints are working!")
                print(f"The CORS issue should be completely resolved!")
        else:
            print(f"\nISSUE: No endpoints are working")
            print(f"Need to investigate further")
        
        return len(working_endpoints)
        
    except Exception as e:
        print(f"Error testing endpoints: {e}")
        return 0

if __name__ == "__main__":
    test_current_endpoints()