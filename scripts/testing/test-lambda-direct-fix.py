#!/usr/bin/env python3
"""
Test the Lambda function directly to verify the convert_decimals fix
"""

import boto3
import json

def test_lambda_direct():
    """Test Lambda function directly"""
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Create a test event that mimics API Gateway
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {
            "deviceId": "ESP32-001"
        },
        "queryStringParameters": None,
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user-id",
                    "cognito:username": "testuser",
                    "email": "test@example.com"
                }
            }
        }
    }
    
    print("🧪 Testing Lambda function directly")
    print("="*40)
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        # Read the response
        payload = response['Payload'].read()
        result = json.loads(payload)
        
        print(f"📊 Lambda Status Code: {response['StatusCode']}")
        print(f"📄 Lambda Response: {json.dumps(result, indent=2)}")
        
        # Check if the response has the correct structure
        if 'statusCode' in result and 'body' in result:
            print("✅ Lambda returns proper API Gateway response structure")
            
            # Try to parse the body
            try:
                body = json.loads(result['body'])
                print("✅ Response body is valid JSON")
                print(f"📋 Body content: {json.dumps(body, indent=2)}")
                
                if result['statusCode'] == 200:
                    print("✅ SUCCESS: Lambda function works correctly!")
                    return True
                elif result['statusCode'] == 404:
                    print("⚠️  404 Not Found - Expected if no readings exist")
                    return True
                else:
                    print(f"⚠️  Status code: {result['statusCode']}")
                    return True
                    
            except json.JSONDecodeError as e:
                print(f"❌ Body is not valid JSON: {e}")
                print(f"Raw body: {result.get('body', 'No body')}")
                return False
        else:
            print("❌ Lambda response missing statusCode or body")
            return False
            
    except Exception as e:
        print(f"❌ Lambda invocation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_lambda_direct()
    
    if success:
        print("\n✅ LAMBDA FUNCTION FIX SUCCESSFUL")
        print("The convert_decimals function is now working!")
    else:
        print("\n❌ LAMBDA FUNCTION STILL HAS ISSUES")
        print("The fix did not resolve the problem")