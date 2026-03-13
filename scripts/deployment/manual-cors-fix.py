#!/usr/bin/env python3
"""
Manual CORS fix using AWS CLI to update API Gateway method responses
"""

import boto3
import json
import sys

def fix_cors_for_endpoint(api_id, resource_id, method='GET'):
    """Fix CORS for a specific API Gateway method"""
    
    client = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Update method response to include CORS headers
        response = client.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True
            }
        )
        print(f"✅ Updated method response for {method} on resource {resource_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update method response: {e}")
        return False

def find_api_resources(api_id):
    """Find API Gateway resources"""
    
    client = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        response = client.get_resources(restApiId=api_id)
        resources = response.get('items', [])
        
        print("📋 API Gateway Resources:")
        for resource in resources:
            path = resource.get('pathPart', 'ROOT')
            resource_id = resource.get('id')
            methods = list(resource.get('resourceMethods', {}).keys())
            print(f"  {resource_id}: {path} - Methods: {methods}")
            
        return resources
        
    except Exception as e:
        print(f"❌ Failed to get resources: {e}")
        return []

def main():
    """Manual CORS fix using AWS API"""
    
    # Your API Gateway ID (from the error URL)
    api_id = "vtqjfznspc"
    
    print("🔧 Manual CORS Fix for API Gateway")
    print("=" * 50)
    
    # First, let's see what resources exist
    resources = find_api_resources(api_id)
    
    # Find the 'latest' resource
    latest_resource = None
    for resource in resources:
        if resource.get('pathPart') == 'latest':
            latest_resource = resource
            break
    
    if not latest_resource:
        print("❌ Could not find 'latest' resource")
        return False
    
    print(f"\n🎯 Found 'latest' resource: {latest_resource['id']}")
    
    # Fix CORS for the latest endpoint
    success = fix_cors_for_endpoint(api_id, latest_resource['id'], 'GET')
    
    if success:
        # Deploy the API to make changes live
        client = boto3.client('apigateway', region_name='ap-south-1')
        try:
            client.create_deployment(
                restApiId=api_id,
                stageName='dev',
                description='Manual CORS fix for latest endpoint'
            )
            print("✅ Deployed API changes")
            
            # Test the fix
            print("\n🧪 Testing the fix...")
            import subprocess
            test_script = "scripts/testing/test-cors-fix.py"
            subprocess.run([sys.executable, test_script])
            
        except Exception as e:
            print(f"❌ Failed to deploy: {e}")
            return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)