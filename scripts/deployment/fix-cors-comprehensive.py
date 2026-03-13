#!/usr/bin/env python3
"""
Comprehensive CORS Fix for AquaChain API
Fixes the 403 preflight error on /api/alerts endpoint
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError

def fix_cors_comprehensive():
    """Fix CORS issues comprehensively"""
    
    print("🔧 Starting comprehensive CORS fix...")
    
    # Initialize clients
    apigateway_client = boto3.client('apigateway', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Your API Gateway ID
    api_id = 'vtqjfznspc'
    
    try:
        # Step 1: Analyze current API structure
        print("📋 Step 1: Analyzing API structure...")
        resources = apigateway_client.get_resources(restApiId=api_id)
        
        # Find all relevant resources
        api_root_id = None
        alerts_resource_id = None
        
        for resource in resources['items']:
            print(f"📦 Resource: {resource['path']} (ID: {resource['id']})")
            
            if resource['path'] == '/api':
                api_root_id = resource['id']
            elif resource['path'] == '/api/alerts':
                alerts_resource_id = resource['id']
        
        if not api_root_id:
            print("❌ /api root resource not found!")
            return False
            
        # Step 2: Check if alerts resource exists
        if not alerts_resource_id:
            print("🔧 Step 2: Creating /api/alerts resource...")
            
            # Create alerts resource under /api
            alerts_response = apigateway_client.create_resource(
                restApiId=api_id,
                parentId=api_root_id,
                pathPart='alerts'
            )
            alerts_resource_id = alerts_response['id']
            print(f"✅ Created /api/alerts resource: {alerts_resource_id}")
        else:
            print(f"✅ Found existing /api/alerts resource: {alerts_resource_id}")
        
        # Step 3: Check existing methods on alerts resource
        print("📋 Step 3: Checking methods on /api/alerts...")
        alerts_resource = apigateway_client.get_resource(
            restApiId=api_id,
            resourceId=alerts_resource_id
        )
        
        existing_methods = alerts_resource.get('resourceMethods', {})
        print(f"📦 Existing methods on /api/alerts: {list(existing_methods.keys())}")
        
        # Step 4: Add OPTIONS method if missing
        if 'OPTIONS' not in existing_methods:
            print("🔧 Step 4: Adding OPTIONS method for CORS...")
            
            # Add OPTIONS method
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add mock integration for OPTIONS
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Add method response for OPTIONS
            apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False,
                    'method.response.header.Access-Control-Allow-Origin': False
                }
            )
            
            # Add integration response for OPTIONS
            apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            print("✅ OPTIONS method added successfully")
        else:
            print("✅ OPTIONS method already exists")
        
        # Step 5: Ensure GET method exists with proper CORS
        if 'GET' not in existing_methods:
            print("🔧 Step 5: Adding GET method...")
            
            # Find the alert detection Lambda function
            lambda_functions = lambda_client.list_functions()
            alert_lambda_arn = None
            
            for func in lambda_functions['Functions']:
                if 'alert' in func['FunctionName'].lower():
                    alert_lambda_arn = func['FunctionArn']
                    print(f"📦 Found alert Lambda: {func['FunctionName']}")
                    break
            
            if alert_lambda_arn:
                # Add GET method
                apigateway_client.put_method(
                    restApiId=api_id,
                    resourceId=alerts_resource_id,
                    httpMethod='GET',
                    authorizationType='COGNITO_USER_POOLS',
                    authorizerId='your-authorizer-id'  # You'll need to get this
                )
                
                # Add Lambda integration
                apigateway_client.put_integration(
                    restApiId=api_id,
                    resourceId=alerts_resource_id,
                    httpMethod='GET',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{alert_lambda_arn}/invocations'
                )
                
                print("✅ GET method added successfully")
            else:
                print("⚠️ No alert Lambda function found - skipping GET method")
        
        # Step 6: Deploy the API
        print("🚀 Step 6: Deploying API changes...")
        apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix CORS for alerts endpoint - comprehensive fix'
        )
        
        print("✅ API deployed successfully!")
        print("🎯 Comprehensive CORS fix complete!")
        print("🔍 Test the endpoint: https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/alerts")
        
        return True
        
    except ClientError as e:
        print(f"❌ AWS API Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_cors_comprehensive()
    sys.exit(0 if success else 1)