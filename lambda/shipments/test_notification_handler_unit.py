"""
Unit tests for notification_handler Lambda function

Tests:
- DynamoDB Stream event parsing
- Email sending via SES
- SMS sending via SNS
- WebSocket message publishing

Requirements: 1.5, 13.1, 13.2, 13.3, 13.4, 13.5
"""
import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import the module under test
import notification_handler


class TestDynamoDBStreamEventParsing(unittest.TestCase):
    """
    Test DynamoDB Stream event parsing
    
    Requirements: 1.5
    """
    
    def test_handler_processes_stream_records(self):
        """Test handler processes all records from stream event"""
        # Setup
        event = {
            'Records': [
                {
                    'eventName': 'INSERT',
                    'dynamodb': {
                        'NewImage': {
                            'shipment_id': {'S': 'ship_001'},
                            'order_id': {'S': 'ord_001'},
                            'internal_status': {'S': 'shipment_created'}
                        }
                    }
                },
                {
                    'eventName': 'MODIFY',
                    'dynamodb': {
                        'OldImage': {
                            'shipment_id': {'S': 'ship_002'},
                            'internal_status': {'S': 'in_transit'}
                        },
                        'NewImage': {
                            'shipment_id': {'S': 'ship_002'},
                            'order_id': {'S': 'ord_002'},
                            'internal_status': {'S': 'delivered'}
                        }
                    }
                }
            ]
        }
        context = Mock(request_id='test-request-123')
        
        with patch('notification_handler.process_stream_record') as mock_process:
            # Execute
            result = notification_handler.handler(event, context)
            
            # Verify
            assert result['statusCode'] == 200
            assert mock_process.call_count == 2
    
    def test_convert_dynamodb_to_dict_handles_string(self):
        """Test conversion of DynamoDB string type"""
        # Setup
        dynamodb_item = {
            'shipment_id': {'S': 'ship_123'},
            'tracking_number': {'S': 'TRACK123'}
        }
        
        # Execute
        result = notification_handler.convert_dynamodb_to_dict(dynamodb_item)
        
        # Verify
        assert result['shipment_id'] == 'ship_123'
        assert result['tracking_number'] == 'TRACK123'
    
    def test_convert_dynamodb_to_dict_handles_number(self):
        """Test conversion of DynamoDB number type"""
        # Setup
        dynamodb_item = {
            'retry_count': {'N': '2'},
            'declared_value': {'N': '5000.50'}
        }
        
        # Execute
        result = notification_handler