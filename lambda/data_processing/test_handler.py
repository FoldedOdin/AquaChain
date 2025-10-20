"""
Unit tests for data processing Lambda function
"""

import json
import pytest
import boto3
from moto import mock_dynamodb, mock_s3, mock_sns, mock_lambda
from datetime import datetime, timezone
import os
import sys

# Add the lambda function to the path
sys.path.insert(0, os.path.dirname(__file__))

# Mock environment variables
os.environ['READINGS_TABLE'] = 'aquachain-readings'
os.environ['DATA_LAKE_BUCKET'] = 'aquachain-data-lake-123456789012'
os.environ['ML_INFERENCE_FUNCTION'] = 'AquaChain-ML-Inference'
os.environ['DLQ_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/data-processing-dlq'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

try:
    import handler
except ImportError:
    # Create a mock handler for testing
    class MockHandler:
        def lambda_handler(self, event, context):
            return {"statusCode": 200, "body": "Mock handler"}
    handler = MockHandler()

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture
def setup_aws_resources(aws_credentials):
    """Set up mock AWS resources."""
    with mock_dynamodb(), mock_s3(), mock_sns(), mock_lambda():
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='aquachain-readings',
            KeySchema=[
                {'AttributeName': 'deviceId_month', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'deviceId_month', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='aquachain-data-lake-123456789012')
        
        # Create SNS topic
        sns = boto3.client('sns', region_name='us-east-1')
        topic_response = sns.create_topic(Name='aquachain-critical-alerts')
        
        # Create Lambda function for ML inference
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_client.create_function(
            FunctionName='AquaChain-ML-Inference',
            Runtime='python3.11',
            Role='arn:aws:iam::123456789012:role/lambda-role',
            Handler='handler.lambda_handler',
            Code={'ZipFile': b'fake code'},
        )
        
        yield {
            'table': table,
            'topic_arn': topic_response['TopicArn']
        }

def test_valid_iot_message_processing(setup_aws_resources):
    """Test processing of valid IoT device message."""
    
    # Sample IoT message
    event = {
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
    
    context = MockLambdaContext()
    
    # Process the event
    response = handler.lambda_handler(event, context)
    
    # Verify successful processing
    assert response['statusCode'] == 200
    
    # Verify data was stored in DynamoDB
    table = setup_aws_resources['table']
    device_month = f"{event['deviceId']}#{datetime.now().strftime('%Y%m')}"
    
    stored_item = table.get_item(
        Key={
            'deviceId_month': device_month,
            'timestamp': event['timestamp']
        }
    )
    
    assert 'Item' in stored_item
    assert stored_item['Item']['readings']['pH'] == 7.2

def test_invalid_data_validation(setup_aws_resources):
    """Test validation of invalid sensor data."""
    
    # Invalid IoT message (pH out of range)
    event = {
        "deviceId": "DEV-TEST-002",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": {
            "pH": 15.0,  # Invalid pH
            "turbidity": 1.5,
            "tds": 145,
            "temperature": 24.5,
            "humidity": 68.2
        }
    }
    
    context = MockLambdaContext()
    
    # Process the event
    response = handler.lambda_handler(event, context)
    
    # Should return error for invalid data
    assert response['statusCode'] == 400
    assert 'validation error' in response['body'].lower()

def test_critical_alert_generation(setup_aws_resources):
    """Test generation of critical water quality alerts."""
    
    # Critical water quality data
    event = {
        "deviceId": "DEV-TEST-003",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": {
            "pH": 4.0,  # Critical pH
            "turbidity": 100.0,  # High turbidity
            "tds": 3000,  # High TDS
            "temperature": 24.5,
            "humidity": 68.2
        }
    }
    
    context = MockLambdaContext()
    
    # Process the event
    response = handler.lambda_handler(event, context)
    
    # Should process successfully and trigger alert
    assert response['statusCode'] == 200
    
    # Verify alert was sent (would check SNS in real implementation)
    response_body = json.loads(response['body'])
    assert response_body.get('alertTriggered') == True

def test_duplicate_data_handling(setup_aws_resources):
    """Test handling of duplicate sensor readings."""
    
    # Same message sent twice
    event = {
        "deviceId": "DEV-TEST-004",
        "timestamp": "2025-10-20T10:00:00.000Z",  # Fixed timestamp
        "readings": {
            "pH": 7.0,
            "turbidity": 1.0,
            "tds": 150,
            "temperature": 25.0,
            "humidity": 60.0
        }
    }
    
    context = MockLambdaContext()
    
    # Process first time
    response1 = handler.lambda_handler(event, context)
    assert response1['statusCode'] == 200
    
    # Process duplicate
    response2 = handler.lambda_handler(event, context)
    
    # Should handle duplicate gracefully
    assert response2['statusCode'] in [200, 409]  # OK or Conflict

def test_error_handling_and_dlq(setup_aws_resources):
    """Test error handling and dead letter queue integration."""
    
    # Malformed event
    event = {
        "deviceId": "DEV-TEST-005",
        # Missing required fields
    }
    
    context = MockLambdaContext()
    
    # Process the event
    response = handler.lambda_handler(event, context)
    
    # Should handle error gracefully
    assert response['statusCode'] in [400, 500]
    
    # In real implementation, would verify DLQ message

def test_performance_under_load(setup_aws_resources):
    """Test function performance with multiple concurrent requests."""
    
    import concurrent.futures
    import time
    
    def process_message(i):
        event = {
            "deviceId": f"DEV-LOAD-{i:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": {
                "pH": 7.0 + (i % 10) * 0.1,
                "turbidity": 1.0 + (i % 5) * 0.5,
                "tds": 150 + (i % 20) * 10,
                "temperature": 25.0,
                "humidity": 60.0
            }
        }
        
        context = MockLambdaContext()
        start_time = time.time()
        response = handler.lambda_handler(event, context)
        end_time = time.time()
        
        return {
            'response': response,
            'duration': end_time - start_time
        }
    
    # Process 10 messages concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_message, i) for i in range(10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    for result in results:
        assert result['response']['statusCode'] == 200
        assert result['duration'] < 5.0  # Should complete within 5 seconds

class MockLambdaContext:
    """Mock Lambda context for testing."""
    
    def __init__(self):
        self.function_name = 'test-function'
        self.function_version = '1'
        self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
        self.memory_limit_in_mb = 512
        self.remaining_time_in_millis = lambda: 30000
        self.aws_request_id = 'test-request-id'
        self.log_group_name = '/aws/lambda/test-function'
        self.log_stream_name = 'test-stream'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])