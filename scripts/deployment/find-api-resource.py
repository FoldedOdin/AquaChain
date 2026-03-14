#!/usr/bin/env python3
"""
Find the missing /api resource by analyzing parent relationships
"""

import boto3
import json

def find_api_resource():
    """Find the /api resource by analyzing parent relationships"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        
        print(f"🔍 Finding /api resource by analyzing parent relationships...")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        # Build parent-child relationships
        resource_map = {}
        parent_counts = {}
        
        for resource in resources['items']:
            resource_id = resource['id']
            path = resource.get('path', '/')
            parent_id = resource.get('parentId')
            
            resource_map[resource_id] = resource
            
            if parent_id:
                if parent_id not in parent_counts:
                    parent_counts[parent_id] = []
                parent_counts[parent_id].append(resource_id)
        
        print(f"\n📊 Parent-child analysis:")
        
        # Find the most common parent (likely /api)
        for parent_id, children in parent_counts.items():
            if len(children) > 3:  # /api should have many children
                print(f"\n   📁 Parent {parent_id} has {len(children)} children:")
                
                # Check if this parent has /api-like children
                api_like_children = 0
                for child_id in children[:5]:  # Show first 5
                    child = resource_map.get(child_id, {})
                    child_path = child.get('path', '')
                    print(f"     - {child_path} ({child_id})")
                    
                    if child_path.startswith('/api/'):
                        api_like_children += 1
                
                if api_like_children > 0:
                    print(f"   🎯 This looks like the /api resource! ({parent_id})")
                    
                    # Get details of this resource
                    try:
                        parent_resource = apigateway.get_resource(
                            restApiId=api_id,
                            resourceId=parent_id
                        )
                        print(f"   📋 Resource details:")
                        print(f"     Path: {parent_resource.get('path', 'Unknown')}")
                        print(f"     Path Part: {parent_resource.get('pathPart', 'Unknown')}")
                        print(f"     Parent ID: {parent_resource.get('parentId', 'None')}")
                        
                        return parent_id
                        
                    except Exception as e:
                        print(f"   ❌ Error getting resource details: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error finding API resource: {e}")
        return None

def create_readings_under_api(api_resource_id):
    """Create readings endpoint under the found /api resource"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_name = 'aquachain-function-readings-service-dev'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:{function_name}"
        
        print(f"\n🔧 Creating readings endpoint under /api ({api_resource_id})...")
        
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
            print(f"   ⚠️ /api/device-readings already exists, finding it...")
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
            print(f"   ⚠️ /api/device-readings/{{deviceId}} already exists, finding it...")
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
            print(f"   ⚠️ /latest already exists, finding it...")
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'latest' and 
                    resource.get('parentId') == device_id_resource_id):
                    latest_resource_id = resource['id']
                    print(f"   ✅ Using existing /latest: {latest_resource_id}")
                    break
        
        if not latest_resource_id:
            print(f"❌ Could not create latest resource")
            return False
        
        # Add GET method to /latest
        print(f"   🔧 Adding GET method to /latest...")
        
        try:
            # Add GET method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=latest_resource_id,
                httpMethod='GET',
                authorizationType='NONE'  # No auth for testing
            )
            
            # Add Lambda integration
            integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=latest_resource_id,
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
                resourceId=latest_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Add mock integration for OPTIONS
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=latest_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            # Add method response for OPTIONS
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=latest_resource_id,
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
                resourceId=latest_resource_id,
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
                StatementId='api-gateway-invoke-device-readings-new',
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
        print(f"❌ Error creating readings endpoint: {e}")
        return False

def test_endpoint():
    """Test the new endpoint"""
    try:
        import requests
        
        print(f"\n🧪 Testing new endpoint...")
        
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/device-readings/ESP32-001/latest"
        
        print(f"   🔍 Testing: {url}")
        
        # Test GET
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! Response: {response.text[:200]}")
            
            try:
                data = response.json()
                if data.get('success'):
                    reading = data.get('reading', {})
                    print(f"   📊 Reading data:")
                    print(f"     pH: {reading.get('pH')}")
                    print(f"     Temperature: {reading.get('temperature')}")
                    print(f"     Timestamp: {reading.get('timestamp')}")
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
    print("🔧 Finding and Creating Readings Endpoint")
    print("=" * 40)
    
    # Step 1: Find the /api resource
    print("\n1. Finding /api resource...")
    api_resource_id = find_api_resource()
    
    if not api_resource_id:
        print("❌ Could not find /api resource")
        return
    
    # Step 2: Create readings endpoint
    print("\n2. Creating readings endpoint...")
    if not create_readings_under_api(api_resource_id):
        print("❌ Failed to create readings endpoint")
        return
    
    # Step 3: Test endpoint
    print("\n3. Testing endpoint...")
    if test_endpoint():
        print(f"\n🎉 Success!")
        print(f"✅ Created endpoint: /api/device-readings/{{deviceId}}/latest")
        print(f"✅ Lambda integration working")
        print(f"✅ CORS configured")
        
        print(f"\n💡 Next step: Update frontend to use new endpoint")
        print(f"   Change from: /api/v1/readings/{{deviceId}}/latest")
        print(f"   Change to:   /api/device-readings/{{deviceId}}/latest")
    else:
        print(f"\n❌ Endpoint created but not working properly")

if __name__ == "__main__":
    main()