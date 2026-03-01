"""
RBAC Integration Middleware
Provides consistent RBAC validation across all backend services for the dashboard overhaul.

This middleware ensures that all services properly validate user permissions
before performing any operations, implementing the authority matrix consistently.
"""

import json
import os
import boto3
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timezone
from functools import wraps
import logging

# Import shared utilities
from structured_logger import get_logger
from audit_logger import audit_logger

logger = get_logger(__name__, 'rbac-middleware')


class RBACMiddleware:
    """
    RBAC middleware for consistent permission validation across all services
    """
    
    def __init__(self, rbac_service_function: str = None):
        """
        Initialize RBAC middleware
        
        Args:
            rbac_service_function: Name of the RBAC service Lambda function
        """
        self.rbac_service_function = rbac_service_function or os.environ.get(
            'RBAC_SERVICE_FUNCTION', 'rbac-service'
        )
        self.lambda_client = boto3.client('lambda')
        
        # Authority matrix for local validation (cached)
        self.authority_matrix = {
            'inventory-manager': {
                'can_view': [
                    'inventory-data', 'demand-forecasts', 'reorder-alerts', 
                    'inventory-audit-history', 'stock-levels'
                ],
                'can_act': [
                    'inventory-planning', 'reorder-requests', 'stock-adjustments',
                    'demand-forecast-review'
                ],
                'can_approve': [],
                'can_configure': []
            },
            'warehouse-manager': {
                'can_view': [
                    'warehouse-operations', 'stock-movements', 'location-data',
                    'receiving-dispatch-data', 'warehouse-performance'
                ],
                'can_act': [
                    'receiving-workflows', 'dispatch-workflows', 'location-management',
                    'stock-movement-tracking', 'warehouse-operations'
                ],
                'can_approve': [],
                'can_configure': []
            },
            'supplier-coordinator': {
                'can_view': [
                    'supplier-profiles', 'contracts', 'supplier-performance',
                    'supplier-risk-indicators', 'supplier-communications'
                ],
                'can_act': [
                    'supplier-communication', 'contract-coordination',
                    'supplier-profile-updates', 'performance-tracking'
                ],
                'can_approve': [],
                'can_configure': []
            },
            'procurement-finance-controller': {
                'can_view': [
                    'financial-data', 'budgets', 'purchase-orders', 'spend-analysis',
                    'supplier-financial-risk', 'budget-utilization', 'audit-trails'
                ],
                'can_act': [
                    'budget-allocation', 'spend-analysis', 'financial-reporting',
                    'purchase-order-review', 'supplier-evaluation'
                ],
                'can_approve': [
                    'purchase-orders', 'budget-changes', 'emergency-purchases',
                    'supplier-contracts', 'financial-commitments'
                ],
                'can_configure': [
                    'budget-rules', 'approval-thresholds', 'financial-policies'
                ]
            },
            'administrator': {
                'can_view': [
                    'system-monitoring', 'user-management', 'security-logs',
                    'system-configuration', 'audit-trails', 'compliance-reports'
                ],
                'can_act': [
                    'user-role-management', 'system-configuration',
                    'security-monitoring', 'incident-response'
                ],
                'can_approve': [],
                'can_configure': [
                    'system-settings', 'security-policies', 'user-roles',
                    'authority-matrix', 'compliance-settings'
                ]
            }
        }
    
    def validate_permissions(
        self,
        user_id: str,
        username: str,
        resource: str,
        action: str,
        request_context: Dict[str, Any],
        use_remote_validation: bool = True
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate user permissions for resource and action
        
        Args:
            user_id: User ID from JWT token
            username: Username from JWT token
            resource: Resource being accessed
            action: Action being performed (view, act, approve, configure)
            request_context: Request context for audit logging
            use_remote_validation: Whether to use remote RBAC service (default: True)
            
        Returns:
            Tuple of (is_authorized, user_role, audit_details)
        """
        try:
            if use_remote_validation:
                # Use remote RBAC service for validation
                return self._validate_with_rbac_service(
                    user_id, username, resource, action, request_context
                )
            else:
                # Use local validation as fallback
                return self._validate_locally(
                    user_id, username, resource, action, request_context
                )
                
        except Exception as e:
            logger.error(
                "RBAC validation failed",
                user_id=user_id,
                resource=resource,
                action=action,
                error=str(e)
            )
            
            # Log security event for validation failure
            audit_logger.log_user_action(
                user_id=user_id,
                action='RBAC_VALIDATION_ERROR',
                resource='RBAC_MIDDLEWARE',
                resource_id=f"{resource}:{action}",
                details={
                    'error': str(e),
                    'resource': resource,
                    'action': action,
                    'validation_method': 'remote' if use_remote_validation else 'local'
                },
                request_context=request_context
            )
            
            # Fail secure - deny access on validation error
            return False, None, {'error': 'RBAC validation failed', 'details': str(e)}
    
    def _validate_with_rbac_service(
        self,
        user_id: str,
        username: str,
        resource: str,
        action: str,
        request_context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate permissions using remote RBAC service
        """
        try:
            payload = {
                'userId': user_id,
                'username': username,
                'resource': resource,
                'action': action,
                'requestContext': request_context
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.rbac_service_function,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'httpMethod': 'POST',
                    'path': '/validate-permissions',
                    'body': json.dumps(payload),
                    'requestContext': request_context
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                return (
                    body.get('authorized', False),
                    body.get('userRole'),
                    body.get('auditDetails', {})
                )
            else:
                logger.warning(
                    "RBAC service returned error",
                    status_code=result.get('statusCode'),
                    user_id=user_id,
                    resource=resource
                )
                # Fall back to local validation
                return self._validate_locally(user_id, username, resource, action, request_context)
                
        except Exception as e:
            logger.warning(
                "RBAC service call failed, falling back to local validation",
                error=str(e),
                user_id=user_id,
                resource=resource
            )
            # Fall back to local validation
            return self._validate_locally(user_id, username, resource, action, request_context)
    
    def _validate_locally(
        self,
        user_id: str,
        username: str,
        resource: str,
        action: str,
        request_context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate permissions using local authority matrix (fallback)
        """
        # This is a simplified local validation
        # In production, this would need to get user role from Cognito or cache
        
        # For now, extract role from username or use a default mapping
        # This is a fallback mechanism and should be enhanced
        user_role = self._extract_user_role(username)
        
        if not user_role or user_role not in self.authority_matrix:
            audit_details = {
                'failure_reason': 'no_valid_role',
                'username': username,
                'resource': resource,
                'action': action
            }
            
            # Log unauthorized access attempt
            audit_logger.log_user_action(
                user_id=user_id,
                action='RBAC_ACCESS_DENIED',
                resource='RBAC_MIDDLEWARE',
                resource_id=f"{resource}:{action}",
                details=audit_details,
                request_context=request_context
            )
            
            return False, None, audit_details
        
        # Check if role can perform action on resource
        role_permissions = self.authority_matrix[user_role]
        action_key = f'can_{action}'
        
        if action_key in role_permissions:
            allowed_resources = role_permissions[action_key]
            is_authorized = resource in allowed_resources
        else:
            is_authorized = False
        
        audit_details = {
            'user_role': user_role,
            'resource': resource,
            'action': action,
            'authorized': is_authorized,
            'validation_method': 'local_fallback'
        }
        
        # Log access attempt
        audit_logger.log_user_action(
            user_id=user_id,
            action='RBAC_ACCESS_CHECK',
            resource='RBAC_MIDDLEWARE',
            resource_id=f"{resource}:{action}",
            details=audit_details,
            request_context=request_context
        )
        
        return is_authorized, user_role, audit_details
    
    def _extract_user_role(self, username: str) -> Optional[str]:
        """
        Extract user role from username (simplified fallback)
        In production, this should query Cognito or use cached role data
        """
        # This is a simplified mapping for fallback purposes
        role_mappings = {
            'inventory': 'inventory-manager',
            'warehouse': 'warehouse-manager',
            'supplier': 'supplier-coordinator',
            'procurement': 'procurement-finance-controller',
            'finance': 'procurement-finance-controller',
            'admin': 'administrator'
        }
        
        username_lower = username.lower()
        for keyword, role in role_mappings.items():
            if keyword in username_lower:
                return role
        
        # Default to most restrictive role if no match
        return None
    
    def require_permission(
        self,
        resource: str,
        action: str,
        use_remote_validation: bool = True
    ):
        """
        Decorator for requiring specific permissions on a function
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            use_remote_validation: Whether to use remote RBAC service
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract request context from Lambda event
                event = args[0] if args else kwargs.get('event', {})
                
                # Extract user information from JWT token or request context
                user_id = self._extract_user_id(event)
                username = self._extract_username(event)
                request_context = self._extract_request_context(event)
                
                if not user_id or not username:
                    logger.warning(
                        "Missing user information in request",
                        resource=resource,
                        action=action
                    )
                    return {
                        'statusCode': 401,
                        'body': json.dumps({
                            'error': 'Authentication required',
                            'resource': resource,
                            'action': action
                        })
                    }
                
                # Validate permissions
                is_authorized, user_role, audit_details = self.validate_permissions(
                    user_id, username, resource, action, request_context, use_remote_validation
                )
                
                if not is_authorized:
                    logger.warning(
                        "Access denied",
                        user_id=user_id,
                        resource=resource,
                        action=action,
                        user_role=user_role
                    )
                    return {
                        'statusCode': 403,
                        'body': json.dumps({
                            'error': 'Access denied',
                            'resource': resource,
                            'action': action,
                            'userRole': user_role,
                            'auditDetails': audit_details
                        })
                    }
                
                # Add user context to kwargs for the function
                kwargs['user_context'] = {
                    'user_id': user_id,
                    'username': username,
                    'user_role': user_role,
                    'request_context': request_context
                }
                
                # Call the original function
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _extract_user_id(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from Lambda event"""
        # Try to get from authorizer context
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        if 'user_id' in authorizer:
            return authorizer['user_id']
        
        # Try to get from claims
        claims = authorizer.get('claims', {})
        if 'sub' in claims:
            return claims['sub']
        
        # Try to get from headers (for testing)
        headers = event.get('headers', {})
        return headers.get('X-User-ID')
    
    def _extract_username(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract username from Lambda event"""
        # Try to get from authorizer context
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        if 'username' in authorizer:
            return authorizer['username']
        
        # Try to get from claims
        claims = authorizer.get('claims', {})
        if 'cognito:username' in claims:
            return claims['cognito:username']
        
        # Try to get from headers (for testing)
        headers = event.get('headers', {})
        return headers.get('X-Username')
    
    def _extract_request_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract request context from Lambda event"""
        request_context = event.get('requestContext', {})
        identity = request_context.get('identity', {})
        
        return {
            'ip_address': identity.get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': request_context.get('requestId', 'unknown'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', 'unknown'),
            'source': 'rbac_middleware'
        }


# Global RBAC middleware instance
rbac_middleware = RBACMiddleware()


def require_permission(resource: str, action: str, use_remote_validation: bool = True):
    """
    Convenience decorator for requiring permissions
    
    Usage:
        @require_permission('inventory-data', 'view')
        def get_inventory_items(event, context, user_context=None):
            # Function implementation
            pass
    """
    return rbac_middleware.require_permission(resource, action, use_remote_validation)


def validate_user_permissions(
    user_id: str,
    username: str,
    resource: str,
    action: str,
    request_context: Dict[str, Any]
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Convenience function for validating permissions
    
    Returns:
        Tuple of (is_authorized, user_role, audit_details)
    """
    return rbac_middleware.validate_permissions(
        user_id, username, resource, action, request_context
    )