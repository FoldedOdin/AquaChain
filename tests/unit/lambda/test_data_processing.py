"""
Unit tests for data_processing Lambda function
Target: 80% code coverage
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add lambda path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'data_processing'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

from handler import (
    lambda_handler,
    extract_iot_data,
    validate_and_sanitize_data,
    check_for_duplicates,
    store_raw_data_s3,
    invoke_ml_inference,
    store_reading_dynamodb,
    is_critical_event,
    DataProcessingError,
    DuplicateDataError
)


@pytest.fixture
def valid_iot_data():
    """Fixture providing valid IoT sensor data"""
    return {
        'deviceId': 'DEV-1234',
        'timestamp': '2025-10-25T12:00:00Z',
        'location': {
            'latitude': 40.7128,
            'longitude': -74.0060
        },
        'readings': {
            'pH': 7.2,
            'turbidity': 5.0,
            'tds': 300.0,
            'temperature': 25.0
        },
        'diagnostics': {
            'batteryLevel': 85.0,
            'signalStrength': -65.0,
            'sensorStatus': 'normal'
        }
    }


@pytest.fixture
def lambda_context():
    """Fixture providing Lambda context"""
    context = Mock()
    context.request_id = 'test-request-123'
    context.function_name = 'data-processing'
    return context


class TestExtractIotData:
    """Test IoT data extraction from various event sources"""
    
    def test_extract_from_direct_invocation(self, valid_iot_data):
        """Test extraction from direct Lambda invocation"""
        result = extract_iot_data(valid_iot_data)
        assert result == valid_iot_data
    
    def test_extract_from_sns_event(self, valid_iot_data):
        """Test extraction from SNS trigger"""
        sns_event = {
            'Records': [{
                'Sns': {
                    'Message': json.dumps(valid_iot_data)
                }
            }]
        }
        result = extract_iot_data(sns_event)
        assert result == valid_iot_data
    
    def test_extract_from_sqs_event(self, valid_iot_data):
        """Test extraction from SQS trigger"""
        sqs_event = {
            'Records': [{
                'body': json.dumps(valid_iot_data)
            }]
        }
        result = extract_iot_data(sqs_event)
        assert result == valid_iot_data


class TestValidateAndSanitizeData:
    """Test data validation and sanitization"""
    
    def test_valid_data_passes_validation(self, valid_iot_data):
        """Test that valid data passes validation"""
        result = validate_and_sanitize_data(valid_iot_data)
        assert result['deviceId'] == 'DEV-1234'
        assert result['readings']['pH'] == 7.2
    
    def test_timestamp_normalization(self, valid_iot_data):
        """Test timestamp is normalized to ISO format with Z"""
        valid_iot_data['timestamp'] = '2025-10-25T12:00:00'
        result = validate_and_sanitize_data(valid_iot_data)
        assert result['timestamp'].endswith('Z')
    
    def test_sensor_value_rounding(self, valid_iot_data):
        """Test sensor values are rounded to appropriate precision"""
        valid_iot_data['readings']['pH'] = 7.12345
        valid_iot_data['readings']['turbidity'] = 5.12345
        result = validate_and_sanitize_data(valid_iot_data)
        assert result['readings']['pH'] == 7.12
        assert result['readings']['turbidity'] == 5.1
    
    def test_invalid_ph_range_raises_error(self, valid_iot_data):
        """Test that pH outside valid range raises ValidationError"""
        from errors import ValidationError
        valid_iot_data['readings']['pH'] = 15.0
        with pytest.raises(ValidationError) as exc_info:
            validate_and_sanitize_data(valid_iot_data)
        assert 'pH value out of valid range' in str(exc_info.value)
    
    def test_invalid_turbidity_range_raises_error(self, valid_iot_data):
        """Test that turbidity outside valid range raises ValidationError"""
        from errors import ValidationError
        valid_iot_data['readings']['turbidity'] = 5000.0
        with pytest.raises(ValidationError) as exc_info:
            validate_and_sanitize_data(valid_iot_data)
        assert 'Turbidity value out of valid range' in str(exc_info.value)
    
    def test_invalid_temperature_range_raises_error(self, valid_iot_data):
        """Test that temperature outside valid range raises ValidationError"""
        from errors import ValidationError
        valid_iot_data['readings']['temperature'] = 150.0
        with pytest.raises(ValidationError) as exc_info:
            validate_and_sanitize_data(valid_iot_data)
        assert 'Temperature value out of valid range' in str(exc_info.value)


class TestCheckForDuplicates:
    """Test duplicate detection logic"""
    
    @patch('handler.dynamodb')
    def test_no_duplicate_passes(self, mock_dynamodb, valid_iot_data):
        """Test that non-duplicate data passes check"""
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        # Should not raise exception
        check_for_duplicates(valid_iot_data)
    
    @patch('handler.dynamodb')
    def test_duplicate_raises_error(self, mock_dynamodb, valid_iot_data):
        """Test that duplicate data raises DuplicateDataError"""
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': {'deviceId': 'DEV-1234'}}
        mock_dynamodb.Table.return_value = mock_table
        
        with pytest.raises(DuplicateDataError):
            check_for_duplicates(valid_iot_data)


class TestStoreRawDataS3:
    """Test S3 storage functionality"""
    
    @patch('handler.s3_client')
    def test_successful_s3_storage(self, mock_s3, valid_iot_data):
        """Test successful storage of raw data in S3"""
        mock_s3.put_object.return_value = {}
        
        result = store_raw_data_s3(valid_iot_data)
        
        assert result.startswith('s3://')
        assert 'raw-readings' in result
        mock_s3.put_object.assert_called_once()
    
    @patch('handler.s3_client')
    def test_s3_storage_with_partitioning(self, mock_s3, valid_iot_data):
        """Test that S3 key includes proper partitioning"""
        mock_s3.put_object.return_value = {}
        
        result = store_raw_data_s3(valid_iot_data)
        
        # Check partitioning structure
        assert 'year=' in result
        assert 'month=' in result
        assert 'day=' in result
        assert 'hour=' in result
    
    @patch('handler.s3_client')
    def test_s3_storage_failure_raises_error(self, mock_s3, valid_iot_data):
        """Test that S3 storage failure raises DatabaseError"""
        from errors import DatabaseError
        mock_s3.put_object.side_effect = Exception('S3 error')
        
        with pytest.raises(DatabaseError):
            store_raw_data_s3(valid_iot_data)


class TestInvokeMLInference:
    """Test ML inference invocation"""
    
    @patch('handler.lambda_client')
    def test_successful_ml_inference(self, mock_lambda, valid_iot_data):
        """Test successful ML inference invocation"""
        ml_response = {
            'wqi': 85.5,
            'anomalyType': 'normal',
            'confidence': 0.95
        }
        
        mock_payload = Mock()
        mock_payload.read.return_value = json.dumps({
            'statusCode': 200,
            'body': json.dumps(ml_response)
        }).encode()
        
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': mock_payload
        }
        
        result = invoke_ml_inference(valid_iot_data)
        
        assert result['wqi'] == 85.5
        assert result['anomalyType'] == 'normal'
        mock_lambda.invoke.assert_called_once()
    
    @patch('handler.lambda_client')
    def test_ml_inference_failure_returns_defaults(self, mock_lambda, valid_iot_data):
        """Test that ML inference failure returns default values"""
        mock_lambda.invoke.side_effect = Exception('ML error')
        
        result = invoke_ml_inference(valid_iot_data)
        
        assert result['wqi'] == 50.0
        assert result['anomalyType'] == 'unknown'
        assert result['confidence'] == 0.0


class TestStoreReadingDynamoDB:
    """Test DynamoDB storage functionality"""
    
    @patch('handler.dynamodb')
    def test_successful_dynamodb_storage(self, mock_dynamodb, valid_iot_data):
        """Test successful storage in DynamoDB"""
        ml_results = {'wqi': 85.5, 'anomalyType': 'normal'}
        s3_reference = 's3://bucket/key'
        
        mock_table = Mock()
        mock_table.put_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        with patch('handler.DynamoDBOperations') as mock_ops:
            mock_ops_instance = Mock()
            mock_ops_instance.store_reading.return_value = {
                'deviceId': 'DEV-1234',
                'ledgerSequence': 12345
            }
            mock_ops.return_value = mock_ops_instance
            
            result = store_reading_dynamodb(valid_iot_data, ml_results, s3_reference)
            
            assert 'ledgerSequence' in result


class TestIsCriticalEvent:
    """Test critical event detection"""
    
    def test_low_wqi_is_critical(self):
        """Test that low WQI is flagged as critical"""
        ml_results = {'wqi': 45.0, 'anomalyType': 'normal'}
        assert is_critical_event(ml_results) is True
    
    def test_contamination_is_critical(self):
        """Test that contamination is flagged as critical"""
        ml_results = {'wqi': 80.0, 'anomalyType': 'contamination'}
        assert is_critical_event(ml_results) is True
    
    def test_normal_event_not_critical(self):
        """Test that normal readings are not critical"""
        ml_results = {'wqi': 85.0, 'anomalyType': 'normal'}
        assert is_critical_event(ml_results) is False


class TestLambdaHandler:
    """Test main Lambda handler"""
    
    @patch('handler.store_reading_dynamodb')
    @patch('handler.invoke_ml_inference')
    @patch('handler.store_raw_data_s3')
    @patch('handler.check_for_duplicates')
    @patch('handler.validate_and_sanitize_data')
    @patch('handler.extract_iot_data')
    def test_successful_processing_flow(
        self, mock_extract, mock_validate, mock_check_dup,
        mock_s3, mock_ml, mock_dynamodb, valid_iot_data, lambda_context
    ):
        """Test complete successful processing flow"""
        mock_extract.return_value = valid_iot_data
        mock_validate.return_value = valid_iot_data
        mock_check_dup.return_value = None
        mock_s3.return_value = 's3://bucket/key'
        mock_ml.return_value = {'wqi': 85.5, 'anomalyType': 'normal', 'confidence': 0.95}
        mock_dynamodb.return_value = {'ledgerSequence': 12345}
        
        response = lambda_handler(valid_iot_data, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['wqi'] == 85.5
        assert body['deviceId'] == 'DEV-1234'
    
    @patch('handler.extract_iot_data')
    @patch('handler.validate_and_sanitize_data')
    def test_validation_error_handling(
        self, mock_validate, mock_extract, valid_iot_data, lambda_context
    ):
        """Test that validation errors are handled properly"""
        from errors import ValidationError as AquaChainValidationError
        
        mock_extract.return_value = valid_iot_data
        mock_validate.side_effect = AquaChainValidationError(
            message="Invalid data",
            details={'field': 'pH'}
        )
        
        with pytest.raises(AquaChainValidationError):
            lambda_handler(valid_iot_data, lambda_context)
    
    @patch('handler.extract_iot_data')
    @patch('handler.validate_and_sanitize_data')
    @patch('handler.check_for_duplicates')
    def test_duplicate_error_handling(
        self, mock_check_dup, mock_validate, mock_extract,
        valid_iot_data, lambda_context
    ):
        """Test that duplicate errors are handled properly"""
        from errors import ValidationError as AquaChainValidationError
        
        mock_extract.return_value = valid_iot_data
        mock_validate.return_value = valid_iot_data
        mock_check_dup.side_effect = DuplicateDataError(
            "Duplicate data",
            device_id='DEV-1234',
            timestamp='2025-10-25T12:00:00Z'
        )
        
        with pytest.raises(AquaChainValidationError):
            lambda_handler(valid_iot_data, lambda_context)
