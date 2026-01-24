"""
JWT Validation Middleware for AquaChain Dashboard Overhaul.
Implements token validation, session management, and multi-factor authentication.

Requirements: 10.2, 10.3
"""

import json
import jwt
import os
import sys
import time
import boto3
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from functools import wraps
from botocore.exceptions import ClientError
import requests

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import AuthenticationError, AuthorizationError, ValidationError
from error_handler import handle_errors
from structured_logger import get_logger
from audit_logger import audit_logger

# Configure structured logging
logger = get_logger(__name__, service='jwt-middleware')


class JWTValidator:
    """
    JWT token validation service with Cognito integration.
    Implements Requirement 10.2 for strong authentication.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'us-east-1'):
        self.user_pool_id = user_pool_id
        self.region = region
        self.issuer = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'
        self.jwks_url = f'{self.issuer}/.well-known/jwks.json'
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        
        # JWKS cache
        self._jwks_cache = None
        self._jwks_cache_time = 0
        self._cache_ttl = 3600  # 1 hour cache
        
        # Token blacklist for revoked tokens
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.blacklist_table_name = os.environ.get('TOKEN_BLACKLIST_TABLE', 'aquachain-token-blacklist')
        try:
            self.blacklist_table = self.dynamodb.Table(self.blacklist_table_name)
        except Exception as e:
            logger.warning(f"Token blacklist table not available: {e}")
            self.blacklist_table = None
    
    def _get_jwks(self) -> Dict:
        """Get JSON Web Key Set from Cognito with caching."""
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
                logger.warning("Using stale JWKS cache due to fetch failure")
                return self._jwks_cache
            raise AuthenticationError(f"Unable to fetch JWKS: {e}")
    
    def _get_public_key(self, token_header: Dict) -> str:
        """Get the public key for token verification."""
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
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        if not self.blacklist_table:
            return False
        
        try:
            response = self.blacklist_table.get_item(
                Key={'jti': jti}
            )
            return 'Item' in response
        except Exception as e:
            logger.warning(f"Error checking token blacklist: {e}")
            return False
    
    def validate_token(
        self, 
        token: str, 
        required_scopes: Optional[List[str]] = None,
        check_blacklist: bool = True
    ) -> Dict[str, Any]:
        """
        Validate JWT token and return decoded claims.
        
        Args:
            token: JWT token to validate
            required_scopes: Optional list of required scopes
            check_blacklist: Whether to check token blacklist
            
        Returns:
            Decoded token claims
            
        Raises:
            AuthenticationError: If token is invalid
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
            token_use = decoded_token.get('token_use')
            if token_use not in ['access', 'id']:
                raise AuthenticationError("Invalid token use")
            
            # Check if token is blacklisted
            if check_blacklist:
                jti = decoded_token.get('jti')
                if jti and self._is_token_blacklisted(jti):
                    raise AuthenticationError("Token has been revoked")
            
            # Validate required scopes if specified
            if required_scopes:
                token_scopes = decoded_token.get('scope', '').split()
                missing_scopes = set(required_scopes) - set(token_scopes)
                if missing_scopes:
                    raise AuthenticationError(
                        f"Missing required scopes: {missing_scopes}"
                    )
            
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise AuthenticationError(f"Token validation failed: {e}")
    
    def blacklist_token(self, jti: str, expires_at: int, reason: str = "logout") -> None:
        """
        Add token to blacklist.
        
        Args:
            jti: Token JTI (unique identifier)
            expires_at: Token expiration timestamp
            reason: Reason for blacklisting
        """
        if not self.blacklist_table:
            logger.warning("Token blacklist table not available")
            return
        
        try:
            self.blacklist_table.put_item(
                Item={
                    'jti': jti,
                    'blacklisted_at': int(time.time()),
                    'expires_at': expires_at,
                    'reason': reason,
                    'ttl': expires_at + 86400  # Keep for 24 hours after expiration
                }
            )
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            # Don't raise - blacklisting failure shouldn't break logout


class SessionManager:
    """
    Session management with proper timeout and security controls.
    Implements Requirement 10.3 for session management security.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sessions_table_name = os.environ.get('SESSIONS_TABLE', 'aquachain-sessions')
        
        try:
            self.sessions_table = self.dynamodb.Table(self.sessions_table_name)
        except Exception as e:
            logger.warning(f"Sessions table not available: {e}")
            self.sessions_table = None
        
        # Session configuration
        self.session_timeout = int(os.environ.get('SESSION_TIMEOUT_MINUTES', '30')) * 60
        self.max_concurrent_sessions = int(os.environ.get('MAX_CONCURRENT_SESSIONS', '5'))
    
    def create_session(
        self, 
        user_id: str, 
        token_jti: str,
        request_context: Dict[str, Any]
    ) -> str:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            token_jti: JWT token JTI
            request_context: Request context for audit
            
        Returns:
            Session ID
        """
        if not self.sessions_table:
            # If no sessions table, return token JTI as session ID
            return token_jti
        
        session_id = f"sess_{int(time.time())}_{token_jti[:8]}"
        current_time = int(time.time())
        expires_at = current_time + self.session_timeout
        
        try:
            # Clean up expired sessions for this user
            self._cleanup_expired_sessions(user_id)
            
            # Check concurrent session limit
            active_sessions = self._get_active_sessions(user_id)
            if len(active_sessions) >= self.max_concurrent_sessions:
                # Remove oldest session
                oldest_session = min(active_sessions, key=lambda x: x['created_at'])
                self._invalidate_session(oldest_session['session_id'])
            
            # Create new session
            self.sessions_table.put_item(
                Item={
                    'session_id': session_id,
                    'user_id': user_id,
                    'token_jti': token_jti,
                    'created_at': current_time,
                    'last_activity': current_time,
                    'expires_at': expires_at,
                    'ip_address': request_context.get('ip_address', 'unknown'),
                    'user_agent': request_context.get('user_agent', 'unknown'),
                    'status': 'active',
                    'ttl': expires_at + 86400  # Keep for 24 hours after expiration
                }
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            # Return token JTI as fallback
            return token_jti
    
    def validate_session(self, session_id: str, user_id: str) -> bool:
        """
        Validate session and update last activity.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            True if session is valid, False otherwise
        """
        if not self.sessions_table:
            # If no sessions table, assume valid
            return True
        
        try:
            response = self.sessions_table.get_item(
                Key={'session_id': session_id}
            )
            
            if 'Item' not in response:
                return False
            
            session = response['Item']
            current_time = int(time.time())
            
            # Check if session belongs to user
            if session.get('user_id') != user_id:
                return False
            
            # Check if session is active
            if session.get('status') != 'active':
                return False
            
            # Check if session has expired
            if session.get('expires_at', 0) < current_time:
                self._invalidate_session(session_id)
                return False
            
            # Update last activity
            self.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET last_activity = :time, expires_at = :expires',
                ExpressionAttributeValues={
                    ':time': current_time,
                    ':expires': current_time + self.session_timeout
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def invalidate_session(self, session_id: str, reason: str = "logout") -> None:
        """
        Invalidate a session.
        
        Args:
            session_id: Session identifier
            reason: Reason for invalidation
        """
        self._invalidate_session(session_id, reason)
    
    def _invalidate_session(self, session_id: str, reason: str = "logout") -> None:
        """Internal method to invalidate session."""
        if not self.sessions_table:
            return
        
        try:
            self.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET #status = :status, invalidated_at = :time, invalidation_reason = :reason',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'invalidated',
                    ':time': int(time.time()),
                    ':reason': reason
                }
            )
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    def _cleanup_expired_sessions(self, user_id: str) -> None:
        """Clean up expired sessions for a user."""
        if not self.sessions_table:
            return
        
        try:
            current_time = int(time.time())
            
            # Query user's sessions
            response = self.sessions_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='expires_at < :current_time AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':current_time': current_time,
                    ':status': 'active'
                }
            )
            
            # Invalidate expired sessions
            for session in response.get('Items', []):
                self._invalidate_session(session['session_id'], 'expired')
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def _get_active_sessions(self, user_id: str) -> List[Dict]:
        """Get active sessions for a user."""
        if not self.sessions_table:
            return []
        
        try:
            current_time = int(time.time())
            
            response = self.sessions_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='expires_at > :current_time AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':current_time': current_time,
                    ':status': 'active'
                }
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []


class MFAValidator:
    """
    Multi-Factor Authentication validator for sensitive operations.
    Implements Requirement 10.2 for MFA enforcement.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # MFA challenges table
        self.mfa_table_name = os.environ.get('MFA_CHALLENGES_TABLE', 'aquachain-mfa-challenges')
        try:
            self.mfa_table = self.dynamodb.Table(self.mfa_table_name)
        except Exception as e:
            logger.warning(f"MFA challenges table not available: {e}")
            self.mfa_table = None
        
        # MFA configuration
        self.mfa_timeout = int(os.environ.get('MFA_TIMEOUT_MINUTES', '5')) * 60
        self.sensitive_operations = [
            'purchase-order-approval',
            'budget-allocation',
            'user-role-management',
            'system-configuration',
            'security-policy-changes'
        ]
    
    def is_sensitive_operation(self, operation: str) -> bool:
        """Check if operation requires MFA."""
        return operation in self.sensitive_operations
    
    def initiate_mfa_challenge(
        self, 
        user_id: str, 
        username: str,
        operation: str,
        request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initiate MFA challenge for sensitive operation.
        
        Args:
            user_id: User identifier
            username: Username
            operation: Operation requiring MFA
            request_context: Request context
            
        Returns:
            MFA challenge details
        """
        if not self.is_sensitive_operation(operation):
            return {'required': False}
        
        try:
            # Check if user has MFA enabled
            user_response = self.cognito_client.admin_get_user(
                UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                Username=username
            )
            
            mfa_enabled = False
            for attr in user_response.get('UserAttributes', []):
                if attr['Name'] == 'phone_number_verified' and attr['Value'] == 'true':
                    mfa_enabled = True
                    break
            
            if not mfa_enabled:
                # Log MFA requirement but allow operation
                logger.warning(
                    f"MFA required but not enabled for user {username} operation {operation}",
                    user_id=user_id,
                    operation=operation
                )
                return {'required': False, 'warning': 'MFA not enabled'}
            
            # Create MFA challenge
            challenge_id = f"mfa_{int(time.time())}_{user_id[:8]}"
            current_time = int(time.time())
            expires_at = current_time + self.mfa_timeout
            
            if self.mfa_table:
                self.mfa_table.put_item(
                    Item={
                        'challenge_id': challenge_id,
                        'user_id': user_id,
                        'username': username,
                        'operation': operation,
                        'created_at': current_time,
                        'expires_at': expires_at,
                        'status': 'pending',
                        'ip_address': request_context.get('ip_address', 'unknown'),
                        'ttl': expires_at + 3600  # Keep for 1 hour after expiration
                    }
                )
            
            # Initiate SMS challenge via Cognito
            try:
                challenge_response = self.cognito_client.admin_initiate_auth(
                    UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                    ClientId=os.environ.get('COGNITO_CLIENT_ID'),
                    AuthFlow='ADMIN_NO_SRP_AUTH',
                    AuthParameters={
                        'USERNAME': username,
                        'SMS_MFA': 'true'
                    }
                )
                
                return {
                    'required': True,
                    'challenge_id': challenge_id,
                    'challenge_type': 'SMS_MFA',
                    'session': challenge_response.get('Session'),
                    'expires_in': self.mfa_timeout
                }
                
            except ClientError as e:
                logger.error(f"Error initiating MFA challenge: {e}")
                return {'required': False, 'error': 'MFA challenge failed'}
            
        except Exception as e:
            logger.error(f"Error in MFA challenge initiation: {e}")
            return {'required': False, 'error': 'MFA system unavailable'}
    
    def verify_mfa_challenge(
        self, 
        challenge_id: str, 
        user_id: str,
        mfa_code: str,
        session: str
    ) -> bool:
        """
        Verify MFA challenge response.
        
        Args:
            challenge_id: Challenge identifier
            user_id: User identifier
            mfa_code: MFA code from user
            session: Cognito session
            
        Returns:
            True if MFA verification successful
        """
        if not self.mfa_table:
            logger.warning("MFA table not available, allowing operation")
            return True
        
        try:
            # Get challenge details
            response = self.mfa_table.get_item(
                Key={'challenge_id': challenge_id}
            )
            
            if 'Item' not in response:
                return False
            
            challenge = response['Item']
            current_time = int(time.time())
            
            # Validate challenge
            if challenge.get('user_id') != user_id:
                return False
            
            if challenge.get('status') != 'pending':
                return False
            
            if challenge.get('expires_at', 0) < current_time:
                self._invalidate_mfa_challenge(challenge_id, 'expired')
                return False
            
            # Verify MFA code with Cognito
            try:
                self.cognito_client.admin_respond_to_auth_challenge(
                    UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                    ClientId=os.environ.get('COGNITO_CLIENT_ID'),
                    ChallengeName='SMS_MFA',
                    Session=session,
                    ChallengeResponses={
                        'SMS_MFA_CODE': mfa_code,
                        'USERNAME': challenge.get('username')
                    }
                )
                
                # Mark challenge as completed
                self.mfa_table.update_item(
                    Key={'challenge_id': challenge_id},
                    UpdateExpression='SET #status = :status, completed_at = :time',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':time': current_time
                    }
                )
                
                return True
                
            except ClientError as e:
                logger.warning(f"MFA verification failed: {e}")
                self._invalidate_mfa_challenge(challenge_id, 'failed')
                return False
            
        except Exception as e:
            logger.error(f"Error verifying MFA challenge: {e}")
            return False
    
    def _invalidate_mfa_challenge(self, challenge_id: str, reason: str) -> None:
        """Invalidate MFA challenge."""
        if not self.mfa_table:
            return
        
        try:
            self.mfa_table.update_item(
                Key={'challenge_id': challenge_id},
                UpdateExpression='SET #status = :status, invalidated_at = :time, invalidation_reason = :reason',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'invalidated',
                    ':time': int(time.time()),
                    ':reason': reason
                }
            )
        except Exception as e:
            logger.error(f"Error invalidating MFA challenge: {e}")


class JWTMiddleware:
    """
    Complete JWT middleware with token validation, session management, and MFA.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'us-east-1'):
        self.jwt_validator = JWTValidator(user_pool_id, region)
        self.session_manager = SessionManager(region)
        self.mfa_validator = MFAValidator(region)
    
    def create_auth_middleware(
        self,
        required_scopes: Optional[List[str]] = None,
        require_mfa_for: Optional[List[str]] = None
    ):
        """
        Create authentication middleware decorator.
        
        Args:
            required_scopes: Required token scopes
            require_mfa_for: Operations requiring MFA
            
        Returns:
            Middleware decorator
        """
        def middleware(func):
            @wraps(func)
            def wrapper(event, context):
                try:
                    # Extract token from Authorization header
                    auth_header = event.get('headers', {}).get('Authorization', '')
                    if not auth_header.startswith('Bearer '):
                        raise AuthenticationError('Missing or invalid Authorization header')
                    
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    
                    # Validate JWT token
                    decoded_token = self.jwt_validator.validate_token(token, required_scopes)
                    
                    # Extract user information
                    user_id = decoded_token.get('sub')
                    username = decoded_token.get('cognito:username', decoded_token.get('username'))
                    user_role = decoded_token.get('cognito:groups', ['consumer'])[0]
                    token_jti = decoded_token.get('jti')
                    
                    # Create request context
                    request_context = {
                        'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
                        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
                        'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
                        'source': 'jwt_middleware'
                    }
                    
                    # Create or validate session
                    session_id = self.session_manager.create_session(
                        user_id, token_jti, request_context
                    )
                    
                    if not self.session_manager.validate_session(session_id, user_id):
                        raise AuthenticationError('Invalid or expired session')
                    
                    # Check MFA requirements
                    operation = event.get('pathParameters', {}).get('operation')
                    mfa_required = False
                    
                    if require_mfa_for and operation in require_mfa_for:
                        mfa_challenge = self.mfa_validator.initiate_mfa_challenge(
                            user_id, username, operation, request_context
                        )
                        
                        if mfa_challenge.get('required'):
                            mfa_required = True
                            # Check if MFA was already completed for this request
                            mfa_token = event.get('headers', {}).get('X-MFA-Token')
                            if not mfa_token or not self.mfa_validator.verify_mfa_challenge(
                                mfa_challenge['challenge_id'], user_id, mfa_token, 
                                mfa_challenge.get('session')
                            ):
                                return {
                                    'statusCode': 202,
                                    'body': json.dumps({
                                        'mfa_required': True,
                                        'challenge': mfa_challenge
                                    })
                                }
                    
                    # Add authentication context to event
                    event['authContext'] = {
                        'userId': user_id,
                        'username': username,
                        'role': user_role,
                        'sessionId': session_id,
                        'tokenJti': token_jti,
                        'mfaRequired': mfa_required,
                        'tokenClaims': decoded_token
                    }
                    
                    # Log successful authentication
                    audit_logger.log_authentication_event(
                        event_type='TOKEN_VALIDATION_SUCCESS',
                        user_id=user_id,
                        success=True,
                        request_context=request_context,
                        details={
                            'session_id': session_id,
                            'mfa_required': mfa_required,
                            'operation': operation
                        }
                    )
                    
                    # Call the original function
                    return func(event, context)
                    
                except (AuthenticationError, AuthorizationError):
                    raise
                except Exception as e:
                    logger.error(f"JWT middleware error: {e}")
                    raise AuthenticationError('Authentication failed')
            
            return wrapper
        return middleware


@handle_errors
def lambda_handler(event, context):
    """
    Lambda handler for JWT middleware operations.
    """
    # Get configuration from environment variables
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id:
        raise ValidationError('Missing Cognito configuration')
    
    jwt_middleware = JWTMiddleware(user_pool_id, region)
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    body = json.loads(event.get('body', '{}'))
    
    if http_method == 'POST' and path.endswith('/logout'):
        # Logout endpoint - blacklist token and invalidate session
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise ValidationError('Missing Authorization header')
        
        token = auth_header[7:]
        
        try:
            decoded_token = jwt_middleware.jwt_validator.validate_token(token, check_blacklist=False)
            user_id = decoded_token.get('sub')
            token_jti = decoded_token.get('jti')
            expires_at = decoded_token.get('exp')
            
            # Blacklist token
            if token_jti:
                jwt_middleware.jwt_validator.blacklist_token(token_jti, expires_at, 'logout')
            
            # Invalidate session
            session_id = body.get('sessionId')
            if session_id:
                jwt_middleware.session_manager.invalidate_session(session_id, 'logout')
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Logged out successfully'})
            }
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Logged out'})
            }
    
    elif http_method == 'POST' and path.endswith('/mfa/initiate'):
        # Initiate MFA challenge
        user_id = body.get('userId')
        username = body.get('username')
        operation = body.get('operation')
        
        if not all([user_id, username, operation]):
            raise ValidationError('Missing required fields: userId, username, operation')
        
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'mfa_api'
        }
        
        mfa_challenge = jwt_middleware.mfa_validator.initiate_mfa_challenge(
            user_id, username, operation, request_context
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(mfa_challenge)
        }
    
    elif http_method == 'POST' and path.endswith('/mfa/verify'):
        # Verify MFA challenge
        challenge_id = body.get('challengeId')
        user_id = body.get('userId')
        mfa_code = body.get('mfaCode')
        session = body.get('session')
        
        if not all([challenge_id, user_id, mfa_code, session]):
            raise ValidationError('Missing required fields: challengeId, userId, mfaCode, session')
        
        is_valid = jwt_middleware.mfa_validator.verify_mfa_challenge(
            challenge_id, user_id, mfa_code, session
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'valid': is_valid,
                'message': 'MFA verification successful' if is_valid else 'MFA verification failed'
            })
        }
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')