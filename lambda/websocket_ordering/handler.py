"""
WebSocket API Lambda Function for Enhanced Consumer Ordering System
Handles real-time order status updates and connection management
"""

import json
import boto3
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import os
from botocore.exceptions import ClientError

# Add shared utilities to path
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='websocket-ordering')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_client = boto3.client('apigatewaymanagementapi')
cognito_client = boto3.client('cognito-idp')
ssm_client = boto3.client('ssm')

# Environment variables
WEBSOCKET_CONNECTIONS_TABLE = os.environ.get('WEBSOCKET_CONNECTIONS_TABLE_NAME', 'aquachain-websocket-connections-dev')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE_NAME', 'aquachain-orders-dev')
WEBSOCKET_ENDPOINT = None  # Will be set dynamically

class WebSocketError(Exception):
    """Custom exception for WebSocket errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for WebSocket API
    Handles connect, disconnect, and message routing for order updates
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
        
        logger.info(f"WebSocket ordering event: {route_key} for connection {connection_id}")
        
        if route_key == '$connect':
            return handle_connect(event, connection_id)
        elif route_key == '$disconnect':
            return handle_disconnect(event, connection_id)
        elif route_key == 'subscribe_order':
            return handle_subscribe_order(event, connection_id)
        elif route_key == 'unsubscribe_order':
            return handle_unsubscribe_order(event, connection_id)
        elif route_key == 'ping':
            return handle_ping(event, connection_id)
        else:
            return handle_default_message(event, connection_id)
        
    except Exception as e:
        logger.error(f"WebSocket ordering handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_connect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket connection establishment for order updates
    """
    try:
        # Extract authentication token from query parameters
        query_params = event.get('queryStringParameters') or {}
        auth_token = query_params.get('token')
        
        if not auth_token:
            logger.warning(f"Connection {connection_id} rejected: No auth token")
            return {'statusCode': 401}
        
        # Validate JWT token
        user_info = validate_jwt_token(auth_token)
        if not user_info:
            logger.warning(f"Connection {connection_id} rejected: Invalid token")
            return {'statusCode': 401}
        
        # Store connection information
        connection_record = {
            'connectionId': connection_id,
            'userId': user_info['sub'],
            'userRole': user_info.get('cognito:groups', ['consumer'])[0],
            'connectionType': 'order_updates',
            'connectedAt': datetime.utcnow().isoformat(),
            'lastPing': datetime.utcnow().isoformat(),
            'orderSubscriptions': [],  # List of order IDs subscribed to
            'ttl': int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }
        
        store_connection(connection_record)
        
        # Send welcome message
        welcome_message = {
            'type': 'connection_established',
            'connectionId': connection_id,
            'userId': user_info['sub'],
            'service': 'order_updates',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, welcome_message)
        
        logger.info(f"Order WebSocket connection established: {connection_id} for user {user_info['sub']}")
        
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
        
        logger.info(f"Order WebSocket connection disconnected: {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")
        return {'statusCode': 500}

def handle_subscribe_order(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle subscription to specific order updates
    """
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('orderId')
        
        if not order_id:
            send_error_message(connection_id, "Missing order ID")
            return {'statusCode': 400}
        
        # Get connection info
        connection = get_connection(connection_id)
        if not connection:
            return {'statusCode': 404}
        
        # Validate subscription permissions
        if not validate_order_subscription_permissions(connection, order_id):
            send_error_message(connection_id, "Insufficient permissions for order subscription")
            return {'statusCode': 403}
        
        # Add order subscription
        add_order_subscription(connection_id, order_id)
        
        # Send confirmation with current order status
        order_status = get_order_status(order_id)
        confirmation_message = {
            'type': 'order_subscription_confirmed',
            'orderId': order_id,
            'currentStatus': order_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, confirmation_message)
        
        logger.info(f"Order subscription added: {order_id} for connection {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling order subscription: {e}")
        send_error_message(connection_id, f"Subscription error: {str(e)}")
        return {'statusCode': 500}

def handle_unsubscribe_order(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle unsubscription from order updates
    """
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('orderId')
        
        if not order_id:
            send_error_message(connection_id, "Missing order ID")
            return {'statusCode': 400}
        
        # Remove order subscription
        remove_order_subscription(connection_id, order_id)
        
        # Send confirmation
        confirmation_message = {
            'type': 'order_unsubscription_confirmed',
            'orderId': order_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        send_message_to_connection(connection_id, confirmation_message)
        
        logger.info(f"Order unsubscribed: {order_id} for connection {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling order unsubscription: {e}")
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
        # For demo purposes, we'll do basic validation
        # In production, implement full JWT verification with Cognito public keys
        
        # Decode without verification for demo (NOT for production)
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        
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

def validate_order_subscription_permissions(connection: Dict[str, Any], order_id: str) -> bool:
    """
    Validate that user has permission to subscribe to specific order updates
    """
    try:
        user_role = connection['userRole']
        user_id = connection['userId']
        
        # Get order information
        order = get_order_info(order_id)
        if not order:
            return False
        
        # Consumers can only subscribe to their own orders
        if user_role == 'consumer':
            return order.get('consumerId') == user_id
        
        # Technicians can subscribe to orders assigned to them
        elif user_role == 'technician':
            return (order.get('consumerId') == user_id or 
                   order.get('assignedTechnician') == user_id)
        
        # Administrators can subscribe to any order
        elif user_role == 'administrator':
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating order subscription permissions: {e}")
        return False

def store_connection(connection: Dict[str, Any]) -> None:
    """
    Store WebSocket connection information in DynamoDB
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        table.put_item(Item=connection)
        
    except Exception as e:
        logger.error(f"Error storing connection: {e}")
        raise WebSocketError(f"Failed to store connection: {e}")

def get_connection(connection_id: str) -> Optional[Dict[str, Any]]:
    """
    Get connection information from DynamoDB
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
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
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        table.delete_item(Key={'connectionId': connection_id})
        
    except Exception as e:
        logger.warning(f"Error removing connection: {e}")

def add_order_subscription(connection_id: str, order_id: str) -> None:
    """
    Add order subscription to connection record
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        
        # Get current connection
        connection = get_connection(connection_id)
        if not connection:
            raise WebSocketError("Connection not found")
        
        # Add order ID to subscriptions if not already present
        current_subscriptions = connection.get('orderSubscriptions', [])
        if order_id not in current_subscriptions:
            current_subscriptions.append(order_id)
            
            table.update_item(
                Key={'connectionId': connection_id},
                UpdateExpression='SET orderSubscriptions = :subscriptions',
                ExpressionAttributeValues={':subscriptions': current_subscriptions}
            )
        
    except Exception as e:
        logger.error(f"Error adding order subscription: {e}")
        raise WebSocketError(f"Failed to add order subscription: {e}")

def remove_order_subscription(connection_id: str, order_id: str) -> None:
    """
    Remove order subscription from connection record
    """
    try:
        # Get current connection
        connection = get_connection(connection_id)
        if not connection:
            return
        
        # Remove order ID from subscriptions
        current_subscriptions = connection.get('orderSubscriptions', [])
        if order_id in current_subscriptions:
            current_subscriptions.remove(order_id)
            
            table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
            table.update_item(
                Key={'connectionId': connection_id},
                UpdateExpression='SET orderSubscriptions = :subscriptions',
                ExpressionAttributeValues={':subscriptions': current_subscriptions}
            )
        
    except Exception as e:
        logger.error(f"Error removing order subscription: {e}")

def update_connection_ping(connection_id: str) -> None:
    """
    Update last ping timestamp for connection
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        
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

def get_order_info(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get order information from DynamoDB
    """
    try:
        table = dynamodb.Table(ORDERS_TABLE)
        response = table.get_item(
            Key={
                'PK': f'ORDER#{order_id}',
                'SK': f'ORDER#{order_id}'
            }
        )
        return response.get('Item')
        
    except Exception as e:
        logger.error(f"Error getting order info: {e}")
        return None

def get_order_status(order_id: str) -> Optional[str]:
    """
    Get current order status
    """
    try:
        order = get_order_info(order_id)
        return order.get('status') if order else None
        
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        return None

# Broadcast functions for sending order updates to subscribed connections

def broadcast_order_status_update(order_id: str, order_data: Dict[str, Any]) -> None:
    """
    Broadcast order status update to subscribed connections
    This function is called when order status changes
    """
    try:
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'order_status_update',
            'orderId': order_id,
            'status': order_data.get('status'),
            'previousStatus': order_data.get('previousStatus'),
            'statusHistory': order_data.get('statusHistory', []),
            'assignedTechnician': order_data.get('assignedTechnician'),
            'estimatedDelivery': order_data.get('estimatedDelivery'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add optional fields if present in order_data
        if 'deviceType' in order_data:
            message['deviceType'] = order_data['deviceType']
        if 'serviceType' in order_data:
            message['serviceType'] = order_data['serviceType']
        if 'amount' in order_data:
            message['amount'] = order_data['amount']
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted order status update for {order_id}: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting order status update: {e}")

def broadcast_payment_status_update(order_id: str, payment_data: Dict[str, Any]) -> None:
    """
    Broadcast payment status update to subscribed connections
    """
    try:
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'payment_status_update',
            'orderId': order_id,
            'paymentStatus': payment_data.get('status'),
            'paymentMethod': payment_data.get('paymentMethod'),
            'amount': payment_data.get('amount'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted payment status update for {order_id}: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting payment status update: {e}")

def broadcast_technician_assignment_update(order_id: str, technician_data: Dict[str, Any]) -> None:
    """
    Broadcast technician assignment update to subscribed connections
    """
    try:
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'technician_assignment_update',
            'orderId': order_id,
            'technicianId': technician_data.get('technicianId'),
            'technicianName': technician_data.get('name'),
            'technicianPhone': technician_data.get('phone'),
            'estimatedArrival': technician_data.get('estimatedArrival'),
            'distance': technician_data.get('distance'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        successful_sends = 0
        failed_sends = 0
        
        for connection in connections:
            if send_message_to_connection(connection['connectionId'], message):
                successful_sends += 1
            else:
                failed_sends += 1
        
        logger.info(f"Broadcasted technician assignment update for {order_id}: "
                   f"{successful_sends} successful, {failed_sends} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting technician assignment update: {e}")

def get_order_subscribed_connections(order_id: str) -> List[Dict[str, Any]]:
    """
    Get connections subscribed to specific order updates
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        
        # Scan for connections with this order in their subscriptions
        response = table.scan(
            FilterExpression='contains(orderSubscriptions, :order_id)',
            ExpressionAttributeValues={':order_id': order_id}
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting order subscribed connections: {e}")
        return []