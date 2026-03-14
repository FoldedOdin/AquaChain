#!/usr/bin/env python3
"""
List all API Gateway resources to understand the structure
"""

import boto3
import json

def list_api_gateway_resources():
    """List all resources in the API Gateway"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        print(f"🔍 Listing all resources in API Gateway: {api_id}")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"\n📋 Found {len(resources['items'])} resources:")
        
        # Group resources by path for better understanding
        resource_tree = {}
        
        for resource in resources['items']:
            resource_id = resource['id']
            path = resource.get('path', '/')
            path_part = resource.get('pathPart', '/')
            parent_id = resource.get('parentId', 'None')
            methods = list(resource.get('resourceMethods', {}).keys())
            
            print(f"\n   📁 {path}")
            print(f"      ID: {resource_id}")
            print(f"      Path Part: {path_part}")
            print(f"      Parent ID: {parent_id}")
            print(f"      Methods: {methods}")
            
            # Store for tree building
            resource_tree[resource_id] = {
                'path': path,
                'pathPart': path_part,
                'parentId': parent_id,
                'methods': methods,
                'children': []
            }
        
        # Find root and /api resources
        root_resource = None
        api_resource = None
        
        for resource_id, resource_data in resource_tree.items():
            if resource_data['path'] == '/':
                root_resource = resource_id
                print(f"\n✅ Found root resource: {resource_id}")
            elif resource_data['path'] == '/api':
                api_resource = resource_id
                print(f"✅ Found /api resource: {resource_id}")
        
        if not api_resource:
            print(f"\n❌ No /api resource found!")
            print(f"💡 Available top-level paths:")
            for resource_id, resource_data in resource_tree.items():
                if resource_data['parentId'] == root_resource:
                    print(f"   - {resource_data['path']} ({resource_id})")
        
        return api_resource
        
    except Exception as e:
        print(f"❌ Error listing resources: {e}")
        return None

def find_suitable_parent():
    """Find a suitable parent resource to create readings under"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"\n🔍 Looking for suitable parent resources...")
        
        candidates = []
        
        for resource in resources['items']:
            path = resource.get('path', '/')
            resource_id = resource['id']
            
            # Look for paths that could be good parents
            if (path in ['/', '/api'] or 
                'api' in path.lower() or 
                path.count('/') <= 2):  # Not too deep
                
                candidates.append({
                    'path': path,
                    'id': resource_id
                })
        
        print(f"   📋 Suitable parent candidates:")
        for candidate in candidates:
            print(f"     - {candidate['path']} ({candidate['id']})")
        
        return candidates
        
    except Exception as e:
        print(f"❌ Error finding parents: {e}")
        return []

def main():
    print("🔍 API Gateway Resource Analysis")
    print("=" * 35)
    
    # Step 1: List all resources
    print("\n1. Listing all resources...")
    api_resource = list_api_gateway_resources()
    
    # Step 2: Find suitable parents if /api doesn't exist
    if not api_resource:
        print("\n2. Finding alternative parent resources...")
        candidates = find_suitable_parent()
        
        if candidates:
            print(f"\n💡 Recommendations:")
            print(f"   1. Create readings endpoint under root: /device-readings")
            print(f"   2. Or create /api first, then /api/device-readings")
            print(f"   3. Use existing path if suitable")
        else:
            print(f"\n❌ No suitable parent resources found")
    else:
        print(f"\n✅ Can create readings endpoint under /api")

if __name__ == "__main__":
    main()