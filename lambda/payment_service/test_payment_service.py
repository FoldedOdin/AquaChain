"""
Unit tests for Payment Service

Tests the core functionality of the payment service including:
- Razorpay order creation and verification
- COD payment processing
- Payment status retrieval
- Webhook handling
"""

import pytest
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


class TestPaymentService:
    """Test cases for PaymentService"""
    
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_create_razorpay_order_success(self, mock_secrets, mock_table):
        """Test successful Razorpay order creation"""
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        mock_table.put_item.return_value = {}
        
        service = PaymentService()
        
        # Act
        result = service.create_razorpay_order(
            amount=100.0,
            order_id='test-order-123',
            currency='INR'
        )
        
        # Assert
        assert result['success'] is True
        assert 'paymentId' in result['data']
        assert 'razorpayOrder' in result['data']
        assert result['data']['razorpayOrder']['amount'] == 10000  # Amount in paise
        assert result['data']['razorpayOrder']['currency'] == 'INR'
        assert result['data']['razorpayOrder']['receipt'] == 'test-order-123'
        
        # Verify DynamoDB call
        mock_table.put_item.assert_called_once()
    
    def test_create_razorpay_order_validation_error(self):
        """Test Razorpay order creation with validation error"""
        # Arrange
        service = PaymentService()
        
        # Act
        result = service.create_razorpay_order(
            amount=-100.0,  # Invalid negative amount
            order_id='test-order-123'
        )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
    
    @patch('payment_service.payments_table')
    def test_create_cod_payment_success(self, mock_table):
        """Test successful COD payment creation"""
        # Arrange
        mock_table.put_item.return_value = {}
        service = PaymentService()
        
        # Act
        result = service.create_cod_payment(
            order_id='test-order-123',
            amount=100.0
        )
        
        # Assert
        assert result['success'] is True
        assert 'paymentId' in result['data']
        assert result['data']['status'] == PaymentStatus.COD_PENDING.value
        
        # Verify DynamoDB call
        mock_table.put_item.assert_called_once()
    
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_verify_razorpay_payment_success(self, mock_secrets, mock_table):
        """Test successful Razorpay payment verification"""
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        mock_table.get_item.return_value = {
            'Item': {
                'paymentId': 'test-payment-123',
                'orderId': 'test-order-123',
                'razorpayOrderId': 'order_test_123',
                'status': PaymentStatus.PENDING.value
            }
        }
        mock_table.update_item.return_value = {}
        
        service = PaymentService()
        
        # Mock signature verification
        with patch('hmac.compare_digest', return_value=True):
            # Act
            result = service.verify_razorpay_payment(
                payment_id='test-payment-123',
                order_id='test-order-123',
                signature='valid_signature'
            )
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == PaymentStatus.COMPLETED.value
        assert result['data']['verified'] is True
        
        # Verify DynamoDB calls
        mock_table.get_item.assert_called_once()
        mock_table.update_item.assert_called_once()
    
    @patch('payment_service.payments_table')
    @patch('payment_service.secrets_client')
    def test_verify_razorpay_payment_invalid_signature(self, mock_secrets, mock_table):
        """Test Razorpay payment verification with invalid signature"""
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        mock_table.get_item.return_value = {
            'Item': {
                'paymentId': 'test-payment-123',
                'orderId': 'test-order-123',
                'razorpayOrderId': 'order_test_123',
                'status': PaymentStatus.PENDING.value
            }
        }
        mock_table.update_item.return_value = {}
        
        service = PaymentService()
        
        # Mock signature verification to fail
        with patch('hmac.compare_digest', return_value=False):
            # Act
            result = service.verify_razorpay_payment(
                payment_id='test-payment-123',
                order_id='test-order-123',
                signature='invalid_signature'
            )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
    
    @patch('payment_service.payments_table')
    def test_get_payment_status_success(self, mock_table):
        """Test successful payment status retrieval"""
        # Arrange
        mock_table.query.return_value = {
            'Items': [{
                'paymentId': 'test-payment-123',
                'status': PaymentStatus.COD_PENDING.value,
                'paymentMethod': PaymentMethod.COD.value,
                'amount': 100.0,
                'createdAt': '2024-01-01T00:00:00+00:00',
                'updatedAt': '2024-01-01T00:00:00+00:00'
            }]
        }
        
        service = PaymentService()
        
        # Act
        result = service.get_payment_status('test-order-123')
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == PaymentStatus.COD_PENDING.value
        assert result['data']['paymentMethod'] == PaymentMethod.COD.value
        assert result['data']['amount'] == 100.0
        
        # Verify DynamoDB call
        mock_table.query.assert_called_once()
    
    @patch('payment_service.payments_table')
    def test_get_payment_status_not_found(self, mock_table):
        """Test payment status retrieval for non-existent order"""
        # Arrange
        mock_table.query.return_value = {'Items': []}
        service = PaymentService()
        
        # Act
        result = service.get_payment_status('non-existent-order')
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == 'NOT_FOUND'
    
    @patch('payment_service.secrets_client')
    def test_handle_payment_webhook_success(self, mock_secrets):
        """Test successful webhook handling"""
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret',
                'webhook_secret': 'test_webhook_secret'
            })
        }
        
        service = PaymentService()
        
        webhook_payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'id': 'pay_test_123',
                    'order_id': 'order_test_123',
                    'status': 'captured'
                }
            }
        }
        
        # Mock signature verification
        with patch('hmac.compare_digest', return_value=True):
            with patch.object(service, '_update_payment_status') as mock_update:
                # Act
                result = service.handle_payment_webhook(
                    payload=webhook_payload,
                    signature='valid_signature'
                )
        
        # Assert
        assert result['success'] is True
        assert result['message'] == 'Webhook processed successfully'
    
    @patch('payment_service.secrets_client')
    def test_handle_payment_webhook_invalid_signature(self, mock_secrets):
        """Test webhook handling with invalid signature"""
        # Arrange
        mock_secrets.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'key_id': 'test_key_id',
                'key_secret': 'test_key_secret'
            })
        }
        
        service = PaymentService()
        
        webhook_payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'id': 'pay_test_123',
                    'order_id': 'order_test_123'
                }
            }
        }
        
        # Mock signature verification to fail
        with patch('hmac.compare_digest', return_value=False):
            # Act
            result = service.handle_payment_webhook(
                payload=webhook_payload,
                signature='invalid_signature'
            )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'Invalid signature'


class TestLambdaHandler:
    """Test cases for Lambda handler"""
    
    @patch('payment_service.PaymentService')
    def test_create_razorpay_order_endpoint(self, mock_service_class):
        """Test create Razorpay order endpoint"""
        # Arrange
        mock_service = MagicMock()
        mock_service.create_razorpay_order.return_value = {
            'success': True,
            'data': {
                'paymentId': 'test-payment-123',
                'razorpayOrder': {
                    'id': 'order_test_123',
                    'amount': 10000,
                    'currency': 'INR'
                }
            }
        }
        mock_service_class.return_value = mock_service
        
        event = {
            'httpMethod': 'POST',
            'path': '/payment/create-razorpay-order',
            'body': json.dumps({
                'amount': 100.0,
                'orderId': 'test-order-123',
                'currency': 'INR'
            }),
            'headers': {}
        }
        
        # Act
        response = payment_service.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'paymentId' in body['data']
        
        # Verify service call
        mock_service.create_razorpay_order.assert_called_once_with(
            amount=100.0,
            order_id='test-order-123',
            currency='INR'
        )
    
    @patch('payment_service.PaymentService')
    def test_create_cod_payment_endpoint(self, mock_service_class):
        """Test create COD payment endpoint"""
        # Arrange
        mock_service = MagicMock()
        mock_service.create_cod_payment.return_value = {
            'success': True,
            'data': {
                'paymentId': 'test-payment-123',
                'status': PaymentStatus.COD_PENDING.value
            }
        }
        mock_service_class.return_value = mock_service
        
        event = {
            'httpMethod': 'POST',
            'path': '/payment/create-cod-payment',
            'body': json.dumps({
                'orderId': 'test-order-123',
                'amount': 100.0
            }),
            'headers': {}
        }
        
        # Act
        response = payment_service.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['status'] == PaymentStatus.COD_PENDING.value
        
        # Verify service call
        mock_service.create_cod_payment.assert_called_once_with(
            order_id='test-order-123',
            amount=100.0
        )
    
    @patch('payment_service.PaymentService')
    def test_get_payment_status_endpoint(self, mock_service_class):
        """Test get payment status endpoint"""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_payment_status.return_value = {
            'success': True,
            'data': {
                'paymentId': 'test-payment-123',
                'status': PaymentStatus.COD_PENDING.value,
                'paymentMethod': PaymentMethod.COD.value,
                'amount': 100.0
            }
        }
        mock_service_class.return_value = mock_service
        
        event = {
            'httpMethod': 'GET',
            'path': '/payment/payment-status',
            'queryStringParameters': {
                'orderId': 'test-order-123'
            },
            'headers': {}
        }
        
        # Act
        response = payment_service.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['status'] == PaymentStatus.COD_PENDING.value
        
        # Verify service call
        mock_service.get_payment_status.assert_called_once_with('test-order-123')
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint handling"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'path': '/payment/invalid-endpoint',
            'headers': {}
        }
        
        # Act
        response = payment_service.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'Invalid endpoint or method'


if __name__ == '__main__':
    pytest.main([__file__])