#!/usr/bin/env python3
"""
Test Correct API Endpoints for Device Data
"""

import boto3
import json
import requests
from datetime import datetime

def get_cognito_token():
    """Get a valid Cognito token for testing"""
    
    # Use the admin user we created
    email = "admin@aquachain.com"
    password = "AdminPassword123!"
    
    print(f"🔐 Getting Cognito token for: {email}")
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
    
    # Get user pool ID
    user_pools = cognito_client.list_user_pools(MaxResults=10)
    aquachain_pool = None
    
    for pool in user_pools['UserPools']:
        if 'aquachain' in pool['Name'].lower():
            aquachain_pool = pool
            break
    
    if not aquachain_pool:
        print("❌ AquaChain user pool not found")
        return None
    
    user_pool_id = aquachain_pool['Id']
    client_id = "692o9a3pjudl1vudfgqpr5nuln"  # From previous test
    
    try:
        # Authenticate user
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        if 'AuthenticationResult' in response:
            access_token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            
            print("✅ Authentication successful!")
            return {
                'access_token': access_token,
                'id_token': id_token
            }
        else:
            print(f"❌ Authentication failed: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None

def test_correct_endpoints(tokens):
    """Test the correct API endpoints"""
    
    if not tokens:
        print("❌ No valid tokens available")
        return False
    
    print(f"\n🧪 Testing Correct API Endpoints")
    print("=" * 50)
    
    # API Gateway URL
    api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    
    headers = {
        'Authorization': f"Bearer {tokens['id_token']}",
        'Content-Type': 'application/json'
    }
    
    # Test different endpoint patterns
    endpoints_to_test = [
        f"{api_url}/api/device-readings/ESP32-001/latest",
        f"{api_url}/device-readings/ESP32-001/latest", 
        f"{api_url}/api/device-readings/ESP32-001/history",
        f"{api_url}/device-readings/ESP32-001/history"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n📍 Testing: {endpoint}")
            
            response = requests.get(endpoint, headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API call successful!")
                print(f"📦 Response: {json.dumps(data, indent=2)}")
                return True
            elif response.status_code == 404:
                print("❌ Endpoint not found")
            elif response.status_code == 401:
                print("❌ Unauthorized")
            elif response.status_code == 403:
                print("❌ Forbidden")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📋 Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
    
    return False

def test_lambda_direct():
    """Test Lambda function directly to confirm it works"""
    
    print(f"\n🧪 Testing Lambda Function Directly")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test with correct path structure
    test_events = [
        {
            "httpMethod": "GET",
            "path": "/api/device-readings/ESP32-001/latest",
            "pathParameters": {
                "deviceId": "ESP32-001"
            },
            "queryStringParameters": None,
            "headers": {
                "Content-Type": "application/json"
            }
        },
        {
            "httpMethod": "GET", 
            "path": "/device-readings/ESP32-001/latest",
            "pathParameters": {
                "deviceId": "ESP32-001"
            },
            "queryStringParameters": None,
            "headers": {
                "Content-Type": "application/json"
            }
        }
    ]
    
    for i, test_event in enumerate(test_events):
        try:
            print(f"\n🧪 Test {i+1}: {test_event['path']}")
            
            response = lambda_client.invoke(
                FunctionName='aquachain-function-readings-service-dev',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"📊 Lambda Response Status: {result.get('statusCode', 'N/A')}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                if body.get('success') and body.get('reading'):
                    reading = body['reading']
                    print("✅ Lambda returned reading:")
                    print(f"   Timestamp: {reading.get('timestamp', 'N/A')}")
                    print(f"   pH: {reading.get('pH', 'N/A')}")
                    print(f"   Temperature: {reading.get('temperature', 'N/A')}")
                    return True
                else:
                    print(f"❌ No reading data: {body}")
            else:
                print(f"❌ Lambda error: {result.get('body', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing Lambda: {e}")
    
    return False

def check_api_gateway_integration():
    """Check API Gateway integration for device-readings"""
    
    print(f"\n🔍 Checking API Gateway Integration")
    print("=" * 50)
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Get the API Gateway
        api_id = "vtqjfznspc"
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_readings_resource = None
        for resource in resources['items']:
            if 'device-readings' in resource.get('pathPart', ''):
                device_readings_resource = resource
                break
        
        if device_readings_resource:
            print(f"✅ Found device-readings resource: {device_readings_resource['id']}")
            print(f"📋 Path: {device_readings_resource.get('path', 'N/A')}")
            print(f"📋 Methods: {list(device_readings_resource.get('resourceMethods', {}).keys())}")
            
            # Check if it has child resources
            child_resources = [r for r in resources['items'] 
                             if r.get('parentId') == device_readings_resource['id']]
            
            if child_resources:
                print(f"📋 Child resources:")
                for child in child_resources:
                    print(f"   - {child.get('pathPart', 'N/A')} ({child['id']})")
            else:
                print("❌ No child resources found (need {deviceId} and {deviceId}/latest)")
                
        else:
            print("❌ device-readings resource not found")
            
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")

def main():
    """Main test function"""
    print("🧪 Correct API Endpoints Test")
    print("=" * 60)
    
    # Check API Gateway structure
    check_api_gateway_integration()
    
    # Test Lambda directly
    lambda_works = test_lambda_direct()
    
    # Get authentication tokens
    tokens = get_cognito_token()
    
    # Test API endpoints
    api_works = False
    if tokens:
        api_works = test_correct_endpoints(tokens)
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 50)
    print(f"✅ Lambda Direct: {'Working' if lambda_works else 'Failed'}")
    print(f"✅ Authentication: {'Success' if tokens else 'Failed'}")
    print(f"✅ API Gateway: {'Working' if api_works else 'Failed'}")
    
    if lambda_works and tokens and not api_works:
        print("\n🔧 Issue is in API Gateway integration")
        print("💡 Possible fixes:")
        print("   1. Create missing {deviceId} and {deviceId}/latest resources")
        print("   2. Configure proper Lambda integration")
        print("   3. Set up correct path parameter mapping")

if __name__ == "__main__":
    main()