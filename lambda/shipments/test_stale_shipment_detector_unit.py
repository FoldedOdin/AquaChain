"""
Unit tests for stale shipment detector
Requirements: 5.3

Tests cover:
- Stale shipment query
- Courier API fallback
- Admin task creation
- Consumer notification
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call

# Import functions from stale_shipment_detector
from stale_shipment_detector import (
    handler,
    get_stale_shipments,
    handle_stale_shipment,
    query_courier_tracking_api,
    query_delhivery_tracking,
    update_shipment_from_courier,
    mark_shipment_as_lost,
    create_stale_shipment_admin_task,
    notify_consumer_about_lost_shipment,
    map_courier_status
)


class TestStaleShipmentQuery:
    """
    Test stale shipment query functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.dynamodb')
    def test_get_stale_shipments_queries_active_statuses(self, mock_dynamodb):
        """Test that get_stale_shipments queries all active statuses"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock query responses for each status
        old_time = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        mock_table.query.return_value = {
            'Items': [
                {
                    'shipment_id': 'ship_1',
                    'internal_status': 'in_transit',
                    'updated_at': old_time,
                    'tracking_number': 'TRACK001',
                    'courier_name': 'Delhivery',
                    'order_id': 'ord_001'
                }
            ]
        }
        
        # Execute
        result = get_stale_shipments()
        
        # Verify - should query all 5 active statuses
        assert mock_table.query.call_count == 5
        
        # Verify query calls for each active status
        active_statuses = ['shipment_created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivery_failed']
        for status in active_statuses:
            mock_table.query.assert_any_call(
                IndexName='status-created_at-index',
                KeyConditionExpression='internal_status = :status',
                ExpressionAttributeValues={':status': status}
            )
    
    @patch('stale_shipment_detector.dynamodb')
    def test_get_stale_shipments_filters_by_threshold(self, mock_dynamodb):
        """Test that shipments are filtered by 7-day threshold"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        now = datetime.utcnow()
        old_time = (now - timedelta(days=10)).isoformat()
        recent_time = (now - timedelta(days=3)).isoformat()
        
        mock_table.query.return_value = {
            'Items': [
                {'shipment_id': 'ship_old', 'updated_at': old_time, 'internal_status': 'in_transit'},
                {'shipment_id': 'ship_recent', 'updated_at': recent_time, 'internal_status': 'in_transit'}
            ]
        }
        
        # Execute
        result = get_stale_shipments()
        
        # Verify - only old shipment should be returned
        stale_ids = [s['shipment_id'] for s in result]
        assert 'ship_old' in stale_ids
        assert 'ship_recent' not in stale_ids

    @patch('stale_shipment_detector.dynamodb')
    def test_get_stale_shipments_handles_missing_updated_at(self, mock_dynamodb):
        """Test that shipments without updated_at are considered stale"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        mock_table.query.return_value = {
            'Items': [
                {'shipment_id': 'ship_no_timestamp', 'internal_status': 'in_transit'},
                {'shipment_id': 'ship_empty_timestamp', 'updated_at': '', 'internal_status': 'in_transit'}
            ]
        }
        
        # Execute
        result = get_stale_shipments()
        
        # Verify - both should be considered stale
        stale_ids = [s['shipment_id'] for s in result]
        assert 'ship_no_timestamp' in stale_ids
        assert 'ship_empty_timestamp' in stale_ids
    
    @patch('stale_shipment_detector.dynamodb')
    def test_get_stale_shipments_handles_pagination(self, mock_dynamodb):
        """Test that pagination is handled correctly"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        old_time = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        # Mock paginated responses
        mock_table.query.side_effect = [
            {
                'Items': [{'shipment_id': 'ship_1', 'updated_at': old_time, 'internal_status': 'in_transit'}],
                'LastEvaluatedKey': {'shipment_id': 'ship_1'}
            },
            {
                'Items': [{'shipment_id': 'ship_2', 'updated_at': old_time, 'internal_status': 'in_transit'}]
            }
        ] * 5  # For each of the 5 active statuses
        
        # Execute
        result = get_stale_shipments()
        
        # Verify - should handle pagination for each status
        assert len(result) >= 2


class TestCourierAPIFallback:
    """
    Test courier API fallback functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.requests.get')
    @patch('stale_shipment_detector.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_success(self, mock_get):
        """Test successful Delhivery API query"""
        # Setup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ShipmentData': [{
                'Shipment': {
                    'Status': {'Status': 'In Transit'},
                    'Scans': [{
                        'ScanDetail': {
                            'ScanDateTime': '2025-12-29T12:00:00Z',
                            'ScannedLocation': 'Mumbai Hub',
                            'Instructions': 'Package in transit'
                        }
                    }]
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Execute
        result = query_delhivery_tracking('TRACK123')
        
        # Verify
        assert result is not None
        assert result['status'] == 'In Transit'
        assert result['location'] == 'Mumbai Hub'
        assert result['description'] == 'Package in transit'

    @patch('stale_shipment_detector.requests.get')
    @patch('stale_shipment_detector.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_no_shipment_data(self, mock_get):
        """Test Delhivery API response with no shipment data"""
        # Setup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ShipmentData': []}
        mock_get.return_value = mock_response
        
        # Execute
        result = query_delhivery_tracking('TRACK123')
        
        # Verify
        assert result is None
    
    @patch('stale_shipment_detector.requests.get')
    @patch('stale_shipment_detector.DELHIVERY_API_KEY', 'test-api-key')
    def test_query_delhivery_tracking_api_error(self, mock_get):
        """Test handling of Delhivery API errors"""
        # Setup
        mock_get.side_effect = Exception('API Error')
        
        # Execute
        result = query_delhivery_tracking('TRACK123')
        
        # Verify
        assert result is None
    
    @patch('stale_shipment_detector.DELHIVERY_API_KEY', '')
    def test_query_delhivery_tracking_no_api_key(self):
        """Test handling when API key is not configured"""
        # Execute
        result = query_delhivery_tracking('TRACK123')
        
        # Verify
        assert result is None
    
    @patch('stale_shipment_detector.query_delhivery_tracking')
    @patch('stale_shipment_detector.query_bluedart_tracking')
    @patch('stale_shipment_detector.query_dtdc_tracking')
    def test_query_courier_tracking_api_routes_correctly(
        self, mock_dtdc, mock_bluedart, mock_delhivery
    ):
        """Test that courier API queries are routed correctly"""
        # Setup
        mock_delhivery.return_value = {'status': 'In Transit'}
        mock_bluedart.return_value = {'status': 'IN TRANSIT'}
        mock_dtdc.return_value = {'status': 'IN-TRANSIT'}
        
        # Execute
        result1 = query_courier_tracking_api('Delhivery', 'TRACK123')
        result2 = query_courier_tracking_api('BlueDart', 'TRACK456')
        result3 = query_courier_tracking_api('DTDC', 'TRACK789')
        
        # Verify
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        mock_delhivery.assert_called_once_with('TRACK123')
        mock_bluedart.assert_called_once_with('TRACK456')
        mock_dtdc.assert_called_once_with('TRACK789')
    
    def test_query_courier_tracking_api_unknown_courier(self):
        """Test handling of unknown courier"""
        # Execute
        result = query_courier_tracking_api('UnknownCourier', 'TRACK123')
        
        # Verify
        assert result is None
    
    @patch('stale_shipment_detector.dynamodb')
    def test_update_shipment_from_courier_updates_status(self, mock_dynamodb):
        """Test that shipment is updated with courier data"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        courier_response = {
            'status': 'In Transit',
            'location': 'Mumbai Hub',
            'timestamp': '2025-12-29T12:00:00Z',
            'description': 'Package in transit'
        }
        
        # Execute
        update_shipment_from_courier('ship_123', courier_response)
        
        # Verify
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args[1]['Key'] == {'shipment_id': 'ship_123'}
        assert 'internal_status' in call_args[1]['UpdateExpression']
        assert 'timeline' in call_args[1]['UpdateExpression']


class TestAdminTaskCreation:
    """
    Test admin task creation functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.dynamodb')
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_create_stale_shipment_admin_task_creates_task(self, mock_sns, mock_dynamodb):
        """Test that admin task is created for stale shipment"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'updated_at': (datetime.utcnow() - timedelta(days=10)).isoformat()
        }
        
        # Execute
        create_stale_shipment_admin_task(shipment)
        
        # Verify
        mock_table.put_item.assert_called_once()
        task_item = mock_table.put_item.call_args[1]['Item']
        assert task_item['task_type'] == 'STALE_SHIPMENT'
        assert task_item['priority'] == 'HIGH'
        assert task_item['shipment_id'] == 'ship_123'
        assert task_item['order_id'] == 'ord_456'
        assert task_item['tracking_number'] == 'TRACK789'
        assert 'recommended_actions' in task_item
        assert len(task_item['recommended_actions']) > 0

    @patch('stale_shipment_detector.dynamodb')
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_create_stale_shipment_admin_task_handles_db_error(self, mock_sns, mock_dynamodb):
        """Test that admin task creation handles database errors gracefully"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.side_effect = Exception('DynamoDB Error')
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'updated_at': (datetime.utcnow() - timedelta(days=10)).isoformat()
        }
        
        # Execute - should not raise exception
        try:
            create_stale_shipment_admin_task(shipment)
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
        
        # Verify - SNS notification should still be sent
        mock_sns.publish.assert_called_once()
    
    @patch('stale_shipment_detector.dynamodb')
    def test_create_stale_shipment_admin_task_includes_recommended_actions(self, mock_dynamodb):
        """Test that admin task includes recommended actions"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'updated_at': (datetime.utcnow() - timedelta(days=10)).isoformat()
        }
        
        # Execute
        create_stale_shipment_admin_task(shipment)
        
        # Verify
        task_item = mock_table.put_item.call_args[1]['Item']
        recommended_actions = task_item['recommended_actions']
        
        # Check for key recommended actions
        assert any('courier' in action.lower() for action in recommended_actions)
        assert any('customer' in action.lower() for action in recommended_actions)
        assert any('replacement' in action.lower() for action in recommended_actions)


class TestConsumerNotification:
    """
    Test consumer notification functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_notify_consumer_about_lost_shipment_sends_notification(self, mock_sns):
        """Test that consumer notification is sent for lost shipment"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery'
        }
        
        # Execute
        notify_consumer_about_lost_shipment(shipment)
        
        # Verify
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        assert call_args[1]['TopicArn'] == 'arn:aws:sns:test'
        assert 'TRACK789' in call_args[1]['Message']
        assert 'Delhivery' in call_args[1]['Message']
    
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_notify_consumer_about_lost_shipment_includes_resolution_steps(self, mock_sns):
        """Test that notification includes resolution steps"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery'
        }
        
        # Execute
        notify_consumer_about_lost_shipment(shipment)
        
        # Verify
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args[1]['Message'])
        assert 'resolution_steps' in message
        assert len(message['resolution_steps']) > 0
        assert 'support_contact' in message
    
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_notify_consumer_about_lost_shipment_sets_high_priority(self, mock_sns):
        """Test that notification is marked as high priority"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery'
        }
        
        # Execute
        notify_consumer_about_lost_shipment(shipment)
        
        # Verify
        call_args = mock_sns.publish.call_args
        message_attrs = call_args[1]['MessageAttributes']
        assert message_attrs['priority']['StringValue'] == 'HIGH'
        assert message_attrs['event_type']['StringValue'] == 'SHIPMENT_LOST'
    
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', '')
    def test_notify_consumer_about_lost_shipment_handles_no_sns_topic(self, mock_sns):
        """Test that notification handles missing SNS topic gracefully"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery'
        }
        
        # Execute - should not raise exception
        try:
            notify_consumer_about_lost_shipment(shipment)
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
        
        # Verify - SNS should not be called
        mock_sns.publish.assert_not_called()
    
    @patch('stale_shipment_detector.sns')
    @patch('stale_shipment_detector.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    def test_notify_consumer_about_lost_shipment_handles_sns_error(self, mock_sns):
        """Test that notification handles SNS errors gracefully"""
        # Setup
        mock_sns.publish.side_effect = Exception('SNS Error')
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery'
        }
        
        # Execute - should not raise exception
        try:
            notify_consumer_about_lost_shipment(shipment)
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")


class TestMarkShipmentAsLost:
    """
    Test mark shipment as lost functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.dynamodb')
    def test_mark_shipment_as_lost_updates_status(self, mock_dynamodb):
        """Test that shipment status is updated to 'lost'"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        mark_shipment_as_lost('ship_123')
        
        # Verify
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args[1]['Key'] == {'shipment_id': 'ship_123'}
        assert ':status' in call_args[1]['ExpressionAttributeValues']
        assert call_args[1]['ExpressionAttributeValues'][':status'] == 'lost'
    
    @patch('stale_shipment_detector.dynamodb')
    def test_mark_shipment_as_lost_appends_timeline_entry(self, mock_dynamodb):
        """Test that timeline entry is appended"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        mark_shipment_as_lost('ship_123')
        
        # Verify
        call_args = mock_table.update_item.call_args
        assert 'timeline' in call_args[1]['UpdateExpression']
        timeline_entry = call_args[1]['ExpressionAttributeValues'][':timeline'][0]
        assert timeline_entry['status'] == 'lost'
        assert 'timestamp' in timeline_entry
        assert 'description' in timeline_entry


class TestHandleStaleShipment:
    """
    Test handle stale shipment functionality
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.query_courier_tracking_api')
    @patch('stale_shipment_detector.update_shipment_from_courier')
    def test_handle_stale_shipment_updates_when_courier_has_data(
        self, mock_update, mock_query
    ):
        """Test that shipment is updated when courier has data"""
        # Setup
        mock_query.return_value = {
            'status': 'In Transit',
            'location': 'Mumbai Hub',
            'timestamp': '2025-12-29T12:00:00Z',
            'description': 'Package in transit'
        }
        
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'order_id': 'ord_456'
        }
        
        # Execute
        result = handle_stale_shipment(shipment)
        
        # Verify
        mock_query.assert_called_once_with(courier_name='Delhivery', tracking_number='TRACK789')
        mock_update.assert_called_once_with('ship_123', mock_query.return_value)
        assert result['marked_lost'] is False
        assert result['admin_task_created'] is False

    @patch('stale_shipment_detector.query_courier_tracking_api')
    @patch('stale_shipment_detector.mark_shipment_as_lost')
    @patch('stale_shipment_detector.create_stale_shipment_admin_task')
    @patch('stale_shipment_detector.notify_consumer_about_lost_shipment')
    def test_handle_stale_shipment_marks_lost_when_no_courier_data(
        self, mock_notify, mock_create_task, mock_mark_lost, mock_query
    ):
        """Test that shipment is marked lost when courier has no data"""
        # Setup
        mock_query.return_value = None
        
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'order_id': 'ord_456'
        }
        
        # Execute
        result = handle_stale_shipment(shipment)
        
        # Verify
        mock_query.assert_called_once_with(courier_name='Delhivery', tracking_number='TRACK789')
        mock_mark_lost.assert_called_once_with('ship_123')
        mock_create_task.assert_called_once_with(shipment)
        mock_notify.assert_called_once_with(shipment)
        assert result['marked_lost'] is True
        assert result['admin_task_created'] is True
    
    @patch('stale_shipment_detector.query_courier_tracking_api')
    @patch('stale_shipment_detector.mark_shipment_as_lost')
    @patch('stale_shipment_detector.create_stale_shipment_admin_task')
    @patch('stale_shipment_detector.notify_consumer_about_lost_shipment')
    def test_handle_stale_shipment_marks_lost_when_courier_has_empty_status(
        self, mock_notify, mock_create_task, mock_mark_lost, mock_query
    ):
        """Test that shipment is marked lost when courier returns empty status"""
        # Setup
        mock_query.return_value = {'status': ''}
        
        shipment = {
            'shipment_id': 'ship_123',
            'tracking_number': 'TRACK789',
            'courier_name': 'Delhivery',
            'order_id': 'ord_456'
        }
        
        # Execute
        result = handle_stale_shipment(shipment)
        
        # Verify
        mock_mark_lost.assert_called_once_with('ship_123')
        mock_create_task.assert_called_once_with(shipment)
        mock_notify.assert_called_once_with(shipment)
        assert result['marked_lost'] is True
        assert result['admin_task_created'] is True


class TestHandlerFunction:
    """
    Test main handler function
    Requirements: 5.3
    """
    
    @patch('stale_shipment_detector.get_stale_shipments')
    @patch('stale_shipment_detector.handle_stale_shipment')
    def test_handler_processes_stale_shipments(self, mock_handle, mock_get):
        """Test that handler processes all stale shipments"""
        # Setup
        mock_get.return_value = [
            {'shipment_id': 'ship_1', 'tracking_number': 'TRACK1', 'courier_name': 'Delhivery', 'order_id': 'ord_1'},
            {'shipment_id': 'ship_2', 'tracking_number': 'TRACK2', 'courier_name': 'BlueDart', 'order_id': 'ord_2'}
        ]
        mock_handle.return_value = {'marked_lost': True, 'admin_task_created': True}
        
        context = Mock()
        context.request_id = 'test-request-id'
        
        # Execute
        response = handler({}, context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['stale_shipments_found'] == 2
        assert body['shipments_marked_lost'] == 2
        assert body['admin_tasks_created'] == 2
        assert mock_handle.call_count == 2
    
    @patch('stale_shipment_detector.get_stale_shipments')
    @patch('stale_shipment_detector.handle_stale_shipment')
    def test_handler_handles_no_stale_shipments(self, mock_handle, mock_get):
        """Test that handler handles case with no stale shipments"""
        # Setup
        mock_get.return_value = []
        
        context = Mock()
        context.request_id = 'test-request-id'
        
        # Execute
        response = handler({}, context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['stale_shipments_found'] == 0
        assert body['shipments_marked_lost'] == 0
        assert body['admin_tasks_created'] == 0
        mock_handle.assert_not_called()
    
    @patch('stale_shipment_detector.get_stale_shipments')
    @patch('stale_shipment_detector.handle_stale_shipment')
    def test_handler_continues_on_individual_shipment_error(self, mock_handle, mock_get):
        """Test that handler continues processing even if one shipment fails"""
        # Setup
        mock_get.return_value = [
            {'shipment_id': 'ship_1', 'tracking_number': 'TRACK1', 'courier_name': 'Delhivery', 'order_id': 'ord_1'},
            {'shipment_id': 'ship_2', 'tracking_number': 'TRACK2', 'courier_name': 'BlueDart', 'order_id': 'ord_2'}
        ]
        mock_handle.side_effect = [
            Exception('Processing error'),
            {'marked_lost': True, 'admin_task_created': True}
        ]
        
        context = Mock()
        context.request_id = 'test-request-id'
        
        # Execute
        response = handler({}, context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['stale_shipments_found'] == 2
        assert body['shipments_marked_lost'] == 1
        assert len(body['errors']) == 1
    
    @patch('stale_shipment_detector.get_stale_shipments')
    def test_handler_handles_get_stale_shipments_error(self, mock_get):
        """Test that handler handles errors in get_stale_shipments"""
        # Setup
        mock_get.side_effect = Exception('Database error')
        
        context = Mock()
        context.request_id = 'test-request-id'
        
        # Execute
        response = handler({}, context)
        
        # Verify
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body


class TestStatusMapping:
    """
    Test courier status mapping
    Requirements: 5.3
    """
    
    def test_map_courier_status_delhivery(self):
        """Test mapping of Delhivery statuses"""
        assert map_courier_status('Picked Up') == 'picked_up'
        assert map_courier_status('In Transit') == 'in_transit'
        assert map_courier_status('Delivered') == 'delivered'
        assert map_courier_status('RTO') == 'returned'
    
    def test_map_courier_status_bluedart(self):
        """Test mapping of BlueDart statuses"""
        assert map_courier_status('MANIFESTED') == 'picked_up'
        assert map_courier_status('IN TRANSIT') == 'in_transit'
        assert map_courier_status('DELIVERED') == 'delivered'
    
    def test_map_courier_status_dtdc(self):
        """Test mapping of DTDC statuses"""
        assert map_courier_status('BOOKED') == 'shipment_created'
        assert map_courier_status('PICKED') == 'picked_up'
        assert map_courier_status('DELIVERED') == 'delivered'
    
    def test_map_courier_status_case_insensitive(self):
        """Test that status mapping is case-insensitive"""
        assert map_courier_status('delivered') == 'delivered'
        assert map_courier_status('DELIVERED') == 'delivered'
        assert map_courier_status('Delivered') == 'delivered'
    
    def test_map_courier_status_unknown_defaults_to_in_transit(self):
        """Test that unknown status defaults to in_transit"""
        assert map_courier_status('UNKNOWN_STATUS') == 'in_transit'
        assert map_courier_status('') == 'in_transit'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
