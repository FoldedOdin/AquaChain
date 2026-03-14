#!/usr/bin/env python3
"""
Fix the existing /api/v1/readings/{deviceId}/latest endpoint integration.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    # The existing resource ID for /api/v1/readings/{deviceId}/latest
    resource_id = 'o47l9d'
    
    print("🔧 Fixing existing readings endpoint integration...")
    print(f"Resource ID: {resource_id}")
    print(f"Path: /api/v1/readings/{{deviceId}}/latest")
    
    try:
        # Check current GET method
        print("\n📋 Checking GET method...")
        method = apigateway.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET'
        )
        
        print(f"   Authorization: {method.get('authorizationType')}")
        print(f"   Authorizer ID: {method.get('authorizerId')}")
        
        # Check current integration
        print("\n📋 Checking integration...")
        try:
            integration = apigateway.get_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET'
            )
            
            print(f"   Type: {integration.get('type')}")
            print(f"   URI: {integration.get('uri')}")
            
            if integration.get('type') == 'AWS_PROXY':
                print("   ✅ Lambda proxy integration exists")
            else:
                print("   ❌ Not a Lambda proxy integration")
                
        except ClientError as e:
            print(f"   ❌ No integration found: {e}")
            integration = None
        
        # Find the readings Lambda function
        lambda_function_name = 'aquachain-function-readings-service-dev'
        lambda_arn = f'arn:aws:lambda:ap-south-1:339713024676:function:{lambda_function_name}'
        
        print(f"\n🔧 Setting up Lambda integration...")
        print(f"   Function: {lambda_function_name}")
        
        # Create or update Lambda integration
        if not integration or integration.get('type') != 'AWS_PROXY':
            print("   📝 Creating Lambda proxy integration...")
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            print("   ✅ Created Lambda integration")
        else:
            print("   ✅ Lambda integration already exists")
        
        # Grant API Gateway permission to invoke Lambda
        print("\n🔐 Setting up Lambda permissions...")
        
        try:
            statement_id = f'apigateway-{api_id}-{resource_id}-GET'
            source_arn = f'arn:aws:execute-api:ap-south-1:339713024676:{api_id}/*/GET/api/v1/readings/*/latest'
            
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            print("   ✅ Added Lambda permission")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                print("   ✅ Lambda permission already exists")
            else:
                print(f"   ⚠️  Could not add Lambda permission: {e}")
        
        # Check and fix Cognito authorizer
        print("\n🔐 Checking Cognito authorizer...")
        
        authorizers = apigateway.get_authorizers(restApiId=api_id)
        cognito_authorizer = None
        
        for auth in authorizers['items']:
            if auth['type'] == 'COGNITO_USER_POOLS':
                cognito_authorizer = auth
                print(f"   ✅ Found Cognito authorizer: {auth['id']}")
                break
        
        if not cognito_authorizer:
            print("   ❌ No Cognito authorizer found")
            return
        
        # Update method to use correct authorizer
        current_auth_id = method.get('authorizerId')
        if current_auth_id != cognito_authorizer['id']:
            print(f"   📝 Updating authorizer from {current_auth_id} to {cognito_authorizer['id']}")
            
            # We need to recreate the method with correct authorizer
            # First delete the method
            try:
                apigateway.delete_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET'
                )
                print("   🗑️  Deleted old method")
            except ClientError as e:
                print(f"   ⚠️  Could not delete method: {e}")
            
            # Recreate with correct authorizer
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='COGNITO_USER_POOLS',
                authorizerId=cognito_authorizer['id']
            )
            
            # Add method response
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            
            # Recreate integration
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            # Add integration response
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            print("   ✅ Recreated method with correct authorizer")
        else:
            print("   ✅ Authorizer is correct")
        
        # Deploy the API
        print("\n🚀 Deploying API...")
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix readings endpoint integration'
        )
        print(f"   ✅ Deployed (ID: {deployment['id']})")
        
        # Test the endpoint
        print(f"\n🧪 Test the endpoint:")
        print(f"   curl -H 'Authorization: Bearer <JWT>' https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
        
        print(f"\n✅ Endpoint should now work with proper authentication!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()