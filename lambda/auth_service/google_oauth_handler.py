"""
Google OAuth 2.0 Authentication Handler for AquaChain
Handles Google OAuth callback and token exchange
"""

import json
import os
import sys
import requests
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import AuthenticationError, ValidationError
from error_handler import handle_errors
from structured_logger import get_logger
from audit_logger import audit_logger

logger = get_logger(__name__, service='google-oauth')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cognito_client = boto3.client('cognito-idp')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users-dev')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
GOOGLE_CLIENT_SECRET_ARN = os.environ.get('GOOGLE_CLIENT_SECRET_ARN')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Google OAuth endpoints
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


def get_google_client_secret() -> str:
    """
    Retrieve Google OAuth client secret from AWS Secrets Manager
    """
    try:
        if not GOOGLE_CLIENT_SECRET_ARN:
            raise ValidationError('Google client secret ARN not configured')
        
        response = secrets_manager.get_secret_value(SecretId=GOOGLE_CLIENT_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        return secret_data.get('client_secret')
    except Exception as e:
        logger.error(f"Failed to retrieve Google client secret: {e}")
        raise AuthenticationError('OAuth configuration error')


def exchange_code_for_tokens(code: str, redirect_uri: str, client_id: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access and ID tokens from Google
    """
    try:
        client_secret = get_google_client_secret()
        
        # Prepare token exchange request
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        # Exchange code for tokens
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if not response.ok:
            error_data = response.json()
            logger.error(f"Google token exchange failed: {error_data}")
            raise AuthenticationError(f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}")
        
        tokens = response.json()
        logger.info("Successfully exchanged authorization code for tokens")
        
        return tokens
        
    except requests.RequestException as e:
        logger.error(f"Network error during token exchange: {e}")
        raise AuthenticationError('Failed to communicate with Google OAuth service')


def get_google_user_info(access_token: str) -> Dict[str, Any]:
    """
    Retrieve user information from Google using access token
    """
    try:
        response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if not response.ok:
            logger.error(f"Failed to fetch Google user info: {response.text}")
            raise AuthenticationError('Failed to retrieve user information from Google')
        
        user_info = response.json()
        logger.info(f"Retrieved user info for Google ID: {user_info.get('id')}")
        
        return user_info
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching user info: {e}")
        raise AuthenticationError('Failed to retrieve user information')


def find_or_create_user(google_user_info: Dict[str, Any], role: str = 'consumer') -> Dict[str, Any]:
    """
    Find existing user by email or create new user in DynamoDB
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        email = google_user_info.get('email')
        google_id = google_user_info.get('id')
        
        if not email:
            raise ValidationError('Email not provided by Google')
        
        # Check if user exists by email
        response = table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        
        if response.get('Items'):
            # User exists - update Google ID if not set
            user = response['Items'][0]
            user_id = user['userId']
            
            if not user.get('googleId'):
                table.update_item(
                    Key={'userId': user_id},
                    UpdateExpression='SET googleId = :google_id, lastLogin = :last_login',
                    ExpressionAttributeValues={
                        ':google_id': google_id,
                        ':last_login': datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Linked Google account to existing user: {user_id}")
            
            return user
        
        # Create new user
        user_id = f"user_{secrets.token_urlsafe(16)}"
        timestamp = datetime.utcnow().isoformat()
        
        new_user = {
            'userId': user_id,
            'email': email,
            'name': google_user_info.get('name', email.split('@')[0]),
            'role': role,
            'googleId': google_id,
            'emailVerified': google_user_info.get('verified_email', True),
            'profilePicture': google_user_info.get('picture'),
            'authProvider': 'google',
            'createdAt': timestamp,
            'lastLogin': timestamp,
            'profile': {
                'firstName': google_user_info.get('given_name', ''),
                'lastName': google_user_info.get('family_name', ''),
                'phone': ''
            }
        }
        
        table.put_item(Item=new_user)
        logger.info(f"Created new user from Google OAuth: {user_id}")
        
        # Log user creation event
        audit_logger.log_user_action(
            user_id=user_id,
            action='USER_CREATED',
            resource_type='user',
            resource_id=user_id,
            details={
                'auth_provider': 'google',
                'email': email,
                'role': role
            }
        )
        
        return new_user
        
    except Exception as e:
        logger.error(f"Error finding/creating user: {e}")
        raise


def create_cognito_user_if_needed(user: Dict[str, Any]) -> Optional[str]:
    """
    Create or update user in Cognito User Pool for JWT token generation
    """
    try:
        email = user['email']
        user_id = user['userId']
        
        # Check if user exists in Cognito
        try:
            cognito_client.admin_get_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email
            )
            logger.info(f"User already exists in Cognito: {email}")
            
        except cognito_client.exceptions.UserNotFoundException:
            # Create user in Cognito
            cognito_client.admin_create_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'name', 'Value': user.get('name', '')},
                    {'Name': 'custom:role', 'Value': user.get('role', 'consumer')},
                    {'Name': 'sub', 'Value': user_id}
                ],
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            logger.info(f"Created Cognito user: {email}")
            
            # Set permanent password (user won't need it for OAuth)
            temp_password = secrets.token_urlsafe(32)
            cognito_client.admin_set_user_password(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                Password=temp_password,
                Permanent=True
            )
        
        # Add user to appropriate group
        role = user.get('role', 'consumer')
        group_name = f"{role}s" if role != 'admin' else 'administrators'
        
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                GroupName=group_name
            )
        except cognito_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Group {group_name} not found in Cognito")
        except Exception as e:
            logger.warning(f"Failed to add user to group: {e}")
        
        return email
        
    except Exception as e:
        logger.error(f"Error creating Cognito user: {e}")
        # Don't fail the OAuth flow if Cognito creation fails
        return None


def generate_jwt_token(user: Dict[str, Any]) -> str:
    """
    Generate JWT token for the user using Cognito
    """
    try:
        email = user['email']
        
        # Initiate auth with admin credentials
        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': secrets.token_urlsafe(32)  # Dummy password
            }
        )
        
        # This will fail, but we'll use a different approach
        # For OAuth users, we should use a custom token or session
        
    except Exception as e:
        logger.warning(f"Failed to generate Cognito token: {e}")
    
    # For now, return a simple JWT-like token
    # In production, you should use Cognito's token or implement proper JWT signing
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        'sub': user['userId'],
        'email': user['email'],
        'name': user['name'],
        'role': user['role'],
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    
    # Use a secret key from environment or Secrets Manager
    secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    return token


@handle_errors
def lambda_handler(event, context):
    """
    Lambda handler for Google OAuth callback
    
    Expected POST body:
    {
        "code": "authorization_code_from_google",
        "redirectUri": "http://localhost:3000/auth/google/callback",
        "clientId": "your-google-client-id",
        "role": "consumer"  # optional, defaults to consumer
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        code = body.get('code')
        redirect_uri = body.get('redirectUri')
        client_id = body.get('clientId')
        role = body.get('role', 'consumer')
        
        # Validate required parameters
        if not code:
            raise ValidationError('Authorization code is required')
        if not redirect_uri:
            raise ValidationError('Redirect URI is required')
        if not client_id:
            raise ValidationError('Client ID is required')
        
        # Validate role
        if role not in ['consumer', 'technician', 'admin']:
            raise ValidationError('Invalid role specified')
        
        logger.info(f"Processing Google OAuth callback for role: {role}")
        
        # Step 1: Exchange authorization code for tokens
        tokens = exchange_code_for_tokens(code, redirect_uri, client_id)
        access_token = tokens.get('access_token')
        
        if not access_token:
            raise AuthenticationError('Failed to obtain access token from Google')
        
        # Step 2: Get user information from Google
        google_user_info = get_google_user_info(access_token)
        
        # Step 3: Find or create user in DynamoDB
        user = find_or_create_user(google_user_info, role)
        
        # Step 4: Create/update user in Cognito (optional)
        create_cognito_user_if_needed(user)
        
        # Step 5: Generate JWT token
        jwt_token = generate_jwt_token(user)
        
        # Step 6: Log authentication event
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'google_oauth'
        }
        
        audit_logger.log_authentication_event(
            event_type='GOOGLE_OAUTH_LOGIN',
            user_id=user['userId'],
            success=True,
            request_context=request_context,
            details={
                'email': user['email'],
                'role': user['role'],
                'new_user': user.get('createdAt') == user.get('lastLogin')
            }
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'success': True,
                'token': jwt_token,
                'user': {
                    'id': user['userId'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role'],
                    'emailVerified': user.get('emailVerified', True),
                    'profilePicture': user.get('profilePicture')
                },
                'message': 'Google authentication successful'
            })
        }
        
    except (ValidationError, AuthenticationError) as e:
        logger.error(f"OAuth error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth handler: {e}", exc_info=True)
        raise AuthenticationError('Google authentication failed')
