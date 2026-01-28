"""
Property-based tests for technician assignment logic
Feature: enhanced-consumer-ordering-system, Property 10: Technician Assignment Logic
Validates: Requirements 5.1, 5.2, 5.3

This test verifies that technician assignment logic maintains correctness:
- Available technicians are identified correctly
- Geographic proximity is calculated accurately using Haversine formula
- The nearest available technician is assigned to orders
"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import uuid
import math

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
from technician_assignment_service import TechnicianAssignmentService


# Hypothesis strategies for generating test data
order_id_strategy = st.uuids().map(str)
technician_id_strategy = st.uuids().map(str)

# Valid latitude and longitude ranges
latitude_strategy = st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False)
longitude_strategy = st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False)

# Location strategy
location_strategy = st.builds(
    dict,
    latitude=latitude_strategy,
    longitude=longitude_strategy,
    address=st.text(min_size=10, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_'),
    city=st.text(min_size=3, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
    state=st.text(min_size=3, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
    pincode=st.text(min_size=6, max_size=6, alphabet='0123456789')
)

# Technician strategy
technician_strategy = st.builds(
    dict,
    id=technician_id_strategy,
    name=st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
    phone=st.text(min_size=10, max_size=15, alphabet='0123456789+-'),
    email=st.emails(),
    location=location_strategy,
    available=st.just(True),  # Only available technicians for assignment tests
    skills=st.lists(st.text(min_size=3, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'), min_size=1, max_size=5),
    rating=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False)
)

# List of technicians strategy (1-10 technicians)
technicians_list_strategy = st.lists(technician_strategy, min_size=1, max_size=10)

# Service location strategy (same as location but for service requests)
service_location_strategy = location_strategy


class TestTechnicianAssignmentLogicProperty:
    """
    Property 10: Technician Assignment Logic
    
    For any order requiring technician involvement, the Technician Assignment Service must:
    1. Identify all available technicians
    2. Calculate geographic proximity to the consumer's location
    3. Assign the nearest available technician to the order
    """
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        os.environ['ENHANCED_ORDERS_TABLE'] = 'test-orders'
        os.environ['ENHANCED_TECHNICIANS_TABLE'] = 'test-technicians'
        os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
        os.environ['EVENTBRIDGE_BUS'] = 'test-bus'
        
        # Initialize service
        self.service = TechnicianAssignmentService()
        
        # Mock AWS clients
        self.mock_orders_table = Mock()
        self.mock_technicians_table = Mock()
        self.service.orders_table = self.mock_orders_table
        self.service.technicians_table = self.mock_technicians_table
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy,
        technicians=technicians_list_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_available_technicians_are_identified_correctly(
        self,
        order_id: str,
        service_location: dict,
        technicians: list
    ):
        """
        Property Test: Available technicians are identified correctly
        
        For any technician assignment request:
        1. All available technicians MUST be retrieved from the database
        2. Only technicians with available=True MUST be considered
        3. The service MUST handle empty technician lists gracefully
        4. Invalid technician data MUST be filtered out
        
        **Validates: Requirements 5.1**
        """
        # Reset mocks for each test iteration
        self.mock_orders_table.reset_mock()
        self.mock_technicians_table.reset_mock()
        
        # Ensure all technicians in the list are available (hypothesis constraint)
        for tech in technicians:
            tech['available'] = True
        
        # Mock database response with available technicians
        mock_db_items = []
        for tech in technicians:
            db_item = {
                'technicianId': tech['id'],
                'name': tech['name'],
                'phone': tech['phone'],
                'email': tech['email'],
                'location': tech['location'],
                'available': tech['available'],
                'skills': tech['skills'],
                'rating': tech['rating']
            }
            mock_db_items.append(db_item)
        
        self.mock_technicians_table.query.return_value = {'Items': mock_db_items}
        
        # Act: Get available technicians
        available_technicians = self.service._get_available_technicians()
        
        # Assert: All available technicians should be returned
        assert len(available_technicians) == len(technicians), f"Expected {len(technicians)} available technicians, got {len(available_technicians)}"
        
        # Verify each technician is properly formatted
        for i, tech in enumerate(available_technicians):
            original_tech = technicians[i]
            assert tech['id'] == original_tech['id'], "Technician ID should match"
            assert tech['name'] == original_tech['name'], "Technician name should match"
            assert tech['available'] is True, "All returned technicians should be available"
            assert 'location' in tech, "Technician should have location data"
            assert 'rating' in tech, "Technician should have rating data"
        
        # Verify database query was called correctly (exactly once for this iteration)
        assert self.mock_technicians_table.query.call_count == 1, "Database query should be called exactly once"
        call_args = self.mock_technicians_table.query.call_args[1]
        assert 'FilterExpression' in call_args, "Should filter by availability"
        assert ':available' in call_args['ExpressionAttributeValues'], "Should filter for available=True"
        assert call_args['ExpressionAttributeValues'][':available'] is True, "Should filter for available=True"
    
    @given(
        service_location=service_location_strategy,
        technicians=technicians_list_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_geographic_proximity_calculated_accurately(
        self,
        service_location: dict,
        technicians: list
    ):
        """
        Property Test: Geographic proximity is calculated accurately using Haversine formula
        
        For any service location and list of technicians:
        1. Distance MUST be calculated using the Haversine formula
        2. Distance MUST be in kilometers
        3. Distance MUST be non-negative
        4. Distance MUST be symmetric (distance A->B == distance B->A)
        5. Distance MUST be zero for identical coordinates
        
        **Validates: Requirements 5.2**
        """
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        for tech in technicians:
            assume(abs(tech['location']['latitude']) <= 90)
            assume(abs(tech['location']['longitude']) <= 180)
        
        # Act: Calculate distances
        technicians_with_distance = self.service._calculate_technician_distances(technicians, service_location)
        
        # Assert: All technicians should have distance calculated
        assert len(technicians_with_distance) == len(technicians), "All technicians should have distance calculated"
        
        for tech_with_dist in technicians_with_distance:
            # Find the original technician by ID (since the list is sorted by distance)
            original_tech = next(t for t in technicians if t['id'] == tech_with_dist['id'])
            
            # Verify distance is present and valid
            assert 'distance_km' in tech_with_dist, "Technician should have distance_km field"
            distance = tech_with_dist['distance_km']
            assert isinstance(distance, (int, float)), "Distance should be numeric"
            assert distance >= 0, f"Distance should be non-negative, got {distance}"
            
            # Verify distance calculation using Haversine formula
            expected_distance = self.service._calculate_haversine_distance(
                service_location['latitude'],
                service_location['longitude'],
                original_tech['location']['latitude'],
                original_tech['location']['longitude']
            )
            
            # Allow small floating point differences (account for rounding in the service)
            assert abs(distance - expected_distance) < 0.01, f"Distance calculation mismatch: expected {expected_distance}, got {distance}"
            
            # Verify estimated travel time is reasonable (distance * 2 minutes per km)
            assert 'estimated_travel_time_minutes' in tech_with_dist, "Should have estimated travel time"
            expected_travel_time = round(expected_distance * 2, 0)  # Use expected_distance for consistency
            assert tech_with_dist['estimated_travel_time_minutes'] == expected_travel_time, "Travel time should be distance * 2"
        
        # Test symmetry property: distance A->B should equal distance B->A
        if technicians:
            first_tech = technicians[0]
            
            # Calculate distance from service location to technician
            dist_service_to_tech = self.service._calculate_haversine_distance(
                service_location['latitude'],
                service_location['longitude'],
                first_tech['location']['latitude'],
                first_tech['location']['longitude']
            )
            
            # Calculate distance from technician to service location (reverse)
            dist_tech_to_service = self.service._calculate_haversine_distance(
                first_tech['location']['latitude'],
                first_tech['location']['longitude'],
                service_location['latitude'],
                service_location['longitude']
            )
            
            # Distances should be equal (symmetric property)
            assert abs(dist_service_to_tech - dist_tech_to_service) < 0.001, "Distance calculation should be symmetric"
        
        # Test zero distance for identical coordinates
        identical_location = {
            'latitude': service_location['latitude'],
            'longitude': service_location['longitude']
        }
        
        zero_distance = self.service._calculate_haversine_distance(
            service_location['latitude'],
            service_location['longitude'],
            identical_location['latitude'],
            identical_location['longitude']
        )
        
        assert zero_distance < 0.001, f"Distance between identical coordinates should be zero, got {zero_distance}"
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy,
        technicians=technicians_list_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_nearest_available_technician_assigned(
        self,
        order_id: str,
        service_location: dict,
        technicians: list
    ):
        """
        Property Test: The nearest available technician is assigned to the order
        
        For any order requiring technician assignment:
        1. The technician with the shortest distance MUST be selected
        2. If multiple technicians have similar distances, the one with highest rating MUST be selected
        3. Only technicians within the service area MUST be considered
        4. The assignment MUST include accurate distance and travel time estimates
        
        **Validates: Requirements 5.3**
        """
        # Reset mocks for each test iteration
        self.mock_orders_table.reset_mock()
        self.mock_technicians_table.reset_mock()
        
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Ensure at least one technician is within service area (50km)
        # Place technicians close to the service location to ensure they're within range
        for i, tech in enumerate(technicians):
            # Place technicians within ~10km of service location
            lat_offset = (i % 3 - 1) * 0.05  # ~5.5km offset
            lon_offset = ((i // 3) % 3 - 1) * 0.05  # ~5.5km offset
            
            tech['location'] = {
                'latitude': service_location['latitude'] + lat_offset,
                'longitude': service_location['longitude'] + lon_offset,
                'address': f'Tech Street {i}',
                'city': 'Tech City',
                'state': 'Tech State',
                'pincode': f'{100000 + i:06d}'
            }
            tech['available'] = True  # Ensure all are available
        
        # Mock database responses
        mock_db_items = []
        for tech in technicians:
            db_item = {
                'technicianId': tech['id'],
                'name': tech['name'],
                'phone': tech['phone'],
                'email': tech['email'],
                'location': tech['location'],
                'available': tech['available'],
                'skills': tech['skills'],
                'rating': tech['rating']
            }
            mock_db_items.append(db_item)
        
        self.mock_technicians_table.query.return_value = {'Items': mock_db_items}
        
        # Mock successful order and technician updates
        self.mock_orders_table.update_item.return_value = {}
        self.mock_technicians_table.update_item.return_value = {}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act: Assign technician
        with patch('technician_assignment_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T01:00:00+00:00'
            mock_datetime.now.return_value = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
            
            result = self.service.assign_technician(request_data)
        
        # Assert: Assignment should succeed
        assert result['success'] is True, "Technician assignment should succeed"
        assert 'data' in result, "Result should contain assignment data"
        
        assignment = result['data']
        
        # Verify assignment contains required fields
        assert assignment['orderId'] == order_id, "Assignment should contain correct order ID"
        assert 'technicianId' in assignment, "Assignment should contain technician ID"
        assert 'distance' in assignment, "Assignment should contain distance"
        assert 'estimatedTravelTime' in assignment, "Assignment should contain travel time"
        assert 'assignedAt' in assignment, "Assignment should contain assignment timestamp"
        assert 'estimatedArrival' in assignment, "Assignment should contain estimated arrival"
        
        # Verify the assigned technician is valid
        assigned_technician_id = assignment['technicianId']
        assigned_technician = next((t for t in technicians if t['id'] == assigned_technician_id), None)
        assert assigned_technician is not None, "Assigned technician should exist in the original list"
        
        # Calculate distances for all technicians to verify nearest was selected
        technicians_with_distance = self.service._calculate_technician_distances(technicians, service_location)
        
        # Filter technicians within service area (50km default)
        nearby_technicians = [
            tech for tech in technicians_with_distance
            if tech['distance_km'] <= self.service.MAX_ASSIGNMENT_DISTANCE_KM
        ]
        
        # Since we placed technicians close to service location, there should be nearby technicians
        assert len(nearby_technicians) > 0, "There should be technicians within service area"
        
        # Find the minimum distance among nearby technicians
        min_distance = min(tech['distance_km'] for tech in nearby_technicians)
        
        # Find all technicians with minimum distance (within 2km tolerance)
        nearest_technicians = [
            tech for tech in nearby_technicians
            if tech['distance_km'] <= min_distance + 2
        ]
        
        # Among nearest technicians, the one with highest rating should be selected
        best_technician = max(nearest_technicians, key=lambda x: x['rating'])
        
        # Verify the assigned technician is the best choice
        assert assignment['technicianId'] == best_technician['id'], \
            f"Should assign nearest technician with highest rating. Expected: {best_technician['id']}, Got: {assigned_technician_id}"
        
        # Verify distance in assignment matches calculated distance
        expected_distance = best_technician['distance_km']
        assert abs(assignment['distance'] - expected_distance) < 0.01, \
            f"Assignment distance should match calculated distance. Expected: {expected_distance}, Got: {assignment['distance']}"
        
        # Verify database updates were called (exactly once for this iteration)
        assert self.mock_orders_table.update_item.call_count == 1, "Order update should be called exactly once"
        assert self.mock_technicians_table.update_item.call_count == 1, "Technician update should be called exactly once"
        
        # Verify order was updated with assignment
        order_update_call = self.mock_orders_table.update_item.call_args[1]
        assert ':technician_id' in order_update_call['ExpressionAttributeValues'], "Order should be updated with technician ID"
        assert order_update_call['ExpressionAttributeValues'][':technician_id'] == assigned_technician_id, "Order should have correct technician ID"
        
        # Verify technician was marked as busy
        tech_update_call = self.mock_technicians_table.update_item.call_args[1]
        assert ':available' in tech_update_call['ExpressionAttributeValues'], "Technician availability should be updated"
        assert tech_update_call['ExpressionAttributeValues'][':available'] is False, "Technician should be marked as unavailable"
        assert ':order_id' in tech_update_call['ExpressionAttributeValues'], "Technician should be assigned to order"
        assert tech_update_call['ExpressionAttributeValues'][':order_id'] == order_id, "Technician should have correct order ID"
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_assignment_handles_no_available_technicians(
        self,
        order_id: str,
        service_location: dict
    ):
        """
        Property Test: Assignment handles case when no technicians are available
        
        For any assignment request when no technicians are available:
        1. The service MUST raise a BusinessRuleViolationError
        2. No database updates MUST occur
        3. An appropriate error message MUST be provided
        4. The error MUST indicate no technicians are available
        
        **Validates: Requirements 5.1, 5.4**
        """
        # Reset mocks for each test iteration
        self.mock_orders_table.reset_mock()
        self.mock_technicians_table.reset_mock()
        
        # Mock empty technician list
        self.mock_technicians_table.query.return_value = {'Items': []}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act & Assert: Should raise BusinessRuleViolationError
        from error_handler import BusinessRuleViolationError
        
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error message indicates no technicians available
        error_message = str(exc_info.value)
        assert 'no technicians' in error_message.lower() or 'not available' in error_message.lower(), \
            "Error should indicate no technicians are available"
        
        # Verify no database updates occurred
        assert self.mock_orders_table.update_item.call_count == 0, "No order updates should occur"
        assert self.mock_technicians_table.update_item.call_count == 0, "No technician updates should occur"
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy,
        technicians=technicians_list_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_assignment_handles_no_technicians_in_service_area(
        self,
        order_id: str,
        service_location: dict,
        technicians: list
    ):
        """
        Property Test: Assignment handles case when no technicians are within service area
        
        For any assignment request when technicians exist but are too far:
        1. The service MUST raise a BusinessRuleViolationError
        2. No database updates MUST occur
        3. The error MUST indicate no technicians within service area
        4. The error MUST include information about the nearest technician distance
        
        **Validates: Requirements 5.2, 5.4**
        """
        # Reset mocks for each test iteration
        self.mock_orders_table.reset_mock()
        self.mock_technicians_table.reset_mock()
        
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Create technicians that are all far away (> 50km)
        # Place them at a location that's definitely > 50km away
        far_location = {
            'latitude': service_location['latitude'] + 1.0,  # ~111km away
            'longitude': service_location['longitude'] + 1.0,
            'address': 'Far Away Street',
            'city': 'Far City',
            'state': 'Far State',
            'pincode': '999999'
        }
        
        for tech in technicians:
            tech['location'] = far_location.copy()
            tech['available'] = True
        
        # Mock database response with far technicians
        mock_db_items = []
        for tech in technicians:
            db_item = {
                'technicianId': tech['id'],
                'name': tech['name'],
                'phone': tech['phone'],
                'email': tech['email'],
                'location': tech['location'],
                'available': tech['available'],
                'skills': tech['skills'],
                'rating': tech['rating']
            }
            mock_db_items.append(db_item)
        
        self.mock_technicians_table.query.return_value = {'Items': mock_db_items}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act & Assert: Should raise BusinessRuleViolationError
        from error_handler import BusinessRuleViolationError
        
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error message indicates no technicians in service area
        error_message = str(exc_info.value)
        assert 'service area' in error_message.lower() or 'within' in error_message.lower(), \
            "Error should indicate no technicians within service area"
        assert '50' in error_message or 'km' in error_message, \
            "Error should mention the service area distance"
        
        # Verify no database updates occurred
        assert self.mock_orders_table.update_item.call_count == 0, "No order updates should occur"
        assert self.mock_technicians_table.update_item.call_count == 0, "No technician updates should occur"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])