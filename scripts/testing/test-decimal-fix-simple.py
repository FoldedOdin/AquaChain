#!/usr/bin/env python3
"""
Simple test for Decimal serialization fix using browser token
"""

import requests
import json

def test_with_browser_token():
    """Test using the token from your browser"""
    
    # Use the token from your browser (you can update this)
    # This is the token from your network trace (might be expired)
    token = "eyJraWQiOiJiWUJ3RGVsWVlkYmFIeVwvcUtlWXJPbDJlUVk2d1hIODVlM00zOFFBMEloWT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1MWEzZWQ0YS1jMGIxLTcwZTgtYTdkNy0xOWQ3Y2EwMzVmZTAiLCJjb2duaXRvOmdyb3VwcyI6WyJjb25zdW1lcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoLTFfUVVEbDdoRzh1IiwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjUxYTNlZDRhLWMwYjEtNzBlOC1hN2Q3LTE5ZDdjYTAzNWZlMCIsImdpdmVuX25hbWUiOiJLYXJ0aGlrIiwib3JpZ2luX2p0aSI6ImFkNWE4MDlk"
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🧪 Testing endpoint: {url}")
    print(f"🔑 Using token: {token[:50]}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n📄 Response Body:")
        try:
            if response.text:
                data = response.json()
                print(json.dumps(data, indent=2))
                
                # If successful, check data types
                if response.status_code == 200 and 'reading' in data:
                    reading = data['reading']
                    print(f"\n🔍 Data Type Analysis:")
                    for key, value in reading.items():
                        data_type = type(value).__name__
                        print(f"  {key}: {data_type} = {value}")
                        
                        # Check if numeric fields are properly converted
                        if key in ['pH', 'tds', 'turbidity', 'temperature', 'qualityScore']:
                            if data_type in ['float', 'int']:
                                print(f"    ✅ Correctly serialized as {data_type}")
                            else:
                                print(f"    ❌ Unexpected type: {data_type}")
            else:
                print("(Empty response)")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Raw response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_lambda_directly():
    """Test Lambda function directly"""
    import boto3
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event that simulates API Gateway
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {
            "deviceId": "ESP32-001"
        },
        "queryStringParameters": None,
        "headers": {
            "Authorization": "Bearer test-token"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user-id",
                    "cognito:groups": ["consumers"]
                }
            }
        }
    }
    
    print(f"\n🔧 Testing Lambda function directly...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        # Read response
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)
        
        print(f"📊 Lambda Response:")
        print(json.dumps(result, indent=2))
        
        # Check if response is properly formatted
        if 'statusCode' in result:
            status_code = result['statusCode']
            print(f"\n✅ Lambda returned status: {status_code}")
            
            if 'body' in result:
                try:
                    body = json.loads(result['body'])
                    print(f"✅ Body is valid JSON")
                    
                    if 'reading' in body:
                        reading = body['reading']
                        print(f"✅ Reading data found")
                        
                        # Check data types
                        for key, value in reading.items():
                            data_type = type(value).__name__
                            print(f"  {key}: {data_type}")
                            
                except json.JSONDecodeError as e:
                    print(f"❌ Body is not valid JSON: {e}")
                    print(f"Raw body: {result['body']}")
        
    except Exception as e:
        print(f"❌ Lambda invocation failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Decimal serialization fix...")
    
    print("\n" + "="*50)
    print("1. Testing via API Gateway")
    print("="*50)
    test_with_browser_token()
    
    print("\n" + "="*50)
    print("2. Testing Lambda directly")
    print("="*50)
    test_lambda_directly()
    
    print("\n✅ Test completed!")
    print("\nℹ️  If the API Gateway test shows 401 Unauthorized, that's expected with an expired token.")
    print("ℹ️  The Lambda direct test should show if Decimal serialization is working.")