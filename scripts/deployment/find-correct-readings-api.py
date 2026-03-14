#!/usr/bin/env python3
"""
Find the correct API Gateway for readings endpoints
"""

import boto3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_all_apis():
    """List all API Gateways and their resources"""
    try:
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        # List all APIs
        response = client.get_rest_apis()
        
        print("📡 Available API Gateways:")
        print("=" * 50)
        
        for api in response['items']:
            api_id = api['id']
            api_name = api['name']
            
            print(f"\n🔹 API: {api_name}")
            print(f"   ID: {api_id}")
            print(f"   URL: https://{api_id}.execute-api.ap-south-1.amazonaws.com/")
            
            # Get resources for this API
            try:
                resources_response = client.get_resources(restApiId=api_id)
                
                print("   Resources:")
                for resource in resources_response['items']:
                    path = resource.get('path', '/')
                    resource_id = resource['id']
                    methods = list(resource.get('resourceMethods', {}).keys())
                    
                    print(f"     {path} ({resource_id}) - Methods: {methods}")
                    
                    # Check if this looks like a readings endpoint
                    if 'readings' in path.lower():
                        print(f"     ⭐ READINGS ENDPOINT FOUND!")
                        
                        # Test this endpoint
                        test_url = f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev{path}"
                        if '{deviceId}' in path:
                            test_url = test_url.replace('{deviceId}', 'ESP32-001')
                        
                        print(f"     🧪 Test URL: {test_url}")
                        
                        # Try to make a request
                        try:
                            import requests
                            response = requests.get(test_url, timeout=5)
                            print(f"     📊 Status: {response.status_code}")
                            
                            # Check CORS headers
                            cors_headers = []
                            for header, value in response.headers.items():
                                if 'access-control' in header.lower():
                                    cors_headers.append(f"{header}: {value}")
                            
                            if cors_headers:
                                print(f"     🌐 CORS Headers: {cors_headers}")
                            else:
                                print(f"     ❌ No CORS headers found")
                                
                        except Exception as e:
                            print(f"     ⚠️ Request failed: {e}")
                
            except Exception as e:
                print(f"   ❌ Could not get resources: {e}")
        
        return response['items']
        
    except Exception as e:
        logger.error(f"Error listing APIs: {e}")
        return []

def find_readings_api():
    """Find the API that handles readings"""
    try:
        # The URL from the error message
        error_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        # Extract API ID from URL
        api_id = "vtqjfznspc"
        
        print(f"🎯 Checking API ID from error URL: {api_id}")
        
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        try:
            # Get API details
            api_response = client.get_rest_api(restApiId=api_id)
            print(f"✅ Found API: {api_response['name']}")
            
            # Get resources
            resources_response = client.get_resources(restApiId=api_id)
            
            print("\n📋 Resources in this API:")
            for resource in resources_response['items']:
                path = resource.get('path', '/')
                methods = list(resource.get('resourceMethods', {}).keys())
                print(f"  {path} - Methods: {methods}")
            
            return api_id
            
        except Exception as e:
            print(f"❌ API {api_id} not found or not accessible: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error finding readings API: {e}")
        return None

def main():
    """Main function"""
    print("🔍 Finding correct API Gateway for readings endpoints...")
    print("=" * 60)
    
    # First, try to find the API from the error URL
    readings_api = find_readings_api()
    
    if readings_api:
        print(f"\n✅ Found readings API: {readings_api}")
    else:
        print("\n❌ Could not find readings API from error URL")
        print("📋 Listing all available APIs...")
        
        # List all APIs to help identify the correct one
        apis = list_all_apis()
        
        if not apis:
            print("❌ No APIs found")
        else:
            print(f"\n📊 Found {len(apis)} API(s) total")

if __name__ == "__main__":
    main()