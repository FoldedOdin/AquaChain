#!/usr/bin/env python3
"""
Create proper Lambda integration for readings endpoint
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

def find_lambda_function():
    """Find the readings Lambda function"""
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # List all functions and find the readings service
        response = lambda_client.list_functions()
        
        for func in response['Functions']:
            func_name = func['FunctionName']
            if 'reading' in func_name.lower() or 'ReadingsService' in func_name:
                logger.info(f"Found readings Lambda: {func_name}")
                return func['FunctionArn']
        
        logger.error("Could not find readings Lambda function")
        return None
        
    except Exception as e:
        logger.error(f"Error finding Lambda function: {e}")
        return None

def create_readings_endpoint():
    """Create the readings endpoint with proper Lambda integration"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Get all resources
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
        
        # Create or find readings resource
        readings_id = None
        for resource in resources_response['items']:
            if resource.get('path') == '/api/v1/readings':
                readings_id = resource['id']
                logger.info(f"Found existing readings resource: {readings_id}")
                break
        
        if not readings_id:
            try:
                readings_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=api_v1_id,
                    pathPart='readings'
                )
                readings_id = readings_resource['id']
                logger.info(f"Created readings resource: {readings_id}")
            except ClientError as e:
                logger.error(f"Error creating readings resource: {e}")
                return False
        
        # Create or find {deviceId} resource
        device_id = None
        resources_response = client.get_resources(restApiId=API_ID)  # Refresh
        for resource in resources_response['items']:
            if resource.get('pathPart') == '{deviceId}' and '/readings/' in resource.get('path', ''):
                device_id = resource['id']
                logger.info(f"Found existing deviceId resource: {device_id}")
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
                return False
        
        # Create or find latest resource
        latest_id = None
        resources_response = client.get_resources(restApiId=API_ID)  # Refresh
        for resource in resources_response['items']:
            if resource.get('pathPart') == 'latest' and '/readings/' in resource.get('path', ''):
                latest_id = resource['id']
                logger.info(f"Found existing latest resource: {latest_id}")
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
                return False
        
        return latest_id
        
    except Exception as e:
        logger.error(f"Error creating readings endpoint: {e}")
        return False

def setup_lambda_integration(resource_id, lambda_arn):
    """Set up Lambda integration for the endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Remove authorization requirement (make it public)
        # Create GET method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='NONE'  # No authentication required
            )
            logger.info("Created GET method without authentication")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.error(f"Error creating GET method: {e}")
                return False
        
        # Add method response
        try:
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='GET',
                statusCode='200'
            )
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add method response: {e}")
        
        # Add Lambda integration
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
            logger.info("Added Lambda integration")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.error(f"Error adding Lambda integration: {e}")
                return False
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName=lambda_arn.split(':')[-1],  # Extract function name from ARN
                StatementId=f'apigateway-{resource_id}-get',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:*:{API_ID}/*/*'
            )
            logger.info("Added Lambda permission")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                logger.info("Lambda permission already exists")
            else:
                logger.warning(f"Could not add Lambda permission: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Lambda integration: {e}")
        return False

def deploy_lambda_changes():
    """Deploy the updated Lambda function"""
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Find the Lambda function
        response = lambda_client.list_functions()
        
        readings_function = None
        for func in response['Functions']:
            if 'reading' in func['FunctionName'].lower():
                readings_function = func['FunctionName']
                break
        
        if not readings_function:
            logger.error("Could not find readings Lambda function to update")
            return False
        
        # Read the updated handler code
        with open('../../lambda/readings_service/handler.py', 'r') as f:
            handler_code = f.read()
        
        # Create a simple zip file with the handler
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('handler.py', handler_code)
        
        zip_buffer.seek(0)
        
        # Update the function code
        lambda_client.update_function_code(
            FunctionName=readings_function,
            ZipFile=zip_buffer.read()
        )
        
        logger.info(f"Updated Lambda function: {readings_function}")
        return True
        
    except Exception as e:
        logger.error(f"Error deploying Lambda changes: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Creating readings endpoint with Lambda integration...")
    
    # Find Lambda function
    lambda_arn = find_lambda_function()
    if not lambda_arn:
        logger.error("❌ Could not find Lambda function")
        return False
    
    # Deploy Lambda changes first
    logger.info("📦 Deploying Lambda changes...")
    if not deploy_lambda_changes():
        logger.warning("⚠️ Could not deploy Lambda changes, continuing with existing function")
    
    # Create endpoint
    logger.info("🌐 Creating readings endpoint...")
    resource_id = create_readings_endpoint()
    if not resource_id:
        logger.error("❌ Could not create readings endpoint")
        return False
    
    # Set up Lambda integration
    logger.info("🔗 Setting up Lambda integration...")
    if not setup_lambda_integration(resource_id, lambda_arn):
        logger.error("❌ Could not set up Lambda integration")
        return False
    
    # Deploy API
    logger.info("🚀 Deploying API...")
    try:
        client = boto3.client('apigateway', region_name=REGION)
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Readings endpoint integration'
        )
        logger.info("✅ API deployed")
    except Exception as e:
        logger.error(f"❌ Error deploying API: {e}")
        return False
    
    # Test endpoint
    logger.info("🧪 Testing endpoint...")
    import time
    time.sleep(5)
    
    try:
        import requests
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        response = requests.get(url, timeout=10)
        logger.info(f"Test response status: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 is OK if no data
            logger.info("✅ Endpoint is working!")
            return True
        else:
            logger.warning(f"⚠️ Endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing endpoint: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Readings endpoint integration completed!")
        print("🌐 Your React frontend should now work without CORS errors")
    else:
        print("\n❌ Endpoint integration encountered issues")
        print("📋 Check the logs for details")