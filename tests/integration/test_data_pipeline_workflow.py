"""
Integration tests for data pipeline workflow
Tests the complete end-to-end data pipeline from IoT message to Lambda processing to DynamoDB storage
Requirements: 3.4, 12.2
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, call
import time

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'data_processing'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from handler import (
    lambda_handler,
    extract_iot_data,
    validate_and_sanitize_data,
    check_for_duplicates,
    store_raw_data_s3,
    invoke_ml_inference,
    store_reading_dynamodb
)


@pytest.fixture
def mock_aws_environment():
    """Fixture providing mocked AWS environment"""
    with patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'READINGS_TABLE': 'test-readings',
        'DATA_LAKE_BUCKET': 'test-data-lake',
        'ML_INFERENCE_FUNCTION': 'test-ml-inference',
        'DLQ_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-dlq'
    }):
        yield


@pytest.fixture
def mock_aws_clients():
    """Fixture providing mocked AWS clients"""
    with patch('boto3.resource') as mock_resource, \
         patch('boto3.client') as mock_client:
        
        mock_dynamodb_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_dynamodb_table
        
        mock_s3 = MagicMock()
        mock_lambda = MagicMock()
        mock_sqs = MagicMock()
        
        def get_client(service_name, **kwargs):
            if service_name == 's3':
                return mock_s3
            elif service_name == 'lambda':
                return mock_lambda
            elif service_name == 'sqs':
                return mock_sqs
            return MagicMock()
        
        mock_client.side_effect = get_client
        
        yield {
            'dynamodb_table': mock_dynamodb_table,
            's3': mock_s3,
            'lambda': mock_lambda,
            'sqs': mock_sqs
        }


@pytest.fixture
def sample_iot_message():
    """Fixture providing sample IoT sensor message"""
    return {
        'deviceId': 'DEV-0001',
        'timestamp': '2025-10-25T12:00:00Z',
        'location': {
            'latitude': 37.7749,
            'longitude': -122.4194
        },
        'readings': {
            'pH': 7.2,
            'turbidity': 2.5,
            'tds': 350.0,
            'temperature': 22.5,
            'humidity': 65.0
        },
        'diagnostics': {
            'batteryLevel': 85.0,
            'signalStrength': -65.0,
            'sensorStatus': 'normal'
        }
    }


@pytest.fixture
def sample_ml_results():
    """Fixture providing sample ML inference results"""
    return {
        'wqi': 85.5,
        'anomalyType': 'normal',
        'confidence': 0.95
    }


class TestIoTMessageIngestion:
    """Test suite for IoT message ingestion"""
    
    def test_extract_iot_data_from_direct_invocation(self, sample_iot_message):
        """Test extracting IoT data from direct Lambda invocation"""
        event = sample_iot_message
        
        extracted_data = extract_iot_data(event)
        
        assert extracted_data == sample_iot_message
        assert extracted_data['deviceId'] == 'DEV-0001'
        assert 'readings' in extracted_data
    
    def test_extract_iot_data_from_sns(self, sample_iot_message):
        """Test extracting IoT data from SNS trigger"""
        event = {
            'Records': [
                {
                    'Sns': {
                        'Message': json.dumps(sample_iot_message)
                    }
                }
            ]
        }
        
        extracted_data = extract_iot_data(event)
        
        assert extracted_data == sample_iot_message
        assert extracted_data['deviceId'] == 'DEV-0001'
    
    def test_extract_iot_data_from_sqs(self, sample_iot_message):
        """Test extracting IoT data from SQS trigger"""
        event = {
            'Records': [
                {
                    'body': json.dumps(sample_iot_message)
                }
            ]
        }
        
        extracted_data = extract_iot_data(event)
        
        assert extracted_data == sample_iot_message
        assert extracted_data['deviceId'] == 'DEV-0001'
    
    def test_extract_iot_data_with_malformed_json(self):
        """Test extracting IoT data with malformed JSON"""
        event = {
            'Records': [
                {
                    'body': 'invalid json {'
                }
            ]
        }
        
        with pytest.raises(json.JSONDecodeError):
            extract_iot_data(event)


class TestDataValidationAndSanitization:
    """Test suite for data validation and sanitization"""
    
    def test_validate_valid_sensor_data(self, sample_iot_message):
        """Test validating valid sensor data"""
        validated_data = validate_and_sanitize_data(sample_iot_message)
        
        assert validated_data['deviceId'] == 'DEV-0001'
        assert validated_data['timestamp'].endswith('Z')
        assert validated_data['readings']['pH'] == 7.2
        assert validated_data['readings']['turbidity'] == 2.5
    
    def test_validate_data_with_out_of_range_ph(self, sample_iot_message):
        """Test validation with out-of-range pH value"""
        from errors import ValidationError
        
        sample_iot_message['readings']['pH'] = 15.0  # Invalid: > 14
        
        with pytest.raises(ValidationError) as exc_info:
            validate_and_sanitize_data(sample_iot_message)
        
        assert 'pH' in str(exc_info.value).lower()
    
    def test_validate_data_with_negative_turbidity(self, sample_iot_message):
        """Test validation with negative turbidity value"""
        from errors import ValidationError
        
        sample_iot_message['readings']['turbidity'] = -5.0  # Invalid: < 0
        
        with pytest.raises(ValidationError) as exc_info:
            validate_and_sanitize_data(sample_iot_message)
        
        assert 'turbidity' in str(exc_info.value).lower()
    
    def test_validate_data_with_missing_required_field(self, sample_iot_message):
        """Test validation with missing required field"""
        from jsonschema import ValidationError
        
        del sample_iot_message['readings']  # Remove required field
        
        with pytest.raises(ValidationError):
            validate_and_sanitize_data(sample_iot_message)
    
    def test_sanitize_timestamp_format(self):
        """Test timestamp sanitization"""
        data = {
            'deviceId': 'DEV-0001',
            'timestamp': '2025-10-25T12:00:00',  # Missing Z
            'location': {'latitude': 37.7749, 'longitude': -122.4194},
            'readings': {'pH': 7.0, 'turbidity': 2.0, 'tds': 300.0, 'temperature': 20.0, 'humidity': 60.0},
            'diagnostics': {'batteryLevel': 80.0, 'signalStrength': -70.0, 'sensorStatus': 'normal'}
        }
        
        validated_data = validate_and_sanitize_data(data)
        
        assert validated_data['timestamp'].endswith('Z')
    
    def test_sanitize_sensor_value_precision(self, sample_iot_message):
        """Test sensor value precision sanitization"""
        sample_iot_message['readings']['pH'] = 7.123456789
        sample_iot_message['readings']['turbidity'] = 2.56789
        
        validated_data = validate_and_sanitize_data(sample_iot_message)
        
        # pH should be rounded to 2 decimal places
        assert validated_data['readings']['pH'] == 7.12
        # Turbidity should be rounded to 1 decimal place
        assert validated_data['readings']['turbidity'] == 2.6


class TestDuplicateDetection:
    """Test suite for duplicate data detection"""
    
    def test_check_for_duplicates_no_duplicate(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test duplicate check when no duplicate exists"""
        # Mock DynamoDB get_item (no duplicate)
        mock_aws_clients['dynamodb_table'].get_item.return_value = {}
        
        # Should not raise exception
        check_for_duplicates(sample_iot_message)
        
        # Verify DynamoDB was queried
        mock_aws_clients['dynamodb_table'].get_item.assert_called_once()
    
    def test_check_for_duplicates_duplicate_found(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test duplicate check when duplicate exists"""
        from handler import DuplicateDataError
        
        # Mock DynamoDB get_item (duplicate found)
        mock_aws_clients['dynamodb_table'].get_item.return_value = {
            'Item': {
                'deviceId_month': 'DEV-0001#202510',
                'timestamp': '2025-10-25T12:00:00Z',
                'readings': sample_iot_message['readings']
            }
        }
        
        # Should raise DuplicateDataError
        with pytest.raises(DuplicateDataError) as exc_info:
            check_for_duplicates(sample_iot_message)
        
        assert 'DEV-0001' in str(exc_info.value)


class TestS3DataStorage:
    """Test suite for S3 data storage"""
    
    def test_store_raw_data_in_s3(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test storing raw data in S3"""
        # Mock S3 put_object
        mock_aws_clients['s3'].put_object.return_value = {}
        
        s3_reference = store_raw_data_s3(sample_iot_message)
        
        # Verify S3 reference format
        assert s3_reference.startswith('s3://test-data-lake/raw-readings/')
        assert 'DEV-0001' in s3_reference
        
        # Verify S3 was called
        mock_aws_clients['s3'].put_object.assert_called_once()
        call_args = mock_aws_clients['s3'].put_object.call_args
        
        # Verify bucket and key
        assert call_args[1]['Bucket'] == 'test-data-lake'
        assert 'raw-readings/' in call_args[1]['Key']
        
        # Verify encryption
        assert call_args[1]['ServerSideEncryption'] == 'aws:kms'
        
        # Verify metadata
        assert call_args[1]['Metadata']['deviceId'] == 'DEV-0001'
    
    def test_store_raw_data_with_partitioning(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test S3 storage with Hive-style partitioning"""
        mock_aws_clients['s3'].put_object.return_value = {}
        
        s3_reference = store_raw_data_s3(sample_iot_message)
        
        # Verify partitioning structure
        assert 'year=2025' in s3_reference
        assert 'month=10' in s3_reference
        assert 'day=25' in s3_reference
        assert 'hour=12' in s3_reference
    
    def test_store_raw_data_s3_failure(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test S3 storage failure handling"""
        from botocore.exceptions import ClientError
        from errors import DatabaseError
        
        # Mock S3 failure
        mock_aws_clients['s3'].put_object.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'PutObject'
        )
        
        # Should raise DatabaseError
        with pytest.raises(DatabaseError) as exc_info:
            store_raw_data_s3(sample_iot_message)
        
        assert 's3' in str(exc_info.value).lower()


class TestMLInference:
    """Test suite for ML inference integration"""
    
    def test_invoke_ml_inference_success(self, mock_aws_environment, mock_aws_clients, sample_iot_message, sample_ml_results):
        """Test successful ML inference invocation"""
        # Mock Lambda invoke
        mock_aws_clients['lambda'].invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps(sample_ml_results)
            }).encode())
        }
        
        ml_results = invoke_ml_inference(sample_iot_message)
        
        # Verify results
        assert ml_results['wqi'] == 85.5
        assert ml_results['anomalyType'] == 'normal'
        assert ml_results['confidence'] == 0.95
        
        # Verify Lambda was invoked
        mock_aws_clients['lambda'].invoke.assert_called_once()
        call_args = mock_aws_clients['lambda'].invoke.call_args
        
        assert call_args[1]['FunctionName'] == 'test-ml-inference'
        assert call_args[1]['InvocationType'] == 'RequestResponse'
    
    def test_invoke_ml_inference_failure_returns_defaults(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test ML inference failure returns default values"""
        from botocore.exceptions import ClientError
        
        # Mock Lambda failure
        mock_aws_clients['lambda'].invoke.side_effect = ClientError(
            {'Error': {'Code': 'ServiceException', 'Message': 'Service error'}},
            'Invoke'
        )
        
        ml_results = invoke_ml_inference(sample_iot_message)
        
        # Verify default values returned
        assert ml_results['wqi'] == 50.0
        assert ml_results['anomalyType'] == 'unknown'
        assert ml_results['confidence'] == 0.0
        assert 'error' in ml_results
    
    def test_invoke_ml_inference_with_contamination_detected(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test ML inference with contamination detection"""
        # Mock Lambda invoke with contamination
        mock_aws_clients['lambda'].invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({
                    'wqi': 35.0,
                    'anomalyType': 'contamination',
                    'confidence': 0.92
                })
            }).encode())
        }
        
        ml_results = invoke_ml_inference(sample_iot_message)
        
        # Verify contamination detected
        assert ml_results['wqi'] < 50
        assert ml_results['anomalyType'] == 'contamination'


class TestDynamoDBStorage:
    """Test suite for DynamoDB storage"""
    
    def test_store_reading_in_dynamodb(self, mock_aws_environment, mock_aws_clients, sample_iot_message, sample_ml_results):
        """Test storing processed reading in DynamoDB"""
        s3_reference = 's3://test-data-lake/raw-readings/test.json'
        
        # Mock DynamoDB operations
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            mock_ops_instance.store_reading.return_value = {
                'device_id': 'DEV-0001',
                'timestamp': '2025-10-25T12:00:00Z',
                'wqi': 85.5,
                'ledgerSequence': 12345
            }
            
            stored_reading = store_reading_dynamodb(sample_iot_message, sample_ml_results, s3_reference)
            
            # Verify stored reading
            assert stored_reading['device_id'] == 'DEV-0001'
            assert stored_reading['wqi'] == 85.5
            assert 'ledgerSequence' in stored_reading
            
            # Verify store_reading was called
            mock_ops_instance.store_reading.assert_called_once()
    
    def test_store_reading_with_ledger_entry(self, mock_aws_environment, mock_aws_clients, sample_iot_message, sample_ml_results):
        """Test that reading includes immutable ledger entry"""
        s3_reference = 's3://test-data-lake/raw-readings/test.json'
        
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            mock_ops_instance.store_reading.return_value = {
                'device_id': 'DEV-0001',
                'timestamp': '2025-10-25T12:00:00Z',
                'ledgerSequence': 12345,
                'ledgerHash': 'abc123def456'
            }
            
            stored_reading = store_reading_dynamodb(sample_iot_message, sample_ml_results, s3_reference)
            
            # Verify ledger fields
            assert 'ledgerSequence' in stored_reading
            assert 'ledgerHash' in stored_reading
    
    def test_store_reading_dynamodb_failure(self, mock_aws_environment, sample_iot_message, sample_ml_results):
        """Test DynamoDB storage failure handling"""
        from errors import DatabaseError
        
        s3_reference = 's3://test-data-lake/raw-readings/test.json'
        
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            # Mock DynamoDB failure
            mock_ops_instance.store_reading.side_effect = Exception('DynamoDB error')
            
            # Should raise DatabaseError
            with pytest.raises(DatabaseError) as exc_info:
                store_reading_dynamodb(sample_iot_message, sample_ml_results, s3_reference)
            
            assert 'dynamodb' in str(exc_info.value).lower()


class TestCompleteDataPipelineWorkflow:
    """Test suite for complete end-to-end data pipeline workflow"""
    
    def test_complete_pipeline_success(self, mock_aws_environment, mock_aws_clients, sample_iot_message, sample_ml_results):
        """Test complete successful data pipeline from IoT message to storage"""
        # Mock all AWS operations
        mock_aws_clients['dynamodb_table'].get_item.return_value = {}  # No duplicate
        mock_aws_clients['s3'].put_object.return_value = {}
        mock_aws_clients['lambda'].invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps(sample_ml_results)
            }).encode())
        }
        
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            mock_ops_instance.store_reading.return_value = {
                'device_id': 'DEV-0001',
                'timestamp': '2025-10-25T12:00:00Z',
                'wqi': 85.5,
                'ledgerSequence': 12345
            }
            
            # Create event
            event = sample_iot_message
            context = MagicMock()
            context.request_id = 'test-request-123'
            
            # Execute pipeline
            response = lambda_handler(event, context)
            
            # Verify success response
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            
            assert body['message'] == 'Data processed successfully'
            assert body['deviceId'] == 'DEV-0001'
            assert body['wqi'] == 85.5
            assert body['anomalyType'] == 'normal'
            assert 'ledgerSequence' in body
            
            # Verify all pipeline steps executed
            mock_aws_clients['dynamodb_table'].get_item.assert_called_once()  # Duplicate check
            mock_aws_clients['s3'].put_object.assert_called_once()  # S3 storage
            mock_aws_clients['lambda'].invoke.assert_called_once()  # ML inference
            mock_ops_instance.store_reading.assert_called_once()  # DynamoDB storage
    
    def test_complete_pipeline_with_validation_error(self, mock_aws_environment, mock_aws_clients):
        """Test pipeline with validation error"""
        from errors import ValidationError
        
        # Invalid IoT message (missing required fields)
        invalid_message = {
            'deviceId': 'DEV-0001'
            # Missing timestamp, readings, etc.
        }
        
        event = invalid_message
        context = MagicMock()
        context.request_id = 'test-request-123'
        
        # Mock SQS for DLQ
        mock_aws_clients['sqs'].send_message.return_value = {}
        
        # Execute pipeline
        with pytest.raises(ValidationError):
            lambda_handler(event, context)
        
        # Verify message sent to DLQ
        mock_aws_clients['sqs'].send_message.assert_called_once()
    
    def test_complete_pipeline_with_duplicate_data(self, mock_aws_environment, mock_aws_clients, sample_iot_message):
        """Test pipeline with duplicate data detection"""
        from errors import ValidationError
        
        # Mock duplicate found
        mock_aws_clients['dynamodb_table'].get_item.return_value = {
            'Item': {
                'deviceId_month': 'DEV-0001#202510',
                'timestamp': '2025-10-25T12:00:00Z'
            }
        }
        
        event = sample_iot_message
        context = MagicMock()
        context.request_id = 'test-request-123'
        
        # Execute pipeline
        with pytest.raises(ValidationError) as exc_info:
            lambda_handler(event, context)
        
        # Verify duplicate error
        assert 'duplicate' in str(exc_info.value).lower()
    
    def test_complete_pipeline_performance(self, mock_aws_environment, mock_aws_clients, sample_iot_message, sample_ml_results):
        """Test pipeline performance metrics"""
        # Mock all AWS operations
        mock_aws_clients['dynamodb_table'].get_item.return_value = {}
        mock_aws_clients['s3'].put_object.return_value = {}
        mock_aws_clients['lambda'].invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps(sample_ml_results)
            }).encode())
        }
        
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            mock_ops_instance.store_reading.return_value = {
                'device_id': 'DEV-0001',
                'timestamp': '2025-10-25T12:00:00Z',
                'wqi': 85.5,
                'ledgerSequence': 12345
            }
            
            event = sample_iot_message
            context = MagicMock()
            context.request_id = 'test-request-123'
            
            # Measure execution time
            start_time = time.time()
            response = lambda_handler(event, context)
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            # Verify response
            assert response['statusCode'] == 200
            
            # Performance should be reasonable (< 5 seconds for mocked operations)
            assert duration_ms < 5000
    
    def test_pipeline_with_multiple_concurrent_messages(self, mock_aws_environment, mock_aws_clients, sample_ml_results):
        """Test pipeline handling multiple concurrent messages"""
        # Create multiple IoT messages
        messages = []
        for i in range(5):
            message = {
                'deviceId': f'DEV-000{i}',
                'timestamp': f'2025-10-25T12:0{i}:00Z',
                'location': {'latitude': 37.7749, 'longitude': -122.4194},
                'readings': {'pH': 7.0 + i * 0.1, 'turbidity': 2.0, 'tds': 300.0, 'temperature': 20.0, 'humidity': 60.0},
                'diagnostics': {'batteryLevel': 80.0, 'signalStrength': -70.0, 'sensorStatus': 'normal'}
            }
            messages.append(message)
        
        # Mock AWS operations
        mock_aws_clients['dynamodb_table'].get_item.return_value = {}
        mock_aws_clients['s3'].put_object.return_value = {}
        mock_aws_clients['lambda'].invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps(sample_ml_results)
            }).encode())
        }
        
        with patch('handler.DynamoDBOperations') as mock_db_ops:
            mock_ops_instance = MagicMock()
            mock_db_ops.return_value = mock_ops_instance
            
            mock_ops_instance.store_reading.return_value = {
                'device_id': 'DEV-0000',
                'timestamp': '2025-10-25T12:00:00Z',
                'wqi': 85.5,
                'ledgerSequence': 12345
            }
            
            context = MagicMock()
            context.request_id = 'test-request-123'
            
            # Process all messages
            responses = []
            for message in messages:
                response = lambda_handler(message, context)
                responses.append(response)
            
            # Verify all succeeded
            assert all(r['statusCode'] == 200 for r in responses)
            
            # Verify all pipeline steps executed for each message
            assert mock_aws_clients['s3'].put_object.call_count == 5
            assert mock_aws_clients['lambda'].invoke.call_count == 5
            assert mock_ops_instance.store_reading.call_count == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
