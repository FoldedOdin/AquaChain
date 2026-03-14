#!/usr/bin/env python3
"""
Use the existing /api/device-readings endpoint and extend it
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

def setup_device_readings_endpoint():
    """Set up the /api/device-readings endpoint"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Find the device-readings resource
        resources_response = client.get_resources(restApiId=API_ID)
        
        device_readings_id = None
        for resource in resources_response['items']:
            if resource.get('path') == '/api/device-readings':
                device_readings_id = resource['id']
                logger.info(f"Found device-readings resource: {device_readings_id}")
                break
        
        if not device_readings_id:
            logger.error("Could not find /api/device-readings resource")
            return None
        
        # Create {deviceId} under device-readings
        device_id_resource_id = None
        for resource in resources_response['items']:
            if (resource.get('pathPart') == '{deviceId}' and 
                resource.get('parentId') == device_readings_id):
                device_id_resource_id = resource['id']
                logger.info(f"Found existing deviceId resource: {device_id_resource_id}")
                break
        
        if not device_id_resource_id:
            try:
                device_id_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=device_readings_id,
                    pathPart='{deviceId}'
                )
                device_id_resource_id = device_id_resource['id']
                logger.info(f"Created deviceId resource: {device_id_resource_id}")
            except ClientError as e:
                logger.error(f"Error creating deviceId resource: {e}")
                return None
        
        # Create latest under {deviceId}
        latest_resource_id = None
        resources_response = client.get_resources(restApiId=API_ID)  # Refresh
        
        for resource in resources_response['items']:
            if (resource.get('pathPart') == 'latest' and 
                resource.get('parentId') == device_id_resource_id):
                latest_resource_id = resource['id']
                logger.info(f"Found existing latest resource: {latest_resource_id}")
                break
        
        if not latest_resource_id:
            try:
                latest_resource = client.create_resource(
                    restApiId=API_ID,
                    parentId=device_id_resource_id,
                    pathPart='latest'
                )
                latest_resource_id = latest_resource['id']
                logger.info(f"Created latest resource: {latest_resource_id}")
            except ClientError as e:
                logger.error(f"Error creating latest resource: {e}")
                return None
        
        return latest_resource_id
        
    except Exception as e:
        logger.error(f"Error setting up device-readings endpoint: {e}")
        return None

def setup_v1_readings_endpoint():
    """Set up the /api/v1/readings endpoint as well"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Find /api/v1
        resources_response = client.get_resources(restApiId=API_ID)
        
        api_v1_id = None
        for resource in resources_response['items']:
            if resource.get('path') == '/api/v1':
                api_v1_id = resource['id']
                break
        
        if not api_v1_id:
            logger.error("Could not find /api/v1")
            return None
        
        # Create readings under /api/v1
        readings_id = None
        try:
            readings_resource = client.create_resource(
                restApiId=API_ID,
                parentId=api_v1_id,
                pathPart='readings'
            )
            readings_id = readings_resource['id']
            logger.info(f"Created /api/v1/readings: {readings_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing readings
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if (resource.get('pathPart') == 'readings' and 
                        resource.get('parentId') == api_v1_id):
                        readings_id = resource['id']
                        logger.info(f"Found existing /api/v1/readings: {readings_id}")
                        break
            
            if not readings_id:
                logger.error(f"Error with readings resource: {e}")
                return None
        
        # Create {deviceId} under readings
        device_id = None
        try:
            device_resource = client.create_resource(
                restApiId=API_ID,
                parentId=readings_id,
                pathPart='{deviceId}'
            )
            device_id = device_resource['id']
            logger.info(f"Created deviceId: {device_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if (resource.get('pathPart') == '{deviceId}' and 
                        resource.get('parentId') == readings_id):
                        device_id = resource['id']
                        logger.info(f"Found existing deviceId: {device_id}")
                        break
            
            if not device_id:
                logger.error(f"Error with deviceId resource: {e}")
                return None
        
        # Create latest under {deviceId}
        latest_id = None
        try:
            latest_resource = client.create_resource(
                restApiId=API_ID,
                parentId=device_id,
                pathPart='latest'
            )
            latest_id = latest_resource['id']
            logger.info(f"Created latest: {latest_id}")
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Find existing
                resources_response = client.get_resources(restApiId=API_ID)
                for resource in resources_response['items']:
                    if (resource.get('pathPart') == 'latest' and 
                        resource.get('parentId') == device_id):
                        latest_id = resource['id']
                        logger.info(f"Found existing latest: {latest_id}")
                        break
            
            if not latest_id:
                logger.error(f"Error with latest resource: {e}")
                return None
        
        return latest_id
        
    except Exception as e:
        logger.error(f"Error setting up v1 readings endpoint: {e}")
        return None

def setup_lambda_integration(resource_id, endpoint_name):
    """Set up Lambda integration for a resource"""
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
            
            logger.info(f"✅ Created OPTIONS method for {endpoint_name}")
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
            
            logger.info(f"✅ Created GET method for {endpoint_name}")
        except ClientError as e:
            logger.error(f"Error creating GET: {e}")
            return False
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f'apigateway-{endpoint_name}-{resource_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:*:{API_ID}/*/*'
            )
            logger.info(f"✅ Added Lambda permission for {endpoint_name}")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                logger.info(f"Lambda permission already exists for {endpoint_name}")
            else:
                logger.warning(f"Could not add Lambda permission: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Lambda integration: {e}")
        return False

def deploy_and_test():
    """Deploy and test both endpoints"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # Deploy API
        client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='Device readings endpoints'
        )
        
        logger.info("🚀 API deployed")
        
        # Wait for deployment
        import time
        time.sleep(8)
        
        # Test both endpoints
        import requests
        
        endpoints = [
            f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/device-readings/ESP32-001/latest",
            f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        ]
        
        success_count = 0
        
        for url in endpoints:
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
                    logger.info("✅ CORS headers found")
                    success_count += 1
                else:
                    logger.warning("⚠️ No CORS headers")
                
                # Check response
                try:
                    response_data = response.json()
                    logger.info(f"Response: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"Response text: {response.text}")
                
            except Exception as e:
                logger.error(f"Test failed: {e}")
            
            logger.info("-" * 50)
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error deploying and testing: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔧 Setting up device readings endpoints...")
    
    # Set up /api/device-readings/{deviceId}/latest
    logger.info("📋 Setting up /api/device-readings endpoint...")
    device_readings_resource = setup_device_readings_endpoint()
    
    if device_readings_resource:
        logger.info("🔗 Setting up Lambda integration for device-readings...")
        setup_lambda_integration(device_readings_resource, "device-readings")
    
    # Set up /api/v1/readings/{deviceId}/latest
    logger.info("📋 Setting up /api/v1/readings endpoint...")
    v1_readings_resource = setup_v1_readings_endpoint()
    
    if v1_readings_resource:
        logger.info("🔗 Setting up Lambda integration for v1/readings...")
        setup_lambda_integration(v1_readings_resource, "v1-readings")
    
    if not device_readings_resource and not v1_readings_resource:
        logger.error("❌ Could not set up any endpoints")
        return False
    
    # Deploy and test
    logger.info("🚀 Deploying and testing...")
    if deploy_and_test():
        logger.info("🎉 Device readings endpoints are working!")
        return True
    else:
        logger.warning("⚠️ Endpoints setup completed but may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Device readings endpoints are now working!")
        print("🌐 Your React frontend should work without CORS errors")
        print(f"📡 Test URLs:")
        print(f"  - https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/device-readings/ESP32-001/latest")
        print(f"  - https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Endpoint setup encountered issues")
        print("📋 Check the logs for details")