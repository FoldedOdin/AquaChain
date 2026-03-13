#!/usr/bin/env python3
"""
Debug the /latest endpoint to understand why CORS is failing
"""

import boto3
import json
import sys

def get_resource_details(api_id, resource_id):
    """Get detailed information about a resource"""
    
    client = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Get resource details
        resource = client.get_resource(
            restApiId=api_id,
            resourceId=resource_id
        )
        
        print(f"📋 Resource Details for {resource_id}:")
        print(f"  Path: {resource.get('pathPart', 'ROOT')}")
        print(f"  Parent: {resource.get('parentId', 'None')}")
        
        # Get methods
        methods = resource.get('resourceMethods', {})
        print(f"  Methods: {list(methods.keys())}")
        
        # Check each method
        for method in methods:
            try:
                method_details = client.get_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method
                )
                
                print(f"\n  🔍 Method {method}:")
                print(f"    Authorization: {method_details.get('authorizationType', 'None')}")
                print(f"    Authorizer: {method_details.get('authorizerId', 'None')}")
                print(f"    API Key Required: {method_details.get('apiKeyRequired', False)}")
                
                # Check method responses
                responses = method_details.get('methodResponses', {})
                print(f"    Responses: {list(responses.keys())}")
                
                for status_code in responses:
                    response_params = responses[status_code].get('responseParameters', {})
                    cors_headers = [k for k in response_params.keys() if 'Access-Control' in k]
                    if cors_headers:
                        print(f"      {status_code}: CORS headers present")
                    else:
                        print(f"      {status_code}: No CORS headers")
                
            except Exception as e:
                print(f"    Error getting method {method}: {e}")
        
        return resource
        
    except Exception as e:
        print(f"❌ Failed to get resource details: {e}")
        return None

def get_parent_resource_path(api_id, resource_id):
    """Get the full path of a resource by traversing parents"""
    
    client = boto3.client('apigateway', region_name='ap-south-1')
    path_parts = []
    
    try:
        current_id = resource_id
        while current_id:
            resource = client.get_resource(restApiId=api_id, resourceId=current_id)
            path_part = resource.get('pathPart')
            if path_part and path_part != '/':
                path_parts.insert(0, path_part)
            current_id = resource.get('parentId')
            
            # Stop at root
            if not current_id or path_part == '/':
                break
        
        return '/' + '/'.join(path_parts) if path_parts else '/'
        
    except Exception as e:
        print(f"Error getting path: {e}")
        return "unknown"

def main():
    """Debug the latest endpoint"""
    
    api_id = "vtqjfznspc"
    latest_resource_id = "7v02j2"
    
    print("🔍 Debugging /latest endpoint CORS issue")
    print("=" * 50)
    
    # Get resource details
    resource = get_resource_details(api_id, latest_resource_id)
    
    if resource:
        # Get full path
        full_path = get_parent_resource_path(api_id, latest_resource_id)
        print(f"\n📍 Full path: {full_path}")
        
        # Check parent resource
        parent_id = resource.get('parentId')
        if parent_id:
            print(f"\n🔍 Parent resource ({parent_id}):")
            get_resource_details(api_id, parent_id)
    
    # Let's also check what happens when we make a direct OPTIONS request
    print(f"\n🧪 Testing direct OPTIONS request...")
    
    import requests
    try:
        response = requests.options(
            f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization,Content-Type'
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print("Headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        if response.text:
            print(f"Body: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()