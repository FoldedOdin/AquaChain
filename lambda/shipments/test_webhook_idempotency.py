"""
Property-based tests for webhook idempotency
Feature: shipment-tracking-automation, Property 2: Webhook Idempotency
Validates: Requirements 2.6

This test verifies that webhook processing is idempotent:
- Duplicate webhooks are detected and skipped
- Event IDs are deterministic based on tracking_number + timestamp + status
- Processing the same webhook multiple times has no additional effect
- Timeline and webhook_events arrays contain no duplicates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List


def generate_event_id(tracking_number: str, timestamp: str, status: str) -> str:
    """
    Generate deterministic event_id from tracking_number + timestamp + status.
    Used for idempotency checking.
    
    Requirements: 2.6
    """
    # Create deterministic hash from key components
    event_key = f"{tracking_number}|{timestamp}|{status}"
    event_hash = hashlib.sha256(event_key.encode()).hexdigest()[:16]
    return f"evt_{event_hash}"


def is_duplicate_webhook(shipment: Dict, event_id: str) -> bool:
    """
    Check if event_id exists in webhook_events array.
    Returns True if duplicate detected.
    
    Requirements: 2.6
    """
    webhook_events = shipment.get('webhook_events', [])
    
    if not webhook_events:
        return False
    
    # Check if event_id already exists
    for event in webhook_events:
        if event.get('event_id') == event_id:
            return True
    
    return False


def simulate_webhook_processing(
    shipment: Dict,
    tracking_number: str,
    timestamp: str,
    status: str,
    location: str = "Test Location",
    description: str = "Test update"
) -> Dict:
    """
    Simulate processing a webhook event.
    Returns updated shipment with new timeline entry and webhook event.
    
    This simulates the update_shipment() function behavior.
    """
    # Generate event_id
    event_id = generate_event_id(tracking_number, timestamp, status)
    
    # Check for duplicate
    if is_duplicate_webhook(shipment, event_id):
        # Return shipment unchanged
        return {
            'shipment': shipment,
            'processed': False,
            'reason': 'duplicate',
            'event_id': event_id
        }
    
    # Create timeline entry
    timeline_entry = {
        'status': status,
        'timestamp': timestamp,
        'location': location,
        'description': description
    }
    
    # Create webhook event entry
    webhook_event = {
        'event_id': event_id,
        'received_at': datetime.utcnow().isoformat(),
        'courier_status': status,
        'raw_payload': json.dumps({'tracking_number': tracking_number, 'status': status})
    }
    
    # Update shipment (simulate DynamoDB update)
    updated_shipment = shipment.copy()
    
    # Append to timeline
    if 'timeline' not in updated_shipment:
        updated_shipment['timeline'] = []
    updated_shipment['timeline'].append(timeline_entry)
    
    # Append to webhook_events
    if 'webhook_events' not in updated_shipment:
        updated_shipment['webhook_events'] = []
    updated_shipment['webhook_events'].append(webhook_event)
    
    # Update status and timestamp
    updated_shipment['internal_status'] = status
    updated_shipment['updated_at'] = datetime.utcnow().isoformat()
    
    return {
        'shipment': updated_shipment,
        'processed': True,
        'reason': 'new_event',
        'event_id': event_id
    }


# Hypothesis strategies for generating test data
tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=10,
    max_size=20
)

status_strategy = st.sampled_from([
    'shipment_created',
    'picked_up',
    'in_transit',
    'out_for_delivery',
    'delivered',
    'delivery_failed',
    'returned',
    'cancelled'
])

timestamp_strategy = st.datetimes(
    min_value=datetime(2025, 1, 1),
    max_value=datetime(2025, 12, 31)
).map(lambda dt: dt.isoformat())

location_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    min_size=5,
    max_size=50
)

description_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    min_size=10,
    max_size=100
)


class TestWebhookIdempotency:
    """
    Property 2: Webhook Idempotency
    
    For any webhook event received multiple times with the same tracking_number,
    timestamp, and status, the system processes it exactly once and subsequent
    duplicates are ignored.
    
    This ensures:
    1. Duplicate webhooks are detected using deterministic event_id
    2. Processing the same webhook multiple times has no additional effect
    3. Timeline and webhook_events arrays contain no duplicate entries
    4. System state remains consistent regardless of duplicate webhooks
    """
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_event_id_is_deterministic(
        self,
        tracking_number: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: Event ID generation is deterministic
        
        For any tracking_number, timestamp, and status, generating the event_id
        multiple times must always produce the same result.
        
        **Validates: Requirements 2.6**
        """
        # Generate event_id multiple times
        event_ids = [
            generate_event_id(tracking_number, timestamp, status)
            for _ in range(10)
        ]
        
        # Assert: All event_ids must be identical
        assert all(eid == event_ids[0] for eid in event_ids), (
            f"Event ID generation must be deterministic. "
            f"tracking_number={tracking_number}, timestamp={timestamp}, status={status}"
        )
        
        # Assert: Event ID has correct format
        assert event_ids[0].startswith('evt_'), "Event ID must start with 'evt_'"
        assert len(event_ids[0]) == 20, "Event ID must be 20 characters (evt_ + 16 hex chars)"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy,
        location=location_strategy,
        description=description_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_duplicate_webhook_is_detected(
        self,
        tracking_number: str,
        timestamp: str,
        status: str,
        location: str,
        description: str
    ):
        """
        Property Test: Duplicate webhooks are detected
        
        For any webhook event, if the same event (same tracking_number, timestamp,
        and status) is processed twice:
        1. The first processing MUST succeed
        2. The second processing MUST be detected as duplicate
        3. The shipment MUST NOT be updated on the second processing
        
        **Validates: Requirements 2.6**
        """
        # Create initial shipment
        shipment = {
            'shipment_id': 'ship_test_001',
            'tracking_number': tracking_number,
            'internal_status': 'shipment_created',
            'timeline': [],
            'webhook_events': []
        }
        
        # Process webhook first time
        result1 = simulate_webhook_processing(
            shipment, tracking_number, timestamp, status, location, description
        )
        
        # Assert: First processing must succeed
        assert result1['processed'] is True, "First webhook processing must succeed"
        assert result1['reason'] == 'new_event', "First processing must be marked as new event"
        
        # Get updated shipment
        updated_shipment = result1['shipment']
        event_id = result1['event_id']
        
        # Assert: Timeline and webhook_events must have one entry
        assert len(updated_shipment['timeline']) == 1, "Timeline must have one entry after first processing"
        assert len(updated_shipment['webhook_events']) == 1, "webhook_events must have one entry after first processing"
        
        # Process same webhook second time
        result2 = simulate_webhook_processing(
            updated_shipment, tracking_number, timestamp, status, location, description
        )
        
        # Assert: Second processing must be detected as duplicate
        assert result2['processed'] is False, "Second webhook processing must be detected as duplicate"
        assert result2['reason'] == 'duplicate', "Second processing must be marked as duplicate"
        assert result2['event_id'] == event_id, "Event ID must be the same for duplicate webhook"
        
        # Get shipment after second processing
        final_shipment = result2['shipment']
        
        # Assert: Shipment must be unchanged after duplicate processing
        assert len(final_shipment['timeline']) == 1, "Timeline must still have one entry after duplicate"
        assert len(final_shipment['webhook_events']) == 1, "webhook_events must still have one entry after duplicate"
        assert final_shipment == updated_shipment, "Shipment must be unchanged after duplicate processing"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy,
        num_duplicates=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_duplicate_webhooks_are_all_detected(
        self,
        tracking_number: str,
        timestamp: str,
        status: str,
        num_duplicates: int
    ):
        """
        Property Test: Multiple duplicate webhooks are all detected
        
        For any webhook event, if the same event is processed N times:
        1. Only the first processing MUST succeed
        2. All subsequent N-1 processings MUST be detected as duplicates
        3. The shipment MUST have exactly one timeline entry and one webhook event
        
        **Validates: Requirements 2.6**
        """
        # Create initial shipment
        shipment = {
            'shipment_id': 'ship_test_002',
            'tracking_number': tracking_number,
            'internal_status': 'shipment_created',
            'timeline': [],
            'webhook_events': []
        }
        
        # Process webhook multiple times
        results = []
        current_shipment = shipment
        
        for i in range(num_duplicates):
            result = simulate_webhook_processing(
                current_shipment, tracking_number, timestamp, status
            )
            results.append(result)
            current_shipment = result['shipment']
        
        # Assert: Only first processing succeeded
        assert results[0]['processed'] is True, "First processing must succeed"
        assert results[0]['reason'] == 'new_event', "First processing must be new event"
        
        # Assert: All subsequent processings were detected as duplicates
        for i in range(1, num_duplicates):
            assert results[i]['processed'] is False, f"Processing {i+1} must be detected as duplicate"
            assert results[i]['reason'] == 'duplicate', f"Processing {i+1} must be marked as duplicate"
        
        # Assert: All event_ids are the same
        event_ids = [r['event_id'] for r in results]
        assert all(eid == event_ids[0] for eid in event_ids), "All event IDs must be identical"
        
        # Assert: Final shipment has exactly one entry
        final_shipment = results[-1]['shipment']
        assert len(final_shipment['timeline']) == 1, "Timeline must have exactly one entry"
        assert len(final_shipment['webhook_events']) == 1, "webhook_events must have exactly one entry"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status1=status_strategy,
        status2=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_different_status_creates_different_event_id(
        self,
        tracking_number: str,
        timestamp: str,
        status1: str,
        status2: str
    ):
        """
        Property Test: Different status creates different event ID
        
        For any tracking_number and timestamp, if two webhooks have different
        statuses, they must have different event IDs and both must be processed.
        
        **Validates: Requirements 2.6**
        """
        # Ensure statuses are different
        assume(status1 != status2)
        
        # Generate event IDs
        event_id1 = generate_event_id(tracking_number, timestamp, status1)
        event_id2 = generate_event_id(tracking_number, timestamp, status2)
        
        # Assert: Event IDs must be different
        assert event_id1 != event_id2, (
            f"Different statuses must produce different event IDs. "
            f"status1={status1}, status2={status2}"
        )
        
        # Create initial shipment
        shipment = {
            'shipment_id': 'ship_test_003',
            'tracking_number': tracking_number,
            'internal_status': 'shipment_created',
            'timeline': [],
            'webhook_events': []
        }
        
        # Process first webhook
        result1 = simulate_webhook_processing(shipment, tracking_number, timestamp, status1)
        assert result1['processed'] is True, "First webhook must be processed"
        
        # Process second webhook with different status
        result2 = simulate_webhook_processing(
            result1['shipment'], tracking_number, timestamp, status2
        )
        assert result2['processed'] is True, "Second webhook with different status must be processed"
        
        # Assert: Both events are in the shipment
        final_shipment = result2['shipment']
        assert len(final_shipment['timeline']) == 2, "Timeline must have two entries"
        assert len(final_shipment['webhook_events']) == 2, "webhook_events must have two entries"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp1=timestamp_strategy,
        timestamp2=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_different_timestamp_creates_different_event_id(
        self,
        tracking_number: str,
        timestamp1: str,
        timestamp2: str,
        status: str
    ):
        """
        Property Test: Different timestamp creates different event ID
        
        For any tracking_number and status, if two webhooks have different
        timestamps, they must have different event IDs and both must be processed.
        
        **Validates: Requirements 2.6**
        """
        # Ensure timestamps are different
        assume(timestamp1 != timestamp2)
        
        # Generate event IDs
        event_id1 = generate_event_id(tracking_number, timestamp1, status)
        event_id2 = generate_event_id(tracking_number, timestamp2, status)
        
        # Assert: Event IDs must be different
        assert event_id1 != event_id2, (
            f"Different timestamps must produce different event IDs. "
            f"timestamp1={timestamp1}, timestamp2={timestamp2}"
        )
        
        # Create initial shipment
        shipment = {
            'shipment_id': 'ship_test_004',
            'tracking_number': tracking_number,
            'internal_status': 'shipment_created',
            'timeline': [],
            'webhook_events': []
        }
        
        # Process first webhook
        result1 = simulate_webhook_processing(shipment, tracking_number, timestamp1, status)
        assert result1['processed'] is True, "First webhook must be processed"
        
        # Process second webhook with different timestamp
        result2 = simulate_webhook_processing(
            result1['shipment'], tracking_number, timestamp2, status
        )
        assert result2['processed'] is True, "Second webhook with different timestamp must be processed"
        
        # Assert: Both events are in the shipment
        final_shipment = result2['shipment']
        assert len(final_shipment['timeline']) == 2, "Timeline must have two entries"
        assert len(final_shipment['webhook_events']) == 2, "webhook_events must have two entries"
    
    @given(
        tracking_number1=tracking_number_strategy,
        tracking_number2=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_different_tracking_number_creates_different_event_id(
        self,
        tracking_number1: str,
        tracking_number2: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: Different tracking number creates different event ID
        
        For any timestamp and status, if two webhooks have different tracking
        numbers, they must have different event IDs.
        
        **Validates: Requirements 2.6**
        """
        # Ensure tracking numbers are different
        assume(tracking_number1 != tracking_number2)
        
        # Generate event IDs
        event_id1 = generate_event_id(tracking_number1, timestamp, status)
        event_id2 = generate_event_id(tracking_number2, timestamp, status)
        
        # Assert: Event IDs must be different
        assert event_id1 != event_id2, (
            f"Different tracking numbers must produce different event IDs. "
            f"tracking_number1={tracking_number1}, tracking_number2={tracking_number2}"
        )
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_is_duplicate_webhook_with_empty_events(
        self,
        tracking_number: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: is_duplicate_webhook returns False for empty webhook_events
        
        For any event_id, if the shipment has no webhook_events:
        1. is_duplicate_webhook() MUST return False
        2. The webhook MUST be processed as a new event
        
        **Validates: Requirements 2.6**
        """
        # Create shipment with empty webhook_events
        shipment = {
            'shipment_id': 'ship_test_005',
            'tracking_number': tracking_number,
            'webhook_events': []
        }
        
        # Generate event_id
        event_id = generate_event_id(tracking_number, timestamp, status)
        
        # Check for duplicate
        result = is_duplicate_webhook(shipment, event_id)
        
        # Assert: Must return False for empty webhook_events
        assert result is False, "is_duplicate_webhook must return False for empty webhook_events"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_is_duplicate_webhook_with_missing_events(
        self,
        tracking_number: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: is_duplicate_webhook handles missing webhook_events field
        
        For any event_id, if the shipment doesn't have a webhook_events field:
        1. is_duplicate_webhook() MUST return False
        2. The webhook MUST be processed as a new event
        
        **Validates: Requirements 2.6**
        """
        # Create shipment without webhook_events field
        shipment = {
            'shipment_id': 'ship_test_006',
            'tracking_number': tracking_number
        }
        
        # Generate event_id
        event_id = generate_event_id(tracking_number, timestamp, status)
        
        # Check for duplicate
        result = is_duplicate_webhook(shipment, event_id)
        
        # Assert: Must return False for missing webhook_events
        assert result is False, "is_duplicate_webhook must return False for missing webhook_events field"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamps=st.lists(
            timestamp_strategy,
            min_size=2,
            max_size=10,
            unique=True
        ),
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_unique_webhooks_are_all_processed(
        self,
        tracking_number: str,
        timestamps: List[str],
        status: str
    ):
        """
        Property Test: Multiple unique webhooks are all processed
        
        For any sequence of unique webhook events (different timestamps):
        1. All webhooks MUST be processed
        2. None should be detected as duplicates
        3. Timeline and webhook_events must have N entries for N unique webhooks
        
        **Validates: Requirements 2.6**
        """
        # Create initial shipment
        shipment = {
            'shipment_id': 'ship_test_007',
            'tracking_number': tracking_number,
            'internal_status': 'shipment_created',
            'timeline': [],
            'webhook_events': []
        }
        
        # Process all unique webhooks
        current_shipment = shipment
        results = []
        
        for timestamp in timestamps:
            result = simulate_webhook_processing(
                current_shipment, tracking_number, timestamp, status
            )
            results.append(result)
            current_shipment = result['shipment']
        
        # Assert: All webhooks were processed
        for i, result in enumerate(results):
            assert result['processed'] is True, f"Webhook {i+1} must be processed"
            assert result['reason'] == 'new_event', f"Webhook {i+1} must be marked as new event"
        
        # Assert: All event_ids are unique
        event_ids = [r['event_id'] for r in results]
        assert len(event_ids) == len(set(event_ids)), "All event IDs must be unique"
        
        # Assert: Final shipment has N entries
        final_shipment = results[-1]['shipment']
        assert len(final_shipment['timeline']) == len(timestamps), (
            f"Timeline must have {len(timestamps)} entries"
        )
        assert len(final_shipment['webhook_events']) == len(timestamps), (
            f"webhook_events must have {len(timestamps)} entries"
        )
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy,
        existing_events=st.lists(
            st.fixed_dictionaries({
                'event_id': st.text(alphabet='abcdef0123456789', min_size=20, max_size=20),
                'received_at': timestamp_strategy,
                'courier_status': status_strategy
            }),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_is_duplicate_webhook_with_existing_events(
        self,
        tracking_number: str,
        timestamp: str,
        status: str,
        existing_events: List[Dict]
    ):
        """
        Property Test: is_duplicate_webhook correctly checks existing events
        
        For any shipment with existing webhook_events:
        1. If event_id matches an existing event, MUST return True
        2. If event_id doesn't match any existing event, MUST return False
        
        **Validates: Requirements 2.6**
        """
        # Generate event_id for new webhook
        new_event_id = generate_event_id(tracking_number, timestamp, status)
        
        # Create shipment with existing events
        shipment = {
            'shipment_id': 'ship_test_008',
            'tracking_number': tracking_number,
            'webhook_events': existing_events
        }
        
        # Check if new event_id exists in existing events
        existing_event_ids = [e['event_id'] for e in existing_events]
        should_be_duplicate = new_event_id in existing_event_ids
        
        # Check for duplicate
        result = is_duplicate_webhook(shipment, new_event_id)
        
        # Assert: Result must match expectation
        if should_be_duplicate:
            assert result is True, f"Event ID {new_event_id} exists in existing events, must be detected as duplicate"
        else:
            assert result is False, f"Event ID {new_event_id} doesn't exist in existing events, must not be detected as duplicate"
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_event_id_format_is_consistent(
        self,
        tracking_number: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: Event ID format is consistent
        
        For any tracking_number, timestamp, and status:
        1. Event ID MUST start with 'evt_'
        2. Event ID MUST be exactly 20 characters long
        3. Event ID MUST contain only lowercase hex characters after prefix
        
        **Validates: Requirements 2.6**
        """
        # Generate event_id
        event_id = generate_event_id(tracking_number, timestamp, status)
        
        # Assert: Format checks
        assert event_id.startswith('evt_'), "Event ID must start with 'evt_'"
        assert len(event_id) == 20, f"Event ID must be 20 characters, got {len(event_id)}"
        
        # Extract hash part (after 'evt_')
        hash_part = event_id[4:]
        assert len(hash_part) == 16, "Hash part must be 16 characters"
        assert all(c in '0123456789abcdef' for c in hash_part), (
            "Hash part must contain only lowercase hex characters"
        )
    
    @given(
        tracking_number=tracking_number_strategy,
        timestamp=timestamp_strategy,
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_webhook_processing_preserves_existing_data(
        self,
        tracking_number: str,
        timestamp: str,
        status: str
    ):
        """
        Property Test: Webhook processing preserves existing shipment data
        
        For any webhook event, processing it must:
        1. Preserve all existing timeline entries
        2. Preserve all existing webhook_events entries
        3. Only append new entries, never modify or remove existing ones
        
        **Validates: Requirements 2.6**
        """
        # Create shipment with existing data
        existing_timeline = [
            {'status': 'shipment_created', 'timestamp': '2025-01-01T00:00:00', 'location': 'Warehouse'},
            {'status': 'picked_up', 'timestamp': '2025-01-02T00:00:00', 'location': 'Hub'}
        ]
        existing_events = [
            {'event_id': 'evt_existing_001', 'received_at': '2025-01-01T00:00:00', 'courier_status': 'CREATED'},
            {'event_id': 'evt_existing_002', 'received_at': '2025-01-02T00:00:00', 'courier_status': 'PICKED'}
        ]
        
        shipment = {
            'shipment_id': 'ship_test_009',
            'tracking_number': tracking_number,
            'internal_status': 'picked_up',
            'timeline': existing_timeline.copy(),
            'webhook_events': existing_events.copy()
        }
        
        # Process new webhook
        result = simulate_webhook_processing(shipment, tracking_number, timestamp, status)
        
        # Assert: Processing succeeded
        assert result['processed'] is True, "Webhook processing must succeed"
        
        # Get updated shipment
        updated_shipment = result['shipment']
        
        # Assert: Existing timeline entries are preserved
        assert len(updated_shipment['timeline']) == len(existing_timeline) + 1, (
            "Timeline must have one more entry"
        )
        for i, existing_entry in enumerate(existing_timeline):
            assert updated_shipment['timeline'][i] == existing_entry, (
                f"Existing timeline entry {i} must be preserved"
            )
        
        # Assert: Existing webhook_events entries are preserved
        assert len(updated_shipment['webhook_events']) == len(existing_events) + 1, (
            "webhook_events must have one more entry"
        )
        for i, existing_event in enumerate(existing_events):
            assert updated_shipment['webhook_events'][i] == existing_event, (
                f"Existing webhook_events entry {i} must be preserved"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
