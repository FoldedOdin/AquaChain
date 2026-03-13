#!/usr/bin/env python3
"""
Fix CORS for /api/alerts endpoint
Addresses the 403 preflight error without breaking existing functionality
"""

import boto3
import json
import sys

def fix_cors_for_alerts():
    """Fix CORS configuration for alerts endpoint"""
    
    print("🔧 Starting CORS fix for /api/alerts endpoint...")
    
    # Initialize API Gateway client
    client = boto3.client('apigateway', region_name='ap-south-1')
    
    # Your API Gateway ID (extracted from the URL)
    api_id = 'vtqjfznspc'
    
    try:
        # Step 1: Get the API structure
        print("📋 Step 1: Analyzing API structure...")
        resources = client.get_resources(restApiId=api_id)
        
        alerts_resource_id = None
        for resource in resources['items']:
            if resource['path'] == '/api/alerts':
                alerts_resource_id = resource['id']
                print(f"✅ Found /api/alerts resource: {alerts_resource_id}")
                break
        
        if not alerts_resource_id:
            print("❌ /api/alerts resource not found!")
            return False
            
        # Step 2: Check existing methods
        print("📋 Step 2: Checking existing methods...")
        resource_methods = client.get_resource(
            restApiId=api_id,
            resourceId=alerts_resource_id
        )
        
        existing_methods = resource_methods.get('resourceMethods', {})
        print(f"📦 Existing methods: {list(existing_methods.keys())}")
        
        # Step 3: Add OPTIONS method if missing
        if 'OPTIONS' not in existing_methods:
            print("🔧 Step 3: Adding OPTIONS method...")
            
            client.put_method(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add mock integration for OPTIONS
            client.put_integration(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Add method response for OPTIONS
            client.put_method_response(
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
            client.put_integration_response(
                restApiId=api_id,
                resourceId=alerts_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            print("✅ OPTIONS method added successfully")
        else:
            print("✅ OPTIONS method already exists")
            
        # Step 4: Deploy the API
        print("🚀 Step 4: Deploying API changes...")
        client.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix CORS for alerts endpoint'
        )
        
        print("✅ API deployed successfully!")
        print("🎯 CORS fix complete - the /api/alerts endpoint should now work")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing CORS: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_cors_for_alerts()
    sys.exit(0 if success else 1)