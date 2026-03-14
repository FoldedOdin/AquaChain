#!/usr/bin/env python3
"""
Test the readings Lambda function directly
"""

import boto3
import json

def test_readings_lambda_direct():
    """Test the readings Lambda function directly"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        function_name = 'aquachain-function-readings-service-dev'
        
        print(f"🧪 Testing Lambda function directly: {function_name}")
        
        # Test event for latest reading
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
        
        print(f"   📋 Test event: {json.dumps(test_event, indent=2)}")
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"   📊 Lambda Response:")
        print(f"     Status Code: {payload.get('statusCode')}")
        print(f"     Body: {payload.get('body')}")
        
        if payload.get('statusCode') == 200:
            try:
                body_data = json.loads(payload.get('body', '{}'))
                print(f"   ✅ SUCCESS! Parsed response:")
                print(f"     Success: {body_data.get('success')}")
                print(f"     Device ID: {body_data.get('deviceId')}")
                
                reading = body_data.get('reading')
                if reading:
                    print(f"     📊 Reading data:")
                    print(f"       Timestamp: {reading.get('timestamp')}")
                    print(f"       pH: {reading.get('pH')}")
                    print(f"       Temperature: {reading.get('temperature')}")
                    print(f"       TDS: {reading.get('tds')}")
                    print(f"       Turbidity: {reading.get('turbidity')}")
                
                return True
                
            except Exception as parse_error:
                print(f"   ⚠️ Could not parse response body: {parse_error}")
                return False
        else:
            print(f"   ❌ Lambda returned error status")
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def test_readings_lambda_history():
    """Test the readings Lambda function for history"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        function_name = 'aquachain-function-readings-service-dev'
        
        print(f"\n🧪 Testing Lambda function for history: {function_name}")
        
        # Test event for history
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/readings/ESP32-001/history",
            "pathParameters": {
                "deviceId": "ESP32-001"
            },
            "queryStringParameters": {
                "days": "7"
            },
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        print(f"   📋 Test event: {json.dumps(test_event, indent=2)}")
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"   📊 Lambda Response:")
        print(f"     Status Code: {payload.get('statusCode')}")
        
        if payload.get('statusCode') == 200:
            try:
                body_data = json.loads(payload.get('body', '{}'))
                print(f"   ✅ SUCCESS! Parsed response:")
                print(f"     Success: {body_data.get('success')}")
                print(f"     Device ID: {body_data.get('deviceId')}")
                print(f"     Days: {body_data.get('days')}")
                print(f"     Count: {body_data.get('count')}")
                
                readings = body_data.get('readings', [])
                if readings:
                    print(f"     📊 Found {len(readings)} readings")
                    print(f"     Latest: {readings[0].get('timestamp')} - pH: {readings[0].get('pH')}")
                
                return True
                
            except Exception as parse_error:
                print(f"   ⚠️ Could not parse response body: {parse_error}")
                return False
        else:
            print(f"   ❌ Lambda returned error status")
            try:
                body_data = json.loads(payload.get('body', '{}'))
                print(f"     Error: {body_data.get('error')}")
            except:
                pass
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def check_api_gateway_integration():
    """Check if the Lambda is properly integrated with API Gateway"""
    try:
        print(f"\n🔍 Checking API Gateway integration...")
        
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        api_id = 'vtqjfznspc'
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        readings_resources = []
        
        for resource in resources['items']:
            path = resource.get('path', '')
            if 'reading' in path.lower():
                readings_resources.append({
                    'path': path,
                    'id': resource['id'],
                    'methods': list(resource.get('resourceMethods', {}).keys())
                })
        
        if readings_resources:
            print(f"   ✅ Found {len(readings_resources)} readings-related resources:")
            for res in readings_resources:
                print(f"     - {res['path']} ({res['id']}) - Methods: {res['methods']}")
        else:
            print(f"   ❌ No readings-related resources found in API Gateway")
        
        return len(readings_resources) > 0
        
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")
        return False

def main():
    print("🧪 Testing Readings Lambda Function Directly")
    print("=" * 45)
    
    # Step 1: Test Lambda function for latest reading
    print("\n1. Testing Lambda for latest reading...")
    latest_works = test_readings_lambda_direct()
    
    # Step 2: Test Lambda function for history
    print("\n2. Testing Lambda for history...")
    history_works = test_readings_lambda_history()
    
    # Step 3: Check API Gateway integration
    print("\n3. Checking API Gateway integration...")
    api_integration = check_api_gateway_integration()
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Lambda Latest: {'✅' if latest_works else '❌'}")
    print(f"   Lambda History: {'✅' if history_works else '❌'}")
    print(f"   API Gateway Integration: {'✅' if api_integration else '❌'}")
    
    if latest_works and history_works:
        print(f"\n🎉 Lambda function is working correctly!")
        
        if not api_integration:
            print(f"💡 Next step: Create API Gateway endpoints to expose the Lambda")
            print(f"   The Lambda function is ready, just needs API Gateway integration")
        else:
            print(f"💡 Next step: Test the API Gateway endpoints")
            print(f"   Both Lambda and API Gateway seem to be configured")
    else:
        print(f"\n❌ Lambda function has issues that need to be fixed first")

if __name__ == "__main__":
    main()