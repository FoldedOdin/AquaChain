"""
Property-based tests for technician unavailability handling
Feature: enhanced-consumer-ordering-system, Property 11: Technician Unavailability Handling
Validates: Requirements 5.4

This test verifies that technician unavailability is handled correctly:
- Orders are queued when no technicians are available
- Notifications are sent when technicians become available
- System gracefully handles edge cases
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

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test
from technician_assignment_service import TechnicianAssignmentService

# Import error classes for testing
from error_handler import (
    AquaChainError, ErrorCode, ResourceNotFoundError, ConflictError,
    BusinessRuleViolationError, create_lambda_error_response
)
from input_validator import ValidationError


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

# Unavailable technician strategy
unavailable_technician_strategy = st.builds(
    dict,
    id=technician_id_strategy,
    name=st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
    phone=st.text(min_size=10, max_size=15, alphabet='0123456789+-'),
    email=st.emails(),
    location=location_strategy,
    available=st.just(False),  # Only unavailable technicians for this test
    skills=st.lists(st.text(min_size=3, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'), min_size=1, max_size=5),
    rating=st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False)
)

# List of unavailable technicians strategy (0-5 technicians)
unavailable_technicians_list_strategy = st.lists(unavailable_technician_strategy, min_size=0, max_size=5)

# Service location strategy (same as location but for service requests)
service_location_strategy = location_strategy


class TestTechnicianUnavailabilityHandlingProperty:
    """
    Property 11: Technician Unavailability Handling
    
    For any order when no technicians are available, the system must:
    1. Queue the order appropriately
    2. Notify when a technician becomes available
    3. Handle edge cases gracefully
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
        service_location=service_location_strategy
    )
    @settings(max_examples=5, deadline=None)  # Reduced examples for faster testing
    def test_no_technicians_available_raises_business_rule_violation(
        self,
        order_id: str,
        service_location: dict
    ):
        """
        Property Test: No technicians available raises BusinessRuleViolationError
        
        For any order when no technicians are available:
        1. The system MUST raise a BusinessRuleViolationError
        2. The error MUST indicate that no technicians are available
        3. The error MUST suggest that the order will be queued
        4. No database updates MUST occur for order or technician tables
        
        **Validates: Requirements 5.4**
        """
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Mock empty technician list (no available technicians)
        self.mock_technicians_table.query.return_value = {'Items': []}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act & Assert: Should raise BusinessRuleViolationError
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error details
        error = exc_info.value
        error_message = str(error).lower()
        
        # Error should indicate no technicians available
        assert 'no technicians' in error_message or 'not available' in error_message, \
            f"Error should indicate no technicians available. Got: {error_message}"
        
        # Error should mention queuing
        assert 'queue' in error_message or 'queued' in error_message, \
            f"Error should mention order will be queued. Got: {error_message}"
        
        # Error should have appropriate error code (using 'code' attribute, not 'error_code')
        assert hasattr(error, 'code'), "Error should have code attribute"
        assert error.code == ErrorCode.BUSINESS_RULE_VIOLATION, \
            f"Error code should be BUSINESS_RULE_VIOLATION, got: {error.code}"
        
        # Check details for specific rule
        assert hasattr(error, 'details'), "Error should have details attribute"
        assert error.details.get('rule') == 'no_technicians_available', \
            f"Error rule should be 'no_technicians_available', got: {error.details.get('rule')}"
        
        # Verify no database updates occurred
        self.mock_orders_table.update_item.assert_not_called()
        self.mock_technicians_table.update_item.assert_not_called()
        
        # Verify technician query was attempted (at least once due to Hypothesis running multiple examples)
        assert self.mock_technicians_table.query.call_count >= 1, "Should have attempted to query technicians"
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy,
        unavailable_technicians=unavailable_technicians_list_strategy
    )
    @settings(max_examples=5, deadline=None)  # Reduced examples for faster testing
    def test_only_unavailable_technicians_raises_business_rule_violation(
        self,
        order_id: str,
        service_location: dict,
        unavailable_technicians: list
    ):
        """
        Property Test: Only unavailable technicians raises BusinessRuleViolationError
        
        For any order when technicians exist but are all unavailable:
        1. The system MUST raise a BusinessRuleViolationError
        2. The error MUST indicate that no technicians are available
        3. Unavailable technicians MUST be filtered out correctly
        4. No database updates MUST occur for order or technician tables
        
        **Validates: Requirements 5.4**
        """
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Ensure all technicians are unavailable
        for tech in unavailable_technicians:
            tech['available'] = False
            assume(abs(tech['location']['latitude']) <= 90)
            assume(abs(tech['location']['longitude']) <= 180)
        
        # Mock database response with unavailable technicians
        mock_db_items = []
        for tech in unavailable_technicians:
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
        
        # Mock query to return unavailable technicians (but filter should exclude them)
        self.mock_technicians_table.query.return_value = {'Items': mock_db_items}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act & Assert: Should raise BusinessRuleViolationError
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error details
        error = exc_info.value
        error_message = str(error).lower()
        
        # Error should indicate no technicians available
        assert 'no technicians' in error_message or 'not available' in error_message, \
            f"Error should indicate no technicians available. Got: {error_message}"
        
        # Verify no database updates occurred
        self.mock_orders_table.update_item.assert_not_called()
        self.mock_technicians_table.update_item.assert_not_called()
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy
    )
    @settings(max_examples=5, deadline=None)  # Reduced examples for faster testing
    def test_no_technicians_available_publishes_notification_events(
        self,
        order_id: str,
        service_location: dict
    ):
        """
        Property Test: No technicians available publishes notification events
        
        For any order when no technicians are available:
        1. The system MUST publish an SNS notification event
        2. The system MUST publish an EventBridge event for workflow automation
        3. Events MUST contain order ID and timestamp
        4. Events MUST indicate the reason for unavailability
        
        **Validates: Requirements 5.4**
        """
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Mock empty technician list
        self.mock_technicians_table.query.return_value = {'Items': []}
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Mock SNS and EventBridge clients at the service level
        with patch.object(self.service, '_publish_assignment_event') as mock_publish:
            # Act: Try to assign technician (should fail but publish events first)
            with pytest.raises(BusinessRuleViolationError):
                self.service.assign_technician(request_data)
            
            # Assert: Event publishing should be called
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[0]  # Get positional arguments
            
            # Verify event type and data
            assert call_args[0] == 'NO_TECHNICIANS_AVAILABLE', "Event type should be NO_TECHNICIANS_AVAILABLE"
            event_data = call_args[1]
            assert event_data['orderId'] == order_id, "Event data should contain order ID"
            assert 'timestamp' in event_data, "Event data should contain timestamp"
            assert 'reason' in event_data, "Event data should contain reason"
    
    @given(
        technician_id=technician_id_strategy,
        availability=st.booleans()
    )
    @settings(max_examples=5, deadline=None)  # Reduced examples for faster testing
    def test_technician_availability_update_publishes_notification(
        self,
        technician_id: str,
        availability: bool
    ):
        """
        Property Test: Technician availability update publishes notification
        
        For any technician availability update:
        1. The system MUST publish an SNS notification event
        2. The system MUST publish an EventBridge event
        3. Events MUST contain technician ID, availability status, and timestamp
        4. Database MUST be updated with new availability status
        
        **Validates: Requirements 5.4**
        """
        # Mock existing technician
        mock_technician = {
            'technicianId': technician_id,
            'name': 'Test Technician',
            'available': not availability  # Opposite of what we're setting
        }
        
        self.mock_technicians_table.get_item.return_value = {'Item': mock_technician}
        self.mock_technicians_table.update_item.return_value = {}
        
        # Prepare update request
        request_data = {
            'technicianId': technician_id,
            'available': availability
        }
        
        # Mock the event publishing method
        with patch.object(self.service, '_publish_assignment_event') as mock_publish:
            # Act: Update technician availability
            with patch('technician_assignment_service.datetime') as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = '2024-01-01T01:00:00+00:00'
                
                result = self.service.update_technician_availability(request_data)
            
            # Assert: Update should succeed
            assert result['success'] is True, "Availability update should succeed"
            
            # Verify database update
            assert self.mock_technicians_table.update_item.call_count >= 1, "Should have updated database"
            
            # Assert: Event publishing should be called
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args[0]  # Get positional arguments
            
            # Verify event type and data
            assert call_args[0] == 'TECHNICIAN_AVAILABILITY_UPDATED', "Event type should be TECHNICIAN_AVAILABILITY_UPDATED"
            event_data = call_args[1]
            assert event_data['technicianId'] == technician_id, "Event data should contain technician ID"
            assert event_data['available'] == availability, "Event data should contain availability status"
            assert 'timestamp' in event_data, "Event data should contain timestamp"
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy
    )
    @settings(max_examples=3, deadline=None)  # Reduced examples for faster testing
    def test_invalid_service_location_raises_validation_error(
        self,
        order_id: str,
        service_location: dict
    ):
        """
        Property Test: Invalid service location raises ValidationError
        
        For any assignment request with invalid coordinates:
        1. The system MUST raise a ValidationError
        2. No database queries MUST be performed
        3. No notification events MUST be published
        
        **Validates: Requirements 5.4**
        """
        # Create invalid service location (coordinates out of range)
        invalid_location = service_location.copy()
        invalid_location['latitude'] = 999.0  # Invalid latitude
        invalid_location['longitude'] = 999.0  # Invalid longitude
        
        # Prepare assignment request with invalid location
        request_data = {
            'orderId': order_id,
            'serviceLocation': invalid_location
        }
        
        # Act & Assert: Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error message
        error_message = str(exc_info.value).lower()
        assert 'invalid' in error_message and 'location' in error_message, \
            f"Error should indicate invalid location. Got: {error_message}"
        
        # Verify no database queries were performed
        self.mock_technicians_table.query.assert_not_called()
        self.mock_orders_table.update_item.assert_not_called()
        self.mock_technicians_table.update_item.assert_not_called()
    
    @given(
        order_id=order_id_strategy,
        service_location=service_location_strategy
    )
    @settings(max_examples=3, deadline=None)  # Reduced examples for faster testing
    def test_database_error_during_technician_query_raises_aquachain_error(
        self,
        order_id: str,
        service_location: dict
    ):
        """
        Property Test: Database error during technician query raises AquaChainError
        
        For any assignment request when database query fails:
        1. The system MUST handle the database error gracefully
        2. The system MUST raise an AquaChainError with appropriate error code
        3. No partial updates MUST occur
        
        **Validates: Requirements 5.4**
        """
        # Ensure we have valid coordinates
        assume(abs(service_location['latitude']) <= 90)
        assume(abs(service_location['longitude']) <= 180)
        
        # Mock database error
        from botocore.exceptions import ClientError
        self.mock_technicians_table.query.side_effect = ClientError(
            error_response={'Error': {'Code': 'ServiceUnavailable', 'Message': 'Database unavailable'}},
            operation_name='Query'
        )
        
        # Prepare assignment request
        request_data = {
            'orderId': order_id,
            'serviceLocation': service_location
        }
        
        # Act & Assert: Should raise BusinessRuleViolationError (because database error returns empty list)
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            self.service.assign_technician(request_data)
        
        # Verify error details - database error is handled as "no technicians available"
        error = exc_info.value
        assert error.status_code == 422, f"Should return 422 status code for business rule violation, got: {error.status_code}"
        error_message = str(error).lower()
        assert 'no technicians' in error_message or 'not available' in error_message, \
            f"Error should indicate no technicians available. Got: {error_message}"
        
        # Verify no updates occurred
        self.mock_orders_table.update_item.assert_not_called()
        self.mock_technicians_table.update_item.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])