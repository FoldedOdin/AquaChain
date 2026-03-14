#!/usr/bin/env python3
"""
Debug API Gateway resource creation
"""

import boto3
import json

def debug_api_gateway():
    """Debug API Gateway resource creation"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        print(f"🔍 Debugging API Gateway: {api_id}")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"\n📋 Current resources:")
        
        v1_resource_id = None
        readings_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('pathPart', resource.get('path', '/'))
            resource_id = resource['id']
            parent_id = resource.get('parentId', 'None')
            
            print(f"   {path} ({resource_id}) - Parent: {parent_id}")
            
            if path == 'v1':
                v1_resource_id = resource_id
                print(f"     📍 Found v1 resource: {resource_id}")
            
            if path == 'readings':
                readings_resource_id = resource_id
                print(f"     📍 Found readings resource: {resource_id}")
        
        if not v1_resource_id:
            print(f"\n❌ No v1 resource found!")
            return
        
        print(f"\n🔧 Attempting to create readings resource under v1...")
        
        try:
            readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=v1_resource_id,
                pathPart='readings'
            )
            print(f"✅ Created readings resource: {readings_resource['id']}")
            
        except apigateway.exceptions.ConflictException as e:
            print(f"⚠️ Resource already exists: {e}")
            
            # Try to find it again with more detailed search
            print(f"   🔍 Searching for existing readings resource...")
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                path_part = resource.get('pathPart', '')
                parent_id = resource.get('parentId', '')
                resource_id = resource['id']
                
                print(f"     Checking: {path_part} (parent: {parent_id})")
                
                if path_part == 'readings':
                    print(f"   Found readings resource: {resource_id} (parent: {parent_id})")
                    if parent_id == v1_resource_id:
                        print(f"   ✅ This is the correct readings resource under v1")
                        readings_resource_id = resource_id
                    else:
                        print(f"   ⚠️ This readings resource has wrong parent (expected: {v1_resource_id})")
            
            # If still not found, list ALL resources with their full paths
            if not readings_resource_id:
                print(f"\n   🔍 Full resource dump:")
                for resource in resources['items']:
                    print(f"     {resource}")
        
        except Exception as e:
            print(f"❌ Error creating readings resource: {e}")
            print(f"   Error type: {type(e)}")
            print(f"   Error details: {e}")
        
        if readings_resource_id:
            print(f"\n✅ Readings resource available: {readings_resource_id}")
        else:
            print(f"\n❌ Could not create or find readings resource")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api_gateway()