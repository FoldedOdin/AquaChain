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
try:
    from jsonschema import validate, ValidationError as JsonSchemaValidationError
except ImportError:
    # Fallback if jsonschema is not available
    JsonSchemaValidationError = Exception
    def validate(instance, schema):
        """Fallback validation - basic type checking only"""
        pass
import logging
import sys
import os

# Add shared utilities to path
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import X-Ray tracing utilities (optional)
try:
    from xray_utils import AquaChainTracer, trace_lambda_handler, EndToEndTracer
    tracer = AquaChainTracer('data-processing')
except ImportError:
    # Fallback if xray_utils not available
    class AquaChainTracer:
        def __init__(self, name): pass
        def trace_critical_path(self, name): return lambda f: f
        def trace_external_call(self, service, operation): return lambda f: f
    tracer = AquaChainTracer('data-processing')
    def trace_lambda_handler(name): return lambda f: f
    class EndToEndTracer:
        @staticmethod
        def start_trace(trace_id, source, event_type): pass

# Import error handling (optional)
try:
    from errors import ValidationError as AquaChainValidationError, DatabaseError
    from error_handler import handle_errors
except ImportError:
    # Fallback error classes
    class AquaChainValidationError(Exception):
        def __init__(self, message, error_code=None, details=None):
            self.message = message
            self.error_code = error_code
            self.details = details or {}
            super().__init__(self.message)
    class DatabaseError(Exception):
        def __init__(self, message, details=None):
            self.message = message
            self.details = details or {}
            super().__init__(self.message)
    def handle_errors(f): return f

# Import structured logging (optional)
try:
    from structured_logger import get_logger
    logger = get_logger(__name__, service='data-processing')
except ImportError:
    # Fallback to standard logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
except Exception:
    # Fallback if get_logger fails for any reason
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Import cold start monitoring (optional)
try:
    from cold_start_monitor import monitor_cold_start, PerformanceTimer
except ImportError:
    def monitor_cold_start(f): return f
    class PerformanceTimer:
        def __init__(self, name): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass

# Import audit logging (optional)
try:
    from audit_logger import audit_logger
except ImportError:
    class AuditLogger:
        def log(self, *args, **kwargs): pass
    audit_logger = AuditLogger()

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')
sqs_client = boto3.client('sqs')
lambda_client = boto3.client('lambda')

# Environment variables
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings')
LEDGER_TABLE = os.environ.get('LEDGER_TABLE', 'aquachain-ledger')
SEQUENCE_TABLE = os.environ.get('SEQUENCE_TABLE', 'AquaChain-Sequence')
DATA_LAKE_BUCKET = os.environ.get('DATA_LAKE_BUCKET', None)  # Optional
SAGEMAKER_ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'aquachain-wqi-endpoint-dev')
DLQ_URL = os.environ.get('DLQ_URL', None)  # Optional
WEBSOCKET_CONNECTIONS_TABLE = os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', 'AquaChain-WebSocketConnections-dev')
WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_ENDPOINT', 'https://p2lgfqqy50.execute-api.ap-south-1.amazonaws.com/dev')

# Simplified validation - use basic Python checks instead of strict JSON schema
# This is more reliable and doesn't depend on jsonschema library
def validate_data_structure(data: Dict[str, Any]) -> None:
    """
    Validate data structure using simple Python checks.
    More reliable than JSON schema validation.
    """
    # Check required top-level fields
    required_fields = ["deviceId", "timestamp", "location", "readings", "diagnostics"]
    for field in required_fields:
        if field not in data:
            raise AquaChainValidationError(
                message=f"Missing required field: {field}",
                details={'missing_field': field}
            )
    
    # Validate deviceId format (DEV-XXXX or ESP32-XXX)
    device_id = data['deviceId']
    if not isinstance(device_id, str):
        raise AquaChainValidationError(
            message="deviceId must be a string",
            details={'deviceId': device_id}
        )
    
    # Validate location
    location = data['location']
    if not isinstance(location, dict):
        raise AquaChainValidationError(
            message="location must be an object",
            details={'location': location}
        )
    if 'latitude' not in location or 'longitude' not in location:
        raise AquaChainValidationError(
            message="location must have latitude and longitude",
            details={'location': location}
        )
    
    # Validate readings
    readings = data['readings']
    if not isinstance(readings, dict):
        raise AquaChainValidationError(
            message="readings must be an object",
            details={'readings': readings}
        )
    
    required_readings = ["pH", "turbidity", "tds", "temperature"]
    for reading in required_readings:
        if reading not in readings:
            raise AquaChainValidationError(
                message=f"Missing required reading: {reading}",
                details={'missing_reading': reading}
            )
    
    # Validate diagnostics
    diagnostics = data['diagnostics']
    if not isinstance(diagnostics, dict):
        raise AquaChainValidationError(
            message="diagnostics must be an object",
            details={'diagnostics': diagnostics}
        )
    
    required_diagnostics = ["batteryLevel", "signalStrength", "sensorStatus"]
    for diag in required_diagnostics:
        if diag not in diagnostics:
            raise AquaChainValidationError(
                message=f"Missing required diagnostic: {diag}",
                details={'missing_diagnostic': diag}
            )

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
    Main Lambda handler that routes between IoT data processing and API requests.
    
    Routes based on event source:
    - API Gateway events → api_handler.lambda_handler
    - IoT/SNS/SQS events → IoT data processing pipeline
    
    Args:
        event: Lambda event (API Gateway, IoT, SNS, SQS, etc.)
        context: Lambda context object with runtime information
    
    Returns:
        Dict containing response appropriate for the event source
    """
    try:
        # Check if this is an API Gateway request
        if 'httpMethod' in event and 'path' in event:
            # This is an API Gateway request - route to API handler
            logger.info("Routing to API handler for HTTP request")
            from api_handler import lambda_handler as api_lambda_handler
            return api_lambda_handler(event, context)
        
        # This is an IoT/SNS/SQS event - process as IoT data
        logger.info("Processing as IoT data event")
        return _process_iot_data(event, context)
    
    except Exception as e:
        logger.error(f"Error in main handler routing: {e}")
        return create_error_response(500, f"Handler routing error: {str(e)}")


def _process_iot_data(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process IoT sensor data through validation, ML inference, storage, and alert detection.
    
    This is the original lambda_handler logic for IoT data processing.
    """
    try:
        request_id = context.request_id if hasattr(context, 'request_id') else None
        start_time = datetime.utcnow()
        
        logger.info(
            f"Processing IoT data event - request_id={request_id}, "
            f"event_source={event.get('Records', [{}])[0].get('eventSource') if 'Records' in event else 'direct'}"
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
        
        # Store raw data in S3 (optional)
        s3_reference = None
        if DATA_LAKE_BUCKET:
            s3_reference = store_raw_data_s3(validated_data)
        else:
            logger.info("S3 data lake not configured, skipping raw data storage")
        
        # Invoke ML inference for WQI calculation
        ml_results = invoke_ml_inference(validated_data)
        
        # Store processed data in DynamoDB
        stored_reading = store_reading_dynamodb(validated_data, ml_results, s3_reference)

        # Push real-time update to WebSocket subscribers
        push_reading_to_websocket_subscribers(validated_data, ml_results, stored_reading)

        # Update device connectionStatus to 'online' so the dashboard reflects live status
        _update_device_connection_status(validated_data['deviceId'], validated_data['timestamp'])

        # Alert detection will be handled by DynamoDB Streams trigger
        # No need to manually trigger alerts here as the alert detection Lambda
        # will be triggered automatically when data is written to DynamoDB
        
        # Log performance metrics
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Data processing completed successfully - request_id={request_id}, "
            f"device_id={validated_data['deviceId']}, wqi={ml_results['wqi']}, "
            f"anomaly_type={ml_results['anomalyType']}, duration_ms={duration_ms}"
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
        
    except AquaChainValidationError as e:
        logger.error(
            "Data validation error: %s", e.message,
            extra={
                'request_id': request_id,
                'error_code': e.error_code or 'VALIDATION_ERROR',
                'details': e.details
            }
        )
        send_to_dlq(event, f"Validation error: {e.message}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': e.message,
                'code': e.error_code or 'VALIDATION_ERROR',
                'details': e.details,
                'requestId': request_id
            })
        }
        
    except DuplicateDataError as e:
        logger.warning(
            f"Duplicate data detected - request_id={request_id}, "
            f"device_id={e.device_id}, timestamp={e.timestamp}"
        )
        raise AquaChainValidationError(
            message="Duplicate data detected",
            error_code='DUPLICATE_DATA',
            details={'device_id': e.device_id, 'timestamp': e.timestamp}
        )
        
    except DataProcessingError as e:
        logger.error(
            f"Data processing error - request_id={request_id}, "
            f"error_code=PROCESSING_ERROR, message={e.message}, details={e.details}"
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
    Also handles both flat and nested data formats from ESP32.
    
    Args:
        event: Lambda event dictionary from various sources
    
    Returns:
        Extracted IoT sensor data as dictionary in nested format
    
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
            data = parsed_message
        elif 'body' in record:
            body: str = record['body']
            parsed_body: Dict[str, Any] = json.loads(body)
            data = parsed_body
        else:
            data = event
    else:
        # Direct invocation or IoT Rule
        data = event
    
    # Check if data is in flat format (ESP32 sends ph, turbidity, tds, temperature)
    # If so, convert to nested format
    if 'ph' in data and 'readings' not in data:
        logger.info(f"Converting flat format to nested - deviceId={data.get('deviceId', 'unknown')}")
        return {
            'deviceId': data.get('deviceId', 'ESP32-001'),
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            'location': {
                'latitude': data.get('latitude', 0.0),
                'longitude': data.get('longitude', 0.0)
            },
            'readings': {
                'pH': data.get('ph'),
                'turbidity': data.get('turbidity'),
                'tds': data.get('tds'),
                'temperature': data.get('temperature')
            },
            'diagnostics': {
                'batteryLevel': data.get('batteryLevel', 100.0),
                'signalStrength': data.get('signalStrength', -50),
                'sensorStatus': data.get('sensorStatus', 'normal')
            }
        }
    
    return data

@tracer.trace_critical_path('validate_sensor_data')
def validate_and_sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate IoT data against schema and sanitize values.
    
    Performs structure validation and range checks for sensor readings.
    Sanitizes timestamp format and rounds sensor values to appropriate precision.
    
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
        # Validate data structure using simplified validation
        validate_data_structure(data)
        
        # Additional range validation
        readings = data['readings']
        
        # pH validation (0-14 is valid range)
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
        
        logger.info(
            f"Data validation successful - device_id={data['deviceId']}, "
            f"pH={data['readings']['pH']}, turbidity={data['readings']['turbidity']}, "
            f"tds={data['readings']['tds']}, temperature={data['readings']['temperature']}"
        )
        return data
        
    except AquaChainValidationError as e:
        logger.error(f"Validation failed: {e.message}, details={e.details}")
        raise
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        raise AquaChainValidationError(
            message="Data validation failed",
            details={'error': str(e)}
        )

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
            f"Error checking duplicates - device_id={device_id}, error={str(e)}"
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
            f"Stored raw data in S3 - device_id={device_id}, s3_reference={s3_reference}"
        )
        return s3_reference
        
    except Exception as e:
        logger.error(
            f"Error storing data in S3 - device_id={device_id}, error={str(e)}"
        )
        raise DatabaseError(
            message="Failed to store raw data in S3",
            details={'device_id': device_id, 'error': str(e)}
        )

@tracer.trace_external_call('lambda', 'invoke_ml_inference')
def invoke_ml_inference(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ML inference for WQI calculation and anomaly detection.
    
    Uses Lambda ML inference function instead of SageMaker for better cost efficiency.
    Falls back to simple calculation if Lambda fails.
    
    Args:
        data: Validated sensor data containing readings and location
    
    Returns:
        Dictionary containing ML inference results:
            - wqi: Water Quality Index (0-100)
            - quality: Quality label (Excellent/Good/Fair/Poor/Very Poor)
            - anomalyType: Type of anomaly detected ('normal', 'contamination', etc.)
            - confidence: Confidence score (0.0-1.0)
            - error: Optional error message if inference failed
    
    Raises:
        DataProcessingError: When ML inference fails critically
    """
    try:
        # Check if we should use Lambda ML inference
        use_lambda_ml = os.environ.get('USE_LAMBDA_ML_INFERENCE', 'false').lower() == 'true'
        ml_function_name = os.environ.get('ML_INFERENCE_FUNCTION_NAME')
        
        if use_lambda_ml and ml_function_name:
            # Use Lambda ML inference
            return invoke_lambda_ml_inference(data, ml_function_name)
        else:
            # Fallback to SageMaker (original code) or simple calculation
            try:
                return invoke_sagemaker_ml_inference(data)
            except Exception as sagemaker_error:
                logger.warning(f"SageMaker inference failed, using simple calculation: {sagemaker_error}")
                return calculate_simple_wqi(data)
            
    except Exception as e:
        logger.error(f"ML inference error - device_id={data['deviceId']}, error={str(e)}")
        # Return simple calculation as fallback
        return calculate_simple_wqi(data)

def invoke_lambda_ml_inference(data: Dict[str, Any], function_name: str) -> Dict[str, Any]:
    """Invoke ML inference Lambda function"""
    try:
        # Prepare payload for ML inference Lambda
        payload = {
            'deviceId': data['deviceId'],
            'timestamp': data['timestamp'],
            'readings': data['readings'],
            'location': data.get('location', {'latitude': 0.0, 'longitude': 0.0})
        }
        
        # Invoke ML inference Lambda
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            
            # Get WQI from response or calculate simple WQI
            wqi = body.get('wqi')
            if wqi is None:
                logger.warning("ML inference returned no WQI, calculating simple WQI")
                return calculate_simple_wqi(data)
            
            # Map WQI to quality label
            quality = map_wqi_to_quality(wqi)
            
            logger.info(
                f"Lambda ML inference completed - device_id={data['deviceId']}, "
                f"wqi={wqi}, quality={quality}, "
                f"anomaly_type={body.get('anomalyType', 'unknown')}"
            )
            
            return {
                'wqi': wqi,
                'quality': quality,
                'anomalyType': body.get('anomalyType', 'normal'),
                'confidence': body.get('confidence', 0.0),
                'modelVersion': body.get('modelVersion', 'lambda-v1.0'),
                'featureImportance': body.get('featureImportance', {})
            }
        else:
            raise Exception(f"Lambda invocation failed: {result}")
            
    except Exception as e:
        logger.error(f"Lambda ML inference error: {e}")
        # Fallback to simple calculation
        return calculate_simple_wqi(data)

def invoke_sagemaker_ml_inference(data: Dict[str, Any]) -> Dict[str, Any]:
    """Original SageMaker ML inference (fallback)"""
    # Prepare enhanced payload for pre-trained model (14 features)
    payload = {
        'deviceId': data['deviceId'],
        'timestamp': data['timestamp'],
        'readings': {
            'pH': data['readings']['pH'],
            'turbidity': data['readings']['turbidity'],
            'tds': data['readings']['tds'],
            'temperature': data['readings']['temperature'],
            'humidity': data['readings'].get('humidity', 50.0)  # Default if not provided
        },
        'location': data.get('location', {'latitude': 0.0, 'longitude': 0.0})
    }
    
    # Invoke SageMaker endpoint
    response = sagemaker_client.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT_NAME,
        ContentType='application/json',
        Accept='application/json',
        Body=json.dumps(payload)
    )
    
    # Parse response
    result = json.loads(response['Body'].read().decode('utf-8'))
    
    logger.info(
        f"SageMaker inference completed - device_id={data['deviceId']}, "
        f"wqi={result['wqi']}, anomaly_type={result['anomalyType']}, "
        f"confidence={result.get('confidence', 0.0)}, "
        f"model_version={result.get('modelVersion', 'unknown')}, "
        f"features_used={len(result.get('featureImportance', {}))}"
    )
    
    return result

def calculate_simple_wqi(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate WQI using simple algorithm as fallback"""
    try:
        readings = data['readings']
        pH = float(readings['pH'])
        turbidity = float(readings['turbidity'])
        tds = float(readings['tds'])
        temperature = float(readings['temperature'])
        
        # Simple WQI calculation (0-100 scale)
        # Ideal values: pH 7.0, turbidity 0, TDS 100, temp 25
        pH_score = max(0, 100 - abs(pH - 7.0) * 15)
        turbidity_score = max(0, 100 - turbidity * 10)
        tds_score = max(0, 100 - abs(tds - 100) / 10)
        temp_score = max(0, 100 - abs(temperature - 25) * 2)
        
        wqi = (pH_score + turbidity_score + tds_score + temp_score) / 4
        wqi = round(wqi, 1)
        
        # Map to quality
        quality = map_wqi_to_quality(wqi)
        
        # Simple anomaly detection
        anomaly_type = 'normal'
        if pH < 6.5 or pH > 8.5:
            anomaly_type = 'pH_anomaly'
        elif turbidity > 5:
            anomaly_type = 'turbidity_high'
        elif tds > 500:
            anomaly_type = 'tds_high'
        
        logger.info(
            f"Simple WQI calculation - device_id={data['deviceId']}, "
            f"wqi={wqi}, quality={quality}, anomaly_type={anomaly_type}"
        )
        
        return {
            'wqi': wqi,
            'quality': quality,
            'anomalyType': anomaly_type,
            'confidence': 0.8,  # Fixed confidence for simple calculation
            'modelVersion': 'simple-v1.0'
        }
        
    except Exception as e:
        logger.error(f"Error in simple WQI calculation: {e}")
        return {
            'wqi': 50.0,  # Neutral WQI
            'quality': 'Fair',  # Default quality
            'anomalyType': 'unknown',
            'confidence': 0.0,
            'error': str(e),
            'modelVersion': 'fallback'
        }

def map_wqi_to_quality(wqi: float) -> str:
    """Map WQI score to quality label"""
    if wqi >= 90:
        return 'Excellent'
    elif wqi >= 70:
        return 'Good'
    elif wqi >= 50:
        return 'Fair'
    elif wqi >= 25:
        return 'Poor'
    else:
        return 'Very Poor'


def push_reading_to_websocket_subscribers(validated_data: Dict[str, Any], ml_results: Dict[str, Any], stored_reading: Dict[str, Any]) -> None:
    """
    Push the new reading to all WebSocket clients subscribed to 'consumer-updates'.
    Queries the topic-index GSI on AquaChain-WebSocketConnections-dev and posts
    to each live connection via API Gateway Management API.
    Stale connections (GoneException) are cleaned up automatically.
    """
    try:
        from decimal import Decimal

        connections_table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        apigw = boto3.client('apigatewaymanagementapi', endpoint_url=WEBSOCKET_ENDPOINT)

        # Query all connections subscribed to consumer-updates
        response = connections_table.query(
            IndexName='topic-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('topic').eq('consumer-updates')
        )
        connections = response.get('Items', [])

        if not connections:
            logger.info("No WebSocket subscribers for consumer-updates, skipping push")
            return

        # Build the message payload — convert Decimals to float for JSON serialisation
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError

        message = json.dumps({
            'type': 'water_quality',
            'data': {
                'deviceId': validated_data['deviceId'],
                'timestamp': validated_data['timestamp'],
                'pH': float(stored_reading.get('pH', validated_data['readings']['pH'])),
                'turbidity': float(stored_reading.get('turbidity', validated_data['readings']['turbidity'])),
                'tds': float(stored_reading.get('tds', validated_data['readings']['tds'])),
                'temperature': float(stored_reading.get('temperature', validated_data['readings']['temperature'])),
                'wqi': float(stored_reading.get('wqi', ml_results['wqi'])),
                'quality': ml_results.get('quality', 'Fair'),
                'anomalyType': ml_results.get('anomalyType', 'normal'),
            }
        }, default=decimal_to_float).encode('utf-8')

        stale = []
        sent = 0
        for conn in connections:
            connection_id = conn['connectionId']
            try:
                apigw.post_to_connection(ConnectionId=connection_id, Data=message)
                sent += 1
            except apigw.exceptions.GoneException:
                stale.append(connection_id)
            except Exception as e:
                logger.warning(f"Failed to push to connection {connection_id}: {e}")

        # Clean up stale connections
        for connection_id in stale:
            try:
                connections_table.delete_item(Key={'connectionId': connection_id})
                logger.info(f"Removed stale WebSocket connection: {connection_id}")
            except Exception as e:
                logger.warning(f"Failed to remove stale connection {connection_id}: {e}")

        logger.info(f"WebSocket push complete — sent={sent}, stale_removed={len(stale)}, device={validated_data['deviceId']}")

    except Exception as e:
        # Non-fatal — never block IoT ingestion due to WebSocket push failure
        logger.error(f"WebSocket push failed for device {validated_data.get('deviceId')}: {e}")


def _update_device_connection_status(device_id: str, timestamp: str) -> None:
    """Update device connectionStatus to 'online' and refresh lastSeen timestamp."""
    devices_table_name = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
    try:
        table = dynamodb.Table(devices_table_name)
        table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET lastSeen = :ts, connectionStatus = :cs, statusUpdatedAt = :ts',
            ExpressionAttributeValues={
                ':ts': timestamp,
                ':cs': 'online',
            }
        )
        logger.info(f"Updated connectionStatus=online for device {device_id}")
    except Exception as e:
        # Non-fatal — log and continue
        logger.warning(f"Could not update device connectionStatus for {device_id}: {e}")


@tracer.trace_external_call('dynamodb', 'put_item')
def store_reading_dynamodb(data: Dict[str, Any], ml_results: Dict[str, Any],
                          s3_reference: Optional[str]) -> Dict[str, Any]:
    """
    Store processed reading in DynamoDB with ledger entry.
    
    Stores the processed sensor reading in DynamoDB along with ML
    inference results and S3 reference. Creates immutable ledger
    entry for audit trail.
    
    Args:
        data: Validated sensor data
        ml_results: ML inference results including WQI and anomaly type
        s3_reference: S3 URI where raw data is stored (optional)
    
    Returns:
        Dictionary containing stored reading with ledger sequence number
    
    Raises:
        DataProcessingError: When DynamoDB storage operation fails
        ClientError: When AWS DynamoDB API call fails
    """
    try:
        from decimal import Decimal
        
        device_id = data['deviceId']
        timestamp = data['timestamp']
        
        # Create partition key (deviceId_month format)
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        partition_key = f"{device_id}_{dt.strftime('%Y-%m')}"
        
        # Prepare reading item
        reading_item = {
            'deviceId': device_id,
            'deviceId_month': partition_key,
            'timestamp': timestamp,
            'pH': Decimal(str(data['readings']['pH'])),
            'turbidity': Decimal(str(data['readings']['turbidity'])),
            'tds': Decimal(str(data['readings']['tds'])),
            'temperature': Decimal(str(data['readings']['temperature'])),
            'wqi': Decimal(str(ml_results['wqi'])),
            'quality': ml_results.get('quality', 'Fair'),
            'qualityScore': Decimal(str(ml_results['wqi'])),  # Keep for backward compatibility
            'qualityStatus': ml_results['anomalyType'],
            'anomalyType': ml_results['anomalyType'],
            'confidence': Decimal(str(ml_results.get('confidence', 0.0))),
            'modelVersion': ml_results.get('modelVersion', 'unknown'),
            'metric_type': 'water_quality',
            'createdAt': datetime.utcnow().isoformat()
        }
        
        if s3_reference:
            reading_item['s3Reference'] = s3_reference
        
        # Store in readings table
        table = dynamodb.Table(READINGS_TABLE)
        table.put_item(Item=reading_item)
        
        logger.info(
            f"Stored reading in DynamoDB - device_id={device_id}, wqi={ml_results['wqi']}"
        )
        
        # Store in secure ledger with cryptographic integrity
        try:
            # Create data hash for ledger entry
            reading_data = {
                'deviceId': device_id,
                'readings': data['readings'],
                'wqi': ml_results['wqi'],
                'anomalyType': ml_results.get('anomalyType', 'unknown'),
                'timestamp': timestamp
            }
            data_hash = hashlib.sha256(json.dumps(reading_data, sort_keys=True).encode()).hexdigest()
            
            # Use secure ledger service with hash chaining and KMS signing
            ledger_service_payload = {
                'operation': 'create_entry',
                'deviceId': device_id,
                'dataHash': data_hash,
                'wqi': ml_results['wqi'],
                'anomalyType': ml_results.get('anomalyType', 'unknown'),
                'metadata': {
                    'event_type': 'READING_INGESTED',
                    'readings': data['readings'],
                    'timestamp': timestamp
                }
            }
            
            # Invoke secure ledger service
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName='aquachain-function-ledger-service-dev',
                InvocationType='RequestResponse',
                Payload=json.dumps(ledger_service_payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result['statusCode'] == 200:
                ledger_result = json.loads(result['body'])
                reading_item['ledgerSequence'] = ledger_result['sequenceNumber']
                reading_item['ledgerLogId'] = ledger_result['logId']
                
                logger.info(
                    f"Stored secure ledger entry - device_id={device_id}, "
                    f"sequence={ledger_result['sequenceNumber']}, "
                    f"logId={ledger_result['logId']}"
                )
            else:
                logger.error(f"Ledger service error: {result}")
                raise Exception(f"Ledger service returned status {result['statusCode']}")
                
        except Exception as e:
            logger.warning(
                f"Error writing to secure ledger - device_id={device_id}, error={str(e)}"
            )
            # Don't fail if ledger write fails, but log the error for monitoring
        
        return reading_item
        
    except Exception as e:
        logger.error(
            f"Error storing reading in DynamoDB - device_id={data['deviceId']}, error={str(e)}"
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
            f"Triggered critical alert - device_id={data['deviceId']}, "
            f"wqi={ml_results['wqi']}, anomaly_type={ml_results['anomalyType']}"
        )
        
    except Exception as e:
        logger.error(
            f"Error triggering alert - device_id={data['deviceId']}, error={str(e)}"
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
    if not DLQ_URL:
        logger.warning("DLQ not configured, skipping failed event logging")
        return
        
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
            f"Sent failed event to DLQ - error_message={error_message}, "
            f"device_id={event.get('deviceId', 'unknown')}"
        )
        
    except Exception as e:
        logger.error(
            f"Error sending to DLQ - error={str(e)}"
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