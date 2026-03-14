#!/usr/bin/env python3
"""
Debug API structure to find existing readings resources
"""

import boto3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = "vtqjfznspc"
REGION = "ap-south-1"

def debug_api_structure():
    """Debug the complete API structure"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Build parent-child relationships
        children_by_parent = {}
        all_resources = {}
        
        for resource in resources_response['items']:
            resource_id = resource['id']
            parent_id = resource.get('parentId')
            
            all_resources[resource_id] = resource
            
            if parent_id not in children_by_parent:
                children_by_parent[parent_id] = []
            children_by_parent[parent_id].append(resource)
        
        def print_resource_tree(resource_id, indent=0):
            """Print resource tree recursively"""
            if resource_id not in all_resources:
                return
            
            resource = all_resources[resource_id]
            path = resource.get('path', '')
            path_part = resource.get('pathPart', '')
            
            prefix = "  " * indent
            print(f"{prefix}{path} ({path_part}) - {resource_id}")
            
            # Get methods
            try:
                methods_response = client.get_resource(
                    restApiId=API_ID,
                    resourceId=resource_id
                )
                methods = list(methods_response.get('resourceMethods', {}).keys())
                if methods:
                    print(f"{prefix}  Methods: {methods}")
            except Exception as e:
                print(f"{prefix}  Could not get methods: {e}")
            
            # Print children
            if resource_id in children_by_parent:
                for child in children_by_parent[resource_id]:
                    print_resource_tree(child['id'], indent + 1)
        
        # Find root resource
        root_id = None
        for resource in all_resources.values():
            if resource.get('parentId') is None:
                root_id = resource['id']
                break
        
        print("🌳 Complete API Structure:")
        print("=" * 50)
        if root_id:
            print_resource_tree(root_id)
        
        # Specifically look for /api/v1 children
        print("\n🔍 /api/v1 children:")
        print("=" * 30)
        
        api_v1_id = None
        for resource in all_resources.values():
            if resource.get('path') == '/api/v1':
                api_v1_id = resource['id']
                break
        
        if api_v1_id and api_v1_id in children_by_parent:
            for child in children_by_parent[api_v1_id]:
                path_part = child.get('pathPart', '')
                child_id = child['id']
                print(f"  {path_part} - {child_id}")
                
                # Check if this is readings
                if 'reading' in path_part.lower():
                    print(f"    ⭐ FOUND READINGS RESOURCE!")
                    
                    # Check its children
                    if child_id in children_by_parent:
                        for grandchild in children_by_parent[child_id]:
                            gc_path_part = grandchild.get('pathPart', '')
                            gc_id = grandchild['id']
                            print(f"      {gc_path_part} - {gc_id}")
        
        return all_resources
        
    except Exception as e:
        logger.error(f"Error debugging API structure: {e}")
        return {}

def find_readings_endpoint():
    """Find the actual readings endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Look for any resource that could be the readings endpoint
        candidates = []
        
        for resource in resources_response['items']:
            path = resource.get('path', '')
            path_part = resource.get('pathPart', '')
            
            if ('reading' in path.lower() or 
                'reading' in path_part.lower() or
                'device' in path_part.lower()):
                candidates.append(resource)
        
        print("\n🎯 Readings endpoint candidates:")
        print("=" * 40)
        
        for candidate in candidates:
            path = candidate.get('path', '')
            path_part = candidate.get('pathPart', '')
            resource_id = candidate['id']
            parent_id = candidate.get('parentId')
            
            print(f"Path: {path}")
            print(f"PathPart: {path_part}")
            print(f"ID: {resource_id}")
            print(f"Parent: {parent_id}")
            
            # Get methods
            try:
                methods_response = client.get_resource(
                    restApiId=API_ID,
                    resourceId=resource_id
                )
                methods = list(methods_response.get('resourceMethods', {}).keys())
                print(f"Methods: {methods}")
            except Exception as e:
                print(f"Methods: Could not get ({e})")
            
            print("-" * 30)
        
        return candidates
        
    except Exception as e:
        logger.error(f"Error finding readings endpoint: {e}")
        return []

def main():
    """Main function"""
    print("🔍 Debugging API Gateway structure...")
    
    # Debug complete structure
    all_resources = debug_api_structure()
    
    # Find readings candidates
    candidates = find_readings_endpoint()
    
    print(f"\n📊 Summary:")
    print(f"Total resources: {len(all_resources)}")
    print(f"Readings candidates: {len(candidates)}")

if __name__ == "__main__":
    main()