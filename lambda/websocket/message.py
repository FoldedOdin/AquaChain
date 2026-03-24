"""
WebSocket Message Handler
Handles incoming WebSocket messages from clients
"""

import json
import boto3
import os
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])
apigateway_management = None  # Initialized per request


def get_apigateway_client(domain_name: str, stage: str):
    """
    Get API Gateway Management API client for posting messages
    """
    endpoint_url = f"https://{domain_name}/{stage}"
    return boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)


def _safe_post(client, connection_id: str, message: dict) -> None:
    """
    Post a message to a WebSocket connection, swallowing errors so the
    handler always returns 200 and never causes a 502 to the client.
    """
    try:
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
    except Exception as e:
        logger.warning(f"post_to_connection failed for {connection_id}: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket messages from clients
    """
    try:
        connection_id = event['requestContext']['connectionId']
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        message_type = body.get('type', 'unknown')
        
        logger.info(f"Received message from {connection_id}: type={message_type}")
        
        # Initialize API Gateway Management client
        global apigateway_management
        apigateway_management = get_apigateway_client(domain_name, stage)
        
        # Handle different message types
        if message_type == 'ping':
            response = {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }
            _safe_post(apigateway_management, connection_id, response)

        elif message_type == 'subscribe':
            topic = body.get('topic', 'default')
            try:
                connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET topic = :topic',
                    ExpressionAttributeValues={':topic': topic}
                )
                logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
            except Exception as db_err:
                logger.error(f"DynamoDB update failed for {connection_id}: {db_err}")

        elif message_type == 'auth':
            response = {
                'type': 'auth_success',
                'message': 'Authentication successful'
            }
            _safe_post(apigateway_management, connection_id, response)

        else:
            logger.warning(f"Unknown message type: {message_type}")
            response = {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }
            _safe_post(apigateway_management, connection_id, response)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed'})
        }

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        # Always return 200 — a 500 here causes API Gateway to send 502 to the client
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processing error', 'error': str(e)})
        }

