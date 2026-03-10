"""
Unit tests for device management Lambda handler
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock AWS services before importing handler
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))


@pytest.fixture
def mock_aws_services():
    """Mock AWS services"""
    with patch('handler.dynamodb') as mock_dynamodb, \
         patch('handler.iot_client') as mock_iot:
        yield {
            'dynamodb': mock_dynamodb,
            'iot_client': mock_iot
        }


@pytest.fixture
def sample_event():
    """Sample API Gateway event"""
    return {
        'httpMethod': 'POST',
        'path': '/devices/register',
        'body': json.dumps({
            'deviceId': 'AQ-001',
            'deviceName': 'Kitchen Monitor',
            'location': 'Kitchen',
            'waterSourceType': 'household'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'user-123'
                }
            }
        }
    }


@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = Mock()
    context.request_id = 'test-request-id'
    context.function_name = 'test-function'
    return context


class TestDeviceRegistration:
    """Test device registration endpoint"""
    
    def test_successful_registration(self, mock_aws_services, sample_event, mock_context):
        """Test successful device registration"""
        from handler import register_device
        
        # Mock IoT Core response
        mock_aws_services['iot_client'].describe_thing.return_value = {
            'thingName': 'AQ-001',
            'thingArn': 'arn:aws:iot:region:account:thing/AQ-001'
        }
        
        # Mock DynamoDB responses
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': None}  # Device not registered
        mock_table.put_item.return_value = {}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Device registered successfully'
        assert body['device']['deviceId'] == 'AQ-001'
        assert body['device']['userId'] == 'user-123'
        
        # Verify DynamoDB put_item called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['device_id'] == 'AQ-001'
        assert call_args['user_id'] == 'user-123'
    
    def test_invalid_device_id_format(self, mock_aws_services, sample_event, mock_context):
        """Test registration with invalid device ID format"""
        from handler import register_device
        
        # Invalid device ID
        body = json.loads(sample_event['body'])
        body['deviceId'] = 'INVALID-123'
        sample_event['body'] = json.dumps(body)
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid device ID format' in body['error']
    
    def test_valid_esp_format(self, mock_aws_services, sample_event, mock_context):
        """Test registration with ESP-XXX format"""
        from handler import register_device
        
        # Valid ESP format
        body = json.loads(sample_event['body'])
        body['deviceId'] = 'ESP-001'
        sample_event['body'] = json.dumps(body)
        
        # Mock IoT Core response
        mock_aws_services['iot_client'].describe_thing.return_value = {
            'thingName': 'ESP-001'
        }
        
        # Mock DynamoDB responses
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': None}
        mock_table.put_item.return_value = {}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['device']['deviceId'] == 'ESP-001'
    
    def test_device_not_in_iot_core(self, mock_aws_services, sample_event, mock_context):
        """Test registration when device doesn't exist in IoT Core"""
        from handler import register_device
        from botocore.exceptions import ClientError
        
        # Mock IoT Core error
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        mock_aws_services['iot_client'].describe_thing.side_effect = ClientError(
            error_response, 'DescribeThing'
        )
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found in IoT registry' in body['error']
    
    def test_device_already_registered_to_same_user(self, mock_aws_services, sample_event, mock_context):
        """Test registration when device already registered to same user"""
        from handler import register_device
        
        # Mock IoT Core response
        mock_aws_services['iot_client'].describe_thing.return_value = {
            'thingName': 'AQ-001'
        }
        
        # Mock DynamoDB - device already exists
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'device_id': 'AQ-001',
                'user_id': 'user-123'  # Same user
            }
        }
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert 'already registered to your account' in body['error']
    
    def test_device_hijacking_prevention(self, mock_aws_services, sample_event, mock_context):
        """Test prevention of device hijacking"""
        from handler import register_device
        
        # Mock IoT Core response
        mock_aws_services['iot_client'].describe_thing.return_value = {
            'thingName': 'AQ-001'
        }
        
        # Mock DynamoDB - device registered to different user
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'device_id': 'AQ-001',
                'user_id': 'different-user'  # Different user
            }
        }
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert 'already registered to another user' in body['error']
    
    def test_missing_device_id(self, mock_aws_services, sample_event, mock_context):
        """Test registration without device ID"""
        from handler import register_device
        
        # Remove deviceId
        body = json.loads(sample_event['body'])
        del body['deviceId']
        sample_event['body'] = json.dumps(body)
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing deviceId' in body['error']
    
    def test_accepts_both_camelcase_and_snakecase(self, mock_aws_services, sample_event, mock_context):
        """Test that handler accepts both camelCase and snake_case"""
        from handler import register_device
        
        # Use snake_case in request
        body = {
            'device_id': 'AQ-002',
            'name': 'Test Device',
            'location': 'Bathroom',
            'water_source_type': 'household'
        }
        sample_event['body'] = json.dumps(body)
        
        # Mock responses
        mock_aws_services['iot_client'].describe_thing.return_value = {
            'thingName': 'AQ-002'
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': None}
        mock_table.put_item.return_value = {}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = register_device(sample_event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['device']['deviceId'] == 'AQ-002'


class TestDeviceListing:
    """Test device listing endpoint"""
    
    def test_list_devices_success(self, mock_aws_services, mock_context):
        """Test successful device listing"""
        from handler import list_devices
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices',
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [
                {
                    'device_id': 'AQ-001',
                    'user_id': 'user-123',
                    'device_name': 'Kitchen Monitor',
                    'location': 'Kitchen',
                    'water_source_type': 'household',
                    'status': 'active',
                    'created_at': '2026-03-09T10:00:00Z'
                },
                {
                    'device_id': 'AQ-002',
                    'user_id': 'user-123',
                    'device_name': 'Bathroom Monitor',
                    'location': 'Bathroom',
                    'water_source_type': 'household',
                    'status': 'active',
                    'created_at': '2026-03-09T11:00:00Z'
                }
            ]
        }
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = list_devices(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['devices']) == 2
        assert body['devices'][0]['deviceId'] == 'AQ-001'
        assert body['devices'][1]['deviceId'] == 'AQ-002'
    
    def test_list_devices_empty(self, mock_aws_services, mock_context):
        """Test listing when user has no devices"""
        from handler import list_devices
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices',
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock empty response
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': []}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = list_devices(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        assert body['devices'] == []
    
    def test_list_devices_unauthorized(self, mock_aws_services, mock_context):
        """Test listing without authentication"""
        from handler import list_devices
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices',
            'requestContext': {}
        }
        
        # Execute
        response = list_devices(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'Unauthorized' in body['error']


class TestDeviceRetrieval:
    """Test get device endpoint"""
    
    def test_get_device_success(self, mock_aws_services, mock_context):
        """Test successful device retrieval"""
        from handler import get_device
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices/AQ-001',
            'pathParameters': {'deviceId': 'AQ-001'},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'device_id': 'AQ-001',
                'user_id': 'user-123',
                'device_name': 'Kitchen Monitor',
                'location': 'Kitchen',
                'water_source_type': 'household',
                'status': 'active'
            }
        }
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = get_device(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['device']['deviceId'] == 'AQ-001'
    
    def test_get_device_not_found(self, mock_aws_services, mock_context):
        """Test getting non-existent device"""
        from handler import get_device
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices/AQ-999',
            'pathParameters': {'deviceId': 'AQ-999'},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock empty response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = get_device(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 404
    
    def test_get_device_access_denied(self, mock_aws_services, mock_context):
        """Test getting device owned by another user"""
        from handler import get_device
        
        event = {
            'httpMethod': 'GET',
            'path': '/devices/AQ-001',
            'pathParameters': {'deviceId': 'AQ-001'},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock device owned by different user
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'device_id': 'AQ-001',
                'user_id': 'different-user'
            }
        }
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = get_device(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert 'Access denied' in body['error']


class TestDeviceDeletion:
    """Test delete device endpoint"""
    
    def test_delete_device_success(self, mock_aws_services, mock_context):
        """Test successful device unpair"""
        from handler import delete_device
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/devices/AQ-001',
            'pathParameters': {'deviceId': 'AQ-001'},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        # Mock DynamoDB responses
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'device_id': 'AQ-001',
                'user_id': 'user-123'
            }
        }
        mock_table.update_item.return_value = {}
        mock_aws_services['dynamodb'].Table.return_value = mock_table
        
        # Execute
        response = delete_device(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'unpaired successfully' in body['message']
        
        # Verify update_item called
        mock_table.update_item.assert_called_once()


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_user_id_from_event(self):
        """Test user ID extraction from event"""
        from handler import get_user_id_from_event
        
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        user_id = get_user_id_from_event(event)
        assert user_id == 'user-123'
    
    def test_get_user_id_missing(self):
        """Test user ID extraction when missing"""
        from handler import get_user_id_from_event
        
        event = {'requestContext': {}}
        user_id = get_user_id_from_event(event)
        assert user_id == ''
    
    def test_create_response(self):
        """Test response creation"""
        from handler import create_response
        
        response = create_response(200, {'message': 'Success'})
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        body = json.loads(response['body'])
        assert body['message'] == 'Success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
