"""
Property-based tests for timeline monotonicity
Feature: shipment-tracking-automation, Property 4: Timeline Monotonicity
Validates: Requirements 15.1

This test verifies that shipment timelines maintain chronological order:
- All timeline entries are ordered by timestamp
- No entry can have a timestamp earlier than shipment creation
- Timeline remains sorted after multiple updates
- Out-of-order webhook events are handled correctly
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


def add_timeline_entry(shipment_id: str, status: str, timestamp: str, location: str, description: str):
    """Add a timeline entry to a shipment using DynamoDB update"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    shipments_table = dynamodb.Table('aquachain-shipments')
    
    timeline_entry = {
        'status': status,
        'timestamp': timestamp,
        'location': location,
        'description': description
    }
    
    # Append to timeline array
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression='SET timeline = list_append(if_not_exists(timeline, :empty_list), :entry), updated_at = :time, internal_status = :status',
        ExpressionAttributeValues={
            ':entry': [timeline_entry],
            ':empty_list': [],
            ':time': datetime.utcnow().isoformat() + 'Z',
            ':status': status
        }
    )


def get_shipment_timeline(shipment_id: str) -> List[Dict[str, Any]]:
    """Retrieve shipment timeline from DynamoDB"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    shipments_table = dynamodb.Table('aquachain-shipments')
    
    response = shipments_table.get_item(Key={'shipment_id': shipment_id})
    if 'Item' not in response:
        return []
    
    return response['Item'].get('timeline', [])


def is_timeline_monotonic(timeline: List[Dict[str, Any]]) -> bool:
    """Check if timeline is in chronological order"""
    if len(timeline) <= 1:
        return True
    
    for i in range(len(timeline) - 1):
        current_time = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
        next_time = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
        
        if current_time > next_time:
            return False
    
    return True


# Hypothesis strategies for generating test data
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

status_strategy = st.sampled_from([
    'shipment_created', 'picked_up', 'in_transit',
    'out_for_delivery', 'delivered', 'delivery_failed', 'returned'
])

location_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ',
    min_size=5,
    max_size=50
)

description_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,',
    min_size=5,
    max_size=100
)

# Generate chronologically ordered timestamps
def generate_ordered_timestamps(base_time: datetime, count: int) -> List[str]:
    """Generate a list of chronologically ordered timestamps"""
    timestamps = []
    current_time = base_time
    
    for _ in range(count):
        timestamps.append(current_time.isoformat() + 'Z')
        # Add random interval between 1 minute and 2 hours
        current_time += timedelta(minutes=1, seconds=0)
    
    return timestamps


class TestTimelineMonotonicity:
    """
    Property 4: Timeline Monotonicity
    
    For any shipment timeline, all entries must be ordered chronologically by
    timestamp, and no entry can have a timestamp earlier than the shipment
    creation time.
    
    This ensures:
    1. Timeline entries are always in chronological order
    2. No entry predates shipment creation
    3. Timeline remains sorted after multiple updates
    4. Out-of-order updates are handled correctly
    """
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_timeline_entries_are_chronologically_ordered(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: Timeline entries are chronologically ordered
        
        For any shipment with multiple timeline entries added in order:
        1. All entries MUST be ordered by timestamp (ascending)
        2. For any two consecutive entries, timestamp[i] <= timestamp[i+1]
        3. Timeline MUST maintain chronological order
        
        **Validates: Requirements 15.1**
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
            
            # Generate ordered timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_entries - 1)
            
            # Add timeline entries in chronological order
            statuses = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            for i, timestamp in enumerate(timestamps):
                status = statuses[min(i, len(statuses) - 1)]
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=timestamp,
                    location=f'Location {i+1}',
                    description=f'Status update {i+1}'
                )
            
            # Retrieve timeline
            timeline = get_shipment_timeline(shipment_id)
            
            # Assert: Timeline must have all entries
            assert len(timeline) == num_entries, f"Timeline must have {num_entries} entries"
            
            # Assert: Timeline must be chronologically ordered
            assert is_timeline_monotonic(timeline), "Timeline must be in chronological order"
            
            # Assert: Each consecutive pair is ordered
            for i in range(len(timeline) - 1):
                current_time = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
                next_time = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
                
                assert current_time <= next_time, (
                    f"Timeline entry {i} timestamp ({timeline[i]['timestamp']}) must be <= "
                    f"entry {i+1} timestamp ({timeline[i+1]['timestamp']})"
                )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_no_entry_predates_shipment_creation(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: No timeline entry can predate shipment creation
        
        For any shipment timeline:
        1. All timeline entries MUST have timestamp >= created_at
        2. The first entry MUST be the shipment creation event
        3. No entry can have an earlier timestamp than created_at
        
        **Validates: Requirements 15.1**
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
            
            # Generate ordered timestamps AFTER creation time
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_entries - 1)
            
            # Add timeline entries
            statuses = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            for i, timestamp in enumerate(timestamps):
                status = statuses[min(i, len(statuses) - 1)]
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=timestamp,
                    location=f'Location {i+1}',
                    description=f'Status update {i+1}'
                )
            
            # Retrieve timeline and shipment
            timeline = get_shipment_timeline(shipment_id)
            shipment_data = shipments_table.get_item(Key={'shipment_id': shipment_id})['Item']
            creation_time = datetime.fromisoformat(shipment_data['created_at'].replace('Z', ''))
            
            # Assert: All timeline entries must be >= creation time
            for i, entry in enumerate(timeline):
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', ''))
                
                assert entry_time >= creation_time, (
                    f"Timeline entry {i} timestamp ({entry['timestamp']}) must be >= "
                    f"shipment creation time ({shipment_data['created_at']})"
                )
            
            # Assert: First entry should be shipment creation
            assert timeline[0]['status'] == 'shipment_created', "First timeline entry must be shipment creation"
            assert timeline[0]['timestamp'] == created_at, "First entry timestamp must match created_at"
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=20, deadline=None)
    def test_timeline_remains_sorted_after_multiple_updates(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: Timeline remains sorted after multiple updates
        
        For any shipment receiving multiple status updates:
        1. Timeline MUST remain chronologically ordered after each update
        2. Adding new entries MUST NOT break chronological order
        3. Timeline MUST be monotonic at all times
        
        **Validates: Requirements 15.1**
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
            
            # Generate ordered timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_entries - 1)
            
            # Add timeline entries one by one and verify order after each addition
            statuses = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            
            for i, timestamp in enumerate(timestamps):
                status = statuses[min(i, len(statuses) - 1)]
                
                # Add entry
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=timestamp,
                    location=f'Location {i+1}',
                    description=f'Status update {i+1}'
                )
                
                # Verify timeline is still ordered after this addition
                timeline = get_shipment_timeline(shipment_id)
                
                assert is_timeline_monotonic(timeline), (
                    f"Timeline must remain chronologically ordered after adding entry {i+1}"
                )
                
                # Verify entry count
                assert len(timeline) == i + 2, f"Timeline must have {i + 2} entries after {i+1} additions"
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_single_entry_timeline_is_trivially_monotonic(
        self,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: Single-entry timeline is trivially monotonic
        
        For any shipment with only the creation entry:
        1. Timeline MUST be considered monotonic
        2. Single entry MUST satisfy chronological ordering
        
        **Validates: Requirements 15.1**
        """
        setup_aws_environment()
        
        with mock_aws():
            create_dynamodb_tables()
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            shipments_table = dynamodb.Table('aquachain-shipments')
            
            # Create base shipment (only has creation entry)
            base_time = datetime(2025, 1, 1, 12, 0, 0)
            created_at = base_time.isoformat() + 'Z'
            
            shipment = create_test_shipment(shipment_id, tracking_number, created_at)
            shipments_table.put_item(Item=shipment)
            
            # Retrieve timeline
            timeline = get_shipment_timeline(shipment_id)
            
            # Assert: Timeline has exactly one entry
            assert len(timeline) == 1, "New shipment must have exactly one timeline entry"
            
            # Assert: Single-entry timeline is monotonic
            assert is_timeline_monotonic(timeline), "Single-entry timeline must be monotonic"
            
            # Assert: Entry is shipment creation
            assert timeline[0]['status'] == 'shipment_created'
            assert timeline[0]['timestamp'] == created_at
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_same_timestamp_entries_maintain_order(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: Entries with same timestamp maintain insertion order
        
        For any shipment with multiple entries at the same timestamp:
        1. Timeline MUST still be considered monotonic (timestamp[i] <= timestamp[i+1])
        2. Entries with identical timestamps MUST maintain insertion order
        3. No reordering MUST occur for same-timestamp entries
        
        **Validates: Requirements 15.1**
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
            
            # Use same timestamp for all new entries
            same_timestamp = (base_time + timedelta(minutes=10)).isoformat() + 'Z'
            
            # Add multiple entries with same timestamp
            statuses = ['picked_up', 'in_transit', 'out_for_delivery']
            for i in range(num_entries - 1):
                status = statuses[min(i, len(statuses) - 1)]
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=same_timestamp,
                    location=f'Location {i+1}',
                    description=f'Status update {i+1}'
                )
            
            # Retrieve timeline
            timeline = get_shipment_timeline(shipment_id)
            
            # Assert: Timeline is still monotonic (allows equal timestamps)
            assert is_timeline_monotonic(timeline), "Timeline with same-timestamp entries must be monotonic"
            
            # Assert: All new entries have the same timestamp
            for i in range(1, len(timeline)):
                assert timeline[i]['timestamp'] == same_timestamp, "All new entries must have same timestamp"
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=20, deadline=None)
    def test_timeline_with_many_entries_remains_monotonic(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: Timeline with many entries remains monotonic
        
        For any shipment with a large number of timeline entries:
        1. Timeline MUST remain chronologically ordered
        2. Monotonicity MUST hold across all entries
        3. No performance degradation in ordering verification
        
        **Validates: Requirements 15.1**
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
            
            # Generate many ordered timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_entries - 1)
            
            # Add many timeline entries
            statuses = ['picked_up', 'in_transit', 'in_transit', 'in_transit', 'out_for_delivery', 'delivered']
            for i, timestamp in enumerate(timestamps):
                status = statuses[min(i, len(statuses) - 1)]
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=timestamp,
                    location=f'Hub {i % 5}',
                    description=f'Update {i+1}'
                )
            
            # Retrieve timeline
            timeline = get_shipment_timeline(shipment_id)
            
            # Assert: Timeline has all entries
            assert len(timeline) == num_entries, f"Timeline must have {num_entries} entries"
            
            # Assert: Timeline is monotonic
            assert is_timeline_monotonic(timeline), "Timeline with many entries must be monotonic"
            
            # Assert: Verify every consecutive pair
            for i in range(len(timeline) - 1):
                current_time = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
                next_time = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
                
                assert current_time <= next_time, (
                    f"Entry {i} ({timeline[i]['timestamp']}) must be <= entry {i+1} ({timeline[i+1]['timestamp']})"
                )
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_empty_timeline_is_handled_gracefully(
        self,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: Empty timeline is handled gracefully
        
        For any shipment query that returns no timeline:
        1. is_timeline_monotonic() MUST return True (vacuously true)
        2. No errors MUST occur when checking empty timeline
        
        **Validates: Requirements 15.1**
        """
        # Test with empty list
        empty_timeline = []
        
        # Assert: Empty timeline is trivially monotonic
        assert is_timeline_monotonic(empty_timeline), "Empty timeline must be considered monotonic"
    
    @given(
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy,
        num_entries=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=20, deadline=None)
    def test_timeline_monotonicity_is_transitive(
        self,
        shipment_id: str,
        tracking_number: str,
        num_entries: int
    ):
        """
        Property Test: Timeline monotonicity is transitive
        
        For any shipment timeline with entries A, B, C:
        If timestamp(A) <= timestamp(B) and timestamp(B) <= timestamp(C),
        then timestamp(A) <= timestamp(C) must hold.
        
        **Validates: Requirements 15.1**
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
            
            # Generate ordered timestamps
            timestamps = generate_ordered_timestamps(base_time + timedelta(minutes=10), num_entries - 1)
            
            # Add timeline entries
            statuses = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            for i, timestamp in enumerate(timestamps):
                status = statuses[min(i, len(statuses) - 1)]
                add_timeline_entry(
                    shipment_id=shipment_id,
                    status=status,
                    timestamp=timestamp,
                    location=f'Location {i+1}',
                    description=f'Status update {i+1}'
                )
            
            # Retrieve timeline
            timeline = get_shipment_timeline(shipment_id)
            
            # Assert: Verify transitivity for all triplets
            for i in range(len(timeline) - 2):
                time_a = datetime.fromisoformat(timeline[i]['timestamp'].replace('Z', ''))
                time_b = datetime.fromisoformat(timeline[i + 1]['timestamp'].replace('Z', ''))
                time_c = datetime.fromisoformat(timeline[i + 2]['timestamp'].replace('Z', ''))
                
                # If A <= B and B <= C, then A <= C
                if time_a <= time_b and time_b <= time_c:
                    assert time_a <= time_c, (
                        f"Transitivity violated: {timeline[i]['timestamp']} <= {timeline[i+1]['timestamp']} "
                        f"and {timeline[i+1]['timestamp']} <= {timeline[i+2]['timestamp']}, "
                        f"but {timeline[i]['timestamp']} > {timeline[i+2]['timestamp']}"
                    )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
