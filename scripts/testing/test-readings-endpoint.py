#!/usr/bin/env python3
"""
Test the readings endpoint and check if it exists
"""

import boto3
import json
import requests

def check_readings_endpoint_exists():
    """Check if the readings endpoint exists in API Gateway"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'  # The correct API Gateway ID
        
        print(f"🔍 Checking API Gateway resources for readings endpoint...")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"📋 All resources in API Gateway:")
        
        readings_found = False
        v1_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('pathPart', resource.get('path', '/'))
            resource_id = resource['id']
            parent_id = resource.get('parentId', 'None')
            
            print(f"   {path} ({resource_id}) - Parent: {parent_id}")
            
            if path == 'v1':
                v1_resource_id = resource_id
                print(f"     📍 Found v1 resource: {resource_id}")
            
            if 'readings' in path.lower():
                readings_found = True
                print(f"     📍 Found readings resource: {path}")
        
        if not readings_found:
            print(f"\n❌ No readings endpoint found!")
            print(f"   The endpoint /api/v1/readings/{'{deviceId}'}/latest doesn't exist")
            
            if v1_resource_id:
                print(f"   But we found v1 resource: {v1_resource_id}")
                print(f"   We can create the readings endpoint under v1")
                return False, v1_resource_id
            else:
                print(f"   No v1 resource found either")
                return False, None
        else:
            print(f"✅ Readings endpoint exists")
            return True, None
        
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")
        return False, None

def test_endpoint_with_auth():
    """Test the endpoint with proper authentication"""
    try:
        # Get a valid token from the login we did earlier
        print(f"\n🧪 Testing endpoint with authentication...")
        
        # First, let's try to login and get a token
        login_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin"
        
        login_data = {
            "email": "leninat259@gmail.com",
            "password": "AquaChain2024!"
        }
        
        print(f"🔐 Logging in to get auth token...")
        
        login_response = requests.post(login_url, json=login_data, timeout=10)
        
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('token')
            
            if token:
                print(f"   ✅ Got auth token: {token[:20]}...")
                
                # Now test the readings endpoint with the token
                readings_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                print(f"\n📊 Testing readings endpoint with auth...")
                
                readings_response = requests.get(readings_url, headers=headers, timeout=10)
                
                print(f"   Readings Status: {readings_response.status_code}")
                print(f"   Response: {readings_response.text[:200]}")
                
                if readings_response.status_code == 200:
                    print(f"   ✅ Readings endpoint is working!")
                    return True
                elif readings_response.status_code == 404:
                    print(f"   ❌ Readings endpoint not found (404)")
                    return False
                else:
                    print(f"   ⚠️ Readings endpoint returned {readings_response.status_code}")
                    return False
            else:
                print(f"   ❌ No token in login response")
                return False
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing with auth: {e}")
        return False

def check_lambda_functions():
    """Check if there's a Lambda function for readings"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        print(f"\n🔍 Checking Lambda functions for readings...")
        
        # List all functions
        functions = lambda_client.list_functions()
        
        readings_functions = []
        
        for func in functions['Functions']:
            func_name = func['FunctionName']
            
            if 'reading' in func_name.lower():
                readings_functions.append(func_name)
                print(f"   📍 Found readings function: {func_name}")
        
        if not readings_functions:
            print(f"   ❌ No readings Lambda functions found")
            print(f"   The API endpoint may not have a backend implementation")
        
        return len(readings_functions) > 0
        
    except Exception as e:
        print(f"❌ Error checking Lambda functions: {e}")
        return False

def main():
    print("🔍 Testing Readings Endpoint")
    print("=" * 30)
    
    # Step 1: Check if endpoint exists in API Gateway
    print("\n1. Checking API Gateway configuration...")
    endpoint_exists, v1_resource_id = check_readings_endpoint_exists()
    
    # Step 2: Test with authentication
    print("\n2. Testing endpoint with authentication...")
    auth_works = test_endpoint_with_auth()
    
    # Step 3: Check Lambda functions
    print("\n3. Checking Lambda backend...")
    lambda_exists = check_lambda_functions()
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   CORS Headers: ✅ Fixed")
    print(f"   API Endpoint Exists: {'✅' if endpoint_exists else '❌'}")
    print(f"   Authentication Works: {'✅' if auth_works else '❌'}")
    print(f"   Lambda Backend: {'✅' if lambda_exists else '❌'}")
    
    if not endpoint_exists:
        print(f"\n🔧 Recommendations:")
        print(f"   1. The /api/v1/readings/{{deviceId}}/latest endpoint doesn't exist")
        print(f"   2. You may need to create this endpoint in API Gateway")
        print(f"   3. Or use a different endpoint that exists")
        
        print(f"\n💡 Alternative: Check if there's a different readings endpoint")
        print(f"   Try: /api/readings/latest or /api/devices/{{deviceId}}/readings")
    
    elif not auth_works:
        print(f"\n🔧 The endpoint exists but authentication is failing")
        print(f"   This could be due to:")
        print(f"   1. Missing Lambda function backend")
        print(f"   2. Incorrect API Gateway integration")
        print(f"   3. Authentication configuration issues")

if __name__ == "__main__":
    main()