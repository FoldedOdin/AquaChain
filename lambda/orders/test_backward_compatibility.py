"""
Test backward compatibility of DeviceOrders API

This test verifies that:
1. GET /api/device-orders/:orderId returns "shipped" status
2. Existing UI components work without changes
3. Internal shipment fields are not exposed

Requirements: 8.1, 8.2, 8.3
"""
import sys
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the handler
from orders.get_orders import (
    handler,
    ensure_backward_compatibility,
    extract_user_id,
    extract_user_role
)


class TestBackwardCompatibility:
    """Test backward compatibility of DeviceOrders API"""
    
    def test_ensure_backward_compatibility_removes_shipment_fields(self):
        """
        Test that shipment_id and tracking_number are removed from response
        
        Requirements: 8.1, 8.2
        """
        # Arrange
        orders = [
            {
                'orderId': 'ord_123',
                'userId': 'user_456',
                'status': 'shipped',
                'shipment_id': 'ship_789',  # Should be removed
                'tracking_number': 'TRACK123',  # Should be removed
                'deviceSKU': 'AQ-001',
                'address': '123 Main St'
            },
            {
                'orderId': 'ord_124',
                'userId': 'user_456',
                'status': 'pending',
                'deviceSKU': 'AQ-002',
                'address': '456 Oak Ave'
            }
        ]
        
        # Act
        result = ensure_backward_compatibility(orders)
        
        # Assert
        assert len(result) == 2
        
        # First order should not have shipment fields
        assert 'shipment_id' not in result[0]
        assert 'tracking_number' not in result[0]
        assert result[0]['status'] == 'shipped'
        assert result[0]['orderId'] == 'ord_123'
        
        # Second order should remain unchanged
        assert result[1]['orderId'] == 'ord_124'
        assert result[1]['status'] == 'pending'
    
    def test_ensure_backward_compatibility_preserves_status(self):
        """
        Test that status field remains unchanged
        
        Requirements: 8.2
        """
        # Arrange
        orders = [
            {
                'orderId': 'ord_123',
                'status': 'shipped',
                'shipment_id': 'ship_789'
            }
        ]
        
        # Act
        result = ensure_backward_compatibility(orders)
        
        # Assert
        assert result[0]['status'] == 'shipped'
        assert 'shipment_id' not in result[0]
    
    def test_ensure_backward_compatibility_handles_orders_without_shipment_fields(self):
        """
        Test that orders without shipment fields are not affected
        
        Requirements: 8.3
        """
        # Arrange
        orders = [
            {
                'orderId': 'ord_123',
                'userId': 'user_456',
                'status': 'pending',
                'deviceSKU': 'AQ-001'
            }
        ]
        
        # Act
        result = ensure_backward_compatibility(orders)
        
        # Assert
        assert len(result) == 1
        assert result[0]['orderId'] == 'ord_123'
        assert result[0]['status'] == 'pending'
        assert 'shipment_id' not in result[0]
        assert 'tracking_number' not in result[0]
    
    def test_extract_user_id_from_event(self):
        """Test extracting user ID from event context"""
        # Arrange
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user_123'
                    }
                }
            }
        }
        
        # Act
        user_id = extract_user_id(event)
        
        # Assert
        assert user_id == 'user_123'
    
    def test_extract_user_role_admin(self):
        """Test extracting admin role from event context"""
        # Arrange
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'custom:role': 'admin'
                    }
                }
            }
        }
        
        # Act
        role = extract_user_role(event)
        
        # Assert
        assert role == 'admin'
    
    def test_extract_user_role_from_cognito_groups(self):
        """Test extracting role from cognito:groups"""
        # Arrange
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'admin,users'
                    }
                }
            }
        }
        
        # Act
        role = extract_user_role(event)
        
        # Assert
        assert role == 'admin'
    
    @patch('orders.get_orders.dynamodb')
    def test_handler_returns_backward_compatible_response(self, mock_dynamodb):
        """
        Test that handler returns backward-compatible response
        
        Requirements: 8.1, 8.2, 8.3
        """
        # Arrange
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock DynamoDB response with shipment fields
        mock_table.query.return_value = {
            'Items': [
                {
                    'orderId': 'ord_123',
                    'userId': 'user_456',
                    'status': 'shipped',
                    'shipment_id': 'ship_789',
                    'tracking_number': 'TRACK123',
                    'deviceSKU': 'AQ-001',
                    'address': '123 Main St',
                    'createdAt': '2025-01-01T00:00:00Z'
                }
            ]
        }
        
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user_456',
                        'custom:role': 'consumer'
                    }
                }
            },
            'queryStringParameters': None
        }
        
        context = Mock()
        context.request_id = 'test-request-123'
        
        # Act
        response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert len(body['orders']) == 1
        
        # Verify shipment fields are not exposed
        order = body['orders'][0]
        assert 'shipment_id' not in order
        assert 'tracking_number' not in order
        
        # Verify status is unchanged
        assert order['status'] == 'shipped'
        assert order['orderId'] == 'ord_123'
    
    @patch('orders.get_orders.dynamodb')
    def test_handler_admin_can_see_all_orders(self, mock_dynamodb):
        """
        Test that admin can see all orders
        
        Requirements: 8.3
        """
        # Arrange
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        mock_table.scan.return_value = {
            'Items': [
                {
                    'orderId': 'ord_123',
                    'userId': 'user_456',
                    'status': 'shipped',
                    'shipment_id': 'ship_789'
                },
                {
                    'orderId': 'ord_124',
                    'userId': 'user_789',
                    'status': 'pending'
                }
            ]
        }
        
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'admin_123',
                        'custom:role': 'admin'
                    }
                }
            },
            'queryStringParameters': None
        }
        
        context = Mock()
        context.request_id = 'test-request-123'
        
        # Act
        response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert len(body['orders']) == 2
        
        # Verify shipment fields are not exposed in any order
        for order in body['orders']:
            assert 'shipment_id' not in order
            assert 'tracking_number' not in order
    
    @patch('orders.get_orders.dynamodb')
    def test_handler_filters_by_status(self, mock_dynamodb):
        """
        Test that handler can filter orders by status
        
        Requirements: 8.3
        """
        # Arrange
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        mock_table.query.return_value = {
            'Items': [
                {
                    'orderId': 'ord_123',
                    'userId': 'user_456',
                    'status': 'shipped',
                    'shipment_id': 'ship_789'
                }
            ]
        }
        
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user_456',
                        'custom:role': 'consumer'
                    }
                }
            },
            'queryStringParameters': {
                'status': 'shipped'
            }
        }
        
        context = Mock()
        context.request_id = 'test-request-123'
        
        # Act
        response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert len(body['orders']) == 1
        assert body['orders'][0]['status'] == 'shipped'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
