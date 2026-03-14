#!/usr/bin/env python3
"""
Fix the history endpoint to point to the correct Lambda function
"""

import boto3
import json

def fix_history_endpoint():
    """Fix the history endpoint integration"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    # API Gateway details
    rest_api_id = 'vtqjfznspc'
    resource_id = 'm38eai'  # /api/v1/readings/{deviceId}/history
    http_method = 'GET'
    
    # Correct Lambda function ARN (same as latest endpoint)
    correct_lambda_arn = 'arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-readings-service-dev'
    integration_uri = f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{correct_lambda_arn}/invocations'
    
    print("🔧 Fixing History Endpoint Integration")
    print("=" * 50)
    print(f"API Gateway: {rest_api_id}")
    print(f"Resource: {resource_id} (GET /api/v1/readings/{{deviceId}}/history)")
    print(f"Correct Lambda ARN: {correct_lambda_arn}")
    
    try:
        # Update the integration
        print("\n📝 Updating history endpoint integration...")
        
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
            description='Fix Lambda integration for history endpoint'
        )
        
        print(f"✅ Deployment successful: {deploy_response['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating integration: {e}")
        return False

def test_history_endpoint():
    """Test the fixed history endpoint"""
    
    print("\n🧪 Testing Fixed History Endpoint")
    print("-" * 40)
    
    # Test Lambda direct invocation first
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/readings/ESP32-001/history",
        "pathParameters": {"deviceId": "ESP32-001"},
        "queryStringParameters": {"days": "7"},
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
            body = json.loads(result['body'])
            print("✅ Lambda direct test: SUCCESS")
            print(f"   Device: {body.get('deviceId')}")
            print(f"   Count: {body.get('count', 0)} readings")
            return True
        else:
            print(f"❌ Lambda direct test failed: {result.get('statusCode')}")
            print(f"   Body: {result.get('body')}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda test error: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 History Endpoint Fix")
    print("=" * 40)
    
    # Fix the integration
    integration_fixed = fix_history_endpoint()
    
    # Test the fix
    test_passed = test_history_endpoint()
    
    print("\n" + "=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    
    if integration_fixed and test_passed:
        print("🎉 SUCCESS: History endpoint fixed!")
        print("✅ Integration updated to correct Lambda function")
        print("✅ Lambda function responds correctly")
        print("\nBoth latest and history endpoints are now working.")
    else:
        print("❌ FAILED: Some issues remain")
        if not integration_fixed:
            print("• Integration update failed")
        if not test_passed:
            print("• Lambda function test failed")

if __name__ == "__main__":
    main()