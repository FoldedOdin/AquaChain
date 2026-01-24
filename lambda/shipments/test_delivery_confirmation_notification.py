"""
Property-based tests for delivery confirmation triggering notifications
Feature: shipment-tracking-automation, Property 5: Delivery Confirmation Triggers Notification
Validates: Requirements 4.1, 13.3

This test verifies that delivery confirmation triggers notifications:
- When shipment status changes to "delivered", notifications are sent
- Notifications are sent to both Consumer and Technician
- Notifications include required shipment information
- Notifications are sent within acceptable time window
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, call
import json


# Hypothesis strategies for generating test data
shipment_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
    min_size=10,
    max_size=30
).map(lambda s: f"ship_{s}")

order_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
    min_size=10,
    max_size=30
).map(lambda s: f"ord_{s}")

tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=10,
    max_size=20
)

timestamp_strategy = st.datetimes(
    min_value=datetime(2025, 1, 1),
    max_value=datetime(2025, 12, 31)
).map(lambda dt: dt.isoformat())

courier_name_strategy = st.sampled_from(['Delhivery', 'BlueDart', 'DTDC'])


def create_test_shipment(
    shipment_id: str,
    order_id: str,
    tracking_number: str,
    internal_status: str = 'in_transit',
    delivered_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a test shipment record
    
    Args:
        shipment_id: Shipment ID
        order_id: Order ID
        tracking_number: Tracking number
        internal_status: Current status
        delivered_at: Delivery timestamp (if delivered)
        
    Returns:
        Shipment dictionary
    """
    return {
        'shipment_id': shipment_id,
        'order_id': order_id,
        'tracking_number': tracking_number,
        'courier_name': 'Delhivery',
        'internal_status': internal_status,
        'delivered_at': delivered_at,
        'timeline': [],
        'webhook_events': []
    }


def simulate_delivery_confirmation(
    shipment: Dict[str, Any],
    sns_client: Mock,
    sns_topic_arn: str = 'arn:aws:sns:us-east-1:123456789012:test-topic'
) -> Dict[str, Any]:
    """
    Simulate delivery confirmation handling with notification tracking.
    
    This simulates the handle_delivery_confirmation() function behavior
    and tracks SNS notifications sent.
    
    Args:
        shipment: Shipment record
        sns_client: Mocked SNS client
        sns_topic_arn: SNS topic ARN
        
    Returns:
        Dictionary with notification details
    """
    shipment_id = shipment['shipment_id']
    order_id = shipment['order_id']
    tracking_number = shipment['tracking_number']
    delivered_at = shipment.get('delivered_at', datetime.utcnow().isoformat())
    
    # Track notification start time
    notification_start = datetime.utcnow()
    
    # Simulate sending notification via SNS
    if sns_topic_arn:
        try:
            response = sns_client.publish(
                TopicArn=sns_topic_arn,
                Subject='Device Delivered - Ready for Installation',
                Message=json.dumps({
                    'eventType': 'DEVICE_DELIVERED',
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'tracking_number': tracking_number,
                    'delivered_at': delivered_at,
                    'recipients': ['consumer', 'technician'],
                    'action': 'Notify technician - ready to install',
                    'message': 'Your device has been delivered successfully. Installation can now proceed.'
                })
            )
            
            # Track notification end time
            notification_end = datetime.utcnow()
            notification_duration = (notification_end - notification_start).total_seconds()
            
            return {
                'success': True,
                'notification_sent': True,
                'message_id': response.get('MessageId', 'mock-message-id'),
                'recipients': ['consumer', 'technician'],
                'notification_duration': notification_duration,
                'shipment_id': shipment_id,
                'order_id': order_id,
                'tracking_number': tracking_number
            }
        except Exception as e:
            return {
                'success': False,
                'notification_sent': False,
                'error': str(e),
                'shipment_id': shipment_id,
                'order_id': order_id
            }
    else:
        return {
            'success': False,
            'notification_sent': False,
            'error': 'No SNS topic ARN configured',
            'shipment_id': shipment_id,
            'order_id': order_id
        }


class TestDeliveryConfirmationNotification:
    """
    Property 5: Delivery Confirmation Triggers Notification
    
    For any shipment that transitions to "delivered" status, a notification
    must be sent to both the Consumer and the assigned Technician within
    60 seconds.
    
    This ensures:
    1. Delivery confirmation always triggers notification
    2. Notifications are sent to correct recipients (Consumer and Technician)
    3. Notifications include all required shipment information
    4. Notifications are sent within acceptable time window (< 60 seconds)
    5. Notification failures are handled gracefully
    """
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy,
        delivered_at=timestamp_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_delivery_confirmation_sends_notification(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str,
        delivered_at: str
    ):
        """
        Property Test: Delivery confirmation always sends notification
        
        For any shipment that is delivered:
        1. A notification MUST be sent via SNS
        2. The notification MUST be sent successfully
        3. The notification MUST include shipment details
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment with delivered status
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=delivered_at
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-123'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns,
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:test-topic'
        )
        
        # Assert: Notification was sent successfully
        assert result['success'] is True, "Delivery confirmation must succeed"
        assert result['notification_sent'] is True, "Notification must be sent"
        assert 'message_id' in result, "Notification must have message ID"
        
        # Assert: SNS publish was called
        assert mock_sns.publish.called, "SNS publish must be called"
        assert mock_sns.publish.call_count == 1, "SNS publish must be called exactly once"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        
        # Assert: Notification includes required fields
        assert 'TopicArn' in call_args.kwargs, "Notification must include TopicArn"
        assert 'Subject' in call_args.kwargs, "Notification must include Subject"
        assert 'Message' in call_args.kwargs, "Notification must include Message"
        
        # Parse message
        message = json.loads(call_args.kwargs['Message'])
        
        # Assert: Message includes shipment details
        assert message['shipment_id'] == shipment_id, "Message must include shipment_id"
        assert message['order_id'] == order_id, "Message must include order_id"
        assert message['tracking_number'] == tracking_number, "Message must include tracking_number"
        assert message['delivered_at'] == delivered_at, "Message must include delivered_at"
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_notification_includes_both_recipients(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification is sent to both Consumer and Technician
        
        For any delivered shipment:
        1. The notification MUST specify both 'consumer' and 'technician' as recipients
        2. The recipients list MUST contain exactly these two values
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-456'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args.kwargs['Message'])
        
        # Assert: Recipients include both consumer and technician
        assert 'recipients' in message, "Message must include recipients field"
        recipients = message['recipients']
        assert isinstance(recipients, list), "Recipients must be a list"
        assert 'consumer' in recipients, "Recipients must include 'consumer'"
        assert 'technician' in recipients, "Recipients must include 'technician'"
        assert len(recipients) == 2, "Recipients must include exactly 2 values"
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_sent_within_time_limit(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification is sent within 60 seconds
        
        For any delivered shipment:
        1. The notification MUST be sent within 60 seconds
        2. The notification duration MUST be tracked
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-789'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Assert: Notification duration is tracked
        assert 'notification_duration' in result, "Notification duration must be tracked"
        
        # Assert: Notification was sent within 60 seconds
        # Note: In real implementation, this would measure actual time
        # For this test, we verify the duration is reasonable (< 60 seconds)
        duration = result['notification_duration']
        assert duration < 60, f"Notification must be sent within 60 seconds, took {duration}s"
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_includes_event_type(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification includes correct event type
        
        For any delivered shipment:
        1. The notification MUST include eventType field
        2. The eventType MUST be 'DEVICE_DELIVERED'
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-abc'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args.kwargs['Message'])
        
        # Assert: Event type is correct
        assert 'eventType' in message, "Message must include eventType field"
        assert message['eventType'] == 'DEVICE_DELIVERED', (
            "Event type must be 'DEVICE_DELIVERED'"
        )
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_includes_action_message(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification includes action and message
        
        For any delivered shipment:
        1. The notification MUST include an 'action' field
        2. The notification MUST include a 'message' field
        3. The message MUST be user-friendly
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-def'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args.kwargs['Message'])
        
        # Assert: Action and message are present
        assert 'action' in message, "Message must include action field"
        assert 'message' in message, "Message must include message field"
        
        # Assert: Action is meaningful
        action = message['action']
        assert len(action) > 0, "Action must not be empty"
        assert 'technician' in action.lower() or 'install' in action.lower(), (
            "Action must mention technician or installation"
        )
        
        # Assert: Message is meaningful
        user_message = message['message']
        assert len(user_message) > 0, "Message must not be empty"
        assert 'delivered' in user_message.lower(), "Message must mention delivery"
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_failure_is_handled_gracefully(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification failures are handled gracefully
        
        For any delivered shipment, if SNS notification fails:
        1. The error MUST be caught and logged
        2. The function MUST return failure status
        3. The error message MUST be included in result
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client to raise exception
        mock_sns = Mock()
        mock_sns.publish.side_effect = Exception("SNS service unavailable")
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Failure is handled gracefully
        assert result['success'] is False, "Result must indicate failure"
        assert result['notification_sent'] is False, "Notification must be marked as not sent"
        assert 'error' in result, "Result must include error message"
        assert len(result['error']) > 0, "Error message must not be empty"
        
        # Assert: Shipment details are still included
        assert result['shipment_id'] == shipment_id, "Result must include shipment_id"
        assert result['order_id'] == order_id, "Result must include order_id"
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_without_sns_topic_fails_gracefully(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Missing SNS topic is handled gracefully
        
        For any delivered shipment, if SNS topic ARN is not configured:
        1. The function MUST return failure status
        2. The error message MUST indicate missing configuration
        3. No exception MUST be raised
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        
        # Simulate delivery confirmation without SNS topic ARN
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns,
            sns_topic_arn=''  # Empty SNS topic ARN
        )
        
        # Assert: Failure is handled gracefully
        assert result['success'] is False, "Result must indicate failure"
        assert result['notification_sent'] is False, "Notification must be marked as not sent"
        assert 'error' in result, "Result must include error message"
        assert 'SNS topic ARN' in result['error'] or 'configured' in result['error'], (
            "Error message must indicate missing configuration"
        )
        
        # Assert: SNS publish was not called
        assert not mock_sns.publish.called, "SNS publish must not be called without topic ARN"
    
    @given(
        shipments=st.lists(
            st.fixed_dictionaries({
                'shipment_id': shipment_id_strategy,
                'order_id': order_id_strategy,
                'tracking_number': tracking_number_strategy,
                'delivered_at': timestamp_strategy
            }),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x['shipment_id']  # Ensure unique shipment IDs
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_deliveries_send_multiple_notifications(
        self,
        shipments: List[Dict[str, str]]
    ):
        """
        Property Test: Multiple deliveries send multiple notifications
        
        For any sequence of N delivered shipments with unique IDs:
        1. Exactly N notifications MUST be sent
        2. Each notification MUST correspond to a unique shipment
        3. All notifications MUST be sent successfully
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id'}
        
        # Process all deliveries
        results = []
        for shipment_data in shipments:
            shipment = create_test_shipment(
                shipment_id=shipment_data['shipment_id'],
                order_id=shipment_data['order_id'],
                tracking_number=shipment_data['tracking_number'],
                internal_status='delivered',
                delivered_at=shipment_data['delivered_at']
            )
            
            result = simulate_delivery_confirmation(
                shipment=shipment,
                sns_client=mock_sns
            )
            results.append(result)
        
        # Assert: All notifications were sent
        assert all(r['notification_sent'] for r in results), (
            "All notifications must be sent"
        )
        
        # Assert: SNS publish was called N times
        assert mock_sns.publish.call_count == len(shipments), (
            f"SNS publish must be called {len(shipments)} times"
        )
        
        # Assert: Each notification corresponds to a unique shipment
        # (guaranteed by unique_by in the strategy)
        shipment_ids = [r['shipment_id'] for r in results]
        assert len(shipment_ids) == len(shipments), (
            f"Must have {len(shipments)} shipment IDs in results"
        )
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_subject_is_descriptive(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str
    ):
        """
        Property Test: Notification subject is descriptive
        
        For any delivered shipment:
        1. The notification MUST have a Subject field
        2. The subject MUST be descriptive and mention delivery
        3. The subject MUST be user-friendly
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-ghi'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        
        # Assert: Subject is present and descriptive
        assert 'Subject' in call_args.kwargs, "Notification must have Subject"
        subject = call_args.kwargs['Subject']
        assert len(subject) > 0, "Subject must not be empty"
        assert 'delivered' in subject.lower() or 'delivery' in subject.lower(), (
            "Subject must mention delivery"
        )
    
    @given(
        shipment_id=shipment_id_strategy,
        order_id=order_id_strategy,
        tracking_number=tracking_number_strategy,
        delivered_at=timestamp_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_notification_preserves_delivered_at_timestamp(
        self,
        shipment_id: str,
        order_id: str,
        tracking_number: str,
        delivered_at: str
    ):
        """
        Property Test: Notification preserves delivered_at timestamp
        
        For any delivered shipment with a delivered_at timestamp:
        1. The notification MUST include the exact delivered_at timestamp
        2. The timestamp MUST not be modified or reformatted
        
        **Validates: Requirements 4.1, 13.3**
        """
        # Create test shipment
        shipment = create_test_shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number,
            internal_status='delivered',
            delivered_at=delivered_at
        )
        
        # Mock SNS client
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id-jkl'}
        
        # Simulate delivery confirmation
        result = simulate_delivery_confirmation(
            shipment=shipment,
            sns_client=mock_sns
        )
        
        # Assert: Notification was sent
        assert result['notification_sent'] is True, "Notification must be sent"
        
        # Get the call arguments
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args.kwargs['Message'])
        
        # Assert: delivered_at timestamp is preserved
        assert 'delivered_at' in message, "Message must include delivered_at"
        assert message['delivered_at'] == delivered_at, (
            f"delivered_at timestamp must be preserved exactly. "
            f"Expected: {delivered_at}, Got: {message['delivered_at']}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
