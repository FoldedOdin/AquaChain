#!/usr/bin/env python3
"""
Debug API Gateway integration issues.
"""

import boto3
import json
from botocore.exceptions import ClientError

def check_integration():
    """Check the API Gateway integration details"""
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    resource_id = 'o47l9d'  # /api/v1/readings/{deviceId}/latest
    
    print("🔍 Checking API Gateway integration...")
    print(f"API ID: {api_id}")
    print(f"Resource ID: {resource_id}")
    
    try:
        # Check the integration
        integration = apigateway.get_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET'
        )
        
        print(f"\n📋 Integration Details:")
        print(f"   Type: {integration.get('type')}")
        print(f"   HTTP Method: {integration.get('httpMethod')}")
        print(f"   URI: {integration.get('uri')}")
        
        # Check if URI is correct
        expected_function = 'aquachain-function-readings-service-dev'
        if expected_function in integration.get('uri', ''):
            print(f"   ✅ URI points to correct function")
        else:
            print(f"   ❌ URI points to wrong function")
            print(f"   Expected: {expected_function}")
        
        # Check method details
        method = apigateway.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET'
        )
        
        print(f"\n📋 Method Details:")
        print(f"   Authorization: {method.get('authorizationType')}")
        print(f"   Authorizer ID: {method.get('authorizerId')}")
        
        # Check Lambda permissions
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        try:
            policy = lambda_client.get_policy(
                FunctionName=expected_function
            )
            
            policy_doc = json.loads(policy['Policy'])
            print(f"\n📋 Lambda Permissions:")
            
            api_gateway_permissions = []
            for statement in policy_doc.get('Statement', []):
                if statement.get('Principal', {}).get('Service') == 'apigateway.amazonaws.com':
                    api_gateway_permissions.append(statement)
            
            if api_gateway_permissions:
                print(f"   ✅ Found {len(api_gateway_permissions)} API Gateway permissions")
                for perm in api_gateway_permissions:
                    source_arn = perm.get('Condition', {}).get('StringEquals', {}).get('AWS:SourceArn', 'Unknown')
                    print(f"   - {source_arn}")
            else:
                print(f"   ❌ No API Gateway permissions found")
                
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                print(f"   ❌ Lambda function not found: {expected_function}")
            else:
                print(f"   ❌ Error checking Lambda permissions: {e}")
        
        # Test Lambda function directly
        print(f"\n🧪 Testing Lambda function directly...")
        
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/readings/ESP32-001/latest",
            "pathParameters": {
                "deviceId": "ESP32-001"
            },
            "queryStringParameters": None,
            "headers": {
                "Authorization": "Bearer test-token"
            },
            "requestContext": {
                "requestId": "test-request-id"
            }
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=expected_function,
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"   Status: {result.get('statusCode')}")
            
            if result.get('statusCode') == 200:
                print(f"   ✅ Lambda function works correctly")
            else:
                print(f"   ⚠️  Lambda returned: {result.get('statusCode')}")
                body = json.loads(result.get('body', '{}'))
                print(f"   Response: {body}")
                
        except Exception as e:
            print(f"   ❌ Error testing Lambda: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error checking integration: {e}")
        return False

def main():
    print("🚀 Debugging API Gateway integration...\n")
    
    success = check_integration()
    
    if success:
        print(f"\n💡 Next steps:")
        print(f"1. If Lambda works but API Gateway returns 500:")
        print(f"   - Check Lambda permissions")
        print(f"   - Verify integration URI")
        print(f"   - Check method configuration")
        print(f"2. If Lambda doesn't work:")
        print(f"   - Check Lambda code")
        print(f"   - Check DynamoDB table access")

if __name__ == "__main__":
    main()