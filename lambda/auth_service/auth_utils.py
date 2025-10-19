"""
Authentication utilities for AquaChain Lambda functions.
Provides reusable authentication and authorization functions.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from .handler import TokenManager, AuthorizationManager, TokenValidationError

class AuthUtils:
    """
    Utility class for common authentication operations.
    """
    
    def __init__(self):
        self.user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if self.user_pool_id:
            self.token_manager = TokenManager(self.user_pool_id, self.region)
            self.auth_manager = AuthorizationManager()
        else:
            self.token_manager = None
            self.auth_manager = None
    
    def extract_user_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract and validate user information from Lambda event.
        Returns user context or None if authentication fails.
        """
        if not self.token_manager:
            return None
        
        try:
            # Extract token from Authorization header
            auth_header = event.get('headers', {}).get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Validate token
            decoded_token = self.token_manager.validate_token(token)
            
            # Extract user information
            user_context = {
                'userId': decoded_token.get('sub'),
                'role': decoded_token.get('cognito:groups', ['consumers'])[0],
                'email': decoded_token.get('email'),
                'deviceIds': decoded_token.get('custom:deviceIds', '').split(',') if decoded_token.get('custom:deviceIds') else []
            }
            
            return user_context
            
        except TokenValidationError:
            return None
        except Exception:
            return None
    
    def check_device_access(self, user_context: Dict, device_id: str) -> bool:
        """
        Check if user has access to specific device.
        """
        if not user_context or not self.auth_manager:
            return False
        
        user_role = user_context.get('role')
        user_id = user_context.get('userId')
        user_devices = user_context.get('deviceIds', [])
        
        return self.auth_manager.can_access_device(
            user_role, user_id, device_id, user_devices
        )
    
    def check_resource_permission(self, user_context: Dict, resource: str, 
                                action: str, resource_owner: str = None) -> bool:
        """
        Check if user has permission for resource action.
        """
        if not user_context or not self.auth_manager:
            return False
        
        user_role = user_context.get('role')
        user_id = user_context.get('userId')
        
        return self.auth_manager.check_permission(
            user_role, resource, action, user_id, resource_owner
        )
    
    def create_auth_response(self, status_code: int, message: str) -> Dict:
        """
        Create standardized authentication response.
        """
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({'error': message} if status_code >= 400 else {'message': message})
        }
    
    def validate_admin_access(self, user_context: Dict) -> bool:
        """
        Check if user has administrator access.
        """
        return user_context and user_context.get('role') == 'administrators'
    
    def validate_technician_access(self, user_context: Dict) -> bool:
        """
        Check if user has technician access.
        """
        return user_context and user_context.get('role') in ['technicians', 'administrators']
    
    def get_user_device_filter(self, user_context: Dict) -> Optional[List[str]]:
        """
        Get device filter for user based on role and permissions.
        Returns None for admin (no filter), device list for consumers, or empty list for no access.
        """
        if not user_context:
            return []
        
        user_role = user_context.get('role')
        
        if user_role == 'administrators':
            return None  # No filter - can access all devices
        elif user_role == 'consumers':
            return user_context.get('deviceIds', [])
        else:
            return []  # No device access for other roles by default

def require_auth(resource: str = None, action: str = None):
    """
    Decorator for Lambda functions that require authentication.
    """
    def decorator(func):
        def wrapper(event, context):
            auth_utils = AuthUtils()
            
            # Extract user context
            user_context = auth_utils.extract_user_from_event(event)
            if not user_context:
                return auth_utils.create_auth_response(401, 'Authentication required')
            
            # Check permissions if specified
            if resource and action:
                resource_owner = event.get('pathParameters', {}).get('userId')
                if not auth_utils.check_resource_permission(
                    user_context, resource, action, resource_owner
                ):
                    return auth_utils.create_auth_response(403, 'Insufficient permissions')
            
            # Add user context to event
            event['userContext'] = user_context
            
            # Call original function
            return func(event, context)
        
        return wrapper
    return decorator

def require_admin(func):
    """
    Decorator for Lambda functions that require administrator access.
    """
    def wrapper(event, context):
        auth_utils = AuthUtils()
        
        # Extract user context
        user_context = auth_utils.extract_user_from_event(event)
        if not user_context:
            return auth_utils.create_auth_response(401, 'Authentication required')
        
        # Check admin access
        if not auth_utils.validate_admin_access(user_context):
            return auth_utils.create_auth_response(403, 'Administrator access required')
        
        # Add user context to event
        event['userContext'] = user_context
        
        # Call original function
        return func(event, context)
    
    return wrapper

def require_technician(func):
    """
    Decorator for Lambda functions that require technician or admin access.
    """
    def wrapper(event, context):
        auth_utils = AuthUtils()
        
        # Extract user context
        user_context = auth_utils.extract_user_from_event(event)
        if not user_context:
            return auth_utils.create_auth_response(401, 'Authentication required')
        
        # Check technician access
        if not auth_utils.validate_technician_access(user_context):
            return auth_utils.create_auth_response(403, 'Technician access required')
        
        # Add user context to event
        event['userContext'] = user_context
        
        # Call original function
        return func(event, context)
    
    return wrapper

# Global auth utils instance
auth_utils = AuthUtils()