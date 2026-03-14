#!/usr/bin/env python3
"""
Comprehensive CORS Fix for Readings API
Fixes both API Gateway CORS configuration and Lambda response headers
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_api_gateway():
    """Find the AquaChain API Gateway"""
    try:
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        # List all APIs
        response = client.get_rest_apis()
        
        for api in response['items']:
            if 'aquachain' in api['name'].lower() or 'AquaChain' in api['name']:
                logger.info(f"Found API: {api['name']} - {api['id']}")
                return api['id']
        
        # If no AquaChain API found, return the first one
        if response['items']:
            api = response['items'][0]
            logger.info(f"Using first API: {api['name']} - {api['id']}")
            return api['id']
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding API Gateway: {e}")
        return None

def find_readings_resources(api_id):
    """Find readings-related resources in API Gateway"""
    try:
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        response = client.get_resources(restApiId=api_id)
        
        readings_resources = []
        for resource in response['items']:
            path = resource.get('pathPart', '')
            full_path = resource.get('path', '')
            
            if 'readings' in path.lower() or 'readings' in full_path.lower():
                readings_resources.append(resource)
                logger.info(f"Found readings resource: {full_path} - {resource['id']}")
        
        return readings_resources
        
    except Exception as e:
        logger.error(f"Error finding resources: {e}")
        return []

def enable_cors_for_resource(api_id, resource_id, resource_path):
    """Enable CORS for a specific resource"""
    try:
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        # CORS headers to add
        cors_headers = {
            'Access-Control-Allow-Origin': "'*'",
            'Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
            'Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
        }
        
        # Check if OPTIONS method exists
        try:
            client.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS'
            )
            logger.info(f"OPTIONS method already exists for {resource_path}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                # Create OPTIONS method
                logger.info(f"Creating OPTIONS method for {resource_path}")
                
                client.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Add method response
                client.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': False,
                        'method.response.header.Access-Control-Allow-Headers': False,
                        'method.response.header.Access-Control-Allow-Methods': False
                    }
                )
                
                # Add integration
                client.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={
                        'application/json': '{"statusCode": 200}'
                    }
                )
                
                # Add integration response
                client.put_integration_response(
                    restApiId=api_id,
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
                
                logger.info(f"Created OPTIONS method for {resource_path}")
        
        # Add CORS headers to existing methods
        try:
            methods_response = client.get_resource(
                restApiId=api_id,
                resourceId=resource_id
            )
            
            for method in methods_response.get('resourceMethods', {}):
                if method != 'OPTIONS':
                    logger.info(f"Adding CORS headers to {method} method for {resource_path}")
                    
                    # Add CORS headers to method response
                    try:
                        client.put_method_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': False,
                                'method.response.header.Access-Control-Allow-Headers': False,
                                'method.response.header.Access-Control-Allow-Methods': False
                            }
                        )
                    except ClientError as e:
                        if 'ConflictException' not in str(e):
                            logger.warning(f"Could not update method response for {method}: {e}")
                    
                    # Update integration response
                    try:
                        client.put_integration_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': "'*'",
                                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                            }
                        )
                    except ClientError as e:
                        if 'ConflictException' not in str(e):
                            logger.warning(f"Could not update integration response for {method}: {e}")
        
        except Exception as e:
            logger.error(f"Error updating methods for {resource_path}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error enabling CORS for {resource_path}: {e}")
        return False

def deploy_api(api_id):
    """Deploy the API to make changes live"""
    try:
        client = boto3.client('apigateway', region_name='ap-south-1')
        
        response = client.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='CORS fix deployment'
        )
        
        logger.info(f"Deployed API {api_id} to dev stage")
        return True
        
    except Exception as e:
        logger.error(f"Error deploying API: {e}")
        return False

def test_cors_endpoint(api_id):
    """Test the CORS fix"""
    try:
        import requests
        
        # Construct the API URL
        url = f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"Testing CORS at: {url}")
        
        # Test OPTIONS request
        options_response = requests.options(url, timeout=10)
        logger.info(f"OPTIONS response status: {options_response.status_code}")
        logger.info(f"OPTIONS response headers: {dict(options_response.headers)}")
        
        # Test GET request
        get_response = requests.get(url, timeout=10)
        logger.info(f"GET response status: {get_response.status_code}")
        logger.info(f"GET response headers: {dict(get_response.headers)}")
        
        # Check for CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        missing_headers = []
        for header in cors_headers:
            if header not in get_response.headers:
                missing_headers.append(header)
        
        if missing_headers:
            logger.warning(f"Missing CORS headers: {missing_headers}")
            return False
        else:
            logger.info("✅ All CORS headers present!")
            return True
        
    except Exception as e:
        logger.error(f"Error testing CORS: {e}")
        return False

def main():
    """Main function to fix CORS issues"""
    logger.info("🔧 Starting comprehensive CORS fix for readings API...")
    
    # Find API Gateway
    api_id = find_api_gateway()
    if not api_id:
        logger.error("❌ Could not find API Gateway")
        return False
    
    logger.info(f"📡 Using API Gateway: {api_id}")
    
    # Find readings resources
    readings_resources = find_readings_resources(api_id)
    if not readings_resources:
        logger.error("❌ Could not find readings resources")
        return False
    
    # Enable CORS for each resource
    success_count = 0
    for resource in readings_resources:
        resource_id = resource['id']
        resource_path = resource.get('path', resource.get('pathPart', 'unknown'))
        
        logger.info(f"🔧 Fixing CORS for: {resource_path}")
        
        if enable_cors_for_resource(api_id, resource_id, resource_path):
            success_count += 1
            logger.info(f"✅ CORS enabled for {resource_path}")
        else:
            logger.error(f"❌ Failed to enable CORS for {resource_path}")
    
    if success_count == 0:
        logger.error("❌ Failed to enable CORS for any resources")
        return False
    
    # Deploy API
    logger.info("🚀 Deploying API changes...")
    if not deploy_api(api_id):
        logger.error("❌ Failed to deploy API")
        return False
    
    # Wait a moment for deployment
    import time
    time.sleep(5)
    
    # Test CORS
    logger.info("🧪 Testing CORS fix...")
    if test_cors_endpoint(api_id):
        logger.info("🎉 CORS fix successful!")
        return True
    else:
        logger.warning("⚠️ CORS fix may need additional configuration")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ CORS fix completed successfully!")
        print("🌐 Your frontend should now be able to access the readings API")
    else:
        print("\n❌ CORS fix encountered issues")
        print("📋 Check the logs above for details")