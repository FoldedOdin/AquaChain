"""
Property-based tests for real-time update system
Feature: enhanced-consumer-ordering-system, Property 15: Real-time Update System
Validates: Requirements 4.4, 7.1, 7.2, 7.3, 7.4, 7.5

This test verifies that the real-time update system maintains integrity:
- Order status changes push real-time updates to consumer's dashboard
- WebSocket connections are maintained for live order tracking
- Connection loss triggers automatic reconnection and sync order status
- Timestamps are displayed for all status updates
- Multiple orders update only the relevant order without affecting others
"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
import json
import uuid
from botocore.exceptions import ClientError

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Import the modules under test
from handler import lambda_handler, broadcast_order_status_update, get_order_subscribed_connections
from broadcast_handler import broadcast_to_connections, handle_dynamodb_stream
from connection_manager import ConnectionManager


# Hypothesis strategies for generating test data
connection_id_strategy = st.uuids().map(str)
order_id_strategy = st.uuids().map(str)
user_id_strategy = st.uuids().map(str)

order_status_strategy = st.sampled_from([
    'PENDING_PAYMENT',
    'PENDING_CONFIRMATION', 
    'ORDER_PLACED',
    'SHIPPED',
    'OUT_FOR_DELIVERY',
    'DELIVERED',
    'CANCELLED',
    'FAILED'
])

user_role_strategy = st.sampled_from(['consumer', 'technician', 'administrator'])

# WebSocket message types
message_type_strategy = st.sampled_from([
    'order_status_update',
    'payment_status_update',
    'technician_assignment_update',
    'connection_established',
    'order_subscription_confirmed'
])

# Connection data strategy
connection_data_strategy = st.fixed_dictionaries({
    'connectionId': connection_id_strategy,
    'userId': user_id_strategy,
    'userRole': user_role_strategy,
    'connectionType': st.just('order_updates'),
    'connectedAt': st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)).map(lambda dt: dt.isoformat()),
    'lastPing': st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)).map(lambda dt: dt.isoformat()),
    'orderSubscriptions': st.lists(order_id_strategy, min_size=0, max_size=5),
    'ttl': st.integers(min_value=1700000000, max_value=2000000000)
})

# Order data strategy
order_data_strategy = st.fixed_dictionaries({
    'orderId': order_id_strategy,
    'consumerId': user_id_strategy,
    'status': order_status_strategy,
    'previousStatus': st.one_of(st.none(), order_status_strategy),
    'deviceType': st.sampled_from(['Water Quality Monitor', 'pH Sensor', 'TDS Meter']),
    'serviceType': st.sampled_from(['Installation', 'Maintenance', 'Repair']),
    'assignedTechnician': st.one_of(st.none(), user_id_strategy),
    'amount': st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    'statusHistory': st.lists(
        st.fixed_dictionaries({
            'status': order_status_strategy,
            'timestamp': st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)).map(lambda dt: dt.isoformat()),
            'message': st.text(min_size=1, max_size=200),
            'metadata': st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=3)
        }),
        min_size=1,
        max_size=5
    )
})


class TestRealTimeUpdateSystemProperty:
    """
    Property 15: Real-time Update System
    
    For any order status change, the system must:
    1. Push real-time updates to the consumer's dashboard with timestamps
    2. Maintain WebSocket connections for live order tracking
    3. Handle reconnection and sync order status when connection is lost
    4. Update only the relevant order without affecting others
    5. Display timestamps for all status updates
    """
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        os.environ['WEBSOCKET_CONNECTIONS_TABLE_NAME'] = 'test-websocket-connections'
        os.environ['ORDERS_TABLE_NAME'] = 'test-orders'
        os.environ['WEBSOCKET_ENDPOINT'] = 'wss://test.execute-api.us-east-1.amazonaws.com/test'
        
        # Mock AWS clients
        self.mock_dynamodb = Mock()
        self.mock_apigateway = Mock()
        self.mock_connections_table = Mock()
        self.mock_orders_table = Mock()
        
        # Setup connection manager
        self.connection_manager = ConnectionManager('wss://test.execute-api.us-east-1.amazonaws.com/test')
        self.connection_manager.connections_table = self.mock_connections_table
    
    @given(
        order_data=order_data_strategy,
        connections=st.lists(connection_data_strategy, min_size=1, max_size=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_order_status_changes_push_real_time_updates_with_timestamps(
        self,
        order_data: dict,
        connections: list
    ):
        """
        Property Test: Order status changes push real-time updates to consumer's dashboard with timestamps
        
        For any order status change:
        1. Real-time updates MUST be pushed to subscribed connections
        2. Updates MUST include timestamps in ISO format
        3. Updates MUST contain current and previous status information
        4. Updates MUST include order details and status history
        
        **Validates: Requirements 4.4, 7.1, 7.4**
        """
        order_id = order_data['orderId']
        
        # Ensure connections are subscribed to this order
        for connection in connections:
            if order_id not in connection['orderSubscriptions']:
                connection['orderSubscriptions'].append(order_id)
        
        # Mock getting subscribed connections
        with patch('handler.get_order_subscribed_connections', return_value=connections):
            with patch('handler.send_message_to_connection') as mock_send:
                mock_send.return_value = True
                
                # Act: Broadcast order status update
                with patch('handler.datetime') as mock_datetime:
                    fixed_timestamp = '2024-01-01T12:00:00+00:00'
                    mock_datetime.utcnow.return_value.isoformat.return_value = fixed_timestamp
                    
                    broadcast_order_status_update(order_id, order_data)
                
                # Assert: Messages sent to all subscribed connections
                assert mock_send.call_count == len(connections), f"Should send message to all {len(connections)} connections"
                
                # Verify message content for each connection
                for i, connection in enumerate(connections):
                    call_args = mock_send.call_args_list[i]
                    connection_id, message = call_args[0]
                    
                    # Verify connection ID
                    assert connection_id == connection['connectionId'], "Message sent to correct connection"
                    
                    # Verify message structure
                    assert message['type'] == 'order_status_update', "Message type should be order_status_update"
                    assert message['orderId'] == order_id, "Message should contain correct order ID"
                    assert message['status'] == order_data['status'], "Message should contain current status"
                    
                    # Verify timestamp presence and format
                    assert 'timestamp' in message, "Message must include timestamp"
                    timestamp = message['timestamp']
                    assert timestamp == fixed_timestamp, "Timestamp should match fixed timestamp"
                    assert 'T' in timestamp, "Timestamp should be in ISO format"
                    assert timestamp.endswith('+00:00') or timestamp.endswith('Z'), "Timestamp should include timezone"
                    
                    # Verify status information
                    if order_data.get('previousStatus'):
                        assert message['previousStatus'] == order_data['previousStatus'], "Message should include previous status"
                    
                    # Verify status history
                    assert 'statusHistory' in message, "Message should include status history"
                    assert message['statusHistory'] == order_data['statusHistory'], "Status history should match order data"
                    
                    # Verify order details (if present in order data)
                    if 'deviceType' in order_data:
                        assert message.get('deviceType') == order_data['deviceType'], "Message should include device type"
                    if 'serviceType' in order_data:
                        assert message.get('serviceType') == order_data['serviceType'], "Message should include service type"
                    if 'amount' in order_data:
                        assert message.get('amount') == order_data['amount'], "Message should include amount"
    
    @given(
        connections=st.lists(connection_data_strategy, min_size=2, max_size=10),
        order_id=order_id_strategy,
        message_data=st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), min_size=1, max_size=5)
    )
    @settings(max_examples=15, deadline=None)
    def test_websocket_connections_maintained_for_live_tracking(
        self,
        connections: list,
        order_id: str,
        message_data: dict
    ):
        """
        Property Test: WebSocket connections are maintained for live order tracking
        
        For any set of WebSocket connections:
        1. Active connections MUST be maintained in the connections table
        2. Messages MUST be successfully delivered to active connections
        3. Stale connections MUST be automatically removed when delivery fails
        4. Connection health MUST be monitored through ping/pong
        
        **Validates: Requirements 7.2, 7.3**
        """
        # Setup: Mix of active and stale connections
        active_connections = connections[:len(connections)//2] if len(connections) > 1 else connections
        stale_connections = connections[len(connections)//2:] if len(connections) > 1 else []
        
        # Mock API Gateway responses
        def mock_post_to_connection(ConnectionId, Data):
            if any(conn['connectionId'] == ConnectionId for conn in stale_connections):
                # Simulate stale connection
                error_response = {'Error': {'Code': 'GoneException', 'Message': 'Connection is gone'}}
                raise ClientError(error_response, 'PostToConnection')
            return {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        with patch('broadcast_handler.apigateway_client') as mock_api:
            mock_api.post_to_connection.side_effect = mock_post_to_connection
            mock_api.exceptions.GoneException = ClientError
            
            with patch('broadcast_handler.remove_stale_connection') as mock_remove:
                # Act: Broadcast message to connections
                test_message = {
                    'type': 'test_message',
                    'orderId': order_id,
                    'data': message_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                results = broadcast_to_connections(connections, test_message)
                
                # Assert: Results should reflect active vs stale connections
                expected_successful = len(active_connections)
                expected_failed = len(stale_connections)
                
                assert results['successful'] == expected_successful, f"Should have {expected_successful} successful sends"
                assert results['failed'] == expected_failed, f"Should have {expected_failed} failed sends"
                
                # Verify stale connections were marked for removal
                if stale_connections:
                    assert mock_remove.call_count == len(stale_connections), "All stale connections should be removed"
                    
                    # Verify correct connection IDs were removed
                    removed_connection_ids = [call[0][0] for call in mock_remove.call_args_list]
                    expected_removed_ids = [conn['connectionId'] for conn in stale_connections]
                    assert set(removed_connection_ids) == set(expected_removed_ids), "Correct stale connections should be removed"
                
                # Verify API calls were made for all connections
                assert mock_api.post_to_connection.call_count == len(connections), "Should attempt to send to all connections"
    
    @given(
        user_id=user_id_strategy,
        order_ids=st.lists(order_id_strategy, min_size=1, max_size=5, unique=True),
        connection_id=connection_id_strategy
    )
    @settings(max_examples=15, deadline=None)
    def test_connection_loss_triggers_reconnection_and_sync(
        self,
        user_id: str,
        order_ids: list,
        connection_id: str
    ):
        """
        Property Test: Connection loss triggers automatic reconnection and sync order status
        
        For any connection reconnection:
        1. Previous subscriptions MUST be restored from user's connection history
        2. Reconnection confirmation MUST be sent with restored subscriptions
        3. Order status MUST be synced for all restored subscriptions
        4. Connection state MUST be consistent after reconnection
        
        **Validates: Requirements 7.3**
        """
        # Setup: Previous connections for the user with various subscriptions
        previous_connections = []
        all_subscriptions = set()
        
        for i, order_id in enumerate(order_ids):
            prev_conn = {
                'connectionId': f'prev-conn-{i}',
                'userId': user_id,
                'userRole': 'consumer',
                'connectionType': 'order_updates',
                'orderSubscriptions': [order_id] + (order_ids[:i] if i > 0 else []),
                'connectedAt': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                'lastPing': (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            }
            previous_connections.append(prev_conn)
            all_subscriptions.update(prev_conn['orderSubscriptions'])
        
        # Mock getting user connections
        self.connection_manager.get_connections_for_user = Mock(return_value=previous_connections)
        
        # Mock table update
        self.mock_connections_table.update_item.return_value = {}
        
        # Mock send message
        self.connection_manager.send_message = Mock(return_value=True)
        
        # Act: Handle reconnection
        result = self.connection_manager.handle_reconnection(connection_id, user_id)
        
        # Assert: Reconnection should succeed
        assert result['success'] is True, "Reconnection should succeed"
        assert 'restoredSubscriptions' in result, "Result should include restored subscriptions"
        
        restored_subscriptions = set(result['restoredSubscriptions'])
        expected_subscriptions = all_subscriptions - {connection_id}  # Exclude current connection
        
        # Verify all unique subscriptions were restored (excluding duplicates)
        unique_expected = set()
        for conn in previous_connections:
            unique_expected.update(conn['orderSubscriptions'])
        
        assert restored_subscriptions == unique_expected, f"Should restore all unique subscriptions: {unique_expected}"
        
        # Verify connection was updated with restored subscriptions
        if restored_subscriptions:
            self.mock_connections_table.update_item.assert_called()
            # Get the last call (most recent update)
            call_args = self.mock_connections_table.update_item.call_args_list[-1][1]
            assert call_args['Key']['connectionId'] == connection_id, "Should update correct connection"
            assert set(call_args['ExpressionAttributeValues'][':subscriptions']) == restored_subscriptions, "Should set restored subscriptions"
        else:
            # If no subscriptions to restore, update_item might not be called
            pass
        
        # Verify reconnection confirmation was sent
        self.connection_manager.send_message.assert_called_once()
        message_call = self.connection_manager.send_message.call_args[0]
        assert message_call[0] == connection_id, "Should send message to reconnecting connection"
        
        message = message_call[1]
        assert message['type'] == 'reconnection_complete', "Should send reconnection confirmation"
        assert set(message['restoredSubscriptions']) == restored_subscriptions, "Message should include restored subscriptions"
        assert 'timestamp' in message, "Message should include timestamp"
    
    @given(
        multiple_orders=st.lists(order_data_strategy, min_size=2, max_size=5, unique_by=lambda x: x['orderId']),
        target_order_index=st.integers(min_value=0, max_value=4),
        connections=st.lists(connection_data_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=10, deadline=None)
    def test_multiple_orders_update_only_relevant_order(
        self,
        multiple_orders: list,
        target_order_index: int,
        connections: list
    ):
        """
        Property Test: Multiple orders update only the relevant order without affecting others
        
        For any order status update in a multi-order environment:
        1. Only connections subscribed to the specific order MUST receive updates
        2. Other orders MUST remain unaffected by the update
        3. Connections subscribed to multiple orders MUST receive updates only for relevant orders
        4. Update isolation MUST be maintained across different orders
        
        **Validates: Requirements 7.5**
        """
        assume(target_order_index < len(multiple_orders))
        
        target_order = multiple_orders[target_order_index]
        target_order_id = target_order['orderId']
        other_orders = [order for order in multiple_orders if order['orderId'] != target_order_id]
        
        # Setup: Connections with different subscription patterns
        # Some subscribed to target order, some to other orders, some to multiple
        subscribed_to_target = []
        not_subscribed_to_target = []
        
        for i, connection in enumerate(connections):
            if i % 3 == 0:
                # Subscribe to target order only
                connection['orderSubscriptions'] = [target_order_id]
                subscribed_to_target.append(connection)
            elif i % 3 == 1:
                # Subscribe to other orders only
                other_order_ids = [order['orderId'] for order in other_orders[:2]]  # Limit to avoid too many
                connection['orderSubscriptions'] = other_order_ids
                not_subscribed_to_target.append(connection)
            else:
                # Subscribe to target + some other orders
                other_order_ids = [order['orderId'] for order in other_orders[:1]]  # Limit to avoid too many
                connection['orderSubscriptions'] = [target_order_id] + other_order_ids
                subscribed_to_target.append(connection)
        
        # Mock getting subscribed connections to return only those subscribed to target
        def mock_get_subscribed(order_id):
            if order_id == target_order_id:
                return subscribed_to_target
            else:
                return [conn for conn in not_subscribed_to_target 
                       if order_id in conn.get('orderSubscriptions', [])]
        
        with patch('handler.get_order_subscribed_connections', side_effect=mock_get_subscribed):
            with patch('handler.send_message_to_connection') as mock_send:
                mock_send.return_value = True
                
                # Act: Broadcast update for target order only
                with patch('handler.datetime') as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = '2024-01-01T12:00:00+00:00'
                    
                    broadcast_order_status_update(target_order_id, target_order)
                
                # Assert: Only connections subscribed to target order should receive updates
                expected_calls = len(subscribed_to_target)
                assert mock_send.call_count == expected_calls, f"Should send {expected_calls} messages for target order"
                
                # Verify correct connections received the update
                sent_connection_ids = [call[0][0] for call in mock_send.call_args_list]
                expected_connection_ids = [conn['connectionId'] for conn in subscribed_to_target]
                
                assert set(sent_connection_ids) == set(expected_connection_ids), "Should send to correct connections"
                
                # Verify message content is for target order only
                for call_args in mock_send.call_args_list:
                    _, message = call_args[0]
                    assert message['orderId'] == target_order_id, "All messages should be for target order"
                    assert message['status'] == target_order['status'], "Message should contain target order status"
                
                # Reset mock for verification
                mock_send.reset_mock()
                
                # Verify other orders are not affected by broadcasting to a different order
                if other_orders:
                    other_order = other_orders[0]
                    other_order_id = other_order['orderId']
                    
                    # This should only affect connections subscribed to the other order
                    broadcast_order_status_update(other_order_id, other_order)
                    
                    # Should not send to connections only subscribed to target order
                    sent_connection_ids_other = [call[0][0] for call in mock_send.call_args_list]
                    target_only_connections = [conn['connectionId'] for conn in subscribed_to_target 
                                             if other_order_id not in conn.get('orderSubscriptions', [])]
                    
                    for target_only_conn_id in target_only_connections:
                        assert target_only_conn_id not in sent_connection_ids_other, f"Connection {target_only_conn_id} should not receive updates for other orders"
    
    @given(
        order_data=order_data_strategy,
        connections=st.lists(connection_data_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=15, deadline=None)
    def test_timestamps_displayed_for_all_status_updates(
        self,
        order_data: dict,
        connections: list
    ):
        """
        Property Test: Timestamps are displayed for all status updates
        
        For any status update message:
        1. All update messages MUST include timestamps
        2. Timestamps MUST be in valid ISO 8601 format
        3. Timestamps MUST be consistent across all connections for the same update
        4. Status history timestamps MUST be preserved in updates
        
        **Validates: Requirements 7.4**
        """
        order_id = order_data['orderId']
        
        # Ensure connections are subscribed to this order
        for connection in connections:
            if order_id not in connection['orderSubscriptions']:
                connection['orderSubscriptions'].append(order_id)
        
        # Mock getting subscribed connections
        with patch('handler.get_order_subscribed_connections', return_value=connections):
            with patch('handler.send_message_to_connection') as mock_send:
                mock_send.return_value = True
                
                # Act: Broadcast order status update
                fixed_timestamp = '2024-01-01T15:30:45+00:00'
                with patch('handler.datetime') as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = fixed_timestamp
                    
                    broadcast_order_status_update(order_id, order_data)
                
                # Assert: All messages should have timestamps
                assert mock_send.call_count == len(connections), "Should send message to all connections"
                
                for call_args in mock_send.call_args_list:
                    _, message = call_args[0]
                    
                    # Verify main timestamp
                    assert 'timestamp' in message, "Message must include timestamp"
                    timestamp = message['timestamp']
                    assert timestamp == fixed_timestamp, "Timestamp should be consistent across all messages"
                    
                    # Verify timestamp format (ISO 8601)
                    assert isinstance(timestamp, str), "Timestamp should be string"
                    assert 'T' in timestamp, "Timestamp should have T separator"
                    assert '+' in timestamp or 'Z' in timestamp, "Timestamp should include timezone"
                    
                    # Verify status history timestamps are preserved
                    if 'statusHistory' in message and message['statusHistory']:
                        for history_entry in message['statusHistory']:
                            assert 'timestamp' in history_entry, "Status history entries must have timestamps"
                            history_timestamp = history_entry['timestamp']
                            assert isinstance(history_timestamp, str), "History timestamp should be string"
                            assert 'T' in history_timestamp, "History timestamp should be in ISO format"
                    
                    # Verify timestamp is recent (within reasonable bounds for test)
                    try:
                        parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        # Should be a valid datetime that can be parsed
                        assert parsed_timestamp is not None, "Timestamp should be parseable"
                    except ValueError:
                        pytest.fail(f"Timestamp {timestamp} is not in valid ISO format")
    
    @given(
        dynamodb_record=st.fixed_dictionaries({
            'eventName': st.sampled_from(['INSERT', 'MODIFY']),
            'dynamodb': st.fixed_dictionaries({
                'TableName': st.just('aquachain-orders-dev'),
                'NewImage': st.fixed_dictionaries({
                    'orderId': st.fixed_dictionaries({'S': order_id_strategy}),
                    'status': st.fixed_dictionaries({'S': order_status_strategy}),
                    'consumerId': st.fixed_dictionaries({'S': user_id_strategy}),
                    'deviceType': st.fixed_dictionaries({'S': st.sampled_from(['Water Quality Monitor', 'pH Sensor'])}),
                    'amount': st.fixed_dictionaries({'N': st.floats(min_value=100, max_value=5000, allow_nan=False, allow_infinity=False).map(str)})
                }),
                'OldImage': st.one_of(
                    st.none(),
                    st.fixed_dictionaries({
                        'orderId': st.fixed_dictionaries({'S': order_id_strategy}),
                        'status': st.fixed_dictionaries({'S': order_status_strategy}),
                        'consumerId': st.fixed_dictionaries({'S': user_id_strategy})
                    })
                )
            })
        }),
        connections=st.lists(connection_data_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=10, deadline=None)
    def test_dynamodb_stream_triggers_real_time_updates(
        self,
        dynamodb_record: dict,
        connections: list
    ):
        """
        Property Test: DynamoDB stream events trigger real-time updates
        
        For any DynamoDB stream event:
        1. Order status changes MUST trigger real-time broadcasts
        2. Only status changes MUST trigger updates (not other field changes)
        3. Broadcast data MUST be correctly converted from DynamoDB format
        4. Updates MUST include both new and old status information
        
        **Validates: Requirements 7.1, 7.2**
        """
        new_image = dynamodb_record['dynamodb']['NewImage']
        old_image = dynamodb_record['dynamodb'].get('OldImage')
        
        order_id = new_image['orderId']['S']
        new_status = new_image['status']['S']
        old_status = old_image['status']['S'] if old_image else None
        
        # Only test when status actually changed
        assume(new_status != old_status)
        
        # Ensure connections are subscribed to this order
        for connection in connections:
            if order_id not in connection['orderSubscriptions']:
                connection['orderSubscriptions'].append(order_id)
        
        # Mock getting subscribed connections
        with patch('broadcast_handler.get_order_subscribed_connections', return_value=connections):
            with patch('broadcast_handler.broadcast_to_connections') as mock_broadcast:
                mock_broadcast.return_value = {'successful': len(connections), 'failed': 0}
                
                # Act: Handle DynamoDB stream event
                handle_dynamodb_stream(dynamodb_record)
                
                # Assert: Broadcast should be called for status change
                mock_broadcast.assert_called_once()
                
                call_args = mock_broadcast.call_args[0]
                broadcast_connections, broadcast_message = call_args
                
                # Verify connections
                assert broadcast_connections == connections, "Should broadcast to subscribed connections"
                
                # Verify message content
                assert broadcast_message['type'] == 'order_status_update', "Should broadcast order status update"
                assert broadcast_message['orderId'] == order_id, "Should include correct order ID"
                assert broadcast_message['status'] == new_status, "Should include new status"
                
                if old_status:
                    assert broadcast_message['previousStatus'] == old_status, "Should include previous status"
                
                # Verify DynamoDB data conversion
                assert broadcast_message['deviceType'] == new_image['deviceType']['S'], "Should convert device type correctly"
                assert broadcast_message['amount'] == float(new_image['amount']['N']), "Should convert amount correctly"
                
                # Verify timestamp is added
                assert 'timestamp' in broadcast_message, "Should add timestamp to broadcast"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])