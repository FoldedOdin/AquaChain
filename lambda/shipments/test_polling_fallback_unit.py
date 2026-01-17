"""
Unit tests for polling fallback mechanism
Requirements: 9.1, 9.2, 9.3

Tests cover:
- Stale shipment detection
- Courier API querying
- Status update from polling
- Error handling for API failures
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call

# Import functions from polling_fallback
from polling_fallback import (
    handler,
    get_active_shipments,
    filter_stale_shipments,
    poll_courier_status,
    query_courier_tracking_api,
    query_delhivery_tracking,
    map_courier_status,
    update_shipment_from_polling,
    update_shipment_timestamp
)


class TestStaleShipmentDetection:
    """
    Test stale shipment detection functionality
    Requirements: 9.1
    """
    
    @patch('polling_fallback.dynamodb')
    def test_get_active_shipments_excludes_terminal_statuses(self, mock_dynamodb):
        """Test that terminal statuses are excluded from active shipments"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock scan response with mixed statuses
        mock_table.scan.return_value = {
            'Items': [
                {'shipment_id': 'ship_1', 'internal_status': 'in_transit'},
                {'shipment_id': 'ship_2', 'internal_status': 'delivered'},
                {'shipment_id': 'ship_3', 'internal_status': 'out_for_delivery'},
                {'shipment_id': 'ship_4', 'internal_status': 'returned'},
                {'shipment_id': 'ship_5', 'internal_status': 'picked_up'},
                {'shipment_id': 'ship_6', 'internal_status': 'cancelled'}
            ]
        }
        
        # Execute
        result = get_active_shipments()
        
        # Verify
        assert len(result) == 3
        active_ids = [s['shipment_id'] for s in result]
        assert 'ship_1' in active_ids  # in_transit
        assert 'ship_3' in active_ids  # out_for_delivery
        assert 'ship_5' in active_ids  # picked_up
        assert 'ship_2' not in active_ids  # delivered
        assert 'ship_4' not in active_ids  # returned
        assert 'ship_6' not in active_ids  # cancelled
    
    @patch('polling_fallback.dynamodb')
    def test_get_active_shipments_handles_pagination(self, mock_dynamodb):
        """Test that pagination is handled correctly"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock paginated scan responses
        mock_table.scan.side_effect = [
            {
                'Items': [
                    {'shipment_id': 'ship_1', 'internal_status': 'in_transit'}
                ],
                'LastEvaluatedKey': {'shipment_id': 'ship_1'}
            },
            {
                'Items': [
                    {'shipment_id': 'ship_2', 'internal_status': 'picked_up'}
                ]
            }
        ]
        
        # Execute
        result = get_active_shipments()
        
        # Verify
        assert len(result) == 2
        assert mock_table.scan.call_count == 2
    
    @patch('polling_fallback.dynamodb')
    def test_get_active_shipments_handles_empty_table(self, mock_dynamodb):
        """Test handling of empty table"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.scan.return_value = {'Items': []}
        
        # Execute
        result = get_active_shipments()
        
        # Verify
        assert len(result) == 0
    
    def test_filter_stale_shipments_identifies_old_updates(self):
        """Test that shipments with old updated_at are identified as stale"""
        # Setup
        now = datetime.utcnow()
        old_time = (now - timedelta(hours=5)).isoformat()
        recent_time = (now - timedelta(hours=2)).isoformat()
        
        shipments = [
            {'shipment_id': 'ship_1', 'updated_at': old_time},
            {'shipment_id': 'ship_2', 'updated_at': recent_time},
            {'shipment_id': 'ship_3', 'updated_at': old_time}
        ]
        
        # Execute
        result = filter_stale_shipments(shipments, threshold_hours=4)
        
        # Verify
        assert len(result) == 2
        stale_ids = [s['shipment_id'] for s in result]
        assert 'ship_1' in stale_ids
        assert 'ship_3' in stale_ids
        assert 'ship_2' not in stale_ids
    
    def test_filter_stale_shipments_handles_missing_updated_at(self):
        """Test that shipments without updated_at are considered stale"""
        # Setup
        shipments = [
            {'shipment_id': 'ship_1', 'updated_at': ''},
            {'shipment_id': 'ship_2'}  # No updated_at field
        ]
        
        # Execute
        result = filter_stale_shipments(shipments, threshold_hours=4)
        
        # Verify
        assert len(result) == 2
    
    def test_filter_stale_shipments_handles_invalid_timestamp(self):
        """Test that shipments with invalid timestamps are considered stale"""
        # Setup
        shipments = [
            {'shipment_id': 'ship_1', 'updated_at': 'invalid-timestamp'}
        ]
        
        # Execute
        result = filter_stale_shipments(shipments, threshold_hours=4)
        
        # Verify
        assert len(result) == 1
    
    def test_filter_stale_shipments_respects_threshold(self):
        """Test that different thresholds work correctly"""
        # Setup
        now = datetime.utcnow()
        shipments = [
            {'shipment_id': 'ship_1', 'updated_at': (now - timedelta(hours=2)).isoformat()},
            {'shipment_id': 'ship_2', 'updated_at': (now - timedelta(hours=5)).isoformat()},
            {'shipment_id': 'ship_3', 'updated_at': (now - timedelta(hours=8)).isoformat()}
        ]
        
        # Execute with 3 hour threshold
        result_3h = filter_stale_shipments(shipments, threshold_hours=3)
        
        # Verify
        assert len(result_3h) == 2  # ship_2 and ship_3
        
        # Execute with 6 hour threshold
        result_6h = filter_stale_shipments(shipments, threshold_hours=6)
        
        # Verify
        assert len(result_6h) == 1  # only ship_3


class TestCourierAPIQuerying:
    """
    Test courier API querying functionality
    Requirements: 9.2
    """
    
    @patch('polling_fallback.requests.get')
    @patch('polling_fallback.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_success(self, mock_get):
        """Test successful Delhivery API query"""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ShipmentData': [{
                'Shipment': {
                    'Status': {'Status': 'In Transit'},
                    'Scans': [{
                        'ScanDetail': {
                            'ScannedLocation': 'Mumbai Hub',
                            'ScanDateTime': '2025-12-29T14:30:00Z',
                            'Instructions': 'Package in transit'
                        }
                    }]
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Execute
        result = query_delhivery_tracking('DELHUB123')
        
        # Verify
        assert result is not None
        assert result['status'] == 'In Transit'
        assert result['location'] == 'Mumbai Hub'
        assert result['timestamp'] == '2025-12-29T14:30:00Z'
        assert result['description'] == 'Package in transit'
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'DELHUB123' in call_args[0][0]
        assert call_args[1]['headers']['Authorization'] == 'Token test-api-key'
    
    @patch('polling_fallback.requests.get')
    @patch('polling_fallback.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_no_shipment_data(self, mock_get):
        """Test Delhivery API response with no shipment data"""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {'ShipmentData': []}
        mock_get.return_value = mock_response
        
        # Execute
        result = query_delhivery_tracking('DELHUB123')
        
        # Verify
        assert result is None
    
    @patch('polling_fallback.requests.get')
    @patch('polling_fallback.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_api_error(self, mock_get):
        """Test handling of Delhivery API errors"""
        # Setup
        mock_get.side_effect = Exception("API timeout")
        
        # Execute
        result = query_delhivery_tracking('DELHUB123')
        
        # Verify
        assert result is None
    
    @patch('polling_fallback.DELHIVERY_API_KEY', '')
    def test_query_delhivery_tracking_no_api_key(self):
        """Test handling when API key is not configured"""
        # Execute
        result = query_delhivery_tracking('DELHUB123')
        
        # Verify
        assert result is None
    
    @patch('polling_fallback.query_delhivery_tracking')
    @patch('polling_fallback.query_bluedart_tracking')
    @patch('polling_fallback.query_dtdc_tracking')
    def test_query_courier_tracking_api_routes_correctly(
        self, mock_dtdc, mock_bluedart, mock_delhivery
    ):
        """Test that courier API queries are routed correctly"""
        # Setup
        mock_delhivery.return_value = {'status': 'In Transit'}
        mock_bluedart.return_value = {'status': 'DELIVERED'}
        mock_dtdc.return_value = {'status': 'PICKED'}
        
        # Test Delhivery
        result = query_courier_tracking_api('Delhivery', 'TRACK123')
        assert result == {'status': 'In Transit'}
        mock_delhivery.assert_called_once_with('TRACK123')
        
        # Test BlueDart
        result = query_courier_tracking_api('BlueDart', 'TRACK456')
        assert result == {'status': 'DELIVERED'}
        mock_bluedart.assert_called_once_with('TRACK456')
        
        # Test DTDC
        result = query_courier_tracking_api('DTDC', 'TRACK789')
        assert result == {'status': 'PICKED'}
        mock_dtdc.assert_called_once_with('TRACK789')
    
    def test_query_courier_tracking_api_unknown_courier(self):
        """Test handling of unknown courier"""
        # Execute
        result = query_courier_tracking_api('UnknownCourier', 'TRACK123')
        
        # Verify
        assert result is None
    
    def test_map_courier_status_delhivery(self):
        """Test mapping of Delhivery statuses"""
        assert map_courier_status('Picked Up') == 'picked_up'
        assert map_courier_status('In Transit') == 'in_transit'
        assert map_courier_status('Out for Delivery') == 'out_for_delivery'
        assert map_courier_status('Delivered') == 'delivered'
        assert map_courier_status('Delivery Failed') == 'delivery_failed'
        assert map_courier_status('RTO') == 'returned'
    
    def test_map_courier_status_case_insensitive(self):
        """Test that status mapping is case-insensitive"""
        assert map_courier_status('in transit') == 'in_transit'
        assert map_courier_status('IN TRANSIT') == 'in_transit'
        assert map_courier_status('In Transit') == 'in_transit'
    
    def test_map_courier_status_unknown(self):
        """Test that unknown statuses default to in_transit"""
        assert map_courier_status('Unknown Status') == 'in_transit'
        assert map_courier_status('') == 'in_transit'
        assert map_courier_status(None) == 'in_transit'


class TestStatusUpdateFromPolling:
    """
    Test status update from polling functionality
    Requirements: 9.3
    """
    
    @patch('polling_fallback.dynamodb')
    @patch('polling_fallback.query_courier_tracking_api')
    @patch('polling_fallback.update_shipment_from_polling')
    def test_poll_courier_status_updates_when_status_changed(
        self, mock_update, mock_query, mock_dynamodb
    ):
        """Test that shipment is updated when status changes"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK123',
            'courier_name': 'Delhivery',
            'internal_status': 'in_transit'
        }
        
        mock_query.return_value = {
            'status': 'Out for Delivery',
            'location': 'Local Hub',
            'timestamp': '2025-12-29T16:00:00Z',
            'description': 'Out for delivery'
        }
        
        # Execute
        result = poll_courier_status(shipment)
        
        # Verify
        assert result is True
        mock_update.assert_called_once()
        call_args = mock_update.call_args[1]
        assert call_args['shipment_id'] == 'ship_123'
        assert call_args['internal_status'] == 'out_for_delivery'
        assert call_args['courier_status'] == 'Out for Delivery'
        assert call_args['location'] == 'Local Hub'
    
    @patch('polling_fallback.query_courier_tracking_api')
    @patch('polling_fallback.update_shipment_timestamp')
    def test_poll_courier_status_no_update_when_status_unchanged(
        self, mock_update_timestamp, mock_query
    ):
        """Test that only timestamp is updated when status hasn't changed"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK123',
            'courier_name': 'Delhivery',
            'internal_status': 'in_transit'
        }
        
        mock_query.return_value = {
            'status': 'In Transit',
            'location': 'Mumbai Hub',
            'timestamp': '2025-12-29T16:00:00Z',
            'description': 'In transit'
        }
        
        # Execute
        result = poll_courier_status(shipment)
        
        # Verify
        assert result is False
        mock_update_timestamp.assert_called_once_with('ship_123')
    
    @patch('polling_fallback.query_courier_tracking_api')
    def test_poll_courier_status_handles_no_response(self, mock_query):
        """Test handling when courier API returns no response"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK123',
            'courier_name': 'Delhivery',
            'internal_status': 'in_transit'
        }
        
        mock_query.return_value = None
        
        # Execute
        result = poll_courier_status(shipment)
        
        # Verify
        assert result is False
    
    @patch('polling_fallback.query_courier_tracking_api')
    def test_poll_courier_status_handles_missing_status(self, mock_query):
        """Test handling when courier response has no status"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK123',
            'courier_name': 'Delhivery',
            'internal_status': 'in_transit'
        }
        
        mock_query.return_value = {
            'location': 'Mumbai Hub',
            'timestamp': '2025-12-29T16:00:00Z'
        }
        
        # Execute
        result = poll_courier_status(shipment)
        
        # Verify
        assert result is False
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_from_polling_creates_timeline_entry(self, mock_dynamodb):
        """Test that timeline entry is created with polling marker"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        update_shipment_from_polling(
            shipment_id='ship_123',
            internal_status='out_for_delivery',
            courier_status='Out for Delivery',
            location='Local Hub',
            timestamp='2025-12-29T16:00:00Z',
            description='Out for delivery'
        )
        
        # Verify
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        
        # Verify timeline entry
        timeline_entry = call_args['ExpressionAttributeValues'][':timeline'][0]
        assert timeline_entry['status'] == 'out_for_delivery'
        assert timeline_entry['location'] == 'Local Hub'
        assert '(from polling)' in timeline_entry['description']
        
        # Verify polling event
        polling_event = call_args['ExpressionAttributeValues'][':event'][0]
        assert polling_event['source'] == 'polling'
        assert polling_event['courier_status'] == 'Out for Delivery'
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_from_polling_sets_delivered_at(self, mock_dynamodb):
        """Test that delivered_at is set for delivered status"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        update_shipment_from_polling(
            shipment_id='ship_123',
            internal_status='delivered',
            courier_status='Delivered',
            location='Customer Address',
            timestamp='2025-12-29T18:00:00Z',
            description='Delivered successfully'
        )
        
        # Verify
        call_args = mock_table.update_item.call_args[1]
        assert 'delivered_at' in call_args['UpdateExpression']
        assert call_args['ExpressionAttributeValues'][':delivered'] == '2025-12-29T18:00:00Z'
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_from_polling_sets_failed_at(self, mock_dynamodb):
        """Test that failed_at is set for delivery_failed status"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        update_shipment_from_polling(
            shipment_id='ship_123',
            internal_status='delivery_failed',
            courier_status='Delivery Failed',
            location='Customer Address',
            timestamp='2025-12-29T18:00:00Z',
            description='Customer unavailable'
        )
        
        # Verify
        call_args = mock_table.update_item.call_args[1]
        assert 'failed_at' in call_args['UpdateExpression']
        assert call_args['ExpressionAttributeValues'][':failed'] == '2025-12-29T18:00:00Z'
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_timestamp_updates_only_timestamp(self, mock_dynamodb):
        """Test that update_shipment_timestamp only updates updated_at"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        update_shipment_timestamp('ship_123')
        
        # Verify
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        assert call_args['UpdateExpression'] == 'SET updated_at = :time'
        assert ':time' in call_args['ExpressionAttributeValues']


class TestErrorHandling:
    """
    Test error handling for API failures
    Requirements: 9.2, 9.3
    """
    
    @patch('polling_fallback.dynamodb')
    def test_get_active_shipments_handles_dynamodb_error(self, mock_dynamodb):
        """Test handling of DynamoDB errors"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.scan.side_effect = Exception("DynamoDB error")
        
        # Execute and verify exception is raised
        with pytest.raises(Exception) as exc_info:
            get_active_shipments()
        
        assert "DynamoDB error" in str(exc_info.value)
    
    @patch('polling_fallback.query_courier_tracking_api')
    def test_poll_courier_status_handles_api_exception(self, mock_query):
        """Test handling of courier API exceptions"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK123',
            'courier_name': 'Delhivery',
            'internal_status': 'in_transit'
        }
        
        mock_query.side_effect = Exception("API timeout")
        
        # Execute and verify exception is raised
        with pytest.raises(Exception) as exc_info:
            poll_courier_status(shipment)
        
        assert "API timeout" in str(exc_info.value)
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_from_polling_handles_update_error(self, mock_dynamodb):
        """Test handling of DynamoDB update errors"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.side_effect = Exception("Update failed")
        
        # Execute and verify exception is raised
        with pytest.raises(Exception) as exc_info:
            update_shipment_from_polling(
                shipment_id='ship_123',
                internal_status='delivered',
                courier_status='Delivered',
                location='Customer',
                timestamp='2025-12-29T18:00:00Z',
                description='Delivered'
            )
        
        assert "Update failed" in str(exc_info.value)
    
    @patch('polling_fallback.dynamodb')
    def test_update_shipment_timestamp_handles_error_gracefully(self, mock_dynamodb):
        """Test that timestamp update errors don't crash"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.side_effect = Exception("Update failed")
        
        # Execute - should not raise exception
        update_shipment_timestamp('ship_123')
        
        # Verify - function completed despite error
        mock_table.update_item.assert_called_once()


class TestHandlerEndToEnd:
    """
    Test end-to-end handler functionality
    Requirements: 9.1, 9.2, 9.3
    """
    
    @patch('polling_fallback.get_active_shipments')
    @patch('polling_fallback.filter_stale_shipments')
    @patch('polling_fallback.poll_courier_status')
    def test_handler_processes_stale_shipments(
        self, mock_poll, mock_filter, mock_get_active
    ):
        """Test handler processes stale shipments successfully"""
        # Setup
        mock_context = MagicMock()
        mock_context.request_id = 'test-request-123'
        
        active_shipments = [
            {
                'shipment_id': 'ship_1',
                'tracking_number': 'TRACK1',
                'courier_name': 'Delhivery',
                'internal_status': 'in_transit'
            },
            {
                'shipment_id': 'ship_2',
                'tracking_number': 'TRACK2',
                'courier_name': 'Delhivery',
                'internal_status': 'picked_up'
            },
            {
                'shipment_id': 'ship_3',
                'tracking_number': 'TRACK3',
                'courier_name': 'Delhivery',
                'internal_status': 'in_transit'
            }
        ]
        
        stale_shipments = [
            {
                'shipment_id': 'ship_1',
                'tracking_number': 'TRACK1',
                'courier_name': 'Delhivery',
                'internal_status': 'in_transit'
            },
            {
                'shipment_id': 'ship_2',
                'tracking_number': 'TRACK2',
                'courier_name': 'Delhivery',
                'internal_status': 'picked_up'
            }
        ]
        
        mock_get_active.return_value = active_shipments
        mock_filter.return_value = stale_shipments
        mock_poll.side_effect = [True, False]  # First updated, second not
        
        # Execute
        response = handler({}, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['shipments_checked'] == 2
        assert body['shipments_updated'] == 1
        assert len(body['errors']) == 0
        
        # Verify functions called
        mock_get_active.assert_called_once()
        mock_filter.assert_called_once()
        assert mock_poll.call_count == 2
    
    @patch('polling_fallback.get_active_shipments')
    @patch('polling_fallback.filter_stale_shipments')
    @patch('polling_fallback.poll_courier_status')
    def test_handler_handles_polling_errors(
        self, mock_poll, mock_filter, mock_get_active
    ):
        """Test handler continues despite individual polling errors"""
        # Setup
        mock_context = MagicMock()
        mock_context.request_id = 'test-request-123'
        
        stale_shipments = [
            {
                'shipment_id': 'ship_1',
                'tracking_number': 'TRACK1',
                'courier_name': 'Delhivery',
                'internal_status': 'in_transit'
            },
            {
                'shipment_id': 'ship_2',
                'tracking_number': 'TRACK2',
                'courier_name': 'Delhivery',
                'internal_status': 'picked_up'
            },
            {
                'shipment_id': 'ship_3',
                'tracking_number': 'TRACK3',
                'courier_name': 'Delhivery',
                'internal_status': 'in_transit'
            }
        ]
        
        mock_get_active.return_value = stale_shipments
        mock_filter.return_value = stale_shipments
        mock_poll.side_effect = [
            True,  # First succeeds
            Exception("API error"),  # Second fails
            True  # Third succeeds
        ]
        
        # Execute
        response = handler({}, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['shipments_checked'] == 3
        assert body['shipments_updated'] == 2
        assert len(body['errors']) == 1
        assert 'ship_2' in body['errors'][0]
    
    @patch('polling_fallback.get_active_shipments')
    def test_handler_handles_get_active_shipments_error(self, mock_get_active):
        """Test handler handles errors in get_active_shipments"""
        # Setup
        mock_context = MagicMock()
        mock_context.request_id = 'test-request-123'
        
        mock_get_active.side_effect = Exception("DynamoDB error")
        
        # Execute
        response = handler({}, mock_context)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'DynamoDB error' in body['error']
    
    @patch('polling_fallback.get_active_shipments')
    @patch('polling_fallback.filter_stale_shipments')
    def test_handler_handles_no_stale_shipments(self, mock_filter, mock_get_active):
        """Test handler handles case with no stale shipments"""
        # Setup
        mock_context = MagicMock()
        mock_context.request_id = 'test-request-123'
        
        mock_get_active.return_value = [{'shipment_id': 'ship_1'}]
        mock_filter.return_value = []  # No stale shipments
        
        # Execute
        response = handler({}, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['shipments_checked'] == 0
        assert body['shipments_updated'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
