#!/usr/bin/env python3
"""
Add logging to the Lambda function to see exactly what request it receives
"""

import boto3
import json

def add_debug_logging_to_lambda():
    """Add debug logging to see the exact request body"""
    print("🔧 Adding debug logging to Lambda function...")
    
    # We'll create a simple test by invoking the Lambda directly with different payloads
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    test_cases = [
        {
            'name': 'Working credentials (direct test)',
            'event': {
                'httpMethod': 'POST',
                'path': '/api/auth/signin',
                'headers': {
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3000'
                },
                'body': json.dumps({
                    'email': 'leninat259@gmail.com',
                    'password': 'AquaChain123!'
                }),
                'requestContext': {
                    'identity': {'sourceIp': '127.0.0.1'},
                    'requestId': 'test-request-1'
                }
            }
        },
        {
            'name': 'Frontend-style request (with rememberMe)',
            'event': {
                'httpMethod': 'POST',
                'path': '/api/auth/signin',
                'headers': {
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3000',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'body': json.dumps({
                    'email': 'leninat259@gmail.com',
                    'password': 'AquaChain123!',
                    'rememberMe': True
                }),
                'requestContext': {
                    'identity': {'sourceIp': '192.168.1.100'},
                    'requestId': 'test-request-2'
                }
            }
        },
        {
            'name': 'Potential case issue',
            'event': {
                'httpMethod': 'POST',
                'path': '/api/auth/signin',
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'email': 'LENINAT259@GMAIL.COM',
                    'password': 'AquaChain123!'
                }),
                'requestContext': {
                    'identity': {'sourceIp': '127.0.0.1'},
                    'requestId': 'test-request-3'
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName='aquachain-function-auth-service-dev',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_case['event'])
            )
            
            payload = json.loads(response['Payload'].read())
            status_code = payload.get('statusCode', 0)
            
            print(f"   Status: {status_code}")
            
            if status_code == 200:
                print("   ✅ SUCCESS")
                body = json.loads(payload.get('body', '{}'))
                if 'user' in body:
                    print(f"   User: {body['user'].get('email')} ({body['user'].get('role')})")
            else:
                print("   ❌ FAILED")
                body = json.loads(payload.get('body', '{}'))
                print(f"   Error: {body.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def check_recent_lambda_logs():
    """Check recent Lambda logs for any patterns"""
    print("\n🔍 Checking recent Lambda logs for patterns...")
    
    try:
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        import time
        end_time = int(time.time() * 1000)
        start_time = end_time - (5 * 60 * 1000)  # Last 5 minutes
        
        response = logs_client.filter_log_events(
            logGroupName='/aws/lambda/aquachain-function-auth-service-dev',
            startTime=start_time,
            endTime=end_time,
            filterPattern='ERROR'
        )
        
        events = response.get('events', [])
        print(f"✅ Found {len(events)} error events in last 5 minutes")
        
        for event in events[-3:]:  # Last 3 errors
            message = event['message']
            if 'Invalid email or password' in message:
                print(f"\n🚨 Authentication failure detected:")
                print(f"   {message}")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def main():
    """Main function"""
    print("🚀 Debugging Lambda Request Body")
    print("=" * 60)
    
    # Test different request formats
    add_debug_logging_to_lambda()
    
    # Check recent logs
    check_recent_lambda_logs()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Try logging in as technician in browser")
    print("2. Check if any of the test cases above match the failure pattern")
    print("3. Look for differences in request format between working and failing calls")

if __name__ == "__main__":
    main()