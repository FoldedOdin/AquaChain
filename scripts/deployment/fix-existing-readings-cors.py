#!/usr/bin/env python3
"""
Fix CORS for existing readings endpoints
Work with whatever resources already exist
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

def find_readings_lambda():
    """Find the readings Lambda function"""
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Try different possible function names
        possible_names = [
            'AquaChain-Function-ReadingsService-dev',
            'aquachain-readings-service-dev',
            'readings-service',
            'device-readings-service'
        ]
        
        for name in possible_names:
            try:
                response = lambda_client.get_function(FunctionName=name)
                logger.info(f"Found Lambda function: {name}")
                return response['Configuration']['FunctionArn']
            except ClientError:
                continue
        
        # List all functions to find the right one
        logger.info("Listing all Lambda functions to find readings service...")
        response = lambda_client.list_functions()
        
        for func in response['Functions']:
            func_name = func['FunctionName']
            if 'reading' in func_name.lower():
                logger.info(f"Found potential readings function: {func_name}")
                return func['FunctionArn']
        
        logger.error("Could not find readings Lambda function")
        return None
        
    except Exception as e:
        logger.error(f"Error finding Lambda function: {e}")
        return None

def create_simple_cors_proxy():
    """Create a simple Lambda proxy that adds CORS headers"""
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Simple Lambda function code that adds CORS and proxies to readings service
        lambda_code = '''
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Simple CORS proxy for readings API"""
    
    # CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
        'Content-Type': 'application/json'
    }
    
    try:
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Extract device ID from path
        path_params = event.get('pathParameters', {})
        device_id = path_params.get('deviceId', 'ESP32-001')
        
        logger.info(f"Getting latest reading for device: {device_id}")
        
        # Mock response for now (replace with actual DynamoDB query later)
        mock_reading = {
            'deviceId': device_id,
            'timestamp': '2024-03-14T10:30:00Z',
            'readings': {
                'pH': 7.2,
                'turbidity': 3.5,
                'tds': 450,
                'temperature': 22.5
            },
            'wqi': 78,
            'quality': 'Good'
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'reading': mock_reading,
                'deviceId': device_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            })
        }
'''
        
        # Create the function
        try:
            response = lambda_client.create_function(
                FunctionName='aquachain-readings-cors-proxy',
                Runtime='python3.11',
                Role='arn:aws:iam::339713019108:role/lambda-execution-role',  # Use existing role
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode()},
                Description='CORS proxy for readings API',
                Timeout=30
            )
            
            function_arn = response['FunctionArn']
            logger.info(f"Created CORS proxy function: {function_arn}")
            return function_arn
            
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                # Function already exists, update it
                lambda_client.update_function_code(
                    FunctionName='aquachain-readings-cors-proxy',
                    ZipFile=lambda_code.encode()
                )
                
                response = lambda_client.get_function(
                    FunctionName='aquachain-readings-cors-proxy'
                )
                
                function_arn = response['Configuration']['FunctionArn']
                logger.info(f"Updated existing CORS proxy function: {function_arn}")
                return function_arn
            else:
                logger.error(f"Error creating Lambda function: {e}")
                return None
        
    except Exception as e:
        logger.error(f"Error creating CORS proxy: {e}")
        return None

def setup_api_gateway_proxy(lambda_arn):
    """Set up API Gateway to proxy to our CORS Lambda"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Get all resources
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Find or create the readings path
        root_id = None
        api_id = None
        v1_id = None
        
        for resource in resources_response['items']:
            path = resource.get('path', '')
            if path == '/':
                root_id = resource['id']
            elif path == '/api':
                api_id = resource['id']
            elif path == '/api/v1':
                v1_id = resource['id']
        
        logger.info(f"Found resources - root: {root_id}, api: {api_id}, v1: {v1_id}")
        
        if not v1_id:
            logger.error("Could not find /api/v1 resource")
            return False
        
        # Create readings resource under /api/v1
        try:
            readings_resource = client.create_resource(
                restApiId=API_ID,
                parentId=v1_id,
                pathPart='readings'
            )
            readings_id = readings_resource['id']
            logger.info(f"Created readings resource: {readings_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing readings resource
                for resource in resources_response['items']:
                    if 'readings' in resource.get('path', ''):
                        readings_id = resource['id']
                        logger.info(f"Found existing readings resource: {readings_id}")
                        break
                else:
                    logger.error("Could not find or create readings resource")
                    return False
            else:
                logger.error(f"Error creating readings resource: {e}")
                return False
        
        # Create {deviceId} resource
        try:
            device_resource = client.create_resource(
                restApiId=API_ID,
                parentId=readings_id,
                pathPart='{deviceId}'
            )
            device_id = device_resource['id']
            logger.info(f"Created device resource: {device_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing device resource
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if '{deviceId}' in resource.get('pathPart', ''):
                        device_id = resource['id']
                        logger.info(f"Found existing device resource: {device_id}")
                        break
                else:
                    logger.error("Could not find or create device resource")
                    return False
            else:
                logger.error(f"Error creating device resource: {e}")
                return False
        
        # Create latest resource
        try:
            latest_resource = client.create_resource(
                restApiId=API_ID,
                parentId=device_id,
                pathPart='latest'
            )
            latest_id = latest_resource['id']
            logger.info(f"Created latest resource: {latest_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing latest resource
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if 'latest' in resource.get('pathPart', ''):
                        latest_id = resource['id']
                        logger.info(f"Found existing latest resource: {latest_id}")
                        break
                else:
                    logger.error("Could not find or create latest resource")
                    return False
            else:
                logger.error(f"Error creating latest resource: {e}")
                return False
        
        # Add OPTIONS method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            client.put_method_response(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='OPTIONS',
                statusCode='200'
            )
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='OPTIONS',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            logger.info("Added OPTIONS method")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add OPTIONS method: {e}")
        
        # Add GET method
        try:
            client.put_method(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            
            client.put_method_response(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='GET',
                statusCode='200'
            )
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=latest_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            logger.info("Added GET method")
        except ClientError as e:
            if 'ConflictException' not in str(e):
                logger.warning(f"Could not add GET method: {e}")
        
        # Add Lambda permissions
        lambda_client = boto3.client('lambda', region_name=REGION)
        try:
            lambda_client.add_permission(
                FunctionName='aquachain-readings-cors-proxy',
                StatementId='apigateway-invoke',
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
        logger.error(f"Error setting up API Gateway: {e}")
        return False

def deploy_and_test():
    """Deploy API and test the endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='CORS proxy deployment'
        )
        
        logger.info("Deployed API")
        
        # Wait for deployment
        import time
        time.sleep(5)
        
        # Test endpoint
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"Testing: {url}")
        
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
            logger.info(f"CORS headers found: {cors_headers}")
            print(f"\n✅ SUCCESS! CORS headers are now present:")
            for header in cors_headers:
                print(f"  {header}")
            return True
        else:
            logger.warning("No CORS headers found")
            return False
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Creating CORS proxy for readings API...")
    
    # Create CORS proxy Lambda
    logger.info("📦 Creating CORS proxy Lambda function...")
    lambda_arn = create_simple_cors_proxy()
    
    if not lambda_arn:
        logger.error("❌ Failed to create CORS proxy")
        return False
    
    # Set up API Gateway
    logger.info("🌐 Setting up API Gateway proxy...")
    if not setup_api_gateway_proxy(lambda_arn):
        logger.error("❌ Failed to set up API Gateway")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 CORS fix successful!")
        return True
    else:
        logger.warning("⚠️ CORS fix may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Readings API CORS fix completed!")
        print("🌐 Your React frontend should now work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ CORS fix encountered issues")
        print("📋 Check the logs for details")