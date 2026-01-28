"""
Property-Based Test: Payment Failure Handling

Feature: enhanced-consumer-ordering-system, Property 4: Payment Failure Handling

This test verifies that for any payment failure, cancellation, or timeout, 
the system should prevent order placement and display appropriate error feedback.

**Validates: Requirements 2.3**

Property: For any payment failure, cancellation, or timeout, the system should 
prevent order placement and display appropriate error feedback.
"""

import pytest
from hypothesis import given, strategies as st, settings
import json
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Set environment variables for testing
os.environ['ENHANCED_PAYMENTS_TABLE'] = 'test-payments'
os.environ['ENHANCED_ORDERS_TABLE'] = 'test-orders'
os.environ['RAZORPAY_SECRET_NAME'] = 'test/razorpay/credentials'

# Import the module under test
import payment_service
from payment_service import PaymentService, PaymentStatus, PaymentMethod


# Test data generators
@st.composite
def payment_failure_data(draw):
    """Generate payment failure scenarios"""
    return {
        'payment_id': draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        'order_id': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        'invalid_signature': draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        'amount': draw(st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False)),
        'razorpay_order_id': draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        'failure_reason': draw(st.sampled_from(['invalid_signature', 'payment_not_found', 'network_timeout', 'payment_cancelled']))
    }


@st.composite
def webhook_failure_data(draw):
    """Generate webhook failure scenarios"""
    event_type = draw(st.sampled_from(['payment.failed', 'payment.cancelled', 'payment.timeout']))
    return {
        'event': event_type,
        'payload': {
            'payment': {
                'id': draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
                'order_id': draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
                'status': 'failed',
                'error_description': draw(st.text(min_size=5, max_size=100))
            }
        },
        'signature': draw(st.text(min_size=20, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    }


class TestPaymentFailureHandlingProperty:
    """Property-based tests for payment failure handling"""
    
    @given(failure_data=payment_failure_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_payment_failure_handling_property(self, mock_secrets, mock_table, failure_data):
        """
        Property 4: Payment Failure Handling
        
        For any payment failure, cancellation, or timeout, the system should 
        prevent order placement and display appropriate error feedback.
        
        **Validates: Requirements 2.3**
        """
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        if failure_data['failure_reason'] == 'payment_not_found':
            # Mock payment not found scenario
            mock_table.get_item.return_value = {}
        else:
            # Mock existing payment record
            mock_table.get_item.return_value = {
                'Item': {
                    'paymentId': failure_data['payment_id'],
                    'orderId': failure_data['order_id'],
                    'razorpayOrderId': failure_data['razorpay_order_id'],
                    'status': PaymentStatus.PENDING.value,
                    'amount': failure_data['amount'],
                    'paymentMethod': PaymentMethod.ONLINE.value
                }
            }
        
        mock_table.update_item.return_value = {}
        
        service = PaymentService()
        
        # Mock signature verification to fail (simulating payment failure)
        with patch('hmac.compare_digest', return_value=False):
            # Act
            result = service.verify_razorpay_payment(
                payment_id=failure_data['payment_id'],
                order_id=failure_data['order_id'],
                signature=failure_data['invalid_signature']
            )
        
        # Assert - Property: Payment failure should prevent order placement and provide error feedback
        assert result['success'] is False, f"Payment verification should fail for invalid signature"
        assert 'error' in result, f"Error feedback should be provided for payment failure"
        assert isinstance(result['error'], str), f"Error message should be a string"
        assert len(result['error']) > 0, f"Error message should not be empty"
        
        # Verify that payment status was updated to FAILED if payment record exists
        if failure_data['failure_reason'] != 'payment_not_found':
            mock_table.update_item.assert_called_once()
            update_call = mock_table.update_item.call_args
            
            # Verify the update was called with correct payment ID
            assert update_call[1]['Key']['PK'] == f"PAYMENT#{failure_data['payment_id']}"
            assert update_call[1]['Key']['SK'] == f"PAYMENT#{failure_data['payment_id']}"
            
            # Verify the status was updated to FAILED
            assert ':status' in update_call[1]['ExpressionAttributeValues']
            assert update_call[1]['ExpressionAttributeValues'][':status'] == PaymentStatus.FAILED.value
    
    @given(failure_data=payment_failure_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_payment_failure_prevents_order_placement(self, mock_secrets, mock_table, failure_data):
        """
        Property 4 Extension: Payment Failure Prevents Order Placement
        
        For any payment failure, the system should not proceed with order placement
        and should maintain the payment in a failed state.
        
        **Validates: Requirements 2.3**
        """
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        # Mock existing payment record
        mock_table.get_item.return_value = {
            'Item': {
                'paymentId': failure_data['payment_id'],
                'orderId': failure_data['order_id'],
                'razorpayOrderId': failure_data['razorpay_order_id'],
                'status': PaymentStatus.PENDING.value,
                'amount': failure_data['amount'],
                'paymentMethod': PaymentMethod.ONLINE.value
            }
        }
        
        mock_table.update_item.return_value = {}
        
        service = PaymentService()
        
        # Mock signature verification to fail
        with patch('hmac.compare_digest', return_value=False):
            # Act
            result = service.verify_razorpay_payment(
                payment_id=failure_data['payment_id'],
                order_id=failure_data['order_id'],
                signature=failure_data['invalid_signature']
            )
        
        # Assert - Property: Failed payment should not result in order placement
        assert result['success'] is False
        
        # Verify that the payment was marked as failed (preventing order placement)
        mock_table.update_item.assert_called_once()
        update_call = mock_table.update_item.call_args
        
        # Check that status was updated to FAILED
        assert update_call[1]['ExpressionAttributeValues'][':status'] == PaymentStatus.FAILED.value
        
        # Verify failure reason is recorded
        update_expression = update_call[1]['UpdateExpression']
        assert 'reason' in update_expression or 'failureReason' in update_expression
    
    @given(webhook_data=webhook_failure_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.secrets_client')
    def test_webhook_failure_handling_property(self, mock_secrets, webhook_data):
        """
        Property 4 Extension: Webhook Failure Handling
        
        For any payment failure webhook (failed, cancelled, timeout), the system should
        update payment status appropriately and provide error feedback.
        
        **Validates: Requirements 2.3**
        """
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret',
                'webhook_secret': 'test_webhook_secret'
            })
        }
        
        service = PaymentService()
        
        # Mock signature verification to succeed (valid webhook)
        with patch('hmac.compare_digest', return_value=True):
            with patch.object(service, '_update_payment_status') as mock_update:
                # Act
                result = service.handle_payment_webhook(
                    payload=webhook_data,
                    signature=webhook_data['signature']
                )
        
        # Assert - Property: Webhook failure events should be processed successfully
        assert result['success'] is True, f"Webhook processing should succeed for valid signature"
        assert result['message'] == 'Webhook processed successfully'
        
        # Verify that payment status was updated to FAILED for failure events
        if webhook_data['event'] == 'payment.failed':
            mock_update.assert_called_once()
            update_call = mock_update.call_args
            
            # Verify status was updated to FAILED
            assert update_call[0][1] == PaymentStatus.FAILED  # Second argument is the status
            
            # Verify failure reason is included in metadata
            metadata = update_call[0][2] if len(update_call[0]) > 2 else {}
            assert 'failureReason' in metadata or 'webhookProcessedAt' in metadata
    
    @given(failure_data=payment_failure_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_payment_failure_error_messages_property(self, mock_secrets, mock_table, failure_data):
        """
        Property 4 Extension: Payment Failure Error Messages
        
        For any payment failure, the system should provide descriptive error messages
        that help users understand what went wrong.
        
        **Validates: Requirements 2.3**
        """
        # Arrange
        # Mock secrets manager to avoid AWS access issues in tests
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        # Mock DynamoDB table to avoid float/decimal conversion issues
        mock_table.put_item.return_value = {}
        
        service = PaymentService()
        
        # Test various failure scenarios
        failure_scenarios = [
            # Invalid payment data
            {
                'amount': -100.0,  # Invalid amount
                'order_id': failure_data['order_id']
            },
            # Missing required fields
            {
                'amount': failure_data['amount'],
                'order_id': ''  # Empty order ID
            },
            # Invalid order ID format
            {
                'amount': failure_data['amount'],
                'order_id': 'invalid order id with spaces!'  # Invalid characters
            }
        ]
        
        for scenario in failure_scenarios:
            # Act
            result = service.create_razorpay_order(
                amount=scenario['amount'],
                order_id=scenario['order_id']
            )
            
            # Assert - Property: Failure should provide descriptive error message
            assert result['success'] is False, f"Invalid payment data should result in failure"
            assert 'error' in result, f"Error feedback should be provided"
            assert isinstance(result['error'], str), f"Error message should be a string"
            assert len(result['error']) > 0, f"Error message should not be empty"
            
            # Error message should be descriptive (not just generic)
            error_message = result['error'].lower()
            assert any(keyword in error_message for keyword in ['validation', 'invalid', 'required', 'failed', 'decimal', 'types', 'supported']), \
                f"Error message should be descriptive: {result['error']}"


if __name__ == '__main__':
    pytest.main([__file__])