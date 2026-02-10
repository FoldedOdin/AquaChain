"""
Unit tests for Razorpay Webhook Handler

Tests webhook signature verification, event processing, and error handling.
"""

import json
import hmac
import hashlib
import pytest
from unittest.mock import Mock, patch, MagicMock
from webhook_handler import lambda_handler


@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = Mock()
    context.function_name = "test-webhook-handler"
    context.request_id = "test-request-id"
    return context


@pytest.fixture
def webhook_secret():
    """Test webhook secret"""
    return "test_webhook_secret_12345"


@pytest.fixture
def valid_payment_captured_payload():
    """Valid payment.captured webhook payload"""
    return {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test123456",
                    "order_id": "order_test123456",
                    "amount": 50000,
                    "currency": "INR",
                    "status": "captured",
                    "method": "card",
                    "captured": True,
                    "email": "test@example.com",
                    "contact": "+919876543210",
                    "created_at": 1234567890
                }
            }
        }
    }


@pytest.fixture
def valid_payment_failed_payload():
    """Valid payment.failed webhook payload"""
    return {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test123456",
                    "order_id": "order_test123456",
                    "amount": 50000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to insufficient funds",
                    "created_at": 1234567890
                }
            }
        }
    }


def generate_signature(payload: dict, secret: str) -> str:
    """Generate HMAC SHA256 signature for webhook payload"""
    payload_str = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()


class TestWebhookSignatureVerification:
    """Test webhook signature verification"""
    
    @patch('webhook_handler.payment_service')
    def test_webhook_with_valid_signature(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test webhook with valid HMAC signature"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True,
            'message': 'Webhook processed successfully'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        mock_payment_service.handle_payment_webhook.assert_called_once()
    
    @patch('webhook_handler.payment_service')
    def test_webhook_with_invalid_signature(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload
    ):
        """Test webhook with invalid signature"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        invalid_signature = "invalid_signature_12345"
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': False,
            'error': 'Invalid signature'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': invalid_signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'signature' in body['error'].lower()
    
    @patch('webhook_handler.payment_service')
    def test_webhook_without_signature(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload
    ):
        """Test webhook without signature header"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        
        event = {
            'body': payload_str,
            'headers': {}
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'signature' in body['error'].lower()
        mock_payment_service.handle_payment_webhook.assert_not_called()
    
    @patch('webhook_handler.payment_service')
    def test_webhook_with_case_insensitive_header(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test webhook with lowercase signature header"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True,
            'message': 'Webhook processed successfully'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'x-razorpay-signature': signature  # lowercase
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200


class TestWebhookEventProcessing:
    """Test webhook event processing"""
    
    @patch('webhook_handler.payment_service')
    def test_payment_captured_event(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test payment.captured event processing"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True,
            'message': 'Payment captured successfully'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        mock_payment_service.handle_payment_webhook.assert_called_once_with(
            valid_payment_captured_payload, signature
        )
    
    @patch('webhook_handler.payment_service')
    def test_payment_failed_event(
        self, mock_payment_service, mock_context, 
        valid_payment_failed_payload, webhook_secret
    ):
        """Test payment.failed event processing"""
        # Setup
        payload_str = json.dumps(valid_payment_failed_payload)
        signature = generate_signature(valid_payment_failed_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True,
            'message': 'Payment failure recorded'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200


class TestWebhookErrorHandling:
    """Test webhook error handling"""
    
    @patch('webhook_handler.payment_service')
    def test_invalid_json_payload(
        self, mock_payment_service, mock_context
    ):
        """Test webhook with invalid JSON payload"""
        # Setup
        event = {
            'body': 'invalid json {{{',
            'headers': {
                'X-Razorpay-Signature': 'test_signature'
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'json' in body['error'].lower()
    
    @patch('webhook_handler.payment_service')
    def test_missing_body(
        self, mock_payment_service, mock_context
    ):
        """Test webhook with missing body"""
        # Setup
        event = {
            'headers': {
                'X-Razorpay-Signature': 'test_signature'
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
    
    @patch('webhook_handler.payment_service')
    def test_payment_service_exception(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test handling of payment service exceptions"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.side_effect = Exception("Database error")
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False


class TestWebhookCORS:
    """Test CORS headers in webhook responses"""
    
    @patch('webhook_handler.payment_service')
    def test_cors_headers_present(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test that CORS headers are present in response"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute
        response = lambda_handler(event, mock_context)
        
        # Verify
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Content-Type'] == 'application/json'


class TestWebhookIdempotency:
    """Test webhook idempotency handling"""
    
    @patch('webhook_handler.payment_service')
    def test_duplicate_webhook_handling(
        self, mock_payment_service, mock_context, 
        valid_payment_captured_payload, webhook_secret
    ):
        """Test that duplicate webhooks are handled gracefully"""
        # Setup
        payload_str = json.dumps(valid_payment_captured_payload)
        signature = generate_signature(valid_payment_captured_payload, webhook_secret)
        
        mock_payment_service.handle_payment_webhook.return_value = {
            'success': True,
            'message': 'Webhook already processed'
        }
        
        event = {
            'body': payload_str,
            'headers': {
                'X-Razorpay-Signature': signature
            }
        }
        
        # Execute - first call
        response1 = lambda_handler(event, mock_context)
        
        # Execute - duplicate call
        response2 = lambda_handler(event, mock_context)
        
        # Verify both return success
        assert response1['statusCode'] == 200
        assert response2['statusCode'] == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
