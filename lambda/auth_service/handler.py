"""
Authentication and authorization service for AquaChain system.
Implements JWT token validation and role-based access control.
Requirements: 8.2, 8.3
"""

import json
import jwt
import requests
import time
import logging
import sys
import os
from typing import Dict, List, Optional, Any
from functools import wraps
import boto3
from botocore.exceptions import ClientError

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import error handling
from errors import AuthenticationError, AuthorizationError, ValidationError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Import audit logging
from audit_logger import audit_logger

# Configure structured logging
logger = get_logger(__name__, service='auth-service')

class TokenManager:
    """
    JWT token validation and management service.
    Implements requirement 8.2 for secure token validation.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'ap-south-1'):
        self.user_pool_id = user_pool_id
        self.region = region
        self.issuer = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'
        self.jwks_url = f'{self.issuer}/.well-known/jwks.json'
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self._jwks_cache = None
        self._jwks_cache_time = 0
        self._cache_ttl = 3600  # 1 hour cache
    
    def _get_jwks(self) -> Dict:
        """
        Get JSON Web Key Set from Cognito with caching.
        """
        current_time = time.time()
        
        # Return cached JWKS if still valid
        if (self._jwks_cache and 
            current_time - self._jwks_cache_time < self._cache_ttl):
            return self._jwks_cache
        
        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            
            self._jwks_cache = response.json()
            self._jwks_cache_time = current_time
            
            return self._jwks_cache
            
        except requests.RequestException as e:
            logger.error(f"Error fetching JWKS: {e}")
            if self._jwks_cache:
                # Return stale cache if available
                return self._jwks_cache
            raise AuthenticationError(f"Unable to fetch JWKS: {e}")
    
    def _get_public_key(self, token_header: Dict) -> str:
        """
        Get the public key for token verification.
        """
        jwks = self._get_jwks()
        
        # Find the key with matching kid
        kid = token_header.get('kid')
        if not kid:
            raise AuthenticationError("Token header missing 'kid'")
        
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        
        raise AuthenticationError(f"Unable to find key with kid: {kid}")
    
    def validate_token(self, token: str, required_scopes: Optional[List[str]] = None) -> Dict:
        """
        Validate JWT token and return decoded claims.
        Implements requirement 8.2 for token validation with Cognito public key verification.
        """
        try:
            # Decode header without verification to get key ID
            unverified_header = jwt.get_unverified_header(token)
            
            # Get public key for verification
            public_key = self._get_public_key(unverified_header)
            
            # Verify and decode token
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                issuer=self.issuer,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_iss': True,
                    'verify_aud': False  # Cognito doesn't always include aud
                }
            )
            
            # Validate token use
            if decoded_token.get('token_use') not in ['access', 'id']:
                raise AuthenticationError("Invalid token use")
            
            # Validate required scopes if specified
            if required_scopes:
                token_scopes = decoded_token.get('scope', '').split()
                missing_scopes = set(required_scopes) - set(token_scopes)
                if missing_scopes:
                    raise AuthorizationError(
                        f"Missing required scopes: {missing_scopes}"
                    )
            
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except AuthenticationError:
            raise
        except AuthorizationError:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise AuthenticationError(f"Token validation failed: {e}")
    
    def refresh_token(self, refresh_token: str, client_id: str) -> Dict:
        """
        Refresh access token using refresh token.
        Implements session management with token refresh logic.
        """
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response.get('AuthenticationResult', {})
            
            return {
                'accessToken': auth_result.get('AccessToken'),
                'idToken': auth_result.get('IdToken'),
                'tokenType': auth_result.get('TokenType', 'Bearer'),
                'expiresIn': auth_result.get('ExpiresIn', 3600)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("Invalid refresh token")
            else:
                logger.error(f"Token refresh error: {e}")
                raise AuthenticationError(f"Token refresh failed: {error_code}")

class AuthorizationManager:
    """
    Role-based access control and permission management.
    Implements requirement 8.3 for role-based permission checking.
    """
    
    # Define role hierarchy and permissions
    ROLE_PERMISSIONS = {
        'administrators': {
            'users': ['create', 'read', 'update', 'delete'],
            'devices': ['create', 'read', 'update', 'delete'],
            'readings': ['read'],
            'service_requests': ['read', 'update'],
            'system': ['read', 'update'],
            'audit': ['read']
        },
        'technicians': {
            'users': ['read_own'],
            'devices': ['read_assigned'],
            'readings': ['read_assigned'],
            'service_requests': ['read_assigned', 'update_assigned'],
            'system': [],
            'audit': []
        },
        'consumers': {
            'users': ['read_own', 'update_own'],
            'devices': ['read_own'],
            'readings': ['read_own'],
            'service_requests': ['create_own', 'read_own'],
            'system': [],
            'audit': []
        }
    }
    
    def __init__(self):
        pass
    
    def check_permission(self, user_role: str, resource: str, action: str, 
                        user_id: str = None, resource_owner: str = None,
                        assigned_technician: str = None) -> bool:
        """
        Check if user has permission to perform action on resource.
        """
        if user_role not in self.ROLE_PERMISSIONS:
            return False
        
        role_perms = self.ROLE_PERMISSIONS[user_role]
        resource_perms = role_perms.get(resource, [])
        
        # Check direct permission
        if action in resource_perms:
            return True
        
        # Check ownership-based permissions
        if user_id and resource_owner:
            if f"{action}_own" in resource_perms and user_id == resource_owner:
                return True
        
        # Check assignment-based permissions (for technicians)
        if user_role == 'technicians' and assigned_technician:
            if f"{action}_assigned" in resource_perms and user_id == assigned_technician:
                return True
        
        return False
    
    def get_user_permissions(self, user_role: str) -> Dict[str, List[str]]:
        """
        Get all permissions for a user role.
        """
        return self.ROLE_PERMISSIONS.get(user_role, {})
    
    def can_access_device(self, user_role: str, user_id: str, device_id: str,
                         user_devices: List[str] = None) -> bool:
        """
        Check if user can access specific device data.
        """
        if user_role == 'administrators':
            return True
        
        if user_role == 'consumers' and user_devices:
            return device_id in user_devices
        
        # For technicians, check if they have active service requests for the device
        # This would require additional database lookup in real implementation
        return False

def create_auth_middleware(token_manager: TokenManager, auth_manager: AuthorizationManager):
    """
    Create authentication and authorization middleware decorator.
    """
    def auth_required(required_scopes: Optional[List[str]] = None,
                     resource: str = None, action: str = None):
        def decorator(func):
            @wraps(func)
            def wrapper(event, context):
                try:
                    # Extract token from Authorization header
                    auth_header = event.get('headers', {}).get('Authorization', '')
                    if not auth_header.startswith('Bearer '):
                        raise AuthenticationError('Missing or invalid Authorization header')
                    
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    
                    # Validate token
                    decoded_token = token_manager.validate_token(token, required_scopes)
                    
                    # Extract user information
                    user_id = decoded_token.get('sub')
                    user_role = decoded_token.get('cognito:groups', ['consumers'])[0]
                    
                    # Check permissions if resource and action specified
                    if resource and action:
                        # Extract resource owner from path parameters or request body
                        resource_owner = event.get('pathParameters', {}).get('userId')
                        
                        if not auth_manager.check_permission(
                            user_role, resource, action, user_id, resource_owner
                        ):
                            raise AuthorizationError('Insufficient permissions')
                    
                    # Add user context to event
                    event['userContext'] = {
                        'userId': user_id,
                        'role': user_role,
                        'email': decoded_token.get('email'),
                        'deviceIds': decoded_token.get('custom:deviceIds', '').split(',') if decoded_token.get('custom:deviceIds') else []
                    }
                    
                    # Call the original function
                    return func(event, context)
                    
                except (AuthenticationError, AuthorizationError):
                    raise
                except Exception as e:
                    logger.error(f"Auth middleware error: {e}")
                    raise
            
            return wrapper
        return decorator
    return auth_required

# Lambda handler for authentication service
@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for authentication operations.
    """
    # Get configuration from environment variables
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
    client_id = os.environ.get('COGNITO_CLIENT_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id or not client_id:
        raise ValidationError('Missing Cognito configuration')
    
    token_manager = TokenManager(user_pool_id, region)
    auth_manager = AuthorizationManager()
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    if http_method == 'POST' and path.endswith('/validate'):
        # Token validation endpoint
        body = json.loads(event.get('body', '{}'))
        token = body.get('token')
        
        if not token:
            raise ValidationError('Token is required')
        
        decoded_token = token_manager.validate_token(token)
        user_id = decoded_token.get('sub')
        
        # Log authentication event
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'api'
        }
        
        audit_logger.log_authentication_event(
            event_type='TOKEN_VALIDATION',
            user_id=user_id,
            success=True,
            request_context=request_context,
            details={'token_type': decoded_token.get('token_use')}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'valid': True,
                'userId': user_id,
                'role': decoded_token.get('cognito:groups', ['consumers'])[0],
                'email': decoded_token.get('email')
            })
        }
    
    elif http_method == 'POST' and path.endswith('/refresh'):
        # Token refresh endpoint
        body = json.loads(event.get('body', '{}'))
        refresh_token = body.get('refreshToken')
        
        if not refresh_token:
            raise ValidationError('Refresh token is required')
        
        new_tokens = token_manager.refresh_token(refresh_token, client_id)
        
        # Extract user ID from new token for audit logging
        try:
            decoded = jwt.decode(new_tokens['idToken'], options={"verify_signature": False})
            user_id = decoded.get('sub', 'unknown')
        except:
            user_id = 'unknown'
        
        # Log authentication event
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'api'
        }
        
        audit_logger.log_authentication_event(
            event_type='TOKEN_REFRESH',
            user_id=user_id,
            success=True,
            request_context=request_context
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(new_tokens)
        }
    
    elif http_method == 'POST' and '/google/callback' in path:
        # Google OAuth callback endpoint - delegate to google_oauth_handler
        from google_oauth_handler import lambda_handler as google_oauth_handler
        return google_oauth_handler(event, context)
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')

# Export the middleware for use in other Lambda functions
import os
if os.environ.get('COGNITO_USER_POOL_ID'):
    token_manager = TokenManager(
        os.environ['COGNITO_USER_POOL_ID'],
        os.environ.get('AWS_REGION', 'us-east-1')
    )
    auth_manager = AuthorizationManager()
    auth_required = create_auth_middleware(token_manager, auth_manager)
else:
    # Fallback for testing or when config not available
    def auth_required(*args, **kwargs):
        def decorator(func):
            return func
        return decorator