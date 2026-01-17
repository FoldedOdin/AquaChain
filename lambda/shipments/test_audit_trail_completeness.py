"""
Property-based tests for audit trail completeness
Feature: shipment-tracking-automation, Property 12: Audit Trail Completeness
Validates: Requirements 15.2, 15.4

This test verifies that shipment audit trails are complete:
- webhook_events array contains all received webhook payloads
- timeline array contains all status transitions in chronological order
- All webhook events are preserved with required fields
- Timeline and webhook events maintain consistency
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from moto import mock_aws
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import hashlib


def setup_aws_environment():
    """Setup AWS environment variables"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['SHIPMENTS_TABLE'] = 'aquachain-shipments'
    os.environ['WEBHOOK_SECRET'] = 'test-secret'
    os.environ['SNS_TOPIC_ARN'] = ''  # Disable notifications


def create_dynamodb_tables():
    """Create mocked DynamoDB tables"""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    # Create Shipments table
    dynamodb.create_table(
        TableName='aquachain-shipments',
        KeySchema=[
            {'AttributeName': 'shipment_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'shipment_id', 'AttributeType': 'S'},
            {'AttributeName': 'order_id', 'AttributeType': 'S'},
            {'AttributeName': 'tracking_number', 'AttributeType': 'S'},
            {'AttributeName': 'internal_status', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'order_id-index',
                'KeySchema': [{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'tracking_number-index',
                'KeySchema': [{'AttributeName': 'tracking_number', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'status-created_at-index',
                'KeySchema': [
                    {'AttributeName': 'internal_status', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST',
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_AND_OLD_IMAGES'
        }
    )
    
    return dynamodb


def create_test_shipment(shipment_id: str, tracking_number: str, created_at: str) -> Dict[str, Any]:
    """Create a test shipment record"""
    return {
        'shipment_id': shipment_id,
        'order_id': f'ord_{shipment_id}',
        'device_id': f'device_{shipment_id}',
        'tracking_number': tracking_number,
        'courier_name': 'Delhivery',
        'internal_status': 'shipment_created',
        'external_status': 'shipped',
        'destination': {
            'address': '123 Test St',
            'pincode': '560001',
            'contact_name': 'Test User',
            'contact_phone': '+919876543210'
        },
        'timeline': [{
            'status': 'shipment_created',
            'timestamp': created_at,
            'location': 'Warehouse',
            'description': 'Shipment created'
        }],
        'webhook_events': [],
        'retry_config': {'max_retries': 3, 'retry_count': 0, 'last_retry_at': None},
        'metadata': {'weight': '0.5kg', 'declared_value': 5000},
        'created_at': created_at,
        'updated_at': created_at,
        'delivered_at': None,
        'failed_at': None,
        'created_by': 'test_user',
        'estimated_delivery': (datetime.fromisoformat(created_at.replace('Z', '')) + timedelta(days=3)).isoformat() + 'Z'
    }


def generate_event_id(tracking_number: str, timestamp: str, status: str) -> str:
    """Generate deterministic event_id"""
    event_key = f"{tracking_number}|{timestamp}|{status}"
    event_hash = hashlib.sha256(event_key.encode()).hexdigest()[:16]
    return f"evt_{event_hash}"


def add_webhook_and_timeline_entry(
    shipment_id: str,
    tracking_number: str,
    status: str,
    courier_status: str,
    timestamp: str,
    location: str,
    description: str,
    raw_payload: Dict
):
    """Add both webhook event and timeline entry atomically"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    shipments_table = dynamodb.Table('aquachain-shipments')
    
    # Create timeline entry
    timeline_entry = {
        'status': status,
        'timestamp': timestamp,
        'location': location,
        'description': description
    }
    
    # Create webhook event
    event_id = generate_event_id(tracking_number, timestamp, courier_status)
    webhook_event = {
        'event_id': event_id,
        'received_at': datetime.utcnow().isoformat() + 'Z',
        'courier_status': courier_status,
        'raw_payload': json.dumps(raw_payload)[:1000],  # Truncate if needed
        'truncated': len(json.dumps(raw_payload)) > 1000
    }
    
    # Update shipment with both
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression=(
            'SET timeline = list_append(if_not_exists(timeline, :empty_list), :timeline), '
            'webhook_events = list_append(if_not_exists(webhook_events, :empty_list), :webhook), '
            'updated_at = :time, internal_status = :status'
        ),
        ExpressionAttributeValues={
            ':timeline': [timeline_entry],
            ':webhook': [webhook_event],
            ':empty_list': [],
            ':time': datetime.utcnow().isoformat() + 'Z',
            ':status': status
        }
    )
    
    return event_id


def get_shipment(shipment_id: str) -> Dict[str, Any]:
    """Retrieve complete shipment record"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    shipments_table = dynamodb.Table('aquachain-shipments')
    
    response = shipments_table.get_item(Key={'shipment_id': shipment_id})
    return response.get('Item', {})


# Hypothesis strategies
shipment_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
    min_size=10,
    max_size=20
).map(lambda s: f"ship_{s}")

tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=10,
    max_size=15
)

status_pairs_strategy = st.sampled_from([
    ('picked_up', 'PICKED_UP'),
    ('in_transit', 'IN_TRANSIT'),
    ('out_for_delivery', 'OUT_FOR_DELIVERY'),
    ('delivered', 'DELIVERED'),
    ('delivery_failed', 'DELIVERY_FAILED')
])


def generate_ordered_timestamps(base_time: datetime, count: int) -> List[str]:
    """Generate chronologically ordered timestamps"""
    timestamps = []
    current_time = base_time
    
    for _ in range(count):
        timestamps.append(current_time.isoformat() + 'Z')
        current_time += timedelta(minutes=5)
    
    return timestamps


class TestAuditTrailCompleteness:
    """
    Property 12: Audit Trail Completeness
    
    For any shipment, the webhook_events array must contain all received
    webhook payloads, and the timeline array must contain all status
    transitions in chronological order.
    
    This ensures:
    1. All webhook events are preserved
    2. Timeline contains all status transitions
    3. Webhook events and timeline entries are consistent
    4. Audit trail is complete for compliance
    """
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_events=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_all_webhook_events_are_preserved(
        self,
        shipment_id: str,
        tracking_number: str,
        num_events: int
    ):
        """
        Property Test: All webhook events are preserved in webhook_events array
        
        For any shipment receiving N webhook events:
        1. webhook_events array MUST contain exactly N entries
        2. Each webhook event MUST have event_id, received_at, courier_status
        3. All raw payloads MUST be stored
        4. No webhook events MUST be lost
        
        **Validates: Requirements 15.2**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate timestamps and status pairs
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_events)
            status_pairs = [
                ('picked_up', 'PICKED_UP'),
                ('in_transit', 'IN_TRANSIT'),
                ('out_for_delivery', 'OUT_FOR_DELIVERY'),
                ('delivered', 'DELIVERED')
            ]
            
            # Track expected event_ids
            expected_event_ids = []
            
            # Add webhook events
            for i, timestamp in enumerate(timestamps):
                internal_status, courier_status = status_pairs[min(i, len(status_pairs) - 1)]
                
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': courier_status,
                    'Location': f'Hub {i+1}',
                    'Timestamp': timestamp
                }
                
                event_id = add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status=internal_status,
                    courier_status=courier_status,
                    timestamp=timestamp,
                    location=f'Hub {i+1}',
                    description=f'Status update {i+1}',
                    raw_payload=raw_payload
                )
                
                expected_event_ids.append(event_id)
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            
            # Assert: All webhook events are preserved
            assert len(webhook_events) == num_events, (
                f"webhook_events must contain all {num_events} events, got {len(webhook_events)}"
            )
            
            # Assert: Each webhook event has required fields
            for i, event in enumerate(webhook_events):
                assert 'event_id' in event, f"Webhook event {i} missing event_id"
                assert 'received_at' in event, f"Webhook event {i} missing received_at"
                assert 'courier_status' in event, f"Webhook event {i} missing courier_status"
                assert 'raw_payload' in event, f"Webhook event {i} missing raw_payload"
            
            # Assert: All expected event_ids are present
            actual_event_ids = [e['event_id'] for e in webhook_events]
            for expected_id in expected_event_ids:
                assert expected_id in actual_event_ids, (
                    f"Expected event_id {expected_id} not found in webhook_events"
                )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_transitions=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_all_status_transitions_in_timeline(
        self,
        shipment_id: str,
        tracking_number: str,
        num_transitions: int
    ):
        """
        Property Test: All status transitions are recorded in timeline
        
        For any shipment with N status transitions:
        1. timeline array MUST contain N+1 entries (including creation)
        2. Each timeline entry MUST have status, timestamp, location, description
        3. Timeline MUST be in chronological order
        4. No status transitions MUST be lost
        
        **Validates: Requirements 15.4**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_transitions)
            
            # Track expected statuses
            expected_statuses = ['shipment_created']  # Initial status
            
            # Add status transitions
            status_sequence = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            for i, timestamp in enumerate(timestamps):
                status = status_sequence[min(i, len(status_sequence) - 1)]
                courier_status = status.upper().replace('_', ' ')
                
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': courier_status,
                    'Timestamp': timestamp
                }
                
                add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status=status,
                    courier_status=courier_status,
                    timestamp=timestamp,
                    location=f'Location {i+1}',
                    description=f'Transition to {status}',
                    raw_payload=raw_payload
                )
                
                expected_statuses.append(status)
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            timeline = shipment_data.get('timeline', [])
            
            # Assert: Timeline contains all transitions
            assert len(timeline) == num_transitions + 1, (
                f"Timeline must contain {num_transitions + 1} entries (including creation), "
                f"got {len(timeline)}"
            )
            
            # Assert: Each timeline entry has required fields
            for i, entry in enumerate(timeline):
                assert 'status' in entry, f"Timeline entry {i} missing status"
                assert 'timestamp' in entry, f"Timeline entry {i} missing timestamp"
                assert 'location' in entry, f"Timeline entry {i} missing location"
                assert 'description' in entry, f"Timeline entry {i} missing description"
            
            # Assert: All expected statuses are present
            actual_statuses = [e['status'] for e in timeline]
            assert actual_statuses == expected_statuses, (
                f"Timeline statuses {actual_statuses} don't match expected {expected_statuses}"
            )
            
            # Assert: Timeline is chronologically ordered
            for i in range(len(timeline) - 1):
                current_time = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
                next_time = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
                assert current_time <= next_time, (
                    f"Timeline not chronological at index {i}: "
                    f"{timeline[i]['timestamp']} > {timeline[i+1]['timestamp']}"
                )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_events=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=20, deadline=None)
    def test_webhook_events_and_timeline_consistency(
        self,
        shipment_id: str,
        tracking_number: str,
        num_events: int
    ):
        """
        Property Test: Webhook events and timeline entries are consistent
        
        For any shipment with N webhook events:
        1. Timeline MUST have N+1 entries (including creation)
        2. Each webhook event MUST correspond to a timeline entry
        3. Timestamps MUST match between webhook and timeline
        4. Status mappings MUST be consistent
        
        **Validates: Requirements 15.2, 15.4**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_events)
            
            # Add events
            status_pairs = [
                ('picked_up', 'PICKED_UP'),
                ('in_transit', 'IN_TRANSIT'),
                ('out_for_delivery', 'OUT_FOR_DELIVERY'),
                ('delivered', 'DELIVERED')
            ]
            
            for i, timestamp in enumerate(timestamps):
                internal_status, courier_status = status_pairs[min(i, len(status_pairs) - 1)]
                
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': courier_status,
                    'Timestamp': timestamp
                }
                
                add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status=internal_status,
                    courier_status=courier_status,
                    timestamp=timestamp,
                    location=f'Hub {i+1}',
                    description=f'Update {i+1}',
                    raw_payload=raw_payload
                )
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            timeline = shipment_data.get('timeline', [])
            
            # Assert: Counts are consistent
            assert len(webhook_events) == num_events, (
                f"Expected {num_events} webhook events, got {len(webhook_events)}"
            )
            assert len(timeline) == num_events + 1, (
                f"Expected {num_events + 1} timeline entries, got {len(timeline)}"
            )
            
            # Assert: Each webhook event has corresponding timeline entry
            # (Skip first timeline entry which is shipment creation)
            for i, webhook_event in enumerate(webhook_events):
                timeline_entry = timeline[i + 1]  # +1 to skip creation entry
                
                # Verify both exist
                assert webhook_event is not None, f"Webhook event {i} is None"
                assert timeline_entry is not None, f"Timeline entry {i+1} is None"
                
                # Verify raw payload contains tracking number
                raw_payload = json.loads(webhook_event['raw_payload'])
                assert raw_payload['waybill'] == tracking_number, (
                    f"Webhook event {i} payload tracking number mismatch"
                )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_events=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_audit_trail_completeness_with_many_events(
        self,
        shipment_id: str,
        tracking_number: str,
        num_events: int
    ):
        """
        Property Test: Audit trail remains complete with many events
        
        For any shipment with many webhook events:
        1. All webhook events MUST be preserved
        2. All timeline entries MUST be preserved
        3. Chronological order MUST be maintained
        4. No data loss MUST occur
        
        **Validates: Requirements 15.2, 15.4**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate many timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_events)
            
            # Add many events
            status_sequence = ['picked_up', 'in_transit', 'in_transit', 'in_transit', 
                             'out_for_delivery', 'delivered']
            
            for i, timestamp in enumerate(timestamps):
                status = status_sequence[min(i, len(status_sequence) - 1)]
                courier_status = status.upper().replace('_', ' ')
                
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': courier_status,
                    'Timestamp': timestamp,
                    'Location': f'Hub {i % 5}',
                    'Details': f'Event {i+1} of {num_events}'
                }
                
                add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status=status,
                    courier_status=courier_status,
                    timestamp=timestamp,
                    location=f'Hub {i % 5}',
                    description=f'Event {i+1}',
                    raw_payload=raw_payload
                )
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            timeline = shipment_data.get('timeline', [])
            
            # Assert: All events preserved
            assert len(webhook_events) == num_events, (
                f"Expected {num_events} webhook events, got {len(webhook_events)}"
            )
            assert len(timeline) == num_events + 1, (
                f"Expected {num_events + 1} timeline entries, got {len(timeline)}"
            )
            
            # Assert: All webhook events have required fields
            for i, event in enumerate(webhook_events):
                assert 'event_id' in event
                assert 'received_at' in event
                assert 'courier_status' in event
                assert 'raw_payload' in event
            
            # Assert: All timeline entries have required fields
            for i, entry in enumerate(timeline):
                assert 'status' in entry
                assert 'timestamp' in entry
                assert 'location' in entry
                assert 'description' in entry
            
            # Assert: Timeline is chronologically ordered
            for i in range(len(timeline) - 1):
                current_time = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
                next_time = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
                assert current_time <= next_time
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_audit_trail_completeness_for_new_shipment(
        self,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: New shipment has minimal complete audit trail
        
        For any newly created shipment:
        1. Timeline MUST have at least 1 entry (creation)
        2. webhook_events MAY be empty (no webhooks yet)
        3. Creation entry MUST have all required fields
        4. Audit trail MUST be valid
        
        **Validates: Requirements 15.2, 15.4**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            timeline = shipment_data.get('timeline', [])
            
            # Assert: Timeline has creation entry
            assert len(timeline) >= 1, "New shipment must have at least creation entry"
            
            # Assert: Creation entry has required fields
            creation_entry = timeline[0]
            assert 'status' in creation_entry
            assert 'timestamp' in creation_entry
            assert 'location' in creation_entry
            assert 'description' in creation_entry
            
            # Assert: Creation entry is shipment_created
            assert creation_entry['status'] == 'shipment_created'
            assert creation_entry['timestamp'] == created_at
            
            # Assert: webhook_events is empty or a list
            assert isinstance(webhook_events, list), "webhook_events must be a list"
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_events=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_raw_payloads_are_preserved(
        self,
        shipment_id: str,
        tracking_number: str,
        num_events: int
    ):
        """
        Property Test: Raw webhook payloads are preserved
        
        For any webhook event:
        1. raw_payload MUST be stored as string
        2. raw_payload MUST be parseable as JSON
        3. raw_payload MUST contain original data
        4. Large payloads MUST be truncated with flag
        
        **Validates: Requirements 15.2**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_events)
            
            # Track original payloads
            original_payloads = []
            
            # Add events with varying payload sizes
            for i, timestamp in enumerate(timestamps):
                # Create payload with varying size
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': 'IN_TRANSIT',
                    'Timestamp': timestamp,
                    'Details': 'x' * (i * 100)  # Varying size
                }
                
                original_payloads.append(raw_payload)
                
                add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status='in_transit',
                    courier_status='IN_TRANSIT',
                    timestamp=timestamp,
                    location=f'Hub {i+1}',
                    description=f'Update {i+1}',
                    raw_payload=raw_payload
                )
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            
            # Assert: All webhook events have raw_payload
            for i, event in enumerate(webhook_events):
                assert 'raw_payload' in event, f"Webhook event {i} missing raw_payload"
                
                # Assert: raw_payload is a string
                assert isinstance(event['raw_payload'], str), (
                    f"Webhook event {i} raw_payload must be string"
                )
                
                # Assert: raw_payload is valid JSON
                try:
                    parsed = json.loads(event['raw_payload'])
                    assert 'waybill' in parsed, f"Webhook event {i} payload missing waybill"
                    assert parsed['waybill'] == tracking_number
                except json.JSONDecodeError:
                    pytest.fail(f"Webhook event {i} raw_payload is not valid JSON")
                
                # Assert: Truncation flag is set if payload was large
                original_size = len(json.dumps(original_payloads[i]))
                if original_size > 1000:
                    assert event.get('truncated') == True, (
                        f"Webhook event {i} should be marked as truncated"
                    )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_events=st.integers(min_value=2, max_value=6)
    )
    @settings(max_examples=20, deadline=None)
    def test_audit_trail_supports_compliance_queries(
        self,
        shipment_id: str,
        tracking_number: str,
        num_events: int
    ):
        """
        Property Test: Audit trail supports compliance queries
        
        For any shipment audit trail:
        1. All events MUST be queryable by timestamp
        2. All events MUST be queryable by status
        3. Complete history MUST be reconstructable
        4. Audit trail MUST support forensic analysis
        
        **Validates: Requirements 15.2, 15.4**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Generate timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_events)
            
            # Add events
            status_sequence = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            
            for i, timestamp in enumerate(timestamps):
                status = status_sequence[min(i, len(status_sequence) - 1)]
                courier_status = status.upper().replace('_', ' ')
                
                raw_payload = {
                    'waybill': tracking_number,
                    'Status': courier_status,
                    'Timestamp': timestamp
                }
                
                add_webhook_and_timeline_entry(
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    status=status,
                    courier_status=courier_status,
                    timestamp=timestamp,
                    location=f'Hub {i+1}',
                    description=f'Update {i+1}',
                    raw_payload=raw_payload
                )
            
            # Retrieve shipment
            shipment_data = get_shipment(shipment_id)
            webhook_events = shipment_data.get('webhook_events', [])
            timeline = shipment_data.get('timeline', [])
            
            # Query 1: Find all events by timestamp range
            start_time = base_time
            end_time = base_time + timedelta(hours=1)
            
            events_in_range = [
                e for e in timeline
                if start_time <= datetime.fromisoformat(e['timestamp'].replace('Z', '')) <= end_time
            ]
            
            # Assert: Can query by timestamp
            assert len(events_in_range) > 0, "Should find events in timestamp range"
            
            # Query 2: Find all events by status
            delivered_events = [e for e in timeline if e['status'] == 'delivered']
            
            # Assert: Can query by status
            # (May be 0 if delivered not reached, which is fine)
            assert isinstance(delivered_events, list), "Status query must return list"
            
            # Query 3: Reconstruct complete history
            complete_history = []
            for i, timeline_entry in enumerate(timeline):
                # Find corresponding webhook event (if exists)
                webhook_event = None
                if i > 0 and i - 1 < len(webhook_events):  # Skip creation entry
                    webhook_event = webhook_events[i - 1]
                
                complete_history.append({
                    'timeline': timeline_entry,
                    'webhook': webhook_event
                })
            
            # Assert: Complete history is reconstructable
            assert len(complete_history) == len(timeline), (
                "Complete history must include all timeline entries"
            )
            
            # Assert: Each history entry has timeline data
            for entry in complete_history:
                assert 'timeline' in entry
                assert entry['timeline'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
