#!/usr/bin/env python3
"""
Check what the existing /api/device-readings endpoint does.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    api_id = 'vtqjfznspc'
    
    print("🔍 Checking /api/device-readings endpoint...")
    
    try:
        # Get the device-readings resource
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_readings_resource = None
        for resource in resources['items']:
            if resource.get('path') == '/api/device-readings':
                device_readings_resource = resource
                break
        
        if not device_readings_resource:
            print("❌ /api/device-readings not found")
            return
        
        resource_id = device_readings_resource['id']
        print(f"✅ Found /api/device-readings: {resource_id}")
        
        # Check methods
        methods = device_readings_resource.get('resourceMethods', {})
        print(f"Methods: {list(methods.keys())}")
        
        for method in methods:
            print(f"\n📋 Checking {method} method...")
            
            try:
                method_details = apigateway.get_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method
                )
                
                print(f"   Authorization: {method_details.get('authorizationType', 'None')}")
                if method_details.get('authorizerId'):
                    print(f"   Authorizer ID: {method_details['authorizerId']}")
                
                # Check integration
                try:
                    integration = apigateway.get_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method
                    )
                    
                    print(f"   Integration type: {integration.get('type')}")
                    if integration.get('uri'):
                        print(f"   Integration URI: {integration['uri']}")
                    
                    # If it's a Lambda integration, show the function name
                    if 'lambda' in integration.get('uri', ''):
                        uri_parts = integration['uri'].split('/')
                        if len(uri_parts) > 6:
                            function_name = uri_parts[6].split(':')[0]
                            print(f"   Lambda function: {function_name}")
                
                except ClientError as e:
                    print(f"   ❌ No integration: {e}")
                    
            except ClientError as e:
                print(f"   ❌ Error getting method: {e}")
        
        # Now let's create the proper /api/v1/readings structure
        print(f"\n🔧 Creating proper /api/v1/readings structure...")
        
        # Find /api/v1 resource
        api_v1_resource = None
        for resource in resources['items']:
            if resource.get('path') == '/api/v1':
                api_v1_resource = resource
                break
        
        if not api_v1_resource:
            print("❌ /api/v1 not found")
            return
        
        print(f"✅ Found /api/v1: {api_v1_resource['id']}")
        
        # Create /api/v1/readings
        try:
            readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=api_v1_resource['id'],
                pathPart='readings'
            )
            print(f"✅ Created /api/v1/readings: {readings_resource['id']}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing readings resource under /api/v1
                for resource in resources['items']:
                    if (resource.get('parentId') == api_v1_resource['id'] and 
                        resource.get('pathPart') == 'readings'):
                        readings_resource = resource
                        print(f"✅ Found existing /api/v1/readings: {readings_resource['id']}")
                        break
                else:
                    print(f"❌ Conflict but can't find existing resource: {e}")
                    return
            else:
                print(f"❌ Error creating readings resource: {e}")
                return
        
        # Create /api/v1/readings/{deviceId}
        try:
            device_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=readings_resource['id'],
                pathPart='{deviceId}'
            )
            print(f"✅ Created /api/v1/readings/{{deviceId}}: {device_resource['id']}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing device resource
                for resource in resources['items']:
                    if (resource.get('parentId') == readings_resource['id'] and 
                        '{deviceId}' in resource.get('pathPart', '')):
                        device_resource = resource
                        print(f"✅ Found existing device resource: {device_resource['id']}")
                        break
                else:
                    print(f"❌ Conflict but can't find existing device resource: {e}")
                    return
            else:
                print(f"❌ Error creating device resource: {e}")
                return
        
        # Create /api/v1/readings/{deviceId}/latest
        try:
            latest_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_resource['id'],
                pathPart='latest'
            )
            print(f"✅ Created /api/v1/readings/{{deviceId}}/latest: {latest_resource['id']}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing latest resource
                for resource in resources['items']:
                    if (resource.get('parentId') == device_resource['id'] and 
                        resource.get('pathPart') == 'latest'):
                        latest_resource = resource
                        print(f"✅ Found existing latest resource: {latest_resource['id']}")
                        break
                else:
                    print(f"❌ Conflict but can't find existing latest resource: {e}")
                    return
            else:
                print(f"❌ Error creating latest resource: {e}")
                return
        
        print(f"\n✅ Resource structure created!")
        print(f"   Path: /api/v1/readings/{{deviceId}}/latest")
        print(f"   Resource ID: {latest_resource['id']}")
        
        # Now we need to add methods and integration - but let's first check if they exist
        print(f"\n🔧 Setting up methods and integration...")
        
        # The rest will be handled by the next script
        print(f"✅ Ready for method and integration setup")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()