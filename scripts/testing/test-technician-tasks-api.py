#!/usr/bin/env python3
"""
Test Technician Tasks API Directly

This script tests the technician tasks API endpoint to see what's happening
when the dashboard tries to fetch tasks.
"""

import boto3
import requests
import json
from datetime import datetime

def get_auth_token():
    """Get authentication token for Sidharth Lenin"""
    try:
        # Use Cognito to get a token for Sidharth
        cognito = boto3.client('cognito-idp')
        
        # Sidharth's credentials
        username = 'leninat259@gmail.com'
        password = 'TempPassword123!'  # This might need to be updated
        
        user_pool_id = 'ap-south-1_QUDl7hG8u'
        client_id = '692o9a3pjudl1vudfgqpr5nuln'
        
        print(f"🔐 Attempting to authenticate Sidharth Lenin...")
        print(f"   Username: {username}")
        
        # Try to authenticate
        response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        if 'AuthenticationResult' in response:
            token = response['AuthenticationResult']['AccessToken']
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting auth token: {e}")
        return None

def test_api_endpoint_with_auth(token):
    """Test the technician tasks API endpoint with authentication"""
    try:
        api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🧪 Testing API endpoint: {api_url}")
        print(f"   Headers: Authorization: Bearer {token[:20]}...")
        
        response = requests.get(api_url, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful!")
            print(f"📋 Tasks returned: {len(data.get('tasks', []))}")
            print(f"📋 Response data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ API call failed")
            print(f"📋 Response body: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")
        return None

def test_api_endpoint_without_auth():
    """Test the API endpoint without authentication to see the error"""
    try:
        api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks"
        
        print(f"🧪 Testing API endpoint without auth: {api_url}")
        
        response = requests.get(api_url)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response body: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")
        return None

def check_api_gateway_integration():
    """Check the API Gateway integration details"""
    try:
        apigateway = boto3.client('apigateway')
        
        rest_api_id = 'vtqjfznspc'
        resource_id = 'aot6xm'  # /api/v1/technician/tasks
        http_method = 'GET'
        
        print(f"🔍 Checking API Gateway integration...")
        
        # Get integration details
        integration = apigateway.get_integration(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )
        
        print(f"✅ Integration found:")
        print(f"   Type: {integration['type']}")
        print(f"   URI: {integration['uri']}")
        print(f"   HTTP Method: {integration['httpMethod']}")
        
        return integration
        
    except Exception as e:
        print(f"❌ Error checking API Gateway integration: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Testing Technician Tasks API")
    print("=" * 60)
    
    # Check API Gateway integration first
    integration = check_api_gateway_integration()
    
    print("\n" + "=" * 60)
    print("🧪 Testing API Endpoint")
    print("=" * 60)
    
    # Test without auth first
    print("\n1. Testing without authentication:")
    test_api_endpoint_without_auth()
    
    # Try to get auth token and test with auth
    print("\n2. Testing with authentication:")
    token = get_auth_token()
    
    if token:
        test_api_endpoint_with_auth(token)
    else:
        print("❌ Cannot test with authentication - no token available")
    
    print("\n" + "=" * 60)
    print("📊 ANALYSIS")
    print("=" * 60)
    
    if integration:
        expected_lambda = "aquachain-function-technician-tasks-dev"
        actual_uri = integration['uri']
        
        if expected_lambda in actual_uri:
            print("✅ API Gateway is routing to the correct Lambda function")
        else:
            print("❌ API Gateway is routing to the wrong Lambda function")
            print(f"   Expected: {expected_lambda}")
            print(f"   Actual URI: {actual_uri}")
    
    print("\n💡 NEXT STEPS:")
    print("1. Check if the Lambda function code is correct")
    print("2. Verify the authentication is working")
    print("3. Check CloudWatch logs for the Lambda function")
    print("4. Test the service request database queries directly")

if __name__ == "__main__":
    main()