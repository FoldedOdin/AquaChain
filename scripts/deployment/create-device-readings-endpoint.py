#!/usr/bin/env python3
"""
Create device readings endpoint under /api/device-readings
"""

import boto3
import json

def create_device_readings_endpoint():
    """Create device readings endpoint"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_name = 'aquachain-function-readings-service-dev'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:{function_name}"
        
        print(f"🔧 Creating device readings endpoint...")
        
        # Get all resources to find /api
        resources = apigateway.get_resources(restApiId=api_id)
        
        api_resource_id = None
        for resource in resources['items']:
            if resource.get('path') == '/api':
                api_resource_id = resource['id']
                print(f"   ✅ Found /api resource: {api_resource_id}")
                break
        
        if not api_resource_id:
            print(f"❌ Could not find /api resource")
            return False
        
        # Create /device-readings under /api
        print(f"   🔧 Creating /api/device-readings...")
        
        device_readings_resource_id = None
        try:
            device_readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=api_resource_id,
                pathPart='device-readings'
            )
            device_readings_resource_id = device_readings_resource['id']
            print(f"   ✅ Created /api/device-readings: {device_readings_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'device-readings' and 
                    resource.get('parentId') == api_resource_id):
                    device_readings_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/device-readings: {device_readings_resource_id}")
                    break
        
        if not device_readings_resource_id:
            print(f"❌ Could not create device-readings resource")
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
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == '{deviceId}' and 
                    resource.get('parentId') == device_readings_resource_id):
                    device_id_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/device-readings/{{deviceId}}: {device_id_resource_id}")
                    break
        
        if not device_id_resource_id:
            print(f"❌ Could not create device ID resource")
            return False
        
        # Create /latest under /api/device-readings/{deviceId}
        print(f"   🔧 Creating /api/device-readings/{{deviceId}}/latest...")
        
        latest_resource_id = None
        try:
            latest_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_id_resource_id,
                pathPart='latest'
            )
            latest_resource_id = latest_resource['id']
            print(f"   ✅ Created /api/device-readings/{{deviceId}}/latest: {latest_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'latest' and 
                    resource.get('parentId') == device_id_resource_id):
                    latest_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/device-readings/{{deviceId}}/latest: {latest_resource_id}")
                    break
        
        if not latest_resource_id:
            print(f"❌ Could not create latest resource")
            return False
        
        # Create /history under /api/device-readings/{deviceId}
        print(f"   🔧 Creating /api/device-readings/{{deviceId}}/history...")
        
        history_resource_id = None
        try:
            history_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_id_resource_id,
                pathPart='history'
            )
            history_resource_id = history_resource['id']
            print(f"   ✅ Created /api/device-readings/{{deviceId}}/history: {history_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Find existing resource
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'history' and 
                    resource.get('parentId') == device_id_resource_id):
                    history_resource_id = resource['id']
                    print(f"   ✅ Using existing /api/device-readings/{{deviceId}}/history: {history_resource_id}")
                    break
        
        if not history_resource_id:
            print(f"❌ Could not create history resource")
            return False
        
        # Add methods to both endpoints
        endpoints = [
            (latest_resource_id, 'latest'),
            (history_resource_id, 'history')
        ]
        
        for resource_id, endpoint_name in endpoints:
            print(f"\n   🔧 Setting up methods for /{endpoint_name}...")
            
            # Add OPTIONS method for CORS
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Add mock integration for OPTIONS
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={'application/json': '{"statusCode": 200}'}
                )
                
                # Add method response for OPTIONS
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
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
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
                
                print(f"     ✅ Added OPTIONS method")
                
            except Exception as e:
                print(f"     ⚠️ OPTIONS method may already exist: {e}")
            
            # Add GET method
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    authorizationType='NONE'  # No auth for now to test
                )
                
                # Add Lambda integration for GET
                integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
                
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=integration_uri
                )
                
                print(f"     ✅ Added GET method with Lambda integration")
                
            except Exception as e:
                print(f"     ⚠️ GET method may already exist: {e}")
        
        # Give API Gateway permission to invoke Lambda
        print(f"\n   🔧 Adding Lambda permissions...")
        
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-device-readings',
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
            description='Added device readings endpoints'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating device readings endpoint: {e}")
        return False

def test_new_endpoints():
    """Test the new endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Testing new endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        endpoints = [
            f"{base_url}/api/device-readings/ESP32-001/latest",
            f"{base_url}/api/device-readings/ESP32-001/history"
        ]
        
        for endpoint in endpoints:
            print(f"\n   🔍 Testing: {endpoint}")
            
            try:
                # Test OPTIONS (CORS)
                options_response = requests.options(endpoint, timeout=10)
                print(f"     OPTIONS: {options_response.status_code}")
                print(f"     CORS: {options_response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
                
                # Test GET
                get_response = requests.get(endpoint, timeout=10)
                print(f"     GET: {get_response.status_code}")
                
                if get_response.status_code == 200:
                    print(f"     ✅ SUCCESS! Response: {get_response.text[:200]}")
                    
                    # Try to parse JSON
                    try:
                        data = get_response.json()
                        if data.get('success'):
                            print(f"     📊 Data received successfully")
                            if 'reading' in data:
                                reading = data['reading']
                                print(f"       pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                            elif 'readings' in data:
                                readings = data['readings']
                                print(f"       Found {len(readings)} readings")
                    except:
                        pass
                else:
                    print(f"     ❌ Error: {get_response.text[:100]}")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

def main():
    print("🔧 Creating Device Readings Endpoint")
    print("=" * 35)
    
    # Step 1: Create endpoints
    print("\n1. Creating API Gateway endpoints...")
    if not create_device_readings_endpoint():
        print("❌ Failed to create endpoints")
        return
    
    # Step 2: Test endpoints
    print("\n2. Testing endpoints...")
    test_new_endpoints()
    
    print(f"\n🎉 Device Readings API Created!")
    print(f"✅ Endpoints created:")
    print(f"   GET /api/device-readings/{{deviceId}}/latest")
    print(f"   GET /api/device-readings/{{deviceId}}/history")
    print(f"✅ CORS configured")
    print(f"✅ No authentication required (for testing)")
    
    print(f"\n💡 Next step: Update frontend to use new endpoints")
    print(f"   Change from: /api/v1/readings/{{deviceId}}/latest")
    print(f"   Change to:   /api/device-readings/{{deviceId}}/latest")

if __name__ == "__main__":
    main()