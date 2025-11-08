"""
Email Verification Lambda Function
Handles email verification status checks and resend verification codes
"""

import json
import boto3
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')


def lambda_handler(event, context):
    """
    Main Lambda handler for email verification operations
    """
    try:
        # Parse request
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
        
        # Handle OPTIONS for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Route to appropriate handler
        if 'verification-status' in path and http_method == 'GET':
            return handle_verification_status(event, headers)
        elif 'resend-verification' in path and http_method == 'POST':
            return handle_resend_verification(event, headers)
        elif 'confirm-signup' in path and http_method == 'POST':
            return handle_confirm_signup(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"Error in email verification handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_verification_status(event, headers):
    """
    Check if user's email is verified
    GET /api/auth/verification-status/{email}
    """
    try:
        # Extract email from path parameters
        path_parameters = event.get('pathParameters', {})
        email = path_parameters.get('email')
        
        if not email:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email parameter is required'})
            }
        
        # Get user from Cognito
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=email
            )
            
            # Check if email is verified
            email_verified = False
            for attribute in response.get('UserAttributes', []):
                if attribute['Name'] == 'email_verified':
                    email_verified = attribute['Value'].lower() == 'true'
                    break
            
            user_status = response.get('UserStatus', 'UNKNOWN')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'email': email,
                    'emailVerified': email_verified,
                    'userStatus': user_status,
                    'enabled': response.get('Enabled', False)
                })
            }
            
        except cognito_client.exceptions.UserNotFoundException:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': 'User not found',
                    'emailVerified': False
                })
            }
            
    except Exception as e:
        logger.error(f"Error checking verification status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to check verification status'})
        }


def handle_resend_verification(event, headers):
    """
    Resend verification code to user's email
    POST /api/auth/resend-verification
    Body: { "email": "user@example.com" }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        
        if not email:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # Resend confirmation code
        try:
            cognito_client.resend_confirmation_code(
                ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
                Username=email
            )
            
            logger.info(f"Verification code resent to {email}")
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Verification code sent successfully',
                    'email': email
                })
            }
            
        except cognito_client.exceptions.UserNotFoundException:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'User not found'})
            }
        except cognito_client.exceptions.InvalidParameterException as e:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': str(e)})
            }
        except cognito_client.exceptions.LimitExceededException:
            return {
                'statusCode': 429,
                'headers': headers,
                'body': json.dumps({'error': 'Too many requests. Please try again later.'})
            }
            
    except Exception as e:
        logger.error(f"Error resending verification code: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to resend verification code'})
        }


def handle_confirm_signup(event, headers):
    """
    Confirm user signup with verification code
    POST /api/auth/confirm-signup
    Body: { "email": "user@example.com", "code": "123456" }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        code = body.get('code')
        
        if not email or not code:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Email and verification code are required'})
            }
        
        # Confirm signup
        try:
            cognito_client.confirm_sign_up(
                ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
                Username=email,
                ConfirmationCode=code
            )
            
            logger.info(f"User {email} confirmed successfully")
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Email verified successfully',
                    'email': email,
                    'verified': True
                })
            }
            
        except cognito_client.exceptions.CodeMismatchException:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid verification code'})
            }
        except cognito_client.exceptions.ExpiredCodeException:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Verification code has expired',
                    'canResend': True
                })
            }
        except cognito_client.exceptions.UserNotFoundException:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'User not found'})
            }
        except cognito_client.exceptions.NotAuthorizedException:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'User is already confirmed'})
            }
            
    except Exception as e:
        logger.error(f"Error confirming signup: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Failed to confirm signup'})
        }
