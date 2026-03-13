#!/usr/bin/env python3
"""
Check the actual alerts endpoint structure
"""

import boto3
import json

def check_alerts_endpoint():
    client = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    try:
        resources = client.get_resources(restApiId=api_id)
        
        print("=== API Structure Analysis ===")
        alerts_resources = []
        api_resources = []
        
        for resource in resources['items']:
            path = resource['path']
            resource_id = resource['id']
            methods = list(resource.get('resourceMethods', {}).keys())
            
            if 'alert' in path.lower():
                alerts_resources.append((path, resource_id, methods))
                print(f"🚨 ALERTS: {path} (ID: {resource_id}) Methods: {methods}")
            
            if path.startswith('/api'):
                api_resources.append((path, resource_id, methods))
        
        print(f"\n=== Found {len(alerts_resources)} alerts-related resources ===")
        for path, resource_id, methods in alerts_resources:
            print(f"  {path} → {methods}")
            
            # Check if OPTIONS method exists
            if 'OPTIONS' not in methods:
                print(f"    ❌ Missing OPTIONS method (CORS issue)")
            else:
                print(f"    ✅ OPTIONS method exists")
        
        print(f"\n=== API Resources Summary ===")
        for path, resource_id, methods in api_resources[:10]:  # Show first 10
            print(f"  {path} → {methods}")
        
        # Check the specific endpoint your frontend is calling
        target_endpoint = "/api/alerts"
        found_target = False
        
        for path, resource_id, methods in api_resources:
            if path == target_endpoint:
                found_target = True
                print(f"\n🎯 Target endpoint {target_endpoint} found!")
                print(f"   Resource ID: {resource_id}")
                print(f"   Methods: {methods}")
                
                if 'OPTIONS' not in methods:
                    print("   ❌ CORS Issue: Missing OPTIONS method")
                    return resource_id, False
                else:
                    print("   ✅ OPTIONS method exists")
                    return resource_id, True
        
        if not found_target:
            print(f"\n❌ Target endpoint {target_endpoint} NOT FOUND")
            print("Available alerts endpoints:")
            for path, resource_id, methods in alerts_resources:
                print(f"  - {path}")
            return None, False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, False

if __name__ == "__main__":
    resource_id, has_options = check_alerts_endpoint()
    if resource_id and not has_options:
        print(f"\n🔧 Need to add OPTIONS method to resource {resource_id}")
    elif resource_id and has_options:
        print(f"\n✅ CORS should be working - check other issues")
    else:
        print(f"\n❌ Need to create the /api/alerts endpoint first")