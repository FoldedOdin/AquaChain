#!/usr/bin/env python3
"""
Fix CORS for the /latest endpoint by adding OPTIONS method
"""

import boto3
import json
import sys

def add_options_method(api_id, resource_id):
    """Add OPTIONS method to a resource"""
    
    client = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Add OPTIONS method
        response = client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'  # OPTIONS should not require auth
        )
        print(f"✅ Added OPTIONS method to resource {resource_id}")
        
        # Add method response for OPTIONS
        client.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='204',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Credentials': True
            }
        )
        print(f"✅ Added method response for OPTIONS")
        
        # Add integration (mock integration for OPTIONS)
        client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 204}'
            }
        )
        print(f"✅ Added mock integration for OPTIONS")
        
        # Add integration response
        client.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='204',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Requested-With'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Credentials': "'true'"
            }
        )
        print(f"✅ Added integration response for OPTIONS")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add OPTIONS method: {e}")
        return False

def main():
    """Fix CORS for latest endpoint"""
    
    # Your API Gateway ID
    api_id = "vtqjfznspc"
    
    # Resource ID for 'latest' endpoint (from previous output)
    latest_resource_id = "7v02j2"
    
    print("🔧 Adding OPTIONS method to /latest endpoint")
    print("=" * 50)
    
    # Add OPTIONS method to latest resource
    success = add_options_method(api_id, latest_resource_id)
    
    if success:
        # Deploy the API to make changes live
        client = boto3.client('apigateway', region_name='ap-south-1')
        try:
            client.create_deployment(
                restApiId=api_id,
                stageName='dev',
                description='Add OPTIONS method to latest endpoint'
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