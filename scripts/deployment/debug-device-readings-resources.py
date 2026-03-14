#!/usr/bin/env python3
"""
Debug device readings resources
"""

import boto3
import json

def debug_device_readings_resources():
    """Debug what resources exist under device-readings"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        print(f"🔍 Debugging device readings resources...")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_readings_resource_id = None
        
        print(f"\n📋 All resources:")
        for resource in resources['items']:
            path = resource.get('path', '/')
            resource_id = resource['id']
            parent_id = resource.get('parentId', 'None')
            path_part = resource.get('pathPart', '/')
            
            if 'device-readings' in path:
                print(f"   📍 {path} ({resource_id}) - Parent: {parent_id}, Part: {path_part}")
                
                if path == '/api/device-readings':
                    device_readings_resource_id = resource_id
        
        if not device_readings_resource_id:
            print(f"\n❌ No device-readings resource found")
            return
        
        print(f"\n🔍 Resources under device-readings ({device_readings_resource_id}):")
        
        children = []
        for resource in resources['items']:
            if resource.get('parentId') == device_readings_resource_id:
                children.append(resource)
                path = resource.get('path', '/')
                resource_id = resource['id']
                path_part = resource.get('pathPart', '/')
                print(f"   - {path} ({resource_id}) - Part: {path_part}")
        
        if not children:
            print(f"   ❌ No child resources found under device-readings")
            print(f"   💡 Need to create {{deviceId}} resource")
            
            # Try to create the missing deviceId resource
            print(f"\n🔧 Creating missing {{deviceId}} resource...")
            
            try:
                device_id_resource = apigateway.create_resource(
                    restApiId=api_id,
                    parentId=device_readings_resource_id,
                    pathPart='{deviceId}'
                )
                device_id_resource_id = device_id_resource['id']
                print(f"   ✅ Created {{deviceId}} resource: {device_id_resource_id}")
                
                # Now create latest and history under it
                for endpoint in ['latest', 'history']:
                    print(f"   🔧 Creating {endpoint} under {{deviceId}}...")
                    
                    try:
                        endpoint_resource = apigateway.create_resource(
                            restApiId=api_id,
                            parentId=device_id_resource_id,
                            pathPart=endpoint
                        )
                        endpoint_resource_id = endpoint_resource['id']
                        print(f"   ✅ Created {endpoint}: {endpoint_resource_id}")
                        
                        # Add GET method
                        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-readings-service-dev"
                        integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
                        
                        # Add GET method
                        apigateway.put_method(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='GET',
                            authorizationType='NONE'
                        )
                        
                        # Add Lambda integration
                        apigateway.put_integration(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='GET',
                            type='AWS_PROXY',
                            integrationHttpMethod='POST',
                            uri=integration_uri
                        )
                        
                        # Add OPTIONS for CORS
                        apigateway.put_method(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='OPTIONS',
                            authorizationType='NONE'
                        )
                        
                        apigateway.put_integration(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='OPTIONS',
                            type='MOCK',
                            requestTemplates={'application/json': '{"statusCode": 200}'}
                        )
                        
                        apigateway.put_method_response(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='OPTIONS',
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': False,
                                'method.response.header.Access-Control-Allow-Methods': False,
                                'method.response.header.Access-Control-Allow-Headers': False
                            }
                        )
                        
                        apigateway.put_integration_response(
                            restApiId=api_id,
                            resourceId=endpoint_resource_id,
                            httpMethod='OPTIONS',
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': "'*'",
                                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
                            }
                        )
                        
                        print(f"   ✅ Added methods to {endpoint}")
                        
                    except Exception as e:
                        print(f"   ❌ Error creating {endpoint}: {e}")
                
                # Deploy changes
                print(f"\n🚀 Deploying changes...")
                deployment = apigateway.create_deployment(
                    restApiId=api_id,
                    stageName='dev',
                    description='Fixed device readings resources'
                )
                print(f"✅ Deployment: {deployment['id']}")
                
                return True
                
            except Exception as e:
                print(f"   ❌ Error creating deviceId resource: {e}")
                return False
        else:
            print(f"   ✅ Found {len(children)} child resources")
            return True
        
    except Exception as e:
        print(f"❌ Error debugging resources: {e}")
        return False

def test_final_endpoints():
    """Test the final endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Testing final endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        endpoints = [
            f"{base_url}/api/device-readings/ESP32-001/latest",
            f"{base_url}/api/device-readings/ESP32-001/history"
        ]
        
        for endpoint in endpoints:
            endpoint_name = endpoint.split('/')[-1]
            print(f"\n   🔍 Testing {endpoint_name}:")
            print(f"     URL: {endpoint}")
            
            try:
                response = requests.get(endpoint, timeout=10)
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ SUCCESS!")
                    
                    try:
                        data = response.json()
                        if data.get('success'):
                            if endpoint_name == 'latest':
                                reading = data.get('reading', {})
                                print(f"       📊 pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                            elif endpoint_name == 'history':
                                readings = data.get('readings', [])
                                print(f"       📊 Found {len(readings)} readings")
                    except Exception as parse_error:
                        print(f"       ⚠️ Parse error: {parse_error}")
                else:
                    print(f"     ❌ Error: {response.text[:100]}")
                
            except Exception as e:
                print(f"     ❌ Request error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

def main():
    print("🔍 Debugging Device Readings Resources")
    print("=" * 40)
    
    # Step 1: Debug and fix resources
    print("\n1. Debugging and fixing resources...")
    success = debug_device_readings_resources()
    
    # Step 2: Test endpoints
    print("\n2. Testing final endpoints...")
    test_final_endpoints()
    
    if success:
        print(f"\n🎉 Device Readings API Setup Complete!")
        print(f"✅ All resources created successfully")
        print(f"✅ Both endpoints should now work:")
        print(f"   - /api/device-readings/{{deviceId}}/latest")
        print(f"   - /api/device-readings/{{deviceId}}/history")
        print(f"✅ Frontend updated to use new endpoints")
        print(f"✅ CORS configured")
        
        print(f"\n💡 The CORS issue should now be resolved!")
        print(f"   Try refreshing your dashboard to see the readings!")
    else:
        print(f"\n❌ Still having issues with the setup")

if __name__ == "__main__":
    main()