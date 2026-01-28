"""
Functional tests for Status Simulator Service
"""

import pytest
import json
from unittest.mock import Mock, patch
from status_simulator_service import StatusSimulatorService, OrderStatus, SimulationStatus, lambda_handler


def test_start_simulation_success():
    """Test successful simulation start"""
    service = StatusSimulatorService()
    
    # Mock the order data
    mock_order = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'status': OrderStatus.ORDER_PLACED.value,
        'simulationEnabled': True,
        'version': 1
    }
    
    # Mock the DynamoDB responses
    service._get_order = Mock(return_value=mock_order)
    service._get_simulation = Mock(return_value=None)  # No existing simulation
    service._create_simulation_record = Mock(return_value={})
    service._schedule_next_transition = Mock()
    
    result = service.start_simulation('123e4567-e89b-12d3-a456-426614174000')
    
    assert result['orderId'] == '123e4567-e89b-12d3-a456-426614174000'
    assert result['status'] == 'started'
    assert result['currentStatus'] == OrderStatus.ORDER_PLACED.value
    assert result['nextStatus'] == OrderStatus.SHIPPED.value
    assert result['intervalSeconds'] == 15


def test_start_simulation_order_not_found():
    """Test simulation start with non-existent order"""
    service = StatusSimulatorService()
    
    # Mock order not found
    service._get_order = Mock(return_value=None)
    
    with pytest.raises(Exception) as exc_info:
        service.start_simulation('123e4567-e89b-12d3-a456-426614174000')
    
    assert "not found" in str(exc_info.value).lower()


def test_start_simulation_not_enabled():
    """Test simulation start with simulation not enabled"""
    service = StatusSimulatorService()
    
    mock_order = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'status': OrderStatus.ORDER_PLACED.value,
        'simulationEnabled': False,  # Not enabled for simulation
        'version': 1
    }
    
    service._get_order = Mock(return_value=mock_order)
    
    with pytest.raises(Exception) as exc_info:
        service.start_simulation('123e4567-e89b-12d3-a456-426614174000')
    
    assert "not enabled for simulation" in str(exc_info.value).lower()


def test_stop_simulation_success():
    """Test successful simulation stop"""
    service = StatusSimulatorService()
    
    mock_simulation = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'isActive': True,
        'currentStatus': OrderStatus.SHIPPED.value
    }
    
    service._get_simulation = Mock(return_value=mock_simulation)
    service._update_simulation_status = Mock()
    
    result = service.stop_simulation('123e4567-e89b-12d3-a456-426614174000')
    
    assert result['orderId'] == '123e4567-e89b-12d3-a456-426614174000'
    assert result['status'] == 'stopped'
    assert 'stoppedAt' in result


def test_get_simulation_status_active():
    """Test getting status of active simulation"""
    service = StatusSimulatorService()
    
    mock_simulation = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'currentStatus': OrderStatus.SHIPPED.value,
        'nextStatus': OrderStatus.OUT_FOR_DELIVERY.value,
        'isActive': True,
        'intervalSeconds': 15,
        'createdAt': '2024-01-01T00:00:00Z',
        'updatedAt': '2024-01-01T00:00:15Z'
    }
    mock_order = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'status': OrderStatus.SHIPPED.value
    }
    
    service._get_simulation = Mock(return_value=mock_simulation)
    service._get_order = Mock(return_value=mock_order)
    
    result = service.get_simulation_status('123e4567-e89b-12d3-a456-426614174000')
    
    assert result['orderId'] == '123e4567-e89b-12d3-a456-426614174000'
    assert result['currentStatus'] == OrderStatus.SHIPPED.value
    assert result['nextStatus'] == OrderStatus.OUT_FOR_DELIVERY.value
    assert result['isActive'] is True
    assert result['intervalSeconds'] == 15


def test_lambda_handler_start_simulation():
    """Test Lambda handler for start simulation"""
    event = {
        'httpMethod': 'POST',
        'path': '/start',
        'body': json.dumps({'orderId': '123e4567-e89b-12d3-a456-426614174000'})
    }
    
    with patch('status_simulator_service.StatusSimulatorService') as mock_service_class:
        mock_service = Mock()
        mock_service.start_simulation.return_value = {
            'orderId': '123e4567-e89b-12d3-a456-426614174000',
            'status': 'started'
        }
        mock_service_class.return_value = mock_service
        
        result = lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        assert 'application/json' in result['headers']['Content-Type']
        
        body = json.loads(result['body'])
        assert body['orderId'] == '123e4567-e89b-12d3-a456-426614174000'
        assert body['status'] == 'started'


def test_lambda_handler_eventbridge_event():
    """Test Lambda handler for EventBridge events"""
    event = {
        'source': 'aquachain.ordering',
        'detail-type': 'Order Status Transition',
        'detail': {
            'orderId': '123e4567-e89b-12d3-a456-426614174000'
        }
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['status'] == 'transition_scheduled'
    assert body['orderId'] == '123e4567-e89b-12d3-a456-426614174000'


def test_lambda_handler_invalid_method():
    """Test Lambda handler with invalid method"""
    event = {
        'httpMethod': 'DELETE',
        'path': '/invalid'
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 404
    body = json.loads(result['body'])
    assert body['error'] == 'Not Found'


def test_authority_restriction_validation():
    """Test that simulation authority restriction is enforced - Requirement 4.5"""
    service = StatusSimulatorService()
    
    # Test order without simulation enabled
    order_without_simulation = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'status': OrderStatus.ORDER_PLACED.value,
        'simulationEnabled': False
    }
    
    with pytest.raises(Exception) as exc_info:
        service._validate_simulation_eligibility(order_without_simulation)
    
    assert "not enabled for simulation" in str(exc_info.value).lower()
    
    # Test order with invalid status
    order_invalid_status = {
        'orderId': '123e4567-e89b-12d3-a456-426614174000',
        'status': OrderStatus.DELIVERED.value,  # Already delivered
        'simulationEnabled': True
    }
    
    with pytest.raises(Exception) as exc_info:
        service._validate_simulation_eligibility(order_invalid_status)
    
    assert "not eligible for simulation" in str(exc_info.value).lower()


def test_status_progression_requirements():
    """Test that status progression follows requirements 4.1, 4.2, 4.3"""
    service = StatusSimulatorService()
    
    # Requirement 4.1: Initialize to ORDER_PLACED
    assert OrderStatus.ORDER_PLACED in service.status_progression
    assert service.status_progression[0] == OrderStatus.ORDER_PLACED
    
    # Requirement 4.2: Progress through specific sequence
    expected_sequence = [
        OrderStatus.ORDER_PLACED,
        OrderStatus.SHIPPED,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.DELIVERED
    ]
    assert service.status_progression == expected_sequence
    
    # Requirement 4.3: 15 second intervals
    assert service.simulation_interval == 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])