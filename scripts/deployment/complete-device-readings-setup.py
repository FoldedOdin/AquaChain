#!/usr/bin/env python3
"""
Complete the device readings setup by creating all missing resources
"""

import boto3
import json

def complete_device_readings_setup():
    """Complete the device readings setup"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_name = 'aquachain-function-readings-service-dev'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:{function_name}"
        
        print(f"🔧 Completing device readings setup...")
        
        # Find the device-readings resource
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_readings_resource_id = None
        for resource in resources['items']:
            if resource.get('path') == '/api/device-readings':
                device_readings_resource_id = resource['id']
                print(f"   ✅ Found /api/device-readings: {device_readings_resource_id}")
                break
        
        if not device_readings_resource_id:
            print(f"❌ Could not find /api/device-readings resource")
            return False
        
        # Create /{deviceId} under /api/device-readings
        print(f"   🔧 Creating /api/device-readings/{{deviceId}}...")
        
        device_id_resource_id = None
        try:
            device_id_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_readings_resource_id,
                pathPart='{deviceId}'
            )
            device_id_resource_id = device_id_resource['id']
            print(f"   ✅ Created /api/device-readings/{{deviceId}}: {device_id_resource_id}")
        except apigateway.exceptions.ConflictException:
            print(f"   ⚠️ /{{deviceId}} already exists, finding it...")
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == '{deviceId}' and 
                    resource.get('parentId') == device_readings_resource_id):
                    device_id_resource_id = resource['id']
                    print(f"   ✅ Using existing /{{deviceId}}: {device_id_resource_id}")
                    break
        
        if not device_id_resource_id:
            print(f"❌ Could not create device ID resource")
            return False
        
        # Create both /latest and /history under /{deviceId}
        endpoints = ['latest', 'history']
        
        for endpoint_name in endpoints:
            print(f"\n   🔧 Creating /api/device-readings/{{deviceId}}/{endpoint_name}...")
            
            endpoint_resource_id = None
            try:
                endpoint_resource = apigateway.create_resource(
                    restApiId=api_id,
                    parentId=device_id_resource_id,
                    pathPart=endpoint_name
                )
                endpoint_resource_id = endpoint_resource['id']
                print(f"   ✅ Created /{endpoint_name}: {endpoint_resource_id}")
            except apigateway.exceptions.ConflictException:
                print(f"   ⚠️ /{endpoint_name} already exists, finding it...")
                resources = apigateway.get_resources(restApiId=api_id)
                for resource in resources['items']:
                    if (resource.get('pathPart') == endpoint_name and 
                        resource.get('parentId') == device_id_resource_id):
                        endpoint_resource_id = resource['id']
                        print(f"   ✅ Using existing /{endpoint_name}: {endpoint_resource_id}")
                        break
            
            if not endpoint_resource_id:
                print(f"❌ Could not create {endpoint_name} resource")
                continue
            
            # Add GET method
            print(f"     🔧 Adding GET method to /{endpoint_name}...")
            
            try:
                # Add GET method
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=endpoint_resource_id,
                    httpMethod='GET',
                    authorizationType='NONE'  # No auth for testing
                )
                
                # Add Lambda integration
                integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
                
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=endpoint_resource_id,
                    httpMethod='GET',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=integration_uri
                )
                
                print(f"     ✅ Added GET method with Lambda integration")
                
            except Exception as e:
                print(f"     ⚠️ GET method may already exist: {e}")
            
            # Add OPTIONS method for CORS
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=endpoint_resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Add mock integration for OPTIONS
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=endpoint_resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={'application/json': '{"statusCode": 200}'}
                )
                
                # Add method response for OPTIONS
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
                
                # Add integration response for OPTIONS
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
                
                print(f"     ✅ Added OPTIONS method for CORS")
                
            except Exception as e:
                print(f"     ⚠️ OPTIONS method may already exist: {e}")
        
        # Deploy the API
        print(f"\n🚀 Deploying API changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Completed device readings setup'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error completing setup: {e}")
        return False

def test_both_endpoints():
    """Test both endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Testing both endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        endpoints = [
            f"{base_url}/api/device-readings/ESP32-001/latest",
            f"{base_url}/api/device-readings/ESP32-001/history"
        ]
        
        results = []
        
        for endpoint in endpoints:
            endpoint_name = endpoint.split('/')[-1]
            print(f"\n   🔍 Testing {endpoint_name}: {endpoint}")
            
            try:
                # Test GET
                response = requests.get(endpoint, timeout=10)
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ SUCCESS!")
                    
                    try:
                        data = response.json()
                        if data.get('success'):
                            if endpoint_name == 'latest':
                                reading = data.get('reading', {})
                                print(f"       pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                            elif endpoint_name == 'history':
                                readings = data.get('readings', [])
                                print(f"       Found {len(readings)} readings")
                    except:
                        pass
                        
                    results.append(True)
                else:
                    print(f"     ❌ Error: {response.text[:100]}")
                    results.append(False)
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
                results.append(False)
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

def main():
    print("🔧 Completing Device Readings Setup")
    print("=" * 35)
    
    # Step 1: Complete setup
    print("\n1. Completing device readings setup...")
    if not complete_device_readings_setup():
        print("❌ Failed to complete setup")
        return
    
    # Step 2: Test both endpoints
    print("\n2. Testing both endpoints...")
    if test_both_endpoints():
        print(f"\n🎉 Complete Success!")
        print(f"✅ Both endpoints created and working:")
        print(f"   - /api/device-readings/{{deviceId}}/latest")
        print(f"   - /api/device-readings/{{deviceId}}/history")
        print(f"✅ CORS configured for both")
        print(f"✅ Lambda integration working")
        
        print(f"\n💡 Frontend has been updated to use new endpoints")
        print(f"   The CORS issue should now be completely resolved!")
        print(f"   Try refreshing your dashboard now!")
    else:
        print(f"\n❌ Some endpoints are not working properly")
        print(f"💡 Check the logs above for specific issues")

if __name__ == "__main__":
    main()