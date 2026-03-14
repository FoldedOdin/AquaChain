#!/usr/bin/env python3
"""
Fix API Gateway CORS for DEFAULT_4XX and DEFAULT_5XX responses
This is the critical fix for CORS issues when API Gateway returns errors
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = "vtqjfznspc"  # From the error URL
REGION = "ap-south-1"

def fix_gateway_responses():
    """Fix DEFAULT_4XX and DEFAULT_5XX gateway responses to include CORS headers"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        # CORS headers to add to all error responses
        cors_headers = {
            'Access-Control-Allow-Origin': "'*'",
            'Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
            'Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
        }
        
        # Fix DEFAULT_4XX response
        logger.info("🔧 Fixing DEFAULT_4XX gateway response...")
        try:
            client.put_gateway_response(
                restApiId=API_ID,
                responseType='DEFAULT_4XX',
                responseParameters={
                    'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                    'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': '{"error": "Client Error", "message": $context.error.messageString, "requestId": "$context.requestId"}'
                }
            )
            logger.info("✅ Fixed DEFAULT_4XX response")
        except ClientError as e:
            logger.error(f"❌ Error fixing DEFAULT_4XX: {e}")
            return False
        
        # Fix DEFAULT_5XX response
        logger.info("🔧 Fixing DEFAULT_5XX gateway response...")
        try:
            client.put_gateway_response(
                restApiId=API_ID,
                responseType='DEFAULT_5XX',
                responseParameters={
                    'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                    'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': '{"error": "Server Error", "message": $context.error.messageString, "requestId": "$context.requestId"}'
                }
            )
            logger.info("✅ Fixed DEFAULT_5XX response")
        except ClientError as e:
            logger.error(f"❌ Error fixing DEFAULT_5XX: {e}")
            return False
        
        # Also fix BAD_REQUEST_PARAMETERS (common cause of 400 errors)
        logger.info("🔧 Fixing BAD_REQUEST_PARAMETERS gateway response...")
        try:
            client.put_gateway_response(
                restApiId=API_ID,
                responseType='BAD_REQUEST_PARAMETERS',
                responseParameters={
                    'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                    'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': '{"error": "Bad Request Parameters", "message": $context.error.messageString, "requestId": "$context.requestId"}'
                }
            )
            logger.info("✅ Fixed BAD_REQUEST_PARAMETERS response")
        except ClientError as e:
            logger.error(f"❌ Error fixing BAD_REQUEST_PARAMETERS: {e}")
            return False
        
        # Fix MISSING_AUTHENTICATION_TOKEN (401 errors)
        logger.info("🔧 Fixing MISSING_AUTHENTICATION_TOKEN gateway response...")
        try:
            client.put_gateway_response(
                restApiId=API_ID,
                responseType='MISSING_AUTHENTICATION_TOKEN',
                responseParameters={
                    'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                    'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': '{"error": "Missing Authentication Token", "message": "Authentication required", "requestId": "$context.requestId"}'
                }
            )
            logger.info("✅ Fixed MISSING_AUTHENTICATION_TOKEN response")
        except ClientError as e:
            logger.error(f"❌ Error fixing MISSING_AUTHENTICATION_TOKEN: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing gateway responses: {e}")
        return False

def deploy_api():
    """Deploy the API to make changes live"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        response = client.create_deployment(
            restApiId=API_ID,
            stageName='dev',
            description='CORS gateway responses fix'
        )
        
        logger.info(f"🚀 Deployed API {API_ID} to dev stage")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deploying API: {e}")
        return False

def verify_gateway_responses():
    """Verify that gateway responses are properly configured"""
    try:
        client = boto3.client('apigateway', region_name=REGION)
        
        response_types = ['DEFAULT_4XX', 'DEFAULT_5XX', 'BAD_REQUEST_PARAMETERS', 'MISSING_AUTHENTICATION_TOKEN']
        
        logger.info("🔍 Verifying gateway responses...")
        
        for response_type in response_types:
            try:
                response = client.get_gateway_response(
                    restApiId=API_ID,
                    responseType=response_type
                )
                
                headers = response.get('responseParameters', {})
                cors_origin = headers.get('gatewayresponse.header.Access-Control-Allow-Origin')
                
                if cors_origin:
                    logger.info(f"✅ {response_type}: CORS headers configured")
                else:
                    logger.warning(f"⚠️ {response_type}: No CORS headers found")
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'NotFoundException':
                    logger.warning(f"⚠️ {response_type}: Not configured")
                else:
                    logger.error(f"❌ Error checking {response_type}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying gateway responses: {e}")
        return False

def test_cors_fix():
    """Test the CORS fix by making requests"""
    try:
        import requests
        
        url = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        logger.info(f"🧪 Testing CORS fix at: {url}")
        
        # Test OPTIONS request
        logger.info("Testing OPTIONS request...")
        options_response = requests.options(url, timeout=10)
        logger.info(f"OPTIONS Status: {options_response.status_code}")
        
        # Check CORS headers in OPTIONS response
        cors_headers = []
        for header, value in options_response.headers.items():
            if 'access-control' in header.lower():
                cors_headers.append(f"{header}: {value}")
        
        if cors_headers:
            logger.info("✅ OPTIONS CORS headers found:")
            for header in cors_headers:
                logger.info(f"  {header}")
        else:
            logger.warning("⚠️ No CORS headers in OPTIONS response")
        
        # Test GET request
        logger.info("Testing GET request...")
        get_response = requests.get(url, timeout=10)
        logger.info(f"GET Status: {get_response.status_code}")
        
        # Check CORS headers in GET response
        cors_headers = []
        for header, value in get_response.headers.items():
            if 'access-control' in header.lower():
                cors_headers.append(f"{header}: {value}")
        
        if cors_headers:
            logger.info("✅ GET CORS headers found:")
            for header in cors_headers:
                logger.info(f"  {header}")
            return True
        else:
            logger.warning("⚠️ No CORS headers in GET response")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing CORS fix: {e}")
        return False

def main():
    """Main function to fix API Gateway CORS"""
    logger.info("🔧 Starting API Gateway CORS fix...")
    logger.info(f"📡 Target API: {API_ID}")
    
    # Fix gateway responses
    if not fix_gateway_responses():
        logger.error("❌ Failed to fix gateway responses")
        return False
    
    # Deploy API
    logger.info("🚀 Deploying API changes...")
    if not deploy_api():
        logger.error("❌ Failed to deploy API")
        return False
    
    # Wait for deployment
    import time
    logger.info("⏳ Waiting for deployment to complete...")
    time.sleep(10)
    
    # Verify configuration
    logger.info("🔍 Verifying gateway responses...")
    verify_gateway_responses()
    
    # Test CORS fix
    logger.info("🧪 Testing CORS fix...")
    if test_cors_fix():
        logger.info("🎉 CORS fix successful!")
        return True
    else:
        logger.warning("⚠️ CORS fix may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ API Gateway CORS fix completed successfully!")
        print("🌐 Your React frontend should now work without CORS errors")
        print(f"📡 Test URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ CORS fix encountered issues")
        print("📋 Check the logs above for details")
        print("💡 You may need to manually configure Gateway Responses in AWS Console")