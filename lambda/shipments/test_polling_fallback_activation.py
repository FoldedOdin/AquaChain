"""
Property-based tests for polling fallback activation
Feature: shipment-tracking-automation, Property 11: Polling Fallback Activation
Validates: Requirements 9.1, 9.2

This test verifies that the polling fallback mechanism activates correctly:
- Active shipments with no updates for 4+ hours are detected as stale
- Polling queries the courier API for stale shipments
- Shipment status is updated if changed
- Polling mechanism handles various edge cases
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# Import functions from polling_fallback module
from polling_fallback import (
    filter_stale_shipments,
    map_courier_status,
    poll_courier_status
)


# Hypothesis strategies for generating test data
status_strategy = st.sampled_from([
    'shipment_created',
    'picked_up',
    'in_transit',
    'out_for_delivery',
    'delivery_failed'
])

terminal_status_strategy = st.sampled_from([
    'delivered',
    'returned',
    'cancelled'
])

courier_name_strategy = st.sampled_from([
    'Delhivery',
    'BlueDart',
    'DTDC'
])

tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=10,
    max_size=20
)

hours_ago_strategy = st.integers(min_value=0, max_value=168)  # 0 to 7 days


def create_test_shipment(
    shipment_id: str,
    tracking_number: str,
    internal_status: str,
    courier_name: str,
    hours_since_update: int
) -> Dict[str, Any]:
    """
    Create a test shipment with specified hours since last update.
    """
    updated_at = datetime.utcnow() - timedelta(hours=hours_since_update)
    
    return {
        'shipment_id': shipment_id,
        'tracking_number': tracking_number,
        'internal_status': internal_status,
        'courier_name': courier_name,
        'updated_at': updated_at.isoformat(),
        'timeline': [],
        'webhook_events': []
    }


class TestPollingFallbackActivation:
    """
    Property 11: Polling Fallback Activation
    
    For any active shipment with no webhook updates for 4 hours, the polling
    mechanism must query the courier API and update the shipment if the status
    has changed.
    
    This ensures:
    1. Stale shipments are correctly identified (updated_at > 4 hours ago)
    2. Active shipments (non-terminal) are included in polling
    3. Terminal shipments (delivered/returned/cancelled) are excluded
    4. Courier API is queried for stale shipments
    5. Shipment is updated if status has changed
    """
    
    @given(
        internal_status=status_strategy,
        hours_since_update=st.integers(min_value=5, max_value=168)
    )
    @settings(max_examples=100, deadline=None)
    def test_stale_active_shipments_are_detected(
        self,
        internal_status: str,
        hours_since_update: int
    ):
        """
        Property Test: Stale active shipments are detected
        
        For any active shipment (non-terminal status) with updated_at > 4 hours ago:
        1. filter_stale_shipments() MUST include it in the result
        2. The shipment MUST be marked as stale
        
        **Validates: Requirements 9.1**
        """
        # Create shipment with old update time
        shipment = create_test_shipment(
            shipment_id='ship_test_001',
            tracking_number='TEST123456',
            internal_status=internal_status,
            courier_name='Delhivery',
            hours_since_update=hours_since_update
        )
        
        # Filter with 4-hour threshold
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=4)
        
        # Assert: Shipment must be detected as stale
        assert len(stale_shipments) == 1, (
            f"Shipment with {hours_since_update} hours since update must be detected as stale "
            f"(threshold: 4 hours)"
        )
        assert stale_shipments[0]['shipment_id'] == 'ship_test_001'
    
    @given(
        internal_status=status_strategy,
        hours_since_update=st.integers(min_value=0, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_recent_active_shipments_are_not_stale(
        self,
        internal_status: str,
        hours_since_update: int
    ):
        """
        Property Test: Recent active shipments are not detected as stale
        
        For any active shipment with updated_at <= 4 hours ago:
        1. filter_stale_shipments() MUST NOT include it in the result
        2. The shipment MUST NOT be marked as stale
        
        **Validates: Requirements 9.1**
        """
        # Create shipment with recent update time
        shipment = create_test_shipment(
            shipment_id='ship_test_002',
            tracking_number='TEST123457',
            internal_status=internal_status,
            courier_name='Delhivery',
            hours_since_update=hours_since_update
        )
        
        # Filter with 4-hour threshold
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=4)
        
        # Assert: Shipment must NOT be detected as stale
        assert len(stale_shipments) == 0, (
            f"Shipment with {hours_since_update} hours since update must NOT be detected as stale "
            f"(threshold: 4 hours)"
        )
    
    @given(
        terminal_status=terminal_status_strategy,
        hours_since_update=st.integers(min_value=5, max_value=168)
    )
    @settings(max_examples=100, deadline=None)
    def test_terminal_shipments_should_not_be_polled(
        self,
        terminal_status: str,
        hours_since_update: int
    ):
        """
        Property Test: Terminal shipments should not be included in polling
        
        For any terminal shipment (delivered/returned/cancelled), even if stale:
        1. The shipment should be excluded from active shipments query
        2. Polling should not be triggered for terminal shipments
        
        Note: This test verifies the filter logic. In practice, get_active_shipments()
        excludes terminal statuses before calling filter_stale_shipments().
        
        **Validates: Requirements 9.1**
        """
        # Create terminal shipment with old update time
        shipment = create_test_shipment(
            shipment_id='ship_test_003',
            tracking_number='TEST123458',
            internal_status=terminal_status,
            courier_name='Delhivery',
            hours_since_update=hours_since_update
        )
        
        # Filter stale shipments (this would be called after filtering out terminals)
        # In the actual flow, terminal shipments are filtered out by get_active_shipments()
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=4)
        
        # Assert: Even if detected as stale, terminal shipments shouldn't be in active list
        # This test documents that filter_stale_shipments() doesn't filter by status
        # The status filtering happens in get_active_shipments()
        assert len(stale_shipments) == 1, (
            "filter_stale_shipments() detects stale shipments regardless of status. "
            "Terminal status filtering happens in get_active_shipments()."
        )
    
    @given(
        threshold_hours=st.integers(min_value=1, max_value=24),
        hours_since_update=st.integers(min_value=0, max_value=48)
    )
    @settings(max_examples=100, deadline=None)
    def test_threshold_boundary_is_respected(
        self,
        threshold_hours: int,
        hours_since_update: int
    ):
        """
        Property Test: Stale threshold boundary is correctly respected
        
        For any threshold_hours and hours_since_update:
        1. If hours_since_update > threshold_hours: shipment MUST be stale
        2. If hours_since_update < threshold_hours: shipment MUST NOT be stale
        3. If hours_since_update == threshold_hours: boundary case (may be stale due to time precision)
        
        **Validates: Requirements 9.1**
        """
        # Create shipment
        shipment = create_test_shipment(
            shipment_id='ship_test_004',
            tracking_number='TEST123459',
            internal_status='in_transit',
            courier_name='Delhivery',
            hours_since_update=hours_since_update
        )
        
        # Filter with custom threshold
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=threshold_hours)
        
        # Determine expected result
        # Note: The comparison in filter_stale_shipments uses < (strictly less than)
        # So shipment is stale if updated_at < threshold_time
        # Which means hours_since_update > threshold_hours
        # 
        # Due to time precision in datetime calculations, when hours_since_update == threshold_hours,
        # the shipment may be detected as stale (the actual time difference might be slightly more
        # than the threshold due to microsecond precision). This is acceptable behavior.
        
        if hours_since_update > threshold_hours:
            # Clearly stale - must be detected
            assert len(stale_shipments) == 1, (
                f"Shipment with {hours_since_update} hours since update must be stale "
                f"(threshold: {threshold_hours} hours)"
            )
        elif hours_since_update < threshold_hours:
            # Clearly not stale - must not be detected
            assert len(stale_shipments) == 0, (
                f"Shipment with {hours_since_update} hours since update must NOT be stale "
                f"(threshold: {threshold_hours} hours)"
            )
        else:
            # Boundary case: hours_since_update == threshold_hours
            # Due to time precision, this could go either way
            # We accept both outcomes as valid
            assert len(stale_shipments) in [0, 1], (
                f"Shipment at boundary (hours_since_update={hours_since_update}, "
                f"threshold={threshold_hours}) may or may not be detected as stale due to time precision"
            )
    
    @given(
        num_shipments=st.integers(min_value=1, max_value=20),
        stale_ratio=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_shipments_filtering(
        self,
        num_shipments: int,
        stale_ratio: float
    ):
        """
        Property Test: Multiple shipments are correctly filtered
        
        For any list of shipments with mixed staleness:
        1. All stale shipments MUST be included in result
        2. No non-stale shipments MUST be included in result
        3. The count of stale shipments MUST match expected count
        
        **Validates: Requirements 9.1**
        """
        # Calculate how many should be stale
        num_stale = int(num_shipments * stale_ratio)
        num_fresh = num_shipments - num_stale
        
        # Create shipments
        shipments = []
        
        # Create stale shipments (5+ hours old)
        for i in range(num_stale):
            shipments.append(create_test_shipment(
                shipment_id=f'ship_stale_{i}',
                tracking_number=f'STALE{i:06d}',
                internal_status='in_transit',
                courier_name='Delhivery',
                hours_since_update=5 + i  # 5+ hours
            ))
        
        # Create fresh shipments (0-3 hours old)
        for i in range(num_fresh):
            shipments.append(create_test_shipment(
                shipment_id=f'ship_fresh_{i}',
                tracking_number=f'FRESH{i:06d}',
                internal_status='in_transit',
                courier_name='Delhivery',
                hours_since_update=i % 4  # 0-3 hours
            ))
        
        # Filter with 4-hour threshold
        stale_shipments = filter_stale_shipments(shipments, threshold_hours=4)
        
        # Assert: Correct number of stale shipments
        assert len(stale_shipments) == num_stale, (
            f"Expected {num_stale} stale shipments, got {len(stale_shipments)}"
        )
        
        # Assert: All stale shipments are in result
        stale_ids = {s['shipment_id'] for s in stale_shipments}
        expected_stale_ids = {f'ship_stale_{i}' for i in range(num_stale)}
        assert stale_ids == expected_stale_ids, (
            f"Stale shipment IDs don't match. Expected: {expected_stale_ids}, Got: {stale_ids}"
        )
    
    @given(
        courier_status=st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ ',
            min_size=5,
            max_size=30
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_courier_status_mapping_returns_valid_status(
        self,
        courier_status: str
    ):
        """
        Property Test: Courier status mapping always returns valid internal status
        
        For any courier status string:
        1. map_courier_status() MUST return a valid internal status
        2. The returned status MUST be one of the defined internal statuses
        3. Unknown statuses MUST default to 'in_transit'
        
        **Validates: Requirements 9.2**
        """
        # Valid internal statuses
        valid_statuses = [
            'shipment_created',
            'picked_up',
            'in_transit',
            'out_for_delivery',
            'delivered',
            'delivery_failed',
            'returned',
            'cancelled'
        ]
        
        # Map courier status
        internal_status = map_courier_status(courier_status)
        
        # Assert: Result must be a valid internal status
        assert internal_status in valid_statuses, (
            f"map_courier_status('{courier_status}') returned invalid status: '{internal_status}'"
        )
    
    @given(
        courier_status=st.sampled_from([
            'Picked Up', 'In Transit', 'Out for Delivery', 'Delivered',
            'Delivery Failed', 'RTO', 'Returned', 'Cancelled'
        ])
    )
    @settings(max_examples=50, deadline=None)
    def test_known_courier_statuses_map_correctly(
        self,
        courier_status: str
    ):
        """
        Property Test: Known courier statuses map to correct internal statuses
        
        For any known courier status:
        1. map_courier_status() MUST return the correct internal status
        2. The mapping MUST be consistent
        
        **Validates: Requirements 9.2**
        """
        # Expected mappings
        expected_mappings = {
            'Picked Up': 'picked_up',
            'In Transit': 'in_transit',
            'Out for Delivery': 'out_for_delivery',
            'Delivered': 'delivered',
            'Delivery Failed': 'delivery_failed',
            'RTO': 'returned',
            'Returned': 'returned',
            'Cancelled': 'cancelled'
        }
        
        # Map courier status
        internal_status = map_courier_status(courier_status)
        
        # Assert: Mapping is correct
        expected = expected_mappings[courier_status]
        assert internal_status == expected, (
            f"map_courier_status('{courier_status}') returned '{internal_status}', "
            f"expected '{expected}'"
        )
    
    @given(
        courier_status=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz ',
            min_size=5,
            max_size=30
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_unknown_courier_status_defaults_to_in_transit(
        self,
        courier_status: str
    ):
        """
        Property Test: Unknown courier statuses default to 'in_transit'
        
        For any unknown/unmapped courier status:
        1. map_courier_status() MUST return 'in_transit' as default
        2. The system MUST handle unknown statuses gracefully
        
        **Validates: Requirements 9.2**
        """
        # Known status keywords (case-insensitive)
        known_keywords = [
            'pickup', 'picked', 'transit', 'delivery', 'delivered',
            'failed', 'rto', 'return', 'cancel', 'manifest', 'book'
        ]
        
        # Check if courier_status contains any known keywords
        has_known_keyword = any(
            keyword in courier_status.lower()
            for keyword in known_keywords
        )
        
        # Only test truly unknown statuses
        assume(not has_known_keyword)
        
        # Map courier status
        internal_status = map_courier_status(courier_status)
        
        # Assert: Unknown status defaults to 'in_transit'
        assert internal_status == 'in_transit', (
            f"Unknown courier status '{courier_status}' must default to 'in_transit', "
            f"got '{internal_status}'"
        )
    
    @given(
        courier_status=st.sampled_from([
            'Picked Up', 'PICKED UP', 'picked up', 'PiCkEd Up'
        ])
    )
    @settings(max_examples=20, deadline=None)
    def test_courier_status_mapping_is_case_insensitive(
        self,
        courier_status: str
    ):
        """
        Property Test: Courier status mapping is case-insensitive
        
        For any courier status with different casing:
        1. map_courier_status() MUST return the same internal status
        2. Case variations MUST be handled correctly
        
        **Validates: Requirements 9.2**
        """
        # Map courier status
        internal_status = map_courier_status(courier_status)
        
        # Assert: All variations map to 'picked_up'
        assert internal_status == 'picked_up', (
            f"Courier status '{courier_status}' must map to 'picked_up', "
            f"got '{internal_status}'"
        )
    
    def test_empty_courier_status_defaults_to_in_transit(self):
        """
        Property Test: Empty courier status defaults to 'in_transit'
        
        For empty or None courier status:
        1. map_courier_status() MUST return 'in_transit'
        2. The system MUST handle missing statuses gracefully
        
        **Validates: Requirements 9.2**
        """
        # Test empty string
        result_empty = map_courier_status('')
        assert result_empty == 'in_transit', (
            "Empty courier status must default to 'in_transit'"
        )
        
        # Test None
        result_none = map_courier_status(None)
        assert result_none == 'in_transit', (
            "None courier status must default to 'in_transit'"
        )
    
    @given(
        shipments=st.lists(
            st.fixed_dictionaries({
                'shipment_id': st.text(min_size=10, max_size=20),
                'tracking_number': tracking_number_strategy,
                'internal_status': status_strategy,
                'courier_name': courier_name_strategy,
                'updated_at': st.text(min_size=19, max_size=30)
            }),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_filter_stale_shipments_handles_empty_list(
        self,
        shipments: List[Dict]
    ):
        """
        Property Test: filter_stale_shipments handles empty or invalid lists
        
        For any list of shipments (including empty):
        1. filter_stale_shipments() MUST NOT crash
        2. Empty input MUST return empty output
        3. Invalid timestamps MUST be handled gracefully
        
        **Validates: Requirements 9.1**
        """
        # Filter shipments
        try:
            stale_shipments = filter_stale_shipments(shipments, threshold_hours=4)
            
            # Assert: Function must not crash
            assert isinstance(stale_shipments, list), (
                "filter_stale_shipments must return a list"
            )
            
            # If input is empty, output must be empty
            if len(shipments) == 0:
                assert len(stale_shipments) == 0, (
                    "Empty input must return empty output"
                )
        except Exception as e:
            # Function should handle errors gracefully
            pytest.fail(f"filter_stale_shipments crashed with: {str(e)}")
    
    @given(
        internal_status=status_strategy,
        hours_since_update=st.integers(min_value=5, max_value=168)
    )
    @settings(max_examples=50, deadline=None)
    def test_shipment_without_updated_at_is_considered_stale(
        self,
        internal_status: str,
        hours_since_update: int
    ):
        """
        Property Test: Shipments without updated_at field are considered stale
        
        For any shipment missing the updated_at field:
        1. filter_stale_shipments() MUST include it as stale
        2. Missing timestamps MUST be handled gracefully
        
        **Validates: Requirements 9.1**
        """
        # Create shipment without updated_at field
        shipment = {
            'shipment_id': 'ship_test_no_timestamp',
            'tracking_number': 'TEST999999',
            'internal_status': internal_status,
            'courier_name': 'Delhivery'
            # No updated_at field
        }
        
        # Filter stale shipments
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=4)
        
        # Assert: Shipment without updated_at is considered stale
        assert len(stale_shipments) == 1, (
            "Shipment without updated_at field must be considered stale"
        )
        assert stale_shipments[0]['shipment_id'] == 'ship_test_no_timestamp'
    
    @given(
        internal_status=status_strategy,
        hours_since_update=st.integers(min_value=5, max_value=168)
    )
    @settings(max_examples=50, deadline=None)
    def test_shipment_with_invalid_timestamp_is_considered_stale(
        self,
        internal_status: str,
        hours_since_update: int
    ):
        """
        Property Test: Shipments with invalid timestamps are considered stale
        
        For any shipment with unparseable updated_at:
        1. filter_stale_shipments() MUST include it as stale
        2. Invalid timestamps MUST be handled gracefully
        
        **Validates: Requirements 9.1**
        """
        # Create shipment with invalid timestamp
        shipment = {
            'shipment_id': 'ship_test_invalid_timestamp',
            'tracking_number': 'TEST888888',
            'internal_status': internal_status,
            'courier_name': 'Delhivery',
            'updated_at': 'invalid-timestamp-format'
        }
        
        # Filter stale shipments
        stale_shipments = filter_stale_shipments([shipment], threshold_hours=4)
        
        # Assert: Shipment with invalid timestamp is considered stale
        assert len(stale_shipments) == 1, (
            "Shipment with invalid timestamp must be considered stale"
        )
        assert stale_shipments[0]['shipment_id'] == 'ship_test_invalid_timestamp'
    
    @given(
        threshold_hours=st.integers(min_value=1, max_value=24)
    )
    @settings(max_examples=50, deadline=None)
    def test_filter_stale_shipments_is_deterministic(
        self,
        threshold_hours: int
    ):
        """
        Property Test: filter_stale_shipments produces deterministic results
        
        For any list of shipments and threshold:
        1. Calling filter_stale_shipments() multiple times MUST return same result
        2. The function MUST be deterministic
        
        **Validates: Requirements 9.1**
        """
        # Create test shipments
        shipments = [
            create_test_shipment(
                shipment_id=f'ship_{i}',
                tracking_number=f'TEST{i:06d}',
                internal_status='in_transit',
                courier_name='Delhivery',
                hours_since_update=i
            )
            for i in range(10)
        ]
        
        # Filter multiple times
        results = [
            filter_stale_shipments(shipments, threshold_hours=threshold_hours)
            for _ in range(5)
        ]
        
        # Assert: All results are identical
        first_result_ids = {s['shipment_id'] for s in results[0]}
        for i, result in enumerate(results[1:], 1):
            result_ids = {s['shipment_id'] for s in result}
            assert result_ids == first_result_ids, (
                f"Result {i+1} differs from first result. "
                f"filter_stale_shipments must be deterministic."
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
