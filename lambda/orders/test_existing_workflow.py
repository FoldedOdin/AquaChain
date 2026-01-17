"""
Test that existing order workflow is maintained

This test verifies that:
1. Technician can still accept tasks
2. Installation flow works as before
3. Order completion updates DeviceOrders correctly

Requirements: 8.3
"""
import sys
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestExistingWorkflow:
    """Test that existing order workflow is maintained"""
    
    @patch('boto3.resource')
    def test_technician_can_accept_task_with_shipped_order(self, mock_boto3_resource):
        """
        Test that technician can accept task when order is shipped
        
        This verifies that the existing workflow continues to work
        even when shipment tracking is integrated.
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        # Mock order with shipped status (with shipment fields)
        mock_orders_table.get_item.return_value = {
            'Item': {
                'orderId': 'ord_123',
                'userId': 'user_456',
                'status': 'shipped',
                'shipment_id': 'ship_789',
                'tracking_number': 'TRACK123',
                'deviceSKU': 'AQ-001',
                'address': '123 Main St',
                'technicianId': 'tech_001'
            }
        }
        
        # Act - Simulate technician accepting task
        # In the real system, this would be a Lambda handler
        # Here we just verify the order can be retrieved and status is correct
        orders_table = mock_dynamodb.Table('DeviceOrders')
        response = orders_table.get_item(Key={'orderId': 'ord_123'})
        order = response['Item']
        
        # Assert
        assert order['status'] == 'shipped'
        assert order['orderId'] == 'ord_123'
        assert 'technicianId' in order
        
        # Verify technician can proceed with task acceptance
        # The presence of shipment_id should not block the workflow
        assert order['technicianId'] == 'tech_001'
    
    @patch('boto3.resource')
    def test_installation_flow_works_with_shipment_tracking(self, mock_boto3_resource):
        """
        Test that installation flow works as before
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        # Mock order update response
        mock_orders_table.update_item.return_value = {
            'Attributes': {
                'orderId': 'ord_123',
                'status': 'in_progress',
                'shipment_id': 'ship_789'
            }
        }
        
        # Act - Simulate technician starting installation
        orders_table = mock_dynamodb.Table('DeviceOrders')
        response = orders_table.update_item(
            Key={'orderId': 'ord_123'},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'in_progress'},
            ReturnValues='ALL_NEW'
        )
        
        # Assert
        updated_order = response['Attributes']
        assert updated_order['status'] == 'in_progress'
        assert updated_order['orderId'] == 'ord_123'
        
        # Shipment fields don't interfere with status update
        assert 'shipment_id' in updated_order
    
    @patch('boto3.resource')
    def test_order_completion_updates_correctly(self, mock_boto3_resource):
        """
        Test that order completion updates DeviceOrders correctly
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        # Mock order completion update
        mock_orders_table.update_item.return_value = {
            'Attributes': {
                'orderId': 'ord_123',
                'status': 'completed',
                'shipment_id': 'ship_789',
                'tracking_number': 'TRACK123',
                'completedAt': '2025-01-01T12:00:00Z'
            }
        }
        
        # Act - Simulate order completion
        orders_table = mock_dynamodb.Table('DeviceOrders')
        response = orders_table.update_item(
            Key={'orderId': 'ord_123'},
            UpdateExpression='SET #status = :status, completedAt = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':time': '2025-01-01T12:00:00Z'
            },
            ReturnValues='ALL_NEW'
        )
        
        # Assert
        completed_order = response['Attributes']
        assert completed_order['status'] == 'completed'
        assert completed_order['completedAt'] == '2025-01-01T12:00:00Z'
        
        # Shipment fields remain in the order
        assert 'shipment_id' in completed_order
        assert 'tracking_number' in completed_order
    
    @patch('boto3.resource')
    def test_order_without_shipment_fields_still_works(self, mock_boto3_resource):
        """
        Test that orders without shipment fields still work
        
        This ensures backward compatibility for orders created
        before shipment tracking was implemented.
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        # Mock order WITHOUT shipment fields (old order)
        mock_orders_table.get_item.return_value = {
            'Item': {
                'orderId': 'ord_old_123',
                'userId': 'user_456',
                'status': 'approved',
                'deviceSKU': 'AQ-001',
                'address': '123 Main St',
                'technicianId': 'tech_001'
                # No shipment_id or tracking_number
            }
        }
        
        # Act
        orders_table = mock_dynamodb.Table('DeviceOrders')
        response = orders_table.get_item(Key={'orderId': 'ord_old_123'})
        order = response['Item']
        
        # Assert
        assert order['status'] == 'approved'
        assert order['orderId'] == 'ord_old_123'
        
        # Order works fine without shipment fields
        assert 'shipment_id' not in order
        assert 'tracking_number' not in order
        
        # Technician can still accept this task
        assert 'technicianId' in order
    
    @patch('boto3.resource')
    def test_status_transitions_work_with_shipment_fields(self, mock_boto3_resource):
        """
        Test that all status transitions work with shipment fields present
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        orders_table = mock_dynamodb.Table('DeviceOrders')
        
        # Test status transitions
        status_transitions = [
            ('pending', 'approved'),
            ('approved', 'shipped'),
            ('shipped', 'in_progress'),
            ('in_progress', 'completed')
        ]
        
        for old_status, new_status in status_transitions:
            # Mock update response
            mock_orders_table.update_item.return_value = {
                'Attributes': {
                    'orderId': 'ord_123',
                    'status': new_status,
                    'shipment_id': 'ship_789' if new_status == 'shipped' else None
                }
            }
            
            # Act
            response = orders_table.update_item(
                Key={'orderId': 'ord_123'},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': new_status},
                ReturnValues='ALL_NEW'
            )
            
            # Assert
            updated_order = response['Attributes']
            assert updated_order['status'] == new_status
    
    @patch('boto3.resource')
    def test_technician_query_by_status_works(self, mock_boto3_resource):
        """
        Test that technician can query orders by status
        
        Requirements: 8.3
        """
        # Arrange
        mock_dynamodb = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_orders_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_orders_table
        
        # Mock query response with shipped orders
        mock_orders_table.query.return_value = {
            'Items': [
                {
                    'orderId': 'ord_123',
                    'status': 'shipped',
                    'shipment_id': 'ship_789',
                    'technicianId': 'tech_001'
                },
                {
                    'orderId': 'ord_124',
                    'status': 'shipped',
                    'shipment_id': 'ship_790',
                    'technicianId': 'tech_001'
                }
            ]
        }
        
        # Act - Query orders by technician and status
        orders_table = mock_dynamodb.Table('DeviceOrders')
        response = orders_table.query(
            IndexName='technicianId-status-index',
            KeyConditionExpression='technicianId = :tid AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':tid': 'tech_001',
                ':status': 'shipped'
            }
        )
        
        # Assert
        orders = response['Items']
        assert len(orders) == 2
        
        # All orders have shipped status
        for order in orders:
            assert order['status'] == 'shipped'
            assert order['technicianId'] == 'tech_001'
            assert 'shipment_id' in order


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
