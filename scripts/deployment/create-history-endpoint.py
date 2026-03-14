#!/usr/bin/env python3
"""
Create the history endpoint for device readings
"""

import boto3
import json

def create_history_endpoint():
    """Create the history endpoint"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_name = 'aquachain-function-readings-service-dev'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:{function_name}"
        
        print(f"🔧 Creating history endpoint...")
        
        # Find the device-readings/{deviceId} resource
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_id_resource_id = None
        device_readings_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('path', '')
            path_part = resource.get('pathPart', '')
            
            if path == '/api/device-readings':
                device_readings_resource_id = resource['id']
                print(f"   ✅ Found /api/device-readings: {device_readings_resource_id}")
            elif path_part == '{deviceId}' and '/device-readings/' in path:
                device_id_resource_id = resource['id']
                print(f"   ✅ Found /api/device-readings/{{deviceId}}: {device_id_resource_id}")
        
        if not device_id_resource_id:
            print(f"❌ Could not find /api/device-readings/{{deviceId}} resource")
            print(f"   Available resources under device-readings:")
            for resource in resources['items']:
                if resource.get('parentId') == device_readings_resource_id:
                    print(f"     - {resource.get('path', 'Unknown')} ({resource['id']})")
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
            print(f"   ⚠️ /history already exists, finding it...")
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'history' and 
                    resource.get('parentId') == device_id_resource_id):
                    history_resource_id = resource['id']
                    print(f"   ✅ Using existing /history: {history_resource_id}")
                    break
        
        if not history_resource_id:
            print(f"❌ Could not create history resource")
            return False
        
        # Add GET method to /history
        print(f"   🔧 Adding GET method to /history...")
        
        try:
            # Add GET method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=history_resource_id,
                httpMethod='GET',
                authorizationType='NONE'  # No auth for testing
            )
            
            # Add Lambda integration
            integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=history_resource_id,
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
                resourceId=history_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add mock integration for OPTIONS
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=history_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            # Add method response for OPTIONS
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=history_resource_id,
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
                resourceId=history_resource_id,
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
        
        # Deploy the API
        print(f"\n🚀 Deploying API changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Added device readings history endpoint'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating history endpoint: {e}")
        return False

def test_history_endpoint():
    """Test the history endpoint"""
    try:
        import requests
        
        print(f"\n🧪 Testing history endpoint...")
        
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/device-readings/ESP32-001/history"
        
        print(f"   🔍 Testing: {url}")
        
        # Test GET
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! Response: {response.text[:200]}")
            
            try:
                data = response.json()
                if data.get('success'):
                    readings = data.get('readings', [])
                    print(f"   📊 Found {len(readings)} readings")
                    if readings:
                        latest = readings[0]
                        print(f"     Latest: {latest.get('timestamp')} - pH: {latest.get('pH')}")
            except:
                pass
                
            return True
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def main():
    print("🔧 Creating History Endpoint")
    print("=" * 30)
    
    # Step 1: Create history endpoint
    print("\n1. Creating history endpoint...")
    if not create_history_endpoint():
        print("❌ Failed to create history endpoint")
        return
    
    # Step 2: Test history endpoint
    print("\n2. Testing history endpoint...")
    if test_history_endpoint():
        print(f"\n🎉 Success!")
        print(f"✅ History endpoint created and working")
        print(f"✅ Both endpoints now available:")
        print(f"   - /api/device-readings/{{deviceId}}/latest")
        print(f"   - /api/device-readings/{{deviceId}}/history")
        
        print(f"\n💡 Frontend has been updated to use new endpoints")
        print(f"   The CORS issue should now be resolved!")
    else:
        print(f"\n❌ History endpoint created but not working properly")

if __name__ == "__main__":
    main()