"""
Unit tests for get_shipment_status Lambda function

Tests:
- Shipment lookup by shipment_id
- Shipment lookup by order_id
- Progress calculation for all statuses
- Timeline formatting
- Error handling (not found, missing params)

Requirements: 3.1, 3.2
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from get_shipment_status import (
    handler,
    calculate_delivery_progress,
    format_timeline,
    error_response
)


@pytest.fixture
def sample_shipment():
    """Sample shipment data for testing"""
    return {
        'shipment_id': 'ship_1735478400000',
        'order_id': 'ord_1735392000000',
        'tracking_number': 'DELHUB123456789',
        'courier_name': 'Delhivery',
        'internal_status': 'in_transit',
        'destination': {
            'address': '123 Main St, Bangalore',
            'pincode': '560001',
            'contact_name': 'John Doe',
            'contact_phone': '+919876543210'
        },
        'estimated_delivery': '2025-12-31T18:00:00Z',
        'delivered_at': None,
        'created_at': '2025-12-29T12:00:00Z',
        'timeline': [
            {
                'status': 'shipment_created',
                'timestamp': '2025-12-29T12:00:00Z',
                'location': 'Mumbai Warehouse',
                'description': 'Shipment created'
            },
            {
                'status': 'picked_up',
                'timestamp': '2025-12-29T14:30:00Z',
                'location': 'Mumbai Hub',
                'description': 'Package picked up'
            },
            {
                'status': 'in_transit',
                'timestamp': '2025-12-29T18:00:00Z',
                'location': 'Pune Hub',
                'description': 'Package in transit'
            }
        ]
    }


@pytest.fixture
def delivered_shipment():
    """Sample delivered shipment for testing"""
    return {
        'shipment_id': 'ship_1735564800000',
        'order_id': 'ord_1735392000001',
        'tracking_number': 'DELHUB987654321',
        'courier_name': 'Delhivery',
        'internal_status': 'delivered',
        'destination': {
            'address': '456 Park Ave, Delhi',
            'pincode': '110001',
            'contact_name': 'Jane Smith',
            'contact_phone': '+919876543211'
        },
        'estimated_delivery': '2025-12-30T18:00:00Z',
        'delivered_at': '2025-12-30T16:30:00Z',
        'created_at': '2025-12-28T10:00:00Z',
        'timeline': [
            {
                'status': 'shipment_created',
                'timestamp': '2025-12-28T10:00:00Z',
                'location': 'Delhi Warehouse',
                'description': 'Shipment created'
            },
            {
                'status': 'delivered',
                'timestamp': '2025-12-30T16:30:00Z',
                'location': 'Customer Address',
                'description': 'Successfully delivered'
            }
        ]
    }


class TestShipmentLookupByShipmentId:
    """Test shipment lookup by shipment_id"""
    
    @patch('get_shipment_status.dynamodb')
    def test_successful_lookup_by_shipment_id(self, mock_dynamodb, sample_shipment):
        """Test successful shipment lookup by shipment_id"""
        # Setup mock
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': sample_shipment}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {'shipmentId': 'ship_1735478400000'},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['shipment']['shipment_id'] == 'ship_1735478400000'
        assert body['shipment']['tracking_number'] == 'DELHUB123456789'
        assert body['shipment']['internal_status'] == 'in_transit'
        assert 'progress' in body
        assert 'timeline' in body['shipment']
        
        # Verify DynamoDB call
        mock_table.get_item.assert_called_once_with(
            Key={'shipment_id': 'ship_1735478400000'}
        )
    
    @patch('get_shipment_status.dynamodb')
    def test_shipment_not_found_by_id(self, mock_dynamodb):
        """Test shipment not found by shipment_id"""
        # Setup mock
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {'shipmentId': 'ship_nonexistent'},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'not found' in body['error'].lower()


class TestShipmentLookupByOrderId:
    """Test shipment lookup by order_id"""
    
    @patch('get_shipment_status.dynamodb')
    def test_successful_lookup_by_order_id(self, mock_dynamodb, sample_shipment):
        """Test successful shipment lookup by order_id"""
        # Setup mock
        mock_table = Mock()
        mock_table.query.return_value = {'Items': [sample_shipment]}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {},
            'queryStringParameters': {'orderId': 'ord_1735392000000'}
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['shipment']['order_id'] == 'ord_1735392000000'
        assert body['shipment']['shipment_id'] == 'ship_1735478400000'
        
        # Verify DynamoDB query
        mock_table.query.assert_called_once()
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs['IndexName'] == 'order_id-index'
        assert ':order_id' in call_kwargs['ExpressionAttributeValues']
    
    @patch('get_shipment_status.dynamodb')
    def test_shipment_not_found_by_order_id(self, mock_dynamodb):
        """Test shipment not found by order_id"""
        # Setup mock
        mock_table = Mock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {},
            'queryStringParameters': {'orderId': 'ord_nonexistent'}
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'not found' in body['error'].lower()


class TestProgressCalculation:
    """Test progress calculation for all statuses"""
    
    def test_progress_shipment_created(self):
        """Test progress calculation for shipment_created status"""
        shipment = {
            'internal_status': 'shipment_created',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 10
        assert progress['current_status'] == 'shipment_created'
        assert progress['status_display'] == 'Shipment Created'
        assert progress['status_color'] == 'blue'
        assert 'ready for pickup' in progress['status_message'].lower()
        assert progress['is_completed'] is False
    
    def test_progress_picked_up(self):
        """Test progress calculation for picked_up status"""
        shipment = {
            'internal_status': 'picked_up',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 30
        assert progress['current_status'] == 'picked_up'
        assert progress['status_display'] == 'Picked Up'
        assert progress['status_color'] == 'blue'
        assert 'picked up' in progress['status_message'].lower()
        assert progress['is_completed'] is False
    
    def test_progress_in_transit(self):
        """Test progress calculation for in_transit status"""
        shipment = {
            'internal_status': 'in_transit',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 60
        assert progress['current_status'] == 'in_transit'
        assert progress['status_display'] == 'In Transit'
        assert progress['status_color'] == 'blue'
        assert 'on the way' in progress['status_message'].lower()
        assert progress['is_completed'] is False
    
    def test_progress_out_for_delivery(self):
        """Test progress calculation for out_for_delivery status"""
        shipment = {
            'internal_status': 'out_for_delivery',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 90
        assert progress['current_status'] == 'out_for_delivery'
        assert progress['status_display'] == 'Out For Delivery'
        assert progress['status_color'] == 'green'
        assert 'out for delivery' in progress['status_message'].lower()
        assert progress['is_completed'] is False
    
    def test_progress_delivered(self):
        """Test progress calculation for delivered status"""
        shipment = {
            'internal_status': 'delivered',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'delivered_at': '2025-12-30T16:30:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 100
        assert progress['current_status'] == 'delivered'
        assert progress['status_display'] == 'Delivered'
        assert progress['status_color'] == 'green'
        assert 'successfully delivered' in progress['status_message'].lower()
        assert progress['is_completed'] is True
        assert progress['actual_delivery'] == '2025-12-30T16:30:00Z'
    
    def test_progress_delivery_failed(self):
        """Test progress calculation for delivery_failed status"""
        shipment = {
            'internal_status': 'delivery_failed',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 0
        assert progress['current_status'] == 'delivery_failed'
        assert progress['status_display'] == 'Delivery Failed'
        assert progress['status_color'] == 'red'
        assert 'failed' in progress['status_message'].lower()
        assert progress['is_completed'] is False
    
    def test_progress_returned(self):
        """Test progress calculation for returned status"""
        shipment = {
            'internal_status': 'returned',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 0
        assert progress['current_status'] == 'returned'
        assert progress['status_display'] == 'Returned'
        assert progress['status_color'] == 'orange'
        assert 'returned' in progress['status_message'].lower()
        assert progress['is_completed'] is True
    
    def test_progress_cancelled(self):
        """Test progress calculation for cancelled status"""
        shipment = {
            'internal_status': 'cancelled',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': []
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['percentage'] == 0
        assert progress['current_status'] == 'cancelled'
        assert progress['status_display'] == 'Cancelled'
        assert progress['status_color'] == 'gray'
        assert 'cancelled' in progress['status_message'].lower()
        assert progress['is_completed'] is True
    
    def test_progress_includes_timeline_count(self):
        """Test that progress includes timeline entry count"""
        shipment = {
            'internal_status': 'in_transit',
            'estimated_delivery': '2025-12-31T18:00:00Z',
            'timeline': [
                {'status': 'shipment_created', 'timestamp': '2025-12-29T12:00:00Z'},
                {'status': 'picked_up', 'timestamp': '2025-12-29T14:30:00Z'},
                {'status': 'in_transit', 'timestamp': '2025-12-29T18:00:00Z'}
            ]
        }
        
        progress = calculate_delivery_progress(shipment)
        
        assert progress['timeline_count'] == 3


class TestTimelineFormatting:
    """Test timeline formatting for UI"""
    
    def test_format_empty_timeline(self):
        """Test formatting empty timeline"""
        timeline = []
        
        formatted = format_timeline(timeline)
        
        assert formatted == []
    
    def test_format_single_entry_timeline(self):
        """Test formatting timeline with single entry"""
        timeline = [
            {
                'status': 'shipment_created',
                'timestamp': '2025-12-29T12:00:00Z',
                'location': 'Mumbai Warehouse',
                'description': 'Shipment created'
            }
        ]
        
        formatted = format_timeline(timeline)
        
        assert len(formatted) == 1
        assert formatted[0]['status'] == 'shipment_created'
        assert formatted[0]['status_display'] == 'Shipment Created'
        assert formatted[0]['icon'] == '📦'
        assert formatted[0]['timestamp'] == '2025-12-29T12:00:00Z'
        assert formatted[0]['location'] == 'Mumbai Warehouse'
        assert formatted[0]['description'] == 'Shipment created'
    
    def test_format_multiple_entries_timeline(self):
        """Test formatting timeline with multiple entries"""
        timeline = [
            {
                'status': 'shipment_created',
                'timestamp': '2025-12-29T12:00:00Z',
                'location': 'Mumbai Warehouse',
                'description': 'Shipment created'
            },
            {
                'status': 'picked_up',
                'timestamp': '2025-12-29T14:30:00Z',
                'location': 'Mumbai Hub',
                'description': 'Package picked up'
            },
            {
                'status': 'in_transit',
                'timestamp': '2025-12-29T18:00:00Z',
                'location': 'Pune Hub',
                'description': 'Package in transit'
            }
        ]
        
        formatted = format_timeline(timeline)
        
        assert len(formatted) == 3
        assert formatted[0]['icon'] == '📦'
        assert formatted[1]['icon'] == '🚚'
        assert formatted[2]['icon'] == '🛣️'
    
    def test_format_timeline_with_all_status_icons(self):
        """Test that all status types have correct icons"""
        statuses = [
            ('shipment_created', '📦'),
            ('picked_up', '🚚'),
            ('in_transit', '🛣️'),
            ('out_for_delivery', '🚛'),
            ('delivered', '✅'),
            ('delivery_failed', '❌'),
            ('returned', '↩️'),
            ('cancelled', '🚫')
        ]
        
        for status, expected_icon in statuses:
            timeline = [
                {
                    'status': status,
                    'timestamp': '2025-12-29T12:00:00Z',
                    'location': 'Test Location',
                    'description': 'Test description'
                }
            ]
            
            formatted = format_timeline(timeline)
            
            assert formatted[0]['icon'] == expected_icon, f"Icon mismatch for status {status}"
    
    def test_format_timeline_missing_optional_fields(self):
        """Test formatting timeline with missing optional fields"""
        timeline = [
            {
                'status': 'in_transit',
                'timestamp': '2025-12-29T18:00:00Z'
                # Missing location and description
            }
        ]
        
        formatted = format_timeline(timeline)
        
        assert len(formatted) == 1
        assert formatted[0]['location'] == 'Unknown'
        assert formatted[0]['description'] == 'Status update'
    
    def test_format_timeline_unknown_status(self):
        """Test formatting timeline with unknown status"""
        timeline = [
            {
                'status': 'unknown_status',
                'timestamp': '2025-12-29T18:00:00Z',
                'location': 'Test Location',
                'description': 'Test description'
            }
        ]
        
        formatted = format_timeline(timeline)
        
        assert len(formatted) == 1
        assert formatted[0]['icon'] == '📍'  # Default icon


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('get_shipment_status.dynamodb')
    def test_missing_parameters(self, mock_dynamodb):
        """Test error when both shipmentId and orderId are missing"""
        # Create event with no parameters
        event = {
            'pathParameters': {},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'required' in body['error'].lower()
    
    @patch('get_shipment_status.dynamodb')
    def test_dynamodb_exception(self, mock_dynamodb):
        """Test handling of DynamoDB exceptions"""
        # Setup mock to raise exception
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception('DynamoDB error')
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {'shipmentId': 'ship_1735478400000'},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body['error'].lower()
    
    def test_error_response_function(self):
        """Test error_response helper function"""
        response = error_response(404, 'Resource not found')
        
        assert response['statusCode'] == 404
        assert 'Content-Type' in response['headers']
        assert 'Access-Control-Allow-Origin' in response['headers']
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'Resource not found'


class TestResponseFormat:
    """Test response format and structure"""
    
    @patch('get_shipment_status.dynamodb')
    def test_response_includes_cors_headers(self, mock_dynamodb, sample_shipment):
        """Test that response includes CORS headers"""
        # Setup mock
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': sample_shipment}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {'shipmentId': 'ship_1735478400000'},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        
        # Verify headers
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Content-Type'] == 'application/json'
    
    @patch('get_shipment_status.dynamodb')
    def test_response_structure(self, mock_dynamodb, sample_shipment):
        """Test that response has correct structure"""
        # Setup mock
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': sample_shipment}
        mock_dynamodb.Table.return_value = mock_table
        
        # Create event
        event = {
            'pathParameters': {'shipmentId': 'ship_1735478400000'},
            'queryStringParameters': None
        }
        
        # Execute
        response = handler(event, None)
        body = json.loads(response['body'])
        
        # Verify structure
        assert 'success' in body
        assert 'shipment' in body
        assert 'progress' in body
        
        # Verify shipment fields
        shipment = body['shipment']
        assert 'shipment_id' in shipment
        assert 'order_id' in shipment
        assert 'tracking_number' in shipment
        assert 'courier_name' in shipment
        assert 'internal_status' in shipment
        assert 'destination' in shipment
        assert 'timeline' in shipment
        
        # Verify progress fields
        progress = body['progress']
        assert 'percentage' in progress
        assert 'current_status' in progress
        assert 'status_display' in progress
        assert 'status_color' in progress
        assert 'status_message' in progress
        assert 'is_completed' in progress


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
