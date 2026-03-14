#!/usr/bin/env python3
"""
Fix API Gateway integration to point to the correct Lambda function
"""

import boto3
import json

def fix_readings_api_integration():
    """Fix the API Gateway integration for readings endpoint"""
    
    # Initialize clients
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    # API Gateway details
    rest_api_id = 'vtqjfznspc'
    resource_id = 'o47l9d'  # /api/v1/readings/{deviceId}/latest
    http_method = 'GET'
    
    # Correct Lambda function ARN
    correct_lambda_arn = 'arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-readings-service-dev'
    integration_uri = f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{correct_lambda_arn}/invocations'
    
    print("🔧 Fixing API Gateway Lambda Integration")
    print("=" * 50)
    print(f"API Gateway: {rest_api_id}")
    print(f"Resource: {resource_id} (GET /api/v1/readings/{{deviceId}}/latest)")
    print(f"Correct Lambda ARN: {correct_lambda_arn}")
    
    try:
        # Update the integration
        print("\n📝 Updating API Gateway integration...")
        
        response = apigateway.put_integration(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri,
            passthroughBehavior='WHEN_NO_MATCH',
            timeoutInMillis=29000
        )
        
        print("✅ Integration updated successfully")
        print(f"New URI: {response['uri']}")
        
        # Deploy the changes
        print("\n🚀 Deploying changes to 'dev' stage...")
        
        deploy_response = apigateway.create_deployment(
            restApiId=rest_api_id,
            stageName='dev',
            description='Fix Lambda integration for readings endpoint'
        )
        
        print(f"✅ Deployment successful: {deploy_response['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating integration: {e}")
        return False

def verify_lambda_permissions():
    """Verify Lambda has permission to be invoked by API Gateway"""
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-readings-service-dev'
    
    print("\n🔍 Checking Lambda permissions...")
    
    try:
        # Get function policy
        try:
            policy_response = lambda_client.get_policy(FunctionName=function_name)
            policy = json.loads(policy_response['Policy'])
            
            # Check if API Gateway has permission
            api_gateway_permission_exists = False
            for statement in policy.get('Statement', []):
                if (statement.get('Principal', {}).get('Service') == 'apigateway.amazonaws.com' and
                    'lambda:InvokeFunction' in statement.get('Action', [])):
                    api_gateway_permission_exists = True
                    break
            
            if api_gateway_permission_exists:
                print("✅ API Gateway has permission to invoke Lambda")
                return True
            else:
                print("⚠️  API Gateway permission not found, adding it...")
                
        except lambda_client.exceptions.ResourceNotFoundException:
            print("⚠️  No policy found, adding API Gateway permission...")
        
        # Add permission for API Gateway to invoke Lambda
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId='api-gateway-invoke-readings',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:ap-south-1:758346259059:vtqjfznspc/*/GET/api/v1/readings/*/latest'
        )
        
        print("✅ Added API Gateway invoke permission")
        return True
        
    except Exception as e:
        print(f"❌ Error checking/adding permissions: {e}")
        return False

def test_fixed_integration():
    """Test the fixed integration"""
    
    print("\n🧪 Testing Fixed Integration")
    print("-" * 30)
    
    # Test Lambda direct invocation first
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/latest",
        "pathParameters": {"deviceId": "ESP32-001"},
        "queryStringParameters": None,
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user",
                    "cognito:username": "testuser",
                    "email": "test@example.com"
                }
            }
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            print("✅ Lambda direct test: SUCCESS")
            return True
        else:
            print(f"❌ Lambda direct test failed: {result.get('statusCode')}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda test error: {e}")
        return False

def main():
    """Main function to fix the integration"""
    
    print("🚀 API Gateway Lambda Integration Fix")
    print("=" * 60)
    
    # Step 1: Fix the integration
    integration_fixed = fix_readings_api_integration()
    
    # Step 2: Verify permissions
    permissions_ok = verify_lambda_permissions()
    
    # Step 3: Test the fix
    test_passed = test_fixed_integration()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if integration_fixed and permissions_ok and test_passed:
        print("🎉 SUCCESS: API Gateway integration fixed!")
        print("✅ Integration updated to correct Lambda function")
        print("✅ Permissions configured correctly")
        print("✅ Lambda function responds correctly")
        print("\nThe readings API should now work with proper authentication.")
        
        print("\n🔧 Next Steps:")
        print("1. Test the API endpoint with authentication")
        print("2. Verify the frontend can now fetch readings data")
        print("3. Confirm device status monitoring didn't break anything")
        
    else:
        print("❌ FAILED: Some issues remain")
        if not integration_fixed:
            print("• Integration update failed")
        if not permissions_ok:
            print("• Permission configuration failed")
        if not test_passed:
            print("• Lambda function test failed")

if __name__ == "__main__":
    main()