#!/usr/bin/env python3
"""
Find the correct API Gateway for AquaChain readings API
"""

import boto3
import json

def find_all_api_gateways():
    """Find all API Gateways and identify the correct one"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        # Get all APIs
        apis = apigateway.get_rest_apis()
        
        print(f"📋 Found {len(apis['items'])} API Gateways:")
        
        for api in apis['items']:
            api_id = api['id']
            api_name = api['name']
            created_date = api['createdDate']
            
            print(f"\n🔍 API: {api_name} ({api_id})")
            print(f"   Created: {created_date}")
            
            # Get resources for this API
            try:
                resources = apigateway.get_resources(restApiId=api_id)
                
                print(f"   Resources ({len(resources['items'])}):")
                
                has_readings = False
                has_v1 = False
                
                for resource in resources['items']:
                    path = resource.get('pathPart', resource.get('path', '/'))
                    resource_id = resource['id']
                    
                    print(f"     {path} ({resource_id})")
                    
                    if 'readings' in path.lower():
                        has_readings = True
                    if 'v1' in path.lower():
                        has_v1 = True
                
                # Check if this looks like the main AquaChain API
                if has_readings or has_v1:
                    print(f"   🎯 This looks like the main AquaChain API!")
                    return api_id, api_name
                    
            except Exception as e:
                print(f"   ❌ Error getting resources: {e}")
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error finding API Gateways: {e}")
        return None, None

def check_specific_endpoint():
    """Check if the specific endpoint exists by testing it"""
    try:
        import requests
        
        # The endpoint from the error message
        test_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        print(f"\n🧪 Testing specific endpoint:")
        print(f"   URL: {test_url}")
        
        # Extract API ID from URL
        api_id_from_url = test_url.split('//')[1].split('.')[0]
        print(f"   API ID from URL: {api_id_from_url}")
        
        # Test OPTIONS request
        try:
            response = requests.options(test_url, timeout=10)
            print(f"   OPTIONS Status: {response.status_code}")
            print(f"   CORS Headers: {response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
        except Exception as e:
            print(f"   OPTIONS Error: {e}")
        
        # Test GET request
        try:
            response = requests.get(test_url, timeout=10)
            print(f"   GET Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   GET Error: {e}")
        
        return api_id_from_url
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return None

def fix_cors_for_specific_api(api_id):
    """Fix CORS for the specific API Gateway"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        print(f"\n🔧 Fixing CORS for API Gateway: {api_id}")
        
        # Get API details
        try:
            api_info = apigateway.get_rest_api(restApiId=api_id)
            print(f"   API Name: {api_info['name']}")
        except Exception as e:
            print(f"   ⚠️ Could not get API info: {e}")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"   Found {len(resources['items'])} resources")
        
        # Add CORS to all resources
        for resource in resources['items']:
            resource_id = resource['id']
            path = resource.get('pathPart', resource.get('path', '/'))
            
            if path == '/':
                continue  # Skip root
            
            print(f"\n   🔧 Processing: {path} ({resource_id})")
            
            try:
                # Get existing methods
                resource_methods = resource.get('resourceMethods', {})
                
                if not resource_methods:
                    print(f"     No methods found, skipping")
                    continue
                
                print(f"     Methods: {list(resource_methods.keys())}")
                
                # Add OPTIONS method if missing
                if 'OPTIONS' not in resource_methods:
                    print(f"     Adding OPTIONS method...")
                    
                    # Create OPTIONS method
                    apigateway.put_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        authorizationType='NONE'
                    )
                    
                    # Add mock integration
                    apigateway.put_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        type='MOCK',
                        requestTemplates={'application/json': '{"statusCode": 200}'}
                    )
                    
                    # Add method response
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
                    
                    # Add integration response
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
                    
                    print(f"     ✅ Added OPTIONS method")
                
                # Add CORS to existing methods
                for method in resource_methods.keys():
                    if method == 'OPTIONS':
                        continue
                    
                    print(f"     Adding CORS to {method}...")
                    
                    try:
                        # Try to update method response
                        apigateway.put_method_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': False
                            }
                        )
                        
                        # Try to update integration response
                        apigateway.put_integration_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': "'*'"
                            }
                        )
                        
                        print(f"       ✅ Added CORS to {method}")
                        
                    except Exception as method_error:
                        print(f"       ⚠️ Could not add CORS to {method}: {method_error}")
                
            except Exception as resource_error:
                print(f"     ❌ Error processing resource: {resource_error}")
        
        # Deploy changes
        print(f"\n🚀 Deploying changes...")
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='CORS fix for readings API'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing CORS: {e}")
        return False

def main():
    print("🔍 Finding Correct API Gateway for CORS Fix")
    print("=" * 45)
    
    # Step 1: Find all API Gateways
    print("\n1. Scanning all API Gateways...")
    main_api_id, main_api_name = find_all_api_gateways()
    
    # Step 2: Check the specific endpoint
    print("\n2. Testing the specific endpoint...")
    url_api_id = check_specific_endpoint()
    
    # Step 3: Use the API ID from URL if we found it
    target_api_id = url_api_id or main_api_id
    
    if target_api_id:
        print(f"\n3. Fixing CORS for API: {target_api_id}")
        if fix_cors_for_specific_api(target_api_id):
            print(f"\n🎉 CORS fix completed!")
            print(f"✅ API Gateway {target_api_id} updated with CORS headers")
            print(f"✅ Try refreshing your dashboard now!")
        else:
            print(f"\n❌ CORS fix failed")
    else:
        print(f"\n❌ Could not identify the correct API Gateway")

if __name__ == "__main__":
    main()