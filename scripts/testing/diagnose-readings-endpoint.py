#!/usr/bin/env python3
"""
Diagnose the readings endpoint issue step by step.
"""

import boto3
import json
import requests
from botocore.exceptions import ClientError

def check_api_gateway_setup():
    """Check API Gateway configuration"""
    print("🔍 Checking API Gateway setup...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    try:
        # Get API info
        api = apigateway.get_rest_api(restApiId=api_id)
        print(f"✅ API found: {api['name']}")
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print("\n📋 API Resources:")
        readings_resources = []
        for resource in resources['items']:
            path = resource.get('path', '')
            if 'readings' in path.lower() or 'latest' in path.lower():
                readings_resources.append(resource)
                print(f"   📍 {path} (ID: {resource['id']})")
                
                # Check methods for this resource
                resource_methods = resource.get('resourceMethods', {})
                for method in resource_methods:
                    print(f"      {method}")
        
        if not readings_resources:
            print("❌ No readings-related resources found!")
            return False
        
        # Check specific endpoint
        target_path = '/api/v1/readings/{deviceId}/latest'
        target_resource = None
        
        for resource in resources['items']:
            if resource.get('path') == target_path:
                target_resource = resource
                break
        
        if target_resource:
            print(f"\n✅ Found target resource: {target_path}")
            
            # Check GET method
            try:
                method = apigateway.get_method(
                    restApiId=api_id,
                    resourceId=target_resource['id'],
                    httpMethod='GET'
                )
                print(f"   ✅ GET method exists")
                print(f"   Authorization: {method.get('authorizationType', 'None')}")
                
                if method.get('authorizerId'):
                    print(f"   Authorizer ID: {method['authorizerId']}")
                
            except ClientError as e:
                print(f"   ❌ GET method not found: {e}")
                return False
        else:
            print(f"❌ Target resource not found: {target_path}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")
        return False

def test_lambda_directly():
    """Test the Lambda function directly"""
    print("\n🧪 Testing Lambda function directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Find the readings Lambda function
    try:
        functions = lambda_client.list_functions()
        readings_function = None
        
        for func in functions['Functions']:
            if 'readings' in func['FunctionName'].lower():
                readings_function = func
                print(f"✅ Found Lambda: {func['FunctionName']}")
                break
        
        if not readings_function:
            print("❌ No readings Lambda function found")
            return False
        
        # Test the function
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
        
        print(f"📤 Invoking Lambda with test event...")
        
        response = lambda_client.invoke(
            FunctionName=readings_function['FunctionName'],
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"📥 Lambda response: {json.dumps(result, indent=2)}")
        
        return result.get('statusCode') == 200 or result.get('statusCode') == 404
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def test_endpoint_with_different_methods():
    """Test the endpoint with different approaches"""
    print("\n🧪 Testing endpoint accessibility...")
    
    base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    
    test_urls = [
        f"{base_url}/api/v1/readings/ESP32-001/latest",
        f"{base_url}/api/device-readings",
        f"{base_url}/api/readings/ESP32-001/latest"
    ]
    
    for url in test_urls:
        print(f"\n📍 Testing: {url}")
        
        try:
            # Test without auth
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Endpoint exists but requires auth")
            elif response.status_code == 403:
                print("   ⚠️  Endpoint exists but forbidden")
            elif response.status_code == 404:
                print("   ❌ Endpoint not found")
            else:
                print(f"   📄 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_cognito_setup():
    """Check Cognito configuration"""
    print("\n🔐 Checking Cognito setup...")
    
    cognito = boto3.client('cognito-idp', region_name='ap-south-1')
    
    try:
        # List user pools
        pools = cognito.list_user_pools(MaxResults=10)
        
        aquachain_pool = None
        for pool in pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                aquachain_pool = pool
                print(f"✅ Found user pool: {pool['Name']} (ID: {pool['Id']})")
                break
        
        if not aquachain_pool:
            print("❌ No AquaChain user pool found")
            return False
        
        # Get pool details
        pool_details = cognito.describe_user_pool(UserPoolId=aquachain_pool['Id'])
        print(f"   Domain: {pool_details['UserPool'].get('Domain', 'Not set')}")
        
        # List app clients
        clients = cognito.list_user_pool_clients(UserPoolId=aquachain_pool['Id'])
        for client in clients['UserPoolClients']:
            print(f"   App Client: {client['ClientName']} (ID: {client['ClientId']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Cognito: {e}")
        return False

def main():
    print("🚀 Diagnosing readings endpoint issue...\n")
    
    # Step 1: Check API Gateway
    api_ok = check_api_gateway_setup()
    
    # Step 2: Test Lambda directly
    lambda_ok = test_lambda_directly()
    
    # Step 3: Test endpoint accessibility
    test_endpoint_with_different_methods()
    
    # Step 4: Check Cognito
    cognito_ok = check_cognito_setup()
    
    print("\n📊 Summary:")
    print(f"   API Gateway: {'✅' if api_ok else '❌'}")
    print(f"   Lambda Function: {'✅' if lambda_ok else '❌'}")
    print(f"   Cognito Setup: {'✅' if cognito_ok else '❌'}")
    
    if api_ok and lambda_ok and cognito_ok:
        print("\n✅ All components look good. The 401 error is expected without authentication.")
        print("   The frontend should work once you refresh to get a new JWT token.")
    else:
        print("\n❌ Found issues that need to be fixed.")

if __name__ == "__main__":
    main()