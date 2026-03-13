#!/usr/bin/env python3
"""
Fix API Gateway resource conflicts by removing duplicate resources.

This script identifies and removes conflicting API Gateway resources that are
preventing the CloudFormation deployment from succeeding.
"""

import boto3
import json
import sys
from typing import List, Dict, Any

def get_api_gateway_client():
    """Get API Gateway client"""
    return boto3.client('apigateway', region_name='ap-south-1')

def get_rest_api_id(api_name: str) -> str:
    """Get REST API ID by name"""
    client = get_api_gateway_client()
    
    try:
        response = client.get_rest_apis()
        for api in response['items']:
            if api['name'] == api_name:
                return api['id']
        
        print(f"❌ API Gateway '{api_name}' not found")
        return None
    except Exception as e:
        print(f"❌ Error getting REST API: {e}")
        return None

def get_api_resources(api_id: str) -> List[Dict[str, Any]]:
    """Get all resources for an API"""
    client = get_api_gateway_client()
    
    try:
        response = client.get_resources(restApiId=api_id)
        return response['items']
    except Exception as e:
        print(f"❌ Error getting API resources: {e}")
        return []

def find_conflicting_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find resources that are causing conflicts"""
    conflicting_resources = []
    
    # Resources that are causing conflicts based on the error messages
    conflict_paths = [
        '/api/v1/readings/{deviceId}/latest',
        '/api/v1/technician/tasks', 
        '/api/devices'
    ]
    
    for resource in resources:
        resource_path = resource.get('path', '')
        if resource_path in conflict_paths:
            conflicting_resources.append(resource)
            print(f"🔍 Found conflicting resource: {resource_path} (ID: {resource['id']})")
    
    return conflicting_resources

def delete_resource(api_id: str, resource_id: str, resource_path: str) -> bool:
    """Delete a specific API Gateway resource"""
    client = get_api_gateway_client()
    
    try:
        print(f"🗑️  Deleting resource: {resource_path} (ID: {resource_id})")
        client.delete_resource(
            restApiId=api_id,
            resourceId=resource_id
        )
        print(f"✅ Successfully deleted resource: {resource_path}")
        return True
    except Exception as e:
        print(f"❌ Error deleting resource {resource_path}: {e}")
        return False

def main():
    """Main function to fix API Gateway conflicts"""
    print("🔧 AquaChain API Gateway Conflict Resolver")
    print("=" * 50)
    
    # Configuration
    api_name = "aquachain-api-rest-dev"
    
    # Get API ID
    print(f"📡 Looking for API Gateway: {api_name}")
    api_id = get_rest_api_id(api_name)
    if not api_id:
        sys.exit(1)
    
    print(f"✅ Found API Gateway: {api_name} (ID: {api_id})")
    
    # Get all resources
    print("📋 Fetching API Gateway resources...")
    resources = get_api_resources(api_id)
    if not resources:
        print("❌ No resources found or error occurred")
        sys.exit(1)
    
    print(f"✅ Found {len(resources)} resources")
    
    # Find conflicting resources
    print("🔍 Identifying conflicting resources...")
    conflicting_resources = find_conflicting_resources(resources)
    
    if not conflicting_resources:
        print("✅ No conflicting resources found!")
        return
    
    print(f"⚠️  Found {len(conflicting_resources)} conflicting resources")
    
    # Confirm deletion
    print("\n🚨 WARNING: This will delete the following API Gateway resources:")
    for resource in conflicting_resources:
        print(f"   - {resource['path']} (ID: {resource['id']})")
    
    print("\n⚠️  These resources will be recreated by the CDK deployment.")
    print("⚠️  Any manual configurations on these resources will be lost.")
    
    confirm = input("\n❓ Do you want to proceed? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled by user")
        return
    
    # Delete conflicting resources
    print("\n🗑️  Deleting conflicting resources...")
    success_count = 0
    
    # Sort by path length (descending) to delete child resources first
    conflicting_resources.sort(key=lambda x: len(x['path']), reverse=True)
    
    for resource in conflicting_resources:
        if delete_resource(api_id, resource['id'], resource['path']):
            success_count += 1
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successfully deleted: {success_count}")
    print(f"   ❌ Failed to delete: {len(conflicting_resources) - success_count}")
    
    if success_count == len(conflicting_resources):
        print("\n🎉 All conflicting resources have been removed!")
        print("🚀 You can now retry the CDK deployment:")
        print("   cd infrastructure/cdk")
        print("   cdk deploy AquaChain-API-dev")
    else:
        print("\n⚠️  Some resources could not be deleted. Check the errors above.")
        print("💡 You may need to delete them manually in the AWS Console.")

if __name__ == "__main__":
    main()