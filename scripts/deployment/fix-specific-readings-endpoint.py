#!/usr/bin/env python3
"""
Fix the specific readings endpoint that the frontend is calling.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    print("🔧 Fixing specific readings endpoint...")
    
    try:
        # Get all resources to find the exact path
        resources = apigateway.get_resources(restApiId=api_id)
        
        print("\n📋 All API resources:")
        for resource in resources['items']:
            path = resource.get('path', '')
            print(f"   {path} (ID: {resource['id']})")
        
        # Look for the readings path that matches /api/v1/readings/{deviceId}/latest
        target_resource = None
        for resource in resources['items']:
            path = resource.get('path', '')
            if '/readings/' in path and '{deviceId}' in path and 'latest' in path:
                target_resource = resource
                break
            elif path == '/api/v1/readings/{deviceId}/latest':
                target_resource = resource
                break
        
        if not target_resource:
            print("\n❌ Could not find the exact readings endpoint")
            print("   Looking for alternative paths...")
            
            # Try to find any readings-related resource
            for resource in resources['items']:
                path = resource.get('path', '')
                if 'readings' in path.lower():
                    print(f"   Found readings resource: {path}")
                    target_resource = resource
                    break
        
        if not target_resource:
            print("❌ No readings resource found. Creating the endpoint...")
            
            # Find the parent resource (/api/v1/readings/{deviceId})
            parent_resource = None
            for resource in resources['items']:
                path = resource.get('path', '')
                if path == '/api/v1/readings/{deviceId}':
                    parent_resource = resource
                    break
            
            if not parent_resource:
                print("❌ Parent resource not found either")
                return
            
            # Create the 'latest' resource
            latest_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=parent_resource['id'],
                pathPart='latest'
            )
            target_resource = latest_resource
            print(f"✅ Created 'latest' resource: {latest_resource['id']}")
        
        resource_id = target_resource['id']
        resource_path = target_resource.get('path', 'Unknown')
        
        print(f"\n🎯 Working with resource: {resource_path} (ID: {resource_id})")
        
        # Add GET method if it doesn't exist
        try:
            method = apigateway.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET'
            )
            print("✅ GET method exists")
        except ClientError:
            print("📝 Creating GET method...")
            
            # Create GET method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='COGNITO_USER_POOLS',
                authorizerId='your-authorizer-id'  # You may need to find this
            )
            
            # Add method response with CORS
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            
            print("✅ Created GET method")
        
        # Add OPTIONS method for CORS preflight
        try:
            apigateway.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS'
            )
            print("✅ OPTIONS method exists")
        except ClientError:
            print("📝 Creating OPTIONS method...")
            
            # Create OPTIONS method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add method response
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
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
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Add integration response
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                }
            )
            
            print("✅ Created OPTIONS method with CORS")
        
        # Deploy the changes
        print("\n🚀 Deploying changes...")
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix specific readings endpoint CORS'
        )
        print(f"✅ Deployed (ID: {deployment['id']})")
        
        print(f"\n🧪 Test the endpoint:")
        print(f"curl -i https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev{resource_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()