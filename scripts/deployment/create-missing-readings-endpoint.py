#!/usr/bin/env python3
"""
Create the missing /api/v1/readings/{deviceId}/latest endpoint in API Gateway.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    print("🔧 Creating missing readings endpoint...")
    
    try:
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        resource_map = {r['path']: r for r in resources['items']}
        
        print("📋 Current resources:")
        for path in sorted(resource_map.keys()):
            print(f"   {path}")
        
        # Find or create the resource hierarchy
        # We need: /api/v1/readings/{deviceId}/latest
        
        # Step 1: Find /api/v1 (should exist)
        api_v1_resource = resource_map.get('/api/v1')
        if not api_v1_resource:
            print("❌ /api/v1 resource not found")
            return
        
        print(f"✅ Found /api/v1 resource: {api_v1_resource['id']}")
        
        # Step 2: Create /api/v1/readings if it doesn't exist
        readings_path = '/api/v1/readings'
        readings_resource = resource_map.get(readings_path)
        
        if not readings_resource:
            print("📝 Creating /api/v1/readings resource...")
            readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=api_v1_resource['id'],
                pathPart='readings'
            )
            print(f"✅ Created readings resource: {readings_resource['id']}")
        else:
            print(f"✅ Found readings resource: {readings_resource['id']}")
        
        # Step 3: Create /api/v1/readings/{deviceId} if it doesn't exist
        device_path = '/api/v1/readings/{deviceId}'
        device_resource = resource_map.get(device_path)
        
        if not device_resource:
            print("📝 Creating /api/v1/readings/{deviceId} resource...")
            device_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=readings_resource['id'],
                pathPart='{deviceId}'
            )
            print(f"✅ Created device resource: {device_resource['id']}")
        else:
            print(f"✅ Found device resource: {device_resource['id']}")
        
        # Step 4: Create /api/v1/readings/{deviceId}/latest if it doesn't exist
        latest_path = '/api/v1/readings/{deviceId}/latest'
        latest_resource = resource_map.get(latest_path)
        
        if not latest_resource:
            print("📝 Creating /api/v1/readings/{deviceId}/latest resource...")
            latest_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_resource['id'],
                pathPart='latest'
            )
            print(f"✅ Created latest resource: {latest_resource['id']}")
        else:
            print(f"✅ Found latest resource: {latest_resource['id']}")
        
        # Step 5: Find the Cognito authorizer
        authorizers = apigateway.get_authorizers(restApiId=api_id)
        cognito_authorizer = None
        
        for auth in authorizers['items']:
            if auth['type'] == 'COGNITO_USER_POOLS':
                cognito_authorizer = auth
                print(f"✅ Found Cognito authorizer: {auth['id']}")
                break
        
        if not cognito_authorizer:
            print("❌ No Cognito authorizer found")
            return
        
        # Step 6: Add GET method to latest resource
        try:
            method = apigateway.get_method(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET'
            )
            print("✅ GET method already exists")
        except ClientError:
            print("📝 Creating GET method...")
            
            # Create GET method with Cognito auth
            apigateway.put_method(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET',
                authorizationType='COGNITO_USER_POOLS',
                authorizerId=cognito_authorizer['id']
            )
            
            # Add method response
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            
            print("✅ Created GET method with Cognito auth")
        
        # Step 7: Add Lambda integration
        lambda_function_name = 'aquachain-function-readings-service-dev'
        lambda_arn = f'arn:aws:lambda:ap-south-1:339713024676:function:{lambda_function_name}'
        
        try:
            integration = apigateway.get_integration(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET'
            )
            print("✅ Lambda integration already exists")
        except ClientError:
            print("📝 Creating Lambda integration...")
            
            # Create Lambda integration
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            # Add integration response
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            print("✅ Created Lambda integration")
        
        # Step 8: Add OPTIONS method for CORS
        try:
            options_method = apigateway.get_method(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='OPTIONS'
            )
            print("✅ OPTIONS method already exists")
        except ClientError:
            print("📝 Creating OPTIONS method for CORS...")
            
            # Create OPTIONS method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add method response
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            )
            
            # Add mock integration
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Add integration response
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=latest_resource['id'],
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'"
                }
            )
            
            print("✅ Created OPTIONS method")
        
        # Step 9: Grant API Gateway permission to invoke Lambda
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        try:
            statement_id = f'apigateway-{api_id}-{latest_resource["id"]}-GET'
            source_arn = f'arn:aws:execute-api:ap-south-1:339713024676:{api_id}/*/GET/api/v1/readings/*/latest'
            
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            print("✅ Added Lambda permission")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                print("✅ Lambda permission already exists")
            else:
                print(f"⚠️  Could not add Lambda permission: {e}")
        
        # Step 10: Deploy the API
        print("🚀 Deploying API...")
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Add missing readings endpoint'
        )
        print(f"✅ Deployed (ID: {deployment['id']})")
        
        print(f"\n🎉 Success! The endpoint should now work:")
        print(f"   https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()