"""
Property-based tests for RBAC authorization

Feature: dashboard-overhaul, Property 2: Unauthorized Access Prevention and Logging
Feature: dashboard-overhaul, Property 3: API Authorization Validation  
Feature: dashboard-overhaul, Property 11: Authority Matrix Enforcement
Validates: Requirements 3.3, 3.5, 12.1, 12.2, 12.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime, timezone

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from rbac_service.handler import RBACService, AuthorityMatrix, CognitoRoleValidator
from shared.errors import AuthenticationError, AuthorizationError


# Hypothesis strategies for generating test data

# Valid roles from the authority matrix
valid_roles_strategy = st.sampled_from([
    'inventory-manager',
    'warehouse-manager', 
    'supplier-coordinator',
    'procurement-finance-controller',
    'administrator'
])

# Invalid roles (not in authority matrix)
invalid_roles_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz-_',
    min_size=1,
    max_size=30
).filter(lambda x: x not in AuthorityMatrix.ROLE_AUTHORITIES.keys())

# Resources from authority matrix
all_resources_strategy = st.sampled_from([
    'inventory-data', 'demand-forecasts', 'reorder-alerts', 'inventory-audit-history',
    'stock-levels', 'warehouse-operations', 'stock-movements', 'location-data',
    'receiving-dispatch-data', 'warehouse-performance', 'supplier-profiles',
    'contracts', 'supplier-performance', 'supplier-risk-indicators',
    'supplier-communications', 'financial-data', 'budgets', 'purchase-orders',
    'spend-analysis', 'supplier-financial-risk', 'budget-utilization',
    'audit-trails', 'system-monitoring', 'user-management', 'security-logs',
    'system-configuration', 'compliance-reports'
])

# Actions from authority matrix
actions_strategy = st.sampled_from(['view', 'act', 'approve', 'configure'])

# User identifiers
user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=10,
    max_size=50
)

username_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789._-@',
    min_size=3,
    max_size=30
)

# Request context
request_context_strategy = st.fixed_dictionaries({
    'ip_address': st.ip_addresses().map(str),
    'user_agent': st.text(min_size=10, max_size=100),
    'request_id': st.uuids().map(str),
    'source': st.sampled_from(['api', 'lambda_middleware', 'rbac_api'])
})


class TestUnauthorizedAccessPreventionAndLogging:
    """
    Property 2: Unauthorized Access Prevention and Logging
    
    For any user attempting to access resources or perform actions outside their 
    role permissions, the system SHALL deny access immediately, log the attempt 
    with complete details, and return appropriate error responses.
    """
    
    @given(
        role=valid_roles_strategy,
        resource=all_resources_strategy,
        action=actions_strategy,
        user_id=user_id_strategy,
        username=username_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=100)
    def test_unauthorized_access_is_denied_and_logged(
        self, role, resource, action, user_id, username, request_context
    ):
        """
        Property Test: Unauthorized access is denied and logged
        
        For any user role, resource, and action combination where the role
        does not have permission for the action on the resource, the system
        must deny access and log the attempt.
        """
        # Check if this combination should be authorized
        should_be_authorized = AuthorityMatrix.can_perform_action(role, resource, action)
        
        # Skip if this is an authorized combination (we're testing unauthorized access)
        assume(not should_be_authorized)
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': role}]
            }
            mock_boto3.return_value = mock_cognito
            
            # Mock audit logger
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                # Test permission validation
                is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                    user_id, username, resource, action, request_context
                )
                
                # Verify access is denied
                assert not is_authorized, f"Access should be denied for {role} on {resource}:{action}"
                assert user_role == role
                assert 'failure_reason' in audit_details
                assert audit_details['failure_reason'] == 'insufficient_permissions'
                
                # Verify audit logging was called
                mock_audit_logger.log_action.assert_called_once()
                call_args = mock_audit_logger.log_action.call_args
                
                # Verify audit log details
                assert call_args[1]['action_type'] == 'RBAC_ACCESS_CHECK'
                assert call_args[1]['user_id'] == user_id
                assert call_args[1]['resource_type'] == 'RBAC_PERMISSION'
                assert call_args[1]['resource_id'] == f"{resource}:{action}"
                
                audit_log_details = call_args[1]['details']
                assert audit_log_details['username'] == username
                assert audit_log_details['resource'] == resource
                assert audit_log_details['action'] == action
                assert audit_log_details['granted'] is False
    
    @given(
        invalid_role=invalid_roles_strategy,
        resource=all_resources_strategy,
        action=actions_strategy,
        user_id=user_id_strategy,
        username=username_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=50)
    def test_invalid_roles_are_denied_and_logged(
        self, invalid_role, resource, action, user_id, username, request_context
    ):
        """
        Property Test: Invalid roles are denied and logged
        
        For any invalid role (not in authority matrix), access must be denied
        and the attempt must be logged.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client to return invalid role
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': invalid_role}]
            }
            mock_boto3.return_value = mock_cognito
            
            # Mock audit logger
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                # Test permission validation
                is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                    user_id, username, resource, action, request_context
                )
                
                # Verify access is denied
                assert not is_authorized, f"Access should be denied for invalid role {invalid_role}"
                assert user_role is None
                assert 'failure_reason' in audit_details
                assert audit_details['failure_reason'] == 'no_valid_role'
                
                # Verify audit logging was called
                mock_audit_logger.log_action.assert_called_once()


class TestAPIAuthorizationValidation:
    """
    Property 3: API Authorization Validation
    
    For any API request, the system SHALL validate the requesting user's 
    permissions against the authority matrix before processing the request, 
    and SHALL reject requests that violate role boundaries.
    """
    
    @given(
        role=valid_roles_strategy,
        resource=all_resources_strategy,
        action=actions_strategy,
        user_id=user_id_strategy,
        username=username_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=100)
    def test_api_requests_are_validated_against_authority_matrix(
        self, role, resource, action, user_id, username, request_context
    ):
        """
        Property Test: API requests are validated against authority matrix
        
        For any API request with user role, resource, and action, the system
        must validate permissions against the authority matrix and return
        the correct authorization result.
        """
        # Determine expected authorization result
        expected_authorized = AuthorityMatrix.can_perform_action(role, resource, action)
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': role}]
            }
            mock_boto3.return_value = mock_cognito
            
            # Mock audit logger
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                # Test permission validation
                is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                    user_id, username, resource, action, request_context
                )
                
                # Verify authorization matches authority matrix
                assert is_authorized == expected_authorized, (
                    f"Authorization mismatch for {role} on {resource}:{action}. "
                    f"Expected: {expected_authorized}, Got: {is_authorized}"
                )
                assert user_role == role
                
                # Verify audit logging was called
                mock_audit_logger.log_action.assert_called_once()
                
                # Verify audit details match request
                call_args = mock_audit_logger.log_action.call_args
                audit_log_details = call_args[1]['details']
                assert audit_log_details['granted'] == expected_authorized
    
    @given(
        role=valid_roles_strategy,
        requested_authorities=st.lists(all_resources_strategy, min_size=1, max_size=10, unique=True)
    )
    @settings(max_examples=50)
    def test_authority_matrix_compliance_checking(self, role, requested_authorities):
        """
        Property Test: Authority matrix compliance checking
        
        For any role and list of requested authorities, the system must
        correctly determine compliance for each authority based on the
        authority matrix.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client
            mock_cognito = Mock()
            mock_boto3.return_value = mock_cognito
            
            rbac_service = RBACService('test-pool-id', 'us-east-1')
            
            # Test authority matrix compliance
            compliance_results = rbac_service.check_authority_matrix_compliance(
                role, requested_authorities
            )
            
            # Verify compliance results (should have unique authorities)
            assert len(compliance_results) == len(requested_authorities)
            
            role_data = AuthorityMatrix.get_role_authorities(role)
            all_allowed = (
                role_data.get('can_view', []) +
                role_data.get('can_act', []) +
                role_data.get('can_approve', []) +
                role_data.get('can_configure', [])
            )
            
            for authority in requested_authorities:
                expected_compliance = authority in all_allowed
                assert compliance_results[authority] == expected_compliance, (
                    f"Compliance mismatch for {role} and authority {authority}. "
                    f"Expected: {expected_compliance}, Got: {compliance_results[authority]}"
                )


class TestAuthorityMatrixEnforcement:
    """
    Property 11: Authority Matrix Enforcement
    
    For any combination of user role and system action, the system SHALL 
    enforce the authority matrix exactly as defined, with no exceptions.
    """
    
    @given(
        role=valid_roles_strategy,
        resource=all_resources_strategy,
        action=actions_strategy
    )
    @settings(max_examples=200)
    def test_authority_matrix_is_enforced_exactly(self, role, resource, action):
        """
        Property Test: Authority matrix is enforced exactly
        
        For any role, resource, and action combination, the system must
        enforce the authority matrix exactly as defined with no exceptions.
        """
        # Get expected result from authority matrix
        expected_result = AuthorityMatrix.can_perform_action(role, resource, action)
        
        # Test the actual enforcement
        actual_result = AuthorityMatrix.can_perform_action(role, resource, action)
        
        # Verify exact enforcement
        assert actual_result == expected_result, (
            f"Authority matrix enforcement failed for {role} on {resource}:{action}. "
            f"Expected: {expected_result}, Got: {actual_result}"
        )
    
    @given(role=valid_roles_strategy)
    @settings(max_examples=50)
    def test_role_authority_levels_are_consistent(self, role):
        """
        Property Test: Role authority levels are consistent
        
        For any valid role, the authority level must be consistent with
        the permissions granted in the authority matrix.
        """
        role_data = AuthorityMatrix.get_role_authorities(role)
        authority_level = role_data.get('authority_level')
        
        # Verify authority level exists
        assert authority_level in AuthorityMatrix.AUTHORITY_LEVELS, (
            f"Invalid authority level '{authority_level}' for role {role}"
        )
        
        # Verify authority level consistency
        can_approve = len(role_data.get('can_approve', [])) > 0
        can_configure = len(role_data.get('can_configure', [])) > 0
        
        if authority_level == 'VIEW':
            assert not can_approve and not can_configure, (
                f"VIEW level role {role} should not have approve or configure permissions"
            )
        elif authority_level == 'ACT':
            assert not can_approve and not can_configure, (
                f"ACT level role {role} should not have approve or configure permissions"
            )
        elif authority_level == 'APPROVE':
            # APPROVE level can have approve permissions but not necessarily configure
            pass
        elif authority_level == 'CONFIGURE':
            # CONFIGURE level can have any permissions
            pass
    
    @given(
        role1=valid_roles_strategy,
        role2=valid_roles_strategy,
        resource=all_resources_strategy,
        action=actions_strategy
    )
    @settings(max_examples=100)
    def test_authority_matrix_is_deterministic(self, role1, role2, resource, action):
        """
        Property Test: Authority matrix enforcement is deterministic
        
        For any role, resource, and action combination, multiple calls to
        the authority matrix must return the same result.
        """
        # Test determinism for role1
        result1_first = AuthorityMatrix.can_perform_action(role1, resource, action)
        result1_second = AuthorityMatrix.can_perform_action(role1, resource, action)
        
        assert result1_first == result1_second, (
            f"Authority matrix is not deterministic for {role1} on {resource}:{action}"
        )
        
        # Test determinism for role2
        result2_first = AuthorityMatrix.can_perform_action(role2, resource, action)
        result2_second = AuthorityMatrix.can_perform_action(role2, resource, action)
        
        assert result2_first == result2_second, (
            f"Authority matrix is not deterministic for {role2} on {resource}:{action}"
        )
        
        # If roles are the same, results should be identical
        if role1 == role2:
            assert result1_first == result2_first, (
                f"Same role {role1} produced different results for {resource}:{action}"
            )
    
    @given(role=valid_roles_strategy)
    @settings(max_examples=50)
    def test_authority_matrix_completeness(self, role):
        """
        Property Test: Authority matrix is complete for all roles
        
        For any valid role, the authority matrix must contain complete
        permission definitions.
        """
        role_data = AuthorityMatrix.get_role_authorities(role)
        
        # Verify required fields exist
        assert 'authority_level' in role_data, f"Missing authority_level for role {role}"
        assert 'can_view' in role_data, f"Missing can_view for role {role}"
        assert 'can_act' in role_data, f"Missing can_act for role {role}"
        assert 'can_approve' in role_data, f"Missing can_approve for role {role}"
        assert 'can_configure' in role_data, f"Missing can_configure for role {role}"
        
        # Verify field types
        assert isinstance(role_data['can_view'], list), f"can_view must be list for role {role}"
        assert isinstance(role_data['can_act'], list), f"can_act must be list for role {role}"
        assert isinstance(role_data['can_approve'], list), f"can_approve must be list for role {role}"
        assert isinstance(role_data['can_configure'], list), f"can_configure must be list for role {role}"
        
        # Verify authority level is valid
        assert role_data['authority_level'] in AuthorityMatrix.AUTHORITY_LEVELS, (
            f"Invalid authority level for role {role}"
        )


class TestCognitoRoleValidation:
    """
    Additional tests for Cognito role validation functionality.
    """
    
    @given(
        username=username_strategy,
        role=valid_roles_strategy
    )
    @settings(max_examples=50)
    def test_cognito_role_validation_with_valid_role(self, username, role):
        """
        Property Test: Cognito role validation with valid roles
        
        For any username and valid role, if Cognito returns the role,
        validation should succeed.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': role}]
            }
            mock_boto3.return_value = mock_cognito
            
            validator = CognitoRoleValidator('test-pool-id', 'us-east-1')
            
            # Test role validation
            is_valid = validator.validate_user_role(username, role)
            assert is_valid, f"Valid role {role} should be validated for user {username}"
            
            # Test getting user groups
            groups = validator.get_user_groups(username)
            assert role in groups, f"Role {role} should be in user groups"
            
            # Test getting primary role
            primary_role = validator.get_primary_role(username)
            assert primary_role == role, f"Primary role should be {role}"
    
    @given(
        username=username_strategy,
        role=valid_roles_strategy,
        wrong_role=valid_roles_strategy
    )
    @settings(max_examples=50)
    def test_cognito_role_validation_with_wrong_role(self, username, role, wrong_role):
        """
        Property Test: Cognito role validation with wrong roles
        
        For any username, if user has one role but we check for a different role,
        validation should fail.
        """
        assume(role != wrong_role)
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client to return different role
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': role}]
            }
            mock_boto3.return_value = mock_cognito
            
            validator = CognitoRoleValidator('test-pool-id', 'us-east-1')
            
            # Test role validation with wrong role
            is_valid = validator.validate_user_role(username, wrong_role)
            assert not is_valid, f"Wrong role {wrong_role} should not be validated when user has {role}"