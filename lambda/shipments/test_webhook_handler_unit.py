"""
Unit tests for webhook_handler Lambda function
Requirements: 2.1, 2.2, 2.3, 2.6

Tests cover:
- Signature verification (valid and invalid)
- Payload normalization for all couriers (Delhivery, BlueDart, DTDC)
- State transition validation
- Idempotency handling
- Status-specific handlers (delivery confirmation, failure, out for delivery)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any

# Import functions from webhook_handler
from webhook_handler import (
    normalize_webhook_payload,
    map_courier_status,
    is_valid_transition,
    generate_event_id,
    is_duplicate_webhook,
    VALID_TRANSITIONS
)


class TestPayloadNormalization:
    """
    Test courier payload normalization
    Requirements: 2.2
    """
    
    def test_delhivery_payload_normalization(self):
        """Test Delhivery webhook payload normalization"""
        payload = {
            'waybill': 'DELHUB123456789',
            'Status': 'In Transit',
            'Scans': [{
                'ScanDetail': {
                    'ScanDateTime': '2025-12-29T18:00:00Z',
                    'ScannedLocation': 'Pune Hub',
                    'Instructions': 'Package in transit'
                }
            }]
        }
        
        result = normalize_webhook_payload('delhivery', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'DELHUB123456789'
        assert result['status'] == 'In Transit'
        assert result['location'] == 'Pune Hub'
        assert result['timestamp'] == '2025-12-29T18:00:00Z'
        assert result['description'] == 'Package in transit'
    
    def test_delhivery_missing_waybill(self):
        """Test Delhivery payload with missing waybill"""
        payload = {'Status': 'In Transit', 'Scans': []}
        result = normalize_webhook_payload('delhivery', payload)
        assert result is None
    
    def test_delhivery_missing_status(self):
        """Test Delhivery payload with missing status"""
        payload = {'waybill': 'DELHUB123456789', 'Scans': []}
        result = normalize_webhook_payload('delhivery', payload)
        assert result is None
    
    def test_bluedart_payload_normalization(self):
        """Test BlueDart webhook payload normalization"""
        payload = {
            'awb_number': 'BD987654321',
            'status': 'IN TRANSIT',
            'status_date': '2025-12-29T15:30:00Z',
            'current_location': 'Mumbai Hub',
            'status_description': 'Shipment in transit'
        }
        
        result = normalize_webhook_payload('bluedart', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'BD987654321'
        assert result['status'] == 'IN TRANSIT'
        assert result['location'] == 'Mumbai Hub'
    
    def test_dtdc_payload_normalization(self):
        """Test DTDC webhook payload normalization"""
        payload = {
            'reference_number': 'DTDC555666777',
            'shipment_status': 'IN-TRANSIT',
            'timestamp': '2025-12-29T12:00:00Z',
            'location': 'Delhi Hub',
            'remarks': 'Package moving to destination'
        }
        
        result = normalize_webhook_payload('dtdc', payload)
        
        assert result is not None
        assert result['tracking_number'] == 'DTDC555666777'
        assert result['status'] == 'IN-TRANSIT'
    
    def test_invalid_payload_type(self):
        """Test normalization with invalid payload type"""
        assert normalize_webhook_payload('delhivery', None) is None
        assert normalize_webhook_payload('delhivery', "not a dict") is None


class TestCourierStatusMapping:
    """
    Test courier status mapping to internal status
    Requirements: 2.2
    """
    
    def test_delhivery_status_mapping(self):
        """Test Delhivery status codes map correctly"""
        assert map_courier_status('Picked Up') == 'picked_up'
        assert map_courier_status('In Transit') == 'in_transit'
        assert map_courier_status('Out for Delivery') == 'out_for_delivery'
        assert map_courier_status('Delivered') == 'delivered'
        assert map_courier_status('Delivery Failed') == 'delivery_failed'
    
    def test_bluedart_status_mapping(self):
        """Test BlueDart status codes map correctly"""
        assert map_courier_status('MANIFESTED') == 'picked_up'
        assert map_courier_status('IN TRANSIT') == 'in_transit'
        assert map_courier_status('DELIVERED') == 'delivered'
    
    def test_dtdc_status_mapping(self):
        """Test DTDC status codes map correctly"""
        assert map_courier_status('BOOKED') == 'shipment_created'
        assert map_courier_status('PICKED') == 'picked_up'
        assert map_courier_status('DELIVERED') == 'delivered'
    
    def test_case_insensitive_mapping(self):
        """Test status mapping is case-insensitive"""
        assert map_courier_status('delivered') == 'delivered'
        assert map_courier_status('DELIVERED') == 'delivered'
    
    def test_unknown_status_defaults_to_in_transit(self):
        """Test unknown status defaults to in_transit"""
        assert map_courier_status('UNKNOWN_STATUS') == 'in_transit'


class TestStateTransitionValidation:
    """
    Test state transition validation
    Requirements: 2.3
    """
    
    def test_valid_transitions(self):
        """Test all valid state transitions"""
        assert is_valid_transition('shipment_created', 'picked_up') is True
        assert is_valid_transition('picked_up', 'in_transit') is True
        assert is_valid_transition('in_transit', 'out_for_delivery') is True
        assert is_valid_transition('out_for_delivery', 'delivered') is True
    
    def test_invalid_transitions(self):
        """Test invalid state transitions"""
        assert is_valid_transition('delivered', 'in_transit') is False
        assert is_valid_transition('returned', 'delivered') is False
        assert is_valid_transition('shipment_created', 'delivered') is False
    
    def test_same_status_transition_allowed(self):
        """Test that same-status transitions are allowed (idempotent)"""
        assert is_valid_transition('in_transit', 'in_transit') is True


class TestIdempotencyHandling:
    """
    Test webhook idempotency handling
    Requirements: 2.6
    """
    
    def test_generate_event_id_deterministic(self):
        """Test that event_id generation is deterministic"""
        tracking = 'TRACK123'
        timestamp = '2025-12-29T12:00:00Z'
        status = 'in_transit'
        
        event_id1 = generate_event_id(tracking, timestamp, status)
        event_id2 = generate_event_id(tracking, timestamp, status)
        
        assert event_id1 == event_id2
        assert event_id1.startswith('evt_')
    
    def test_generate_event_id_unique_for_different_inputs(self):
        """Test that different inputs produce different event_ids"""
        event_id1 = generate_event_id('TRACK123', '2025-12-29T12:00:00Z', 'in_transit')
        event_id2 = generate_event_id('TRACK456', '2025-12-29T12:00:00Z', 'in_transit')
        
        assert event_id1 != event_id2
    
    def test_is_duplicate_webhook_detects_duplicate(self):
        """Test that duplicate webhooks are detected"""
        shipment = {
            'webhook_events': [
                {'event_id': 'evt_abc123'},
                {'event_id': 'evt_def456'}
            ]
        }
        
        assert is_duplicate_webhook(shipment, 'evt_abc123') is True
    
    def test_is_duplicate_webhook_allows_new_event(self):
        """Test that new events are not marked as duplicates"""
        shipment = {'webhook_events': [{'event_id': 'evt_abc123'}]}
        assert is_duplicate_webhook(shipment, 'evt_xyz789') is False


class TestSignatureVerification:
    """
    Test webhook signature verification
    Requirements: 2.1, 10.1, 10.2
    """
    
    @patch('webhook_handler.WEBHOOK_SECRET', 'test-secret')
    def test_valid_signature_accepted(self):
        """Test that valid HMAC-SHA256 signature is accepted"""
        from webhook_handler import verify_webhook_signature
        
        payload = json.dumps({'test': 'data'})
        secret = 'test-secret'
        
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'headers': {'X-Webhook-Signature': signature},
            'body': payload
        }
        
        result = verify_webhook_signature(event)
        assert result is True
    
    def test_missing_signature_rejected(self):
        """Test that missing signature is rejected"""
        from webhook_handler import verify_webhook_signature
        
        event = {
            'headers': {},
            'body': json.dumps({'test': 'data'})
        }
        
        result = verify_webhook_signature(event)
        assert result is False


class TestStatusSpecificHandlers:
    """
    Test status-specific handler functions
    Requirements: 4.1, 6.1, 13.2, 13.3
    """
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    @patch('webhook_handler.sns')
    def test_handle_delivery_confirmation_sends_notification(self, mock_sns):
        """Test delivery confirmation sends notifications"""
        from webhook_handler import handle_delivery_confirmation
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'delivered_at': '2025-12-29T18:00:00Z'
        }
        
        handle_delivery_confirmation(shipment)
        
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        
        assert call_args[1]['TopicArn'] == 'arn:aws:sns:test'
        assert 'Device Delivered' in call_args[1]['Subject']
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    @patch('webhook_handler.SHIPMENTS_TABLE', 'test-table')
    @patch('webhook_handler.dynamodb')
    @patch('webhook_handler.sns')
    def test_handle_delivery_failure_increments_retry(self, mock_sns, mock_dynamodb):
        """Test delivery failure increments retry counter"""
        from webhook_handler import handle_delivery_failure
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'retry_config': {'retry_count': 1, 'max_retries': 3}
        }
        
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        handle_delivery_failure(shipment)
        
        mock_table.update_item.assert_called_once()
    
    @patch('webhook_handler.SNS_TOPIC_ARN', 'arn:aws:sns:test')
    @patch('webhook_handler.sns')
    def test_handle_out_for_delivery_sends_notification(self, mock_sns):
        """Test out for delivery sends notifications"""
        from webhook_handler import handle_out_for_delivery
        
        shipment = {
            'shipment_id': 'ship_123',
            'order_id': 'ord_456',
            'tracking_number': 'TRACK789',
            'estimated_delivery': '2025-12-30T18:00:00Z'
        }
        
        handle_out_for_delivery(shipment)
        
        mock_sns.publish.assert_called_once()


class TestWebhookHandlerIntegration:
    """
    Test the main webhook handler function
    Requirements: 2.1, 2.2, 2.3, 2.6
    """
    
    @patch('webhook_handler.WEBHOOK_SECRET', 'test-secret')
    @patch('webhook_handler.handle_delivery_confirmation')
    @patch('webhook_handler.update_shipment')
    @patch('webhook_handler.lookup_shipment_by_tracking')
    def test_handler_processes_valid_webhook(self, mock_lookup, mock_update, mock_handle_delivery):
        """Test handler processes valid webhook successfully"""
        from webhook_handler import handler
        
        payload = {
            'waybill': 'TRACK123',
            'Status': 'Delivered',
            'Scans': [{
                'ScanDetail': {
                    'ScanDateTime': '2025-12-29T18:00:00Z',
                    'ScannedLocation': 'Customer Location',
                    'Instructions': 'Delivered successfully'
                }
            }]
        }
        
        secret = 'test-secret'
        body = json.dumps(payload)
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        
        event = {
            'headers': {'X-Webhook-Signature': signature},
            'body': body,
            'pathParameters': {'courier': 'delhivery'}
        }
        
        mock_lookup.return_value = {
            'shipment_id': 'ship_123',
            'internal_status': 'out_for_delivery',
            'webhook_events': []
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 200
        mock_update.assert_called_once()
        mock_handle_delivery.assert_called_once()
    
    def test_handler_rejects_invalid_signature(self):
        """Test handler rejects webhook with invalid signature"""
        from webhook_handler import handler
        
        payload = {'waybill': 'TRACK123', 'Status': 'Delivered'}
        
        event = {
            'headers': {'X-Webhook-Signature': 'invalid_signature'},
            'body': json.dumps(payload),
            'pathParameters': {'courier': 'delhivery'}
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 401
    
    @patch('webhook_handler.WEBHOOK_SECRET', 'test-secret')
    @patch('webhook_handler.lookup_shipment_by_tracking')
    def test_handler_returns_404_for_unknown_shipment(self, mock_lookup):
        """Test handler returns 404 when shipment not found"""
        from webhook_handler import handler
        
        payload = {
            'waybill': 'UNKNOWN_TRACKING',
            'Status': 'In Transit',
            'Scans': []
        }
        
        secret = 'test-secret'
        body = json.dumps(payload)
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        
        event = {
            'headers': {'X-Webhook-Signature': signature},
            'body': body,
            'pathParameters': {'courier': 'delhivery'}
        }
        
        mock_lookup.return_value = None
        
        response = handler(event, None)
        
        assert response['statusCode'] == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
