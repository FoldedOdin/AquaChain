"""
WebSocket Broadcast Handler for AquaChain System
Handles broadcasting updates to WebSocket connections
Triggered by SNS topics and DynamoDB Streams
"""

import json
import boto3
from datetime import datetime
from typing import Dict, Any, List
import logging

# Add shared utilities to path
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='websocket-broadcast')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_client = boto3.client('apigatewaymanagementapi')

# Environment variables
CONNECTIONS_TABLE = 'aquachain-websocket-connections'
WEBSOCKET_ENDPOINT = None  # Will be set from environment

def lambda_handler(event, context):
    """
    Main handler for WebSocket broadcasts
    """
    try:
        # Set WebSocket endpoint
        global WEBSOCKET_ENDPOINT
        WEBSOCKET_ENDPOINT = context.invoked_function_arn.replace('arn:aws:lambda:', 'https://').replace(':function:', '.execute-api.').replace('broadcast_handler', 'websocket')
        apigateway_client.meta.config.endpoint_url = WEBSOCKET_ENDPOINT
        
        logger.info(f"Processing broadcast event: {json.dumps(event)}")
        
        # Handle different event sources
        if 'Records' in event:
            for record in event['Records']:
                if 'Sns' in record:
                    handle_sns_message(record['Sns'])
                elif 'dynamodb' in record:
                    handle_dynamodb_stream(record)
        else:
            # Direct invocation
            handle_direct_broadcast(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Broadcast completed'})
        }
        
    except Exception as e:
        logger.error(f"Broadcast handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_sns_message(sns_message: Dict[str, Any]) -> None:
    """
    Handle SNS message for broadcasting
    """
    try:
        topic_arn = sns_message['TopicArn']
        message = json.loads(sns_message['Message'])
        
        if 'aquachain-critical-alerts' in topic_arn or 'aquachain-warning-alerts' in topic_arn:
            broadcast_alert(message)
        elif 'aquachain-service-updates' in topic_arn:
            broadcast_service_update(message)
        elif 'aquachain-system-alerts' in topic_arn:
            broadcast_system_alert(message)
        else:
            logger.warning(f"Unknown SNS topic: {topic_arn}")
        
    except Exception as e:
        logger.error(f"Error handling SNS message: {e}")

def handle_dynamodb_stream(record: Dict[str, Any]) -> None:
    """
    Handle DynamoDB Stream event for real-time updates
    """
    try:
        event_name = record['eventName']
        table_name = record['dynamodb'].get('TableName', '')
        
        if 'aquachain-readings' in table_name and event_name == 'INSERT':
            # New water quality reading
            new_image = record['dynamodb']['NewImage']
            reading_data = convert_dynamodb_to_dict(new_image)
            broadcast_water_quality_reading(reading_data)
            
        elif 'aquachain-service-requests' in table_name and event_name in ['INSERT', 'MODIFY']:
            # Service request update
            new_image = record['dynamodb']['NewImage']
            service_request = convert_dynamodb_to_dict(new_image)
            broadcast_service_request_update(service_request)
        
    except Exception as e:
        logger.error(f"Error handling DynamoDB stream: {e}")

def handle_direct_broadcast(event: Dict[str, Any]) -> None:
    """
    Handle direct broadcast invocation
    """
    try:
        broadcast_type = event.get('broadcastType')
        data = event.get('data')
        
        if broadcast_type == 'water_quality_reading':
            broadcast_water_quality_reading(data)
        elif broadcast_type == 'alert':
            broadcast_alert(data)
        elif broadcast_type == 'service_request_update':
            broadcast_service_request_update(data)
        elif broadcast_type == 'system_status':
            broadcast_system_status(data)
        else:
            logger.warning(f"Unknown broadcast type: {broadcast_type}")
        
    except Exception as e:
        logger.error(f"Error handling direct broadcast: {e}")

def broadcast_water_quality_reading(reading_data: Dict[str, Any]) -> None:
    """
    Broadcast new water quality reading to subscribed connections
    """
    try:
        device_id = reading_data['deviceId']
        
        # Get connections subscribed to water quality readings for this device
        connections = get_subscribed_connections('water_quality_readings', {'deviceIds': [device_id]})
        
        message = {
            'type': 'water_quality_reading',
            'deviceId': device_id,
            'timestamp': reading_data['timestamp'],
            'wqi': reading_data['wqi'],
            'readings': reading_data['readings'],
            'anomalyType': reading_data['anomalyType'],
            'location': reading_data.get('location', {}),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted water quality reading for device {device_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting water quality reading: {e}")

def broadcast_alert(alert_data: Dict[str, Any]) -> None:
    """
    Broadcast alert to subscribed connections
    """
    try:
        device_id = alert_data['deviceId']
        alert_level = alert_data['alertLevel']
        
        # Get connections subscribed to alerts for this device
        connections = get_subscribed_connections('alerts', {'deviceIds': [device_id]})
        
        message = {
            'type': 'alert',
            'alertLevel': alert_level,
            'deviceId': device_id,
            'timestamp': alert_data['timestamp'],
            'wqi': alert_data['wqi'],
            'anomalyType': alert_data['anomalyType'],
            'alertReasons': alert_data.get('alertReasons', []),
            'location': alert_data.get('location', {}),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted {alert_level} alert for device {device_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting alert: {e}")

def broadcast_service_update(service_data: Dict[str, Any]) -> None:
    """
    Broadcast service request update
    """
    try:
        consumer_id = service_data.get('consumerId')
        technician_id = service_data.get('technicianId')
        request_id = service_data.get('requestId')
        
        # Get connections for consumer
        consumer_connections = []
        if consumer_id:
            consumer_connections = get_subscribed_connections('service_requests', {'userId': consumer_id})
        
        # Get connections for technician
        technician_connections = []
        if technician_id:
            technician_connections = get_subscribed_connections('service_requests', {'technicianId': technician_id})
        
        all_connections = consumer_connections + technician_connections
        
        message = {
            'type': 'service_request_update',
            'requestId': request_id,
            'status': service_data.get('status'),
            'updateType': service_data.get('updateType'),
            'estimatedArrival': service_data.get('estimatedArrival'),
            'notes': service_data.get('notes', []),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(all_connections, message)
        
        logger.info(f"Broadcasted service request update for {request_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting service update: {e}")

def broadcast_service_request_update(service_request: Dict[str, Any]) -> None:
    """
    Broadcast service request update from DynamoDB stream
    """
    try:
        consumer_id = service_request.get('consumerId')
        technician_id = service_request.get('technicianId')
        request_id = service_request.get('requestId')
        status = service_request.get('status')
        
        # Get connections for consumer
        consumer_connections = []
        if consumer_id:
            consumer_connections = get_subscribed_connections('service_requests', {'userId': consumer_id})
        
        # Get connections for technician
        technician_connections = []
        if technician_id:
            technician_connections = get_subscribed_connections('service_requests', {'technicianId': technician_id})
        
        all_connections = consumer_connections + technician_connections
        
        message = {
            'type': 'service_request_update',
            'requestId': request_id,
            'status': status,
            'deviceId': service_request.get('deviceId'),
            'location': service_request.get('location', {}),
            'estimatedArrival': service_request.get('estimatedArrival'),
            'notes': service_request.get('notes', []),
            'createdAt': service_request.get('createdAt'),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(all_connections, message)
        
        logger.info(f"Broadcasted service request update for {request_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting service request update: {e}")

def broadcast_system_alert(system_data: Dict[str, Any]) -> None:
    """
    Broadcast system-wide alert to administrators
    """
    try:
        # Get admin connections subscribed to system status
        connections = get_subscribed_connections('system_status', {})
        
        message = {
            'type': 'system_alert',
            'alertType': system_data.get('alertType'),
            'severity': system_data.get('severity'),
            'message': system_data.get('message'),
            'affectedServices': system_data.get('affectedServices', []),
            'timestamp': system_data.get('timestamp'),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted system alert: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting system alert: {e}")

def broadcast_system_status(status_data: Dict[str, Any]) -> None:
    """
    Broadcast system status update to administrators
    """
    try:
        # Get admin connections subscribed to system status
        connections = get_subscribed_connections('system_status', {})
        
        message = {
            'type': 'system_status',
            'overallHealth': status_data.get('overallHealth'),
            'services': status_data.get('services', {}),
            'metrics': status_data.get('metrics', {}),
            'activeAlerts': status_data.get('activeAlerts', []),
            'timestamp': status_data.get('timestamp'),
            'broadcastTime': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted system status: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting system status: {e}")

def get_subscribed_connections(subscription_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get connections subscribed to specific data stream with matching filters
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Scan for active connections
        response = table.scan(
            FilterExpression='attribute_exists(connectionId)'
        )
        connections = response.get('Items', [])
        
        matching_connections = []
        
        for connection in connections:
            subscriptions = connection.get('subscriptions', [])
            
            for subscription in subscriptions:
                if subscription.get('type') == subscription_type:
                    # Check if filters match
                    if subscription_matches_filters(subscription.get('filters', {}), filters):
                        matching_connections.append(connection)
                        break
        
        return matching_connections
        
    except Exception as e:
        logger.error(f"Error getting subscribed connections: {e}")
        return []

def subscription_matches_filters(subscription_filters: Dict[str, Any], 
                               broadcast_filters: Dict[str, Any]) -> bool:
    """
    Check if subscription filters match broadcast filters
    """
    try:
        # If no broadcast filters, match all subscriptions
        if not broadcast_filters:
            return True
        
        # Check device IDs
        sub_device_ids = set(subscription_filters.get('deviceIds', []))
        broadcast_device_ids = set(broadcast_filters.get('deviceIds', []))
        
        if broadcast_device_ids:
            if sub_device_ids:
                # Both have device IDs - check intersection
                if not sub_device_ids.intersection(broadcast_device_ids):
                    return False
            # If subscription has no device filter, it matches all devices
        
        # Check user ID
        sub_user_id = subscription_filters.get('userId')
        broadcast_user_id = broadcast_filters.get('userId')
        
        if broadcast_user_id and sub_user_id:
            if sub_user_id != broadcast_user_id:
                return False
        
        # Check technician ID
        sub_technician_id = subscription_filters.get('technicianId')
        broadcast_technician_id = broadcast_filters.get('technicianId')
        
        if broadcast_technician_id and sub_technician_id:
            if sub_technician_id != broadcast_technician_id:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error matching subscription filters: {e}")
        return False

def broadcast_to_connections(connections: List[Dict[str, Any]], 
                           message: Dict[str, Any]) -> Dict[str, int]:
    """
    Send message to multiple WebSocket connections
    """
    successful = 0
    failed = 0
    stale_connections = []
    
    for connection in connections:
        connection_id = connection['connectionId']
        
        try:
            apigateway_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
            successful += 1
            
        except apigateway_client.exceptions.GoneException:
            # Connection is stale, mark for removal
            logger.info(f"Connection {connection_id} is gone, marking for removal")
            stale_connections.append(connection_id)
            failed += 1
            
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
            failed += 1
    
    # Clean up stale connections
    for connection_id in stale_connections:
        remove_stale_connection(connection_id)
    
    return {'successful': successful, 'failed': failed}

def remove_stale_connection(connection_id: str) -> None:
    """
    Remove stale WebSocket connection from database
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.delete_item(Key={'connectionId': connection_id})
        logger.info(f"Removed stale connection: {connection_id}")
        
    except Exception as e:
        logger.warning(f"Error removing stale connection {connection_id}: {e}")

def convert_dynamodb_to_dict(dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert DynamoDB item format to regular dictionary
    """
    def convert_value(value):
        if isinstance(value, dict):
            if 'S' in value:
                return value['S']
            elif 'N' in value:
                return float(value['N'])
            elif 'B' in value:
                return value['B']
            elif 'SS' in value:
                return value['SS']
            elif 'NS' in value:
                return [float(n) for n in value['NS']]
            elif 'BS' in value:
                return value['BS']
            elif 'M' in value:
                return {k: convert_value(v) for k, v in value['M'].items()}
            elif 'L' in value:
                return [convert_value(item) for item in value['L']]
            elif 'NULL' in value:
                return None
            elif 'BOOL' in value:
                return value['BOOL']
        return value
    
    return {key: convert_value(value) for key, value in dynamodb_item.items()}