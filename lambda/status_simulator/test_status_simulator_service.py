"""
Unit tests for Status Simulator Service
Tests simulation control, status progression, and error handling
"""

import sys
import os
import pytest
import json
import unittest.mock
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
import status_simulator_service
from status_simulator_service import StatusSimulatorService, OrderStatus, SimulationStatus


class TestStatusSimulatorService:
    """Unit tests for StatusSimulatorService"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        os.environ['ENHANCED_ORDERS_TABLE'] = 'test-orders'
        os.environ['ENHANCED_SIMULATIONS_TABLE'] = 'test-simulations'
        os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
        os.environ['EVENTBRIDGE_BUS'] = 'test-bus'
        
        # Initialize service
        self.service = StatusSimulatorService()
        
        # Mock AWS clients
        self.mock_orders_table = Mock()
        self.mock_simulations_table = Mock()
        self.service.orders_table = self.mock_orders_table
        self.service.simulations_table = self.mock_simulations_table
    
    def test_start_simulation_success(self):
        """Test successful simulation start"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'simulationEnabled': True,
            'version': 1
        }
        
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        self.mock_simulations_table.get_item.return_value = {}  # No existing simulation
        self.mock_simulations_table.put_item.return_value = {}
        
        # Act
        result = self.service.start_simulation(order_id)
        
        # Assert
        assert result['orderId'] == order_id
        assert result['status'] == 'started'
        assert result['currentStatus'] == OrderStatus.ORDER_PLACED.value
        assert result['nextStatus'] == OrderStatus.SHIPPED.value
        assert result['intervalSeconds'] == 15
        
        # Verify DynamoDB calls
        self.mock_orders_table.get_item.assert_called_once()
        self.mock_simulations_table.put_item.assert_called_once()
    
    def test_start_simulation_order_not_found(self):
        """Test simulation start with non-existent order"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        self.mock_orders_table.get_item.return_value = {}  # No order found
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.start_simulation(order_id)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_start_simulation_not_enabled(self):
        """Test simulation start with simulation not enabled"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'simulationEnabled': False,  # Not enabled for simulation
            'version': 1
        }
        
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.start_simulation(order_id)
        
        assert "not enabled for simulation" in str(exc_info.value).lower()
    
    def test_start_simulation_invalid_status(self):
        """Test simulation start with invalid order status"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.DELIVERED.value,  # Already delivered
            'simulationEnabled': True,
            'version': 1
        }
        
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.start_simulation(order_id)
        
        assert "not eligible for simulation" in str(exc_info.value).lower()
    
    def test_stop_simulation_success(self):
        """Test successful simulation stop"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        mock_simulation = {
            'orderId': order_id,
            'isActive': True,
            'currentStatus': OrderStatus.SHIPPED.value
        }
        
        self.mock_simulations_table.get_item.return_value = {'Item': mock_simulation}
        self.mock_simulations_table.update_item.return_value = {}
        
        # Act
        result = self.service.stop_simulation(order_id)
        
        # Assert
        assert result['orderId'] == order_id
        assert result['status'] == 'stopped'
        assert 'stoppedAt' in result
        
        # Verify DynamoDB calls
        self.mock_simulations_table.get_item.assert_called_once()
        self.mock_simulations_table.update_item.assert_called_once()
    
    def test_stop_simulation_not_found(self):
        """Test simulation stop with no existing simulation"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        self.mock_simulations_table.get_item.return_value = {}  # No simulation found
        
        # Act
        result = self.service.stop_simulation(order_id)
        
        # Assert
        assert result['orderId'] == order_id
        assert result['status'] == 'not_found'
        assert 'No active simulation found' in result['message']
    
    def test_get_simulation_status_active(self):
        """Test getting status of active simulation"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        mock_simulation = {
            'orderId': order_id,
            'currentStatus': OrderStatus.SHIPPED.value,
            'nextStatus': OrderStatus.OUT_FOR_DELIVERY.value,
            'isActive': True,
            'intervalSeconds': 15,
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:15Z'
        }
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.SHIPPED.value
        }
        
        self.mock_simulations_table.get_item.return_value = {'Item': mock_simulation}
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        
        # Act
        result = self.service.get_simulation_status(order_id)
        
        # Assert
        assert result['orderId'] == order_id
        assert result['currentStatus'] == OrderStatus.SHIPPED.value
        assert result['nextStatus'] == OrderStatus.OUT_FOR_DELIVERY.value
        assert result['isActive'] is True
        assert result['intervalSeconds'] == 15
    
    def test_get_simulation_status_not_found(self):
        """Test getting status of non-existent simulation"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        self.mock_simulations_table.get_item.return_value = {}  # No simulation found
        
        # Act
        result = self.service.get_simulation_status(order_id)
        
        # Assert
        assert result['orderId'] == order_id
        assert result['isActive'] is False
        assert result['status'] == 'not_found'
    
    def test_get_next_status_progression(self):
        """Test status progression logic"""
        # Test normal progression
        assert self.service._get_next_status(OrderStatus.ORDER_PLACED) == OrderStatus.SHIPPED
        assert self.service._get_next_status(OrderStatus.SHIPPED) == OrderStatus.OUT_FOR_DELIVERY
        assert self.service._get_next_status(OrderStatus.OUT_FOR_DELIVERY) == OrderStatus.DELIVERED
        assert self.service._get_next_status(OrderStatus.DELIVERED) is None
        
        # Test invalid status
        assert self.service._get_next_status(OrderStatus.CANCELLED) is None
    
    @patch('status_simulator_service.eventbridge')
    def test_schedule_next_transition(self, mock_eventbridge):
        """Test scheduling next transition"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        next_status = OrderStatus.SHIPPED
        
        mock_eventbridge.put_events.return_value = {}
        self.mock_simulations_table.update_item.return_value = {}
        
        # Act
        self.service._schedule_next_transition(order_id, next_status)
        
        # Assert
        mock_eventbridge.put_events.assert_called_once()
        self.mock_simulations_table.update_item.assert_called_once()
        
        # Verify event structure
        call_args = mock_eventbridge.put_events.call_args[1]
        entries = call_args['Entries']
        assert len(entries) == 1
        assert entries[0]['Source'] == 'aquachain.ordering'
        assert entries[0]['DetailType'] == 'Order Status Transition'
        
        detail = json.loads(entries[0]['Detail'])
        assert detail['orderId'] == order_id
        assert detail['targetStatus'] == next_status.value
    
    @patch('status_simulator_service.sns')
    def test_publish_status_change_event(self, mock_sns):
        """Test publishing status change event"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        from_status = OrderStatus.ORDER_PLACED.value
        to_status = OrderStatus.SHIPPED.value
        
        mock_sns.publish.return_value = {}
        
        # Act
        self.service._publish_status_change_event(order_id, from_status, to_status)
        
        # Assert
        mock_sns.publish.assert_called_once()
        
        # Verify message structure
        call_args = mock_sns.publish.call_args[1]
        message = json.loads(call_args['Message'])
        assert message['eventType'] == 'ORDER_STATUS_CHANGED'
        assert message['orderId'] == order_id
        assert message['fromStatus'] == from_status
        assert message['toStatus'] == to_status
        assert message['source'] == 'status_simulator'
    
    def test_process_status_transition_success(self):
        """Test successful status transition processing"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        
        mock_simulation = {
            'orderId': order_id,
            'isActive': True,
            'currentStatus': OrderStatus.ORDER_PLACED.value
        }
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'version': 1
        }
        
        self.mock_simulations_table.get_item.return_value = {'Item': mock_simulation}
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        self.mock_orders_table.update_item.return_value = {}
        self.mock_simulations_table.update_item.return_value = {}
        
        # Mock EventBridge and SNS
        with patch('status_simulator_service.eventbridge') as mock_eventbridge, \
             patch('status_simulator_service.sns') as mock_sns:
            
            mock_eventbridge.put_events.return_value = {}
            mock_sns.publish.return_value = {}
            
            # Act
            result = self.service.process_status_transition(order_id)
            
            # Assert
            assert result['orderId'] == order_id
            assert result['status'] == 'transitioned'
            assert result['fromStatus'] == OrderStatus.ORDER_PLACED.value
            assert result['toStatus'] == OrderStatus.SHIPPED.value
            assert result['nextStatus'] == OrderStatus.OUT_FOR_DELIVERY.value
            
            # Verify order status was updated
            self.mock_orders_table.update_item.assert_called()
            
            # Verify next transition was scheduled
            mock_eventbridge.put_events.assert_called_once()
            
            # Verify status change event was published
            mock_sns.publish.assert_called_once()
    
    def test_process_status_transition_completion(self):
        """Test status transition when reaching final status"""
        # Arrange
        order_id = '123e4567-e89b-12d3-a456-426614174000'
        
        mock_simulation = {
            'orderId': order_id,
            'isActive': True,
            'currentStatus': OrderStatus.OUT_FOR_DELIVERY.value
        }
        mock_order = {
            'orderId': order_id,
            'status': OrderStatus.OUT_FOR_DELIVERY.value,
            'version': 1
        }
        
        self.mock_simulations_table.get_item.return_value = {'Item': mock_simulation}
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        self.mock_orders_table.update_item.return_value = {}
        self.mock_simulations_table.update_item.return_value = {}
        
        # Mock SNS
        with patch('status_simulator_service.sns') as mock_sns:
            mock_sns.publish.return_value = {}
            
            # Act
            result = self.service.process_status_transition(order_id)
            
            # Assert
            assert result['orderId'] == order_id
            assert result['status'] == 'transitioned'
            assert result['fromStatus'] == OrderStatus.OUT_FOR_DELIVERY.value
            assert result['toStatus'] == OrderStatus.DELIVERED.value
            assert result['nextStatus'] is None  # No more transitions
            
            # Verify simulation was marked as completed
            update_calls = self.mock_simulations_table.update_item.call_args_list
            assert len(update_calls) >= 1  # At least one call to update simulation


if __name__ == '__main__':
    pytest.main([__file__])