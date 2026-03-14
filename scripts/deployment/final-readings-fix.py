#!/usr/bin/env python3
"""
Final fix - find existing resources and set up Lambda integration
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = "vtqjfznspc"
REGION = "ap-south-1"

def find_all_existing_resources():
    """Find all existing resources and their complete paths"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Find resources that could be readings endpoints
        readings_endpoints = []
        
        for resource in resources_response['items']:
            path = resource.get('path', '')
            
            # Look for paths that end with /latest or contain readings/device
            if (path.endswith('/latest') or 
                ('reading' in path.lower() and '{deviceId}' in path) or
                ('device' in path.lower() and '{deviceId}' in path)):
                
                readings_endpoints.append(resource)
                logger.info(f"Found potential readings endpoint: {path} - {resource['id']}")
        
        return readings_endpoints
        
    except Exception as e:
        logger.error(f"Error finding resources: {e}")
        return []

def setup_lambda_for_resource(resource_id, resource_path):
    """Set up Lambda integration for a specific resource"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        logger.info(f"Setting up Lambda for: {resource_path}")
        
        # Find Lambda function
        lambda_arn = None
        function_name = None
        
        response = lambda_client.list_functions()
        for func in response['Functions']:
            if 'reading' in func['FunctionName'].lower():
                lambda_arn = func['FunctionArn']
                function_name = func['FunctionName']
                logger.info(f"Found Lambda: {function_name}")
                break
        
        if not lambda_arn:
            logger.error("Could not find readings Lambda function")
            return False
        
        # Clear existing methods
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']:
            try:
                client.delete_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod=method
                )
                logger.info(f"Deleted existing {method} method")
            except ClientError:
                pass
        
        # Create OPTIONS method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            logger.info("✅ Created OPTIONS method")
        except ClientError as e:
            logger.error(f"Error creating OPTIONS: {e}")
            return False
        
        # Create GET method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            logger.info("✅ Created GET method")
        except ClientError as e:
            logger.error(f"Error creating GET: {e}")
            return False
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f'apigateway-{resource_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:*:{API_ID}/*/*'
            )
            logger.info("✅ Added Lambda permission")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                logger.info("Lambda permission already exists")
            else:
                logger.warning(f"Could not add Lambda permission: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Lambda integration: {e}")
        return False

def create_missing_latest_endpoints():
    """Create /latest endpoints under existing {deviceId} resources"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Find {deviceId} resources
        device_id_resources = []
        for resource in resources_response['items']:
            path_part = resource.get('pathPart', '')
            path = resource.get('path', '')
            
            if path_part == '{deviceId}' and ('reading' in path.lower() or 'device' in path.lower()):
                device_id_resources.append(resource)
                logger.info(f"Found deviceId resource: {path} - {resource['id']}")
        
        latest_resources = []
        
        for device_resource in device_id_resources:
            device_id = device_resource['id']
            device_path = device_resource.get('path', '')
            
            # Check if latest already exists
            latest_exists = False
            for resource in resources_response['items']:
                if (resource.get('pathPart') == 'latest' and 
                    resource.get('parentId') == device_id):
                    latest_exists = True
                    latest_resources.append(resource)
                    logger.info(f"Found existing latest: {resource.get('path')} - {resource['id']}")
                    break
            
            if not latest_exists:
                # Create latest endpoint
                try:
                    latest_resource = client.create_resource(
                        restApiId=API_ID,
                        parentId=device_id,
                        pathPart='latest'
                    )
                    latest_resources.append(latest_resource)
                    logger.info(f"Created latest endpoint: {device_path}/latest - {latest_resource['id']}")
                except ClientError as e:
                    logger.error(f"Error creating latest endpoint: {e}")
        
        return latest_resources
        
    except Exception as e:
        logger.error(f"Error creating missing latest endpoints: {e}")
        return []

def deploy_and_test():
    """Deploy and test the endpoints"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Final readings endpoints fix'
        )
        
        logger.info("🚀 API deployed")
        
        # Wait for deployment
        import time
        time.sleep(8)
        
        # Test the main endpoint
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"🧪 Testing: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            logger.info(f"Status: {response.status_code}")
            
            # Check CORS headers
            cors_headers = []
            for header, value in response.headers.items():
                if 'access-control' in header.lower():
                    cors_headers.append(f"{header}: {value}")
            
            if cors_headers:
                logger.info("✅ CORS headers found:")
                for header in cors_headers:
                    logger.info(f"  {header}")
                
                # Check response content
                try:
                    response_data = response.json()
                    logger.info(f"Response: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"Response text: {response.text}")
                
                return True
            else:
                logger.warning("⚠️ No CORS headers found")
                return False
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Final readings endpoint fix...")
    
    # Find existing resources
    logger.info("🔍 Finding existing resources...")
    existing_endpoints = find_all_existing_resources()
    
    # Create missing /latest endpoints
    logger.info("📋 Creating missing /latest endpoints...")
    latest_endpoints = create_missing_latest_endpoints()
    
    # Set up Lambda integration for all endpoints
    all_endpoints = existing_endpoints + latest_endpoints
    
    if not all_endpoints:
        logger.error("❌ No endpoints found or created")
        return False
    
    success_count = 0
    for endpoint in all_endpoints:
        resource_id = endpoint['id']
        resource_path = endpoint.get('path', '')
        
        logger.info(f"🔗 Setting up Lambda integration for: {resource_path}")
        if setup_lambda_for_resource(resource_id, resource_path):
            success_count += 1
    
    if success_count == 0:
        logger.error("❌ Could not set up any Lambda integrations")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 Final readings endpoint fix successful!")
        return True
    else:
        logger.warning("⚠️ Fix completed but may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Final readings endpoint fix completed!")
        print("🌐 Your React frontend should now work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Final fix encountered issues")
        print("📋 Check the logs for details")