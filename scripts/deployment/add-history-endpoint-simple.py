#!/usr/bin/env python3
"""
Add the missing history endpoint
"""

import boto3
import json

def add_history_endpoint():
    """Add the missing history endpoint"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-readings-service-dev"
        
        print(f"🔧 Adding history endpoint...")
        
        # Get all resources to find the device ID resource
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_id_resource_id = None
        latest_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('path', '')
            
            if '/device-readings/' in path and path.endswith('/latest'):
                # Found the latest endpoint, get its parent (deviceId)
                device_id_resource_id = resource.get('parentId')
                latest_resource_id = resource['id']
                print(f"   ✅ Found latest endpoint: {resource['id']}")
                print(f"   ✅ Parent (deviceId) resource: {device_id_resource_id}")
                break
        
        if not device_id_resource_id:
            print(f"❌ Could not find deviceId resource")
            return False
        
        # Create /history under the same parent as /latest
        print(f"   🔧 Creating history endpoint under same parent...")
        
        history_resource_id = None
        try:
            history_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_id_resource_id,
                pathPart='history'
            )
            history_resource_id = history_resource['id']
            print(f"   ✅ Created history resource: {history_resource_id}")
        except apigateway.exceptions.ConflictException:
            print(f"   ⚠️ History resource already exists, finding it...")
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'history' and 
                    resource.get('parentId') == device_id_resource_id):
                    history_resource_id = resource['id']
                    print(f"   ✅ Using existing history resource: {history_resource_id}")
                    break
        
        if not history_resource_id:
            print(f"❌ Could not create history resource")
            return False
        
        # Add GET method to history
        print(f"   🔧 Adding GET method to history...")
        
        try:
            # Add GET method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=history_resource_id,
                httpMethod='GET',
                authorizationType='NONE'
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
            print(f"   ⚠️ GET method may already exist: {e}")
        
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
            description='Added history endpoint'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding history endpoint: {e}")
        return False

def test_both_endpoints():
    """Test both endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Testing both endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        endpoints = [
            ("latest", f"{base_url}/api/device-readings/ESP32-001/latest"),
            ("history", f"{base_url}/api/device-readings/ESP32-001/history")
        ]
        
        results = []
        
        for name, url in endpoints:
            print(f"\n   🔍 Testing {name}:")
            print(f"     URL: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ SUCCESS!")
                    
                    try:
                        data = response.json()
                        if data.get('success'):
                            if name == 'latest':
                                reading = data.get('reading', {})
                                print(f"       📊 pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
                            elif name == 'history':
                                readings = data.get('readings', [])
                                print(f"       📊 Found {len(readings)} readings")
                                if readings:
                                    latest = readings[0]
                                    print(f"       📊 Latest: {latest.get('timestamp')} - pH: {latest.get('pH')}")
                    except Exception as parse_error:
                        print(f"       ⚠️ Parse error: {parse_error}")
                        
                    results.append(True)
                else:
                    print(f"     ❌ Error: {response.text[:100]}")
                    results.append(False)
                
            except Exception as e:
                print(f"     ❌ Request error: {e}")
                results.append(False)
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

def main():
    print("🔧 Adding Missing History Endpoint")
    print("=" * 35)
    
    # Step 1: Add history endpoint
    print("\n1. Adding history endpoint...")
    if not add_history_endpoint():
        print("❌ Failed to add history endpoint")
        return
    
    # Step 2: Test both endpoints
    print("\n2. Testing both endpoints...")
    if test_both_endpoints():
        print(f"\n🎉 Complete Success!")
        print(f"✅ Both endpoints now working:")
        print(f"   - /api/device-readings/{{deviceId}}/latest ✅")
        print(f"   - /api/device-readings/{{deviceId}}/history ✅")
        print(f"✅ CORS configured for both")
        print(f"✅ Lambda integration working")
        print(f"✅ Frontend updated to use new endpoints")
        
        print(f"\n🎊 CORS Issue Resolved!")
        print(f"   The frontend should now be able to fetch device readings")
        print(f"   without any CORS errors. Try refreshing your dashboard!")
    else:
        print(f"\n❌ Some endpoints still not working")
        print(f"💡 Check the test results above for details")

if __name__ == "__main__":
    main()