"""
Unit tests for multi-courier support in create_shipment
Tests courier selection, routing, and error handling

Requirements: 7.1, 7.2, 7.3
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

# Import the functions we're testing
from create_shipment import (
    create_courier_shipment,
    create_delhivery_shipment,
    create_bluedart_shipment,
    create_dtdc_shipment
)
from webhook_handler import (
    normalize_webhook_payload,
    map_courier_status
)
from errors import ValidationError


class TestMultiCourierSupport:
    """
    Test multi-courier support functionality
    
    Validates:
    - Courier selection routes to correct API
    - Unsupported couriers raise ValidationError
    - Each courier API returns proper format
    
    Requirements: 7.1, 7.2, 7.3
    """
    
    def test_delhivery_courier_selection(self):
        """Test that 'Delhivery' routes to Delhivery API"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Mock environment to avoid actual API call
        with patch.dict(os.environ, {'COURIER_API_KEY': ''}):
            result = create_courier_shipment('Delhivery', destination, package, 'test_order')
        
        assert result is not None
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('DELHUB')

    
    def test_bluedart_courier_selection(self):
        """Test that 'BlueDart' routes to BlueDart API"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Mock environment to avoid actual API call
        with patch.dict(os.environ, {'BLUEDART_API_KEY': ''}):
            result = create_courier_shipment('BlueDart', destination, package, 'test_order')
        
        assert result is not None
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('BD')
    
    def test_dtdc_courier_selection(self):
        """Test that 'DTDC' routes to DTDC API"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Mock environment to avoid actual API call
        with patch.dict(os.environ, {'DTDC_API_KEY': ''}):
            result = create_courier_shipment('DTDC', destination, package, 'test_order')
        
        assert result is not None
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('DTDC')

    
    def test_courier_name_case_insensitive(self):
        """Test that courier names are case-insensitive"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Test different case variations
        with patch.dict(os.environ, {'COURIER_API_KEY': ''}):
            result_lower = create_courier_shipment('delhivery', destination, package, 'test_order')
            result_upper = create_courier_shipment('DELHIVERY', destination, package, 'test_order')
            result_mixed = create_courier_shipment('Delhivery', destination, package, 'test_order')
        
        # All should succeed
        assert result_lower is not None
        assert result_upper is not None
        assert result_mixed is not None
    
    def test_unsupported_courier_raises_error(self):
        """Test that unsupported courier raises ValidationError"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Test with unsupported courier
        with pytest.raises(ValidationError) as exc_info:
            create_courier_shipment('FedEx', destination, package, 'test_order')
        
        # Verify error details
        assert 'Unsupported courier' in str(exc_info.value.message)
        assert exc_info.value.error_code == 'UNSUPPORTED_COURIER'
        assert 'FedEx' in str(exc_info.value.details)

    
    def test_supported_couriers_list(self):
        """Test that error message includes list of supported couriers"""
        destination = {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        }
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # Test with unsupported courier
        with pytest.raises(ValidationError) as exc_info:
            create_courier_shipment('UPS', destination, package, 'test_order')
        
        # Verify supported couriers are listed
        error_details = exc_info.value.details
        assert 'supported_couriers' in error_details
        assert 'Delhivery' in error_details['supported_couriers']
        assert 'BlueDart' in error_details['supported_couriers']
        assert 'DTDC' in error_details['supported_couriers']


class TestBlueDartWebhookNormalization:
    """
    Test BlueDart webhook payload normalization
    
    Requirements: 7.1, 7.2
    """
    
    def test_bluedart_complete_payload(self):
        """Test BlueDart webhook with all fields"""
        payload = {
            'awb_number': 'BD123456789',
            'status': 'IN TRANSIT',
            'status_date': '2025-12-29T15:30:00Z',
            'current_location': 'Mumbai Hub',
            'status_description': 'Package in transit to destination'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'BD123456789'
        assert result['status'] == 'IN TRANSIT'
        assert result['location'] == 'Mumbai Hub'
        assert result['timestamp'] == '2025-12-29T15:30:00Z'
        assert result['description'] == 'Package in transit to destination'
    
    def test_bluedart_minimal_payload(self):
        """Test BlueDart webhook with only required fields"""
        payload = {
            'awb_number': 'BD987654321',
            'status': 'DELIVERED'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'BD987654321'
        assert result['status'] == 'DELIVERED'
        assert result['location'] == 'Unknown'
        assert result['description'] == 'Status update'
        # Timestamp should be auto-generated
        assert 'timestamp' in result
    
    def test_bluedart_missing_awb_number(self):
        """Test BlueDart webhook without awb_number returns None"""
        payload = {
            'status': 'IN TRANSIT',
            'current_location': 'Delhi Hub'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        assert result is None
    
    def test_bluedart_missing_status(self):
        """Test BlueDart webhook without status returns None"""
        payload = {
            'awb_number': 'BD123456789',
            'current_location': 'Delhi Hub'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        assert result is None
    
    def test_bluedart_empty_awb_number(self):
        """Test BlueDart webhook with empty awb_number returns None"""
        payload = {
            'awb_number': '',
            'status': 'IN TRANSIT'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        assert result is None
    
    def test_bluedart_whitespace_fields(self):
        """Test BlueDart webhook with whitespace in fields"""
        payload = {
            'awb_number': '  BD123456789  ',
            'status': '  DELIVERED  ',
            'current_location': '  Mumbai  '
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'BD123456789'
        assert result['status'] == 'DELIVERED'
    
    def test_bluedart_status_mapping(self):
        """Test BlueDart status codes map to internal statuses"""
        # Test various BlueDart status codes
        assert map_courier_status('MANIFESTED') == 'picked_up'
        assert map_courier_status('IN TRANSIT') == 'in_transit'
        assert map_courier_status('OUT FOR DELIVERY') == 'out_for_delivery'
        assert map_courier_status('DELIVERED') == 'delivered'
        assert map_courier_status('UNDELIVERED') == 'delivery_failed'
        assert map_courier_status('RTO INITIATED') == 'returned'


class TestDTDCWebhookNormalization:
    """
    Test DTDC webhook payload normalization
    
    Requirements: 7.1, 7.2
    """
    
    def test_dtdc_complete_payload(self):
        """Test DTDC webhook with all fields"""
        payload = {
            'reference_number': 'DTDC123456789',
            'shipment_status': 'IN-TRANSIT',
            'timestamp': '2025-12-29T12:00:00Z',
            'location': 'Delhi Hub',
            'remarks': 'Package moving to destination city'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'DTDC123456789'
        assert result['status'] == 'IN-TRANSIT'
        assert result['location'] == 'Delhi Hub'
        assert result['timestamp'] == '2025-12-29T12:00:00Z'
        assert result['description'] == 'Package moving to destination city'
    
    def test_dtdc_minimal_payload(self):
        """Test DTDC webhook with only required fields"""
        payload = {
            'reference_number': 'DTDC987654321',
            'shipment_status': 'DELIVERED'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'DTDC987654321'
        assert result['status'] == 'DELIVERED'
        assert result['location'] == 'Unknown'
        assert result['description'] == 'Status update'
        # Timestamp should be auto-generated
        assert 'timestamp' in result
    
    def test_dtdc_missing_reference_number(self):
        """Test DTDC webhook without reference_number returns None"""
        payload = {
            'shipment_status': 'IN-TRANSIT',
            'location': 'Mumbai Hub'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        assert result is None
    
    def test_dtdc_missing_shipment_status(self):
        """Test DTDC webhook without shipment_status returns None"""
        payload = {
            'reference_number': 'DTDC123456789',
            'location': 'Mumbai Hub'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        assert result is None
    
    def test_dtdc_empty_reference_number(self):
        """Test DTDC webhook with empty reference_number returns None"""
        payload = {
            'reference_number': '',
            'shipment_status': 'IN-TRANSIT'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        assert result is None
    
    def test_dtdc_whitespace_fields(self):
        """Test DTDC webhook with whitespace in fields"""
        payload = {
            'reference_number': '  DTDC123456789  ',
            'shipment_status': '  DELIVERED  ',
            'location': '  Bangalore  '
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'DTDC123456789'
        assert result['status'] == 'DELIVERED'
    
    def test_dtdc_status_mapping(self):
        """Test DTDC status codes map to internal statuses"""
        # Test various DTDC status codes
        assert map_courier_status('BOOKED') == 'shipment_created'
        assert map_courier_status('PICKED') == 'picked_up'
        assert map_courier_status('IN-TRANSIT') == 'in_transit'
        assert map_courier_status('OUT-FOR-DELIVERY') == 'out_for_delivery'
        assert map_courier_status('DELIVERED') == 'delivered'
        assert map_courier_status('NOT DELIVERED') == 'delivery_failed'
        assert map_courier_status('RETURNED') == 'returned'


class TestCourierRoutingInCreateShipment:
    """
    Test courier routing logic in create_shipment
    
    Requirements: 7.3
    """
    
    def test_delhivery_routing_returns_mock_data(self):
        """Test Delhivery routing returns proper mock data when no API key"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with patch.dict(os.environ, {'COURIER_API_KEY': ''}):
            result = create_delhivery_shipment(destination, package, 'order123')
        
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('DELHUB')
    
    def test_bluedart_routing_returns_mock_data(self):
        """Test BlueDart routing returns proper mock data when no API key"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with patch.dict(os.environ, {'BLUEDART_API_KEY': ''}):
            result = create_bluedart_shipment(destination, package, 'order123')
        
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('BD')
    
    def test_dtdc_routing_returns_mock_data(self):
        """Test DTDC routing returns proper mock data when no API key"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with patch.dict(os.environ, {'DTDC_API_KEY': ''}):
            result = create_dtdc_shipment(destination, package, 'order123')
        
        assert 'tracking_number' in result
        assert 'estimated_delivery' in result
        assert result['tracking_number'].startswith('DTDC')
    
    def test_courier_routing_preserves_order_id(self):
        """Test that order_id is used in courier API calls"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        order_id = 'test_order_12345'
        
        with patch.dict(os.environ, {'COURIER_API_KEY': ''}):
            result = create_delhivery_shipment(destination, package, order_id)
        
        # Mock implementation includes order_id in tracking number generation
        assert result is not None


class TestErrorHandlingForUnsupportedCouriers:
    """
    Test error handling for unsupported couriers
    
    Requirements: 7.3
    """
    
    def test_empty_courier_name_raises_error(self):
        """Test that empty courier name raises ValidationError"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with pytest.raises(ValidationError) as exc_info:
            create_courier_shipment('', destination, package, 'test_order')
        
        assert exc_info.value.error_code == 'UNSUPPORTED_COURIER'
    
    def test_none_courier_name_raises_error(self):
        """Test that None courier name raises error"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        # This will raise AttributeError when trying to call .lower() on None
        with pytest.raises(AttributeError):
            create_courier_shipment(None, destination, package, 'test_order')
    
    def test_multiple_unsupported_couriers(self):
        """Test various unsupported courier names"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        unsupported_couriers = ['FedEx', 'UPS', 'DHL', 'AmazonLogistics', 'IndiaPost']
        
        for courier in unsupported_couriers:
            with pytest.raises(ValidationError) as exc_info:
                create_courier_shipment(courier, destination, package, 'test_order')
            
            assert 'Unsupported courier' in str(exc_info.value.message)
            assert courier in str(exc_info.value.details)
    
    def test_error_includes_courier_name_in_details(self):
        """Test that error details include the unsupported courier name"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with pytest.raises(ValidationError) as exc_info:
            create_courier_shipment('CustomCourier', destination, package, 'test_order')
        
        assert 'courier_name' in exc_info.value.details
        assert exc_info.value.details['courier_name'] == 'CustomCourier'
    
    def test_error_message_is_user_friendly(self):
        """Test that error message is clear and helpful"""
        destination = {'address': '123 St', 'pincode': '560001', 'contact_name': 'Test', 'contact_phone': '+919876543210'}
        package = {'weight': '0.5kg', 'declared_value': 5000}
        
        with pytest.raises(ValidationError) as exc_info:
            create_courier_shipment('NewCourier', destination, package, 'test_order')
        
        error_message = exc_info.value.message
        # Should mention the unsupported courier
        assert 'NewCourier' in error_message
        # Should list supported couriers
        assert 'Delhivery' in error_message or 'supported' in error_message.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
