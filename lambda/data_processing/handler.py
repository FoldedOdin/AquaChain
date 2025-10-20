"""
Data Processing Lambda Function for AquaChain System
Handles IoT device data validation, sanitization, and orchestration
"""

import json
import boto3
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
import logging
import sys
import os

# Add shared utilities to path
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import X-Ray tracing utilities
from xray_utils import AquaChainTracer, trace_lambda_handler, EndToEndTracer

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    pass

class DuplicateDataError(Exception):
    """Exception for duplicate data detection"""
    pass

@trace_lambda_handler('data-processing')
def lambda_handler(event, context):
    """
    Main Lambda handler for IoT data processing
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
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
        logger.error(f"Data validation error: {e}")
        send_to_dlq(event, f"Validation error: {e}")
        return create_error_response(400, "Invalid data format")
        
    except DuplicateDataError as e:
        logger.warning(f"Duplicate data detected: {e}")
        return create_error_response(409, "Duplicate data")
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        send_to_dlq(event, f"Processing error: {e}")
        return create_error_response(500, "Internal processing error")

def extract_iot_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract IoT data from Lambda event
    Handles both direct invocation and IoT Rule triggers
    """
    if 'Records' in event:
        # SNS/SQS trigger
        record = event['Records'][0]
        if 'Sns' in record:
            return json.loads(record['Sns']['Message'])
        elif 'body' in record:
            return json.loads(record['body'])
    
    # Direct invocation or IoT Rule
    return event

@tracer.trace_critical_path('validate_sensor_data')
def validate_and_sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate IoT data against schema and sanitize values
    """
    try:
        # Validate against JSON schema
        validate(instance=data, schema=IOT_DATA_SCHEMA)
        
        # Additional range validation
        readings = data['readings']
        
        # pH validation (6.5-8.5 is safe range)
        if not (0 <= readings['pH'] <= 14):
            raise ValidationError("pH value out of valid range")
        
        # Turbidity validation (0-4000 NTU)
        if not (0 <= readings['turbidity'] <= 4000):
            raise ValidationError("Turbidity value out of valid range")
        
        # TDS validation (0-5000 ppm)
        if not (0 <= readings['tds'] <= 5000):
            raise ValidationError("TDS value out of valid range")
        
        # Temperature validation (-40 to 125°C)
        if not (-40 <= readings['temperature'] <= 125):
            raise ValidationError("Temperature value out of valid range")
        
        # Humidity validation (0-100%)
        if not (0 <= readings['humidity'] <= 100):
            raise ValidationError("Humidity value out of valid range")
        
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
        
        logger.info(f"Data validation successful for device {data['deviceId']}")
        return data
        
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise

def check_for_duplicates(data: Dict[str, Any]) -> None:
    """
    Check for duplicate readings using device ID and timestamp
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
        logger.warning(f"Error checking duplicates: {e}")
        # Continue processing if duplicate check fails

@tracer.trace_external_call('s3', 'put_object')
def store_raw_data_s3(data: Dict[str, Any]) -> str:
    """
    Store raw IoT data in S3 data lake with partitioned structure
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
        logger.info(f"Stored raw data in S3: {s3_reference}")
        return s3_reference
        
    except Exception as e:
        logger.error(f"Error storing data in S3: {e}")
        raise DataProcessingError(f"Failed to store raw data: {e}")

@tracer.trace_external_call('lambda', 'invoke_ml_inference')
def invoke_ml_inference(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ML inference Lambda for WQI calculation and anomaly detection
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
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] != 200:
            raise DataProcessingError(f"ML inference failed: {result}")
        
        # Parse ML results
        ml_results = json.loads(result['body'])
        
        logger.info(f"ML inference completed: WQI={ml_results['wqi']}, "
                   f"Anomaly={ml_results['anomalyType']}")
        
        return ml_results
        
    except Exception as e:
        logger.error(f"ML inference error: {e}")
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
    Store processed reading in DynamoDB with ledger entry
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
        
        logger.info(f"Stored reading in DynamoDB with ledger sequence: "
                   f"{stored_reading.get('ledgerSequence')}")
        
        return stored_reading
        
    except Exception as e:
        logger.error(f"Error storing reading in DynamoDB: {e}")
        raise DataProcessingError(f"Failed to store reading: {e}")

def is_critical_event(ml_results: Dict[str, Any]) -> bool:
    """
    Determine if reading represents a critical water quality event
    """
    wqi = ml_results.get('wqi', 100)
    anomaly_type = ml_results.get('anomalyType', 'normal')
    
    # Critical if WQI below 50 or contamination detected
    return wqi < 50 or anomaly_type == 'contamination'

def trigger_alert_notification(data: Dict[str, Any], ml_results: Dict[str, Any]) -> None:
    """
    Trigger alert notification for critical events
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
        
        logger.info(f"Triggered critical alert for device {data['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error triggering alert: {e}")
        # Don't fail the entire process if alert fails

def send_to_dlq(event: Dict[str, Any], error_message: str) -> None:
    """
    Send failed events to dead letter queue for manual review
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
        
        logger.info(f"Sent failed event to DLQ: {error_message}")
        
    except Exception as e:
        logger.error(f"Error sending to DLQ: {e}")

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create standardized error response
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