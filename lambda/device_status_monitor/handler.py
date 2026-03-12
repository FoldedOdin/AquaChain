"""
Device Status Monitor Lambda
Monitors device online/offline status based on data transmission patterns
"""

import json
import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings')
OFFLINE_THRESHOLD_MINUTES = int(os.environ.get('OFFLINE_THRESHOLD_MINUTES', '5'))  # 5 minutes default

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB tables
devices_table = dynamodb.Table(DEVICES_TABLE)
readings_table = dynamodb.Table(READINGS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for device status monitoring
    Triggered by CloudWatch Events (scheduled every 2 minutes)
    """
    try:
        logger.info("Starting device status monitoring")
        
        # Get all active devices
        devices = get_all_active_devices()
        logger.info(f"Found {len(devices)} active devices to monitor")
        
        # Check status for each device
        status_updates = []
        for device in devices:
            device_id = device['deviceId']
            current_status = device.get('connectionStatus', 'unknown')
            
            # Determine new status based on last data transmission
            new_status = determine_device_status(device)
            
            # Update status if changed
            if new_status != current_status:
                update_device_status(device_id, new_status)
                status_updates.append({
                    'deviceId': device_id,
                    'oldStatus': current_status,
                    'newStatus': new_status,
                    'lastSeen': device.get('lastSeen', 'unknown')
                })
                logger.info(f"Device {device_id} status changed: {current_status} → {new_status}")
        
        # Publish CloudWatch metrics
        publish_status_metrics(devices, status_updates)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Device status monitoring completed',
                'devicesChecked': len(devices),
                'statusUpdates': len(status_updates),
                'updates': status_updates
            })
        }
        
    except Exception as e:
        logger.error(f"Error in device status monitoring: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Device status monitoring failed'})
        }


def get_all_active_devices() -> List[Dict[str, Any]]:
    """
    Get all devices that should be monitored for status
    Returns devices with status 'active' or 'provisioned'
    """
    try:
        # Scan for active devices (in production, consider using GSI)
        response = devices_table.scan(
            FilterExpression='#status IN (:active, :provisioned)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':active': 'active',
                ':provisioned': 'provisioned'
            }
        )
        
        devices = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = devices_table.scan(
                FilterExpression='#status IN (:active, :provisioned)',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':active': 'active',
                    ':provisioned': 'provisioned'
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            devices.extend(response.get('Items', []))
        
        return devices
        
    except Exception as e:
        logger.error(f"Error getting active devices: {str(e)}")
        return []


def determine_device_status(device: Dict[str, Any]) -> str:
    """
    Determine device online/offline status based on last data transmission
    
    Status Logic:
    - online: Device sent data within OFFLINE_THRESHOLD_MINUTES
    - offline: Device hasn't sent data for > OFFLINE_THRESHOLD_MINUTES
    - unknown: No lastSeen timestamp available
    """
    device_id = device['deviceId']
    last_seen = device.get('lastSeen')
    
    if not last_seen:
        logger.warning(f"Device {device_id} has no lastSeen timestamp")
        return 'unknown'
    
    try:
        # Parse lastSeen timestamp
        if isinstance(last_seen, str):
            # Handle ISO format: "2024-01-15T10:30:00Z"
            last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
        else:
            logger.warning(f"Device {device_id} has invalid lastSeen format: {last_seen}")
            return 'unknown'
        
        # Calculate time difference
        now = datetime.now(last_seen_dt.tzinfo)  # Use same timezone
        time_diff = now - last_seen_dt
        
        # Determine status based on threshold
        if time_diff.total_seconds() <= (OFFLINE_THRESHOLD_MINUTES * 60):
            return 'online'
        else:
            return 'offline'
            
    except Exception as e:
        logger.error(f"Error parsing lastSeen for device {device_id}: {str(e)}")
        return 'unknown'


def update_device_status(device_id: str, new_status: str) -> None:
    """
    Update device connection status in DynamoDB
    """
    try:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        devices_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET connectionStatus = :status, statusUpdatedAt = :timestamp',
            ExpressionAttributeValues={
                ':status': new_status,
                ':timestamp': timestamp
            }
        )
        
        logger.info(f"Updated device {device_id} status to {new_status}")
        
    except Exception as e:
        logger.error(f"Error updating device {device_id} status: {str(e)}")


def publish_status_metrics(devices: List[Dict[str, Any]], status_updates: List[Dict[str, Any]]) -> None:
    """
    Publish device status metrics to CloudWatch
    """
    try:
        # Count devices by status
        status_counts = {'online': 0, 'offline': 0, 'unknown': 0}
        
        for device in devices:
            status = device.get('connectionStatus', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
        
        # Publish metrics
        metric_data = []
        
        for status, count in status_counts.items():
            metric_data.append({
                'MetricName': f'DevicesCount{status.capitalize()}',
                'Value': count,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            })
        
        # Total devices metric
        metric_data.append({
            'MetricName': 'DevicesTotal',
            'Value': len(devices),
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        })
        
        # Status changes metric
        metric_data.append({
            'MetricName': 'DeviceStatusChanges',
            'Value': len(status_updates),
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        })
        
        # Publish to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='AquaChain/DeviceStatus',
            MetricData=metric_data
        )
        
        logger.info(f"Published metrics: {status_counts}, changes: {len(status_updates)}")
        
    except Exception as e:
        logger.error(f"Error publishing metrics: {str(e)}")


def handle_device_offline_alert(device_id: str, offline_duration_minutes: int) -> None:
    """
    Handle alerts for devices that have been offline for extended periods
    This could trigger notifications to users or technicians
    """
    try:
        # For now, just log the alert
        # In production, this could trigger SNS notifications
        logger.warning(f"Device {device_id} has been offline for {offline_duration_minutes} minutes")
        
        # Publish alert metric
        cloudwatch.put_metric_data(
            Namespace='AquaChain/Alerts',
            MetricData=[{
                'MetricName': 'DeviceOfflineAlert',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'DeviceId', 'Value': device_id}
                ]
            }]
        )
        
    except Exception as e:
        logger.error(f"Error handling offline alert for device {device_id}: {str(e)}")