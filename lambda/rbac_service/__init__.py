"""
RBAC Service Package for AquaChain Dashboard Overhaul.

This package provides role-based access control functionality including:
- Authority matrix enforcement
- Cognito role validation
- Permission checking
- Audit logging
- Middleware decorators for Lambda functions
"""

from .handler import RBACService, AuthorityMatrix, CognitoRoleValidator
from .rbac_middleware import (
    RBACMiddleware,
    get_rbac_middleware,
    require_permission,
    require_role,
    require_authority_level,
    require_admin,
    require_finance_controller,
    require_operations_role,
    require_approval_authority,
    require_configuration_authority
)

__all__ = [
    'RBACService',
    'AuthorityMatrix', 
    'CognitoRoleValidator',
    'RBACMiddleware',
    'get_rbac_middleware',
    'require_permission',
    'require_role',
    'require_authority_level',
    'require_admin',
    'require_finance_controller',
    'require_operations_role',
    'require_approval_authority',
    'require_configuration_authority'
]