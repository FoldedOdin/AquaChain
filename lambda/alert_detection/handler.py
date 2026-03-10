"""
Alert Detection Lambda Function for AquaChain System
Handles critical event detection, alert classification, and threshold monitoring
"""

import json
import boto3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Environment variables
ALERTS_TABLE = 'aquachain-alerts'
USERS_TABLE = 'aquachain-users'
CRITICAL_ALERTS_TOPIC = 'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-critical-alerts-dev'
WARNING_ALERTS_TOPIC = 'arn:aws:sns:ap-south-1:758346259059:aquachain-topic-monitoring-warning-dev'
NOTIFICATION_LAMBDA = 'aquachain-function-notification-dev'

# Alert thresholds based on requirements
CRITICAL_THRESHOLDS = {
    'wqi_min': 50,  # WQI below 50 is critical
    'pH_min': 6.5,  # pH below 6.5 is critical
    'pH_max': 8.5,  # pH above 8.5 is critical
    'turbidity_max': 25,  # High turbidity indicates contamination
    'tds_max': 1000  # High TDS indicates contamination
}

WARNING_THRESHOLDS = {
    'wqi_min': 70,  # WQI below 70 is warning
    'pH_min': 6.8,  # pH below 6.8 is warning
    'pH_max': 8.2,  # pH above 8.2 is warning
    'turbidity_max': 10,  # Moderate turbidity is warning
    'tds_max': 600  # Moderate TDS is warning
}

# Alert escalation settings
ESCALATION_WINDOW_MINUTES = 30  # Time window for sustained issues
ESCALATION_THRESHOLD_COUNT = 3  # Number of alerts in window to trigger escalation

class AlertDetectionError(Exception):
    """Custom exception for alert detection errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for alert detection
    Triggered by DynamoDB Streams from readings table
    """
    try:
        logger.info(f"Processing alert detection event: {json.dumps(event)}")
        
        # Process each record from DynamoDB Stream
        for record in event.get('Records', []):
            if record['eventName'] in ['INSERT', 'MODIFY']:
                process_reading_record(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alert detection completed',
                'processedRecords': len(event.get('Records', []))
            })
        }
        
    except Exception as e:
        logger.error(f"Alert detection error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def process_reading_record(record: Dict[str, Any]) -> None:
    """
    Process individual DynamoDB Stream record for alert detection
    """
    try:
        # Extract reading data from DynamoDB Stream record
        if record['eventName'] == 'INSERT':
            reading_data = record['dynamodb']['NewImage']
        else:  # MODIFY
            reading_data = record['dynamodb']['NewImage']
        
        # Convert DynamoDB format to standard format
        reading = convert_dynamodb_record(reading_data)
        
        # Detect alert conditions
        alert_level = detect_alert_level(reading)
        
        if alert_level != 'safe':
            # Create alert record
            alert = create_alert_record(reading, alert_level)
            
            # Store alert in database
            store_alert(alert)
            
            # Check for alert deduplication
            if not is_duplicate_alert(alert):
                # Trigger notification
                trigger_alert_notification(alert)
                
                # Check for escalation conditions
                check_alert_escalation(alert)
            
            logger.info(f"Alert processed: {alert_level} for device {reading['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error processing reading record: {e}")
        raise AlertDetectionError(f"Failed to process record: {e}")

def convert_dynamodb_record(dynamodb_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert DynamoDB Stream record format to standard reading format
    """
    try:
        reading = {
            'deviceId': dynamodb_data['deviceId']['S'],
            'timestamp': dynamodb_data['timestamp']['S'],
            'wqi': float(dynamodb_data['wqi']['N']),
            'anomalyType': dynamodb_data['anomalyType']['S'],
            'readings': {
                'pH': float(dynamodb_data['readings']['M']['pH']['N']),
                'turbidity': float(dynamodb_data['readings']['M']['turbidity']['N']),
                'tds': float(dynamodb_data['readings']['M']['tds']['N']),
                'temperature': float(dynamodb_data['readings']['M']['temperature']['N'])
            },
            'location': {
                'latitude': float(dynamodb_data['location']['M']['latitude']['N']),
                'longitude': float(dynamodb_data['location']['M']['longitude']['N'])
            }
        }
        
        return reading
        
    except Exception as e:
        logger.error(f"Error converting DynamoDB record: {e}")
        raise AlertDetectionError(f"Record conversion failed: {e}")

def detect_alert_level(reading: Dict[str, Any]) -> str:
    """
    Detect alert level based on WQI and sensor thresholds
    Returns: 'critical', 'warning', or 'safe'
    """
    try:
        wqi = reading['wqi']
        readings = reading['readings']
        anomaly_type = reading['anomalyType']
        
        # Check for critical conditions
        if (wqi < CRITICAL_THRESHOLDS['wqi_min'] or
            readings['pH'] < CRITICAL_THRESHOLDS['pH_min'] or
            readings['pH'] > CRITICAL_THRESHOLDS['pH_max'] or
            readings['turbidity'] > CRITICAL_THRESHOLDS['turbidity_max'] or
            readings['tds'] > CRITICAL_THRESHOLDS['tds_max'] or
            anomaly_type == 'contamination'):
            
            return 'critical'
        
        # Check for warning conditions
        if (wqi < WARNING_THRESHOLDS['wqi_min'] or
            readings['pH'] < WARNING_THRESHOLDS['pH_min'] or
            readings['pH'] > WARNING_THRESHOLDS['pH_max'] or
            readings['turbidity'] > WARNING_THRESHOLDS['turbidity_max'] or
            readings['tds'] > WARNING_THRESHOLDS['tds_max'] or
            anomaly_type == 'sensor_fault'):
            
            return 'warning'
        
        return 'safe'
        
    except Exception as e:
        logger.error(f"Error detecting alert level: {e}")
        return 'safe'  # Default to safe if detection fails

def create_alert_record(reading: Dict[str, Any], alert_level: str) -> Dict[str, Any]:
    """
    Create alert record with all necessary information
    """
    try:
        alert_id = generate_alert_id(reading['deviceId'], reading['timestamp'])
        
        # Determine specific alert reasons
        alert_reasons = get_alert_reasons(reading, alert_level)
        
        alert = {
            'alertId': alert_id,
            'deviceId': reading['deviceId'],
            'timestamp': reading['timestamp'],
            'alertLevel': alert_level,
            'wqi': reading['wqi'],
            'anomalyType': reading['anomalyType'],
            'readings': reading['readings'],
            'location': reading['location'],
            'alertReasons': alert_reasons,
            'status': 'active',
            'createdAt': datetime.utcnow().isoformat(),
            'acknowledgedAt': None,
            'resolvedAt': None,
            'notificationsSent': [],
            'escalated': False
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating alert record: {e}")
        raise AlertDetectionError(f"Alert creation failed: {e}")

def generate_alert_id(device_id: str, timestamp: str) -> str:
    """
    Generate unique alert ID based on device and timestamp
    """
    data = f"{device_id}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()[:12]

def get_alert_reasons(reading: Dict[str, Any], alert_level: str) -> List[str]:
    """
    Get specific reasons for the alert based on threshold violations
    """
    reasons = []
    wqi = reading['wqi']
    readings = reading['readings']
    anomaly_type = reading['anomalyType']
    
    thresholds = CRITICAL_THRESHOLDS if alert_level == 'critical' else WARNING_THRESHOLDS
    
    # Check each threshold
    if wqi < thresholds['wqi_min']:
        reasons.append(f"Water Quality Index ({wqi:.1f}) below safe threshold ({thresholds['wqi_min']})")
    
    if readings['pH'] < thresholds['pH_min']:
        reasons.append(f"pH level ({readings['pH']:.2f}) too acidic (below {thresholds['pH_min']})")
    elif readings['pH'] > thresholds['pH_max']:
        reasons.append(f"pH level ({readings['pH']:.2f}) too alkaline (above {thresholds['pH_max']})")
    
    if readings['turbidity'] > thresholds['turbidity_max']:
        reasons.append(f"High turbidity ({readings['turbidity']:.1f} NTU) indicates water cloudiness")
    
    if readings['tds'] > thresholds['tds_max']:
        reasons.append(f"High dissolved solids ({readings['tds']:.0f} ppm) detected")
    
    if anomaly_type == 'contamination':
        reasons.append("AI model detected potential water contamination")
    elif anomaly_type == 'sensor_fault':
        reasons.append("Sensor malfunction detected - readings may be inaccurate")
    
    return reasons

def convert_floats_to_decimal(obj):
    """
    Recursively convert float values to Decimal for DynamoDB compatibility
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj

def store_alert(alert: Dict[str, Any]) -> None:
    """
    Store alert record in DynamoDB
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        # Add TTL for alert cleanup (30 days)
        ttl_timestamp = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        alert['ttl'] = ttl_timestamp
        
        # Convert floats to Decimal for DynamoDB
        alert_decimal = convert_floats_to_decimal(alert)
        
        table.put_item(Item=alert_decimal)
        
        logger.info(f"Stored alert {alert['alertId']} for device {alert['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error storing alert: {e}")
        raise AlertDetectionError(f"Alert storage failed: {e}")

def is_duplicate_alert(alert: Dict[str, Any]) -> bool:
    """
    Check if similar alert was recently sent to avoid spam
    Deduplication window: 5 minutes for same device and alert level
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        # Calculate deduplication window
        current_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
        window_start = current_time - timedelta(minutes=5)
        
        # Query recent alerts for same device
        response = table.query(
            IndexName='DeviceAlerts',  # GSI on deviceId
            KeyConditionExpression='deviceId = :deviceId',
            FilterExpression='alertLevel = :alertLevel AND createdAt > :windowStart',
            ExpressionAttributeValues={
                ':deviceId': alert['deviceId'],
                ':alertLevel': alert['alertLevel'],
                ':windowStart': window_start.isoformat()
            }
        )
        
        # Check if any recent alerts found
        recent_alerts = response.get('Items', [])
        
        if recent_alerts:
            logger.info(f"Duplicate alert detected for device {alert['deviceId']} - skipping notification")
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Error checking duplicate alert: {e}")
        return False  # Continue with notification if check fails

def trigger_alert_notification(alert: Dict[str, Any]) -> None:
    """
    Trigger alert notification through SNS and notification service
    """
    try:
        # Determine SNS topic based on alert level
        topic_arn = CRITICAL_ALERTS_TOPIC if alert['alertLevel'] == 'critical' else WARNING_ALERTS_TOPIC
        
        # Create notification message
        notification_message = {
            'alertId': alert['alertId'],
            'deviceId': alert['deviceId'],
            'alertLevel': alert['alertLevel'],
            'timestamp': alert['timestamp'],
            'wqi': alert['wqi'],
            'location': alert['location'],
            'alertReasons': alert['alertReasons'],
            'anomalyType': alert['anomalyType']
        }
        
        # Publish to SNS topic
        sns_response = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(notification_message),
            Subject=f"{alert['alertLevel'].title()} Water Quality Alert - Device {alert['deviceId']}",
            MessageAttributes={
                'alertLevel': {'DataType': 'String', 'StringValue': alert['alertLevel']},
                'deviceId': {'DataType': 'String', 'StringValue': alert['deviceId']},
                'wqi': {'DataType': 'Number', 'StringValue': str(alert['wqi'])}
            }
        )
        
        # Invoke notification service Lambda for multi-channel delivery
        lambda_client.invoke(
            FunctionName=NOTIFICATION_LAMBDA,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'action': 'send_alert',
                'alert': notification_message
            })
        )
        
        # Update alert record with notification info
        update_alert_notifications(alert['alertId'], 'sns', sns_response['MessageId'])
        
        logger.info(f"Triggered {alert['alertLevel']} alert notification for device {alert['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error triggering alert notification: {e}")
        # Don't fail the entire process if notification fails

def check_alert_escalation(alert: Dict[str, Any]) -> None:
    """
    Check if alert should be escalated based on sustained issues
    """
    try:
        if alert['alertLevel'] != 'critical':
            return  # Only escalate critical alerts
        
        # Check for sustained critical alerts in the last 30 minutes
        current_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
        window_start = current_time - timedelta(minutes=ESCALATION_WINDOW_MINUTES)
        
        table = dynamodb.Table(ALERTS_TABLE)
        
        # Query recent critical alerts for same device
        response = table.query(
            IndexName='DeviceAlerts',
            KeyConditionExpression='deviceId = :deviceId',
            FilterExpression='alertLevel = :alertLevel AND createdAt > :windowStart',
            ExpressionAttributeValues={
                ':deviceId': alert['deviceId'],
                ':alertLevel': 'critical',
                ':windowStart': window_start.isoformat()
            }
        )
        
        critical_alerts = response.get('Items', [])
        
        # Check if escalation threshold is met
        if len(critical_alerts) >= ESCALATION_THRESHOLD_COUNT:
            escalate_alert(alert, len(critical_alerts))
        
    except Exception as e:
        logger.error(f"Error checking alert escalation: {e}")

def escalate_alert(alert: Dict[str, Any], alert_count: int) -> None:
    """
    Escalate sustained critical alerts to administrators
    """
    try:
        escalation_message = {
            'alertId': alert['alertId'],
            'deviceId': alert['deviceId'],
            'alertLevel': 'escalated',
            'sustainedAlertCount': alert_count,
            'timeWindow': f"{ESCALATION_WINDOW_MINUTES} minutes",
            'location': alert['location'],
            'latestWQI': alert['wqi'],
            'alertReasons': alert['alertReasons'],
            'escalatedAt': datetime.utcnow().isoformat()
        }
        
        # Send escalation notification to admin topic
        admin_topic = 'arn:aws:sns:us-east-1:123456789012:aquachain-admin-alerts'
        
        sns_client.publish(
            TopicArn=admin_topic,
            Message=json.dumps(escalation_message),
            Subject=f"ESCALATED: Sustained Critical Water Quality Issues - Device {alert['deviceId']}",
            MessageAttributes={
                'alertLevel': {'DataType': 'String', 'StringValue': 'escalated'},
                'deviceId': {'DataType': 'String', 'StringValue': alert['deviceId']},
                'sustainedCount': {'DataType': 'Number', 'StringValue': str(alert_count)}
            }
        )
        
        # Mark alert as escalated
        update_alert_escalation(alert['alertId'])
        
        logger.warning(f"Escalated sustained critical alerts for device {alert['deviceId']} "
                      f"({alert_count} alerts in {ESCALATION_WINDOW_MINUTES} minutes)")
        
    except Exception as e:
        logger.error(f"Error escalating alert: {e}")

def update_alert_notifications(alert_id: str, channel: str, message_id: str) -> None:
    """
    Update alert record with notification delivery information
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        notification_record = {
            'channel': channel,
            'messageId': message_id,
            'sentAt': datetime.utcnow().isoformat()
        }
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET notificationsSent = list_append(if_not_exists(notificationsSent, :empty_list), :notification)',
            ExpressionAttributeValues={
                ':notification': [notification_record],
                ':empty_list': []
            }
        )
        
    except Exception as e:
        logger.warning(f"Error updating alert notifications: {e}")

def update_alert_escalation(alert_id: str) -> None:
    """
    Mark alert as escalated in database
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET escalated = :escalated, escalatedAt = :escalatedAt',
            ExpressionAttributeValues={
                ':escalated': True,
                ':escalatedAt': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.warning(f"Error updating alert escalation: {e}")

def get_device_users(device_id: str) -> List[Dict[str, Any]]:
    """
    Get users associated with a device for targeted notifications
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        # Query users who have this device associated
        response = table.scan(
            FilterExpression='contains(deviceIds, :deviceId)',
            ExpressionAttributeValues={
                ':deviceId': device_id
            }
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.warning(f"Error getting device users: {e}")
        return []