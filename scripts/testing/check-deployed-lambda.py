#!/usr/bin/env python3
"""
Check Deployed Lambda Function

This script checks what's actually deployed in the technician tasks Lambda function
and compares it with what we expect.
"""

import boto3
import json
import zipfile
import tempfile
import os

def download_and_inspect_lambda():
    """Download and inspect the deployed Lambda function"""
    try:
        lambda_client = boto3.client('lambda')
        
        function_name = 'aquachain-function-technician-tasks-dev'
        
        print(f"🔍 Inspecting deployed Lambda function: {function_name}")
        
        # Get function configuration
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print(f"✅ Function Configuration:")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Handler: {config['Handler']}")
        print(f"   Last Modified: {config['LastModified']}")
        print(f"   Code Size: {config['CodeSize']} bytes")
        print(f"   Timeout: {config['Timeout']} seconds")
        print(f"   Memory: {config['MemorySize']} MB")
        
        # Check environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        print(f"   Environment Variables ({len(env_vars)}):")
        for key, value in env_vars.items():
            print(f"     {key}: {value}")
        
        # Get function code URL
        function_info = lambda_client.get_function(FunctionName=function_name)
        code_location = function_info['Code']['Location']
        
        print(f"\n📦 Code Location: {code_location[:100]}...")
        
        return config
        
    except Exception as e:
        print(f"❌ Error inspecting Lambda function: {e}")
        return None

def test_lambda_with_different_payloads():
    """Test the Lambda function with different payload formats"""
    try:
        lambda_client = boto3.client('lambda')
        function_name = 'aquachain-function-technician-tasks-dev'
        
        print(f"🧪 Testing Lambda function with different payloads...")
        
        # Test payload 1: Minimal
        test_payloads = [
            {
                "name": "Minimal payload",
                "payload": {
                    "httpMethod": "GET",
                    "path": "/api/v1/technician/tasks"
                }
            },
            {
                "name": "With authorization context",
                "payload": {
                    "httpMethod": "GET",
                    "path": "/api/v1/technician/tasks",
                    "requestContext": {
                        "authorizer": {
                            "claims": {
                                "sub": "31333d7a-7031-703b-2e21-966a49444222",
                                "email": "leninat259@gmail.com"
                            }
                        }
                    }
                }
            },
            {
                "name": "Direct user info",
                "payload": {
                    "httpMethod": "GET",
                    "path": "/api/v1/technician/tasks",
                    "userId": "31333d7a-7031-703b-2e21-966a49444222",
                    "userRole": "technician"
                }
            }
        ]
        
        for test in test_payloads:
            print(f"\n   🧪 Testing: {test['name']}")
            
            try:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test['payload'])
                )
                
                payload = json.loads(response['Payload'].read())
                
                print(f"      Status Code: {payload.get('statusCode', 'N/A')}")
                
                if 'body' in payload:
                    try:
                        body = json.loads(payload['body'])
                        if 'tasks' in body:
                            print(f"      ✅ Tasks: {len(body['tasks'])}")
                        elif 'error' in body:
                            print(f"      ❌ Error: {body['error']}")
                        else:
                            print(f"      📋 Response keys: {list(body.keys())}")
                    except:
                        print(f"      📋 Raw body: {payload['body'][:100]}...")
                
                if 'errorMessage' in payload:
                    print(f"      ❌ Lambda Error: {payload['errorMessage']}")
                    
            except Exception as e:
                print(f"      ❌ Test failed: {e}")
        
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")

def check_lambda_logs_detailed():
    """Check Lambda logs in detail"""
    try:
        logs_client = boto3.client('logs')
        log_group = '/aws/lambda/aquachain-function-technician-tasks-dev'
        
        print(f"🔍 Checking detailed Lambda logs...")
        
        # Get the most recent log stream
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams_response.get('logStreams'):
            print(f"   ❌ No log streams found")
            return
        
        latest_stream = streams_response['logStreams'][0]
        stream_name = latest_stream['logStreamName']
        
        print(f"   📋 Latest stream: {stream_name}")
        
        # Get recent events
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=20,
            startFromHead=False
        )
        
        events = events_response.get('events', [])
        print(f"   📋 Recent events: {len(events)}")
        
        for event in events[-10:]:  # Last 10 events
            timestamp = event['timestamp']
            message = event['message'].strip()
            print(f"      {timestamp}: {message}")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def main():
    """Main function"""
    print("🚀 Checking Deployed Lambda Function")
    print("=" * 60)
    
    # Step 1: Inspect deployed function
    print("\n1. FUNCTION INSPECTION")
    print("-" * 30)
    config = download_and_inspect_lambda()
    
    # Step 2: Test with different payloads
    print("\n2. PAYLOAD TESTING")
    print("-" * 30)
    test_lambda_with_different_payloads()
    
    # Step 3: Check logs
    print("\n3. LOG ANALYSIS")
    print("-" * 30)
    check_lambda_logs_detailed()
    
    # Analysis
    print("\n" + "=" * 60)
    print("📊 ANALYSIS")
    print("=" * 60)
    
    if config:
        print("✅ Lambda function is deployed and accessible")
        
        # Check handler
        expected_handler = "lambda_function.lambda_handler"
        actual_handler = config.get('Handler', '')
        
        if actual_handler == expected_handler:
            print(f"✅ Handler is correct: {actual_handler}")
        else:
            print(f"❌ Handler mismatch:")
            print(f"   Expected: {expected_handler}")
            print(f"   Actual: {actual_handler}")
        
        # Check environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        required_vars = ['SERVICE_REQUESTS_TABLE', 'USERS_TABLE']
        
        for var in required_vars:
            if var in env_vars:
                print(f"✅ Environment variable {var}: {env_vars[var]}")
            else:
                print(f"❌ Missing environment variable: {var}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"1. If handler is wrong, redeploy the correct function")
    print(f"2. If environment variables are missing, update function config")
    print(f"3. Check if the function code matches expected logic")
    print(f"4. Verify authentication handling in the function")

if __name__ == "__main__":
    main()