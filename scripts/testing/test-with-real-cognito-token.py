#!/usr/bin/env python3
"""
Test with real Cognito token to isolate backend vs frontend issues
"""

import boto3
import requests
import json
import subprocess
import time

def get_fresh_cognito_token():
    """Get a fresh Cognito token for testing"""
    
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    
    # Use existing user credentials
    username = "karthikkpradeep123@gmail.com"
    password = "TempPassword123!"  # You may need to update this
    
    user_pool_id = "ap-south-1_QUDl7hG8u"
    client_id = "692o9a3pjudl1vudfgqpr5nuln"
    
    try:
        # Try to authenticate
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print(f"✅ Got fresh Cognito token")
        return access_token
        
    except Exception as e:
        print(f"❌ Could not get fresh token: {e}")
        print(f"ℹ️  Using the token from your browser network trace...")
        
        # Use the token from the browser (may be expired)
        browser_token = "eyJraWQiOiJiWUJ3RGVsWVlkYmFIeVwvcUtlWXJPbDJlUVk2d1hIODVlM00zOFFBMEloWT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1MWEzZWQ0YS1jMGIxLTcwZTgtYTdkNy0xOWQ3Y2EwMzVmZTAiLCJjb2duaXRvOmdyb3VwcyI6WyJjb25zdW1lcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoLTFfUVVEbDdoRzh1IiwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjUxYTNlZDRhLWMwYjEtNzBlOC1hN2Q3LTE5ZDdjYTAzNWZlMCIsImdpdmVuX25hbWUiOiJLYXJ0aGlrIiwib3JpZ2luX2p0aSI6ImFkNWE4MDlk"
        return browser_token

def test_with_curl(token):
    """Test using curl command to isolate backend issues"""
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print(f"\n🧪 Testing with curl...")
    print(f"🔗 URL: {url}")
    print(f"🔑 Token: {token[:50]}...")
    
    # Use curl command
    curl_command = [
        'curl', '-s', '-w', '\\nHTTP_CODE:%{http_code}\\n',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        url
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
        
        output = result.stdout
        lines = output.strip().split('\n')
        
        # Extract HTTP code
        http_code = None
        response_body = []
        
        for line in lines:
            if line.startswith('HTTP_CODE:'):
                http_code = int(line.split(':')[1])
            else:
                response_body.append(line)
        
        response_text = '\n'.join(response_body)
        
        print(f"📊 Curl Status Code: {http_code}")
        print(f"📋 Curl Response:")
        print(response_text)
        
        if http_code == 500:
            print(f"\n❌ CURL ALSO RETURNS 500!")
            print(f"✅ This confirms the issue is in the BACKEND (Lambda/Cognito)")
            print(f"✅ NOT a frontend issue")
            return False, "backend"
            
        elif http_code == 401:
            print(f"\n✅ CURL RETURNS 401 (Unauthorized)")
            print(f"ℹ️  This suggests the token is expired or invalid")
            print(f"ℹ️  But the backend is working correctly")
            return True, "token_expired"
            
        elif http_code == 200:
            print(f"\n🎉 CURL RETURNS 200 SUCCESS!")
            print(f"✅ Backend is working perfectly")
            try:
                data = json.loads(response_text)
                print(f"📋 Response data: {json.dumps(data, indent=2)}")
            except:
                print(f"📋 Response text: {response_text}")
            return True, "success"
            
        else:
            print(f"\n📋 Unexpected status code: {http_code}")
            return True, f"unexpected_{http_code}"
        
    except subprocess.TimeoutExpired:
        print(f"❌ Curl command timed out")
        return False, "timeout"
    except Exception as e:
        print(f"❌ Curl command failed: {e}")
        return False, "error"

def test_with_requests(token):
    """Test using Python requests library"""
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    print(f"\n🧪 Testing with Python requests...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📊 Requests Status Code: {response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'access-control-allow-origin', 'x-amzn-errortype', 'x-amzn-requestid']:
                print(f"  {key}: {value}")
        
        print(f"📋 Response Body:")
        try:
            if response.text:
                data = response.json()
                print(json.dumps(data, indent=2))
        except:
            print(response.text)
        
        return response.status_code, response.text
        
    except Exception as e:
        print(f"❌ Requests failed: {e}")
        return None, str(e)

def check_cloudwatch_logs_for_errors():
    """Check CloudWatch logs for any Lambda errors"""
    
    print(f"\n📋 Checking CloudWatch logs for Lambda errors...")
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    log_group = '/aws/lambda/aquachain-function-readings-service-dev'
    
    try:
        # Get recent log events (last 10 minutes)
        end_time = int(time.time() * 1000)
        start_time = end_time - (10 * 60 * 1000)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            limit=20
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"📋 Recent log events ({len(events)} found):")
            
            error_found = False
            for event in events:
                message = event['message'].strip()
                timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
                
                # Look for errors, exceptions, or important info
                if any(keyword in message.lower() for keyword in ['error', 'exception', 'traceback', 'failed', 'user info', 'authorizer keys']):
                    print(f"  {timestamp}: {message}")
                    if 'error' in message.lower() or 'exception' in message.lower():
                        error_found = True
            
            return error_found
        else:
            print(f"📋 No recent log events found")
            return False
        
    except Exception as e:
        print(f"⚠️  Could not check logs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing with real Cognito token to isolate backend vs frontend issues...")
    
    # Step 1: Get a token
    token = get_fresh_cognito_token()
    
    # Step 2: Test with curl (most reliable)
    curl_success, curl_result = test_with_curl(token)
    
    # Step 3: Test with requests library
    requests_status, requests_body = test_with_requests(token)
    
    # Step 4: Check logs for errors
    errors_in_logs = check_cloudwatch_logs_for_errors()
    
    # Step 5: Analysis
    print(f"\n" + "="*70)
    print("ANALYSIS:")
    print("="*70)
    
    if curl_result == "backend":
        print(f"❌ BACKEND ISSUE CONFIRMED")
        print(f"   Both curl and browser return 500")
        print(f"   The problem is in Lambda or Cognito authorizer")
        print(f"   Check CloudWatch logs for Lambda errors")
        
    elif curl_result == "token_expired":
        print(f"✅ BACKEND IS WORKING")
        print(f"   Curl returns 401 (token expired)")
        print(f"   If browser returns 500, it's a frontend issue")
        print(f"   Try refreshing the browser token")
        
    elif curl_result == "success":
        print(f"🎉 EVERYTHING IS WORKING!")
        print(f"   Curl returns 200 success")
        print(f"   If browser still shows 500, it's a frontend caching issue")
        print(f"   Try hard refresh (Ctrl+F5) in browser")
        
    else:
        print(f"📋 Mixed results - need more investigation")
        print(f"   Curl result: {curl_result}")
        print(f"   Requests status: {requests_status}")
    
    if errors_in_logs:
        print(f"\n⚠️  ERRORS FOUND IN LAMBDA LOGS")
        print(f"   Check the log output above for specific errors")
        print(f"   This confirms a Lambda execution issue")
    else:
        print(f"\n✅ No errors in Lambda logs")
        print(f"   Lambda is executing without exceptions")
    
    print(f"\n" + "="*70)
    print("NEXT STEPS:")
    if curl_result == "backend":
        print("1. Check CloudWatch logs for Lambda errors")
        print("2. Look for Cognito authorizer structure issues")
        print("3. Fix Lambda code to handle authorizer safely")
    elif curl_result == "token_expired":
        print("1. Get a fresh token from browser login")
        print("2. Test again with the new token")
        print("3. If still 500 in browser, check frontend code")
    else:
        print("1. Hard refresh browser (Ctrl+F5)")
        print("2. Check browser console for errors")
        print("3. Verify frontend is using correct API endpoint")
    print("="*70)