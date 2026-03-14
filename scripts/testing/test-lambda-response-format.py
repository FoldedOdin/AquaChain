#!/usr/bin/env python3
"""
Test Lambda response format directly
"""

import boto3
import json

def test_lambda_response_format():
    """Test Lambda response format for API Gateway compatibility"""
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event that simulates API Gateway request
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {
            "deviceId": "ESP32-001"
        },
        "queryStringParameters": None,
        "headers": {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
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
    
    print(f"🧪 Testing Lambda response format...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        # Read response
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)
        
        print(f"📊 Lambda Response Structure:")
        print(json.dumps(result, indent=2))
        
        # Validate API Gateway proxy response format
        print(f"\n🔍 API Gateway Compatibility Check:")
        
        required_fields = ['statusCode', 'body', 'headers']
        for field in required_fields:
            if field in result:
                print(f"  ✅ {field}: Present")
            else:
                print(f"  ❌ {field}: MISSING")
                return False
        
        # Check statusCode type
        if isinstance(result['statusCode'], int):
            print(f"  ✅ statusCode is integer: {result['statusCode']}")
        else:
            print(f"  ❌ statusCode is not integer: {type(result['statusCode'])}")
            return False
        
        # Check body is string
        if isinstance(result['body'], str):
            print(f"  ✅ body is string (length: {len(result['body'])})")
            
            # Try to parse body as JSON
            try:
                body_data = json.loads(result['body'])
                print(f"  ✅ body contains valid JSON")
                
                # Check if reading data exists and has proper types
                if 'reading' in body_data:
                    reading = body_data['reading']
                    print(f"\n🔍 Sensor Data Types:")
                    
                    sensor_fields = ['pH', 'tds', 'turbidity', 'temperature', 'qualityScore']
                    all_good = True
                    
                    for field in sensor_fields:
                        if field in reading:
                            value = reading[field]
                            data_type = type(value).__name__
                            print(f"    {field}: {data_type} = {value}")
                            
                            if data_type not in ['float', 'int']:
                                print(f"    ❌ {field} should be numeric, got {data_type}")
                                all_good = False
                            else:
                                print(f"    ✅ {field} is properly converted")
                    
                    if all_good:
                        print(f"\n🎉 All sensor values are properly converted!")
                    else:
                        print(f"\n❌ Some sensor values have incorrect types")
                        return False
                
            except json.JSONDecodeError as e:
                print(f"  ❌ body is not valid JSON: {e}")
                return False
        else:
            print(f"  ❌ body is not string: {type(result['body'])}")
            return False
        
        # Check headers
        if isinstance(result['headers'], dict):
            print(f"  ✅ headers is dictionary")
            
            # Check CORS headers
            cors_headers = ['Access-Control-Allow-Origin', 'Content-Type']
            for header in cors_headers:
                if header in result['headers']:
                    print(f"    ✅ {header}: {result['headers'][header]}")
                else:
                    print(f"    ⚠️  {header}: Missing (may cause CORS issues)")
        else:
            print(f"  ❌ headers is not dictionary: {type(result['headers'])}")
            return False
        
        # Check isBase64Encoded
        if 'isBase64Encoded' in result:
            if isinstance(result['isBase64Encoded'], bool):
                print(f"  ✅ isBase64Encoded: {result['isBase64Encoded']}")
            else:
                print(f"  ❌ isBase64Encoded is not boolean: {type(result['isBase64Encoded'])}")
        else:
            print(f"  ⚠️  isBase64Encoded: Missing (recommended for proxy integration)")
        
        print(f"\n✅ Lambda response format is API Gateway compatible!")
        return True
        
    except Exception as e:
        print(f"❌ Lambda invocation failed: {e}")
        return False

def test_error_response_format():
    """Test error response format"""
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event with missing device ID to trigger error
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/latest",  # Missing deviceId
        "pathParameters": {},  # Empty path parameters
        "queryStringParameters": None,
        "headers": {
            "Authorization": "Bearer test-token"
        }
    }
    
    print(f"\n🧪 Testing error response format...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)
        
        print(f"📊 Error Response:")
        print(json.dumps(result, indent=2))
        
        # Should return 400 Bad Request
        if result.get('statusCode') == 400:
            print(f"✅ Correct error status code: 400")
            
            # Check error body
            body = json.loads(result['body'])
            if 'error' in body and 'code' in body:
                print(f"✅ Error response has proper structure")
                return True
            else:
                print(f"❌ Error response missing error/code fields")
                return False
        else:
            print(f"❌ Expected 400, got {result.get('statusCode')}")
            return False
            
    except Exception as e:
        print(f"❌ Error test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Lambda response format for API Gateway compatibility...")
    
    success1 = test_lambda_response_format()
    success2 = test_error_response_format()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Lambda response format is fully API Gateway compatible")
        print(f"✅ Decimal serialization is working correctly")
        print(f"✅ Error handling is working correctly")
        print(f"\n🚀 Your API should now work in the browser!")
    else:
        print(f"\n❌ Some tests failed")
        print(f"ℹ️  Check the output above for specific issues")