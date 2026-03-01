"""
Get user verification status from Cognito
Simple endpoint to check if a user's email is verified
"""

import json
import boto3
import os
from botocore.exceptions import ClientError

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Content-Type': 'application/json'
}

def lambda_handler(event, context):
    """Check user verification status"""
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Get email from path parameters
        email = event.get('pathParameters', {}).get('email')
        
        if not email:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Email parameter required'})
            }
        
        # Get Cognito configuration
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        if not user_pool_id:
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Cognito not configured'})
            }
        
        # Check user in Cognito
        cognito = boto3.client('cognito-idp', region_name=os.environ.get('REGION', 'ap-south-1'))
        
        try:
            response = cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            
            # Check if email is verified
            email_verified = False
            for attr in response.get('UserAttributes', []):
                if attr['Name'] == 'email_verified':
                    email_verified = attr['Value'].lower() == 'true'
                    break
            
            user_status = response.get('UserStatus', 'UNKNOWN')
            
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'email': email,
                    'verified': email_verified,
                    'status': user_status,
                    'exists': True
                })
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'UserNotFoundException':
                # User doesn't exist - not verified
                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'email': email,
                        'verified': False,
                        'status': 'NOT_FOUND',
                        'exists': False
                    })
                }
            else:
                raise
        
    except Exception as e:
        print(f"Error checking verification status: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }
