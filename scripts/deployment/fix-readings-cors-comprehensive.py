#!/usr/bin/env python3
"""
Comprehensive fix for readings API CORS issues.
This script addresses all potential causes of the 400 error with missing CORS headers.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def main():
    # Initialize AWS clients
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    # Your API Gateway ID (extracted from the URL)
    api_id = 'vtqjfznspc'
    
    print("🔧 Starting comprehensive CORS fix for readings API...")
    
    try:
        # Step 1: Fix Gateway Responses for 4XX and 5XX errors
        print("\n1️⃣ Fixing Gateway Response CORS headers...")
        
        gateway_responses = ['DEFAULT_4XX', 'DEFAULT_5XX']
        
        for response_type in gateway_responses:
            try:
                # Update gateway response to include CORS headers
                apigateway.update_gateway_response(
                    restApiId=api_id,
                    responseType=response_type,
                    patchOperations=[
                        {
                            'op': 'add',
                            'path': '/responseParameters/gatewayresponse.header.Access-Control-Allow-Origin',
                            'value': "'*'"
                        },
                        {
                            'op': 'add',
                            'path': '/responseParameters/gatewayresponse.header.Access-Control-Allow-Headers',
                            'value': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
                        },
                        {
                            'op': 'add',
                            'path': '/responseParameters/gatewayresponse.header.Access-Control-Allow-Methods',
                            'value': "'GET,POST,PUT,DELETE,OPTIONS'"
                        }
                    ]
                )
                print(f"   ✅ Updated {response_type} gateway response")
            except ClientError as e:
                if 'NotFoundException' in str(e):
                    # Create gateway response if it doesn't exist
                    apigateway.put_gateway_response(
                        restApiId=api_id,
                        responseType=response_type,
                        responseParameters={
                            'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                            'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                        }
                    )
                    print(f"   ✅ Created {response_type} gateway response")
                else:
                    print(f"   ❌ Error updating {response_type}: {e}")
        
        # Step 2: Find and fix the readings resource
        print("\n2️⃣ Finding readings API resources...")
        
        resources = apigateway.get_resources(restApiId=api_id)
        readings_resource = None
        latest_resource = None
        
        for resource in resources['items']:
            path = resource.get('pathPart', '')
            full_path = resource.get('path', '')
            
            print(f"   Found resource: {full_path} (pathPart: {path})")
            
            if 'readings' in path.lower():
                readings_resource = resource
            elif '{deviceId}' in path or 'latest' in path.lower():
                latest_resource = resource
        
        if not readings_resource and not latest_resource:
            print("   ❌ Could not find readings or latest resource")
            return
        
        target_resource = latest_resource or readings_resource
        resource_id = target_resource['id']
        
        print(f"   ✅ Using resource: {target_resource.get('path', 'Unknown')} (ID: {resource_id})")
        
        # Step 3: Add OPTIONS method if it doesn't exist
        print("\n3️⃣ Adding OPTIONS method for CORS preflight...")
        
        try:
            # Check if OPTIONS method exists
            try:
                apigateway.get_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS'
                )
                print("   ✅ OPTIONS method already exists")
            except ClientError:
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
                
                # Add integration
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
                
                print("   ✅ Created OPTIONS method with CORS headers")
        
        except ClientError as e:
            print(f"   ❌ Error setting up OPTIONS method: {e}")
        
        # Step 4: Fix GET method CORS headers
        print("\n4️⃣ Fixing GET method CORS headers...")
        
        try:
            # Add CORS headers to GET method response
            try:
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
                print("   ✅ Added CORS headers to GET method response")
            except ClientError as e:
                if 'ConflictException' in str(e):
                    print("   ✅ GET method response already configured")
                else:
                    print(f"   ⚠️  Could not update GET method response: {e}")
            
            # Update integration response to include CORS headers
            try:
                apigateway.update_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    statusCode='200',
                    patchOperations=[
                        {
                            'op': 'add',
                            'path': '/responseParameters/method.response.header.Access-Control-Allow-Origin',
                            'value': "'*'"
                        }
                    ]
                )
                print("   ✅ Updated GET integration response with CORS")
            except ClientError as e:
                print(f"   ⚠️  Could not update GET integration response: {e}")
        
        except ClientError as e:
            print(f"   ❌ Error fixing GET method: {e}")
        
        # Step 5: Deploy the API
        print("\n5️⃣ Deploying API changes...")
        
        try:
            deployment = apigateway.create_deployment(
                restApiId=api_id,
                stageName='dev',
                description='Fix CORS headers for readings endpoint'
            )
            print(f"   ✅ Deployed to dev stage (Deployment ID: {deployment['id']})")
        except ClientError as e:
            print(f"   ❌ Error deploying API: {e}")
        
        # Step 6: Test the fix
        print("\n6️⃣ Testing the fix...")
        print("   Run this command to test:")
        print(f"   curl -i -H 'Origin: http://localhost:3000' https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
        print("\n   Expected response should include:")
        print("   Access-Control-Allow-Origin: *")
        
        print("\n✅ CORS fix completed! The API should now work with your frontend.")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()