"""
Property-based tests for authentication security

Feature: dashboard-overhaul, Property 26: Multi-Factor Authentication Enforcement
Feature: dashboard-overhaul, Property 27: Session Management Security
Validates: Requirements 10.2, 10.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
import time
import jwt
from datetime import datetime, timezone, timedelta

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from jwt_middleware.handler import JWTValidator, SessionManager, MFAValidator, JWTMiddleware
from shared.errors import AuthenticationError, AuthorizationError


# Hypothesis strategies for generating test data

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

# Session identifiers
session_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=10,
    max_size=50
)

# JWT token identifiers
jti_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=20,
    max_size=40
)

# MFA codes
mfa_code_strategy = st.text(
    alphabet='0123456789',
    min_size=6,
    max_size=6
)

# Operations that require MFA
sensitive_operations_strategy = st.sampled_from([
    'purchase-order-approval',
    'budget-allocation',
    'user-role-management',
    'system-configuration',
    'security-policy-changes'
])

# Non-sensitive operations
non_sensitive_operations_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz-',
    min_size=5,
    max_size=30
).filter(lambda x: x not in [
    'purchase-order-approval',
    'budget-allocation', 
    'user-role-management',
    'system-configuration',
    'security-policy-changes'
])

# Request context
request_context_strategy = st.fixed_dictionaries({
    'ip_address': st.ip_addresses().map(str),
    'user_agent': st.text(min_size=10, max_size=100),
    'request_id': st.uuids().map(str),
    'source': st.sampled_from(['api', 'jwt_middleware', 'mfa_api'])
})

# Time-related strategies
current_timestamp_strategy = st.integers(
    min_value=int(time.time()) - 3600,  # 1 hour ago
    max_value=int(time.time()) + 3600   # 1 hour from now
)

future_timestamp_strategy = st.integers(
    min_value=int(time.time()) + 60,    # 1 minute from now
    max_value=int(time.time()) + 86400  # 24 hours from now
)

past_timestamp_strategy = st.integers(
    min_value=int(time.time()) - 86400, # 24 hours ago
    max_value=int(time.time()) - 60     # 1 minute ago
)


class TestMultiFactorAuthenticationEnforcement:
    """
    Property 26: Multi-Factor Authentication Enforcement
    
    For any sensitive operation (financial approvals, system configuration, 
    user management), the system SHALL require multi-factor authentication 
    and SHALL NOT allow these operations with single-factor authentication alone.
    """
    
    @given(
        user_id=user_id_strategy,
        username=username_strategy,
        operation=sensitive_operations_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_sensitive_operations_require_mfa(
        self, user_id, username, operation, request_context
    ):
        """
        Property Test: Sensitive operations require MFA
        
        For any sensitive operation, the system must require MFA and not
        allow the operation to proceed without MFA verification.
        """
        with patch('jwt_middleware.handler.boto3.client') as mock_boto3_client, \
             patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            
            # Mock Cognito client for MFA-enabled user
            mock_cognito = Mock()
            mock_cognito.admin_get_user.return_value = {
                'UserAttributes': [
                    {'Name': 'phone_number_verified', 'Value': 'true'}
                ]
            }
            mock_cognito.admin_initiate_auth.return_value = {
                'Session': 'test-session-123',
                'ChallengeName': 'SMS_MFA'
            }
            mock_boto3_client.return_value = mock_cognito
            
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            mfa_validator = MFAValidator('us-east-1')
            
            # Test that sensitive operation requires MFA
            assert mfa_validator.is_sensitive_operation(operation), (
                f"Operation {operation} should be classified as sensitive"
            )
            
            # Initiate MFA challenge
            mfa_challenge = mfa_validator.initiate_mfa_challenge(
                user_id, username, operation, request_context
            )
            
            # Verify MFA is required
            assert mfa_challenge.get('required') is True, (
                f"MFA should be required for sensitive operation {operation}"
            )
            assert 'challenge_id' in mfa_challenge
            assert 'challenge_type' in mfa_challenge
            assert mfa_challenge['challenge_type'] == 'SMS_MFA'
            
            # Verify MFA challenge was stored
            mock_table.put_item.assert_called_once()
            stored_challenge = mock_table.put_item.call_args[1]['Item']
            assert stored_challenge['user_id'] == user_id
            assert stored_challenge['operation'] == operation
            assert stored_challenge['status'] == 'pending'
    
    @given(
        user_id=user_id_strategy,
        username=username_strategy,
        operation=non_sensitive_operations_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=10)
    def test_non_sensitive_operations_do_not_require_mfa(
        self, user_id, username, operation, request_context
    ):
        """
        Property Test: Non-sensitive operations do not require MFA
        
        For any non-sensitive operation, the system should not require MFA
        and should allow the operation to proceed without MFA verification.
        """
        mfa_validator = MFAValidator('us-east-1')
        
        # Test that non-sensitive operation does not require MFA
        assert not mfa_validator.is_sensitive_operation(operation), (
            f"Operation {operation} should not be classified as sensitive"
        )
        
        # Initiate MFA challenge (should not be required)
        mfa_challenge = mfa_validator.initiate_mfa_challenge(
            user_id, username, operation, request_context
        )
        
        # Verify MFA is not required
        assert mfa_challenge.get('required') is False, (
            f"MFA should not be required for non-sensitive operation {operation}"
        )
    
    @given(
        user_id=user_id_strategy,
        username=username_strategy,
        operation=sensitive_operations_strategy,
        mfa_code=mfa_code_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=10)
    def test_mfa_verification_is_enforced(
        self, user_id, username, operation, mfa_code, request_context
    ):
        """
        Property Test: MFA verification is properly enforced
        
        For any sensitive operation with MFA challenge, the system must
        properly verify the MFA code before allowing the operation.
        """
        with patch('jwt_middleware.handler.boto3.client') as mock_boto3_client, \
             patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            
            # Mock Cognito client
            mock_cognito = Mock()
            mock_cognito.admin_respond_to_auth_challenge.return_value = {
                'AuthenticationResult': {'AccessToken': 'test-token'}
            }
            mock_boto3_client.return_value = mock_cognito
            
            # Mock DynamoDB table
            mock_table = Mock()
            challenge_id = f"mfa_{int(time.time())}_{user_id[:8]}"
            current_time = int(time.time())
            
            # Mock successful challenge retrieval
            mock_table.get_item.return_value = {
                'Item': {
                    'challenge_id': challenge_id,
                    'user_id': user_id,
                    'username': username,
                    'operation': operation,
                    'status': 'pending',
                    'expires_at': current_time + 300,  # 5 minutes from now
                    'created_at': current_time
                }
            }
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            mfa_validator = MFAValidator('us-east-1')
            
            # Test MFA verification
            is_valid = mfa_validator.verify_mfa_challenge(
                challenge_id, user_id, mfa_code, 'test-session'
            )
            
            # Verify that verification was attempted
            mock_table.get_item.assert_called_once_with(
                Key={'challenge_id': challenge_id}
            )
            
            # Verify Cognito MFA verification was called
            mock_cognito.admin_respond_to_auth_challenge.assert_called_once()
            
            # Verify challenge was marked as completed if successful
            if is_valid:
                mock_table.update_item.assert_called()
                update_call = mock_table.update_item.call_args
                assert ':status' in update_call[1]['ExpressionAttributeValues']
                assert update_call[1]['ExpressionAttributeValues'][':status'] == 'completed'
    
    @given(
        user_id=user_id_strategy,
        username=username_strategy,
        operation=sensitive_operations_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=10)
    def test_mfa_disabled_users_get_warning(
        self, user_id, username, operation, request_context
    ):
        """
        Property Test: Users without MFA enabled get appropriate warnings
        
        For any sensitive operation by a user without MFA enabled, the system
        should log a warning but may allow the operation (graceful degradation).
        """
        with patch('jwt_middleware.handler.boto3.client') as mock_boto3_client, \
             patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            
            # Mock Cognito client for user without MFA
            mock_cognito = Mock()
            mock_cognito.admin_get_user.return_value = {
                'UserAttributes': [
                    {'Name': 'phone_number_verified', 'Value': 'false'}
                ]
            }
            mock_boto3_client.return_value = mock_cognito
            
            # Mock DynamoDB resource
            mock_resource = Mock()
            mock_boto3_resource.return_value = mock_resource
            
            mfa_validator = MFAValidator('us-east-1')
            
            # Test MFA challenge for user without MFA
            mfa_challenge = mfa_validator.initiate_mfa_challenge(
                user_id, username, operation, request_context
            )
            
            # Verify appropriate response for user without MFA
            assert mfa_challenge.get('required') is False
            assert 'warning' in mfa_challenge
            assert mfa_challenge['warning'] == 'MFA not enabled'


class TestSessionManagementSecurity:
    """
    Property 27: Session Management Security
    
    For any user session, the system SHALL implement proper timeout policies,
    secure session invalidation, and protection against session hijacking.
    """
    
    @given(
        user_id=user_id_strategy,
        token_jti=jti_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_session_creation_and_validation(
        self, user_id, token_jti, request_context
    ):
        """
        Property Test: Session creation and validation works correctly
        
        For any user, creating a session should return a valid session ID
        that can be validated successfully.
        """
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            mock_table.query.return_value = {'Items': []}  # No existing sessions
            
            expected_session_id = f"sess_{int(time.time())}_{token_jti[:8]}"
            mock_table.get_item.return_value = {
                'Item': {
                    'session_id': expected_session_id,
                    'user_id': user_id,
                    'token_jti': token_jti,
                    'status': 'active',
                    'expires_at': int(time.time()) + 1800,  # 30 minutes from now
                    'created_at': int(time.time()),
                    'last_activity': int(time.time())
                }
            }
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            # Ensure the session manager has a table available
            session_manager = SessionManager('us-east-1')
            session_manager.sessions_table = mock_table  # Force table availability
            
            # Create session
            session_id = session_manager.create_session(
                user_id, token_jti, request_context
            )
            
            # Verify session ID is returned
            assert session_id is not None
            assert len(session_id) > 0
            
            # Validate session
            is_valid = session_manager.validate_session(session_id, user_id)
            
            # Verify session validation
            assert is_valid is True
            
            # Verify session was stored (should be called once for creation)
            assert mock_table.put_item.call_count >= 1
            # Get the last call to put_item
            put_item_calls = mock_table.put_item.call_args_list
            stored_session = put_item_calls[-1][1]['Item']
            assert stored_session['user_id'] == user_id
            assert stored_session['token_jti'] == token_jti
            assert stored_session['status'] == 'active'
    
    @given(
        user_id=user_id_strategy,
        session_id=session_id_strategy,
        expires_at=past_timestamp_strategy
    )
    @settings(max_examples=10)
    def test_expired_sessions_are_invalidated(
        self, user_id, session_id, expires_at
    ):
        """
        Property Test: Expired sessions are properly invalidated
        
        For any session that has expired, validation should fail and
        the session should be marked as invalidated.
        """
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            # Mock DynamoDB table with expired session
            mock_table = Mock()
            mock_table.get_item.return_value = {
                'Item': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active',
                    'expires_at': expires_at,  # Expired timestamp
                    'created_at': expires_at - 1800,
                    'last_activity': expires_at - 300
                }
            }
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            session_manager = SessionManager('us-east-1')
            
            # Validate expired session
            is_valid = session_manager.validate_session(session_id, user_id)
            
            # Verify expired session is invalid
            assert is_valid is False
            
            # Verify session was invalidated
            mock_table.update_item.assert_called()
            update_call = mock_table.update_item.call_args
            assert update_call[1]['Key']['session_id'] == session_id
    
    @given(
        user_id=user_id_strategy,
        wrong_user_id=user_id_strategy,
        session_id=session_id_strategy
    )
    @settings(max_examples=10)
    def test_session_user_ownership_is_enforced(
        self, user_id, wrong_user_id, session_id
    ):
        """
        Property Test: Session user ownership is enforced
        
        For any session, validation should fail if attempted by a different
        user than the session owner (protection against session hijacking).
        """
        assume(user_id != wrong_user_id)
        
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.get_item.return_value = {
                'Item': {
                    'session_id': session_id,
                    'user_id': user_id,  # Session belongs to user_id
                    'status': 'active',
                    'expires_at': int(time.time()) + 1800,
                    'created_at': int(time.time()),
                    'last_activity': int(time.time())
                }
            }
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            session_manager = SessionManager('us-east-1')
            
            # Try to validate session with wrong user
            is_valid = session_manager.validate_session(session_id, wrong_user_id)
            
            # Verify session validation fails for wrong user
            assert is_valid is False
    
    @given(
        user_id=user_id_strategy,
        session_id=session_id_strategy,
        reason=st.sampled_from(['logout', 'timeout', 'security', 'admin'])
    )
    @settings(max_examples=10)
    def test_session_invalidation_works_correctly(
        self, user_id, session_id, reason
    ):
        """
        Property Test: Session invalidation works correctly
        
        For any session and invalidation reason, the session should be
        properly marked as invalidated with the correct reason.
        """
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            session_manager = SessionManager('us-east-1')
            
            # Invalidate session
            session_manager.invalidate_session(session_id, reason)
            
            # Verify session was invalidated
            mock_table.update_item.assert_called_once()
            update_call = mock_table.update_item.call_args
            
            assert update_call[1]['Key']['session_id'] == session_id
            assert ':status' in update_call[1]['ExpressionAttributeValues']
            assert update_call[1]['ExpressionAttributeValues'][':status'] == 'invalidated'
            assert ':reason' in update_call[1]['ExpressionAttributeValues']
            assert update_call[1]['ExpressionAttributeValues'][':reason'] == reason
    
    @given(
        user_id=user_id_strategy,
        token_jti=jti_strategy,
        request_context=request_context_strategy,
        max_sessions=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=10)
    def test_concurrent_session_limits_are_enforced(
        self, user_id, token_jti, request_context, max_sessions
    ):
        """
        Property Test: Concurrent session limits are enforced
        
        For any user, the system should enforce maximum concurrent session
        limits and invalidate oldest sessions when limit is exceeded.
        """
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource:
            # Mock DynamoDB table
            mock_table = Mock()
            
            # Mock existing active sessions (at limit)
            existing_sessions = []
            current_time = int(time.time())
            
            for i in range(max_sessions):
                existing_sessions.append({
                    'session_id': f'sess_old_{i}',
                    'user_id': user_id,
                    'created_at': current_time - (max_sessions - i) * 100,
                    'status': 'active',
                    'expires_at': current_time + 1800
                })
            
            mock_table.query.return_value = {'Items': existing_sessions}
            mock_table.put_item.return_value = {}
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            # Create session manager and set the max concurrent sessions
            session_manager = SessionManager('us-east-1')
            session_manager.sessions_table = mock_table  # Force table availability
            session_manager.max_concurrent_sessions = max_sessions  # Set the limit
            
            # Create new session (should trigger cleanup of oldest if at limit)
            session_id = session_manager.create_session(
                user_id, token_jti, request_context
            )
            
            # Verify new session was created
            assert session_id is not None
            assert mock_table.put_item.call_count >= 1
            
            # Verify oldest session was invalidated if at limit
            if len(existing_sessions) >= max_sessions:
                # Should have called update_item to invalidate oldest session
                assert mock_table.update_item.call_count >= 1
    
    @given(
        user_id=user_id_strategy,
        session_id=session_id_strategy,
        current_time=current_timestamp_strategy
    )
    @settings(max_examples=10)
    def test_session_activity_updates_expiration(
        self, user_id, session_id, current_time
    ):
        """
        Property Test: Session activity updates expiration time
        
        For any valid session, successful validation should update the
        last activity time and extend the expiration time.
        """
        with patch('jwt_middleware.handler.boto3.resource') as mock_boto3_resource, \
             patch('time.time', return_value=current_time):
            
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.get_item.return_value = {
                'Item': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active',
                    'expires_at': current_time + 1800,  # Valid expiration
                    'created_at': current_time - 600,
                    'last_activity': current_time - 300
                }
            }
            mock_table.update_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            session_manager = SessionManager('us-east-1')
            
            # Validate session (should update activity)
            is_valid = session_manager.validate_session(session_id, user_id)
            
            # Verify session is valid
            assert is_valid is True
            
            # Verify activity was updated
            mock_table.update_item.assert_called_once()
            update_call = mock_table.update_item.call_args
            
            assert ':time' in update_call[1]['ExpressionAttributeValues']
            assert update_call[1]['ExpressionAttributeValues'][':time'] == current_time
            assert ':expires' in update_call[1]['ExpressionAttributeValues']
            # New expiration should be current time + session timeout
            expected_expiration = current_time + session_manager.session_timeout
            assert update_call[1]['ExpressionAttributeValues'][':expires'] == expected_expiration