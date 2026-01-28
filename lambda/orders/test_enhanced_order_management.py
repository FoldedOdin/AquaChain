"""
Unit tests for Enhanced Order Management Service
Tests order creation, status updates, retrieval, and error handling
"""

import sys
import os
import pytest
import json
import unittest.mock
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
import enhanced_order_management
from enhanced_order_management import OrderManagementService, OrderStatus, PaymentMethod


class TestOrderManagementService:
    """Unit tests for OrderManagementService"""
    
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
    
    def test_create_order_cod_success(self):
        """Test successful COD order creation"""
        # Arrange
        request_data = {
            'consumerId': '123e4567-e89b-12d3-a456-426614174000',
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'deliveryAddress': {
                'street': '123 Main St',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '560001',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'John Doe',
                'phone': '+919876543210',
                'email': 'john@example.com'
            },
            'amount': Decimal('5000.00')
        }
        
        # Mock DynamoDB put_item
        self.mock_orders_table.put_item.return_value = {}
        
        # Act
        with patch('enhanced_order_management.uuid.uuid4') as mock_uuid, \
             patch('enhanced_order_management.datetime') as mock_datetime:
            
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-order-id')
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00+00:00'
            
            result = self.service.create_order(request_data)
        
        # Assert
        assert result['success'] is True
        assert result['data']['id'] == 'test-order-id'
        assert result['data']['status'] == OrderStatus.PENDING_CONFIRMATION.value
        assert result['data']['paymentMethod'] == 'COD'
        
        # Verify DynamoDB call
        self.mock_orders_table.put_item.assert_called_once()
        call_args = self.mock_orders_table.put_item.call_args[1]
        assert call_args['Item']['orderId'] == 'test-order-id'
        assert call_args['Item']['status'] == OrderStatus.PENDING_CONFIRMATION.value
    
    def test_create_order_online_success(self):
        """Test successful online payment order creation"""
        # Arrange
        request_data = {
            'consumerId': '123e4567-e89b-12d3-a456-426614174000',
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'ONLINE',
            'deliveryAddress': {
                'street': '123 Main St',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '560001',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'John Doe',
                'phone': '+919876543210',
                'email': 'john@example.com'
            },
            'amount': Decimal('5000.00')
        }
        
        # Mock DynamoDB put_item
        self.mock_orders_table.put_item.return_value = {}
        
        # Act
        with patch('enhanced_order_management.uuid.uuid4') as mock_uuid, \
             patch('enhanced_order_management.datetime') as mock_datetime:
            
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-order-id')
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T00:00:00+00:00'
            
            result = self.service.create_order(request_data)
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == OrderStatus.PENDING_PAYMENT.value
        assert result['data']['paymentMethod'] == 'ONLINE'
    
    def test_create_order_validation_error(self):
        """Test order creation with validation error"""
        # Arrange - missing required fields
        request_data = {
            'consumerId': 'invalid-uuid',
            'deviceType': '',  # Empty string should fail
            'paymentMethod': 'INVALID'  # Invalid payment method
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            self.service.create_order(request_data)
    
    def test_update_order_status_success(self):
        """Test successful order status update"""
        # Arrange
        order_id = 'test-order-id'
        current_order = {
            'orderId': order_id,
            'status': OrderStatus.PENDING_CONFIRMATION.value,
            'version': 1,
            'statusHistory': []
        }
        
        request_data = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'reason': 'Order confirmed by customer'
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock update_item
        updated_order = {**current_order, 'status': OrderStatus.ORDER_PLACED.value, 'version': 2}
        self.mock_orders_table.update_item.return_value = {'Attributes': updated_order}
        
        # Act
        result = self.service.update_order_status(request_data)
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == OrderStatus.ORDER_PLACED.value
        
        # Verify update_item was called with optimistic locking
        self.mock_orders_table.update_item.assert_called_once()
        call_args = self.mock_orders_table.update_item.call_args[1]
        assert ':current_version' in call_args['ExpressionAttributeValues']
        assert call_args['ExpressionAttributeValues'][':current_version'] == 1
    
    def test_update_order_status_invalid_transition(self):
        """Test order status update with invalid transition"""
        # Arrange
        order_id = 'test-order-id'
        current_order = {
            'orderId': order_id,
            'status': OrderStatus.DELIVERED.value,  # Terminal state
            'version': 1
        }
        
        request_data = {
            'orderId': order_id,
            'status': OrderStatus.SHIPPED.value  # Invalid transition from DELIVERED
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Act & Assert
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.update_order_status(request_data)
        
        assert 'Invalid state transition' in str(exc_info.value)
    
    def test_update_order_status_order_not_found(self):
        """Test order status update when order doesn't exist"""
        # Arrange
        request_data = {
            'orderId': 'non-existent-order',
            'status': OrderStatus.ORDER_PLACED.value
        }
        
        # Mock get order returns None
        self.service._get_order_by_id = Mock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            self.service.update_order_status(request_data)
    
    def test_update_order_status_optimistic_locking_conflict(self):
        """Test order status update with optimistic locking conflict"""
        # Arrange
        order_id = 'test-order-id'
        current_order = {
            'orderId': order_id,
            'status': OrderStatus.PENDING_CONFIRMATION.value,
            'version': 1,
            'statusHistory': []
        }
        
        request_data = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=current_order)
        
        # Mock update_item to raise ConditionalCheckFailedException
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ConditionalCheckFailedException',
                'Message': 'The conditional request failed'
            }
        }
        self.mock_orders_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            self.service.update_order_status(request_data)
        
        assert 'modified by another process' in str(exc_info.value)
    
    def test_get_order_success(self):
        """Test successful order retrieval"""
        # Arrange
        order_id = 'test-order-id'
        order_data = {
            'orderId': order_id,
            'consumerId': '123e4567-e89b-12d3-a456-426614174000',
            'deviceType': 'Water Quality Monitor',
            'status': OrderStatus.ORDER_PLACED.value,
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00',
            'statusHistory': []
        }
        
        # Mock get order
        self.service._get_order_by_id = Mock(return_value=order_data)
        
        # Act
        result = self.service.get_order(order_id)
        
        # Assert
        assert result['success'] is True
        assert result['data']['id'] == order_id
        assert result['data']['status'] == OrderStatus.ORDER_PLACED.value
    
    def test_get_order_not_found(self):
        """Test order retrieval when order doesn't exist"""
        # Arrange
        order_id = 'non-existent-order'
        
        # Mock get order returns None
        self.service._get_order_by_id = Mock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            self.service.get_order(order_id)
    
    def test_get_orders_by_consumer_success(self):
        """Test successful consumer orders retrieval"""
        # Arrange
        consumer_id = '123e4567-e89b-12d3-a456-426614174000'
        orders_data = [
            {
                'orderId': 'order-1',
                'consumerId': consumer_id,
                'status': OrderStatus.ORDER_PLACED.value,
                'createdAt': '2024-01-01T00:00:00+00:00',
                'updatedAt': '2024-01-01T00:00:00+00:00',
                'statusHistory': []
            },
            {
                'orderId': 'order-2',
                'consumerId': consumer_id,
                'status': OrderStatus.SHIPPED.value,
                'createdAt': '2024-01-02T00:00:00+00:00',
                'updatedAt': '2024-01-02T00:00:00+00:00',
                'statusHistory': []
            }
        ]
        
        # Mock query
        self.mock_orders_table.query.return_value = {
            'Items': orders_data,
            'Count': 2
        }
        
        # Act
        result = self.service.get_orders_by_consumer(consumer_id)
        
        # Assert
        assert result['success'] is True
        assert result['count'] == 2
        assert len(result['data']) == 2
        assert result['data'][0]['id'] == 'order-1'
        assert result['data'][1]['id'] == 'order-2'
        
        # Verify query parameters
        self.mock_orders_table.query.assert_called_once()
        call_args = self.mock_orders_table.query.call_args[1]
        assert call_args['IndexName'] == 'GSI1'
        assert call_args['KeyConditionExpression'] == 'GSI1PK = :consumer_pk'
        assert call_args['ExpressionAttributeValues'][':consumer_pk'] == f'CONSUMER#{consumer_id}'
    
    def test_get_orders_by_consumer_with_pagination(self):
        """Test consumer orders retrieval with pagination"""
        # Arrange
        consumer_id = '123e4567-e89b-12d3-a456-426614174000'
        last_evaluated_key = json.dumps({'GSI1PK': f'CONSUMER#{consumer_id}', 'GSI1SK': 'ORDER#2024-01-01T00:00:00+00:00#order-1'})
        
        # Mock query with LastEvaluatedKey
        self.mock_orders_table.query.return_value = {
            'Items': [],
            'Count': 0,
            'LastEvaluatedKey': {'GSI1PK': f'CONSUMER#{consumer_id}', 'GSI1SK': 'ORDER#2024-01-02T00:00:00+00:00#order-2'}
        }
        
        # Act
        result = self.service.get_orders_by_consumer(consumer_id, limit=10, last_evaluated_key=last_evaluated_key)
        
        # Assert
        assert result['success'] is True
        assert 'lastEvaluatedKey' in result
        
        # Verify ExclusiveStartKey was passed
        call_args = self.mock_orders_table.query.call_args[1]
        assert 'ExclusiveStartKey' in call_args
    
    def test_cancel_order_success(self):
        """Test successful order cancellation"""
        # Arrange
        order_id = 'test-order-id'
        reason = 'Customer requested cancellation'
        
        # Mock update_order_status
        expected_result = {
            'success': True,
            'data': {'id': order_id, 'status': OrderStatus.CANCELLED.value},
            'message': f'Order status updated to {OrderStatus.CANCELLED.value}'
        }
        self.service.update_order_status = Mock(return_value=expected_result)
        
        # Act
        result = self.service.cancel_order(order_id, reason)
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == OrderStatus.CANCELLED.value
        
        # Verify update_order_status was called correctly
        self.service.update_order_status.assert_called_once_with({
            'orderId': order_id,
            'status': OrderStatus.CANCELLED.value,
            'reason': reason
        }, None)
    
    def test_is_valid_transition(self):
        """Test state transition validation"""
        # Valid transitions
        assert self.service._is_valid_transition(OrderStatus.PENDING_CONFIRMATION, OrderStatus.ORDER_PLACED) is True
        assert self.service._is_valid_transition(OrderStatus.ORDER_PLACED, OrderStatus.SHIPPED) is True
        assert self.service._is_valid_transition(OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY) is True
        assert self.service._is_valid_transition(OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED) is True
        
        # Invalid transitions
        assert self.service._is_valid_transition(OrderStatus.DELIVERED, OrderStatus.SHIPPED) is False
        assert self.service._is_valid_transition(OrderStatus.CANCELLED, OrderStatus.ORDER_PLACED) is False
        assert self.service._is_valid_transition(OrderStatus.PENDING_CONFIRMATION, OrderStatus.DELIVERED) is False
    
    def test_convert_to_response_format(self):
        """Test conversion from DynamoDB record to API response format"""
        # Arrange
        order_record = {
            'orderId': 'test-order-id',
            'consumerId': '123e4567-e89b-12d3-a456-426614174000',
            'deviceType': 'Water Quality Monitor',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'status': OrderStatus.ORDER_PLACED.value,
            'amount': 5000.0,
            'deliveryAddress': {'street': '123 Main St'},
            'contactInfo': {'name': 'John Doe'},
            'assignedTechnician': 'tech-123',
            'paymentId': 'pay-123',
            'specialInstructions': 'Handle with care',
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00',
            'statusHistory': []
        }
        
        # Act
        result = self.service._convert_to_response_format(order_record)
        
        # Assert
        assert result['id'] == 'test-order-id'
        assert result['consumerId'] == '123e4567-e89b-12d3-a456-426614174000'
        assert result['deviceType'] == 'Water Quality Monitor'
        assert result['serviceType'] == 'Installation'
        assert result['paymentMethod'] == 'COD'
        assert result['status'] == OrderStatus.ORDER_PLACED.value
        assert result['amount'] == 5000.0
        assert result['assignedTechnician'] == 'tech-123'
        assert result['paymentId'] == 'pay-123'
        assert result['specialInstructions'] == 'Handle with care'
        assert result['createdAt'] == '2024-01-01T00:00:00+00:00'
        assert result['updatedAt'] == '2024-01-01T00:00:00+00:00'


class TestLambdaHandler:
    """Unit tests for lambda_handler function"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        os.environ['ENHANCED_ORDERS_TABLE'] = 'test-orders'
        
        # Patch the order_service
        self.mock_service = Mock()
        enhanced_order_management.order_service = self.mock_service
    
    def test_create_order_endpoint(self):
        """Test POST /orders endpoint"""
        # Arrange
        event = {
            'httpMethod': 'POST',
            'path': '/orders',
            'body': json.dumps({
                'consumerId': '123e4567-e89b-12d3-a456-426614174000',
                'deviceType': 'Water Quality Monitor',
                'serviceType': 'Installation',
                'paymentMethod': 'COD',
                'deliveryAddress': {'street': '123 Main St'},
                'contactInfo': {'name': 'John Doe'}
            })
        }
        
        expected_response = {
            'success': True,
            'data': {'id': 'test-order-id', 'status': 'PENDING_CONFIRMATION'}
        }
        self.mock_service.create_order.return_value = expected_response
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 201
        assert 'X-Correlation-ID' in response['headers']
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['id'] == 'test-order-id'
    
    def test_update_order_status_endpoint(self):
        """Test PUT /orders/{orderId}/status endpoint"""
        # Arrange
        event = {
            'httpMethod': 'PUT',
            'path': '/orders/test-order-id/status',
            'pathParameters': {'orderId': 'test-order-id'},
            'body': json.dumps({
                'status': 'ORDER_PLACED',
                'reason': 'Order confirmed'
            })
        }
        
        expected_response = {
            'success': True,
            'data': {'id': 'test-order-id', 'status': 'ORDER_PLACED'}
        }
        self.mock_service.update_order_status.return_value = expected_response
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        
        # Verify service was called with correct parameters
        call_args = self.mock_service.update_order_status.call_args[0][0]
        assert call_args['orderId'] == 'test-order-id'
        assert call_args['status'] == 'ORDER_PLACED'
        assert call_args['reason'] == 'Order confirmed'
    
    def test_get_order_endpoint(self):
        """Test GET /orders/{orderId} endpoint"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'path': '/orders/test-order-id',
            'pathParameters': {'orderId': 'test-order-id'}
        }
        
        expected_response = {
            'success': True,
            'data': {'id': 'test-order-id', 'status': 'ORDER_PLACED'}
        }
        self.mock_service.get_order.return_value = expected_response
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        
        # Verify service was called with correct order ID
        self.mock_service.get_order.assert_called_once_with('test-order-id', unittest.mock.ANY)
    
    def test_get_orders_by_consumer_endpoint(self):
        """Test GET /orders?consumerId={consumerId} endpoint"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'path': '/orders',
            'queryStringParameters': {
                'consumerId': '123e4567-e89b-12d3-a456-426614174000',
                'limit': '10'
            }
        }
        
        expected_response = {
            'success': True,
            'data': [{'id': 'order-1'}, {'id': 'order-2'}],
            'count': 2
        }
        self.mock_service.get_orders_by_consumer.return_value = expected_response
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['count'] == 2
        
        # Verify service was called with correct parameters
        self.mock_service.get_orders_by_consumer.assert_called_once_with(
            '123e4567-e89b-12d3-a456-426614174000', 10, None, unittest.mock.ANY
        )
    
    def test_cancel_order_endpoint(self):
        """Test PUT /orders/{orderId}/cancel endpoint"""
        # Arrange
        event = {
            'httpMethod': 'PUT',
            'path': '/orders/test-order-id/cancel',
            'pathParameters': {'orderId': 'test-order-id'},
            'body': json.dumps({
                'reason': 'Customer requested cancellation'
            })
        }
        
        expected_response = {
            'success': True,
            'data': {'id': 'test-order-id', 'status': 'CANCELLED'}
        }
        self.mock_service.cancel_order.return_value = expected_response
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        
        # Verify service was called with correct parameters
        self.mock_service.cancel_order.assert_called_once_with(
            'test-order-id', 'Customer requested cancellation', unittest.mock.ANY
        )
    
    def test_unsupported_operation(self):
        """Test unsupported HTTP method/path combination"""
        # Arrange
        event = {
            'httpMethod': 'DELETE',
            'path': '/orders/test-order-id'
        }
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] is True
        assert 'Unsupported operation' in body['message']
    
    def test_invalid_json_body(self):
        """Test request with invalid JSON body"""
        # Arrange
        event = {
            'httpMethod': 'POST',
            'path': '/orders',
            'body': 'invalid json'
        }
        
        # Act
        response = enhanced_order_management.lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] is True
        assert 'Invalid JSON' in body['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])