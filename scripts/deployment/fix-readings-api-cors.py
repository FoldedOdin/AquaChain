#!/usr/bin/env python3
"""
Fix CORS for the specific readings API
Target API: vtqjfznspc (aquachain-api-rest-dev)
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

def create_readings_endpoints():
    """Create the missing readings endpoints with proper CORS"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Get the root resource
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Find the /api/v1 resource
        api_v1_resource = None
        for resource in resources_response['items']:
            if resource.get('path') == '/api/v1':
                api_v1_resource = resource
                break
        
        if not api_v1_resource:
            logger.error("Could not find /api/v1 resource")
            return False
        
        api_v1_id = api_v1_resource['id']
        logger.info(f"Found /api/v1 resource: {api_v1_id}")
        
        # Create /api/v1/readings resource
        try:
            readings_resource = client.create_resource(
                restApiId=API_ID,
                parentId=api_v1_id,
                pathPart='readings'
            )
            readings_id = readings_resource['id']
            logger.info(f"Created /api/v1/readings resource: {readings_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Resource already exists, find it
                for resource in resources_response['items']:
                    if resource.get('path') == '/api/v1/readings':
                        readings_id = resource['id']
                        logger.info(f"Found existing /api/v1/readings resource: {readings_id}")
                        break
                else:
                    logger.error("Could not find or create readings resource")
                    return False
            else:
                logger.error(f"Error creating readings resource: {e}")
                return False
        
        # Create /api/v1/readings/{deviceId} resource
        try:
            device_resource = client.create_resource(
                restApiId=API_ID,
                parentId=readings_id,
                pathPart='{deviceId}'
            )
            device_id = device_resource['id']
            logger.info(f"Created /api/v1/readings/{{deviceId}} resource: {device_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Resource already exists, find it
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if resource.get('pathPart') == '{deviceId}' and '/readings/' in resource.get('path', ''):
                        device_id = resource['id']
                        logger.info(f"Found existing deviceId resource: {device_id}")
                        break
                else:
                    logger.error("Could not find or create deviceId resource")
                    return False
            else:
                logger.error(f"Error creating deviceId resource: {e}")
                return False
        
        # Create /api/v1/readings/{deviceId}/latest resource
        try:
            latest_resource = client.create_resource(
                restApiId=API_ID,
                parentId=device_id,
                pathPart='latest'
            )
            latest_id = latest_resource['id']
            logger.info(f"Created /api/v1/readings/{{deviceId}}/latest resource: {latest_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Resource already exists, find it
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if resource.get('pathPart') == 'latest' and '/readings/' in resource.get('path', ''):
                        latest_id = resource['id']
                        logger.info(f"Found existing latest resource: {latest_id}")
                        break
                else:
                    logger.error("Could not find or create latest resource")
                    return False
            else:
                logger.error(f"Error creating latest resource: {e}")
                return False
        
        return latest_id
        
    except Exception as e:
        logger.error(f"Error creating readings endpoints: {e}")
        return False

def add_cors_method(resource_id, resource_path):
    """Add CORS OPTIONS method to a resource"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Create OPTIONS method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            logger.info(f"Created OPTIONS method for {resource_path}")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.error(f"Error creating OPTIONS method: {e}")
                return False
        
        # Add method response for OPTIONS
        try:
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False,
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False
                }
            )
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add method response: {e}")
        
        # Add integration for OPTIONS (mock)
        try:
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add integration: {e}")
        
        # Add integration response for OPTIONS
        try:
            client.put_integration_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': ''
                }
            )
            logger.info(f"Added CORS integration response for {resource_path}")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add integration response: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding CORS method: {e}")
        return False

def add_get_method_with_cors(resource_id, resource_path):
    """Add GET method with Lambda integration and CORS"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Find the readings Lambda function
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        try:
            lambda_response = lambda_client.get_function(
                FunctionName='AquaChain-Function-ReadingsService-dev'
            )
            lambda_arn = lambda_response['Configuration']['FunctionArn']
            logger.info(f"Found Lambda function: {lambda_arn}")
        except Exception as e:
            logger.error(f"Could not find readings Lambda function: {e}")
            return False
        
        # Create GET method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            logger.info(f"Created GET method for {resource_path}")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.error(f"Error creating GET method: {e}")
                return False
        
        # Add method response for GET
        try:
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False,
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False
                }
            )
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add GET method response: {e}")
        
        # Add Lambda integration for GET
        integration_uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        try:
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            logger.info(f"Added Lambda integration for {resource_path}")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add Lambda integration: {e}")
        
        # Add integration response for GET
        try:
            client.put_integration_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                }
            )
            logger.info(f"Added CORS integration response for GET {resource_path}")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add GET integration response: {e}")
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName='AquaChain-Function-ReadingsService-dev',
                StatementId=f'apigateway-{resource_id}-get',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:*:{API_ID}/*/*'
            )
            logger.info(f"Added Lambda permission for {resource_path}")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                logger.info(f"Lambda permission already exists for {resource_path}")
            else:
                logger.warning(f"Could not add Lambda permission: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding GET method: {e}")
        return False

def deploy_api():
    """Deploy the API to make changes live"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        response = client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Readings API CORS fix'
        )
        
        logger.info(f"Deployed API {API_ID} to dev stage")
        return True
        
    except Exception as e:
        logger.error(f"Error deploying API: {e}")
        return False

def test_endpoint():
    """Test the fixed endpoint"""
    try:
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"Testing endpoint: {url}")
        
        # Test OPTIONS
        options_response = requests.options(url, timeout=10)
        logger.info(f"OPTIONS status: {options_response.status_code}")
        
        # Test GET
        get_response = requests.get(url, timeout=10)
        logger.info(f"GET status: {get_response.status_code}")
        
        # Check CORS headers
        cors_headers = []
        for header, value in get_response.headers.items():
            if 'access-control' in header.lower():
                cors_headers.append(f"{header}: {value}")
        
        if cors_headers:
            logger.info(f"CORS headers: {cors_headers}")
            return True
        else:
            logger.warning("No CORS headers found")
            return False
        
    except Exception as e:
        logger.error(f"Error testing endpoint: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Fixing CORS for readings API endpoints...")
    
    # Create the readings endpoints
    logger.info("📋 Creating readings endpoints...")
    latest_resource_id = create_readings_endpoints()
    
    if not latest_resource_id:
        logger.error("❌ Failed to create readings endpoints")
        return False
    
    # Add CORS to the latest endpoint
    logger.info("🌐 Adding CORS to /latest endpoint...")
    if not add_cors_method(latest_resource_id, "/api/v1/readings/{deviceId}/latest"):
        logger.error("❌ Failed to add CORS to latest endpoint")
        return False
    
    # Add GET method with Lambda integration
    logger.info("🔗 Adding GET method with Lambda integration...")
    if not add_get_method_with_cors(latest_resource_id, "/api/v1/readings/{deviceId}/latest"):
        logger.error("❌ Failed to add GET method")
        return False
    
    # Deploy API
    logger.info("🚀 Deploying API...")
    if not deploy_api():
        logger.error("❌ Failed to deploy API")
        return False
    
    # Wait for deployment
    import time
    time.sleep(5)
    
    # Test endpoint
    logger.info("🧪 Testing endpoint...")
    if test_endpoint():
        logger.info("✅ CORS fix successful!")
        return True
    else:
        logger.warning("⚠️ CORS fix may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Readings API CORS fix completed!")
        print("🌐 Your React frontend should now work without CORS errors")
    else:
        print("\n❌ CORS fix encountered issues")
        print("📋 Check the logs for details")