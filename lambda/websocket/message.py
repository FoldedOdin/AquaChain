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
            # Respond to ping with pong
            response = {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }
            apigateway_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )
            
        elif message_type == 'subscribe':
            # Update subscription topic
            topic = body.get('topic', 'default')
            connections_table.update_item(
                Key={'connectionId': connection_id},
                UpdateExpression='SET topic = :topic',
                ExpressionAttributeValues={':topic': topic}
            )
            logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
            
        elif message_type == 'auth':
            # Handle authentication
            token = body.get('token')
            # TODO: Validate token with Cognito
            # For now, just acknowledge
            response = {
                'type': 'auth_success',
                'message': 'Authentication successful'
            }
            apigateway_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )
            
        else:
            # Unknown message type
            logger.warning(f"Unknown message type: {message_type}")
            response = {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }
            apigateway_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(response).encode('utf-8')
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed'})
        }
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to process message',
                'error': str(e)
            })
        }

