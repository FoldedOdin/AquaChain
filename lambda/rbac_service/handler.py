"""
Role-Based Access Control (RBAC) Service for AquaChain Dashboard Overhaul.
Implements comprehensive role validation, authority matrix enforcement, and audit logging.

Requirements: 3.1, 3.3, 3.5, 12.1, 12.3
"""

import json
import os
import sys
import boto3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import AuthenticationError, AuthorizationError, ValidationError
from error_handler import handle_errors
from structured_logger import get_logger
from audit_logger import audit_logger

# Configure structured logging
logger = get_logger(__name__, service='rbac-service')


class AuthorityMatrix:
    """
    Authority matrix defining what each role can view, act upon, approve, and configure.
    Implements Requirements 12.1 and 12.3 for explicit role boundaries.
    """
    
    # Authority levels in order of increasing privilege
    AUTHORITY_LEVELS = ['VIEW', 'ACT', 'APPROVE', 'CONFIGURE']
    
    # Role authority matrix as defined in Requirements 12
    ROLE_AUTHORITIES = {
        'inventory-manager': {
            'authority_level': 'ACT',
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
            'authority_level': 'ACT',
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
            'authority_level': 'ACT',
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
            'authority_level': 'APPROVE',
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
            'authority_level': 'CONFIGURE',
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
    
    @classmethod
    def get_role_authorities(cls, role: str) -> Dict[str, Any]:
        """Get authorities for a specific role."""
        return cls.ROLE_AUTHORITIES.get(role, {})
    
    @classmethod
    def has_authority_level(cls, role: str, required_level: str) -> bool:
        """Check if role has required authority level or higher."""
        role_data = cls.get_role_authorities(role)
        if not role_data:
            return False
        
        role_level = role_data.get('authority_level')
        if not role_level:
            return False
        
        try:
            role_index = cls.AUTHORITY_LEVELS.index(role_level)
            required_index = cls.AUTHORITY_LEVELS.index(required_level)
            return role_index >= required_index
        except ValueError:
            return False
    
    @classmethod
    def can_perform_action(cls, role: str, resource: str, action_type: str) -> bool:
        """
        Check if role can perform specific action on resource.
        
        Args:
            role: User role
            resource: Resource identifier
            action_type: Type of action (view, act, approve, configure)
        
        Returns:
            True if action is allowed, False otherwise
        """
        role_data = cls.get_role_authorities(role)
        if not role_data:
            return False
        
        action_key = f'can_{action_type}'
        allowed_resources = role_data.get(action_key, [])
        
        return resource in allowed_resources


class CognitoRoleValidator:
    """
    Validates user roles against AWS Cognito user groups.
    Implements Requirement 3.1 for role validation against Cognito.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'us-east-1'):
        self.user_pool_id = user_pool_id
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
    
    def get_user_groups(self, username: str) -> List[str]:
        """
        Get user groups from Cognito.
        
        Args:
            username: Cognito username
            
        Returns:
            List of group names user belongs to
            
        Raises:
            AuthenticationError: If user not found or other Cognito error
        """
        try:
            response = self.cognito_client.admin_list_groups_for_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            groups = [group['GroupName'] for group in response.get('Groups', [])]
            return groups
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                raise AuthenticationError(f"User not found: {username}")
            else:
                logger.error(f"Error getting user groups: {e}")
                raise AuthenticationError(f"Failed to validate user groups: {error_code}")
    
    def validate_user_role(self, username: str, required_role: str) -> bool:
        """
        Validate that user has required role.
        
        Args:
            username: Cognito username
            required_role: Required role name
            
        Returns:
            True if user has required role, False otherwise
        """
        try:
            user_groups = self.get_user_groups(username)
            return required_role in user_groups
        except AuthenticationError:
            return False
    
    def get_primary_role(self, username: str) -> Optional[str]:
        """
        Get user's primary role (highest authority level).
        
        Args:
            username: Cognito username
            
        Returns:
            Primary role name or None if no valid roles
        """
        try:
            user_groups = self.get_user_groups(username)
            
            # Find the role with highest authority level
            primary_role = None
            highest_authority_index = -1
            
            for group in user_groups:
                if group in AuthorityMatrix.ROLE_AUTHORITIES:
                    role_data = AuthorityMatrix.get_role_authorities(group)
                    authority_level = role_data.get('authority_level')
                    
                    if authority_level in AuthorityMatrix.AUTHORITY_LEVELS:
                        authority_index = AuthorityMatrix.AUTHORITY_LEVELS.index(authority_level)
                        if authority_index > highest_authority_index:
                            highest_authority_index = authority_index
                            primary_role = group
            
            return primary_role
            
        except AuthenticationError:
            return None


class RBACService:
    """
    Main RBAC service implementing permission checking and audit logging.
    Implements Requirements 3.3, 3.5, 12.1, and 12.3.
    """
    
    def __init__(self, user_pool_id: str, region: str = 'us-east-1'):
        self.user_pool_id = user_pool_id
        self.region = region
        self.cognito_validator = CognitoRoleValidator(user_pool_id, region)
    
    def validate_user_permissions(
        self,
        user_id: str,
        username: str,
        resource: str,
        action: str,
        request_context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate user permissions for resource and action.
        
        Args:
            user_id: User ID from JWT token
            username: Username from JWT token
            resource: Resource being accessed
            action: Action being performed
            request_context: Request context for audit logging
            
        Returns:
            Tuple of (is_authorized, user_role, audit_details)
        """
        audit_details = {
            'resource': resource,
            'action': action,
            'validation_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Get user's primary role from Cognito
            user_role = self.cognito_validator.get_primary_role(username)
            
            if not user_role:
                audit_details['failure_reason'] = 'no_valid_role'
                self._log_access_attempt(
                    user_id, username, resource, action, False, 
                    request_context, audit_details
                )
                return False, None, audit_details
            
            audit_details['user_role'] = user_role
            
            # Check if role can perform action on resource
            is_authorized = AuthorityMatrix.can_perform_action(user_role, resource, action)
            
            if not is_authorized:
                audit_details['failure_reason'] = 'insufficient_permissions'
                audit_details['required_action'] = action
                audit_details['attempted_resource'] = resource
            
            # Log access attempt
            self._log_access_attempt(
                user_id, username, resource, action, is_authorized,
                request_context, audit_details
            )
            
            return is_authorized, user_role, audit_details
            
        except Exception as e:
            logger.error(f"Error validating permissions: {e}")
            audit_details['failure_reason'] = 'validation_error'
            audit_details['error'] = str(e)
            
            self._log_access_attempt(
                user_id, username, resource, action, False,
                request_context, audit_details
            )
            
            return False, None, audit_details
    
    def check_authority_matrix_compliance(
        self,
        user_role: str,
        requested_authorities: List[str]
    ) -> Dict[str, bool]:
        """
        Check compliance with authority matrix for multiple authorities.
        
        Args:
            user_role: User's role
            requested_authorities: List of authorities being requested
            
        Returns:
            Dictionary mapping authority to compliance status
        """
        compliance_results = {}
        role_data = AuthorityMatrix.get_role_authorities(user_role)
        
        if not role_data:
            return {auth: False for auth in requested_authorities}
        
        for authority in requested_authorities:
            # Check if authority is in any of the role's allowed lists
            is_compliant = (
                authority in role_data.get('can_view', []) or
                authority in role_data.get('can_act', []) or
                authority in role_data.get('can_approve', []) or
                authority in role_data.get('can_configure', [])
            )
            compliance_results[authority] = is_compliant
        
        return compliance_results
    
    def get_user_permissions(self, username: str) -> Dict[str, Any]:
        """
        Get comprehensive permissions for a user.
        
        Args:
            username: Cognito username
            
        Returns:
            Dictionary containing user's permissions and role information
        """
        try:
            user_role = self.cognito_validator.get_primary_role(username)
            
            if not user_role:
                return {
                    'role': None,
                    'authority_level': None,
                    'permissions': {},
                    'valid': False
                }
            
            role_data = AuthorityMatrix.get_role_authorities(user_role)
            
            return {
                'role': user_role,
                'authority_level': role_data.get('authority_level'),
                'permissions': {
                    'can_view': role_data.get('can_view', []),
                    'can_act': role_data.get('can_act', []),
                    'can_approve': role_data.get('can_approve', []),
                    'can_configure': role_data.get('can_configure', [])
                },
                'valid': True
            }
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return {
                'role': None,
                'authority_level': None,
                'permissions': {},
                'valid': False,
                'error': str(e)
            }
    
    def _log_access_attempt(
        self,
        user_id: str,
        username: str,
        resource: str,
        action: str,
        granted: bool,
        request_context: Dict[str, Any],
        details: Dict[str, Any]
    ) -> None:
        """
        Log access attempt for audit trail.
        Implements Requirement 3.5 for comprehensive audit logging.
        """
        try:
            audit_details = {
                'username': username,
                'resource': resource,
                'action': action,
                'granted': granted,
                **details
            }
            
            # Log to audit system
            audit_logger.log_action(
                action_type='RBAC_ACCESS_CHECK',
                user_id=user_id,
                resource_type='RBAC_PERMISSION',
                resource_id=f"{resource}:{action}",
                details=audit_details,
                request_context=request_context
            )
            
            # Also log to structured logger for immediate monitoring
            log_level = 'warning' if not granted else 'info'
            logger.log(
                log_level,
                f"Access {'granted' if granted else 'denied'} for user {username} on {resource}:{action}",
                request_id=request_context.get('request_id'),
                user_id=user_id,
                resource=resource,
                action=action,
                granted=granted,
                user_role=details.get('user_role')
            )
            
        except Exception as e:
            logger.error(f"Error logging access attempt: {e}")


@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for RBAC service operations.
    """
    # Get configuration from environment variables
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not user_pool_id:
        raise ValidationError('Missing Cognito configuration')
    
    rbac_service = RBACService(user_pool_id, region)
    
    # Extract request information
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    body = json.loads(event.get('body', '{}'))
    
    # Extract request context for audit logging
    request_context = {
        'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
        'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
        'source': 'rbac_api'
    }
    
    if http_method == 'POST' and path.endswith('/validate-permissions'):
        # Validate user permissions for resource and action
        user_id = body.get('userId')
        username = body.get('username')
        resource = body.get('resource')
        action = body.get('action')
        
        if not all([user_id, username, resource, action]):
            raise ValidationError('Missing required fields: userId, username, resource, action')
        
        is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
            user_id, username, resource, action, request_context
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'authorized': is_authorized,
                'userRole': user_role,
                'auditDetails': audit_details
            })
        }
    
    elif http_method == 'POST' and path.endswith('/check-authority-matrix'):
        # Check authority matrix compliance
        user_role = body.get('userRole')
        requested_authorities = body.get('requestedAuthorities', [])
        
        if not user_role or not requested_authorities:
            raise ValidationError('Missing required fields: userRole, requestedAuthorities')
        
        compliance_results = rbac_service.check_authority_matrix_compliance(
            user_role, requested_authorities
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'complianceResults': compliance_results,
                'userRole': user_role
            })
        }
    
    elif http_method == 'GET' and path.endswith('/user-permissions'):
        # Get user permissions
        username = event.get('queryStringParameters', {}).get('username')
        
        if not username:
            raise ValidationError('Missing required parameter: username')
        
        permissions = rbac_service.get_user_permissions(username)
        
        return {
            'statusCode': 200,
            'body': json.dumps(permissions)
        }
    
    elif http_method == 'GET' and path.endswith('/authority-matrix'):
        # Get complete authority matrix (admin only)
        # This endpoint would need additional authentication in real implementation
        return {
            'statusCode': 200,
            'body': json.dumps({
                'authorityMatrix': AuthorityMatrix.ROLE_AUTHORITIES,
                'authorityLevels': AuthorityMatrix.AUTHORITY_LEVELS
            })
        }
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')