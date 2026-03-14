#!/usr/bin/env python3
"""
Simulate the exact request the frontend makes to identify the issue
"""

import requests
import json
import time

def simulate_frontend_request():
    """Simulate the exact request structure the frontend sends"""
    print("🌐 Simulating exact frontend request...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    # Exact headers that React would send
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000',
        'Pragma': 'no-cache',
        'Referer': 'http://localhost:3000/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Exact payload structure from AuthForms.tsx
    payload = {
        'email': 'leninat259@gmail.com',  # After sanitization (lowercase, trimmed)
        'password': 'AquaChain123!',
        'rememberMe': True,
        'csrfToken': 'mock-csrf-token-12345',
        'recaptchaToken': 'dev-recaptcha-token-' + str(int(time.time() * 1000))
    }
    
    print(f"📋 Request details:")
    print(f"   URL: {url}")
    print(f"   Headers: {json.dumps(headers, indent=2)}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"\n✅ Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   🎉 SUCCESS!")
            data = response.json()
            if 'user' in data:
                user = data['user']
                print(f"   User: {user.get('email')} ({user.get('role')})")
        else:
            print("   ❌ FAILED!")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw response: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False

def test_without_extra_fields():
    """Test without the extra fields that might be causing issues"""
    print("\n🧪 Testing without extra fields...")
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    # Minimal payload - just email and password
    payload = {
        'email': 'leninat259@gmail.com',
        'password': 'AquaChain123!'
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS without extra fields!")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def check_lambda_logs_after_test():
    """Check Lambda logs immediately after our test"""
    print("\n🔍 Checking Lambda logs after test...")
    
    import boto3
    
    try:
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        # Get logs from the last 2 minutes
        end_time = int(time.time() * 1000)
        start_time = end_time - (2 * 60 * 1000)
        
        response = logs_client.filter_log_events(
            logGroupName='/aws/lambda/aquachain-function-auth-service-dev',
            startTime=start_time,
            endTime=end_time
        )
        
        events = response.get('events', [])
        print(f"   Found {len(events)} log events in last 2 minutes")
        
        # Look for our test requests
        for event in events[-5:]:
            message = event['message']
            timestamp = event['timestamp']
            readable_time = time.strftime('%H:%M:%S', time.localtime(timestamp/1000))
            
            if any(keyword in message.lower() for keyword in ['error', 'invalid', 'failed']):
                print(f"   🚨 {readable_time}: {message}")
            elif 'signin' in message.lower() or 'auth' in message.lower():
                print(f"   📋 {readable_time}: {message}")
        
    except Exception as e:
        print(f"   ❌ Error checking logs: {e}")

def main():
    """Main function"""
    print("🚀 Simulating Exact Frontend Request")
    print("=" * 60)
    
    # Test with full frontend payload
    result1 = simulate_frontend_request()
    
    # Test with minimal payload
    result2 = test_without_extra_fields()
    
    # Check logs
    check_lambda_logs_after_test()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    if result1:
        print("✅ Full frontend request: SUCCESS")
    else:
        print("❌ Full frontend request: FAILED")
    
    if result2:
        print("✅ Minimal request: SUCCESS")
    else:
        print("❌ Minimal request: FAILED")
    
    if result1 and result2:
        print("\n🎉 BOTH REQUESTS WORK!")
        print("   The issue might be intermittent or browser-specific")
    elif result2 and not result1:
        print("\n🔍 EXTRA FIELDS CAUSE THE ISSUE!")
        print("   The csrfToken or recaptchaToken might be causing problems")
    else:
        print("\n🔧 BOTH REQUESTS FAIL")
        print("   There's a fundamental issue with the API or authentication")

if __name__ == "__main__":
    main()