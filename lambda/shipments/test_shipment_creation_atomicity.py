"""
Property-based tests for shipment creation atomicity
Feature: shipment-tracking-automation, Property 1: Shipment Creation Atomicity
Validates: Requirements 1.3

This test verifies that shipment creation is atomic:
- Either both Shipments table record AND DeviceOrders update succeed
- Or both operations fail (no partial updates visible)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from moto import mock_aws
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Import the module under test
import create_shipment
from errors import DatabaseError


def setup_aws_environment():
    """Setup AWS environment variables"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['SHIPMENTS_TABLE'] = 'aquachain-shipments'
    os.environ['ORDERS_TABLE'] = 'DeviceOrders'
    os.environ['COURIER_API_KEY'] = ''  # Mock mode
    os.environ['SNS_TOPIC_ARN'] = ''  # Disable notifications


def create_dynamodb_tables():
    """Create mocked DynamoDB tables - returns context manager"""
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
    
    # Create DeviceOrders table
    dynamodb.create_table(
        TableName='DeviceOrders',
        KeySchema=[
            {'AttributeName': 'orderId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'orderId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    return dynamodb


# Hypothesis strategies for generating test data
order_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
    min_size=10,
    max_size=20
).map(lambda s: f"ord_{s}")

device_id_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=10,
    max_size=15
).map(lambda s: f"AquaChain-Device-{s}")

courier_strategy = st.sampled_from(['Delhivery', 'BlueDart', 'DTDC'])

address_strategy = st.text(min_size=10, max_size=100)
pincode_strategy = st.from_regex(r'[1-9][0-9]{5}', fullmatch=True)
name_strategy = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ', min_size=3, max_size=50)
phone_strategy = st.from_regex(r'\+91[6-9][0-9]{9}', fullmatch=True)

weight_strategy = st.floats(min_value=0.1, max_value=10.0).map(lambda w: f"{w:.1f}kg")
value_strategy = st.integers(min_value=1000, max_value=50000)


class TestShipmentCreationAtomicity:
    """
    Property 1: Shipment Creation Atomicity
    
    For any order marked as "shipped", creating a shipment record and updating
    the order status must succeed or fail atomically—partial updates are never visible.
    
    This means:
    1. If transaction succeeds: Both Shipments record exists AND DeviceOrders is updated
    2. If transaction fails: Neither Shipments record exists NOR DeviceOrders is updated
    3. No intermediate state where only one operation succeeded
    """
    
    @given(
        order_id=order_id_strategy,
        device_id=device_id_strategy,
        courier_name=courier_strategy,
        address=address_strategy,
        pincode=pincode_strategy,
        contact_name=name_strategy,
        contact_phone=phone_strategy,
        weight=weight_strategy,
        declared_value=value_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_successful_shipment_creation_is_atomic(
        self,
        order_id: str,
        device_id: str,
        courier_name: str,
        address: str,
        pincode: str,
        contact_name: str,
        contact_phone: str,
        weight: str,
        declared_value: int
    ):
        """
        Property Test: Successful shipment creation updates both tables atomically
        
        For any valid order and shipment data, when the transaction succeeds:
        1. A new record MUST exist in Shipments table
        2. The DeviceOrders record MUST be updated with shipment_id and tracking_number
        3. Both updates MUST be visible together (atomicity)
        
        **Validates: Requirements 1.3**
        """
        # Setup AWS environment
        setup_aws_environment()
        
        with mock_aws():
            # Create tables within the mock context
            dynamodb = create_dynamodb_tables()
            
            # Reinitialize the module's boto3 clients to use mocked resources
            create_shipment.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            create_shipment.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
            create_shipment.sns = boto3.client('sns', region_name='us-east-1')
            
            # Setup: Create an order in DeviceOrders table
            dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
            orders_table = dynamodb_resource.Table('DeviceOrders')
            
            orders_table.put_item(Item={
                'orderId': order_id,
                'device_id': device_id,
                'status': 'approved',
                'consumerEmail': 'test@example.com',
                'consumerName': 'Test Consumer',
                'createdAt': datetime.utcnow().isoformat() + 'Z'
            })
            
            # Prepare shipment creation request
            shipment_request = {
                'order_id': order_id,
                'courier_name': courier_name,
                'service_type': 'Surface',
                'destination': {
                    'address': address,
                    'pincode': pincode,
                    'contact_name': contact_name,
                    'contact_phone': contact_phone
                },
                'package_details': {
                    'weight': weight,
                    'declared_value': declared_value,
                    'insurance': True
                }
            }
            
            # Generate shipment_id and tracking_number
            shipment_id = create_shipment.generate_shipment_id()
            tracking_number = f"MOCK{int(datetime.now().timestamp())}"
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Build shipment item
            order = orders_table.get_item(Key={'orderId': order_id})['Item']
            shipment_item = create_shipment.build_shipment_item(
                shipment_id=shipment_id,
                order_id=order_id,
                order=order,
                body=shipment_request,
                tracking_number=tracking_number,
                estimated_delivery=(datetime.now() + timedelta(days=3)).isoformat() + 'Z',
                timestamp=timestamp,
                user_id='test_user'
            )
            
            # Execute atomic transaction
            create_shipment.execute_atomic_transaction(
                shipment_item=shipment_item,
                order_id=order_id,
                shipment_id=shipment_id,
                tracking_number=tracking_number,
                timestamp=timestamp
            )
            
            # Verify atomicity: Both operations succeeded
            shipments_table = dynamodb_resource.Table('aquachain-shipments')
            
            # 1. Shipment record must exist
            shipment_response = shipments_table.get_item(Key={'shipment_id': shipment_id})
            assert 'Item' in shipment_response, "Shipment record must exist after successful transaction"
            
            shipment = shipment_response['Item']
            assert shipment['shipment_id'] == shipment_id
            assert shipment['order_id'] == order_id
            assert shipment['tracking_number'] == tracking_number
            assert shipment['internal_status'] == 'shipment_created'
            assert shipment['external_status'] == 'shipped'
            
            # 2. Order must be updated
            order_response = orders_table.get_item(Key={'orderId': order_id})
            assert 'Item' in order_response, "Order record must exist after successful transaction"
            
            updated_order = order_response['Item']
            assert updated_order['status'] == 'shipped', "Order status must be updated to 'shipped'"
            assert updated_order['shipment_id'] == shipment_id, "Order must have shipment_id"
            assert updated_order['tracking_number'] == tracking_number, "Order must have tracking_number"
            assert 'shipped_at' in updated_order, "Order must have shipped_at timestamp"
            
            # 3. Verify consistency: shipment_id and tracking_number match
            assert shipment['shipment_id'] == updated_order['shipment_id']
            assert shipment['tracking_number'] == updated_order['tracking_number']
            assert shipment['order_id'] == updated_order['orderId']
    
    @given(
        order_id=order_id_strategy,
        device_id=device_id_strategy,
        courier_name=courier_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_failed_transaction_leaves_no_partial_updates(
        self,
        order_id: str,
        device_id: str,
        courier_name: str
    ):
        """
        Property Test: Failed transaction leaves no partial updates
        
        For any shipment creation attempt that fails (e.g., order doesn't exist),
        the transaction MUST roll back completely:
        1. No record MUST exist in Shipments table
        2. No updates MUST be made to DeviceOrders table
        3. System MUST be in consistent state (no orphaned data)
        
        **Validates: Requirements 1.3**
        """
        # Setup AWS environment
        setup_aws_environment()
        
        with mock_aws():
            # Create tables within the mock context
            dynamodb = create_dynamodb_tables()
            
            # Reinitialize the module's boto3 clients to use mocked resources
            create_shipment.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            create_shipment.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
            create_shipment.sns = boto3.client('sns', region_name='us-east-1')
            
            # Setup: Do NOT create order (simulate order not found scenario)
            dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
            
            # Generate shipment data
            shipment_id = create_shipment.generate_shipment_id()
            tracking_number = f"MOCK{int(datetime.now().timestamp())}"
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Build minimal shipment item
            shipment_item = {
                'shipment_id': shipment_id,
                'order_id': order_id,
                'device_id': device_id,
                'tracking_number': tracking_number,
                'courier_name': courier_name,
                'internal_status': 'shipment_created',
                'external_status': 'shipped',
                'created_at': timestamp,
                'updated_at': timestamp
            }
            
            # Attempt atomic transaction (should fail because order doesn't exist)
            with pytest.raises(DatabaseError) as exc_info:
                create_shipment.execute_atomic_transaction(
                    shipment_item=shipment_item,
                    order_id=order_id,
                    shipment_id=shipment_id,
                    tracking_number=tracking_number,
                    timestamp=timestamp
                )
            
            # Verify the error is about order not found or transaction failed
            assert 'ORDER_NOT_FOUND' in str(exc_info.value.error_code) or 'TRANSACTION_CANCELLED' in str(exc_info.value.error_code) or 'TRANSACTION_FAILED' in str(exc_info.value.error_code)
            
            # Verify atomicity: No partial updates
            shipments_table = dynamodb_resource.Table('aquachain-shipments')
            orders_table = dynamodb_resource.Table('DeviceOrders')
            
            # 1. Shipment record must NOT exist
            shipment_response = shipments_table.get_item(Key={'shipment_id': shipment_id})
            assert 'Item' not in shipment_response, "Shipment record must NOT exist after failed transaction"
            
            # 2. Order must NOT exist (we never created it)
            order_response = orders_table.get_item(Key={'orderId': order_id})
            assert 'Item' not in order_response, "Order record must NOT exist"
            
            # 3. Verify no orphaned data in either table
            # Scan Shipments table for this order_id
            shipments_scan = shipments_table.scan(
                FilterExpression='order_id = :oid',
                ExpressionAttributeValues={':oid': order_id}
            )
            assert shipments_scan['Count'] == 0, "No shipment records should exist for non-existent order"
    
    @given(
        order_id=order_id_strategy,
        device_id=device_id_strategy,
        courier_name=courier_strategy,
        address=address_strategy,
        pincode=pincode_strategy,
        contact_name=name_strategy,
        contact_phone=phone_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_duplicate_shipment_creation_fails_atomically(
        self,
        order_id: str,
        device_id: str,
        courier_name: str,
        address: str,
        pincode: str,
        contact_name: str,
        contact_phone: str
    ):
        """
        Property Test: Duplicate shipment creation fails atomically
        
        For any order that already has a shipment, attempting to create
        a second shipment MUST fail atomically:
        1. The duplicate shipment record MUST NOT be created
        2. The existing order MUST NOT be modified
        3. The original shipment MUST remain unchanged
        
        **Validates: Requirements 1.3**
        """
        # Setup AWS environment
        setup_aws_environment()
        
        with mock_aws():
            # Create tables within the mock context
            dynamodb = create_dynamodb_tables()
            
            # Reinitialize the module's boto3 clients to use mocked resources
            create_shipment.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            create_shipment.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
            create_shipment.sns = boto3.client('sns', region_name='us-east-1')
            
            # Setup: Create an order
            dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
            orders_table = dynamodb_resource.Table('DeviceOrders')
            
            orders_table.put_item(Item={
                'orderId': order_id,
                'device_id': device_id,
                'status': 'approved',
                'consumerEmail': 'test@example.com',
                'consumerName': 'Test Consumer',
                'createdAt': datetime.utcnow().isoformat() + 'Z'
            })
            
            # Create first shipment successfully
            shipment_id_1 = create_shipment.generate_shipment_id()
            tracking_number_1 = f"MOCK{int(datetime.now().timestamp())}"
            timestamp_1 = datetime.utcnow().isoformat() + 'Z'
            
            shipment_request = {
                'order_id': order_id,
                'courier_name': courier_name,
                'destination': {
                    'address': address,
                    'pincode': pincode,
                    'contact_name': contact_name,
                    'contact_phone': contact_phone
                },
                'package_details': {
                    'weight': '0.5kg',
                    'declared_value': 5000
                }
            }
            
            order = orders_table.get_item(Key={'orderId': order_id})['Item']
            shipment_item_1 = create_shipment.build_shipment_item(
                shipment_id=shipment_id_1,
                order_id=order_id,
                order=order,
                body=shipment_request,
                tracking_number=tracking_number_1,
                estimated_delivery=(datetime.now() + timedelta(days=3)).isoformat() + 'Z',
                timestamp=timestamp_1,
                user_id='test_user'
            )
            
            # First transaction should succeed
            create_shipment.execute_atomic_transaction(
                shipment_item=shipment_item_1,
                order_id=order_id,
                shipment_id=shipment_id_1,
                tracking_number=tracking_number_1,
                timestamp=timestamp_1
            )
            
            # Verify first shipment exists
            shipments_table = dynamodb_resource.Table('aquachain-shipments')
            first_shipment = shipments_table.get_item(Key={'shipment_id': shipment_id_1})['Item']
            first_order_state = orders_table.get_item(Key={'orderId': order_id})['Item']
            
            # Attempt to create duplicate shipment with same shipment_id (should fail)
            import time
            time.sleep(0.001)  # Ensure different timestamp
            
            shipment_id_2 = shipment_id_1  # Same shipment_id (duplicate)
            tracking_number_2 = f"MOCK{int(datetime.now().timestamp())}"
            timestamp_2 = datetime.utcnow().isoformat() + 'Z'
            
            shipment_item_2 = create_shipment.build_shipment_item(
                shipment_id=shipment_id_2,
                order_id=order_id,
                order=order,
                body=shipment_request,
                tracking_number=tracking_number_2,
                estimated_delivery=(datetime.now() + timedelta(days=3)).isoformat() + 'Z',
                timestamp=timestamp_2,
                user_id='test_user'
            )
            
            # Second transaction should fail
            with pytest.raises(DatabaseError) as exc_info:
                create_shipment.execute_atomic_transaction(
                    shipment_item=shipment_item_2,
                    order_id=order_id,
                    shipment_id=shipment_id_2,
                    tracking_number=tracking_number_2,
                    timestamp=timestamp_2
                )
            
            # Verify error is about duplicate shipment
            assert 'SHIPMENT_ALREADY_EXISTS' in str(exc_info.value.error_code) or 'TRANSACTION_CANCELLED' in str(exc_info.value.error_code)
            
            # Verify atomicity: Original data unchanged
            # 1. Original shipment must still exist with original data
            current_shipment = shipments_table.get_item(Key={'shipment_id': shipment_id_1})['Item']
            assert current_shipment['shipment_id'] == first_shipment['shipment_id']
            assert current_shipment['tracking_number'] == first_shipment['tracking_number']
            assert current_shipment['created_at'] == first_shipment['created_at']
            
            # 2. Order must still have original shipment data
            current_order = orders_table.get_item(Key={'orderId': order_id})['Item']
            assert current_order['shipment_id'] == first_order_state['shipment_id']
            assert current_order['tracking_number'] == first_order_state['tracking_number']
            assert current_order['shipped_at'] == first_order_state['shipped_at']
            
            # 3. No duplicate shipment records
            shipments_scan = shipments_table.scan(
                FilterExpression='order_id = :oid',
                ExpressionAttributeValues={':oid': order_id}
            )
            assert shipments_scan['Count'] == 1, "Only one shipment should exist for the order"
    
    @given(
        order_id=order_id_strategy,
        device_id=device_id_strategy,
        courier_name=courier_strategy,
        num_concurrent_attempts=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_concurrent_shipment_creation_maintains_atomicity(
        self,
        order_id: str,
        device_id: str,
        courier_name: str,
        num_concurrent_attempts: int
    ):
        """
        Property Test: Concurrent shipment creation attempts maintain atomicity
        
        For any order, when multiple concurrent shipment creation attempts occur:
        1. At most one shipment MUST be created successfully
        2. The order MUST be updated exactly once
        3. No partial updates MUST be visible
        4. All failed attempts MUST leave no trace
        
        **Validates: Requirements 1.3**
        """
        # Setup AWS environment
        setup_aws_environment()
        
        with mock_aws():
            # Create tables within the mock context
            dynamodb = create_dynamodb_tables()
            
            # Reinitialize the module's boto3 clients to use mocked resources
            create_shipment.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            create_shipment.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
            create_shipment.sns = boto3.client('sns', region_name='us-east-1')
            
            # Setup: Create an order
            dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
            orders_table = dynamodb_resource.Table('DeviceOrders')
            
            orders_table.put_item(Item={
                'orderId': order_id,
                'device_id': device_id,
                'status': 'approved',
                'consumerEmail': 'test@example.com',
                'consumerName': 'Test Consumer',
                'createdAt': datetime.utcnow().isoformat() + 'Z'
            })
            
            # Simulate concurrent attempts with different shipment_ids
            successful_attempts = []
            failed_attempts = []
            
            for i in range(num_concurrent_attempts):
                import time
                time.sleep(0.001)  # Ensure unique timestamps
                
                shipment_id = create_shipment.generate_shipment_id()
                tracking_number = f"MOCK{int(datetime.now().timestamp())}{i}"
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                shipment_item = {
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'device_id': device_id,
                    'tracking_number': tracking_number,
                    'courier_name': courier_name,
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
                        'timestamp': timestamp,
                        'location': 'Warehouse',
                        'description': 'Shipment created'
                    }],
                    'webhook_events': [],
                    'retry_config': {'max_retries': 3, 'retry_count': 0, 'last_retry_at': None},
                    'metadata': {'weight': '0.5kg', 'declared_value': 5000},
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'delivered_at': None,
                    'failed_at': None,
                    'created_by': 'test_user',
                    'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat() + 'Z'
                }
                
                try:
                    create_shipment.execute_atomic_transaction(
                        shipment_item=shipment_item,
                        order_id=order_id,
                        shipment_id=shipment_id,
                        tracking_number=tracking_number,
                        timestamp=timestamp
                    )
                    successful_attempts.append(shipment_id)
                except DatabaseError:
                    failed_attempts.append(shipment_id)
            
            # Verify atomicity properties
            shipments_table = dynamodb_resource.Table('aquachain-shipments')
            
            # 1. At most one shipment should succeed
            assert len(successful_attempts) <= 1, "At most one concurrent attempt should succeed"
            
            # 2. Count actual shipments in database
            shipments_scan = shipments_table.scan(
                FilterExpression='order_id = :oid',
                ExpressionAttributeValues={':oid': order_id}
            )
            assert shipments_scan['Count'] <= 1, "At most one shipment record should exist"
            
            # 3. If a shipment succeeded, verify order is updated correctly
            if len(successful_attempts) == 1:
                successful_shipment_id = successful_attempts[0]
                
                # Verify shipment exists
                shipment = shipments_table.get_item(Key={'shipment_id': successful_shipment_id})['Item']
                assert shipment['order_id'] == order_id
                
                # Verify order is updated
                order = orders_table.get_item(Key={'orderId': order_id})['Item']
                assert order['status'] == 'shipped'
                assert order['shipment_id'] == successful_shipment_id
                assert 'tracking_number' in order
                assert 'shipped_at' in order
            
            # 4. Verify failed attempts left no trace
            for failed_shipment_id in failed_attempts:
                shipment_response = shipments_table.get_item(Key={'shipment_id': failed_shipment_id})
                assert 'Item' not in shipment_response, f"Failed shipment {failed_shipment_id} should not exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
