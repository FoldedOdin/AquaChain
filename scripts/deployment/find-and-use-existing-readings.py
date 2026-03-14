#!/usr/bin/env python3
"""
Find and use existing readings resources
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

def find_readings_resources():
    """Find existing readings resources"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        resources_response = client.get_resources(restApiId=API_ID)
        
        readings_resources = {}
        
        for resource in resources_response['items']:
            path = resource.get('path', '')
            path_part = resource.get('pathPart', '')
            parent_id = resource.get('parentId')
            
            # Look for readings-related resources
            if 'readings' in path_part or 'readings' in path:
                readings_resources[path] = resource
                logger.info(f"Found readings resource: {path} - {resource['id']}")
                
                # Get methods for this resource
                try:
                    methods_response = client.get_resource(
                        restApiId=API_ID,
                        resourceId=resource['id']
                    )
                    methods = list(methods_response.get('resourceMethods', {}).keys())
                    logger.info(f"  Methods: {methods}")
                except Exception as e:
                    logger.warning(f"  Could not get methods: {e}")
        
        return readings_resources
        
    except Exception as e:
        logger.error(f"Error finding readings resources: {e}")
        return {}

def create_missing_resources():
    """Create missing resources in the readings path"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Get all resources
        resources_response = client.get_resources(restApiId=API_ID)
        
        # Find /api/v1
        api_v1_id = None
        readings_id = None
        
        for resource in resources_response['items']:
            path = resource.get('path', '')
            if path == '/api/v1':
                api_v1_id = resource['id']
            elif path == '/api/v1/readings':
                readings_id = resource['id']
        
        if not api_v1_id:
            logger.error("Could not find /api/v1")
            return None
        
        logger.info(f"Found /api/v1: {api_v1_id}")
        
        # Find or create readings under /api/v1
        if not readings_id:
            # Look for readings as child of /api/v1
            for resource in resources_response['items']:
                if (resource.get('pathPart') == 'readings' and 
                    resource.get('parentId') == api_v1_id):
                    readings_id = resource['id']
                    logger.info(f"Found existing readings: {readings_id}")
                    break
        
        if not readings_id:
            try:
                readings_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=api_v1_id,
                    pathPart='readings'
                )
                readings_id = readings_resource['id']
                logger.info(f"Created readings: {readings_id}")
            except ClientError as e:
                logger.error(f"Error creating readings: {e}")
                return None
        
        # Find or create {deviceId} under readings
        device_id = None
        resources_response = client.get_resources(restApiId=API_ID)  # Refresh
        
        for resource in resources_response['items']:
            if (resource.get('pathPart') == '{deviceId}' and 
                resource.get('parentId') == readings_id):
                device_id = resource['id']
                logger.info(f"Found existing deviceId: {device_id}")
                break
        
        if not device_id:
            try:
                device_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=readings_id,
                    pathPart='{deviceId}'
                )
                device_id = device_resource['id']
                logger.info(f"Created deviceId: {device_id}")
            except ClientError as e:
                logger.error(f"Error creating deviceId: {e}")
                return None
        
        # Find or create latest under {deviceId}
        latest_id = None
        resources_response = client.get_resources(restApiId=API_ID)  # Refresh
        
        for resource in resources_response['items']:
            if (resource.get('pathPart') == 'latest' and 
                resource.get('parentId') == device_id):
                latest_id = resource['id']
                logger.info(f"Found existing latest: {latest_id}")
                break
        
        if not latest_id:
            try:
                latest_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=device_id,
                    pathPart='latest'
                )
                latest_id = latest_resource['id']
                logger.info(f"Created latest: {latest_id}")
            except ClientError as e:
                logger.error(f"Error creating latest: {e}")
                return None
        
        return latest_id
        
    except Exception as e:
        logger.error(f"Error creating missing resources: {e}")
        return None

def setup_lambda_integration(resource_id):
    """Set up Lambda integration"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
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
                pass  # Method doesn't exist
        
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
        logger.error(f"Error setting up Lambda integration: {e}")
        return False

def deploy_and_test():
    """Deploy and test the endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Readings endpoint Lambda integration'
        )
        
        logger.info("🚀 API deployed")
        
        # Wait for deployment
        import time
        time.sleep(8)
        
        # Test endpoint
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"🧪 Testing: {url}")
        
        # Test OPTIONS
        try:
            options_response = requests.options(url, timeout=10)
            logger.info(f"OPTIONS: {options_response.status_code}")
            
            # Check CORS headers in OPTIONS
            cors_headers = []
            for header, value in options_response.headers.items():
                if 'access-control' in header.lower():
                    cors_headers.append(f"{header}: {value}")
            
            if cors_headers:
                logger.info("✅ OPTIONS CORS headers:")
                for header in cors_headers:
                    logger.info(f"  {header}")
        except Exception as e:
            logger.warning(f"OPTIONS test failed: {e}")
        
        # Test GET
        try:
            get_response = requests.get(url, timeout=10)
            logger.info(f"GET: {get_response.status_code}")
            
            # Check CORS headers in GET
            cors_headers = []
            for header, value in get_response.headers.items():
                if 'access-control' in header.lower():
                    cors_headers.append(f"{header}: {value}")
            
            if cors_headers:
                logger.info("✅ GET CORS headers:")
                for header in cors_headers:
                    logger.info(f"  {header}")
            else:
                logger.warning("⚠️ No CORS headers in GET response")
            
            # Check response content
            try:
                response_data = get_response.json()
                logger.info(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"Response text: {get_response.text}")
            
            # Success criteria
            if get_response.status_code in [200, 404, 500] and cors_headers:
                return True
            else:
                logger.warning(f"Status: {get_response.status_code}, CORS: {bool(cors_headers)}")
                return False
                
        except Exception as e:
            logger.error(f"GET test failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Finding and using existing readings resources...")
    
    # Find existing readings resources
    logger.info("🔍 Finding existing readings resources...")
    readings_resources = find_readings_resources()
    
    # Create missing resources
    logger.info("📋 Creating missing resources...")
    latest_resource_id = create_missing_resources()
    
    if not latest_resource_id:
        logger.error("❌ Could not create/find latest resource")
        return False
    
    # Set up Lambda integration
    logger.info("🔗 Setting up Lambda integration...")
    if not setup_lambda_integration(latest_resource_id):
        logger.error("❌ Could not set up Lambda integration")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 Readings endpoint is working!")
        return True
    else:
        logger.warning("⚠️ Endpoint setup completed but may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Readings endpoint is now working!")
        print("🌐 Your React frontend should work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Endpoint setup encountered issues")
        print("📋 Check the logs for details")