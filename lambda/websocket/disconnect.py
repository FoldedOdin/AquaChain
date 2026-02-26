"""
WebSocket Disconnect Handler
Handles WebSocket disconnections and removes connection info from DynamoDB
"""

import json
import boto3
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection requests
    """
    try:
        connection_id = event['requestContext']['connectionId']
        
        logger.info(f"WebSocket disconnection: {connection_id}")
        
        # Remove connection from DynamoDB
        connections_table.delete_item(
            Key={
                'connectionId': connection_id
            }
        )
        
        logger.info(f"Connection {connection_id} removed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Disconnected successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling disconnection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to disconnect',
                'error': str(e)
            })
        }

