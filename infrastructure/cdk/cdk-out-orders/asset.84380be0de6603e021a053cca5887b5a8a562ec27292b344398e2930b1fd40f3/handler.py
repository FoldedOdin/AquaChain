"""
WebSocket API Lambda Function for AquaChain System
Handles real-time connections, authentication, and live updates
"""

import json
import boto3
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from botocore.exceptions import ClientError

# Add shared utilities to path
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='websocket-api')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_client = boto3.client('apigatewaymanagementapi')
cognito_client = boto3.client('cognito-idp')
ssm_client = boto3.client('ssm')

# Environment variables
CONNECTIONS_TABLE = 'aquachain-websocket-connections'
USERS_TABLE = 'aquachain-users'
WEBSOCKET_ENDPOINT = None  # Will be set dynamically

# Connection types
CONNECTION_TYPES = {
    'dashboard': 'consumer_dashboard',
    'technician': 'technician_app',
    'admin': 'admin_console'
}

class WebSocketError(Exception):
    """Custom exception for WebSocket errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for WebSocket API
    Handles connect, disconnect, and message routing
    """
    try:
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        domain_name = event.get('requestContext', {}).get('domainName')
        stage = event.get('requestContext', {}).get('stage')
        
        # Set API Gateway Management API endpoint
        global WEBSOCKET_ENDPOINT
        WEBSOCKET_ENDPOINT = f"https://{domain_name}/{stage}"
        apigateway_client.meta.config.endpoint_url = WEBSOCKET_ENDPOINT
        
        logger.info(f"WebSocket event: {route_key} for connection {connection_id}")
        
        if route_key == '$connect':
            return handle_connect(event, connection_id)
        elif route_key == '$disconnect':
            return handle_disconnect(event, connection_id)
        elif route_key == 'subscribe':
            return handle_subscribe(event, connection_id)
        elif route_key == 'unsubscribe':
            return handle_unsubscribe(event, connection_id)
        elif route_key == 'ping':
            return handle_ping(event, connection_id)
        else:
            return handle_default_message(event, connection_id)
        
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_connect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket connection establishment
    """
    try:
        # Extract authentication token from query parameters
        query_params = event.get('queryStringParameters') or {}
        auth_token = query_params.get('token')
        connection_type = query_params.get('type', 'dashboard')
        
        if not auth_token:
            logger.warning(f"Connection {connection_id} rejected: No auth token")
            return {'statusCode': 401}
        
        # Validate JWT token
        user_info = validate_jwt_token(auth_token)
        if not user_info:
            logger.warning(f"Connection {connection_id} rejected: Invalid token")
            return {'statusCode': 401}
        
        # Validate connection type against user role
        if not validate_connection_type(user_info, connection_type):
            logger.warning(f"Connection {connection_id} rejected: Invalid connection type for role")
            return {'statusCode': 403}
        
        # Store connection information
        connection_record = {
            'connectionId': connection_id,
            'userId': user_info['sub'],
            'userRole': user_info.get('cognito:groups', ['consumer'])[0],
            'connectionType': connection_type,
            'connectedAt': datetime.utcnow().isoformat(),
            'lastPing': datetime.utcnow().isoformat(),
            'subscriptions': [],
            'ttl': int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }
        
        store_connection(connection_record)
        
        # Send welcome message
        welcome_message = {
            'type': 'connection_established',
            'connectionId': connection_id,
            'userId': user_info['sub'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, welcome_message)
        
        logger.info(f"Connection established: {connection_id} for user {user_info['sub']}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling connect: {e}")
        return {'statusCode': 500}

def handle_disconnect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection
    """
    try:
        # Remove connection record
        remove_connection(connection_id)
        
        logger.info(f"Connection disconnected: {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")
        return {'statusCode': 500}

def handle_subscribe(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle subscription to specific data streams
    """
    try:
        body = json.loads(event.get('body', '{}'))
        subscription_type = body.get('subscriptionType')
        filters = body.get('filters', {})
        
        if not subscription_type:
            send_error_message(connection_id, "Missing subscription type")
            return {'statusCode': 400}
        
        # Get connection info
        connection = get_connection(connection_id)
        if not connection:
            return {'statusCode': 404}
        
        # Validate subscription permissions
        if not validate_subscription_permissions(connection, subscription_type, filters):
            send_error_message(connection_id, "Insufficient permissions for subscription")
            return {'statusCode': 403}
        
        # Add subscription
        subscription = {
            'type': subscription_type,
            'filters': filters,
            'subscribedAt': datetime.utcnow().isoformat()
        }
        
        add_subscription(connection_id, subscription)
        
        # Send confirmation
        confirmation_message = {
            'type': 'subscription_confirmed',
            'subscriptionType': subscription_type,
            'filters': filters,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, confirmation_message)
        
        logger.info(f"Subscription added: {subscription_type} for connection {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling subscribe: {e}")
        send_error_message(connection_id, f"Subscription error: {str(e)}")
        return {'statusCode': 500}

def handle_unsubscribe(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle unsubscription from data streams
    """
    try:
        body = json.loads(event.get('body', '{}'))
        subscription_type = body.get('subscriptionType')
        
        if not subscription_type:
            send_error_message(connection_id, "Missing subscription type")
            return {'statusCode': 400}
        
        # Remove subscription
        remove_subscription(connection_id, subscription_type)
        
        # Send confirmation
        confirmation_message = {
            'type': 'unsubscription_confirmed',
            'subscriptionType': subscription_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, confirmation_message)
        
        logger.info(f"Unsubscribed: {subscription_type} for connection {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling unsubscribe: {e}")
        return {'statusCode': 500}

def handle_ping(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle ping messages to keep connection alive
    """
    try:
        # Update last ping timestamp
        update_connection_ping(connection_id)
        
        # Send pong response
        pong_message = {
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, pong_message)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling ping: {e}")
        return {'statusCode': 500}

def handle_default_message(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle unknown message types
    """
    try:
        error_message = {
            'type': 'error',
            'message': 'Unknown message type',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, error_message)
        
        return {'statusCode': 400}
        
    except Exception as e:
        logger.error(f"Error handling default message: {e}")
        return {'statusCode': 500}

def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and extract user information
    """
    try:
        # Get Cognito public keys (in production, cache these)
        public_keys = get_cognito_public_keys()
        
        # Decode token header to get key ID
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        
        if kid not in public_keys:
            logger.warning(f"Unknown key ID: {kid}")
            return None
        
        # Verify and decode token
        public_key = public_keys[kid]
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=get_cognito_client_id()
        )
        
        # Check token expiration
        if decoded_token.get('exp', 0) < datetime.utcnow().timestamp():
            logger.warning("Token expired")
            return None
        
        return decoded_token
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error validating JWT token: {e}")
        return None

def validate_connection_type(user_info: Dict[str, Any], connection_type: str) -> bool:
    """
    Validate that user role can use the requested connection type
    """
    user_groups = user_info.get('cognito:groups', ['consumer'])
    user_role = user_groups[0] if user_groups else 'consumer'
    
    allowed_types = {
        'consumer': ['dashboard'],
        'technician': ['dashboard', 'technician'],
        'administrator': ['dashboard', 'technician', 'admin']
    }
    
    return connection_type in allowed_types.get(user_role, [])

def validate_subscription_permissions(connection: Dict[str, Any], 
                                    subscription_type: str, 
                                    filters: Dict[str, Any]) -> bool:
    """
    Validate that user has permission to subscribe to specific data streams
    """
    user_role = connection['userRole']
    user_id = connection['userId']
    
    # Define subscription permissions by role
    if subscription_type == 'water_quality_readings':
        if user_role == 'consumer':
            # Consumers can only subscribe to their own devices
            device_ids = filters.get('deviceIds', [])
            user_devices = get_user_devices(user_id)
            return all(device_id in user_devices for device_id in device_ids)
        elif user_role in ['technician', 'administrator']:
            # Technicians and admins can subscribe to any devices
            return True
    
    elif subscription_type == 'alerts':
        if user_role == 'consumer':
            # Consumers can only subscribe to alerts for their devices
            device_ids = filters.get('deviceIds', [])
            user_devices = get_user_devices(user_id)
            return all(device_id in user_devices for device_id in device_ids)
        elif user_role in ['technician', 'administrator']:
            return True
    
    elif subscription_type == 'service_requests':
        if user_role == 'consumer':
            # Consumers can only subscribe to their own service requests
            return filters.get('userId') == user_id
        elif user_role == 'technician':
            # Technicians can subscribe to their assigned requests
            return filters.get('technicianId') == user_id
        elif user_role == 'administrator':
            return True
    
    elif subscription_type == 'system_status':
        # Only administrators can subscribe to system status
        return user_role == 'administrator'
    
    return False

def store_connection(connection: Dict[str, Any]) -> None:
    """
    Store WebSocket connection information in DynamoDB
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.put_item(Item=connection)
        
    except Exception as e:
        logger.error(f"Error storing connection: {e}")
        raise WebSocketError(f"Failed to store connection: {e}")

def get_connection(connection_id: str) -> Optional[Dict[str, Any]]:
    """
    Get connection information from DynamoDB
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        response = table.get_item(Key={'connectionId': connection_id})
        return response.get('Item')
        
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        return None

def remove_connection(connection_id: str) -> None:
    """
    Remove connection from DynamoDB
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.delete_item(Key={'connectionId': connection_id})
        
    except Exception as e:
        logger.warning(f"Error removing connection: {e}")

def add_subscription(connection_id: str, subscription: Dict[str, Any]) -> None:
    """
    Add subscription to connection record
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        table.update_item(
            Key={'connectionId': connection_id},
            UpdateExpression='SET subscriptions = list_append(if_not_exists(subscriptions, :empty_list), :subscription)',
            ExpressionAttributeValues={
                ':subscription': [subscription],
                ':empty_list': []
            }
        )
        
    except Exception as e:
        logger.error(f"Error adding subscription: {e}")
        raise WebSocketError(f"Failed to add subscription: {e}")

def remove_subscription(connection_id: str, subscription_type: str) -> None:
    """
    Remove subscription from connection record
    """
    try:
        # Get current connection
        connection = get_connection(connection_id)
        if not connection:
            return
        
        # Filter out the subscription
        updated_subscriptions = [
            sub for sub in connection.get('subscriptions', [])
            if sub.get('type') != subscription_type
        ]
        
        # Update connection record
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.update_item(
            Key={'connectionId': connection_id},
            UpdateExpression='SET subscriptions = :subscriptions',
            ExpressionAttributeValues={':subscriptions': updated_subscriptions}
        )
        
    except Exception as e:
        logger.error(f"Error removing subscription: {e}")

def update_connection_ping(connection_id: str) -> None:
    """
    Update last ping timestamp for connection
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        table.update_item(
            Key={'connectionId': connection_id},
            UpdateExpression='SET lastPing = :timestamp',
            ExpressionAttributeValues={':timestamp': datetime.utcnow().isoformat()}
        )
        
    except Exception as e:
        logger.warning(f"Error updating connection ping: {e}")

def send_message_to_connection(connection_id: str, message: Dict[str, Any]) -> bool:
    """
    Send message to specific WebSocket connection
    """
    try:
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'GoneException':
            # Connection is closed, remove it
            logger.info(f"Connection {connection_id} is gone, removing")
            remove_connection(connection_id)
        else:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending message to connection {connection_id}: {e}")
        return False

def send_error_message(connection_id: str, error_message: str) -> None:
    """
    Send error message to connection
    """
    error_msg = {
        'type': 'error',
        'message': error_message,
        'timestamp': datetime.utcnow().isoformat()
    }
    send_message_to_connection(connection_id, error_msg)

def get_user_devices(user_id: str) -> List[str]:
    """
    Get list of device IDs associated with user
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'userId': user_id})
        user = response.get('Item', {})
        return user.get('deviceIds', [])
        
    except Exception as e:
        logger.error(f"Error getting user devices: {e}")
        return []

def get_cognito_public_keys() -> Dict[str, str]:
    """
    Get Cognito public keys for JWT verification
    In production, these should be cached
    """
    try:
        # This would typically fetch from Cognito JWKS endpoint
        # For now, return a placeholder
        return {
            'key1': 'public_key_1',
            'key2': 'public_key_2'
        }
    except Exception as e:
        logger.error(f"Error getting Cognito public keys: {e}")
        return {}

def get_cognito_client_id() -> str:
    """
    Get Cognito client ID from SSM Parameter Store
    """
    try:
        response = ssm_client.get_parameter(
            Name='/aquachain/cognito/client-id',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Error getting Cognito client ID: {e}")
        return 'default-client-id'

# Broadcast functions for sending updates to subscribed connections

def broadcast_water_quality_update(device_id: str, reading_data: Dict[str, Any]) -> None:
    """
    Broadcast water quality update to subscribed connections
    This function would be called from the data processing pipeline
    """
    try:
        # Get connections subscribed to water quality readings for this device
        connections = get_subscribed_connections('water_quality_readings', {'deviceIds': [device_id]})
        
        message = {
            'type': 'water_quality_update',
            'deviceId': device_id,
            'data': reading_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted water quality update for device {device_id}: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting water quality update: {e}")

def broadcast_alert(alert_data: Dict[str, Any]) -> None:
    """
    Broadcast alert to subscribed connections
    """
    try:
        device_id = alert_data['deviceId']
        
        # Get connections subscribed to alerts for this device
        connections = get_subscribed_connections('alerts', {'deviceIds': [device_id]})
        
        message = {
            'type': 'alert',
            'data': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted alert for device {device_id}: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting alert: {e}")

def broadcast_service_request_update(service_request: Dict[str, Any]) -> None:
    """
    Broadcast service request update to relevant connections
    """
    try:
        consumer_id = service_request['consumerId']
        technician_id = service_request.get('technicianId')
        
        # Get connections for consumer
        consumer_connections = get_subscribed_connections('service_requests', {'userId': consumer_id})
        
        # Get connections for technician if assigned
        technician_connections = []
        if technician_id:
            technician_connections = get_subscribed_connections('service_requests', {'technicianId': technician_id})
        
        all_connections = consumer_connections + technician_connections
        
        message = {
            'type': 'service_request_update',
            'data': service_request,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in all_connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted service request update: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting service request update: {e}")

def get_subscribed_connections(subscription_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get connections subscribed to specific data stream with matching filters
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Scan for connections with matching subscriptions
        # In production, consider using GSI for better performance
        response = table.scan()
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
        # Check device IDs
        sub_device_ids = set(subscription_filters.get('deviceIds', []))
        broadcast_device_ids = set(broadcast_filters.get('deviceIds', []))
        
        if sub_device_ids and broadcast_device_ids:
            if not sub_device_ids.intersection(broadcast_device_ids):
                return False
        
        # Check user ID
        sub_user_id = subscription_filters.get('userId')
        broadcast_user_id = broadcast_filters.get('userId')
        
        if sub_user_id and broadcast_user_id:
            if sub_user_id != broadcast_user_id:
                return False
        
        # Check technician ID
        sub_technician_id = subscription_filters.get('technicianId')
        broadcast_technician_id = broadcast_filters.get('technicianId')
        
        if sub_technician_id and broadcast_technician_id:
            if sub_technician_id != broadcast_technician_id:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error matching subscription filters: {e}")
        return False