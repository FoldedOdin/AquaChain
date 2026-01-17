"""
Test graceful degradation for Shipments table unavailability

This test verifies that:
1. DynamoDB errors in create_shipment are caught
2. Order proceeds with manual tracking when Shipments table unavailable
3. Error is logged and DevOps is alerted

Requirements: 8.4
"""
import sys
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the functions
from shipments.create_shipment import (
    execute_atomic_transaction,
    alert_devops_shipments_table_unavailable,
    fallback_update_order_status,
    convert_to_dynamodb_format
)


class TestGracefulDegradation:
    """Test graceful degradation when Shipments table is unavailable"""
    
    @patch('shipments.create_shipment.dynamodb_client')
    @patch('shipments.create_shipment.fallback_update_order_status')
    @patch('shipments.create_shipment.alert_devops_shipments_table_unavailable')
    def test_execute_atomic_transaction_handles_table_not_found(
        self,
        mock_alert_devops,
        mock_fallback_update,
        mock_dynamodb_client
    ):
        """
        Test that ResourceNotFoundException triggers graceful degradation
        
        Requirements: 8.4
        """
        # Arrange
        shipment_item = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789'
        }
        
        # Mock DynamoDB client to raise ResourceNotFoundException
        mock_dynamodb_client.transact_write_items.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'ResourceNotFoundException',
                    'Message': 'Requested resource not found'
                }
            },
            'TransactWriteItems'
        )
        
        # Mock fallback to succeed
        mock_fallback_update.return_value = None
        
        # Act
        execute_atomic_transaction(
            shipment_item=shipment_item,
            order_id='ord_456',
            shipment_id='ship_123',
            tracking_number='TRACK789',
            timestamp='2025-01-01T00:00:00Z'
        )
        
        # Assert
        # DevOps alert should be called
        mock_alert_devops.assert_called_once_with('ord_456', 'ship_123', 'TRACK789')
        
        # Fallback update should be called
        mock_fallback_update.assert_called_once_with(
            'ord_456',
            'TRACK789',
            '2025-01-01T00:00:00Z'
        )
    
    @patch('shipments.create_shipment.sns')
    @patch('shipments.create_shipment.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    def test_alert_devops_sends_sns_notification(self, mock_sns):
        """
        Test that DevOps alert sends SNS notification
        
        Requirements: 8.4
        """
        # Arrange
        mock_sns.publish.return_value = {'MessageId': 'msg-123'}
        
        # Act
        alert_devops_shipments_table_unavailable(
            order_id='ord_456',
            shipment_id='ship_123',
            tracking_number='TRACK789'
        )
        
        # Assert
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        
        # Verify SNS topic ARN
        assert call_args[1]['TopicArn'] == 'arn:aws:sns:us-east-1:123456789012:test-topic'
        
        # Verify subject
        assert call_args[1]['Subject'] == 'ALERT: Shipments Table Unavailable'
        
        # Verify message content
        message = json.loads(call_args[1]['Message'])
        assert message['alert_type'] == 'SHIPMENTS_TABLE_UNAVAILABLE'
        assert message['severity'] == 'HIGH'
        assert message['order_id'] == 'ord_456'
        assert message['shipment_id'] == 'ship_123'
        assert message['tracking_number'] == 'TRACK789'
        assert 'manual tracking' in message['message'].lower()
    
    @patch('shipments.create_shipment.dynamodb')
    def test_fallback_update_order_status_updates_order(self, mock_dynamodb):
        """
        Test that fallback updates order status without shipment_id
        
        Requirements: 8.4
        """
        # Arrange
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Act
        fallback_update_order_status(
            order_id='ord_456',
            tracking_number='TRACK789',
            timestamp='2025-01-01T00:00:00Z'
        )
        
        # Assert
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        
        # Verify key
        assert call_args[1]['Key'] == {'orderId': 'ord_456'}
        
        # Verify update expression doesn't include shipment_id
        update_expr = call_args[1]['UpdateExpression']
        assert 'shipment_id' not in update_expr
        assert 'tracking_number' in update_expr
        assert '#status' in update_expr
        
        # Verify expression attribute values
        expr_values = call_args[1]['ExpressionAttributeValues']
        assert expr_values[':shipped'] == 'shipped'
        assert expr_values[':tracking'] == 'TRACK789'
        assert expr_values[':time'] == '2025-01-01T00:00:00Z'
    
    @patch('shipments.create_shipment.dynamodb')
    def test_fallback_update_order_status_raises_on_failure(self, mock_dynamodb):
        """
        Test that fallback raises exception if order update fails
        
        Requirements: 8.4
        """
        # Arrange
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock update_item to raise exception
        mock_table.update_item.side_effect = Exception('DynamoDB error')
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            fallback_update_order_status(
                order_id='ord_456',
                tracking_number='TRACK789',
                timestamp='2025-01-01T00:00:00Z'
            )
        
        assert 'DynamoDB error' in str(exc_info.value)
    
    @patch('shipments.create_shipment.dynamodb_client')
    @patch('shipments.create_shipment.fallback_update_order_status')
    @patch('shipments.create_shipment.alert_devops_shipments_table_unavailable')
    def test_execute_atomic_transaction_raises_if_fallback_fails(
        self,
        mock_alert_devops,
        mock_fallback_update,
        mock_dynamodb_client
    ):
        """
        Test that exception is raised if fallback update fails
        
        Requirements: 8.4
        """
        # Arrange
        shipment_item = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789'
        }
        
        # Mock DynamoDB client to raise ResourceNotFoundException
        mock_dynamodb_client.transact_write_items.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'ResourceNotFoundException',
                    'Message': 'Requested resource not found'
                }
            },
            'TransactWriteItems'
        )
        
        # Mock fallback to fail
        mock_fallback_update.side_effect = Exception('Fallback failed')
        
        # Act & Assert
        with pytest.raises(Exception):
            execute_atomic_transaction(
                shipment_item=shipment_item,
                order_id='ord_456',
                shipment_id='ship_123',
                tracking_number='TRACK789',
                timestamp='2025-01-01T00:00:00Z'
            )
        
        # DevOps alert should still be called
        mock_alert_devops.assert_called_once()
    
    @patch('shipments.create_shipment.sns')
    @patch('shipments.create_shipment.SNS_TOPIC_ARN', '')
    def test_alert_devops_handles_missing_sns_topic(self, mock_sns):
        """
        Test that alert handles missing SNS topic gracefully
        
        Requirements: 8.4
        """
        # Act - should not raise exception
        alert_devops_shipments_table_unavailable(
            order_id='ord_456',
            shipment_id='ship_123',
            tracking_number='TRACK789'
        )
        
        # Assert - SNS should not be called
        mock_sns.publish.assert_not_called()
    
    @patch('shipments.create_shipment.sns')
    @patch('shipments.create_shipment.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test-topic')
    def test_alert_devops_handles_sns_failure(self, mock_sns):
        """
        Test that alert handles SNS failure gracefully
        
        Requirements: 8.4
        """
        # Arrange
        mock_sns.publish.side_effect = Exception('SNS error')
        
        # Act - should not raise exception
        alert_devops_shipments_table_unavailable(
            order_id='ord_456',
            shipment_id='ship_123',
            tracking_number='TRACK789'
        )
        
        # Assert - exception was caught and logged
        mock_sns.publish.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
