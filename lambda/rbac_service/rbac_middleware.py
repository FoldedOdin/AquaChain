"""
RBAC Middleware for Lambda functions.
Provides decorators and utilities for enforcing role-based access control.
"""

import json
import os
import sys
from functools import wraps
from typing import Dict, List, Optional, Any, Callable

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import AuthenticationError, AuthorizationError, ValidationError
from structured_logger import get_logger

# Import RBAC service components
from .handler import RBACService, AuthorityMatrix

logger = get_logger(__name__, service='rbac-middleware')


class RBACMiddleware:
    """
    Middleware class for RBAC enforcement in Lambda functions.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'us-east-1'):
        self.rbac_service = RBACService(user_pool_id, region)
    
    def extract_user_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user context from Lambda event.
        Assumes JWT token has been validated and user context added to event.
        
        Args:
            event: Lambda event object
            
        Returns:
            User context dictionary
            
        Raises:
            AuthenticationError: If user context is missing or invalid
        """
        user_context = event.get('userContext')
        
        if not user_context:
            raise AuthenticationError('User context not found in event')
        
        required_fields = ['userId', 'username', 'role']
        missing_fields = [field for field in required_fields if not user_context.get(field)]
        
        if missing_fields:
            raise AuthenticationError(f'Missing user context fields: {missing_fields}')
        
        return user_context
    
    def create_request_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create request context for audit logging.
        
        Args:
            event: Lambda event object
            
        Returns:
            Request context dictionary
        """
        return {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'lambda_middleware'
        }
    
    def require_permission(
        self,
        resource: str,
        action: str,
        allow_self_access: bool = False,
        resource_owner_field: str = 'userId'
    ):
        """
        Decorator to require specific permission for Lambda function.
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            allow_self_access: Whether to allow access to own resources
            resource_owner_field: Field name for resource owner in path parameters
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
                try:
                    # Extract user context
                    user_context = self.extract_user_context(event)
                    request_context = self.create_request_context(event)
                    
                    user_id = user_context['userId']
                    username = user_context['username']
                    
                    # Check if this is self-access
                    if allow_self_access:
                        resource_owner = event.get('pathParameters', {}).get(resource_owner_field)
                        if resource_owner and resource_owner == user_id:
                            # Allow self-access without permission check
                            return func(event, context)
                    
                    # Validate permissions
                    is_authorized, user_role, audit_details = self.rbac_service.validate_user_permissions(
                        user_id, username, resource, action, request_context
                    )
                    
                    if not is_authorized:
                        raise AuthorizationError(
                            f'Insufficient permissions for {action} on {resource}',
                            details={
                                'required_resource': resource,
                                'required_action': action,
                                'user_role': user_role
                            }
                        )
                    
                    # Add RBAC context to event for use in function
                    event['rbacContext'] = {
                        'userRole': user_role,
                        'authorizedResource': resource,
                        'authorizedAction': action,
                        'auditDetails': audit_details
                    }
                    
                    return func(event, context)
                    
                except (AuthenticationError, AuthorizationError):
                    raise
                except Exception as e:
                    logger.error(f"RBAC middleware error: {e}")
                    raise AuthorizationError('Permission validation failed')
            
            return wrapper
        return decorator
    
    def require_role(self, required_roles: List[str]):
        """
        Decorator to require specific role(s) for Lambda function.
        
        Args:
            required_roles: List of acceptable roles
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
                try:
                    # Extract user context
                    user_context = self.extract_user_context(event)
                    user_role = user_context.get('role')
                    
                    if user_role not in required_roles:
                        request_context = self.create_request_context(event)
                        
                        # Log unauthorized access attempt
                        logger.warning(
                            f"Role access denied: user has role '{user_role}', required: {required_roles}",
                            request_id=request_context.get('request_id'),
                            user_id=user_context.get('userId'),
                            user_role=user_role,
                            required_roles=required_roles
                        )
                        
                        raise AuthorizationError(
                            f'Role {user_role} not authorized. Required roles: {required_roles}',
                            details={
                                'user_role': user_role,
                                'required_roles': required_roles
                            }
                        )
                    
                    return func(event, context)
                    
                except (AuthenticationError, AuthorizationError):
                    raise
                except Exception as e:
                    logger.error(f"Role validation error: {e}")
                    raise AuthorizationError('Role validation failed')
            
            return wrapper
        return decorator
    
    def require_authority_level(self, required_level: str):
        """
        Decorator to require minimum authority level for Lambda function.
        
        Args:
            required_level: Required authority level (VIEW, ACT, APPROVE, CONFIGURE)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
                try:
                    # Extract user context
                    user_context = self.extract_user_context(event)
                    user_role = user_context.get('role')
                    
                    if not AuthorityMatrix.has_authority_level(user_role, required_level):
                        request_context = self.create_request_context(event)
                        
                        # Log unauthorized access attempt
                        logger.warning(
                            f"Authority level access denied: user role '{user_role}' lacks '{required_level}' authority",
                            request_id=request_context.get('request_id'),
                            user_id=user_context.get('userId'),
                            user_role=user_role,
                            required_authority_level=required_level
                        )
                        
                        raise AuthorizationError(
                            f'Insufficient authority level. Required: {required_level}',
                            details={
                                'user_role': user_role,
                                'required_authority_level': required_level
                            }
                        )
                    
                    return func(event, context)
                    
                except (AuthenticationError, AuthorizationError):
                    raise
                except Exception as e:
                    logger.error(f"Authority level validation error: {e}")
                    raise AuthorizationError('Authority level validation failed')
            
            return wrapper
        return decorator


# Create global middleware instance
_middleware_instance = None

def get_rbac_middleware() -> RBACMiddleware:
    """
    Get global RBAC middleware instance.
    
    Returns:
        RBACMiddleware instance
    """
    global _middleware_instance
    
    if _middleware_instance is None:
        user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if not user_pool_id:
            raise ValidationError('COGNITO_USER_POOL_ID environment variable not set')
        
        _middleware_instance = RBACMiddleware(user_pool_id, region)
    
    return _middleware_instance


# Convenience decorators using global middleware
def require_permission(resource: str, action: str, allow_self_access: bool = False, resource_owner_field: str = 'userId'):
    """Convenience decorator using global middleware."""
    return get_rbac_middleware().require_permission(resource, action, allow_self_access, resource_owner_field)

def require_role(required_roles: List[str]):
    """Convenience decorator using global middleware."""
    return get_rbac_middleware().require_role(required_roles)

def require_authority_level(required_level: str):
    """Convenience decorator using global middleware."""
    return get_rbac_middleware().require_authority_level(required_level)

# Specific role decorators for common use cases
def require_admin(func: Callable) -> Callable:
    """Decorator requiring administrator role."""
    return require_role(['administrator'])(func)

def require_finance_controller(func: Callable) -> Callable:
    """Decorator requiring procurement-finance-controller role."""
    return require_role(['procurement-finance-controller'])(func)

def require_operations_role(func: Callable) -> Callable:
    """Decorator requiring any operations role."""
    return require_role(['inventory-manager', 'warehouse-manager', 'supplier-coordinator'])(func)

def require_approval_authority(func: Callable) -> Callable:
    """Decorator requiring APPROVE authority level."""
    return require_authority_level('APPROVE')(func)

def require_configuration_authority(func: Callable) -> Callable:
    """Decorator requiring CONFIGURE authority level."""
    return require_authority_level('CONFIGURE')(func)