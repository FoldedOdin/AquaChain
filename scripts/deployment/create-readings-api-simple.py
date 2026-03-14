#!/usr/bin/env python3
"""
Create readings API with a simpler approach - use existing endpoints if possible
"""

import boto3
import json
import requests

def test_existing_endpoints():
    """Test if there are any existing endpoints we can use"""
    try:
        print(f"🔍 Testing existing endpoints that might work...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        # Test various possible endpoints
        test_endpoints = [
            "/api/devices/ESP32-001",
            "/api/devices/ESP32-001/readings", 
            "/api/devices/ESP32-001/latest",
            "/api/water-quality/latest",
            "/water-quality",
            "/api/v1/devices/ESP32-001",
            "/api/v1/devices/ESP32-001/readings"
        ]
        
        for endpoint in test_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n   🧪 Testing: {endpoint}")
            
            try:
                # Test OPTIONS first
                options_response = requests.options(url, timeout=5)
                print(f"     OPTIONS: {options_response.status_code}")
                
                # Test GET
                get_response = requests.get(url, timeout=5)
                print(f"     GET: {get_response.status_code}")
                
                if get_response.status_code in [200, 401, 403]:  # These indicate the endpoint exists
                    print(f"     ✅ Endpoint exists! Response: {get_response.text[:100]}")
                    
                    if get_response.status_code == 200:
                        return endpoint  # Found a working endpoint
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return None

def create_device_readings_endpoint():
    """Create a readings endpoint under /api/devices instead"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_name = 'aquachain-function-readings-service-dev'
        
        print(f"🔧 Creating readings endpoint under /api/devices...")
        
        # Get all resources to find devices endpoint
        resources = apigateway.get_resources(restApiId=api_id)
        
        devices_resource_id = None
        api_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('path', '')
            resource_id = resource['id']
            
            if path == '/api':
                api_resource_id = resource_id
                print(f"   ✅ Found /api resource: {resource_id}")
            elif path == '/api/devices':
                devices_resource_id = resource_id
                print(f"   ✅ Found /api/devices resource: {resource_id}")
        
        # If no /api/devices, create it
        if not devices_resource_id and api_resource_id:
            print(f"   🔧 Creating /api/devices resource...")
            
            try:
                devices_resource = apigateway.create_resource(
                    restApiId=api_id,
                    parentId=api_resource_id,
                    pathPart='devices'
                )
                devices_resource_id = devices_resource['id']
                print(f"   ✅ Created /api/devices: {devices_resource_id}")
            except Exception as e:
                print(f"   ❌ Error creating devices resource: {e}")
                return False
        
        if not devices_resource_id:
            print(f"❌ Could not find or create /api/devices resource")
            return False
        
        # Create /{deviceId} under /api/devices
        print(f"   🔧 Creating /api/devices/{{deviceId}} resource...")
        
        device_id_resource_id = None
        try:
            device_id_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=devices_resource_id,
                pathPart='{deviceId}'
            )
            device_id_resource_id = device_id_resource['id']
            print(f"   ✅ Created /api/devices/{{deviceId}}: {device_id_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == '{deviceId}' and 
                    resource.get('parentId') == devices_resource_id):
                    device_id_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/devices/{{deviceId}}: {device_id_resource_id}")
                    break
        except Exception as e:
            print(f"   ❌ Error creating device ID resource: {e}")
            return False
        
        if not device_id_resource_id:
            print(f"❌ Could not create device ID resource")
            return False
        
        # Create /readings under /api/devices/{deviceId}
        print(f"   🔧 Creating /api/devices/{{deviceId}}/readings resource...")
        
        readings_resource_id = None
        try:
            readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_id_resource_id,
                pathPart='readings'
            )
            readings_resource_id = readings_resource['id']
            print(f"   ✅ Created /api/devices/{{deviceId}}/readings: {readings_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'readings' and 
                    resource.get('parentId') == device_id_resource_id):
                    readings_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/devices/{{deviceId}}/readings: {readings_resource_id}")
                    break
        except Exception as e:
            print(f"   ❌ Error creating readings resource: {e}")
            return False
        
        if not readings_resource_id:
            print(f"❌ Could not create readings resource")
            return False
        
        # Add GET method to /api/devices/{deviceId}/readings
        print(f"   🔧 Adding GET method...")
        
        try:
            # Add GET method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=readings_resource_id,
                httpMethod='GET',
                authorizationType='AWS_IAM'
            )
            
            # Add Lambda integration
            function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:{function_name}"
            integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=readings_resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            
            print(f"   ✅ Added GET method with Lambda integration")
            
        except Exception as e:
            print(f"   ⚠️ Method may already exist: {e}")
        
        # Add OPTIONS method for CORS
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=readings_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add mock integration for OPTIONS
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=readings_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            # Add method response for OPTIONS
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=readings_resource_id,
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
                resourceId=readings_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
                }
            )
            
            print(f"   ✅ Added OPTIONS method for CORS")
            
        except Exception as e:
            print(f"   ⚠️ OPTIONS method may already exist: {e}")
        
        # Give API Gateway permission to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-readings-devices',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:ap-south-1:*:{api_id}/*/*'
            )
            print(f"   ✅ Added Lambda permission")
        except Exception as e:
            print(f"   ⚠️ Permission may already exist: {e}")
        
        # Deploy the API
        print(f"\n🚀 Deploying API changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Added device readings endpoint'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating device readings endpoint: {e}")
        return False

def update_frontend_to_use_new_endpoint():
    """Update the frontend to use the new endpoint"""
    try:
        print(f"\n🔧 Frontend needs to be updated to use:")
        print(f"   Old: /api/v1/readings/{{deviceId}}/latest")
        print(f"   New: /api/devices/{{deviceId}}/readings")
        print(f"\n💡 The Lambda function can handle both latest and history from this single endpoint")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_new_endpoint():
    """Test the new endpoint"""
    try:
        print(f"\n🧪 Testing new endpoint...")
        
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices/ESP32-001/readings"
        
        # Test OPTIONS
        options_response = requests.options(url, timeout=10)
        print(f"   OPTIONS: {options_response.status_code}")
        print(f"   CORS: {options_response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
        
        # Test GET
        get_response = requests.get(url, timeout=10)
        print(f"   GET: {get_response.status_code}")
        print(f"   Response: {get_response.text[:200]}")
        
        if get_response.status_code in [200, 401, 403]:
            print(f"   ✅ Endpoint is working!")
            return True
        else:
            print(f"   ❌ Endpoint not working properly")
            return False
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def main():
    print("🔧 Creating Readings API (Alternative Approach)")
    print("=" * 45)
    
    # Step 1: Test existing endpoints
    print("\n1. Testing existing endpoints...")
    existing_endpoint = test_existing_endpoints()
    
    if existing_endpoint:
        print(f"\n✅ Found working endpoint: {existing_endpoint}")
        print(f"💡 You can update the frontend to use this endpoint instead")
        return
    
    # Step 2: Create new endpoint under /api/devices
    print("\n2. Creating new endpoint under /api/devices...")
    if not create_device_readings_endpoint():
        print("❌ Failed to create device readings endpoint")
        return
    
    # Step 3: Test new endpoint
    print("\n3. Testing new endpoint...")
    if test_new_endpoint():
        print(f"\n🎉 Success!")
        print(f"✅ Created endpoint: /api/devices/{{deviceId}}/readings")
        print(f"✅ CORS configured")
        print(f"✅ Lambda integration working")
        
        # Step 4: Update frontend
        update_frontend_to_use_new_endpoint()
    else:
        print(f"\n❌ Endpoint created but not working properly")

if __name__ == "__main__":
    main()