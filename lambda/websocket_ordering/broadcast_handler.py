"""
WebSocket Broadcast Handler for Enhanced Consumer Ordering System
Handles broadcasting order status updates to WebSocket connections
Triggered by DynamoDB Streams, SNS topics, and direct invocations
"""

import json
import boto3
from datetime import datetime
from typing import Dict, Any, List
import logging
import os

# Add shared utilities to path
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='websocket-ordering-broadcast')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_client = boto3.client('apigatewaymanagementapi')

# Environment variables
WEBSOCKET_CONNECTIONS_TABLE = os.environ.get('WEBSOCKET_CONNECTIONS_TABLE_NAME', 'aquachain-websocket-connections-dev')
WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_ENDPOINT')

def lambda_handler(event, context):
    """
    Main handler for WebSocket order broadcasts
    """
    try:
        # Set WebSocket endpoint if not provided in environment
        global WEBSOCKET_ENDPOINT
        if not WEBSOCKET_ENDPOINT:
            # Extract from context for API Gateway invocations
            domain_name = event.get('requestContext', {}).get('domainName')
            stage = event.get('requestContext', {}).get('stage')
            if domain_name and stage:
                WEBSOCKET_ENDPOINT = f"https://{domain_name}/{stage}"
                apigateway_client.meta.config.endpoint_url = WEBSOCKET_ENDPOINT
        else:
            apigateway_client.meta.config.endpoint_url = WEBSOCKET_ENDPOINT
        
        logger.info(f"Processing order broadcast event: {json.dumps(event, default=str)}")
        
        # Handle different event sources
        if 'Records' in event:
            for record in event['Records']:
                if 'Sns' in record:
                    handle_sns_message(record['Sns'])
                elif 'dynamodb' in record:
                    handle_dynamodb_stream(record)
                elif 'eventSource' == 'aws:events':
                    handle_eventbridge_event(record)
        else:
            # Direct invocation
            handle_direct_broadcast(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Order broadcast completed'})
        }
        
    except Exception as e:
        logger.error(f"Order broadcast handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_sns_message(sns_message: Dict[str, Any]) -> None:
    """
    Handle SNS message for order broadcasting
    """
    try:
        topic_arn = sns_message['TopicArn']
        message = json.loads(sns_message['Message'])
        
        if 'order-status-updates' in topic_arn:
            broadcast_order_status_update(message)
        elif 'payment-status-updates' in topic_arn:
            broadcast_payment_status_update(message)
        elif 'technician-assignments' in topic_arn:
            broadcast_technician_assignment_update(message)
        else:
            logger.warning(f"Unknown SNS topic for orders: {topic_arn}")
        
    except Exception as e:
        logger.error(f"Error handling SNS message: {e}")

def handle_dynamodb_stream(record: Dict[str, Any]) -> None:
    """
    Handle DynamoDB Stream event for real-time order updates
    """
    try:
        event_name = record['eventName']
        table_name = record['dynamodb'].get('TableName', '')
        
        if 'orders' in table_name and event_name in ['INSERT', 'MODIFY']:
            # Order status change
            new_image = record['dynamodb'].get('NewImage', {})
            old_image = record['dynamodb'].get('OldImage', {})
            
            order_data = convert_dynamodb_to_dict(new_image)
            old_order_data = convert_dynamodb_to_dict(old_image) if old_image else {}
            
            # Check if status changed
            new_status = order_data.get('status')
            old_status = old_order_data.get('status')
            
            if new_status != old_status:
                order_data['previousStatus'] = old_status
                broadcast_order_status_update(order_data)
            
            # Check if technician assignment changed
            new_technician = order_data.get('assignedTechnician')
            old_technician = old_order_data.get('assignedTechnician')
            
            if new_technician != old_technician and new_technician:
                broadcast_technician_assignment_update(order_data)
            
        elif 'payments' in table_name and event_name in ['INSERT', 'MODIFY']:
            # Payment status change
            new_image = record['dynamodb'].get('NewImage', {})
            old_image = record['dynamodb'].get('OldImage', {})
            
            payment_data = convert_dynamodb_to_dict(new_image)
            old_payment_data = convert_dynamodb_to_dict(old_image) if old_image else {}
            
            # Check if payment status changed
            new_status = payment_data.get('status')
            old_status = old_payment_data.get('status')
            
            if new_status != old_status:
                broadcast_payment_status_update(payment_data)
        
    except Exception as e:
        logger.error(f"Error handling DynamoDB stream: {e}")

def handle_eventbridge_event(event_record: Dict[str, Any]) -> None:
    """
    Handle EventBridge event for order updates
    """
    try:
        detail = event_record.get('detail', {})
        detail_type = event_record.get('detail-type', '')
        
        if detail_type == 'Order Status Update':
            broadcast_order_status_update(detail)
        elif detail_type == 'Payment Status Update':
            broadcast_payment_status_update(detail)
        elif detail_type == 'Technician Assignment Update':
            broadcast_technician_assignment_update(detail)
        else:
            logger.warning(f"Unknown EventBridge detail type: {detail_type}")
        
    except Exception as e:
        logger.error(f"Error handling EventBridge event: {e}")

def handle_direct_broadcast(event: Dict[str, Any]) -> None:
    """
    Handle direct broadcast invocation
    """
    try:
        broadcast_type = event.get('broadcastType')
        data = event.get('data')
        
        if broadcast_type == 'order_status_update':
            broadcast_order_status_update(data)
        elif broadcast_type == 'payment_status_update':
            broadcast_payment_status_update(data)
        elif broadcast_type == 'technician_assignment_update':
            broadcast_technician_assignment_update(data)
        else:
            logger.warning(f"Unknown broadcast type: {broadcast_type}")
        
    except Exception as e:
        logger.error(f"Error handling direct broadcast: {e}")

def broadcast_order_status_update(order_data: Dict[str, Any]) -> None:
    """
    Broadcast order status update to subscribed connections
    """
    try:
        order_id = order_data.get('orderId') or order_data.get('id')
        if not order_id:
            logger.error("No order ID found in order data")
            return
        
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        # Prepare status history for broadcast
        status_history = order_data.get('statusHistory', [])
        if isinstance(status_history, str):
            try:
                status_history = json.loads(status_history)
            except json.JSONDecodeError:
                status_history = []
        
        message = {
            'type': 'order_status_update',
            'orderId': order_id,
            'status': order_data.get('status'),
            'previousStatus': order_data.get('previousStatus'),
            'statusHistory': status_history,
            'assignedTechnician': order_data.get('assignedTechnician'),
            'estimatedDelivery': order_data.get('estimatedDelivery'),
            'deviceType': order_data.get('deviceType'),
            'serviceType': order_data.get('serviceType'),
            'amount': order_data.get('amount'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted order status update for {order_id} (status: {order_data.get('status')}): "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting order status update: {e}")

def broadcast_payment_status_update(payment_data: Dict[str, Any]) -> None:
    """
    Broadcast payment status update to subscribed connections
    """
    try:
        order_id = payment_data.get('orderId')
        if not order_id:
            logger.error("No order ID found in payment data")
            return
        
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'payment_status_update',
            'orderId': order_id,
            'paymentId': payment_data.get('paymentId') or payment_data.get('id'),
            'paymentStatus': payment_data.get('status'),
            'paymentMethod': payment_data.get('paymentMethod'),
            'amount': payment_data.get('amount'),
            'razorpayPaymentId': payment_data.get('razorpayPaymentId'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted payment status update for order {order_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting payment status update: {e}")

def broadcast_technician_assignment_update(assignment_data: Dict[str, Any]) -> None:
    """
    Broadcast technician assignment update to subscribed connections
    """
    try:
        order_id = assignment_data.get('orderId')
        if not order_id:
            logger.error("No order ID found in assignment data")
            return
        
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'technician_assignment_update',
            'orderId': order_id,
            'technicianId': assignment_data.get('assignedTechnician') or assignment_data.get('technicianId'),
            'technicianName': assignment_data.get('technicianName'),
            'technicianPhone': assignment_data.get('technicianPhone'),
            'estimatedArrival': assignment_data.get('estimatedArrival'),
            'distance': assignment_data.get('distance'),
            'assignedAt': assignment_data.get('assignedAt'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted technician assignment update for order {order_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting technician assignment update: {e}")

def broadcast_cod_countdown_update(order_id: str, countdown_data: Dict[str, Any]) -> None:
    """
    Broadcast COD countdown timer update to subscribed connections
    """
    try:
        # Get connections subscribed to this order
        connections = get_order_subscribed_connections(order_id)
        
        message = {
            'type': 'cod_countdown_update',
            'orderId': order_id,
            'remainingSeconds': countdown_data.get('remainingSeconds'),
            'isActive': countdown_data.get('isActive', True),
            'canCancel': countdown_data.get('canCancel', True),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        results = broadcast_to_connections(connections, message)
        
        logger.info(f"Broadcasted COD countdown update for order {order_id}: "
                   f"{results['successful']} successful, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error broadcasting COD countdown update: {e}")

def get_order_subscribed_connections(order_id: str) -> List[Dict[str, Any]]:
    """
    Get connections subscribed to specific order updates
    """
    try:
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
        
        # Scan for connections with this order in their subscriptions
        # In production, consider using a GSI for better performance
        response = table.scan(
            FilterExpression='contains(orderSubscriptions, :order_id) AND connectionType = :conn_type',
            ExpressionAttributeValues={
                ':order_id': order_id,
                ':conn_type': 'order_updates'
            }
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting order subscribed connections: {e}")
        return []

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
        table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
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
                try:
                    return int(value['N'])
                except ValueError:
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

# Utility functions for external invocation

def invoke_order_status_broadcast(order_id: str, order_data: Dict[str, Any]) -> None:
    """
    Utility function to invoke order status broadcast from other services
    """
    try:
        lambda_client = boto3.client('lambda')
        
        payload = {
            'broadcastType': 'order_status_update',
            'data': {
                'orderId': order_id,
                **order_data
            }
        }
        
        lambda_client.invoke(
            FunctionName=os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Invoked order status broadcast for {order_id}")
        
    except Exception as e:
        logger.error(f"Error invoking order status broadcast: {e}")

def invoke_payment_status_broadcast(order_id: str, payment_data: Dict[str, Any]) -> None:
    """
    Utility function to invoke payment status broadcast from other services
    """
    try:
        lambda_client = boto3.client('lambda')
        
        payload = {
            'broadcastType': 'payment_status_update',
            'data': {
                'orderId': order_id,
                **payment_data
            }
        }
        
        lambda_client.invoke(
            FunctionName=os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Invoked payment status broadcast for {order_id}")
        
    except Exception as e:
        logger.error(f"Error invoking payment status broadcast: {e}")

def invoke_technician_assignment_broadcast(order_id: str, assignment_data: Dict[str, Any]) -> None:
    """
    Utility function to invoke technician assignment broadcast from other services
    """
    try:
        lambda_client = boto3.client('lambda')
        
        payload = {
            'broadcastType': 'technician_assignment_update',
            'data': {
                'orderId': order_id,
                **assignment_data
            }
        }
        
        lambda_client.invoke(
            FunctionName=os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Invoked technician assignment broadcast for {order_id}")
        
    except Exception as e:
        logger.error(f"Error invoking technician assignment broadcast: {e}")