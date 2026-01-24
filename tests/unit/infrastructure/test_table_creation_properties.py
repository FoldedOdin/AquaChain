"""
Property-based tests for DynamoDB table creation
Feature: shipment-tracking-automation, Property 1: Table Creation Idempotency
Validates: Requirements 1.1
"""

import pytest
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3
from typing import Dict, Any

# Add infrastructure path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'infrastructure', 'dynamodb'))

from shipments_table import ShipmentsTableManager
from device_orders_table import DeviceOrdersTableManager


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto"""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create a mocked DynamoDB client"""
    with mock_aws():
        yield boto3.client('dynamodb', region_name='us-east-1')


class TestTableCreationIdempotency:
    """
    Property 1: Table Creation Idempotency
    
    For any table creation operation, calling create_table multiple times
    should be idempotent - the first call creates the table, subsequent calls
    should handle the ResourceInUseException gracefully and return table info
    without error.
    """
    
    @mock_aws
    @given(call_count=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_shipments_table_creation_is_idempotent(self, call_count: int):
        """
        Property Test: Shipments table creation is idempotent
        
        For any number of consecutive create_table calls (1-5),
        the operation should succeed without raising exceptions,
        and the table should exist with the correct structure.
        
        **Validates: Requirements 1.1**
        """
        manager = ShipmentsTableManager(region_name='us-east-1')
        
        # Call create_table multiple times
        responses = []
        for i in range(call_count):
            response = manager.create_shipments_table()
            responses.append(response)
            
            # Verify response is valid
            assert response is not None
            assert 'TableDescription' in response or 'Table' in response
        
        # Verify table exists after all calls
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        table_description = dynamodb.describe_table(TableName='aquachain-shipments')
        
        # Verify table structure
        table = table_description['Table']
        assert table['TableName'] == 'aquachain-shipments'
        assert table['TableStatus'] in ['CREATING', 'ACTIVE']
        
        # Verify primary key
        key_schema = table['KeySchema']
        assert len(key_schema) == 1
        assert key_schema[0]['AttributeName'] == 'shipment_id'
        assert key_schema[0]['KeyType'] == 'HASH'
        
        # Verify GSIs exist
        gsis = table.get('GlobalSecondaryIndexes', [])
        gsi_names = [gsi['IndexName'] for gsi in gsis]
        assert 'order_id-index' in gsi_names
        assert 'tracking_number-index' in gsi_names
        assert 'status-created_at-index' in gsi_names
        
        # Verify billing mode
        assert table.get('BillingModeSummary', {}).get('BillingMode') == 'PAY_PER_REQUEST'
        
        # Verify streams enabled
        stream_spec = table.get('StreamSpecification', {})
        assert stream_spec.get('StreamEnabled') is True
    
    @mock_aws
    @given(call_count=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_device_orders_table_creation_is_idempotent(self, call_count: int):
        """
        Property Test: DeviceOrders table creation is idempotent
        
        For any number of consecutive create_table calls (1-5),
        the operation should succeed without raising exceptions,
        and the table should exist with the correct structure.
        
        **Validates: Requirements 1.1**
        """
        manager = DeviceOrdersTableManager(region_name='us-east-1')
        
        # Call create_table multiple times
        responses = []
        for i in range(call_count):
            response = manager.create_device_orders_table()
            responses.append(response)
            
            # Verify response is valid
            assert response is not None
            assert 'TableDescription' in response or 'Table' in response
        
        # Verify table exists after all calls
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        table_description = dynamodb.describe_table(TableName='DeviceOrders')
        
        # Verify table structure
        table = table_description['Table']
        assert table['TableName'] == 'DeviceOrders'
        assert table['TableStatus'] in ['CREATING', 'ACTIVE']
        
        # Verify primary key
        key_schema = table['KeySchema']
        assert len(key_schema) == 1
        assert key_schema[0]['AttributeName'] == 'orderId'
        assert key_schema[0]['KeyType'] == 'HASH'
        
        # Verify GSIs exist
        gsis = table.get('GlobalSecondaryIndexes', [])
        gsi_names = [gsi['IndexName'] for gsi in gsis]
        assert 'userId-createdAt-index' in gsi_names
        assert 'status-createdAt-index' in gsi_names
        
        # Verify billing mode
        assert table.get('BillingModeSummary', {}).get('BillingMode') == 'PAY_PER_REQUEST'
        
        # Verify streams enabled
        stream_spec = table.get('StreamSpecification', {})
        assert stream_spec.get('StreamEnabled') is True
    
    @mock_aws
    @given(
        first_region=st.sampled_from(['us-east-1', 'us-west-2', 'eu-west-1']),
        second_region=st.sampled_from(['us-east-1', 'us-west-2', 'eu-west-1'])
    )
    @settings(max_examples=50, deadline=None)
    def test_table_creation_idempotency_across_regions(self, first_region: str, second_region: str):
        """
        Property Test: Table creation in same region is idempotent
        
        For any region, creating a table twice in the same region should be idempotent.
        Creating in different regions should create separate tables.
        
        **Validates: Requirements 1.1**
        """
        # Create table in first region
        manager1 = ShipmentsTableManager(region_name=first_region)
        response1 = manager1.create_shipments_table()
        assert response1 is not None
        
        if first_region == second_region:
            # Same region - should be idempotent
            manager2 = ShipmentsTableManager(region_name=second_region)
            response2 = manager2.create_shipments_table()
            assert response2 is not None
            
            # Verify only one table exists in the region
            dynamodb = boto3.client('dynamodb', region_name=first_region)
            table_description = dynamodb.describe_table(TableName='aquachain-shipments')
            assert table_description['Table']['TableName'] == 'aquachain-shipments'
        else:
            # Different regions - should create separate tables
            manager2 = ShipmentsTableManager(region_name=second_region)
            response2 = manager2.create_shipments_table()
            assert response2 is not None
            
            # Verify table exists in both regions
            dynamodb1 = boto3.client('dynamodb', region_name=first_region)
            dynamodb2 = boto3.client('dynamodb', region_name=second_region)
            
            table1 = dynamodb1.describe_table(TableName='aquachain-shipments')
            table2 = dynamodb2.describe_table(TableName='aquachain-shipments')
            
            assert table1['Table']['TableName'] == 'aquachain-shipments'
            assert table2['Table']['TableName'] == 'aquachain-shipments'
    
    @mock_aws
    @given(call_count=st.integers(min_value=2, max_value=10))
    @settings(max_examples=100, deadline=None)
    def test_concurrent_table_creation_attempts_are_safe(self, call_count: int):
        """
        Property Test: Concurrent table creation attempts are safe
        
        For any number of concurrent-like table creation attempts,
        all calls should complete without raising exceptions,
        and exactly one table should exist with correct structure.
        
        **Validates: Requirements 1.1**
        """
        manager = ShipmentsTableManager(region_name='us-east-1')
        
        # Simulate concurrent creation attempts
        results = []
        exceptions = []
        
        for i in range(call_count):
            try:
                response = manager.create_shipments_table()
                results.append(response)
            except Exception as e:
                exceptions.append(e)
        
        # All calls should succeed (no unhandled exceptions)
        assert len(exceptions) == 0
        assert len(results) == call_count
        
        # Verify exactly one table exists
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        tables = dynamodb.list_tables()
        
        # Count how many times our table appears
        shipment_tables = [t for t in tables['TableNames'] if t == 'aquachain-shipments']
        assert len(shipment_tables) == 1
        
        # Verify table structure is correct
        table_description = dynamodb.describe_table(TableName='aquachain-shipments')
        table = table_description['Table']
        assert table['TableName'] == 'aquachain-shipments'
        
        # Verify all essential components exist
        assert len(table['KeySchema']) == 1
        assert len(table.get('GlobalSecondaryIndexes', [])) == 3
        assert table.get('StreamSpecification', {}).get('StreamEnabled') is True
