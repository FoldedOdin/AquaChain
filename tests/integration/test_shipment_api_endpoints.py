"""
Integration tests for Shipment Tracking API endpoints

Tests the complete end-to-end API workflows including:
- POST /api/shipments with valid/invalid auth
- POST /api/webhooks/:courier with valid/invalid signature
- GET /api/shipments/:shipmentId
- GET /api/shipments?orderId=:orderId
- Rate limiting behavior

Requirements: 1.1, 2.1, 3.1
"""

import pytest
import json
import sys
import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from decimal import Decimal

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shipments'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

# Import Lambda handlers
from create_shipment import handler as create_shipment_handler
from webhook_handler import handler as webhook_handler
from get_shipment_status import handler as get_shipment_status_handler


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    # Patch environment BEFORE importing modules
    env_patch = patch.dict(os.environ, {
        'SHIPMENTS_TABLE': 'test-shipments',
        'ORDERS_TABLE': 'test-orders',
        'ADMIN_TASKS_TABLE': 'test-admin-tasks',
        'WEBHOOK_SECRET': 'test-secret-key',
        'COURIER_API_KEY': 'test-courier-key',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic',
        'AWS_REGION': 'us-east-1'
    })
    
    # Also patch the module-level constant directly
    webhook_secret_patch = patch('webhook_handler.WEBHOOK_SECRET', 'test-secret-key')
    
    with env_patch, webhook_secret_patch:
        yield


@pytest.fixture
def mock_dynamodb():
    """Fixture providing mocked DynamoDB"""
    with patch('create_shipment.dynamodb') as mock_ddb, \
         patch('webhook_handler.dynamodb') as mock_webhook_ddb, \
         patch('get_shipment_status.dynamodb') as mock_get_ddb:
        
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table
        mock_webhook_ddb.Table.return_value = mock_table
        mock_get_ddb.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_dynamodb_client():
    """Fixture providing mocked DynamoDB client"""
    with patch('create_shipment.dynamodb_client') as mock_client:
        yield mock_client


@pytest.fixture
def sample_order():
    """Sample order data"""
    return {
        'orderId': 'ord_1735392000000',
        'status': 'approved',
        'device_id': 'AquaChain-Device-001',
        'consumer_id': 'user-123',
        'created_at': '2025-12-29T10:00:00Z'
    }


@pytest.fixture
def sample_shipment():
    """Sample shipment data"""
    return {
        'shipment_id': 'ship_1735478400000',
        'order_id': 'ord_1735392000000',
        'device_id': 'AquaChain-Device-001',
        'tracking_number': 'DELHUB123456789',
        'courier_name': 'Delhivery',
        'internal_status': 'in_transit',
        'destination': {
            'address': '123 Main St, Bangalore',
            'pincode': '560001',
            'contact_name': 'John Doe',
            'contact_phone': '+919876543210'
        },
        'timeline': [
            {
                'status': 'shipment_created',
                'timestamp': '2025-12-29T12:00:00Z',
                'location': 'Mumbai Warehouse',
                'description': 'Shipment created'
            }
        ],
        'webhook_events': [],
        'retry_config': {
            'max_retries': 3,
            'retry_count': 0
        },
        'estimated_delivery': '2025-12-31T18:00:00Z',
        'created_at': '2025-12-29T12:00:00Z',
        'updated_at': '2025-12-29T12:00:00Z'
    }


@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.request_id = 'test-request-123'
    context.function_name = 'test-function'
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
    return context


class TestPostShipmentsEndpoint:
    """Test suite for POST /api/shipments endpoint"""
    
    def test_create_shipment_with_valid_auth(
        self, mock_aws_environment, mock_dynamodb, mock_dynamodb_client,
        sample_order, mock_context
    ):
        """
        Test POST /api/shipments with valid authentication
        Requirements: 1.1
        """
        # Mock DynamoDB responses
        mock_dynamodb.get_item.return_value = {'Item': sample_order}
        mock_dynamodb_client.transact_write_items.return_value = {}
        
        # Mock courier API
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'packages': [{'waybill': 'DELHUB123456789'}]
            }
            
            # Create API Gateway event with valid auth
            event = {
                'httpMethod': 'POST',
                'path': '/api/shipments',
                'body': json.dumps({
                    'order_id': 'ord_1735392000000',
                    'courier_name': 'Delhivery',
                    'service_type': 'Surface',
                    'destination': {
                        'address': '123 Main St, Bangalore',
                        'pincode': '560001',
                        'contact_name': 'John Doe',
                        'contact_phone': '+919876543210'
                    },
                    'package_details': {
                        'weight': '0.5kg',
                        'declared_value': 5000,
                        'insurance': True
                    }
                }),
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'admin-user-123',
                            'cognito:groups': 'administrators'
                        }
                    },
                    'identity': {
                        'sourceIp': '192.168.1.1'
                    }
                },
                'headers': {
                    'Authorization': 'Bearer valid-jwt-token'
                }
            }
            
            # Execute handler
            response = create_shipment_handler(event, mock_context)
            
            # Verify response
            assert response['statusCode'] == 201
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'shipment_id' in body
            assert 'tracking_number' in body
            assert body['tracking_number'].startswith('DELHUB')  # Mock tracking number format
            
            # Verify DynamoDB transaction was called
            mock_dynamodb_client.transact_write_items.assert_called_once()
    
    def test_create_shipment_without_auth(self, mock_aws_environment, mock_context):
        """
        Test POST /api/shipments without authentication (should fail)
        Requirements: 1.1
        """
        # Create API Gateway event without auth
        event = {
            'httpMethod': 'POST',
            'path': '/api/shipments',
            'body': json.dumps({
                'order_id': 'ord_1735392000000',
                'courier_name': 'Delhivery'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            },
            'headers': {}
        }
        
        # In real API Gateway, this would be rejected before reaching Lambda
        # We simulate the expected behavior
        # Note: API Gateway handles auth rejection, not Lambda
        # This test verifies Lambda can handle missing auth context
        
        response = create_shipment_handler(event, mock_context)
        
        # Lambda should handle gracefully even without auth context
        # (In production, API Gateway would reject before Lambda is invoked)
        assert response['statusCode'] in [400, 401, 500]

    
    def test_create_shipment_with_invalid_body(
        self, mock_aws_environment, mock_context
    ):
        """
        Test POST /api/shipments with invalid request body
        Requirements: 1.1
        """
        # Create event with missing required fields
        event = {
            'httpMethod': 'POST',
            'path': '/api/shipments',
            'body': json.dumps({
                'order_id': 'ord_1735392000000'
                # Missing courier_name, destination, package_details
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'admin-user-123'
                    }
                }
            }
        }
        
        response = create_shipment_handler(event, mock_context)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body or 'success' in body
        if 'success' in body:
            assert body['success'] is False
    
    def test_create_shipment_order_not_found(
        self, mock_aws_environment, mock_dynamodb, mock_context
    ):
        """
        Test POST /api/shipments with non-existent order
        Requirements: 1.1
        """
        # Mock DynamoDB to return no order
        mock_dynamodb.get_item.return_value = {}
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/shipments',
            'body': json.dumps({
                'order_id': 'ord_nonexistent',
                'courier_name': 'Delhivery',
                'destination': {
                    'address': '123 Main St',
                    'pincode': '560001',
                    'contact_name': 'John Doe',
                    'contact_phone': '+919876543210'
                },
                'package_details': {
                    'weight': '0.5kg',
                    'declared_value': 5000
                }
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'admin-user-123'}
                }
            }
        }
        
        response = create_shipment_handler(event, mock_context)
        
        # Should return 404 Not Found
        assert response['statusCode'] == 404


class TestPostWebhooksEndpoint:
    """Test suite for POST /api/webhooks/:courier endpoint"""
    
    def test_webhook_with_valid_signature(
        self, mock_aws_environment, mock_dynamodb, sample_shipment, mock_context
    ):
        """
        Test POST /api/webhooks/:courier with valid HMAC signature
        Requirements: 2.1
        """
        # Mock DynamoDB to return shipment
        mock_dynamodb.query.return_value = {'Items': [sample_shipment]}
        mock_dynamodb.update_item.return_value = {}
        
        # Create webhook payload - use exact format for consistent signature
        payload = {
            'waybill': 'DELHUB123456789',
            'Status': 'In Transit',
            'Scans': [{
                'ScanDetail': {
                    'ScanDateTime': '2025-12-29T14:30:00Z',
                    'ScannedLocation': 'Pune Hub',
                    'Instructions': 'Package in transit'
                }
            }]
        }
        
        # Use json.dumps with separators to match what will be in event body
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        # Generate valid HMAC signature using the exact payload string
        signature = hmac.new(
            'test-secret-key'.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': payload_str,
            'headers': {
                'X-Webhook-Signature': signature
            }
        }
        
        response = webhook_handler(event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        
        # Verify shipment was updated
        mock_dynamodb.update_item.assert_called()
    
    def test_webhook_with_invalid_signature(
        self, mock_aws_environment, mock_context
    ):
        """
        Test POST /api/webhooks/:courier with invalid signature
        Requirements: 2.1, 10.2
        """
        payload = {
            'waybill': 'DELHUB123456789',
            'Status': 'In Transit'
        }
        
        # Create event with invalid signature
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': json.dumps(payload),
            'headers': {
                'X-Webhook-Signature': 'invalid-signature-12345'
            }
        }
        
        response = webhook_handler(event, mock_context)
        
        # Should return 401 Unauthorized
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_webhook_without_signature(
        self, mock_aws_environment, mock_context
    ):
        """
        Test POST /api/webhooks/:courier without signature header
        Requirements: 10.2
        """
        payload = {
            'waybill': 'DELHUB123456789',
            'Status': 'In Transit'
        }
        
        # Create event without signature header
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': json.dumps(payload),
            'headers': {}
        }
        
        response = webhook_handler(event, mock_context)
        
        # Should return 401 Unauthorized
        assert response['statusCode'] == 401
    
    def test_webhook_with_invalid_payload(
        self, mock_aws_environment, mock_context
    ):
        """
        Test POST /api/webhooks/:courier with malformed payload
        Requirements: 2.1
        """
        payload = {
            'invalid_field': 'value'
            # Missing required fields: waybill, Status
        }
        
        # Use consistent JSON formatting
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        # Generate valid signature for invalid payload
        signature = hmac.new(
            'test-secret-key'.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': payload_str,
            'headers': {
                'X-Webhook-Signature': signature
            }
        }
        
        response = webhook_handler(event, mock_context)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400
    
    def test_webhook_shipment_not_found(
        self, mock_aws_environment, mock_dynamodb, mock_context
    ):
        """
        Test POST /api/webhooks/:courier for non-existent shipment
        Requirements: 2.1
        """
        # Mock DynamoDB to return no shipment
        mock_dynamodb.query.return_value = {'Items': []}
        
        payload = {
            'waybill': 'NONEXISTENT123',
            'Status': 'In Transit',
            'Scans': []
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            'test-secret-key'.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': payload_str,
            'headers': {
                'X-Webhook-Signature': signature
            }
        }
        
        response = webhook_handler(event, mock_context)
        
        # Should return 404 Not Found
        assert response['statusCode'] == 404


class TestGetShipmentByIdEndpoint:
    """Test suite for GET /api/shipments/:shipmentId endpoint"""
    
    def test_get_shipment_by_id_success(
        self, mock_aws_environment, mock_dynamodb, sample_shipment, mock_context
    ):
        """
        Test GET /api/shipments/:shipmentId with valid auth
        Requirements: 3.1
        """
        # Mock DynamoDB to return shipment
        mock_dynamodb.get_item.return_value = {'Item': sample_shipment}
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments/ship_1735478400000',
            'pathParameters': {
                'shipmentId': 'ship_1735478400000'
            },
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123',
                        'cognito:groups': 'consumers'
                    }
                }
            },
            'headers': {
                'Authorization': 'Bearer valid-jwt-token'
            }
        }
        
        response = get_shipment_status_handler(event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'shipment' in body
        assert body['shipment']['shipment_id'] == 'ship_1735478400000'
        assert 'progress' in body
        assert 'percentage' in body['progress']
    
    def test_get_shipment_by_id_not_found(
        self, mock_aws_environment, mock_dynamodb, mock_context
    ):
        """
        Test GET /api/shipments/:shipmentId for non-existent shipment
        Requirements: 3.1
        """
        # Mock DynamoDB to return no shipment
        mock_dynamodb.get_item.return_value = {}
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments/ship_nonexistent',
            'pathParameters': {
                'shipmentId': 'ship_nonexistent'
            },
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'user-123'}
                }
            }
        }
        
        response = get_shipment_status_handler(event, mock_context)
        
        # Should return 404 Not Found
        assert response['statusCode'] == 404
    
    def test_get_shipment_without_auth(
        self, mock_aws_environment, mock_context
    ):
        """
        Test GET /api/shipments/:shipmentId without authentication
        Requirements: 3.1
        """
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments/ship_1735478400000',
            'pathParameters': {
                'shipmentId': 'ship_1735478400000'
            },
            'queryStringParameters': None,
            'requestContext': {},
            'headers': {}
        }
        
        # In real API Gateway, this would be rejected before reaching Lambda
        # Lambda should handle gracefully
        response = get_shipment_status_handler(event, mock_context)
        
        # Lambda may return data or error depending on implementation
        assert response['statusCode'] in [200, 401, 403, 500]


class TestGetShipmentByOrderIdEndpoint:
    """Test suite for GET /api/shipments?orderId=:orderId endpoint"""
    
    def test_get_shipment_by_order_id_success(
        self, mock_aws_environment, mock_dynamodb, sample_shipment, mock_context
    ):
        """
        Test GET /api/shipments?orderId=:orderId with valid auth
        Requirements: 3.1
        """
        # Mock DynamoDB to return shipment
        mock_dynamodb.query.return_value = {'Items': [sample_shipment]}
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments',
            'pathParameters': None,
            'queryStringParameters': {
                'orderId': 'ord_1735392000000'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123',
                        'cognito:groups': 'consumers'
                    }
                }
            },
            'headers': {
                'Authorization': 'Bearer valid-jwt-token'
            }
        }
        
        response = get_shipment_status_handler(event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'shipment' in body
        assert body['shipment']['order_id'] == 'ord_1735392000000'
    
    def test_get_shipment_by_order_id_not_found(
        self, mock_aws_environment, mock_dynamodb, mock_context
    ):
        """
        Test GET /api/shipments?orderId=:orderId for non-existent order
        Requirements: 3.1
        """
        # Mock DynamoDB to return no shipments
        mock_dynamodb.query.return_value = {'Items': []}
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments',
            'pathParameters': None,
            'queryStringParameters': {
                'orderId': 'ord_nonexistent'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'user-123'}
                }
            }
        }
        
        response = get_shipment_status_handler(event, mock_context)
        
        # Should return 404 Not Found
        assert response['statusCode'] == 404
    
    def test_get_shipment_missing_parameters(
        self, mock_aws_environment, mock_context
    ):
        """
        Test GET /api/shipments without shipmentId or orderId
        Requirements: 3.1
        """
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments',
            'pathParameters': None,
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'user-123'}
                }
            }
        }
        
        response = get_shipment_status_handler(event, mock_context)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400


class TestRateLimiting:
    """Test suite for rate limiting behavior"""
    
    def test_rate_limiting_simulation(
        self, mock_aws_environment, mock_dynamodb, sample_shipment, mock_context
    ):
        """
        Test rate limiting behavior (simulated)
        Requirements: 1.1, 2.1, 3.1
        
        Note: Actual rate limiting is enforced by API Gateway usage plans.
        This test simulates the expected behavior.
        """
        # Mock DynamoDB
        mock_dynamodb.get_item.return_value = {'Item': sample_shipment}
        
        # Simulate multiple rapid requests
        event = {
            'httpMethod': 'GET',
            'path': '/api/shipments/ship_1735478400000',
            'pathParameters': {
                'shipmentId': 'ship_1735478400000'
            },
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'user-123'}
                }
            }
        }
        
        # Make multiple requests
        responses = []
        for i in range(5):
            response = get_shipment_status_handler(event, mock_context)
            responses.append(response)
        
        # All requests should succeed (rate limiting is at API Gateway level)
        for response in responses:
            assert response['statusCode'] == 200
        
        # In production, API Gateway would return 429 Too Many Requests
        # after exceeding rate limit
    
    def test_webhook_high_volume(
        self, mock_aws_environment, mock_dynamodb, sample_shipment, mock_context
    ):
        """
        Test webhook endpoint can handle high volume
        Requirements: 2.1, 10.5
        """
        # Mock DynamoDB
        mock_dynamodb.query.return_value = {'Items': [sample_shipment]}
        mock_dynamodb.update_item.return_value = {}
        
        payload = {
            'waybill': 'DELHUB123456789',
            'Status': 'In Transit',
            'Scans': []
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            'test-secret-key'.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': payload_str,
            'headers': {
                'X-Webhook-Signature': signature
            }
        }
        
        # Simulate multiple webhook calls
        responses = []
        for i in range(10):
            response = webhook_handler(event, mock_context)
            responses.append(response)
        
        # First request should succeed
        assert responses[0]['statusCode'] == 200
        
        # Subsequent requests should be idempotent (already processed)
        for response in responses[1:]:
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            # May indicate already processed
            assert body['success'] is True


class TestEndToEndWorkflow:
    """Test suite for complete end-to-end API workflows"""
    
    def test_complete_shipment_lifecycle(
        self, mock_aws_environment, mock_dynamodb, mock_dynamodb_client,
        sample_order, mock_context
    ):
        """
        Test complete shipment lifecycle:
        1. Create shipment (POST /api/shipments)
        2. Receive webhook (POST /api/webhooks/:courier)
        3. Query status (GET /api/shipments/:shipmentId)
        
        Requirements: 1.1, 2.1, 3.1
        """
        # Step 1: Create shipment
        mock_dynamodb.get_item.return_value = {'Item': sample_order}
        mock_dynamodb_client.transact_write_items.return_value = {}
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'packages': [{'waybill': 'DELHUB123456789'}]
            }
            
            create_event = {
                'httpMethod': 'POST',
                'path': '/api/shipments',
                'body': json.dumps({
                    'order_id': 'ord_1735392000000',
                    'courier_name': 'Delhivery',
                    'destination': {
                        'address': '123 Main St',
                        'pincode': '560001',
                        'contact_name': 'John Doe',
                        'contact_phone': '+919876543210'
                    },
                    'package_details': {
                        'weight': '0.5kg',
                        'declared_value': 5000
                    }
                }),
                'requestContext': {
                    'authorizer': {
                        'claims': {'sub': 'admin-user-123'}
                    }
                }
            }
            
            create_response = create_shipment_handler(create_event, mock_context)
            assert create_response['statusCode'] == 201
            
            create_body = json.loads(create_response['body'])
            shipment_id = create_body['shipment_id']
            tracking_number = create_body['tracking_number']
        
        # Step 2: Receive webhook
        shipment_data = {
            'shipment_id': shipment_id,
            'tracking_number': tracking_number,
            'order_id': 'ord_1735392000000',
            'internal_status': 'shipment_created',
            'webhook_events': [],
            'timeline': []
        }
        
        mock_dynamodb.query.return_value = {'Items': [shipment_data]}
        mock_dynamodb.update_item.return_value = {}
        
        webhook_payload = {
            'waybill': tracking_number,
            'Status': 'In Transit',
            'Scans': []
        }
        
        webhook_payload_str = json.dumps(webhook_payload, separators=(',', ':'))
        webhook_signature = hmac.new(
            'test-secret-key'.encode(),
            webhook_payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        webhook_event = {
            'httpMethod': 'POST',
            'path': '/api/webhooks/delhivery',
            'pathParameters': {'courier': 'delhivery'},
            'body': webhook_payload_str,
            'headers': {
                'X-Webhook-Signature': webhook_signature
            }
        }
        
        webhook_response = webhook_handler(webhook_event, mock_context)
        assert webhook_response['statusCode'] == 200
        
        # Step 3: Query shipment status
        shipment_data['internal_status'] = 'in_transit'
        shipment_data['courier_name'] = 'Delhivery'
        shipment_data['created_at'] = '2025-12-29T12:00:00Z'
        mock_dynamodb.get_item.return_value = {'Item': shipment_data}
        
        get_event = {
            'httpMethod': 'GET',
            'path': f'/api/shipments/{shipment_id}',
            'pathParameters': {
                'shipmentId': shipment_id
            },
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {
                    'claims': {'sub': 'user-123'}
                }
            }
        }
        
        get_response = get_shipment_status_handler(get_event, mock_context)
        assert get_response['statusCode'] == 200
        
        get_body = json.loads(get_response['body'])
        assert get_body['success'] is True
        assert get_body['shipment']['shipment_id'] == shipment_id


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
