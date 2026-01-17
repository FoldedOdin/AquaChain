"""
Property-based tests for courier payload normalization
Feature: shipment-tracking-automation, Property 10: Courier Payload Normalization
Validates: Requirements 2.2

This test verifies that courier webhook payload normalization is robust:
- All courier payloads are normalized to internal format
- Required fields (tracking_number, status, location, timestamp, description) are present
- Missing or malformed fields are handled gracefully
- Invalid payloads return None
- Normalized output is consistent across couriers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import Dict, Any, Optional
import json


def normalize_webhook_payload(courier_name: str, payload: Dict) -> Optional[Dict]:
    """
    Normalize courier-specific webhook payload to internal format.
    Extracts: tracking_number, status, location, timestamp, description
    Handles missing or malformed fields gracefully.
    Returns None for invalid payloads.
    
    Requirements: 2.2
    """
    try:
        if not payload or not isinstance(payload, dict):
            print(f"ERROR: Invalid payload type: {type(payload)}")
            return None
        
        if courier_name.lower() == 'delhivery':
            # Extract tracking number
            tracking_number = payload.get('waybill', '').strip()
            if not tracking_number:
                print("ERROR: Missing 'waybill' in Delhivery payload")
                return None
            
            # Extract status
            status = payload.get('Status', '').strip()
            if not status:
                print("ERROR: Missing 'Status' in Delhivery payload")
                return None
            
            # Extract scan details (latest scan)
            scans = payload.get('Scans', [])
            if scans and isinstance(scans, list) and len(scans) > 0:
                latest_scan = scans[-1]
                scan_detail = latest_scan.get('ScanDetail', {}) if isinstance(latest_scan, dict) else {}
                location = scan_detail.get('ScannedLocation', 'Unknown')
                timestamp = scan_detail.get('ScanDateTime', '')
                description = scan_detail.get('Instructions', 'Status update')
            else:
                location = 'Unknown'
                timestamp = ''
                description = 'Status update'
            
            # Use current time as fallback only if timestamp is missing
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': location,
                'timestamp': timestamp,
                'description': description
            }
        
        elif courier_name.lower() == 'bluedart':
            tracking_number = payload.get('awb_number', '').strip()
            status = payload.get('status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in BlueDart payload")
                return None
            
            timestamp = payload.get('status_date', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('current_location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('status_description', 'Status update')
            }
        
        elif courier_name.lower() == 'dtdc':
            tracking_number = payload.get('reference_number', '').strip()
            status = payload.get('shipment_status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in DTDC payload")
                return None
            
            timestamp = payload.get('timestamp', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('remarks', 'Status update')
            }
        
        else:
            # Generic fallback for unknown couriers
            print(f"WARNING: Unknown courier '{courier_name}', using generic normalization")
            tracking_number = payload.get('tracking_number', '').strip()
            status = payload.get('status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in generic payload")
                return None
            
            timestamp = payload.get('timestamp', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('description', 'Status update')
            }
    
    except Exception as e:
        print(f"ERROR: Payload normalization exception: {str(e)}")
        return None


# Hypothesis strategies for generating test data

# Generate valid tracking numbers
tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=8,
    max_size=20
)

# Generate valid status strings
status_strategy = st.sampled_from([
    'Picked Up', 'In Transit', 'Out for Delivery', 'Delivered',
    'Delivery Failed', 'RTO', 'Returned', 'Cancelled',
    'MANIFESTED', 'IN TRANSIT', 'OUT FOR DELIVERY', 'DELIVERED',
    'BOOKED', 'PICKED', 'IN-TRANSIT', 'OUT-FOR-DELIVERY'
])

# Generate location strings
location_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ',
    min_size=3,
    max_size=50
)

# Generate ISO timestamp strings
timestamp_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31)
).map(lambda dt: dt.isoformat())

# Generate description strings
description_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,',
    min_size=5,
    max_size=100
)


class TestCourierPayloadNormalization:
    """
    Property 10: Courier Payload Normalization
    
    For any courier webhook payload, the normalization function must produce
    a valid internal format containing tracking_number, status, location,
    timestamp, and description fields.
    
    This ensures:
    1. All courier formats are normalized to consistent internal structure
    2. Required fields are always present in normalized output
    3. Missing or malformed fields are handled gracefully
    4. Invalid payloads return None
    5. Normalization is consistent and deterministic
    """
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_delhivery_payload_normalization_produces_valid_format(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str
    ):
        """
        Property Test: Delhivery payloads are normalized to valid internal format
        
        For any valid Delhivery webhook payload:
        1. Normalization MUST return a dict (not None)
        2. Result MUST contain all required fields: tracking_number, status,
           location, timestamp, description
        3. tracking_number and status MUST match input values
        
        **Validates: Requirements 2.2**
        """
        # Create Delhivery-format payload
        payload = {
            'waybill': tracking_number,
            'Status': status,
            'Scans': [{
                'ScanDetail': {
                    'ScannedLocation': location,
                    'ScanDateTime': timestamp,
                    'Instructions': description
                }
            }]
        }
        
        # Normalize payload
        result = normalize_webhook_payload('delhivery', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Valid Delhivery payload must be normalized successfully"
        
        # Assert: All required fields must be present
        required_fields = ['tracking_number', 'status', 'location', 'timestamp', 'description']
        for field in required_fields:
            assert field in result, f"Normalized payload must contain '{field}' field"
        
        # Assert: tracking_number and status must match input
        assert result['tracking_number'] == tracking_number, "tracking_number must match input"
        assert result['status'] == status, "status must match input"
        assert result['location'] == location, "location must match input"
        assert result['timestamp'] == timestamp, "timestamp must match input"
        assert result['description'] == description, "description must match input"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_bluedart_payload_normalization_produces_valid_format(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str
    ):
        """
        Property Test: BlueDart payloads are normalized to valid internal format
        
        For any valid BlueDart webhook payload:
        1. Normalization MUST return a dict (not None)
        2. Result MUST contain all required fields
        3. Field values MUST match input values
        
        **Validates: Requirements 2.2**
        """
        # Create BlueDart-format payload
        payload = {
            'awb_number': tracking_number,
            'status': status,
            'current_location': location,
            'status_date': timestamp,
            'status_description': description
        }
        
        # Normalize payload
        result = normalize_webhook_payload('bluedart', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Valid BlueDart payload must be normalized successfully"
        
        # Assert: All required fields must be present
        required_fields = ['tracking_number', 'status', 'location', 'timestamp', 'description']
        for field in required_fields:
            assert field in result, f"Normalized payload must contain '{field}' field"
        
        # Assert: Field values must match input
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status
        assert result['location'] == location
        assert result['timestamp'] == timestamp
        assert result['description'] == description
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_dtdc_payload_normalization_produces_valid_format(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str
    ):
        """
        Property Test: DTDC payloads are normalized to valid internal format
        
        For any valid DTDC webhook payload:
        1. Normalization MUST return a dict (not None)
        2. Result MUST contain all required fields
        3. Field values MUST match input values
        
        **Validates: Requirements 2.2**
        """
        # Create DTDC-format payload
        payload = {
            'reference_number': tracking_number,
            'shipment_status': status,
            'location': location,
            'timestamp': timestamp,
            'remarks': description
        }
        
        # Normalize payload
        result = normalize_webhook_payload('dtdc', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Valid DTDC payload must be normalized successfully"
        
        # Assert: All required fields must be present
        required_fields = ['tracking_number', 'status', 'location', 'timestamp', 'description']
        for field in required_fields:
            assert field in result, f"Normalized payload must contain '{field}' field"
        
        # Assert: Field values must match input
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status
        assert result['location'] == location
        assert result['timestamp'] == timestamp
        assert result['description'] == description
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_missing_tracking_number_returns_none(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: Missing tracking number returns None
        
        For any courier payload missing the tracking number field:
        1. Normalization MUST return None
        2. Invalid payload MUST NOT be processed
        
        **Validates: Requirements 2.2**
        """
        # Test Delhivery without waybill
        delhivery_payload = {
            'Status': status,
            'Scans': []
        }
        result = normalize_webhook_payload('delhivery', delhivery_payload)
        assert result is None, "Delhivery payload without waybill must return None"
        
        # Test BlueDart without awb_number
        bluedart_payload = {
            'status': status
        }
        result = normalize_webhook_payload('bluedart', bluedart_payload)
        assert result is None, "BlueDart payload without awb_number must return None"
        
        # Test DTDC without reference_number
        dtdc_payload = {
            'shipment_status': status
        }
        result = normalize_webhook_payload('dtdc', dtdc_payload)
        assert result is None, "DTDC payload without reference_number must return None"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_missing_status_returns_none(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: Missing status returns None
        
        For any courier payload missing the status field:
        1. Normalization MUST return None
        2. Invalid payload MUST NOT be processed
        
        **Validates: Requirements 2.2**
        """
        # Test Delhivery without Status
        delhivery_payload = {
            'waybill': tracking_number,
            'Scans': []
        }
        result = normalize_webhook_payload('delhivery', delhivery_payload)
        assert result is None, "Delhivery payload without Status must return None"
        
        # Test BlueDart without status
        bluedart_payload = {
            'awb_number': tracking_number
        }
        result = normalize_webhook_payload('bluedart', bluedart_payload)
        assert result is None, "BlueDart payload without status must return None"
        
        # Test DTDC without shipment_status
        dtdc_payload = {
            'reference_number': tracking_number
        }
        result = normalize_webhook_payload('dtdc', dtdc_payload)
        assert result is None, "DTDC payload without shipment_status must return None"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_tracking_number_returns_none(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: Empty tracking number returns None
        
        For any courier payload with empty/whitespace tracking number:
        1. Normalization MUST return None
        2. Invalid payload MUST NOT be processed
        
        **Validates: Requirements 2.2**
        """
        # Test Delhivery with empty waybill
        delhivery_payload = {
            'waybill': '   ',  # Whitespace only
            'Status': status,
            'Scans': []
        }
        result = normalize_webhook_payload('delhivery', delhivery_payload)
        assert result is None, "Delhivery payload with empty waybill must return None"
        
        # Test BlueDart with empty awb_number
        bluedart_payload = {
            'awb_number': '',
            'status': status
        }
        result = normalize_webhook_payload('bluedart', bluedart_payload)
        assert result is None, "BlueDart payload with empty awb_number must return None"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_status_returns_none(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: Empty status returns None
        
        For any courier payload with empty/whitespace status:
        1. Normalization MUST return None
        2. Invalid payload MUST NOT be processed
        
        **Validates: Requirements 2.2**
        """
        # Test Delhivery with empty Status
        delhivery_payload = {
            'waybill': tracking_number,
            'Status': '   ',  # Whitespace only
            'Scans': []
        }
        result = normalize_webhook_payload('delhivery', delhivery_payload)
        assert result is None, "Delhivery payload with empty Status must return None"
        
        # Test DTDC with empty shipment_status
        dtdc_payload = {
            'reference_number': tracking_number,
            'shipment_status': ''
        }
        result = normalize_webhook_payload('dtdc', dtdc_payload)
        assert result is None, "DTDC payload with empty shipment_status must return None"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_null_payload_returns_none(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: Null/None payload returns None
        
        For any courier with None or non-dict payload:
        1. Normalization MUST return None
        2. Invalid payload MUST NOT be processed
        
        **Validates: Requirements 2.2**
        """
        # Test with None payload
        result = normalize_webhook_payload('delhivery', None)
        assert result is None, "None payload must return None"
        
        # Test with non-dict payload (string)
        result = normalize_webhook_payload('bluedart', "not a dict")
        assert result is None, "String payload must return None"
        
        # Test with non-dict payload (list)
        result = normalize_webhook_payload('dtdc', [1, 2, 3])
        assert result is None, "List payload must return None"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_delhivery_missing_scans_uses_defaults(
        self,
        tracking_number: str,
        status: str,
        location: str
    ):
        """
        Property Test: Delhivery payload without Scans uses default values
        
        For any Delhivery payload without Scans array:
        1. Normalization MUST still succeed
        2. Default values MUST be used for location, timestamp, description
        3. Required fields tracking_number and status MUST be present
        
        **Validates: Requirements 2.2**
        """
        # Create Delhivery payload without Scans
        payload = {
            'waybill': tracking_number,
            'Status': status
        }
        
        # Normalize payload
        result = normalize_webhook_payload('delhivery', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Delhivery payload without Scans must still normalize"
        
        # Assert: Required fields must be present
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status
        
        # Assert: Default values must be used
        assert result['location'] == 'Unknown', "Missing location must default to 'Unknown'"
        assert 'timestamp' in result, "timestamp must be present"
        assert result['description'] == 'Status update', "Missing description must default to 'Status update'"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_bluedart_missing_optional_fields_uses_defaults(
        self,
        tracking_number: str,
        status: str
    ):
        """
        Property Test: BlueDart payload without optional fields uses defaults
        
        For any BlueDart payload with only required fields:
        1. Normalization MUST succeed
        2. Default values MUST be used for missing optional fields
        
        **Validates: Requirements 2.2**
        """
        # Create BlueDart payload with only required fields
        payload = {
            'awb_number': tracking_number,
            'status': status
        }
        
        # Normalize payload
        result = normalize_webhook_payload('bluedart', payload)
        
        # Assert: Result must not be None
        assert result is not None, "BlueDart payload with only required fields must normalize"
        
        # Assert: Required fields must be present
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status
        
        # Assert: Default values must be used for optional fields
        assert result['location'] == 'Unknown'
        assert 'timestamp' in result
        assert result['description'] == 'Status update'
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_normalization_is_deterministic(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str
    ):
        """
        Property Test: Normalization is deterministic
        
        For any courier payload, normalizing the same payload multiple times
        must always produce identical results.
        
        **Validates: Requirements 2.2**
        """
        # Create Delhivery payload
        payload = {
            'waybill': tracking_number,
            'Status': status,
            'Scans': [{
                'ScanDetail': {
                    'ScannedLocation': location,
                    'ScanDateTime': timestamp,
                    'Instructions': description
                }
            }]
        }
        
        # Normalize multiple times
        results = [normalize_webhook_payload('delhivery', payload) for _ in range(5)]
        
        # Assert: All results must be identical
        for i in range(1, len(results)):
            assert results[i] == results[0], "Normalization must be deterministic"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_generic_courier_normalization(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str
    ):
        """
        Property Test: Generic courier normalization works for unknown couriers
        
        For any unknown courier with generic payload format:
        1. Normalization MUST succeed
        2. All required fields MUST be present
        
        **Validates: Requirements 2.2**
        """
        # Create generic payload
        payload = {
            'tracking_number': tracking_number,
            'status': status,
            'location': location,
            'timestamp': timestamp,
            'description': description
        }
        
        # Normalize with unknown courier name
        result = normalize_webhook_payload('unknown_courier', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Generic payload must normalize for unknown courier"
        
        # Assert: All fields must match input
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status
        assert result['location'] == location
        assert result['timestamp'] == timestamp
        assert result['description'] == description
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        timestamp=timestamp_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_courier_name_is_case_insensitive(
        self,
        tracking_number: str,
        status: str,
        timestamp: str
    ):
        """
        Property Test: Courier name matching is case-insensitive
        
        For any courier payload, the courier name should be matched
        case-insensitively (DELHIVERY, delhivery, Delhivery all work).
        
        **Validates: Requirements 2.2**
        """
        # Create Delhivery payload with timestamp to ensure determinism
        payload = {
            'waybill': tracking_number,
            'Status': status,
            'Scans': [{
                'ScanDetail': {
                    'ScannedLocation': 'Test Location',
                    'ScanDateTime': timestamp,
                    'Instructions': 'Test instruction'
                }
            }]
        }
        
        # Test with different case variations
        result_lower = normalize_webhook_payload('delhivery', payload)
        result_upper = normalize_webhook_payload('DELHIVERY', payload)
        result_mixed = normalize_webhook_payload('Delhivery', payload)
        
        # Assert: All should succeed
        assert result_lower is not None, "Lowercase courier name must work"
        assert result_upper is not None, "Uppercase courier name must work"
        assert result_mixed is not None, "Mixed case courier name must work"
        
        # Assert: All should produce same result
        assert result_lower == result_upper == result_mixed, "Case variations must produce identical results"
    
    @given(
        tracking_number=tracking_number_strategy,
        status=status_strategy,
        location=location_strategy,
        timestamp=timestamp_strategy,
        description=description_strategy,
        extra_fields=st.dictionaries(
            keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_extra_fields_are_ignored(
        self,
        tracking_number: str,
        status: str,
        location: str,
        timestamp: str,
        description: str,
        extra_fields: Dict[str, Any]
    ):
        """
        Property Test: Extra fields in payload are ignored
        
        For any courier payload with additional unknown fields:
        1. Normalization MUST still succeed
        2. Only standard fields MUST be in output
        3. Extra fields MUST NOT cause errors
        
        **Validates: Requirements 2.2**
        """
        # Create Delhivery payload with extra fields
        payload = {
            'waybill': tracking_number,
            'Status': status,
            'Scans': [{
                'ScanDetail': {
                    'ScannedLocation': location,
                    'ScanDateTime': timestamp,
                    'Instructions': description
                }
            }],
            **extra_fields  # Add extra unknown fields
        }
        
        # Normalize payload
        result = normalize_webhook_payload('delhivery', payload)
        
        # Assert: Result must not be None
        assert result is not None, "Payload with extra fields must normalize successfully"
        
        # Assert: Only standard fields in output
        assert set(result.keys()) == {'tracking_number', 'status', 'location', 'timestamp', 'description'}, \
            "Normalized output must contain only standard fields"
        
        # Assert: Required values must be correct
        assert result['tracking_number'] == tracking_number
        assert result['status'] == status


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
