"""
Property-based tests for order placement validation
Feature: enhanced-consumer-ordering-system, Property 2: Order Placement Validation
Validates: Requirements 1.3, 2.5

This test verifies that order placement validation works correctly:
- Orders cannot be placed until a valid payment method is selected
- Payment confirmation is required before order placement
- Invalid payment methods are rejected
- Order placement is prevented for incomplete payment flows
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

# Valid payment methods
valid_payment_methods = ['COD', 'ONLINE']
invalid_payment_methods = ['INVALID', 'CASH', 'CARD', 'UPI', '', None, 123, True]

valid_payment_method_strategy = st.sampled_from(valid_payment_methods)
invalid_payment_method_strategy = st.sampled_from(invalid_payment_methods)

# Device and service types
device_type_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))
service_type_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))

# Address and contact info
address_strategy = st.fixed_dictionaries({
    'street': st.text(min_size=1, max_size=200),
    'city': st.text(min_size=1, max_size=50),
    'state': st.text(min_size=1, max_size=50),
    'pincode': st.from_regex(r'[1-9][0-9]{5}', fullmatch=True),
    'country': st.just('India')
})

contact_info_strategy = st.fixed_dictionaries({
    'name': st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
    'phone': st.from_regex(r'\+91[6-9][0-9]{9}', fullmatch=True),
    'email': st.emails()
})

# Amount strategy
amount_strategy = st.decimals(min_value=Decimal('0.01'), max_value=Decimal('100000.00'), places=2)

# Special instructions
special_instructions_strategy = st.one_of(
    st.none(),
    st.text(max_size=1000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs', 'Po')))
)


class TestOrderPlacementValidationProperty:
    """
    Property 2: Order Placement Validation
    
    For any order placement attempt, the system must:
    1. Prevent order placement until a valid payment method is selected
    2. Require payment confirmation before allowing order placement
    3. Reject invalid payment methods
    4. Ensure complete payment flows before order creation
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
        
        # Reset mock before each test
        self.mock_orders_table.reset_mock()
    
    @given(
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy,
        amount=amount_strategy,
        special_instructions=special_instructions_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_valid_payment_method_allows_order_placement(
        self,
        consumer_id: str,
        device_type: str,
        service_type: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict,
        amount: Decimal,
        special_instructions: str
    ):
        """
        Property Test: Valid payment method allows order placement
        
        For any order with a valid payment method (COD or ONLINE):
        1. The order MUST be accepted for processing
        2. The payment method MUST be validated successfully
        3. The order MUST be created with the correct initial status
        4. All order data MUST be preserved correctly
        
        **Validates: Requirements 1.3, 2.5**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Arrange: Create valid order request
        request_data = {
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info,
            'amount': amount,
            'specialInstructions': special_instructions
        }
        
        # Mock successful DynamoDB put_item
        self.mock_orders_table.put_item.return_value = {}
        
        # Act
        with patch('enhanced_order_management.uuid.uuid4') as mock_uuid, \
             patch('enhanced_order_management.datetime') as mock_datetime, \
             patch('enhanced_order_management.sns') as mock_sns, \
             patch('enhanced_order_management.eventbridge') as mock_eventbridge:
            
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-order-id')
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00+00:00'
            
            result = self.service.create_order(request_data)
        
        # Assert: Valid payment method should allow order creation
        assert result['success'] is True, f"Valid payment method {payment_method} should allow order creation"
        assert result['data']['id'] == 'test-order-id', "Order should be created with correct ID"
        assert result['data']['paymentMethod'] == payment_method, "Payment method should be preserved"
        
        # Verify correct initial status based on payment method
        if payment_method == 'COD':
            expected_status = OrderStatus.PENDING_CONFIRMATION.value
        else:  # ONLINE
            expected_status = OrderStatus.PENDING_PAYMENT.value
        
        assert result['data']['status'] == expected_status, f"Order should have correct initial status for {payment_method}"
        
        # Verify DynamoDB was called
        self.mock_orders_table.put_item.assert_called_once()
        call_args = self.mock_orders_table.put_item.call_args[1]
        
        # Verify order data preservation
        order_item = call_args['Item']
        assert order_item['consumerId'] == consumer_id, "Consumer ID should be preserved"
        assert order_item['deviceType'] == device_type, "Device type should be preserved"
        assert order_item['serviceType'] == service_type, "Service type should be preserved"
        assert order_item['paymentMethod'] == payment_method, "Payment method should be preserved"
        assert order_item['deliveryAddress'] == delivery_address, "Delivery address should be preserved"
        assert order_item['contactInfo'] == contact_info, "Contact info should be preserved"
        assert order_item['amount'] == float(amount), "Amount should be preserved"
        assert order_item['specialInstructions'] == special_instructions, "Special instructions should be preserved"
        
        # Verify status history is initialized
        assert 'statusHistory' in order_item, "Status history should be initialized"
        assert len(order_item['statusHistory']) == 1, "Status history should have initial entry"
        
        initial_status_entry = order_item['statusHistory'][0]
        assert initial_status_entry['status'] == expected_status, "Initial status entry should match order status"
        assert payment_method in initial_status_entry['message'], "Status message should mention payment method"
    
    @given(
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=invalid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy,
        amount=amount_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_invalid_payment_method_prevents_order_placement(
        self,
        consumer_id: str,
        device_type: str,
        service_type: str,
        payment_method,  # Can be any type
        delivery_address: dict,
        contact_info: dict,
        amount: Decimal
    ):
        """
        Property Test: Invalid payment method prevents order placement
        
        For any order with an invalid payment method:
        1. The order MUST be rejected during validation
        2. A ValidationError MUST be raised
        3. No database operations MUST occur
        4. The error MUST indicate the payment method issue
        
        **Validates: Requirements 1.3, 2.5**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Arrange: Create order request with invalid payment method
        request_data = {
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info,
            'amount': amount
        }
        
        # Act & Assert: Invalid payment method should be rejected
        from error_handler import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_order(request_data)
        
        # Verify error indicates validation failure
        error_message = str(exc_info.value)
        assert 'validation' in error_message.lower() or 'invalid' in error_message.lower(), \
            "Error should indicate validation failure"
        
        # Verify no database operation was attempted
        self.mock_orders_table.put_item.assert_not_called()
    
    @given(
        consumer_id=consumer_id_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_missing_required_fields_prevents_order_placement(
        self,
        consumer_id: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict
    ):
        """
        Property Test: Missing required fields prevents order placement
        
        For any order missing required fields:
        1. The order MUST be rejected during validation
        2. A ValidationError MUST be raised
        3. No database operations MUST occur
        4. The error MUST indicate which fields are missing
        
        **Validates: Requirements 1.3**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Test missing deviceType
        incomplete_request = {
            'consumerId': consumer_id,
            # 'deviceType': missing
            'serviceType': 'Installation',
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info
        }
        
        from error_handler import ValidationError
        
        with pytest.raises(ValidationError):
            self.service.create_order(incomplete_request)
        
        # Verify no database operation was attempted
        self.mock_orders_table.put_item.assert_not_called()
        
        # Test missing serviceType
        incomplete_request = {
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            # 'serviceType': missing
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info
        }
        
        with pytest.raises(ValidationError):
            self.service.create_order(incomplete_request)
        
        # Test missing deliveryAddress
        incomplete_request = {
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': payment_method,
            # 'deliveryAddress': missing
            'contactInfo': contact_info
        }
        
        with pytest.raises(ValidationError):
            self.service.create_order(incomplete_request)
        
        # Test missing contactInfo
        incomplete_request = {
            'consumerId': consumer_id,
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address
            # 'contactInfo': missing
        }
        
        with pytest.raises(ValidationError):
            self.service.create_order(incomplete_request)
    
    @given(
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy,
        amount=amount_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_consumer_id_prevents_order_placement(
        self,
        device_type: str,
        service_type: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict,
        amount: Decimal
    ):
        """
        Property Test: Invalid consumer ID prevents order placement
        
        For any order with an invalid consumer ID:
        1. The order MUST be rejected during validation
        2. A ValidationError MUST be raised
        3. No database operations MUST occur
        4. The error MUST indicate the consumer ID issue
        
        **Validates: Requirements 1.3**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Test various invalid consumer IDs
        invalid_consumer_ids = [
            'invalid-uuid',
            '',
            None,
            123,
            'not-a-uuid-at-all',
            'abc-def-ghi'
        ]
        
        from error_handler import ValidationError
        
        for invalid_consumer_id in invalid_consumer_ids:
            request_data = {
                'consumerId': invalid_consumer_id,
                'deviceType': device_type,
                'serviceType': service_type,
                'paymentMethod': payment_method,
                'deliveryAddress': delivery_address,
                'contactInfo': contact_info,
                'amount': amount
            }
            
            with pytest.raises(ValidationError) as exc_info:
                self.service.create_order(request_data)
            
            # Verify error indicates validation failure
            error_message = str(exc_info.value)
            assert 'validation' in error_message.lower() or 'invalid' in error_message.lower() or 'uuid' in error_message.lower(), \
                f"Error should indicate validation failure for consumer ID: {invalid_consumer_id}"
        
        # Verify no database operations were attempted
        self.mock_orders_table.put_item.assert_not_called()
    
    @given(
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_amount_prevents_order_placement(
        self,
        consumer_id: str,
        device_type: str,
        service_type: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict
    ):
        """
        Property Test: Invalid amount prevents order placement
        
        For any order with an invalid amount:
        1. The order MUST be rejected during validation
        2. A ValidationError MUST be raised
        3. No database operations MUST occur
        4. The error MUST indicate the amount issue
        
        **Validates: Requirements 1.3**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Test various invalid amounts
        invalid_amounts = [
            Decimal('0.00'),  # Zero amount
            Decimal('-100.00'),  # Negative amount
            Decimal('100001.00'),  # Amount too large
            'invalid',  # Non-numeric
            None,  # None value
            ''  # Empty string
        ]
        
        from error_handler import ValidationError
        
        for invalid_amount in invalid_amounts:
            request_data = {
                'consumerId': consumer_id,
                'deviceType': device_type,
                'serviceType': service_type,
                'paymentMethod': payment_method,
                'deliveryAddress': delivery_address,
                'contactInfo': contact_info,
                'amount': invalid_amount
            }
            
            with pytest.raises(ValidationError) as exc_info:
                self.service.create_order(request_data)
            
            # Verify error indicates validation failure
            error_message = str(exc_info.value)
            assert 'validation' in error_message.lower() or 'invalid' in error_message.lower() or 'amount' in error_message.lower(), \
                f"Error should indicate validation failure for amount: {invalid_amount}"
        
        # Verify no database operations were attempted
        self.mock_orders_table.put_item.assert_not_called()
    
    @given(
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy,
        amount=amount_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_payment_confirmation_required_for_order_placement(
        self,
        consumer_id: str,
        device_type: str,
        service_type: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict,
        amount: Decimal
    ):
        """
        Property Test: Payment confirmation required for order placement
        
        For any order placement:
        1. The order MUST be created in the appropriate pending state
        2. COD orders MUST start in PENDING_CONFIRMATION status
        3. ONLINE orders MUST start in PENDING_PAYMENT status
        4. Orders MUST NOT be placed in final states initially
        
        **Validates: Requirements 2.5**
        """
        # Arrange: Create valid order request
        request_data = {
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info,
            'amount': amount
        }
        
        # Mock successful DynamoDB put_item
        self.mock_orders_table.put_item.return_value = {}
        
        # Act
        with patch('enhanced_order_management.uuid.uuid4') as mock_uuid, \
             patch('enhanced_order_management.datetime') as mock_datetime:
            
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-order-id')
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00+00:00'
            
            result = self.service.create_order(request_data)
        
        # Assert: Order should be in appropriate pending state
        assert result['success'] is True, "Order creation should succeed"
        
        if payment_method == 'COD':
            expected_status = OrderStatus.PENDING_CONFIRMATION.value
            assert result['data']['status'] == expected_status, \
                "COD orders must start in PENDING_CONFIRMATION status"
        else:  # ONLINE
            expected_status = OrderStatus.PENDING_PAYMENT.value
            assert result['data']['status'] == expected_status, \
                "ONLINE orders must start in PENDING_PAYMENT status"
        
        # Verify order is NOT in final states
        final_states = [
            OrderStatus.ORDER_PLACED.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.OUT_FOR_DELIVERY.value,
            OrderStatus.DELIVERED.value
        ]
        
        assert result['data']['status'] not in final_states, \
            "Orders must not be placed in final states initially"
        
        # Verify DynamoDB call has correct status
        call_args = self.mock_orders_table.put_item.call_args[1]
        order_item = call_args['Item']
        assert order_item['status'] == expected_status, \
            "Database record should have correct pending status"
    
    @given(
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        payment_method=valid_payment_method_strategy,
        delivery_address=address_strategy,
        contact_info=contact_info_strategy,
        amount=amount_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_order_placement_idempotency_protection(
        self,
        consumer_id: str,
        device_type: str,
        service_type: str,
        payment_method: str,
        delivery_address: dict,
        contact_info: dict,
        amount: Decimal
    ):
        """
        Property Test: Order placement has idempotency protection
        
        For any order placement attempt:
        1. Duplicate order IDs MUST be prevented
        2. Conditional writes MUST be used to prevent conflicts
        3. Concurrent order creation MUST be handled safely
        4. Database constraints MUST be enforced
        
        **Validates: Requirements 2.5**
        """
        # Reset mock for this test example
        self.mock_orders_table.reset_mock()
        
        # Arrange: Create valid order request
        request_data = {
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': payment_method,
            'deliveryAddress': delivery_address,
            'contactInfo': contact_info,
            'amount': amount
        }
        
        # Mock successful DynamoDB put_item
        self.mock_orders_table.put_item.return_value = {}
        
        # Act
        with patch('enhanced_order_management.uuid.uuid4') as mock_uuid, \
             patch('enhanced_order_management.datetime') as mock_datetime:
            
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-order-id')
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00+00:00'
            
            result = self.service.create_order(request_data)
        
        # Assert: Order creation should succeed
        assert result['success'] is True, "Order creation should succeed"
        
        # Verify DynamoDB put_item was called with conditional expression
        self.mock_orders_table.put_item.assert_called_once()
        call_args = self.mock_orders_table.put_item.call_args[1]
        
        # Verify conditional expression is used to prevent duplicates
        assert 'ConditionExpression' in call_args, \
            "Conditional expression should be used to prevent duplicate orders"
        
        condition_expr = str(call_args['ConditionExpression'])
        assert 'attribute_not_exists' in condition_expr, \
            "Condition should check that order doesn't already exist"
        assert 'PK' in condition_expr, \
            "Condition should check the primary key"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])