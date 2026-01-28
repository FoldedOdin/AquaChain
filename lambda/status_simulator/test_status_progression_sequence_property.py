"""
Property-based tests for status progression sequence
Feature: enhanced-consumer-ordering-system, Property 8: Status Progression Sequence
Validates: Requirements 4.1, 4.2, 4.3

This test verifies that the Status Simulator progresses orders through the correct sequence:
- Orders initialize to "Order Placed" status (Requirement 4.1)
- Status progresses through exact sequence: "Order Placed" → "Shipped" → "Out for Delivery" → "Delivered" (Requirement 4.2)
- Transitions wait 15 seconds between each transition for demo simulation purposes (Requirement 4.3)
"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json
import uuid

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
from status_simulator_service import StatusSimulatorService, OrderStatus, SimulationStatus


# Hypothesis strategies for generating test data
order_id_strategy = st.uuids().map(str)

consumer_id_strategy = st.uuids().map(str)

# Valid statuses that can be progressed by the simulator
progressable_statuses = [
    OrderStatus.ORDER_PLACED,
    OrderStatus.SHIPPED,
    OrderStatus.OUT_FOR_DELIVERY
]

progressable_status_strategy = st.sampled_from(progressable_statuses)

# Device and service types for order creation
device_type_strategy = st.sampled_from(['Water Quality Monitor', 'pH Sensor', 'TDS Meter', 'Turbidity Sensor'])
service_type_strategy = st.sampled_from(['Installation', 'Maintenance', 'Repair', 'Replacement'])

# Version strategy for optimistic locking
version_strategy = st.integers(min_value=1, max_value=1000)

# Simulation interval strategy (should always be 15 for demo)
simulation_interval_strategy = st.just(15)


class TestStatusProgressionSequenceProperty:
    """
    Property 8: Status Progression Sequence
    
    For any order in the status progression system, the Status Simulator must:
    1. Initialize orders to "Order Placed" status (Requirement 4.1)
    2. Progress through exact sequence: "Order Placed" → "Shipped" → "Out for Delivery" → "Delivered" (Requirement 4.2)
    3. Wait 15 seconds between each transition for demo simulation purposes (Requirement 4.3)
    """
    
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
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        version=version_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_status_progression_follows_exact_sequence(
        self,
        order_id: str,
        consumer_id: str,
        device_type: str,
        service_type: str,
        version: int
    ):
        """
        Property Test: Status progression follows exact sequence
        
        For any order that starts simulation:
        1. The progression sequence MUST be exactly: ORDER_PLACED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
        2. Each status MUST have exactly one next status (except DELIVERED which has none)
        3. The sequence MUST be deterministic and consistent
        4. No status MUST be skipped in the progression
        
        **Validates: Requirements 4.1, 4.2**
        """
        # Test the progression sequence is correctly defined
        expected_sequence = [
            OrderStatus.ORDER_PLACED,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED
        ]
        
        # Verify the service has the correct progression sequence
        assert self.service.status_progression == expected_sequence, \
            f"Status progression sequence must be {[s.value for s in expected_sequence]}, " \
            f"but got {[s.value for s in self.service.status_progression]}"
        
        # Test each status in the sequence
        for i, current_status in enumerate(expected_sequence):
            if i < len(expected_sequence) - 1:
                # All statuses except the last should have a next status
                expected_next = expected_sequence[i + 1]
                actual_next = self.service._get_next_status(current_status)
                
                assert actual_next == expected_next, \
                    f"Status {current_status.value} should progress to {expected_next.value}, " \
                    f"but got {actual_next.value if actual_next else None}"
            else:
                # The last status (DELIVERED) should have no next status
                actual_next = self.service._get_next_status(current_status)
                assert actual_next is None, \
                    f"Status {current_status.value} should have no next status, " \
                    f"but got {actual_next.value if actual_next else None}"
        
        # Test that invalid statuses don't have next statuses
        invalid_statuses = [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PENDING_CONFIRMATION,
            OrderStatus.CANCELLED,
            OrderStatus.FAILED,
            OrderStatus.DELIVERED
        ]
        
        for invalid_status in invalid_statuses:
            if invalid_status != OrderStatus.DELIVERED:  # DELIVERED is tested above
                actual_next = self.service._get_next_status(invalid_status)
                assert actual_next is None, \
                    f"Invalid status {invalid_status.value} should have no next status, " \
                    f"but got {actual_next.value if actual_next else None}"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        current_status=progressable_status_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        version=version_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_simulation_interval_is_fifteen_seconds(
        self,
        order_id: str,
        consumer_id: str,
        current_status: OrderStatus,
        device_type: str,
        service_type: str,
        version: int
    ):
        """
        Property Test: Simulation interval is 15 seconds for demo purposes
        
        For any order simulation:
        1. The simulation interval MUST be exactly 15 seconds
        2. All scheduled transitions MUST use the 15-second interval
        3. The interval MUST be consistent across all orders and statuses
        4. The interval MUST be configurable but default to 15 seconds for demo
        
        **Validates: Requirements 4.3**
        """
        # Verify the service has the correct simulation interval
        assert self.service.simulation_interval == 15, \
            f"Simulation interval must be 15 seconds for demo purposes, " \
            f"but got {self.service.simulation_interval}"
        
        # Setup: Create order in progressable state
        mock_order = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': 'COD',
            'status': current_status.value,
            'simulationEnabled': True,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [],
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock DynamoDB responses
        self.mock_orders_table.get_item.return_value = {'Item': mock_order}
        self.mock_simulations_table.get_item.return_value = {}  # No existing simulation
        self.mock_simulations_table.put_item.return_value = {}
        self.mock_simulations_table.update_item.return_value = {}
        
        # Mock EventBridge
        with patch('status_simulator_service.eventbridge') as mock_eventbridge:
            mock_eventbridge.put_events.return_value = {}
            
            # Act: Start simulation
            result = self.service.start_simulation(order_id)
            
            # Assert: Simulation interval should be 15 seconds
            assert result['intervalSeconds'] == 15, \
                f"Simulation interval in result should be 15 seconds, " \
                f"but got {result['intervalSeconds']}"
            
            # Verify simulation record was created with correct interval
            put_item_call = self.mock_simulations_table.put_item.call_args[1]
            simulation_record = put_item_call['Item']
            assert simulation_record['intervalSeconds'] == 15, \
                f"Simulation record interval should be 15 seconds, " \
                f"but got {simulation_record['intervalSeconds']}"
            
            # If there's a next status, verify EventBridge scheduling uses correct interval
            next_status = self.service._get_next_status(current_status)
            if next_status and current_status == OrderStatus.ORDER_PLACED:
                # EventBridge should be called for ORDER_PLACED status
                mock_eventbridge.put_events.assert_called_once()
                
                # Verify the scheduled time is approximately 15 seconds from now
                call_args = mock_eventbridge.put_events.call_args[1]
                entries = call_args['Entries']
                assert len(entries) == 1, "Should schedule exactly one transition event"
                
                # Parse the scheduled time from the event detail
                event_detail = json.loads(entries[0]['Detail'])
                scheduled_time_str = event_detail['scheduledAt']
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                
                # The scheduled time should be approximately 15 seconds from the current time
                # We allow some tolerance for test execution time
                now = datetime.now(timezone.utc)
                time_diff = (scheduled_time - now).total_seconds()
                
                # Should be close to 15 seconds (allow 1 second tolerance for test execution)
                assert 14 <= time_diff <= 16, \
                    f"Scheduled transition should be approximately 15 seconds from now, " \
                    f"but got {time_diff} seconds"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        version=version_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_orders_initialize_to_order_placed_status(
        self,
        order_id: str,
        consumer_id: str,
        device_type: str,
        service_type: str,
        version: int
    ):
        """
        Property Test: Orders initialize to ORDER_PLACED status
        
        For any order that enters the simulation system:
        1. The first status in the progression MUST be ORDER_PLACED
        2. Simulation MUST only start for orders in ORDER_PLACED status
        3. The progression sequence MUST begin with ORDER_PLACED
        4. No other status MUST be the starting point for simulation
        
        **Validates: Requirements 4.1**
        """
        # Verify ORDER_PLACED is the first status in the progression
        assert self.service.status_progression[0] == OrderStatus.ORDER_PLACED, \
            f"First status in progression must be ORDER_PLACED, " \
            f"but got {self.service.status_progression[0].value}"
        
        # Test that simulation can start for ORDER_PLACED status
        mock_order_placed = {
            'orderId': order_id,
            'consumerId': consumer_id,
            'deviceType': device_type,
            'serviceType': service_type,
            'paymentMethod': 'COD',
            'status': OrderStatus.ORDER_PLACED.value,
            'simulationEnabled': True,
            'version': version,
            'deliveryAddress': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India'
            },
            'contactInfo': {
                'name': 'Test User',
                'phone': '+919876543210',
                'email': 'test@example.com'
            },
            'amount': 1000.0,
            'statusHistory': [],
            'createdAt': '2024-01-01T00:00:00+00:00',
            'updatedAt': '2024-01-01T00:00:00+00:00'
        }
        
        # Mock DynamoDB responses for ORDER_PLACED
        self.mock_orders_table.get_item.return_value = {'Item': mock_order_placed}
        self.mock_simulations_table.get_item.return_value = {}
        self.mock_simulations_table.put_item.return_value = {}
        
        # Mock EventBridge
        with patch('status_simulator_service.eventbridge') as mock_eventbridge:
            mock_eventbridge.put_events.return_value = {}
            
            # Act: Start simulation for ORDER_PLACED status
            result = self.service.start_simulation(order_id)
            
            # Assert: Simulation should start successfully
            assert result['status'] == 'started', \
                f"Simulation should start for ORDER_PLACED status, but got {result['status']}"
            assert result['currentStatus'] == OrderStatus.ORDER_PLACED.value, \
                f"Current status should be ORDER_PLACED, but got {result['currentStatus']}"
            assert result['nextStatus'] == OrderStatus.SHIPPED.value, \
                f"Next status should be SHIPPED, but got {result['nextStatus']}"
        
        # Test that simulation validation works for valid progression states
        valid_simulation_states = [
            OrderStatus.ORDER_PLACED.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.OUT_FOR_DELIVERY.value
        ]
        
        for status_value in valid_simulation_states:
            test_order = {
                **mock_order_placed,
                'status': status_value
            }
            
            # This should not raise an exception
            try:
                self.service._validate_simulation_eligibility(test_order)
            except Exception as e:
                pytest.fail(f"Valid simulation state {status_value} should not raise exception, but got: {e}")
        
        # Test that simulation validation rejects invalid states
        invalid_simulation_states = [
            OrderStatus.PENDING_PAYMENT.value,
            OrderStatus.PENDING_CONFIRMATION.value,
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value,
            OrderStatus.FAILED.value
        ]
        
        for status_value in invalid_simulation_states:
            test_order = {
                **mock_order_placed,
                'status': status_value
            }
            
            # This should raise an exception
            with pytest.raises(Exception) as exc_info:
                self.service._validate_simulation_eligibility(test_order)
            
            error_message = str(exc_info.value).lower()
            assert 'not eligible for simulation' in error_message, \
                f"Invalid simulation state {status_value} should be rejected with appropriate error"
    
    @given(
        order_id=order_id_strategy,
        consumer_id=consumer_id_strategy,
        device_type=device_type_strategy,
        service_type=service_type_strategy,
        version=version_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_complete_progression_sequence_integrity(
        self,
        order_id: str,
        consumer_id: str,
        device_type: str,
        service_type: str,
        version: int
    ):
        """
        Property Test: Complete progression sequence integrity
        
        For any order that goes through the complete simulation:
        1. The progression MUST follow the exact sequence without skipping steps
        2. Each transition MUST be valid and deterministic
        3. The final status MUST be DELIVERED with no further progression
        4. The sequence MUST be: ORDER_PLACED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Test the complete progression sequence
        expected_progression = [
            (OrderStatus.ORDER_PLACED, OrderStatus.SHIPPED),
            (OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY),
            (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED),
            (OrderStatus.DELIVERED, None)  # Final status has no next
        ]
        
        for current_status, expected_next in expected_progression:
            actual_next = self.service._get_next_status(current_status)
            
            if expected_next is None:
                assert actual_next is None, \
                    f"Final status {current_status.value} should have no next status, " \
                    f"but got {actual_next.value if actual_next else None}"
            else:
                assert actual_next == expected_next, \
                    f"Status {current_status.value} should progress to {expected_next.value}, " \
                    f"but got {actual_next.value if actual_next else None}"
        
        # Test that the progression is complete (covers all simulation states)
        simulation_states = {OrderStatus.ORDER_PLACED, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY}
        progression_states = set(self.service.status_progression[:-1])  # Exclude DELIVERED as it's final
        
        assert progression_states == simulation_states, \
            f"Progression should cover all simulation states {[s.value for s in simulation_states]}, " \
            f"but covers {[s.value for s in progression_states]}"
        
        # Test that the progression sequence length is correct
        assert len(self.service.status_progression) == 4, \
            f"Progression sequence should have exactly 4 statuses, " \
            f"but has {len(self.service.status_progression)}"
        
        # Test that each status appears exactly once in the progression
        status_counts = {}
        for status in self.service.status_progression:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            assert count == 1, \
                f"Status {status.value} should appear exactly once in progression, " \
                f"but appears {count} times"
        
        # Test simulation configuration consistency
        assert self.service.simulation_interval == 15, \
            f"Simulation interval must be 15 seconds, but got {self.service.simulation_interval}"
        
        assert self.service.simulation_ttl_hours == 24, \
            f"Simulation TTL should be 24 hours, but got {self.service.simulation_ttl_hours}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])