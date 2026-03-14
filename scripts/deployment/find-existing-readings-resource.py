#!/usr/bin/env python3
"""
Find and use the existing readings resource structure.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    print("🔍 Finding existing readings resources...")
    
    try:
        # Get all resources with more details
        resources = apigateway.get_resources(restApiId=api_id)
        
        print("📋 All resources with parent info:")
        resource_map = {}
        parent_map = {}
        
        for resource in resources['items']:
            resource_id = resource['id']
            path = resource.get('path', '')
            parent_id = resource.get('parentId')
            path_part = resource.get('pathPart', '')
            
            resource_map[resource_id] = resource
            if parent_id:
                parent_map[resource_id] = parent_id
            
            print(f"   {path} (ID: {resource_id}, Parent: {parent_id}, Part: {path_part})")
        
        # Find /api/v1 resource
        api_v1_resource = None
        for resource in resources['items']:
            if resource.get('path') == '/api/v1':
                api_v1_resource = resource
                break
        
        if not api_v1_resource:
            print("❌ /api/v1 not found")
            return
        
        print(f"\n✅ Found /api/v1: {api_v1_resource['id']}")
        
        # Find children of /api/v1
        v1_children = []
        for resource in resources['items']:
            if resource.get('parentId') == api_v1_resource['id']:
                v1_children.append(resource)
                print(f"   Child: {resource.get('pathPart')} -> {resource.get('path')}")
        
        # Look for readings resource
        readings_resource = None
        for child in v1_children:
            if child.get('pathPart') == 'readings':
                readings_resource = child
                break
        
        if readings_resource:
            print(f"\n✅ Found readings resource: {readings_resource['id']}")
            
            # Find children of readings
            readings_children = []
            for resource in resources['items']:
                if resource.get('parentId') == readings_resource['id']:
                    readings_children.append(resource)
                    print(f"   Readings child: {resource.get('pathPart')} -> {resource.get('path')}")
            
            # Look for {deviceId} resource
            device_resource = None
            for child in readings_children:
                if '{deviceId}' in child.get('pathPart', ''):
                    device_resource = child
                    break
            
            if device_resource:
                print(f"\n✅ Found device resource: {device_resource['id']}")
                
                # Find children of device
                device_children = []
                for resource in resources['items']:
                    if resource.get('parentId') == device_resource['id']:
                        device_children.append(resource)
                        print(f"   Device child: {resource.get('pathPart')} -> {resource.get('path')}")
                
                # Look for latest resource
                latest_resource = None
                for child in device_children:
                    if child.get('pathPart') == 'latest':
                        latest_resource = child
                        break
                
                if latest_resource:
                    print(f"\n✅ Found latest resource: {latest_resource['id']}")
                    print(f"   Full path: {latest_resource.get('path')}")
                    
                    # Check methods
                    methods = latest_resource.get('resourceMethods', {})
                    print(f"   Methods: {list(methods.keys())}")
                    
                    if 'GET' in methods:
                        print("   ✅ GET method exists")
                        
                        # Check the method details
                        method = apigateway.get_method(
                            restApiId=api_id,
                            resourceId=latest_resource['id'],
                            httpMethod='GET'
                        )
                        
                        print(f"   Authorization: {method.get('authorizationType')}")
                        print(f"   Authorizer ID: {method.get('authorizerId')}")
                        
                        # Check integration
                        try:
                            integration = apigateway.get_integration(
                                restApiId=api_id,
                                resourceId=latest_resource['id'],
                                httpMethod='GET'
                            )
                            print(f"   Integration type: {integration.get('type')}")
                            print(f"   Integration URI: {integration.get('uri')}")
                        except ClientError as e:
                            print(f"   ❌ No integration: {e}")
                    else:
                        print("   ❌ GET method missing")
                else:
                    print("\n❌ Latest resource not found")
            else:
                print("\n❌ Device resource not found")
        else:
            print("\n❌ Readings resource not found under /api/v1")
            
            # Maybe it's somewhere else?
            print("\n🔍 Searching for 'readings' anywhere...")
            for resource in resources['items']:
                path_part = resource.get('pathPart', '')
                path = resource.get('path', '')
                if 'readings' in path_part.lower() or 'readings' in path.lower():
                    print(f"   Found: {path} (Part: {path_part}, ID: {resource['id']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()