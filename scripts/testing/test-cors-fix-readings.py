#!/usr/bin/env python3
"""
Test CORS Fix for Readings API
Verifies that CORS headers are properly configured
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cors_headers(url):
    """Test CORS headers for a given URL"""
    logger.info(f"Testing CORS for: {url}")
    
    try:
        # Test OPTIONS preflight request
        logger.info("🔍 Testing OPTIONS preflight request...")
        options_response = requests.options(url, timeout=10)
        
        print(f"OPTIONS Status Code: {options_response.status_code}")
        print("OPTIONS Headers:")
        for header, value in options_response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        # Test GET request
        logger.info("🔍 Testing GET request...")
        get_response = requests.get(url, timeout=10)
        
        print(f"\nGET Status Code: {get_response.status_code}")
        print("GET Headers:")
        for header, value in get_response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        # Check required CORS headers
        required_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        missing_headers = []
        for header in required_headers:
            if header not in get_response.headers:
                missing_headers.append(header)
        
        if missing_headers:
            print(f"\n❌ Missing CORS headers: {missing_headers}")
            return False
        else:
            print(f"\n✅ All required CORS headers present!")
            
            # Check if Access-Control-Allow-Origin allows all origins
            origin_header = get_response.headers.get('Access-Control-Allow-Origin')
            if origin_header == '*':
                print("✅ Access-Control-Allow-Origin allows all origins")
            else:
                print(f"⚠️ Access-Control-Allow-Origin: {origin_header}")
            
            return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_browser_simulation():
    """Simulate browser CORS preflight + actual request"""
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print("🌐 Simulating browser CORS flow...")
    print(f"URL: {url}")
    
    # Simulate preflight request (what browser sends before actual request)
    preflight_headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'content-type'
    }
    
    try:
        print("\n1️⃣ Sending preflight OPTIONS request...")
        preflight_response = requests.options(url, headers=preflight_headers, timeout=10)
        
        print(f"Preflight Status: {preflight_response.status_code}")
        
        # Check preflight response
        allow_origin = preflight_response.headers.get('Access-Control-Allow-Origin')
        allow_methods = preflight_response.headers.get('Access-Control-Allow-Methods')
        allow_headers = preflight_response.headers.get('Access-Control-Allow-Headers')
        
        print(f"Allow-Origin: {allow_origin}")
        print(f"Allow-Methods: {allow_methods}")
        print(f"Allow-Headers: {allow_headers}")
        
        if preflight_response.status_code != 200:
            print("❌ Preflight failed - browser would block the request")
            return False
        
        if not allow_origin or allow_origin not in ['*', 'http://localhost:3000']:
            print("❌ Origin not allowed - browser would block the request")
            return False
        
        print("✅ Preflight successful")
        
        # Simulate actual request
        print("\n2️⃣ Sending actual GET request...")
        actual_headers = {
            'Origin': 'http://localhost:3000'
        }
        
        actual_response = requests.get(url, headers=actual_headers, timeout=10)
        
        print(f"Actual Status: {actual_response.status_code}")
        
        # Check actual response headers
        response_origin = actual_response.headers.get('Access-Control-Allow-Origin')
        print(f"Response Allow-Origin: {response_origin}")
        
        if not response_origin or response_origin not in ['*', 'http://localhost:3000']:
            print("❌ Response missing CORS headers - browser would block")
            return False
        
        print("✅ Actual request successful")
        
        # Try to parse response
        try:
            response_data = actual_response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {actual_response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser simulation failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing CORS Configuration for AquaChain Readings API")
    print("=" * 60)
    
    # Test the specific URL from the error
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    # Test basic CORS headers
    cors_ok = test_cors_headers(url)
    
    print("\n" + "=" * 60)
    
    # Test browser simulation
    browser_ok = test_browser_simulation()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    
    if cors_ok and browser_ok:
        print("✅ CORS is properly configured!")
        print("🎉 Your React frontend should now work without CORS errors")
    elif cors_ok:
        print("⚠️ Basic CORS headers present but browser simulation failed")
        print("🔧 May need additional configuration")
    else:
        print("❌ CORS is not properly configured")
        print("🔧 Run the CORS fix script: python scripts/deployment/fix-cors-comprehensive-readings.py")

if __name__ == "__main__":
    main()