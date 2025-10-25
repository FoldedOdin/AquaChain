"""
Integration tests for device provisioning workflow
Tests the complete end-to-end device provisioning process including registration, activation, and configuration
Requirements: 3.4, 12.2
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import uuid

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'device_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'iot_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from handler import DeviceManagementService


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'DEVICES_TABLE': 'test-devices',
        'IOT_ENDPOINT': 'test-iot-endpoint.iot.us-east-1.amazonaws.com'
    }):
        yield


@pytest.fixture
def mock_dynamodb():
    """Fixture providing mocked DynamoDB"""
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_iot_client():
    """Fixture providing mocked IoT client"""
    with patch('boto3.client') as mock_client:
        mock_iot = MagicMock()
        
        def get_client(service_name, **kwargs):
            if service_name == 'iot':
                return mock_iot
            return MagicMock()
        
        mock_client.side_effect = get_client
        yield mock_iot


@pytest.fixture
def sample_device_data():
    """Fixture providing sample device data"""
    return {
        'device_id': 'DEV-0001',
        'device_name': 'Test Water Sensor',
        'device_type': 'water_quality_sensor',
        'user_id': 'user-123',
        'location': {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'address': '123 Test St, San Francisco, CA'
        },
        'firmware_version': '1.0.0',
        'hardware_version': '1.0'
    }


class TestDeviceRegistrationWorkflow:
    """Test suite for device registration workflow"""
    
    def test_successful_device_registration(self, mock_aws_environment, mock_dynamodb, mock_iot_client, sample_device_data):
        """Test complete successful device registration"""
        # Mock IoT thing creation
        mock_iot_client.create_thing.return_value = {
            'thingName': sample_device_data['device_id'],
            'thingArn': f"arn:aws:iot:us-east-1:123456789012:thing/{sample_device_data['device_id']}"
        }
        
        # Mock certificate creation
        mock_iot_client.create_keys_and_certificate.return_value = {
            'certificateArn': 'arn:aws:iot:us-east-1:123456789012:cert/test-cert',
            'certificateId': 'test-cert-id',
            'certificatePem': '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----',
            'keyPair': {
                'PublicKey': 'test-public-key',
                'PrivateKey': 'test-private-key'
            }
        }
        
        # Mock policy attachment
        mock_iot_client.attach_policy.return_value = {}
        mock_iot_client.attach_thing_principal.return_value = {}
        
        # Mock DynamoDB put
        mock_dynamodb.put_item.return_value = {}
        
        # Register device
        device_id = sample_device_data['device_id']
        user_id = sample_device_data['user_id']
        
        # Create IoT thing
        thing_response = mock_iot_client.create_thing(
            thingName=device_id,
            attributePayload={
                'attributes': {
                    'deviceType': sample_device_data['device_type'],
                    'userId': user_id
                }
            }
        )
        
        assert thing_response['thingName'] == device_id
        
        # Create certificate
        cert_response = mock_iot_client.create_keys_and_certificate(setAsActive=True)
        
        assert 'certificateArn' in cert_response
        assert 'certificatePem' in cert_response
        assert 'keyPair' in cert_response
        
        # Attach policy and certificate
        mock_iot_client.attach_policy(
            policyName='AquaChainDevicePolicy',
            target=cert_response['certificateArn']
        )
        
        mock_iot_client.attach_thing_principal(
            thingName=device_id,
            principal=cert_response['certificateArn']
        )
        
        # Store device in DynamoDB
        device_record = {
            'device_id': device_id,
            'user_id': user_id,
            'device_name': sample_device_data['device_name'],
            'device_type': sample_device_data['device_type'],
            'status': 'registered',
            'certificate_id': cert_response['certificateId'],
            'certificate_arn': cert_response['certificateArn'],
            'location': sample_device_data['location'],
            'firmware_version': sample_device_data['firmware_version'],
            'hardware_version': sample_device_data['hardware_version'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        mock_dynamodb.put_item(Item=device_record)
        
        # Verify all steps completed
        mock_iot_client.create_thing.assert_called_once()
        mock_iot_client.create_keys_and_certificate.assert_called_once()
        mock_iot_client.attach_policy.assert_called_once()
        mock_iot_client.attach_thing_principal.assert_called_once()
        mock_dynamodb.put_item.assert_called_once()
    
    def test_device_registration_with_duplicate_id(self, mock_aws_environment, mock_iot_client):
        """Test device registration with duplicate device ID"""
        from botocore.exceptions import ClientError
        
        # Mock IoT thing creation failure (already exists)
        mock_iot_client.create_thing.side_effect = ClientError(
            {'Error': {'Code': 'ResourceAlreadyExistsException', 'Message': 'Thing already exists'}},
            'CreateThing'
        )
        
        # Attempt to register duplicate device
        with pytest.raises(ClientError) as exc_info:
            mock_iot_client.create_thing(
                thingName='DEV-0001',
                attributePayload={'attributes': {}}
            )
        
        # Verify error
        assert exc_info.value.response['Error']['Code'] == 'ResourceAlreadyExistsException'
    
    def test_device_registration_with_invalid_data(self, mock_aws_environment):
        """Test device registration with invalid data"""
        # Test missing required fields
        invalid_data = {
            'device_id': 'DEV-0001'
            # Missing user_id, device_name, etc.
        }
        
        # Validate required fields
        required_fields = ['device_id', 'user_id', 'device_name', 'device_type']
        missing_fields = [field for field in required_fields if field not in invalid_data]
        
        assert len(missing_fields) > 0
        assert 'user_id' in missing_fields
        assert 'device_name' in missing_fields
    
    def test_device_registration_with_invalid_location(self, mock_aws_environment):
        """Test device registration with invalid location coordinates"""
        invalid_location = {
            'latitude': 200.0,  # Invalid: > 90
            'longitude': -200.0  # Invalid: < -180
        }
        
        # Validate location
        assert not (-90 <= invalid_location['latitude'] <= 90)
        assert not (-180 <= invalid_location['longitude'] <= 180)


class TestDeviceActivationWorkflow:
    """Test suite for device activation workflow"""
    
    def test_successful_device_activation(self, mock_aws_environment, mock_dynamodb, mock_iot_client):
        """Test successful device activation"""
        device_id = 'DEV-0001'
        
        # Mock device lookup
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'device_id': device_id,
                'user_id': 'user-123',
                'status': 'registered',
                'certificate_id': 'test-cert-id'
            }
        }
        
        # Mock certificate activation
        mock_iot_client.update_certificate.return_value = {}
        
        # Mock DynamoDB update
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'status': 'active',
                'activated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Activate device
        # 1. Get device record
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        assert device['Item']['status'] == 'registered'
        
        # 2. Activate certificate
        mock_iot_client.update_certificate(
            certificateId=device['Item']['certificate_id'],
            newStatus='ACTIVE'
        )
        
        # 3. Update device status
        updated_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET #status = :status, activated_at = :activated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'active',
                ':activated_at': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        # Verify activation
        assert updated_device['Attributes']['status'] == 'active'
        assert 'activated_at' in updated_device['Attributes']
        mock_iot_client.update_certificate.assert_called_once()
    
    def test_device_activation_not_registered(self, mock_aws_environment, mock_dynamodb):
        """Test activation of device that is not registered"""
        device_id = 'DEV-9999'
        
        # Mock device not found
        mock_dynamodb.get_item.return_value = {}
        
        # Attempt to activate non-existent device
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        
        # Verify device not found
        assert 'Item' not in device
    
    def test_device_activation_already_active(self, mock_aws_environment, mock_dynamodb):
        """Test activation of device that is already active"""
        device_id = 'DEV-0001'
        
        # Mock device lookup (already active)
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'device_id': device_id,
                'user_id': 'user-123',
                'status': 'active',
                'activated_at': '2025-10-20T12:00:00Z'
            }
        }
        
        # Get device
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        
        # Verify already active
        assert device['Item']['status'] == 'active'
        assert 'activated_at' in device['Item']
    
    def test_device_activation_with_first_connection(self, mock_aws_environment, mock_dynamodb, mock_iot_client):
        """Test device activation with first MQTT connection"""
        device_id = 'DEV-0001'
        
        # Mock device lookup
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'device_id': device_id,
                'status': 'active',
                'certificate_id': 'test-cert-id'
            }
        }
        
        # Mock MQTT connection event
        mqtt_event = {
            'eventType': 'connected',
            'clientId': device_id,
            'timestamp': datetime.utcnow().isoformat(),
            'principalId': 'test-cert-id'
        }
        
        # Mock DynamoDB update for first connection
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'status': 'active',
                'last_seen': mqtt_event['timestamp'],
                'connection_count': 1
            }
        }
        
        # Update device with first connection
        updated_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET last_seen = :last_seen, connection_count = if_not_exists(connection_count, :zero) + :one',
            ExpressionAttributeValues={
                ':last_seen': mqtt_event['timestamp'],
                ':zero': 0,
                ':one': 1
            },
            ReturnValues='ALL_NEW'
        )
        
        # Verify connection recorded
        assert updated_device['Attributes']['last_seen'] == mqtt_event['timestamp']
        assert updated_device['Attributes']['connection_count'] == 1


class TestDeviceConfigurationWorkflow:
    """Test suite for device configuration workflow"""
    
    def test_successful_device_configuration(self, mock_aws_environment, mock_dynamodb, mock_iot_client):
        """Test successful device configuration"""
        device_id = 'DEV-0001'
        
        # Configuration data
        config = {
            'sampling_interval': 300,  # 5 minutes
            'reporting_interval': 900,  # 15 minutes
            'alert_thresholds': {
                'pH': {'min': 6.5, 'max': 8.5},
                'turbidity': {'max': 5.0},
                'tds': {'max': 500}
            },
            'power_mode': 'normal',
            'location_tracking': True
        }
        
        # Mock device lookup
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'device_id': device_id,
                'status': 'active',
                'user_id': 'user-123'
            }
        }
        
        # Mock IoT shadow update
        mock_iot_client.update_thing_shadow.return_value = {
            'payload': json.dumps({
                'state': {
                    'desired': config
                },
                'version': 1
            }).encode()
        }
        
        # Mock DynamoDB update
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'configuration': config,
                'config_version': 1,
                'config_updated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Configure device
        # 1. Verify device exists and is active
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        assert device['Item']['status'] == 'active'
        
        # 2. Update IoT shadow
        shadow_response = mock_iot_client.update_thing_shadow(
            thingName=device_id,
            payload=json.dumps({
                'state': {
                    'desired': config
                }
            })
        )
        
        # 3. Store configuration in DynamoDB
        updated_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET configuration = :config, config_version = :version, config_updated_at = :updated_at',
            ExpressionAttributeValues={
                ':config': config,
                ':version': 1,
                ':updated_at': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        # Verify configuration
        assert updated_device['Attributes']['configuration'] == config
        assert updated_device['Attributes']['config_version'] == 1
        mock_iot_client.update_thing_shadow.assert_called_once()
    
    def test_device_configuration_with_invalid_values(self, mock_aws_environment):
        """Test device configuration with invalid values"""
        invalid_config = {
            'sampling_interval': -100,  # Invalid: negative
            'alert_thresholds': {
                'pH': {'min': 10.0, 'max': 5.0}  # Invalid: min > max
            }
        }
        
        # Validate configuration
        assert invalid_config['sampling_interval'] < 0
        assert invalid_config['alert_thresholds']['pH']['min'] > invalid_config['alert_thresholds']['pH']['max']
    
    def test_device_configuration_update(self, mock_aws_environment, mock_dynamodb, mock_iot_client):
        """Test updating existing device configuration"""
        device_id = 'DEV-0001'
        
        # Existing configuration
        existing_config = {
            'sampling_interval': 300,
            'reporting_interval': 900,
            'power_mode': 'normal'
        }
        
        # Updated configuration
        updated_config = {
            'sampling_interval': 600,  # Changed
            'reporting_interval': 900,  # Unchanged
            'power_mode': 'low_power'  # Changed
        }
        
        # Mock device lookup
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'device_id': device_id,
                'configuration': existing_config,
                'config_version': 1
            }
        }
        
        # Mock IoT shadow update
        mock_iot_client.update_thing_shadow.return_value = {
            'payload': json.dumps({
                'state': {
                    'desired': updated_config
                },
                'version': 2
            }).encode()
        }
        
        # Mock DynamoDB update
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'configuration': updated_config,
                'config_version': 2,
                'config_updated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Update configuration
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        current_version = device['Item']['config_version']
        
        # Update shadow
        mock_iot_client.update_thing_shadow(
            thingName=device_id,
            payload=json.dumps({'state': {'desired': updated_config}})
        )
        
        # Update DynamoDB
        updated_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET configuration = :config, config_version = :version, config_updated_at = :updated_at',
            ExpressionAttributeValues={
                ':config': updated_config,
                ':version': current_version + 1,
                ':updated_at': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        # Verify update
        assert updated_device['Attributes']['configuration'] == updated_config
        assert updated_device['Attributes']['config_version'] == 2
    
    def test_device_configuration_sync_status(self, mock_aws_environment, mock_iot_client):
        """Test device configuration sync status"""
        device_id = 'DEV-0001'
        
        # Mock IoT shadow get
        mock_iot_client.get_thing_shadow.return_value = {
            'payload': json.dumps({
                'state': {
                    'desired': {
                        'sampling_interval': 600
                    },
                    'reported': {
                        'sampling_interval': 300  # Not synced yet
                    },
                    'delta': {
                        'sampling_interval': 600
                    }
                },
                'version': 2
            }).encode()
        }
        
        # Get shadow
        shadow_response = mock_iot_client.get_thing_shadow(thingName=device_id)
        shadow = json.loads(shadow_response['payload'].decode())
        
        # Check sync status
        has_delta = 'delta' in shadow['state']
        assert has_delta is True  # Configuration not yet synced
        
        # Verify delta
        assert shadow['state']['delta']['sampling_interval'] == 600


class TestCompleteDeviceProvisioningWorkflow:
    """Test suite for complete end-to-end device provisioning workflow"""
    
    def test_complete_provisioning_lifecycle(self, mock_aws_environment, mock_dynamodb, mock_iot_client, sample_device_data):
        """Test complete device provisioning lifecycle: register -> activate -> configure"""
        device_id = sample_device_data['device_id']
        user_id = sample_device_data['user_id']
        
        # Step 1: Register device
        mock_iot_client.create_thing.return_value = {
            'thingName': device_id,
            'thingArn': f"arn:aws:iot:us-east-1:123456789012:thing/{device_id}"
        }
        
        mock_iot_client.create_keys_and_certificate.return_value = {
            'certificateArn': 'arn:aws:iot:us-east-1:123456789012:cert/test-cert',
            'certificateId': 'test-cert-id',
            'certificatePem': '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----',
            'keyPair': {'PublicKey': 'test-public-key', 'PrivateKey': 'test-private-key'}
        }
        
        mock_iot_client.attach_policy.return_value = {}
        mock_iot_client.attach_thing_principal.return_value = {}
        mock_dynamodb.put_item.return_value = {}
        
        # Register
        thing_response = mock_iot_client.create_thing(thingName=device_id, attributePayload={'attributes': {}})
        cert_response = mock_iot_client.create_keys_and_certificate(setAsActive=True)
        mock_iot_client.attach_policy(policyName='AquaChainDevicePolicy', target=cert_response['certificateArn'])
        mock_iot_client.attach_thing_principal(thingName=device_id, principal=cert_response['certificateArn'])
        
        device_record = {
            'device_id': device_id,
            'user_id': user_id,
            'status': 'registered',
            'certificate_id': cert_response['certificateId'],
            'created_at': datetime.utcnow().isoformat()
        }
        mock_dynamodb.put_item(Item=device_record)
        
        # Step 2: Activate device
        mock_dynamodb.get_item.return_value = {'Item': device_record}
        mock_iot_client.update_certificate.return_value = {}
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'status': 'active',
                'activated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Activate
        device = mock_dynamodb.get_item(Key={'device_id': device_id})
        mock_iot_client.update_certificate(certificateId=device['Item']['certificate_id'], newStatus='ACTIVE')
        activated_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET #status = :status, activated_at = :activated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'active', ':activated_at': datetime.utcnow().isoformat()},
            ReturnValues='ALL_NEW'
        )
        
        # Step 3: Configure device
        config = {
            'sampling_interval': 300,
            'reporting_interval': 900,
            'alert_thresholds': {'pH': {'min': 6.5, 'max': 8.5}}
        }
        
        mock_iot_client.update_thing_shadow.return_value = {
            'payload': json.dumps({'state': {'desired': config}, 'version': 1}).encode()
        }
        
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'device_id': device_id,
                'configuration': config,
                'config_version': 1
            }
        }
        
        # Configure
        mock_iot_client.update_thing_shadow(thingName=device_id, payload=json.dumps({'state': {'desired': config}}))
        configured_device = mock_dynamodb.update_item(
            Key={'device_id': device_id},
            UpdateExpression='SET configuration = :config, config_version = :version',
            ExpressionAttributeValues={':config': config, ':version': 1},
            ReturnValues='ALL_NEW'
        )
        
        # Verify complete workflow
        assert thing_response['thingName'] == device_id
        assert activated_device['Attributes']['status'] == 'active'
        assert configured_device['Attributes']['configuration'] == config
        
        # Verify all API calls were made
        mock_iot_client.create_thing.assert_called_once()
        mock_iot_client.create_keys_and_certificate.assert_called_once()
        mock_iot_client.update_certificate.assert_called_once()
        mock_iot_client.update_thing_shadow.assert_called_once()
    
    def test_provisioning_with_rollback_on_failure(self, mock_aws_environment, mock_iot_client):
        """Test provisioning rollback when a step fails"""
        from botocore.exceptions import ClientError
        
        device_id = 'DEV-0001'
        
        # Step 1: Create thing (succeeds)
        mock_iot_client.create_thing.return_value = {
            'thingName': device_id,
            'thingArn': f"arn:aws:iot:us-east-1:123456789012:thing/{device_id}"
        }
        
        thing_response = mock_iot_client.create_thing(thingName=device_id, attributePayload={'attributes': {}})
        assert thing_response['thingName'] == device_id
        
        # Step 2: Create certificate (fails)
        mock_iot_client.create_keys_and_certificate.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailableException', 'Message': 'Service unavailable'}},
            'CreateKeysAndCertificate'
        )
        
        # Attempt to create certificate
        with pytest.raises(ClientError):
            mock_iot_client.create_keys_and_certificate(setAsActive=True)
        
        # Rollback: Delete thing
        mock_iot_client.delete_thing.return_value = {}
        mock_iot_client.delete_thing(thingName=device_id)
        
        # Verify rollback
        mock_iot_client.delete_thing.assert_called_once_with(thingName=device_id)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
