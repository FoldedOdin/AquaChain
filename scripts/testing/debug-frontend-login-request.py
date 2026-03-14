#!/usr/bin/env python3
"""
Debug the exact request the frontend is making vs what works
"""

import json
import time
import boto3

def get_recent_auth_logs():
    """Get recent auth service logs to see what requests are failing"""
    print("🔍 Checking recent auth service logs...")
    
    try:
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        # Get logs from the last 10 minutes
        end_time = int(time.time() * 1000)
        start_time = end_time - (10 * 60 * 1000)  # 10 minutes ago
        
        response = logs_client.filter_log_events(
            logGroupName='/aws/lambda/aquachain-function-auth-service-dev',
            startTime=start_time,
            endTime=end_time
        )
        
        events = response.get('events', [])
        print(f"✅ Found {len(events)} log events in last 10 minutes")
        
        # Look for recent requests
        for event in events[-10:]:  # Last 10 events
            message = event['message']
            timestamp = event['timestamp']
            
            # Convert timestamp to readable format
            readable_time = time.strftime('%H:%M:%S', time.localtime(timestamp/1000))
            
            print(f"\n📋 {readable_time}: {message}")
            
            # Look for specific patterns
            if 'signin' in message.lower():
                print("   🔍 This is a signin request")
            if 'error' in message.lower():
                print("   ❌ This is an error")
            if 'invalid email or password' in message.lower():
                print("   🚨 Authentication failure detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting logs: {e}")
        return False

def test_different_request_formats():
    """Test different ways the request might be formatted"""
    print("\n🧪 Testing different request formats...")
    
    import requests
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    # Test cases that might match what frontend is doing
    test_cases = [
        {
            'name': 'Standard format (works)',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'With extra fields (frontend might add)',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'AquaChain123!',
                'rememberMe': True
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'With Origin header (CORS)',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        },
        {
            'name': 'Case sensitive email test',
            'payload': {
                'email': 'LENINAT259@GMAIL.COM',
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                url, 
                json=test_case['payload'],
                headers=test_case['headers'],
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS")
            else:
                print(f"   ❌ FAILED: {response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def main():
    """Main function"""
    print("🚀 Debugging Frontend Login Request")
    print("=" * 60)
    
    # First check recent logs
    get_recent_auth_logs()
    
    # Then test different formats
    test_different_request_formats()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Try logging in as technician in browser")
    print("2. Immediately run this script to see the failed request")
    print("3. Compare the failed request format with working ones")
    print("4. Check if frontend is sending extra fields or wrong format")

if __name__ == "__main__":
    main()