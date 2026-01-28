"""
Property-based tests for order state transitions
Feature: enhanced-consumer-ordering-system, Property 16: State Management Integrity
Validates: Requirements 8.1, 8.2, 8.4, 8.5

This test verifies that order state transitions maintain integrity:
- Valid state transitions are enforced
- State changes are logged with timestamps and user context
- Concurrent state changes are handled using optimistic locking
- Business rules are validated before allowing state transitions
"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import uuid

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
from enhanced_order_management import OrderManagementService, OrderStatus, PaymentMethod


# Hypothesis strategies for generating test data
order_id_strategy = st.uuids().map(str)

consumer_id_strategy = st.uuids().map(str)

# Valid order status transitions based on the business logic
valid_status_pairs = [
    (OrderStatus.PENDING_PAYMENT, OrderStatus.ORDER_PLACED),
    (OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED),
    (OrderStatus.PENDING_PAYMENT, OrderStatus.FAILED),
    (OrderStatus.PENDING_CONFIRMATION, OrderStatus.ORDER_PLACED),
    (OrderStatus.PENDING_CONFIRMATION, OrderStatus.CANCELLED),
    (OrderStatus.ORDER_PLACED, OrderStatus.SHIPPED),
    (OrderStatus.ORDER_PLACED, OrderStatus.CANCELLED),
    (OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY),
    (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
    (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED),
    (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED),
]

# Invalid order status transitions
invalid_status_pairs = [
    (OrderStatus.DELIVERED, OrderStatus.SHIPPED),
    (OrderStatus.DELIVERED, OrderStatus.ORDER_PLACED),
    (OrderStatus.CANCELLED, OrderStatus.ORDER_PLACED),
    (OrderStatus.CANCELLED, OrderStatus.SHIPPED),
    (OrderStatus.FAILED, OrderStatus.ORDER_PLACED),
    (OrderStatus.PENDING_CONFIRMATION, OrderStatus.DELIVERED),
    (OrderStatus.PENDING_PAYMENT, OrderStatus.DELIVERED),
]

valid_transition_strategy = st.sampled_from(valid_status_pairs)
invalid_transition_strategy = st.sampled_from(invalid_status_pairs)

reason_strategy = st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))

version_strategy = st.integers(min_value=1, max_value=1000)

metadata_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
    values=st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    ),
    max_size=5
)


class TestOrderStateTransitionsProperty:
    """
    Property 16: State Management Integrity
    
    For any order state transition attempt, the Order State Manager must:
    1. Enforce valid state transitions and prevent invalid state changes
    2. Log all changes with timestamps and user context
    3. Validate business rules before allowing state transitions
    4. Handle concurrent state changes using optimistic locking
    """
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        os.environ['ENHANCED_ORDERS_TABLE'] = 'test-orders'
        os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
        os.environ['EVENTBRIDGE_BUS'] = 'test-bus'
        
        # Initialize service
        self.service = OrderManagementService()
        
        # Mock AWS clients
        self.mock_orders_table = Mock()
        self.service.orders_table = self.mock_orders_table
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        transition=valid_transition_strategy,
        reason=reason_strategy,
        version=version_strategy,
        metadata=metadata_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_valid_state_transitions_are_enforced(
        self,
        order_id: str,
        consumer_id: str,
        transition: tuple,
        reason: str,
        version: int,
        metadata: dict
    ):
        """
        Property Test: Valid state transitions are enforced
        
        For any valid state transition (current_status -> new_status):
        1. The transition MUST be allowed by the state machine
        2. The order status MUST be updated to the new status
        3. The status history MUST include the new status update
        4. The version MUST be incremented for optimistic locking
        
        **Validates: Requirements 8.1, 8.4**
        """
        current_status, new_status = transition
        
        # Setup: Create current order state with all required fields
        current_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': current_status.value,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [{
                'status': current_status.value,
                'timestamp': '2024-01-01T00:00:00+00:00',
                'message': 'Initial status',
                'metadata': {}
            }],
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock successful update
        updated_order = {
            **current_order,
            'status': new_status.value,
            'version': version + 1,
            'updatedAt': '2024-01-01T01:00:00+00:00'
        }
        self.mock_orders_table.update_item.return_value = {'Attributes': updated_order}
        
        # Reset mock call count
        self.mock_orders_table.update_item.reset_mock()
        
        # Prepare update request
        request_data = {
            'orderId': order_id,
            'status': new_status.value,
            'reason': reason,
            'metadata': metadata
        }
        
        # Act
        with patch('enhanced_order_management.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T01:00:00+00:00'
            
            result = self.service.update_order_status(request_data)
        
        # Assert: Valid transition should succeed
        assert result['success'] is True, f"Valid transition from {current_status.value} to {new_status.value} should succeed"
        assert result['data']['status'] == new_status.value, "Order status should be updated to new status"
        
        # Verify optimistic locking was used (should be called exactly once)
        assert self.mock_orders_table.update_item.call_count == 1, f"Expected update_item to be called once, but was called {self.mock_orders_table.update_item.call_count} times"
        call_args = self.mock_orders_table.update_item.call_args[1]
        
        # Check condition expression for optimistic locking
        assert 'ConditionExpression' in call_args, "Optimistic locking condition should be present"
        assert ':current_version' in call_args['ExpressionAttributeValues'], "Current version should be checked"
        assert call_args['ExpressionAttributeValues'][':current_version'] == version, "Current version should match"
        
        # Check version increment
        assert ':new_version' in call_args['ExpressionAttributeValues'], "New version should be set"
        assert call_args['ExpressionAttributeValues'][':new_version'] == version + 1, "Version should be incremented"
        
        # Check status history update
        assert ':status_history' in call_args['ExpressionAttributeValues'], "Status history should be updated"
        status_history = call_args['ExpressionAttributeValues'][':status_history']
        
        # Verify new status entry was added
        assert len(status_history) == 2, "Status history should have original + new entry"
        new_entry = status_history[-1]  # Last entry should be the new one
        assert new_entry['status'] == new_status.value, "New status entry should have correct status"
        
        # The reason gets URL-encoded by the input validator for security
        import urllib.parse
        expected_reason = urllib.parse.quote(reason, safe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~')
        assert new_entry['message'] == expected_reason, f"New status entry should have the URL-encoded reason. Expected: '{expected_reason}', Got: '{new_entry['message']}'"
        assert new_entry['metadata'] == metadata, "New status entry should have the provided metadata"
        assert 'timestamp' in new_entry, "New status entry should have timestamp"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        transition=invalid_transition_strategy,
        reason=reason_strategy,
        version=version_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_invalid_state_transitions_are_prevented(
        self,
        order_id: str,
        consumer_id: str,
        transition: tuple,
        reason: str,
        version: int
    ):
        """
        Property Test: Invalid state transitions are prevented
        
        For any invalid state transition (current_status -> new_status):
        1. The transition MUST be rejected by the state machine
        2. A BusinessRuleViolationError MUST be raised
        3. No database updates MUST occur
        4. The order state MUST remain unchanged
        
        **Validates: Requirements 8.1, 8.4**
        """
        current_status, new_status = transition
        
        # Setup: Create current order state with all required fields
        current_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': current_status.value,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [{
                'status': current_status.value,
                'timestamp': '2024-01-01T00:00:00+00:00',
                'message': 'Initial status',
                'metadata': {}
            }]
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Prepare update request
        request_data = {
            'orderId': order_id,
            'status': new_status.value,
            'reason': reason
        }
        
        # Act & Assert: Invalid transition should be rejected
        from error_handler import BusinessRuleViolationError
        
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.update_order_status(request_data)
        
        # Verify error message contains transition information
        error_message = str(exc_info.value)
        assert 'Invalid state transition' in error_message, "Error should mention invalid state transition"
        assert current_status.value in error_message, "Error should mention current status"
        assert new_status.value in error_message, "Error should mention target status"
        
        # Verify no database update was attempted
        self.mock_orders_table.update_item.assert_not_called()
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        transition=valid_transition_strategy,
        reason=reason_strategy,
        version=version_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_concurrent_state_changes_handled_with_optimistic_locking(
        self,
        order_id: str,
        consumer_id: str,
        transition: tuple,
        reason: str,
        version: int
    ):
        """
        Property Test: Concurrent state changes are handled using optimistic locking
        
        For any concurrent state change attempt:
        1. The first update MUST succeed if the version matches
        2. The second update MUST fail with ConflictError due to version mismatch
        3. The failed update MUST not modify the order state
        4. The system MUST remain in a consistent state
        
        **Validates: Requirements 8.4, 8.5**
        """
        current_status, new_status = transition
        
        # Setup: Create current order state with all required fields
        current_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': current_status.value,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [],
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock ConditionalCheckFailedException for optimistic locking conflict
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ConditionalCheckFailedException',
                'Message': 'The conditional request failed'
            }
        }
        self.mock_orders_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        
        # Reset call count
        self.mock_orders_table.update_item.reset_mock()
        
        # Prepare update request
        request_data = {
            'orderId': order_id,
            'status': new_status.value,
            'reason': reason
        }
        
        # Act & Assert: Concurrent update should fail with ConflictError
        from error_handler import ConflictError
        
        with pytest.raises(ConflictError) as exc_info:
            self.service.update_order_status(request_data)
        
        # Verify error message indicates concurrent modification
        error_message = str(exc_info.value)
        assert 'modified by another process' in error_message, "Error should indicate concurrent modification"
        
        # Verify optimistic locking was attempted
        self.mock_orders_table.update_item.assert_called_once()
        call_args = self.mock_orders_table.update_item.call_args[1]
        assert 'ConditionExpression' in call_args, "Optimistic locking condition should be present"
        assert ':current_version' in call_args['ExpressionAttributeValues'], "Current version should be checked"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        transition=valid_transition_strategy,
        reason=reason_strategy,
        version=version_strategy,
        metadata=metadata_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_state_changes_logged_with_timestamps_and_context(
        self,
        order_id: str,
        consumer_id: str,
        transition: tuple,
        reason: str,
        version: int,
        metadata: dict
    ):
        """
        Property Test: State changes are logged with timestamps and user context
        
        For any successful state transition:
        1. The status history MUST be updated with the new entry
        2. The entry MUST contain the new status, timestamp, reason, and metadata
        3. The timestamp MUST be in ISO format
        4. The entry MUST preserve all provided context information
        
        **Validates: Requirements 8.2**
        """
        current_status, new_status = transition
        
        # Setup: Create current order state with existing history
        existing_history = [{
            'status': current_status.value,
            'timestamp': '2024-01-01T00:00:00+00:00',
            'message': 'Initial status',
            'metadata': {}
        }]
        
        # Setup: Create current order state with all required fields
        current_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': current_status.value,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': existing_history.copy(),
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock successful update
        updated_order = {**current_order, 'status': new_status.value, 'version': version + 1}
        self.mock_orders_table.update_item.return_value = {'Attributes': updated_order}
        
        # Prepare update request
        request_data = {
            'orderId': order_id,
            'status': new_status.value,
            'reason': reason,
            'metadata': metadata
        }
        
        # Act
        fixed_timestamp = '2024-01-01T01:00:00+00:00'
        with patch('enhanced_order_management.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = fixed_timestamp
            
            result = self.service.update_order_status(request_data)
        
        # Assert: Status history should be properly updated
        call_args = self.mock_orders_table.update_item.call_args[1]
        status_history = call_args['ExpressionAttributeValues'][':status_history']
        
        # Verify history length increased
        assert len(status_history) == len(existing_history) + 1, "Status history should have one more entry"
        
        # Verify new entry content
        new_entry = status_history[-1]  # Last entry should be the new one
        assert new_entry['status'] == new_status.value, "New entry should have correct status"
        assert new_entry['timestamp'] == fixed_timestamp, "New entry should have correct timestamp"
        
        # The reason gets URL-encoded by the input validator for security
        import urllib.parse
        expected_reason = urllib.parse.quote(reason, safe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~')
        assert new_entry['message'] == expected_reason, "New entry should have URL-encoded reason"
        assert new_entry['metadata'] == metadata, "New entry should have provided metadata"
        
        # Verify timestamp format (ISO 8601)
        timestamp = new_entry['timestamp']
        assert 'T' in timestamp, "Timestamp should be in ISO format with T separator"
        assert timestamp.endswith('+00:00') or timestamp.endswith('Z'), "Timestamp should include timezone"
        
        # Verify existing history is preserved
        for i, original_entry in enumerate(existing_history):
            assert status_history[i] == original_entry, f"Original history entry {i} should be preserved"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        version=version_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_business_rules_validated_before_state_transitions(
        self,
        order_id: str,
        consumer_id: str,
        version: int
    ):
        """
        Property Test: Business rules are validated before allowing state transitions
        
        For any state transition attempt:
        1. The current order MUST exist before transition is allowed
        2. The transition MUST be validated against business rules
        3. Invalid transitions MUST be rejected before any database operations
        4. Valid transitions MUST only proceed after all validations pass
        
        **Validates: Requirements 8.1, 8.5**
        """
        # Test case 1: Order not found
        self.service._get_order_by_id = Mock(return_value=None)
        
        # Reset mock call count
        self.mock_orders_table.update_item.reset_mock()
        
        request_data = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'reason': 'Test transition'
        }
        
        # Act & Assert: Non-existent order should be rejected
        from error_handler import ResourceNotFoundError
        
        with pytest.raises(ResourceNotFoundError) as exc_info:
            self.service.update_order_status(request_data)
        
        # Verify error indicates order not found
        error_message = str(exc_info.value)
        assert 'Order' in error_message, "Error should mention Order"
        assert order_id in error_message or 'not found' in error_message.lower(), "Error should include order ID or 'not found'"
        
        # Verify no database update was attempted
        self.mock_orders_table.update_item.assert_not_called()
        
        # Test case 2: Valid business rule validation
        # Setup: Create order in valid state for transition with all required fields
        current_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': OrderStatus.PENDING_CONFIRMATION.value,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [],
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock get order to return valid order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock successful update
        updated_order = {**current_order, 'status': OrderStatus.ORDER_PLACED.value, 'version': version + 1}
        self.mock_orders_table.update_item.return_value = {'Attributes': updated_order}
        
        # Act: Valid transition should succeed
        with patch('enhanced_order_management.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T01:00:00+00:00'
            
            result = self.service.update_order_status(request_data)
        
        # Assert: Valid business rule should allow transition
        assert result['success'] is True, "Valid business rule should allow transition"
        
        # Verify database update was attempted after validation
        self.mock_orders_table.update_item.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])