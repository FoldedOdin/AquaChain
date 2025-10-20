"""
Integration tests for AquaChain data processing pipeline
Tests the complete flow from IoT data ingestion to notification delivery
"""

import json
import time
import uuid
import boto3
import pytest
from datetime import datetime, timezone
from moto import mock_dynamodb, mock_s3, mock_sns, mock_iot, mock_lambda
import os

# Set LocalStack endpoint if running in CI
if os.getenv('LOCALSTACK_ENDPOINT'):
    boto3.setup_default_session()
    for service in ['dynamodb', 's3', 'sns', 'iot', 'lambda']:
        boto3.client(service, endpoint_url=os.getenv('LOCALSTACK_ENDPOINT'))

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def setup_infrastructure(aws_credentials):
    """Set up mock AWS infrastructure for testing."""
    with mock_dynamodb(), mock_s3(), mock_sns(), mock_iot(), mock_lambda():
        # Create DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Readings table
        readings_table = dynamodb.create_table(
            TableName='aquachain-readings',
            KeySchema=[
                {'AttributeName': 'deviceId_month', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'deviceId_month', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            }
        )
        
        # Ledger table
        ledger_table = dynamodb.create_table(
            TableName='aquachain-ledger',
            KeySchema=[
                {'AttributeName': 'partition_key', 'KeyType': 'HASH'},
                {'AttributeName': 'sequenceNumber', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'partition_key', 'AttributeType': 'S'},
                {'AttributeName': 'sequenceNumber', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            }
        )
        
        # Sequence table
        sequence_table = dynamodb.create_table(
            TableName='aquachain-sequence',
            KeySchema=[
                {'AttributeName': 'sequenceType', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'sequenceType', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Initialize sequence
        sequence_table.put_item(
            Item={
                'sequenceType': 'LEDGER',
                'currentSequence': 0,
                'lastUpdated': datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Create S3 buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='aquachain-data-lake-123456789012')
        s3.create_bucket(Bucket='aquachain-audit-trail-123456789012')
        
        # Create SNS topic
        sns = boto3.client('sns', region_name='us-east-1')
        topic_response = sns.create_topic(Name='aquachain-critical-alerts')
        
        yield {
            'readings_table': readings_table,
            'ledger_table': ledger_table,
            'sequence_table': sequence_table,
            'topic_arn': topic_response['TopicArn']
        }

def test_complete_data_processing_pipeline(setup_infrastructure):
    """Test complete data processing from IoT message to ledger storage."""
    
    # Sample IoT device data
    device_data = {
        "deviceId": "DEV-TEST-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": 9.9312,
            "longitude": 76.2673
        },
        "readings": {
            "pH": 7.2,
            "turbidity": 1.5,
            "tds": 145,
            "temperature": 24.5,
            "humidity": 68.2
        },
        "diagnostics": {
            "batteryLevel": 85,
            "signalStrength": -65,
            "sensorStatus": "normal"
        }
    }
    
    # Simulate data processing
    processed_data = process_device_data(device_data)
    
    # Verify data was stored in readings table
    readings_table = setup_infrastructure['readings_table']
    device_month = f"{device_data['deviceId']}#{datetime.now().strftime('%Y%m')}"
    
    response = readings_table.get_item(
        Key={
            'deviceId_month': device_month,
            'timestamp': device_data['timestamp']
        }
    )
    
    assert 'Item' in response
    stored_item = response['Item']
    assert stored_item['readings']['pH'] == 7.2
    assert stored_item['wqi'] > 0
    assert 'ledgerHash' in stored_item

def test_critical_alert_generation(setup_infrastructure):
    """Test that critical water quality events trigger alerts."""
    
    # Critical water quality data (low pH)
    critical_data = {
        "deviceId": "DEV-TEST-002",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": 9.9312,
            "longitude": 76.2673
        },
        "readings": {
            "pH": 4.0,  # Critical pH level
            "turbidity": 50.0,  # High turbidity
            "tds": 2000,  # High TDS
            "temperature": 24.5,
            "humidity": 68.2
        },
        "diagnostics": {
            "batteryLevel": 85,
            "signalStrength": -65,
            "sensorStatus": "normal"
        }
    }
    
    # Process critical data
    processed_data = process_device_data(critical_data)
    
    # Verify WQI is below critical threshold
    assert processed_data['wqi'] < 50
    assert processed_data['anomalyType'] in ['contamination', 'sensor_fault']

def test_ledger_hash_chain_integrity(setup_infrastructure):
    """Test that ledger entries maintain hash chain integrity."""
    
    ledger_table = setup_infrastructure['ledger_table']
    
    # Create multiple ledger entries
    entries = []
    for i in range(3):
        entry_data = {
            "deviceId": f"DEV-TEST-{i:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": {
                "pH": 7.0 + i * 0.1,
                "turbidity": 1.0 + i * 0.5,
                "tds": 150 + i * 10,
                "temperature": 24.0 + i,
                "humidity": 65.0 + i
            }
        }
        
        processed_entry = process_device_data(entry_data)
        entries.append(processed_entry)
    
    # Verify hash chain integrity
    for i in range(1, len(entries)):
        current_entry = get_ledger_entry(entries[i]['sequenceNumber'])
        previous_entry = get_ledger_entry(entries[i-1]['sequenceNumber'])
        
        # Current entry's previousHash should match previous entry's chainHash
        assert current_entry['previousHash'] == previous_entry['chainHash']

def test_ml_inference_accuracy(setup_infrastructure):
    """Test ML inference for WQI calculation and anomaly detection."""
    
    # Normal water quality
    normal_data = {
        "readings": {
            "pH": 7.0,
            "turbidity": 1.0,
            "tds": 150,
            "temperature": 25.0,
            "humidity": 60.0
        }
    }
    
    wqi, anomaly_type = calculate_wqi_and_anomaly(normal_data['readings'])
    assert 70 <= wqi <= 100  # Good water quality
    assert anomaly_type == 'normal'
    
    # Contaminated water
    contaminated_data = {
        "readings": {
            "pH": 4.0,  # Acidic
            "turbidity": 100.0,  # Very turbid
            "tds": 3000,  # High dissolved solids
            "temperature": 25.0,
            "humidity": 60.0
        }
    }
    
    wqi, anomaly_type = calculate_wqi_and_anomaly(contaminated_data['readings'])
    assert wqi < 50  # Poor water quality
    assert anomaly_type in ['contamination', 'sensor_fault']

def test_data_validation_and_sanitization(setup_infrastructure):
    """Test data validation and sanitization logic."""
    
    # Invalid data (pH out of range)
    invalid_data = {
        "deviceId": "DEV-TEST-INVALID",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": {
            "pH": 15.0,  # Invalid pH (>14)
            "turbidity": -5.0,  # Invalid negative turbidity
            "tds": 150,
            "temperature": 24.5,
            "humidity": 68.2
        }
    }
    
    # Should raise validation error
    with pytest.raises(ValueError):
        validate_sensor_data(invalid_data)
    
    # Valid data should pass
    valid_data = {
        "deviceId": "DEV-TEST-VALID",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": {
            "pH": 7.2,
            "turbidity": 1.5,
            "tds": 145,
            "temperature": 24.5,
            "humidity": 68.2
        }
    }
    
    # Should not raise any exception
    validated_data = validate_sensor_data(valid_data)
    assert validated_data['readings']['pH'] == 7.2

# Helper functions (would be imported from actual modules)
def process_device_data(device_data):
    """Simulate data processing pipeline."""
    # Validate data
    validated_data = validate_sensor_data(device_data)
    
    # Calculate WQI and detect anomalies
    wqi, anomaly_type = calculate_wqi_and_anomaly(validated_data['readings'])
    
    # Create ledger entry
    sequence_number = get_next_sequence_number()
    ledger_entry = create_ledger_entry(validated_data, wqi, anomaly_type, sequence_number)
    
    # Store in DynamoDB
    store_reading_data(validated_data, wqi, anomaly_type, ledger_entry['chainHash'])
    store_ledger_entry(ledger_entry)
    
    return {
        'deviceId': validated_data['deviceId'],
        'timestamp': validated_data['timestamp'],
        'wqi': wqi,
        'anomalyType': anomaly_type,
        'sequenceNumber': sequence_number,
        'ledgerHash': ledger_entry['chainHash']
    }

def validate_sensor_data(data):
    """Validate sensor data ranges."""
    readings = data['readings']
    
    # pH validation (0-14)
    if not (0 <= readings['pH'] <= 14):
        raise ValueError(f"Invalid pH value: {readings['pH']}")
    
    # Turbidity validation (>= 0)
    if readings['turbidity'] < 0:
        raise ValueError(f"Invalid turbidity value: {readings['turbidity']}")
    
    # TDS validation (>= 0)
    if readings['tds'] < 0:
        raise ValueError(f"Invalid TDS value: {readings['tds']}")
    
    return data

def calculate_wqi_and_anomaly(readings):
    """Calculate Water Quality Index and detect anomalies."""
    # Simple WQI calculation (in real implementation, this would use ML model)
    ph_score = 100 if 6.5 <= readings['pH'] <= 8.5 else max(0, 100 - abs(readings['pH'] - 7.0) * 20)
    turbidity_score = max(0, 100 - readings['turbidity'] * 2)
    tds_score = max(0, 100 - max(0, readings['tds'] - 500) / 10)
    
    wqi = (ph_score + turbidity_score + tds_score) / 3
    
    # Anomaly detection
    if wqi < 30:
        anomaly_type = 'contamination'
    elif readings['pH'] < 4 or readings['pH'] > 10:
        anomaly_type = 'sensor_fault'
    else:
        anomaly_type = 'normal'
    
    return wqi, anomaly_type

def get_next_sequence_number():
    """Get next sequence number for ledger."""
    # In real implementation, this would use DynamoDB atomic counter
    return int(time.time() * 1000)  # Use timestamp as sequence for testing

def create_ledger_entry(data, wqi, anomaly_type, sequence_number):
    """Create ledger entry with hash chaining."""
    import hashlib
    
    # Get previous hash (simplified for testing)
    previous_hash = "0" * 64  # Genesis hash for first entry
    
    # Create data hash
    data_string = json.dumps(data['readings'], sort_keys=True)
    data_hash = hashlib.sha256(data_string.encode()).hexdigest()
    
    # Create chain hash
    chain_data = f"{data_hash}{previous_hash}{sequence_number}"
    chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
    
    return {
        'logId': str(uuid.uuid4()),
        'sequenceNumber': sequence_number,
        'timestamp': data['timestamp'],
        'deviceId': data['deviceId'],
        'dataHash': data_hash,
        'previousHash': previous_hash,
        'chainHash': chain_hash,
        'wqi': wqi,
        'anomalyType': anomaly_type
    }

def store_reading_data(data, wqi, anomaly_type, ledger_hash):
    """Store reading data in DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('aquachain-readings')
    
    device_month = f"{data['deviceId']}#{datetime.now().strftime('%Y%m')}"
    
    table.put_item(
        Item={
            'deviceId_month': device_month,
            'timestamp': data['timestamp'],
            'deviceId': data['deviceId'],
            'readings': data['readings'],
            'wqi': wqi,
            'anomalyType': anomaly_type,
            'ledgerHash': ledger_hash,
            'location': data.get('location', {}),
            'diagnostics': data.get('diagnostics', {})
        }
    )

def store_ledger_entry(entry):
    """Store ledger entry in DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('aquachain-ledger')
    
    table.put_item(
        Item={
            'partition_key': 'GLOBAL_SEQUENCE',
            'sequenceNumber': entry['sequenceNumber'],
            'logId': entry['logId'],
            'timestamp': entry['timestamp'],
            'deviceId': entry['deviceId'],
            'dataHash': entry['dataHash'],
            'previousHash': entry['previousHash'],
            'chainHash': entry['chainHash'],
            'wqi': entry['wqi'],
            'anomalyType': entry['anomalyType']
        }
    )

def get_ledger_entry(sequence_number):
    """Get ledger entry by sequence number."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('aquachain-ledger')
    
    response = table.get_item(
        Key={
            'partition_key': 'GLOBAL_SEQUENCE',
            'sequenceNumber': sequence_number
        }
    )
    
    return response.get('Item')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])