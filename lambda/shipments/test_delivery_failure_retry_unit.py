"""
Unit tests for delivery failure retry logic
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5

Tests cover:
- Retry counter increment
- Redelivery scheduling when retries available
- Admin escalation when max retries exceeded
- Admin task creation
- Notification sending for each scenario
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call

# Import functions from webhook_handler
from webhook_handler import (
    handle_delivery_failure,
    schedule_redelivery,
    create_admin_task
)


class TestRetryCounterIncrement:
    """
    Test retry counter increment functionality
    Requirements: 6.1
    """
    
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.schedule_redelivery')
    def test_retry_counter_increments_successfully(self, mock_schedule, mock_dynamodb):
        """Test that retry counter increments and returns updated count"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {
                'retry_count': 0,
                'max_retries': 3
            }
        }
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            'Attributes': {
                'retry_config': {
                    'retry_count': 1,
                    'last_retry_at': '2025-12-29T12:00:00'
                }
            }
        }
        
        # Execute
        result = handle_delivery_failure(shipment)
        
        # Verify
        assert result == 1
        mock_table.update_item.assert_called_once()
        
        # Verify update expression
        call_args = mock_table.update_item.call_args
        assert 'retry_config.retry_count' in call_args[1]['UpdateExpression']
        assert 'retry_config.last_retry_at' in call_args[1]['UpdateExpression']
        assert call_args[1]['ExpressionAttributeValues'][':inc'] == 1
        
        # Verify schedule_redelivery was called
        mock_schedule.assert_called_once_with('ship_123', 'ord_456', 1, 3)
    
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.schedule_redelivery')
    def test_retry_counter_handles_existing_count(self, mock_schedule, mock_dynamodb):
        """Test retry counter increments from existing count"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {
                'retry_count': 2,
                'max_retries': 3
            }
        }
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            'Attributes': {
                'retry_config': {
                    'retry_count': 3,
                    'last_retry_at': '2025-12-29T12:00:00'
                }
            }
        }
        
        # Execute
        result = handle_delivery_failure(shipment)
        
        # Verify
        assert result == 3
        mock_schedule.assert_called_once_with('ship_123', 'ord_456', 3, 3)
    
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.schedule_redelivery')
    def test_retry_counter_handles_update_failure(self, mock_schedule, mock_dynamodb):
        """Test retry counter returns current count on update failure"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {
                'retry_count': 1,
                'max_retries': 3
            }
        }
        
        # Mock DynamoDB to raise exception
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.side_effect = Exception("DynamoDB error")
        
        # Execute
        result = handle_delivery_failure(shipment)
        
        # Verify - should return current count on failure
        assert result == 1
        mock_schedule.assert_not_called()


class TestRedeliveryScheduling:
    """
    Test redelivery scheduling logic
    Requirements: 6.2, 6.3, 6.4
    """
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.sns')
    @patch('webhook_handler.create_admin_task')
    def test_schedules_redelivery_when_retries_available(self, mock_create_task, mock_sns):
        """Test redelivery notification sent when retries < max"""
        # Execute
        schedule_redelivery('ship_123', 'ord_456', retry_count=1, max_retries=3)
        
        # Verify
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        
        # Verify notification content
        message = json.loads(call_args[1]['Message'])
        assert message['eventType'] == 'DELIVERY_FAILED_RETRY'
        assert message['shipment_id'] == 'ship_123'
        assert message['order_id'] == 'ord_456'
        assert message['retry_count'] == 1
        assert message['max_retries'] == 3
        assert 'consumer' in message['recipients']
        assert 'new_delivery_date' in message
        
        # Verify admin task NOT created
        mock_create_task.assert_not_called()
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.sns')
    @patch('webhook_handler.create_admin_task')
    def test_escalates_to_admin_when_max_retries_exceeded(self, mock_create_task, mock_sns):
        """Test admin escalation when retry_count >= max_retries"""
        # Execute
        schedule_redelivery('ship_123', 'ord_456', retry_count=3, max_retries=3)
        
        # Verify
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        
        # Verify escalation notification
        message = json.loads(call_args[1]['Message'])
        assert message['eventType'] == 'DELIVERY_FAILED_MAX_RETRIES'
        assert message['priority'] == 'HIGH'
        assert message['shipment_id'] == 'ship_123'
        assert message['order_id'] == 'ord_456'
        assert 'admin' in message['recipients']
        assert 'recommended_actions' in message
        
        # Verify admin task created
        mock_create_task.assert_called_once_with('ship_123', 'ord_456', 3)
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.sns')
    @patch('webhook_handler.create_admin_task')
    def test_handles_notification_failure_gracefully(self, mock_create_task, mock_sns):
        """Test that notification failures don't crash the function"""
        # Setup
        mock_sns.publish.side_effect = Exception("SNS error")
        
        # Execute - should not raise exception
        schedule_redelivery('ship_123', 'ord_456', retry_count=1, max_retries=3)
        
        # Verify - function completed despite error
        mock_sns.publish.assert_called_once()


class TestAdminTaskCreation:
    """
    Test admin task creation for max retries
    Requirements: 6.5
    """
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_creates_admin_task_with_correct_fields(self, mock_sns, mock_dynamodb):
        """Test admin task created with all required fields"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        create_admin_task('ship_123', 'ord_456', retry_count=3)
        
        # Verify
        mock_table.put_item.assert_called_once()
        task_item = mock_table.put_item.call_args[1]['Item']
        
        # Verify task structure
        assert task_item['task_type'] == 'DELIVERY_FAILED'
        assert task_item['priority'] == 'HIGH'
        assert task_item['status'] == 'PENDING'
        assert task_item['shipment_id'] == 'ship_123'
        assert task_item['order_id'] == 'ord_456'
        assert task_item['retry_count'] == 3
        assert 'task_id' in task_item
        assert 'title' in task_item
        assert 'description' in task_item
        assert 'recommended_actions' in task_item
        assert len(task_item['recommended_actions']) > 0
        assert 'created_at' in task_item
        assert 'updated_at' in task_item
    
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_admin_task_includes_recommended_actions(self, mock_sns, mock_dynamodb):
        """Test admin task includes recommended actions"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Execute
        create_admin_task('ship_123', 'ord_456', retry_count=3)
        
        # Verify
        task_item = mock_table.put_item.call_args[1]['Item']
        actions = task_item['recommended_actions']
        
        # Verify recommended actions
        assert 'Contact customer to verify delivery address' in actions
        assert 'Consider alternative courier service' in actions
        assert 'Initiate return to sender if undeliverable' in actions
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_handles_dynamodb_failure_gracefully(self, mock_sns, mock_dynamodb):
        """Test that DynamoDB failures don't crash the function"""
        # Setup
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.side_effect = Exception("Table does not exist")
        
        # Execute - should not raise exception
        create_admin_task('ship_123', 'ord_456', retry_count=3)
        
        # Verify - SNS notification still sent
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args[1]['Message'])
        assert message['eventType'] == 'ADMIN_TASK_CREATED'
        assert 'task' in message


class TestEndToEndDeliveryFailure:
    """
    Test end-to-end delivery failure flow
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_first_failure_schedules_redelivery(self, mock_sns, mock_dynamodb):
        """Test first delivery failure schedules redelivery"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {
                'retry_count': 0,
                'max_retries': 3
            }
        }
        
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            'Attributes': {
                'retry_config': {
                    'retry_count': 1,
                    'last_retry_at': '2025-12-29T12:00:00'
                }
            }
        }
        
        # Execute
        result = handle_delivery_failure(shipment)
        
        # Verify
        assert result == 1
        
        # Verify redelivery notification sent
        assert mock_sns.publish.call_count == 1
        message = json.loads(mock_sns.publish.call_args[1]['Message'])
        assert message['eventType'] == 'DELIVERY_FAILED_RETRY'
        assert 'consumer' in message['recipients']
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_max_retries_escalates_to_admin(self, mock_sns, mock_dynamodb):
        """Test max retries exceeded escalates to admin and creates task"""
        # Setup
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {
                'retry_count': 2,
                'max_retries': 3
            }
        }
        
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            'Attributes': {
                'retry_config': {
                    'retry_count': 3,
                    'last_retry_at': '2025-12-29T12:00:00'
                }
            }
        }
        
        # Execute
        result = handle_delivery_failure(shipment)
        
        # Verify
        assert result == 3
        
        # Verify escalation notification sent (at least one call)
        assert mock_sns.publish.call_count >= 1
        
        # Find the escalation message
        escalation_found = False
        for call_obj in mock_sns.publish.call_args_list:
            message = json.loads(call_obj[1]['Message'])
            if message['eventType'] == 'DELIVERY_FAILED_MAX_RETRIES':
                escalation_found = True
                assert message['priority'] == 'HIGH'
                assert 'admin' in message['recipients']
                break
        
        assert escalation_found, "Escalation notification not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
