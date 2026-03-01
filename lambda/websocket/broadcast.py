"""
WebSocket Broadcast Handler
Broadcasts messages to all connected clients on a specific topic
"""

import json
import boto3
import os
import logging
from typing import Dict, Any, List
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])


def get_apigateway_client(domain_name: str, stage: str):
    """
    Get API Gateway Management API client for posting messages
    """
    endpoint_url = f"https://{domain_name}/{stage}"
    return boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)


def get_connections_by_topic(topic: str) -> List[Dict[str, Any]]:
    """
    Query all connections subscribed to a specific topic
    """
    try:
        response = connections_table.query(
            IndexName='topic-index',
            KeyConditionExpression=Key('topic').eq(topic)
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error querying connections by topic: {str(e)}")
        return []


def broadcast_to_connections(
    connections: List[Dict[str, Any]],
    message: Dict[str, Any],
    domain_name: str,
    stage: str
) -> Dict[str, int]:
    """
    Broadcast message to all connections
    Returns dict with success and failure counts
    """
    apigateway_management = get_apigateway_client(domain_name, stage)
    
    success_count = 0
    failure_count = 0
    stale_connections = []
    
    message_data = json.dumps(message).encode('utf-8')
    
    for connection in connections:
        connection_id = connection['connectionId']
        try:
            apigateway_management.post_to_connection(
                ConnectionId=connection_id,
                Data=message_data
            )
            success_count += 1
            logger.debug(f"Message sent to connection: {connection_id}")
            
        except apigateway_management.exceptions.GoneException:
            # Connection is stale, mark for deletion
            logger.warning(f"Stale connection detected: {connection_id}")
            stale_connections.append(connection_id)
            failure_count += 1
            
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {str(e)}")
            failure_count += 1
    
    # Clean up stale connections
    for connection_id in stale_connections:
        try:
            connections_table.delete_item(
                Key={'connectionId': connection_id}
            )
            logger.info(f"Removed stale connection: {connection_id}")
        except Exception as e:
            logger.error(f"Error removing stale connection {connection_id}: {str(e)}")
    
    return {
        'success': success_count,
        'failure': failure_count,
        'stale': len(stale_connections)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle broadcast requests
    
    Expected event format:
    {
        "topic": "admin-dashboard",
        "message": {
            "type": "update",
            "data": {...}
        },
        "domainName": "xxx.execute-api.region.amazonaws.com",
        "stage": "dev"
    }
    """
    try:
        # Extract parameters
        topic = event.get('topic', 'default')
        message = event.get('message', {})
        domain_name = event.get('domainName')
        stage = event.get('stage', os.environ.get('ENVIRONMENT', 'dev'))
        
        logger.info(f"Broadcasting to topic: {topic}")
        
        # Get all connections for this topic
        connections = get_connections_by_topic(topic)
        
        if not connections:
            logger.info(f"No connections found for topic: {topic}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No connections to broadcast to',
                    'topic': topic,
                    'connectionCount': 0
                })
            }
        
        logger.info(f"Found {len(connections)} connections for topic: {topic}")
        
        # Broadcast message to all connections
        results = broadcast_to_connections(
            connections,
            message,
            domain_name,
            stage
        )
        
        logger.info(
            f"Broadcast complete: {results['success']} success, "
            f"{results['failure']} failure, {results['stale']} stale"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Broadcast complete',
                'topic': topic,
                'connectionCount': len(connections),
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to broadcast message',
                'error': str(e)
            })
        }
