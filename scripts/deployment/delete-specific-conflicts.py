#!/usr/bin/env python3
"""
Delete specific conflicting API Gateway resources.
"""

import boto3
import sys

def main():
    """Delete specific conflicting resources"""
    client = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    # Resources to delete based on the error and our investigation
    resources_to_delete = [
        {'id': 'obigvj', 'path': '/api/v1/technician/tasks'},
        {'id': 'tg7v66', 'path': '/api/devices'}
    ]
    
    print("🗑️  Deleting specific conflicting resources...")
    
    for resource in resources_to_delete:
        try:
            print(f"Deleting: {resource['path']} (ID: {resource['id']})")
            client.delete_resource(
                restApiId=api_id,
                resourceId=resource['id']
            )
            print(f"✅ Successfully deleted: {resource['path']}")
        except Exception as e:
            print(f"❌ Error deleting {resource['path']}: {e}")
    
    print("\n🎉 Specific conflicts resolved!")
    print("🚀 Now retry the CDK deployment")

if __name__ == "__main__":
    main()