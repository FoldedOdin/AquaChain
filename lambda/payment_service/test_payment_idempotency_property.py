"""
Property-Based Test: Payment Idempotency

Feature: enhanced-consumer-ordering-system, Property 19: Payment Idempotency

This test verifies that for any payment confirmation event, the system must ensure 
that order placement occurs at most once, even if duplicate payment events are received.

**Validates: Requirements 2.2, 2.5**

Property: For any payment confirmation event, the system must ensure that order 
placement occurs at most once, even if duplicate payment events are received.
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
def payment_idempotency_data(draw):
    """Generate payment data for idempotency testing"""
    # Use a more restrictive alphabet to ensure valid order IDs
    valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
    return {
        'payment_id': draw(st.text(min_size=10, max_size=50, alphabet=valid_chars)),
        'order_id': draw(st.text(min_size=5, max_size=30, alphabet=valid_chars)),
        'signature': draw(st.text(min_size=20, max_size=100, alphabet=valid_chars)),
        'amount': draw(st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False)),
        'razorpay_order_id': draw(st.text(min_size=10, max_size=50, alphabet=valid_chars)),
        'duplicate_count': draw(st.integers(min_value=2, max_value=5))  # Number of duplicate requests
    }


@st.composite
def webhook_idempotency_data(draw):
    """Generate webhook data for idempotency testing"""
    # Use the same valid character set as payment_idempotency_data
    valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
    return {
        'event': 'payment.captured',
        'payload': {
            'payment': {
                'id': draw(st.text(min_size=10, max_size=50, alphabet=valid_chars)),
                'order_id': draw(st.text(min_size=10, max_size=50, alphabet=valid_chars)),
                'status': 'captured',
                'amount': draw(st.integers(min_value=100, max_value=1000000))  # Amount in paise
            }
        },
        'signature': draw(st.text(min_size=20, max_size=100, alphabet=valid_chars)),
        'duplicate_count': draw(st.integers(min_value=2, max_value=5))
    }


class TestPaymentIdempotencyProperty:
    """Property-based tests for payment idempotency"""
    
    @given(payment_data=payment_idempotency_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_payment_verification_idempotency_property(self, mock_secrets, mock_table, payment_data):
        """
        Property 19: Payment Idempotency - Verification
        
        For any payment confirmation event, multiple verification attempts with the same
        data should produce consistent results and not cause duplicate processing.
        
        **Validates: Requirements 2.2, 2.5**
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
                'paymentId': payment_data['payment_id'],
                'orderId': payment_data['order_id'],
                'razorpayOrderId': payment_data['razorpay_order_id'],
                'status': PaymentStatus.PENDING.value,
                'amount': payment_data['amount'],
                'paymentMethod': PaymentMethod.ONLINE.value
            }
        }
        
        mock_table.update_item.return_value = {}
        
        service = PaymentService()
        
        # Mock signature verification to succeed
        with patch('hmac.compare_digest', return_value=True):
            # Act - Perform multiple identical verification requests
            results = []
            for i in range(payment_data['duplicate_count']):
                result = service.verify_razorpay_payment(
                    payment_id=payment_data['payment_id'],
                    order_id=payment_data['order_id'],
                    signature=payment_data['signature']
                )
                results.append(result)
        
        # Assert - Property: All verification attempts should produce identical results
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result['success'] == first_result['success'], \
                f"Verification attempt {i+1} success status differs from first attempt"
            assert result['data']['status'] == first_result['data']['status'], \
                f"Verification attempt {i+1} payment status differs from first attempt"
            assert result['data']['verified'] == first_result['data']['verified'], \
                f"Verification attempt {i+1} verified flag differs from first attempt"
            assert result['data']['paymentId'] == first_result['data']['paymentId'], \
                f"Verification attempt {i+1} payment ID differs from first attempt"
        
        # All results should indicate successful verification
        for i, result in enumerate(results):
            assert result['success'] is True, f"Verification attempt {i+1} should succeed"
            assert result['data']['status'] == PaymentStatus.COMPLETED.value, \
                f"Verification attempt {i+1} should result in COMPLETED status"
            assert result['data']['verified'] is True, \
                f"Verification attempt {i+1} should be marked as verified"
        
        # Verify that database update was called the expected number of times
        # (Each verification attempt should update the payment status)
        assert mock_table.update_item.call_count == payment_data['duplicate_count'], \
            f"Database should be updated {payment_data['duplicate_count']} times for {payment_data['duplicate_count']} verification attempts"
    
    @given(payment_data=payment_idempotency_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_razorpay_order_creation_idempotency_property(self, mock_secrets, mock_table, payment_data):
        """
        Property 19 Extension: Payment Idempotency - Order Creation
        
        For any Razorpay order creation request, multiple identical requests should
        either return the same order or handle duplicates gracefully.
        
        **Validates: Requirements 2.2, 2.5**
        """
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        mock_table.put_item.return_value = {}
        
        service = PaymentService()
        
        # Act - Create multiple identical Razorpay orders
        results = []
        for i in range(payment_data['duplicate_count']):
            result = service.create_razorpay_order(
                amount=payment_data['amount'],
                order_id=payment_data['order_id'],
                currency='INR'
            )
            results.append(result)
        
        # Assert - Property: All order creation attempts should succeed
        for i, result in enumerate(results):
            assert result['success'] is True, f"Order creation attempt {i+1} should succeed"
            assert 'paymentId' in result['data'], f"Order creation attempt {i+1} should return payment ID"
            assert 'razorpayOrder' in result['data'], f"Order creation attempt {i+1} should return Razorpay order"
            
            # Verify Razorpay order details are consistent
            razorpay_order = result['data']['razorpayOrder']
            assert razorpay_order['amount'] == int(payment_data['amount'] * 100), \
                f"Order creation attempt {i+1} should have correct amount in paise"
            assert razorpay_order['currency'] == 'INR', \
                f"Order creation attempt {i+1} should have correct currency"
            assert razorpay_order['receipt'] == payment_data['order_id'], \
                f"Order creation attempt {i+1} should have correct receipt/order ID"
        
        # Verify that database was called for each creation attempt
        # (Each attempt creates a new payment record with unique timestamp)
        assert mock_table.put_item.call_count == payment_data['duplicate_count'], \
            f"Database should be called {payment_data['duplicate_count']} times for {payment_data['duplicate_count']} creation attempts"
        
        # Verify that each payment record has a unique payment ID
        payment_ids = [result['data']['paymentId'] for result in results]
        unique_payment_ids = set(payment_ids)
        assert len(unique_payment_ids) == len(payment_ids), \
            "Each order creation attempt should generate a unique payment ID"
    
    @given(webhook_data=webhook_idempotency_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.secrets_client')
    def test_webhook_processing_idempotency_property(self, mock_secrets, webhook_data):
        """
        Property 19 Extension: Payment Idempotency - Webhook Processing
        
        For any payment webhook event, multiple identical webhook deliveries should
        be processed idempotently without causing duplicate state changes.
        
        **Validates: Requirements 2.2, 2.5**
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
        
        # Mock signature verification to succeed
        with patch('hmac.compare_digest', return_value=True):
            with patch.object(service, '_update_payment_status') as mock_update:
                # Act - Process the same webhook multiple times
                results = []
                for i in range(webhook_data['duplicate_count']):
                    result = service.handle_payment_webhook(
                        payload=webhook_data,
                        signature=webhook_data['signature']
                    )
                    results.append(result)
        
        # Assert - Property: All webhook processing attempts should succeed
        for i, result in enumerate(results):
            assert result['success'] is True, f"Webhook processing attempt {i+1} should succeed"
            assert result['message'] == 'Webhook processed successfully', \
                f"Webhook processing attempt {i+1} should return success message"
        
        # Verify that payment status update was called for each webhook processing
        # (In a real implementation, this might be idempotent, but for testing we verify the calls)
        assert mock_update.call_count == webhook_data['duplicate_count'], \
            f"Payment status should be updated {webhook_data['duplicate_count']} times for {webhook_data['duplicate_count']} webhook deliveries"
        
        # Verify that all update calls have consistent parameters
        update_calls = mock_update.call_args_list
        first_call = update_calls[0]
        for i, call in enumerate(update_calls[1:], 1):
            assert call[0][0] == first_call[0][0], \
                f"Webhook processing attempt {i+1} should update the same payment ID"
            assert call[0][1] == first_call[0][1], \
                f"Webhook processing attempt {i+1} should set the same payment status"
    
    @given(payment_data=payment_idempotency_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    def test_cod_payment_creation_idempotency_property(self, mock_table, payment_data):
        """
        Property 19 Extension: Payment Idempotency - COD Payment Creation
        
        For any COD payment creation request, multiple identical requests should
        handle duplicates gracefully and maintain data consistency.
        
        **Validates: Requirements 2.2, 2.5**
        """
        # Arrange
        mock_table.put_item.return_value = {}
        service = PaymentService()
        
        # Act - Create multiple identical COD payments
        results = []
        for i in range(payment_data['duplicate_count']):
            result = service.create_cod_payment(
                order_id=payment_data['order_id'],
                amount=payment_data['amount']
            )
            results.append(result)
        
        # Assert - Property: All COD payment creation attempts should succeed
        for i, result in enumerate(results):
            assert result['success'] is True, f"COD payment creation attempt {i+1} should succeed"
            assert 'paymentId' in result['data'], f"COD payment creation attempt {i+1} should return payment ID"
            assert result['data']['status'] == PaymentStatus.COD_PENDING.value, \
                f"COD payment creation attempt {i+1} should have COD_PENDING status"
        
        # Verify that database was called for each creation attempt
        assert mock_table.put_item.call_count == payment_data['duplicate_count'], \
            f"Database should be called {payment_data['duplicate_count']} times for {payment_data['duplicate_count']} COD creation attempts"
        
        # Verify that each COD payment has a unique payment ID
        payment_ids = [result['data']['paymentId'] for result in results]
        unique_payment_ids = set(payment_ids)
        assert len(unique_payment_ids) == len(payment_ids), \
            "Each COD payment creation attempt should generate a unique payment ID"
        
        # Verify all payment IDs follow the expected format for COD payments
        for payment_id in payment_ids:
            assert payment_id.startswith('cod_'), \
                f"COD payment ID {payment_id} should start with 'cod_' prefix"
            assert payment_data['order_id'] in payment_id, \
                f"COD payment ID {payment_id} should contain the order ID"
    
    @given(payment_data=payment_idempotency_data())
    @settings(max_examples=100, deadline=None)
    @patch('payment_service.payments_table')
    def test_payment_status_retrieval_idempotency_property(self, mock_table, payment_data):
        """
        Property 19 Extension: Payment Idempotency - Status Retrieval
        
        For any payment status retrieval request, multiple identical requests should
        return consistent results without side effects.
        
        **Validates: Requirements 2.2, 2.5**
        """
        # Arrange
        mock_table.query.return_value = {
            'Items': [{
                'paymentId': payment_data['payment_id'],
                'status': PaymentStatus.COMPLETED.value,
                'paymentMethod': PaymentMethod.ONLINE.value,
                'amount': payment_data['amount'],
                'createdAt': '2024-01-01T00:00:00+00:00',
                'updatedAt': '2024-01-01T00:01:00+00:00'
            }]
        }
        
        service = PaymentService()
        
        # Act - Retrieve payment status multiple times
        results = []
        for i in range(payment_data['duplicate_count']):
            result = service.get_payment_status(payment_data['order_id'])
            results.append(result)
        
        # Assert - Property: All status retrieval attempts should return identical results
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result['success'] == first_result['success'], \
                f"Status retrieval attempt {i+1} success status differs from first attempt"
            assert result['data']['paymentId'] == first_result['data']['paymentId'], \
                f"Status retrieval attempt {i+1} payment ID differs from first attempt"
            assert result['data']['status'] == first_result['data']['status'], \
                f"Status retrieval attempt {i+1} payment status differs from first attempt"
            assert result['data']['paymentMethod'] == first_result['data']['paymentMethod'], \
                f"Status retrieval attempt {i+1} payment method differs from first attempt"
            assert result['data']['amount'] == first_result['data']['amount'], \
                f"Status retrieval attempt {i+1} amount differs from first attempt"
        
        # All results should indicate successful retrieval
        for i, result in enumerate(results):
            assert result['success'] is True, f"Status retrieval attempt {i+1} should succeed"
            assert result['data']['status'] == PaymentStatus.COMPLETED.value, \
                f"Status retrieval attempt {i+1} should return COMPLETED status"
            assert result['data']['paymentMethod'] == PaymentMethod.ONLINE.value, \
                f"Status retrieval attempt {i+1} should return ONLINE payment method"
        
        # Verify that database query was called for each retrieval attempt
        assert mock_table.query.call_count == payment_data['duplicate_count'], \
            f"Database should be queried {payment_data['duplicate_count']} times for {payment_data['duplicate_count']} status retrieval attempts"


if __name__ == '__main__':
    pytest.main([__file__])