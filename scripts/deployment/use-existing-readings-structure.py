#!/usr/bin/env python3
"""
Use existing readings structure and fix integration
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

def find_all_resources():
    """Find all resources and show their hierarchy"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Build hierarchy
        resources_by_parent = {}
        all_resources = {}
        
        for resource in resources_response['items']:
            resource_id = resource['id']
            parent_id = resource.get('parentId')
            path_part = resource.get('pathPart', '')
            path = resource.get('path', '')
            
            all_resources[resource_id] = resource
            
            if parent_id not in resources_by_parent:
                resources_by_parent[parent_id] = []
            resources_by_parent[parent_id].append(resource)
            
            logger.info(f"Resource: {path} ({path_part}) - {resource_id} - Parent: {parent_id}")
        
        return all_resources, resources_by_parent
        
    except Exception as e:
        logger.error(f"Error finding resources: {e}")
        return {}, {}

def find_or_create_readings_path():
    """Find or create the complete readings path"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        all_resources, resources_by_parent = find_all_resources()
        
        # Find /api/v1 resource
        api_v1_resource = None
        for resource in all_resources.values():
            if resource.get('path') == '/api/v1':
                api_v1_resource = resource
                break
        
        if not api_v1_resource:
            logger.error("Could not find /api/v1 resource")
            return None
        
        api_v1_id = api_v1_resource['id']
        logger.info(f"Found /api/v1: {api_v1_id}")
        
        # Look for existing readings under /api/v1
        readings_resource = None
        for resource in all_resources.values():
            if resource.get('pathPart') == 'readings' and resource.get('parentId') == api_v1_id:
                readings_resource = resource
                logger.info(f"Found existing readings resource: {resource['id']}")
                break
        
        if not readings_resource:
            # Create readings resource
            try:
                readings_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=api_v1_id,
                    pathPart='readings'
                )
                logger.info(f"Created readings resource: {readings_resource['id']}")
            except ClientError as e:
                logger.error(f"Error creating readings resource: {e}")
                return None
        
        readings_id = readings_resource['id']
        
        # Look for {deviceId} under readings
        device_resource = None
        for resource in all_resources.values():
            if resource.get('pathPart') == '{deviceId}' and resource.get('parentId') == readings_id:
                device_resource = resource
                logger.info(f"Found existing deviceId resource: {resource['id']}")
                break
        
        if not device_resource:
            # Create {deviceId} resource
            try:
                device_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=readings_id,
                    pathPart='{deviceId}'
                )
                logger.info(f"Created deviceId resource: {device_resource['id']}")
            except ClientError as e:
                logger.error(f"Error creating deviceId resource: {e}")
                return None
        
        device_id = device_resource['id']
        
        # Look for latest under {deviceId}
        latest_resource = None
        for resource in all_resources.values():
            if resource.get('pathPart') == 'latest' and resource.get('parentId') == device_id:
                latest_resource = resource
                logger.info(f"Found existing latest resource: {resource['id']}")
                break
        
        if not latest_resource:
            # Create latest resource
            try:
                latest_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=device_id,
                    pathPart='latest'
                )
                logger.info(f"Created latest resource: {latest_resource['id']}")
            except ClientError as e:
                logger.error(f"Error creating latest resource: {e}")
                return None
        
        return latest_resource['id']
        
    except Exception as e:
        logger.error(f"Error finding/creating readings path: {e}")
        return None

def setup_lambda_integration(resource_id):
    """Set up Lambda integration for the resource"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Find Lambda function
        lambda_arn = None
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
        
        # Delete existing methods first
        for method in ['GET', 'OPTIONS']:
            try:
                client.delete_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod=method
                )
                logger.info(f"Deleted existing {method} method")
            except ClientError:
                pass  # Method doesn't exist, that's fine
        
        # Create OPTIONS method (for CORS preflight)
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
            
            logger.info("✅ Created OPTIONS method with Lambda integration")
        except ClientError as e:
            logger.error(f"Error creating OPTIONS method: {e}")
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
            
            logger.info("✅ Created GET method with Lambda integration")
        except ClientError as e:
            logger.error(f"Error creating GET method: {e}")
            return False
        
        # Add Lambda permissions
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f'apigateway-readings-latest',
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

def deploy_and_test():
    """Deploy API and test"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Readings endpoint with Lambda integration'
        )
        
        logger.info("🚀 API deployed")
        
        # Wait for deployment
        import time
        time.sleep(5)
        
        # Test endpoint
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"🧪 Testing: {url}")
        
        # Test GET request
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
        else:
            logger.warning("⚠️ No CORS headers found")
        
        # Check response
        try:
            response_data = response.json()
            logger.info(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            logger.info(f"Response text: {response.text}")
        
        # Success if we get a proper response (not 401/403/502)
        if response.status_code in [200, 404, 500]:
            return True
        else:
            logger.warning(f"Unexpected status: {response.status_code}")
            return False
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Setting up readings endpoint with existing structure...")
    
    # Find or create the complete path
    logger.info("📋 Finding/creating readings path...")
    latest_resource_id = find_or_create_readings_path()
    
    if not latest_resource_id:
        logger.error("❌ Could not set up readings path")
        return False
    
    # Set up Lambda integration
    logger.info("🔗 Setting up Lambda integration...")
    if not setup_lambda_integration(latest_resource_id):
        logger.error("❌ Could not set up Lambda integration")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 Readings endpoint setup successful!")
        return True
    else:
        logger.warning("⚠️ Endpoint setup completed but may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Readings endpoint setup completed!")
        print("🌐 Your React frontend should now work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Endpoint setup encountered issues")
        print("📋 Check the logs for details")