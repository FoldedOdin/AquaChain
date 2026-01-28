"""
Minimal tests for Status Simulator Service
"""

import pytest
from status_simulator_service import StatusSimulatorService, OrderStatus, SimulationStatus


def test_status_simulator_service_creation():
    """Test that StatusSimulatorService can be created"""
    service = StatusSimulatorService()
    
    assert service is not None
    assert hasattr(service, 'status_progression')
    assert hasattr(service, 'simulation_interval')
    assert service.simulation_interval == 15


def test_order_status_enum():
    """Test OrderStatus enum values"""
    assert OrderStatus.ORDER_PLACED.value == 'ORDER_PLACED'
    assert OrderStatus.SHIPPED.value == 'SHIPPED'
    assert OrderStatus.OUT_FOR_DELIVERY.value == 'OUT_FOR_DELIVERY'
    assert OrderStatus.DELIVERED.value == 'DELIVERED'


def test_simulation_status_enum():
    """Test SimulationStatus enum values"""
    assert SimulationStatus.ACTIVE.value == 'ACTIVE'
    assert SimulationStatus.STOPPED.value == 'STOPPED'
    assert SimulationStatus.COMPLETED.value == 'COMPLETED'
    assert SimulationStatus.ERROR.value == 'ERROR'


def test_get_next_status():
    """Test status progression logic"""
    service = StatusSimulatorService()
    
    # Test normal progression
    assert service._get_next_status(OrderStatus.ORDER_PLACED) == OrderStatus.SHIPPED
    assert service._get_next_status(OrderStatus.SHIPPED) == OrderStatus.OUT_FOR_DELIVERY
    assert service._get_next_status(OrderStatus.OUT_FOR_DELIVERY) == OrderStatus.DELIVERED
    assert service._get_next_status(OrderStatus.DELIVERED) is None


def test_status_progression_sequence():
    """Test that the status progression sequence is correct"""
    service = StatusSimulatorService()
    
    expected_sequence = [
        OrderStatus.ORDER_PLACED,
        OrderStatus.SHIPPED,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.DELIVERED
    ]
    
    assert service.status_progression == expected_sequence


if __name__ == '__main__':
    pytest.main([__file__, '-v'])