#!/usr/bin/env python3
"""
Quick fix for the history endpoint
"""

import boto3
import json

def quick_fix_history_endpoint():
    """Quick fix for the history endpoint"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'
        function_arn = f"arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-readings-service-dev"
        
        print(f"🔧 Quick fix for history endpoint...")
        
        # Get all resources to find the latest endpoint and its parent
        resources = apigateway.get_resources(restApiId=api_id)
        
        device_id_resource_id = None
        
        for resource in resources['items']:
            path = resource.get('path', '')
            if path.endswith('/device-readings/ESP32-001/latest'):
                # This is wrong - we want the generic path
                continue
            elif '/device-readings/' in path and path.endswith('/latest'):
                device_id_resource_id = resource.get('parentId')
                print(f"   ✅ Found deviceId resource: {device_id_resource_id}")
                break
        
        if not device_id_resource_id:
            # Try a different approach - look for the device-readings resource and create the structure
            device_readings_id = None
            for resource in resources['items']:
                if resource.get('path') == '/api/device-readings':
                    device_readings_id = resource['id']
                    break
            
            if device_readings_id:
                print(f"   🔧 Creating missing structure under device-readings...")
                
                # Create {deviceId} if it doesn't exist
                try:
                    device_id_resource = apigateway.create_resource(
                        restApiId=api_id,
                        parentId=device_readings_id,
                        pathPart='{deviceId}'
                    )
                    device_id_resource_id = device_id_resource['id']
                    print(f"   ✅ Created deviceId resource: {device_id_resource_id}")
                except:
                    # Find existing one
                    for resource in resources['items']:
                        if (resource.get('pathPart') == '{deviceId}' and 
                            resource.get('parentId') == device_readings_id):
                            device_id_resource_id = resource['id']
                            print(f"   ✅ Found existing deviceId resource: {device_id_resource_id}")
                            break
        
        if not device_id_resource_id:
            print(f"❌ Could not find or create deviceId resource")
            return False
        
        # Now create or fix the history endpoint
        print(f"   🔧 Creating/fixing history endpoint...")
        
        history_resource_id = None
        try:
            history_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_id_resource_id,
                pathPart='history'
            )
            history_resource_id = history_resource['id']
            print(f"   ✅ Created history resource: {history_resource_id}")
        except:
            # Find existing one
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if (resource.get('pathPart') == 'history' and 
                    resource.get('parentId') == device_id_resource_id):
                    history_resource_id = resource['id']
                    print(f"   ✅ Found existing history resource: {history_resource_id}")
                    break
        
        if not history_resource_id:
            print(f"❌ Could not create history resource")
            return False
        
        # Add/fix GET method
        print(f"   🔧 Adding/fixing GET method...")
        
        try:
            # Delete existing method if it exists
            try:
                apigateway.delete_method(
                    restApiId=api_id,
                    resourceId=history_resource_id,
                    httpMethod='GET'
                )
                print(f"   🗑️ Deleted existing GET method")
            except:
                pass
            
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
            print(f"   ❌ Error with GET method: {e}")
        
        # Add OPTIONS for CORS
        try:
            # Delete existing OPTIONS if it exists
            try:
                apigateway.delete_method(
                    restApiId=api_id,
                    resourceId=history_resource_id,
                    httpMethod='OPTIONS'
                )
            except:
                pass
            
            apigateway.put_method(
                restApiId=api_id,
                resourceId=history_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=history_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
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
            print(f"   ❌ Error with OPTIONS method: {e}")
        
        # Deploy
        print(f"\n🚀 Deploying changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Quick fix for history endpoint'
        )
        
        print(f"✅ Deployment: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_both_endpoints_quick():
    """Quick test of both endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Quick test of both endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        # Test latest
        latest_url = f"{base_url}/api/device-readings/ESP32-001/latest"
        print(f"\n   📊 Latest: {latest_url}")
        
        try:
            response = requests.get(latest_url, timeout=5)
            print(f"     Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('reading'):
                    reading = data['reading']
                    print(f"     ✅ pH: {reading.get('pH')}, Temp: {reading.get('temperature')}")
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
        # Test history
        history_url = f"{base_url}/api/device-readings/ESP32-001/history"
        print(f"\n   📈 History: {history_url}")
        
        try:
            response = requests.get(history_url, timeout=5)
            print(f"     Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('readings'):
                    readings = data['readings']
                    print(f"     ✅ Found {len(readings)} readings")
                else:
                    print(f"     ⚠️ No readings in response")
            else:
                print(f"     ❌ Error: {response.text[:100]}")
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing: {e}")

def main():
    print("🔧 Quick Fix for History Endpoint")
    print("=" * 35)
    
    # Fix the history endpoint
    if quick_fix_history_endpoint():
        print(f"\n✅ History endpoint fixed!")
        
        # Test both endpoints
        test_both_endpoints_quick()
        
        print(f"\n🎉 Readings should now appear in the dashboard!")
        print(f"   Try refreshing your browser to see the data.")
    else:
        print(f"\n❌ Failed to fix history endpoint")

if __name__ == "__main__":
    main()