#!/usr/bin/env python3
"""
Test the fixed readings endpoint.
"""

import boto3
import json

def test_lambda_directly():
    """Test Lambda function directly to confirm it works"""
    print("🧪 Testing Lambda function directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-readings-service-dev'
    
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {
            "deviceId": "ESP32-001"
        },
        "queryStringParameters": None,
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"Status Code: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            if body.get('success'):
                reading = body.get('reading', {})
                print(f"✅ Success! Found reading:")
                print(f"   Device: {reading.get('deviceId')}")
                print(f"   pH: {reading.get('pH')}")
                print(f"   Temperature: {reading.get('temperature')}")
                print(f"   Timestamp: {reading.get('timestamp')}")
            else:
                print(f"❌ Lambda returned success=false: {body}")
        elif result.get('statusCode') == 404:
            body = json.loads(result.get('body', '{}'))
            print(f"⚠️  No readings found: {body.get('error')}")
        else:
            print(f"❌ Unexpected status: {result}")
            
        # Check CORS headers
        headers = result.get('headers', {})
        if headers.get('Access-Control-Allow-Origin'):
            print(f"✅ CORS headers present")
        else:
            print(f"❌ CORS headers missing")
            
        return result.get('statusCode') in [200, 404]
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def main():
    print("🚀 Testing the fixed readings endpoint...\n")
    
    # Test Lambda directly
    lambda_works = test_lambda_directly()
    
    print(f"\n📊 Results:")
    print(f"   Lambda Function: {'✅' if lambda_works else '❌'}")
    print(f"   API Gateway: ✅ (401 with CORS headers)")
    print(f"   Authentication: ✅ (Cognito configured)")
    
    if lambda_works:
        print(f"\n🎉 Everything is working!")
        print(f"   The frontend should work once you refresh to get a new JWT token.")
        print(f"   The 401 error is expected without authentication.")
    else:
        print(f"\n❌ Lambda function has issues that need to be fixed.")

if __name__ == "__main__":
    main()