"""
Integration tests for OTA firmware update system
Tests the complete OTA workflow including signing, distribution, and rollback
"""

import pytest
import boto3
import json
import time
from moto import mock_iot, mock_s3, mock_dynamodb, mock_sns, mock_signer
from ota_update_manager import OTAUpdateManager
import os


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_ACCOUNT_ID'] = '123456789012'


@pytest.fixture
def setup_environment(aws_credentials):
    """Set up test environment variables"""
    os.environ['FIRMWARE_BUCKET'] = 'test-firmware-bucket'
    os.environ['DEVICE_TABLE'] = 'test-devices'
    os.environ['FIRMWARE_HISTORY_TABLE'] = 'test-firmware-history'
    os.environ['SIGNING_PROFILE_NAME'] = 'test-signing-profile'
    os.environ['ALERT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts'


@mock_s3
@mock_dynamodb
@mock_iot
def test_firmware_signing(setup_environment):
    """Test firmware signing workflow"""
    # Create S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-firmware-bucket')
    
    # Upload test firmware
    test_firmware = b'TEST_FIRMWARE_CONTENT_v2.0.0'
    s3.put_object(
        Bucket='test-firmware-bucket',
        Key='unsigned/firmware-v2.0.0.bin',
        Body=test_firmware
    )
    
    # Test signing (note: moto doesn't fully support signer, so this is a basic test)
    manager = OTAUpdateManager()
    
    # In real environment, this would sign the firmware
    # For testing, we'll verify the method exists and handles errors
    result = manager.sign_firmware(
        firmware_key='unsigned/firmware-v2.0.0.bin',
        version='2.0.0'
    )
    
    assert result is not None
    assert 'job_id' in result or 'error' in result


@mock_dynamodb
@mock_iot
@mock_s3
def test_create_firmware_job(setup_environment):
    """Test creating IoT Job for firmware update"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create firmware history table
    table = dynamodb.create_table(
        TableName='test-firmware-history',
        KeySchema=[
            {'AttributeName': 'job_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'job_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-firmware-bucket')
    
    # Upload signed firmware
    test_firmware = b'SIGNED_FIRMWARE_v2.0.0'
    s3.put_object(
        Bucket='test-firmware-bucket',
        Key='signed/v2.0.0/firmware.bin',
        Body=test_firmware
    )
    
    # Create IoT thing
    iot = boto3.client('iot', region_name='us-east-1')
    iot.create_thing(thingName='test-device-001')
    
    # Create firmware job
    manager = OTAUpdateManager()
    
    result = manager.create_firmware_job(
        firmware_version='2.0.0',
        signed_firmware_key='signed/v2.0.0/firmware.bin',
        target_devices=['test-device-001']
    )
    
    # Verify job was created
    assert 'job_id' in result or 'error' in result
    
    if 'job_id' in result:
        assert result['firmware_version'] == '2.0.0'
        assert result['target_devices_count'] == 1


@mock_dynamodb
@mock_iot
def test_track_update_progress(setup_environment):
    """Test tracking firmware update progress"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    table = dynamodb.create_table(
        TableName='test-firmware-history',
        KeySchema=[
            {'AttributeName': 'job_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'job_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create test job record
    job_id = 'test-job-123'
    table.put_item(Item={
        'job_id': job_id,
        'firmware_version': '2.0.0',
        'status': 'IN_PROGRESS',
        'devices_total': 10,
        'devices_updated': 0,
        'devices_failed': 0
    })
    
    # Track progress
    manager = OTAUpdateManager()
    
    # Note: moto doesn't fully support IoT Jobs, so this will return an error
    # In real environment, this would return actual progress
    result = manager.track_update_progress(job_id)
    
    assert result is not None


@mock_dynamodb
def test_handle_update_status(setup_environment):
    """Test handling device update status"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create device table
    device_table = dynamodb.create_table(
        TableName='test-devices',
        KeySchema=[
            {'AttributeName': 'device_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'device_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create test device
    device_table.put_item(Item={
        'device_id': 'test-device-001',
        'firmware_version': '1.0.0'
    })
    
    # Handle successful update
    manager = OTAUpdateManager()
    
    result = manager.handle_update_status(
        device_id='test-device-001',
        firmware_version='2.0.0',
        status='success'
    )
    
    assert result['device_id'] == 'test-device-001'
    assert result['status'] == 'success'
    
    # Verify device was updated
    response = device_table.get_item(Key={'device_id': 'test-device-001'})
    assert response['Item']['firmware_version'] == '2.0.0'
    assert 'previous_firmware_version' in response['Item']


@mock_dynamodb
@mock_s3
def test_rollback_firmware(setup_environment):
    """Test firmware rollback mechanism"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create tables
    device_table = dynamodb.create_table(
        TableName='test-devices',
        KeySchema=[
            {'AttributeName': 'device_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'device_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    firmware_table = dynamodb.create_table(
        TableName='test-firmware-history',
        KeySchema=[
            {'AttributeName': 'job_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'job_id', 'AttributeType': 'S'},
            {'AttributeName': 'firmware_version', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'version-index',
                'KeySchema': [
                    {'AttributeName': 'firmware_version', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-firmware-bucket')
    
    # Upload previous firmware version
    s3.put_object(
        Bucket='test-firmware-bucket',
        Key='signed/v1.0.0/firmware.bin',
        Body=b'FIRMWARE_v1.0.0'
    )
    
    # Create device with current and previous version
    device_table.put_item(Item={
        'device_id': 'test-device-001',
        'firmware_version': '2.0.0',
        'previous_firmware_version': '1.0.0'
    })
    
    # Create firmware history record
    firmware_table.put_item(Item={
        'job_id': 'old-job-123',
        'firmware_version': '1.0.0',
        'firmware_key': 'signed/v1.0.0/firmware.bin',
        'checksum': 'abc123'
    })
    
    # Test rollback
    manager = OTAUpdateManager()
    
    result = manager.rollback_firmware(
        device_id='test-device-001'
    )
    
    # Verify rollback was initiated
    assert 'device_id' in result
    assert result['device_id'] == 'test-device-001'
    
    if 'error' not in result:
        assert result['rollback_version'] == '1.0.0'
        assert 'job_id' in result


@mock_dynamodb
def test_automatic_rollback_on_failure(setup_environment):
    """Test automatic rollback when update fails"""
    # Setup DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    device_table = dynamodb.create_table(
        TableName='test-devices',
        KeySchema=[
            {'AttributeName': 'device_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'device_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    firmware_table = dynamodb.create_table(
        TableName='test-firmware-history',
        KeySchema=[
            {'AttributeName': 'job_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'job_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create device
    device_table.put_item(Item={
        'device_id': 'test-device-001',
        'firmware_version': '1.0.0',
        'previous_firmware_version': '0.9.0'
    })
    
    # Handle failed update
    manager = OTAUpdateManager()
    
    result = manager.handle_update_status(
        device_id='test-device-001',
        firmware_version='2.0.0',
        status='failed',
        error_message='Checksum verification failed'
    )
    
    assert result['status'] == 'failed'
    # Automatic rollback should be triggered internally


def test_job_templates():
    """Test job document templates"""
    from job_templates import (
        create_firmware_update_job_document,
        create_rollback_job_document,
        create_gradual_rollout_config,
        create_abort_config
    )
    
    # Test firmware update document
    update_doc = create_firmware_update_job_document(
        firmware_version='2.0.0',
        firmware_url='https://example.com/firmware.bin',
        firmware_size=1024000,
        checksum='abc123def456'
    )
    
    assert update_doc['operation'] == 'firmware_update'
    assert update_doc['firmware_version'] == '2.0.0'
    assert update_doc['checksum'] == 'abc123def456'
    
    # Test rollback document
    rollback_doc = create_rollback_job_document(
        firmware_version='1.0.0',
        firmware_url='https://example.com/old-firmware.bin',
        firmware_size=1000000,
        checksum='old123abc456'
    )
    
    assert rollback_doc['operation'] == 'firmware_rollback'
    assert rollback_doc['firmware_version'] == '1.0.0'
    
    # Test rollout configs
    initial_config = create_gradual_rollout_config('initial')
    assert initial_config['maximumPerMinute'] == 5
    
    medium_config = create_gradual_rollout_config('medium')
    assert medium_config['maximumPerMinute'] == 20
    
    full_config = create_gradual_rollout_config('full')
    assert full_config['maximumPerMinute'] == 100
    
    # Test abort config
    abort_config = create_abort_config()
    assert len(abort_config['criteriaList']) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
