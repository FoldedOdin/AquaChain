#!/usr/bin/env python3
"""
Fix CORS issues for the readings API endpoint
"""

import boto3
import json

def check_api_gateway_cors():
    """Check current API Gateway CORS configuration"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        # Find the API Gateway
        apis = apigateway.get_rest_apis()
        
        aquachain_api = None
        for api in apis['items']:
            if 'aquachain' in api['name'].lower():
                aquachain_api = api
                break
        
        if not aquachain_api:
            print("❌ No AquaChain API Gateway found")
            return None
        
        api_id = aquachain_api['id']
        api_name = aquachain_api['name']
        
        print(f"✅ Found API Gateway: {api_name} ({api_id})")
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"\n📋 API Resources:")
        readings_resource = None
        
        for resource in resources['items']:
            path = resource['pathPart'] if 'pathPart' in resource else resource['path']
            resource_id = resource['id']
            
            print(f"   {path} ({resource_id})")
            
            # Look for readings resource
            if 'readings' in path.lower() or 'latest' in path.lower():
                readings_resource = resource
                print(f"     📍 Found readings resource: {path}")
        
        return api_id, readings_resource
        
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")
        return None, None

def add_cors_to_resource(api_id, resource_id, resource_path):
    """Add CORS headers to a specific resource"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        print(f"\n🔧 Adding CORS to resource: {resource_path} ({resource_id})")
        
        # Check if OPTIONS method exists
        try:
            methods = apigateway.get_resource(
                restApiId=api_id,
                resourceId=resource_id
            )
            
            existing_methods = methods.get('resourceMethods', {})
            print(f"   Existing methods: {list(existing_methods.keys())}")
            
            # Add OPTIONS method if it doesn't exist
            if 'OPTIONS' not in existing_methods:
                print(f"   Adding OPTIONS method...")
                
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Add integration for OPTIONS
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={
                        'application/json': '{"statusCode": 200}'
                    }
                )
                
                # Add method response for OPTIONS
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': False,
                        'method.response.header.Access-Control-Allow-Methods': False,
                        'method.response.header.Access-Control-Allow-Headers': False
                    }
                )
                
                # Add integration response for OPTIONS
                apigateway.put_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
                
                print(f"   ✅ Added OPTIONS method with CORS headers")
            else:
                print(f"   ✅ OPTIONS method already exists")
            
            # Add CORS headers to existing methods
            for method in existing_methods.keys():
                if method != 'OPTIONS':
                    print(f"   Adding CORS headers to {method} method...")
                    
                    try:
                        # Add CORS headers to method response
                        apigateway.put_method_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': False
                            }
                        )
                        
                        # Update integration response to include CORS headers
                        apigateway.put_integration_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': "'*'"
                            }
                        )
                        
                        print(f"     ✅ Added CORS headers to {method}")
                        
                    except Exception as e:
                        print(f"     ⚠️ Could not add CORS to {method}: {e}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error adding CORS: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error in add_cors_to_resource: {e}")
        return False

def deploy_api_changes(api_id):
    """Deploy the API changes"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        print(f"\n🚀 Deploying API changes...")
        
        # Create deployment
        response = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='CORS fix for readings API'
        )
        
        deployment_id = response['id']
        print(f"✅ Deployment created: {deployment_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying API: {e}")
        return False

def test_cors_fix():
    """Test the CORS fix by making a request"""
    try:
        import requests
        
        api_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        print(f"\n🧪 Testing CORS fix...")
        print(f"   URL: {api_url}")
        
        # Make OPTIONS request to check CORS
        options_response = requests.options(api_url)
        
        print(f"📋 OPTIONS Response:")
        print(f"   Status: {options_response.status_code}")
        print(f"   Headers: {dict(options_response.headers)}")
        
        # Check for CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"\n📋 CORS Headers:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"   {status} {header}: {value or 'Missing'}")
        
        # Make GET request to check actual endpoint
        try:
            get_response = requests.get(api_url, timeout=10)
            print(f"\n📋 GET Response:")
            print(f"   Status: {get_response.status_code}")
            print(f"   CORS Origin: {get_response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
            
            if get_response.status_code == 200:
                print(f"   ✅ API endpoint is working")
            else:
                print(f"   ⚠️ API returned {get_response.status_code}: {get_response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ GET request failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")
        return False

def main():
    print("🔧 Fixing CORS for Readings API")
    print("=" * 35)
    
    # Step 1: Check current API Gateway configuration
    print("\n1. Checking API Gateway configuration...")
    api_id, readings_resource = check_api_gateway_cors()
    
    if not api_id:
        print("❌ Could not find API Gateway")
        return
    
    # Step 2: Add CORS to all resources (not just readings)
    print("\n2. Adding CORS headers to API resources...")
    
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        cors_added = False
        for resource in resources['items']:
            resource_id = resource['id']
            resource_path = resource.get('pathPart', resource.get('path', 'unknown'))
            
            # Skip root resource
            if resource_path == '/':
                continue
            
            print(f"\n   Processing resource: {resource_path}")
            
            if add_cors_to_resource(api_id, resource_id, resource_path):
                cors_added = True
        
        if cors_added:
            # Step 3: Deploy changes
            print("\n3. Deploying API changes...")
            if deploy_api_changes(api_id):
                print("✅ API deployment successful")
                
                # Step 4: Test the fix
                print("\n4. Testing CORS fix...")
                test_cors_fix()
                
                print(f"\n🎉 CORS fix completed!")
                print(f"✅ API Gateway has been updated with CORS headers")
                print(f"✅ Frontend should now be able to make API requests")
                print(f"\nTry refreshing your dashboard - the CORS errors should be resolved!")
            else:
                print("❌ API deployment failed")
        else:
            print("⚠️ No CORS changes were made")
    
    except Exception as e:
        print(f"❌ Error in main process: {e}")

if __name__ == "__main__":
    main()