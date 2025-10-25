"""
Data Processing Lambda Function for AquaChain System
Handles IoT device data validation, sanitization, and orchestration
"""

import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from jsonschema import validate, ValidationError
import logging
import sys
import os

# Add shared utilities to path
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import X-Ray tracing utilities
from xray_utils import AquaChainTracer, trace_lambda_handler, EndToEndTracer

# Import error handling
from errors import ValidationError as AquaChainValidationError, DatabaseError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Import cold start monitoring
from cold_start_monitor import monitor_cold_start, PerformanceTimer

# Import audit logging
from audit_logger import audit_logger

# Configure structured logging
logger = get_logger(__name__, service='data-processing')

# Initialize tracer
tracer = AquaChainTracer('data-processing')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs')

# Environment variables
READINGS_TABLE = 'aquachain-readings'
DATA_LAKE_BUCKET = 'aquachain-data-lake'
ML_INFERENCE_FUNCTION = 'AquaChain-ML-Inference'
DLQ_URL = 'https://sqs.us-east-1.amazonaws.com/123456789012/aquachain-dlq'

# JSON Schema for IoT device data validation
IOT_DATA_SCHEMA = {
    "type": "object",
    "required": ["deviceId", "timestamp", "location", "readings", "diagnostics"],
    "properties": {
        "deviceId": {
            "type": "string",
            "pattern": "^DEV-[0-9]{4}$"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "location": {
            "type": "object",
            "required": ["latitude", "longitude"],
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180}
            }
        },
        "readings": {
            "type": "object",
            "required": ["pH", "turbidity", "tds", "temperature", "humidity"],
            "properties": {
                "pH": {"type": "number", "minimum": 0, "maximum": 14},
                "turbidity": {"type": "number", "minimum": 0, "maximum": 4000},
                "tds": {"type": "number", "minimum": 0, "maximum": 5000},
                "temperature": {"type": "number", "minimum": -40, "maximum": 125},
                "humidity": {"type": "number", "minimum": 0, "maximum": 100}
            }
        },
        "diagnostics": {
            "type": "object",
            "required": ["batteryLevel", "signalStrength", "sensorStatus"],
            "properties": {
                "batteryLevel": {"type": "number", "minimum": 0, "maximum": 100},
                "signalStrength": {"type": "number", "minimum": -120, "maximum": 0},
                "sensorStatus": {"type": "string", "enum": ["normal", "warning", "error"]}
            }
        }
    }
}

class DataProcessingError(Exception):
    """Custom exception for data processing errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize DataProcessingError.
        
        Args:
            message: Error message describing the issue
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class DuplicateDataError(Exception):
    """Exception for duplicate data detection"""
    
    def __init__(self, message: str, device_id: Optional[str] = None, 
                 timestamp: Optional[str] = None) -> None:
        """
        Initialize DuplicateDataError.
        
        Args:
            message: Error message describing the duplicate
            device_id: Optional device identifier
            timestamp: Optional timestamp of duplicate reading
        """
        self.message = message
        self.device_id = device_id
        self.timestamp = timestamp
        super().__init__(self.message)

@monitor_cold_start
@handle_errors
@trace_lambda_handler('data-processing')
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for IoT data processing.
    
    Processes incoming IoT sensor data through validation, ML inference,
    storage, and alert detection pipeline.
    
    Args:
        event: Lambda event containing IoT sensor data. Can be from direct
               invocation, SNS, SQS, or IoT Rule trigger
        context: Lambda context object with runtime information
    
    Returns:
        Dict containing:
            - statusCode: HTTP status code (200 for success, 4xx/5xx for errors)
            - body: JSON string with processing results or error message
            - headers: Optional response headers
    
    Raises:
        ValidationError: When input data fails schema validation
        DuplicateDataError: When duplicate reading is detected
        DataProcessingError: When processing pipeline fails
    """
    try:
        request_id = context.request_id if hasattr(context, 'request_id') else None
        start_time = datetime.utcnow()
        
        logger.info(
            "Processing IoT data event",
            request_id=request_id,
            event_source=event.get('Records', [{}])[0].get('eventSource') if 'Records' in event else 'direct'
        )
        
        # Extract IoT data from event
        iot_data = extract_iot_data(event)
        
        # Start end-to-end tracing
        trace_id = f"{iot_data['deviceId']}-{iot_data['timestamp']}"
        EndToEndTracer.start_trace(trace_id, 'iot_device', 'sensor_reading')
        
        # Validate and sanitize data
        validated_data = validate_and_sanitize_data(iot_data)
        
        # Check for duplicates
        check_for_duplicates(validated_data)
        
        # Store raw data in S3
        s3_reference = store_raw_data_s3(validated_data)
        
        # Invoke ML inference for WQI calculation
        ml_results = invoke_ml_inference(validated_data)
        
        # Store processed data in DynamoDB
        stored_reading = store_reading_dynamodb(validated_data, ml_results, s3_reference)
        
        # Alert detection will be handled by DynamoDB Streams trigger
        # No need to manually trigger alerts here as the alert detection Lambda
        # will be triggered automatically when data is written to DynamoDB
        
        # Log performance metrics
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            "Data processing completed successfully",
            request_id=request_id,
            device_id=validated_data['deviceId'],
            wqi=ml_results['wqi'],
            anomaly_type=ml_results['anomalyType'],
            duration_ms=duration_ms
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data processed successfully',
                'deviceId': validated_data['deviceId'],
                'timestamp': validated_data['timestamp'],
                'wqi': ml_results['wqi'],
                'anomalyType': ml_results['anomalyType'],
                'ledgerSequence': stored_reading.get('ledgerSequence')
            })
        }
        
    except ValidationError as e:
        logger.error(
            "Data validation error",
            request_id=request_id,
            error_code='VALIDATION_ERROR',
            error_message=str(e)
        )
        send_to_dlq(event, f"Validation error: {e}")
        raise AquaChainValidationError(
            message="Invalid data format",
            details={'validation_error': str(e)}
        )
        
    except DuplicateDataError as e:
        logger.warning(
            "Duplicate data detected",
            request_id=request_id,
            device_id=e.device_id,
            timestamp=e.timestamp
        )
        raise AquaChainValidationError(
            message="Duplicate data detected",
            error_code='DUPLICATE_DATA',
            details={'device_id': e.device_id, 'timestamp': e.timestamp}
        )
        
    except DataProcessingError as e:
        logger.error(
            "Data processing error",
            request_id=request_id,
            error_code='PROCESSING_ERROR',
            error_message=e.message,
            error_details=e.details
        )
        send_to_dlq(event, f"Processing error: {e}")
        raise DatabaseError(
            message="Data processing failed",
            details=e.details
        )

def extract_iot_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract IoT data from Lambda event.
    
    Handles multiple event sources including direct invocation,
    SNS notifications, SQS messages, and IoT Rule triggers.
    
    Args:
        event: Lambda event dictionary from various sources
    
    Returns:
        Extracted IoT sensor data as dictionary
    
    Raises:
        KeyError: When required event fields are missing
        json.JSONDecodeError: When event payload is not valid JSON
    """
    if 'Records' in event:
        # SNS/SQS trigger
        record: Dict[str, Any] = event['Records'][0]
        if 'Sns' in record:
            message: str = record['Sns']['Message']
            parsed_message: Dict[str, Any] = json.loads(message)
            return parsed_message
        elif 'body' in record:
            body: str = record['body']
            parsed_body: Dict[str, Any] = json.loads(body)
            return parsed_body
    
    # Direct invocation or IoT Rule
    return event

@tracer.trace_critical_path('validate_sensor_data')
def validate_and_sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate IoT data against schema and sanitize values.
    
    Performs JSON schema validation and additional range checks for
    sensor readings. Sanitizes timestamp format and rounds sensor
    values to appropriate precision.
    
    Args:
        data: Raw IoT sensor data dictionary containing deviceId,
              timestamp, location, readings, and diagnostics
    
    Returns:
        Validated and sanitized data dictionary with:
            - Normalized timestamp in ISO format with 'Z' suffix
            - Rounded sensor values to appropriate precision
            - All fields validated against schema and ranges
    
    Raises:
        ValidationError: When data fails schema validation or range checks
    """
    try:
        # Validate against JSON schema
        validate(instance=data, schema=IOT_DATA_SCHEMA)
        
        # Additional range validation
        readings = data['readings']
        
        # pH validation (6.5-8.5 is safe range)
        if not (0 <= readings['pH'] <= 14):
            raise AquaChainValidationError(
                message="pH value out of valid range",
                details={'value': readings['pH'], 'valid_range': '0-14'}
            )
        
        # Turbidity validation (0-4000 NTU)
        if not (0 <= readings['turbidity'] <= 4000):
            raise AquaChainValidationError(
                message="Turbidity value out of valid range",
                details={'value': readings['turbidity'], 'valid_range': '0-4000'}
            )
        
        # TDS validation (0-5000 ppm)
        if not (0 <= readings['tds'] <= 5000):
            raise AquaChainValidationError(
                message="TDS value out of valid range",
                details={'value': readings['tds'], 'valid_range': '0-5000'}
            )
        
        # Temperature validation (-40 to 125°C)
        if not (-40 <= readings['temperature'] <= 125):
            raise AquaChainValidationError(
                message="Temperature value out of valid range",
                details={'value': readings['temperature'], 'valid_range': '-40 to 125'}
            )
        
        # Humidity validation (0-100%)
        if not (0 <= readings['humidity'] <= 100):
            raise AquaChainValidationError(
                message="Humidity value out of valid range",
                details={'value': readings['humidity'], 'valid_range': '0-100'}
            )
        
        # Sanitize timestamp to ISO format
        timestamp = data['timestamp']
        if not timestamp.endswith('Z'):
            timestamp += 'Z'
        data['timestamp'] = timestamp
        
        # Round sensor values to appropriate precision
        data['readings']['pH'] = round(readings['pH'], 2)
        data['readings']['turbidity'] = round(readings['turbidity'], 1)
        data['readings']['tds'] = round(readings['tds'], 0)
        data['readings']['temperature'] = round(readings['temperature'], 1)
        data['readings']['humidity'] = round(readings['humidity'], 1)
        
        logger.info(
            "Data validation successful",
            device_id=data['deviceId'],
            ph=data['readings']['pH'],
            turbidity=data['readings']['turbidity'],
            tds=data['readings']['tds']
        )
        return data
        
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise

def check_for_duplicates(data: Dict[str, Any]) -> None:
    """
    Check for duplicate readings using device ID and timestamp.
    
    Queries DynamoDB to detect if a reading with the same device ID
    and timestamp already exists. Uses time-windowed partition keys
    for efficient lookups.
    
    Args:
        data: Validated sensor data containing deviceId and timestamp
    
    Returns:
        None
    
    Raises:
        DuplicateDataError: When duplicate reading is found
    """
    device_id = data['deviceId']
    timestamp = data['timestamp']
    
    # Generate partition key for time-windowed lookup
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    partition_key = f"{device_id}#{dt.strftime('%Y%m')}"
    
    try:
        table = dynamodb.Table(READINGS_TABLE)
        response = table.get_item(
            Key={
                'deviceId_month': partition_key,
                'timestamp': timestamp
            }
        )
        
        if 'Item' in response:
            raise DuplicateDataError(f"Duplicate reading for device {device_id} at {timestamp}")
            
    except Exception as e:
        if isinstance(e, DuplicateDataError):
            raise
        logger.warning(
            "Error checking duplicates",
            device_id=device_id,
            error_message=str(e)
        )
        # Continue processing if duplicate check fails

@tracer.trace_external_call('s3', 'put_object')
def store_raw_data_s3(data: Dict[str, Any]) -> str:
    """
    Store raw IoT data in S3 data lake with partitioned structure.
    
    Stores raw sensor data in S3 with Hive-style partitioning by
    year/month/day/hour for efficient querying. Applies KMS encryption
    and adds metadata tags.
    
    Args:
        data: Validated sensor data to store
    
    Returns:
        S3 URI string in format 's3://bucket/key'
    
    Raises:
        DataProcessingError: When S3 storage operation fails
        ClientError: When AWS S3 API call fails
    """
    device_id = data['deviceId']
    timestamp = data['timestamp']
    
    # Parse timestamp for partitioning
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    # Create S3 key with partitioning
    s3_key = (f"raw-readings/"
              f"year={dt.year}/"
              f"month={dt.month:02d}/"
              f"day={dt.day:02d}/"
              f"hour={dt.hour:02d}/"
              f"{device_id}-{dt.strftime('%Y%m%d%H%M%S')}.json")
    
    try:
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            ServerSideEncryption='aws:kms',
            Metadata={
                'deviceId': device_id,
                'timestamp': timestamp,
                'dataType': 'raw-reading'
            }
        )
        
        s3_reference = f"s3://{DATA_LAKE_BUCKET}/{s3_key}"
        logger.info(
            "Stored raw data in S3",
            device_id=device_id,
            s3_reference=s3_reference
        )
        return s3_reference
        
    except Exception as e:
        logger.error(
            "Error storing data in S3",
            device_id=device_id,
            error_message=str(e)
        )
        raise DatabaseError(
            message="Failed to store raw data in S3",
            details={'device_id': device_id, 'error': str(e)}
        )

@tracer.trace_external_call('lambda', 'invoke_ml_inference')
def invoke_ml_inference(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ML inference Lambda for WQI calculation and anomaly detection.
    
    Synchronously invokes the ML inference Lambda function to calculate
    Water Quality Index (WQI) and detect anomalies. Returns default
    values if ML inference fails to prevent pipeline disruption.
    
    Args:
        data: Validated sensor data containing readings and location
    
    Returns:
        Dictionary containing ML inference results:
            - wqi: Water Quality Index (0-100)
            - anomalyType: Type of anomaly detected ('normal', 'contamination', etc.)
            - confidence: Confidence score (0.0-1.0)
            - error: Optional error message if inference failed
    
    Raises:
        DataProcessingError: When ML inference fails critically
    """
    try:
        payload = {
            'deviceId': data['deviceId'],
            'timestamp': data['timestamp'],
            'readings': data['readings'],
            'location': data['location']
        }
        
        response = lambda_client.invoke(
            FunctionName=ML_INFERENCE_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        payload_data = response['Payload'].read()
        result: Dict[str, Any] = json.loads(payload_data)
        
        if response['StatusCode'] != 200:
            raise DataProcessingError(f"ML inference failed: {result}")
        
        # Parse ML results
        body_str: str = result['body']
        ml_results: Dict[str, Any] = json.loads(body_str)
        
        logger.info(
            "ML inference completed",
            device_id=data['deviceId'],
            wqi=ml_results['wqi'],
            anomaly_type=ml_results['anomalyType'],
            confidence=ml_results.get('confidence', 0.0)
        )
        
        return ml_results
        
    except Exception as e:
        logger.error(
            "ML inference error",
            device_id=data['deviceId'],
            error_message=str(e)
        )
        # Return default values if ML fails
        return {
            'wqi': 50.0,  # Neutral WQI
            'anomalyType': 'unknown',
            'confidence': 0.0,
            'error': str(e)
        }

@tracer.trace_external_call('dynamodb', 'put_item')
def store_reading_dynamodb(data: Dict[str, Any], ml_results: Dict[str, Any], 
                          s3_reference: str) -> Dict[str, Any]:
    """
    Store processed reading in DynamoDB with ledger entry.
    
    Stores the processed sensor reading in DynamoDB along with ML
    inference results and S3 reference. Creates immutable ledger
    entry for audit trail.
    
    Args:
        data: Validated sensor data
        ml_results: ML inference results including WQI and anomaly type
        s3_reference: S3 URI where raw data is stored
    
    Returns:
        Dictionary containing stored reading with ledger sequence number
    
    Raises:
        DataProcessingError: When DynamoDB storage operation fails
        ClientError: When AWS DynamoDB API call fails
    """
    try:
        # Import DynamoDB operations
        import sys
        sys.path.append('/opt/python')  # Lambda layer path
        from infrastructure.dynamodb.operations import DynamoDBOperations
        
        db_ops = DynamoDBOperations()
        
        # Store reading with ledger entry
        stored_reading = db_ops.store_reading(
            device_id=data['deviceId'],
            timestamp=data['timestamp'],
            readings=data['readings'],
            wqi=ml_results['wqi'],
            anomaly_type=ml_results['anomalyType'],
            location=data['location'],
            diagnostics=data['diagnostics'],
            s3_reference=s3_reference
        )
        
        logger.info(
            "Stored reading in DynamoDB",
            device_id=data['deviceId'],
            ledger_sequence=stored_reading.get('ledgerSequence'),
            wqi=ml_results['wqi']
        )
        
        return stored_reading
        
    except Exception as e:
        logger.error(
            "Error storing reading in DynamoDB",
            device_id=data['deviceId'],
            error_message=str(e)
        )
        raise DatabaseError(
            message="Failed to store reading in DynamoDB",
            details={'device_id': data['deviceId'], 'error': str(e)}
        )

def is_critical_event(ml_results: Dict[str, Any]) -> bool:
    """
    Determine if reading represents a critical water quality event.
    
    Evaluates ML inference results to determine if the reading
    represents a critical event requiring immediate attention.
    
    Args:
        ml_results: ML inference results containing WQI and anomaly type
    
    Returns:
        True if event is critical (WQI < 50 or contamination detected),
        False otherwise
    """
    wqi: float = float(ml_results.get('wqi', 100))
    anomaly_type: str = str(ml_results.get('anomalyType', 'normal'))
    
    # Critical if WQI below 50 or contamination detected
    return wqi < 50 or anomaly_type == 'contamination'

def trigger_alert_notification(data: Dict[str, Any], ml_results: Dict[str, Any]) -> None:
    """
    Trigger alert notification for critical events.
    
    Publishes critical water quality alerts to SNS topic for
    downstream processing and notification delivery.
    
    Args:
        data: Validated sensor data with device and location info
        ml_results: ML inference results with WQI and anomaly type
    
    Returns:
        None
    
    Raises:
        ClientError: When SNS publish operation fails (logged but not raised)
    """
    try:
        sns_client = boto3.client('sns')
        
        alert_message = {
            'deviceId': data['deviceId'],
            'timestamp': data['timestamp'],
            'location': data['location'],
            'wqi': ml_results['wqi'],
            'anomalyType': ml_results['anomalyType'],
            'alertType': 'critical',
            'readings': data['readings']
        }
        
        # Publish to SNS topic for alert processing
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:aquachain-critical-alerts',
            Message=json.dumps(alert_message),
            Subject=f'Critical Water Quality Alert - Device {data["deviceId"]}',
            MessageAttributes={
                'alertType': {'DataType': 'String', 'StringValue': 'critical'},
                'deviceId': {'DataType': 'String', 'StringValue': data['deviceId']},
                'wqi': {'DataType': 'Number', 'StringValue': str(ml_results['wqi'])}
            }
        )
        
        logger.info(
            "Triggered critical alert",
            device_id=data['deviceId'],
            wqi=ml_results['wqi'],
            anomaly_type=ml_results['anomalyType']
        )
        
    except Exception as e:
        logger.error(
            "Error triggering alert",
            device_id=data['deviceId'],
            error_message=str(e)
        )
        # Don't fail the entire process if alert fails

def send_to_dlq(event: Dict[str, Any], error_message: str) -> None:
    """
    Send failed events to dead letter queue for manual review.
    
    Sends events that failed processing to SQS dead letter queue
    with error context for manual investigation and retry.
    
    Args:
        event: Original Lambda event that failed processing
        error_message: Description of the error that occurred
    
    Returns:
        None
    
    Raises:
        ClientError: When SQS send operation fails (logged but not raised)
    """
    try:
        dlq_message = {
            'originalEvent': event,
            'errorMessage': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'processingAttempt': 1
        }
        
        sqs_client.send_message(
            QueueUrl=DLQ_URL,
            MessageBody=json.dumps(dlq_message),
            MessageAttributes={
                'errorType': {'DataType': 'String', 'StringValue': 'processing_error'},
                'deviceId': {'DataType': 'String', 'StringValue': event.get('deviceId', 'unknown')}
            }
        )
        
        logger.info(
            "Sent failed event to DLQ",
            error_message=error_message,
            device_id=event.get('deviceId', 'unknown')
        )
        
    except Exception as e:
        logger.error(
            "Error sending to DLQ",
            error_message=str(e)
        )

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Generates a consistent error response format for Lambda
    function returns.
    
    Args:
        status_code: HTTP status code (400, 409, 500, etc.)
        message: Human-readable error message
    
    Returns:
        Dictionary with statusCode, body (JSON string), and headers
    """
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }