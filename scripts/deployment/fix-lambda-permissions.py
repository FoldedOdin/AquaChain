#!/usr/bin/env python3
"""
Fix Lambda permissions for API Gateway
"""

import boto3
import json

def fix_lambda_permissions():
    """Fix Lambda permissions for API Gateway"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        function_name = 'aquachain-function-readings-service-dev'
        api_id = 'vtqjfznspc'
        
        print(f"🔧 Fixing Lambda permissions for {function_name}...")
        
        # Remove existing permission if it exists
        try:
            lambda_client.remove_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-device-readings-new'
            )
            print(f"   ✅ Removed existing permission")
        except Exception as e:
            print(f"   ⚠️ No existing permission to remove: {e}")
        
        # Add correct permission
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-device-readings-fixed',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:ap-south-1:758346259059:{api_id}/*/*'
            )
            print(f"   ✅ Added correct Lambda permission")
        except Exception as e:
            print(f"   ❌ Error adding permission: {e}")
        
        # List current permissions to verify
        try:
            policy = lambda_client.get_policy(FunctionName=function_name)
            policy_doc = json.loads(policy['Policy'])
            
            print(f"\n   📋 Current Lambda permissions:")
            for statement in policy_doc.get('Statement', []):
                sid = statement.get('Sid', 'Unknown')
                principal = statement.get('Principal', {})
                source_arn = statement.get('Condition', {}).get('StringEquals', {}).get('AWS:SourceArn', 'None')
                print(f"     - {sid}: {principal} -> {source_arn}")
                
        except Exception as e:
            print(f"   ⚠️ Could not list permissions: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        return False

def test_lambda_direct():
    """Test Lambda function directly to make sure it works"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        function_name = 'aquachain-function-readings-service-dev'
        
        print(f"\n🧪 Testing Lambda function directly...")
        
        # Test event that matches API Gateway format
        test_event = {
            "httpMethod": "GET",
            "path": "/api/device-readings/ESP32-001/latest",
            "pathParameters": {
                "deviceId": "ESP32-001"
            },
            "queryStringParameters": None,
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"   Status Code: {payload.get('statusCode')}")
        
        if payload.get('statusCode') == 200:
            print(f"   ✅ Lambda is working correctly")
            return True
        else:
            print(f"   ❌ Lambda error: {payload.get('body')}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def test_api_gateway_endpoint():
    """Test the API Gateway endpoint"""
    try:
        import requests
        
        print(f"\n🧪 Testing API Gateway endpoint...")
        
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/device-readings/ESP32-001/latest"
        
        print(f"   🔍 Testing: {url}")
        
        # Test OPTIONS first
        try:
            options_response = requests.options(url, timeout=10)
            print(f"   OPTIONS: {options_response.status_code}")
            print(f"   CORS: {options_response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
        except Exception as e:
            print(f"   OPTIONS Error: {e}")
        
        # Test GET
        try:
            get_response = requests.get(url, timeout=10)
            print(f"   GET: {get_response.status_code}")
            
            if get_response.status_code == 200:
                print(f"   ✅ SUCCESS! Response: {get_response.text[:200]}")
                return True
            else:
                print(f"   ❌ Error: {get_response.text[:100]}")
                return False
        except Exception as e:
            print(f"   GET Error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def redeploy_api():
    """Redeploy the API to make sure changes take effect"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        print(f"\n🚀 Redeploying API to apply changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fixed Lambda permissions for device readings'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error redeploying API: {e}")
        return False

def main():
    print("🔧 Fixing Lambda Permissions and Testing")
    print("=" * 40)
    
    # Step 1: Fix Lambda permissions
    print("\n1. Fixing Lambda permissions...")
    if not fix_lambda_permissions():
        print("❌ Failed to fix permissions")
        return
    
    # Step 2: Test Lambda directly
    print("\n2. Testing Lambda function directly...")
    if not test_lambda_direct():
        print("❌ Lambda function has issues")
        return
    
    # Step 3: Redeploy API
    print("\n3. Redeploying API...")
    if not redeploy_api():
        print("❌ Failed to redeploy API")
        return
    
    # Step 4: Test API Gateway endpoint
    print("\n4. Testing API Gateway endpoint...")
    if test_api_gateway_endpoint():
        print(f"\n🎉 Success!")
        print(f"✅ Lambda permissions fixed")
        print(f"✅ API Gateway endpoint working")
        print(f"✅ Ready to update frontend")
        
        print(f"\n💡 Frontend update needed:")
        print(f"   Change from: /api/v1/readings/{{deviceId}}/latest")
        print(f"   Change to:   /api/device-readings/{{deviceId}}/latest")
    else:
        print(f"\n❌ Still having issues with the endpoint")
        print(f"💡 Try waiting a few minutes for AWS changes to propagate")

if __name__ == "__main__":
    main()