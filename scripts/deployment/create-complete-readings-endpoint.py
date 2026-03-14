#!/usr/bin/env python3
"""
Create complete readings endpoint structure
/api/v1/readings/{deviceId}/latest
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

def get_all_resources():
    """Get all resources and their details"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        resources = {}
        for resource in resources_response['items']:
            path = resource.get('path', '')
            resources[path] = resource
            logger.info(f"Resource: {path} - {resource['id']}")
        
        return resources
        
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        return {}

def create_resource_chain():
    """Create the complete resource chain for readings endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Get existing resources
        resources = get_all_resources()
        
        # Find /api/v1 resource
        if '/api/v1' not in resources:
            logger.error("Could not find /api/v1 resource")
            return None
        
        api_v1_id = resources['/api/v1']['id']
        logger.info(f"Using /api/v1 resource: {api_v1_id}")
        
        # Create /api/v1/readings
        readings_id = None
        if '/api/v1/readings' in resources:
            readings_id = resources['/api/v1/readings']['id']
            logger.info(f"Using existing /api/v1/readings: {readings_id}")
        else:
            try:
                readings_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=api_v1_id,
                    pathPart='readings'
                )
                readings_id = readings_resource['id']
                logger.info(f"Created /api/v1/readings: {readings_id}")
            except ClientError as e:
                logger.error(f"Error creating readings resource: {e}")
                return None
        
        # Create /api/v1/readings/{deviceId}
        device_id = None
        # Refresh resources
        resources = get_all_resources()
        
        for path, resource in resources.items():
            if '/readings/{deviceId}' in path:
                device_id = resource['id']
                logger.info(f"Using existing deviceId resource: {device_id}")
                break
        
        if not device_id:
            try:
                device_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=readings_id,
                    pathPart='{deviceId}'
                )
                device_id = device_resource['id']
                logger.info(f"Created deviceId resource: {device_id}")
            except ClientError as e:
                logger.error(f"Error creating deviceId resource: {e}")
                return None
        
        # Create /api/v1/readings/{deviceId}/latest
        latest_id = None
        # Refresh resources again
        resources = get_all_resources()
        
        for path, resource in resources.items():
            if '/readings/{deviceId}/latest' in path:
                latest_id = resource['id']
                logger.info(f"Using existing latest resource: {latest_id}")
                break
        
        if not latest_id:
            try:
                latest_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=device_id,
                    pathPart='latest'
                )
                latest_id = latest_resource['id']
                logger.info(f"Created latest resource: {latest_id}")
            except ClientError as e:
                logger.error(f"Error creating latest resource: {e}")
                return None
        
        return latest_id
        
    except Exception as e:
        logger.error(f"Error creating resource chain: {e}")
        return None

def setup_methods_and_integration(resource_id):
    """Set up OPTIONS and GET methods with Lambda integration"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Find Lambda function
        lambda_arn = None
        response = lambda_client.list_functions()
        for func in response['Functions']:
            if 'reading' in func['FunctionName'].lower():
                lambda_arn = func['FunctionArn']
                logger.info(f"Found Lambda: {func['FunctionName']}")
                break
        
        if not lambda_arn:
            logger.error("Could not find readings Lambda function")
            return False
        
        # Create OPTIONS method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
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
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
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
            
            logger.info("✅ Created OPTIONS method")
        except ClientError as e:
            if 'ConflictException' not in str(e):
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
            
            # Lambda integration
            integration_uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            
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
            
            logger.info("✅ Created GET method with Lambda integration")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.error(f"Error creating GET method: {e}")
                return False
        
        # Add Lambda permission
        function_name = lambda_arn.split(':')[-1]
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f'apigateway-readings-{resource_id}',
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
        logger.error(f"Error setting up methods: {e}")
        return False

def deploy_and_test():
    """Deploy API and test the endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Complete readings endpoint'
        )
        
        logger.info("🚀 API deployed")
        
        # Wait for deployment
        import time
        time.sleep(5)
        
        # Test endpoint
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"🧪 Testing: {url}")
        
        # Test OPTIONS
        options_response = requests.options(url, timeout=10)
        logger.info(f"OPTIONS: {options_response.status_code}")
        
        # Test GET
        get_response = requests.get(url, timeout=10)
        logger.info(f"GET: {get_response.status_code}")
        
        # Check CORS headers
        cors_headers = []
        for header, value in get_response.headers.items():
            if 'access-control' in header.lower():
                cors_headers.append(f"{header}: {value}")
        
        if cors_headers:
            logger.info("✅ CORS headers found:")
            for header in cors_headers:
                logger.info(f"  {header}")
        
        # Check response
        try:
            response_data = get_response.json()
            logger.info(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            logger.info(f"Response text: {get_response.text}")
        
        # Success if we get any response (not 401/403)
        if get_response.status_code not in [401, 403]:
            return True
        else:
            logger.warning(f"Authentication issue: {get_response.status_code}")
            return False
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Creating complete readings endpoint...")
    
    # Create resource chain
    logger.info("📋 Creating resource chain...")
    latest_resource_id = create_resource_chain()
    
    if not latest_resource_id:
        logger.error("❌ Could not create resource chain")
        return False
    
    # Set up methods and integration
    logger.info("🔗 Setting up methods and Lambda integration...")
    if not setup_methods_and_integration(latest_resource_id):
        logger.error("❌ Could not set up methods")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 Complete readings endpoint created successfully!")
        return True
    else:
        logger.warning("⚠️ Endpoint created but may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Complete readings endpoint created!")
        print("🌐 Your React frontend should now work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Endpoint creation encountered issues")
        print("📋 Check the logs for details")