"""
WebSocket Connect Handler
Handles new WebSocket connections and stores connection info in DynamoDB
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket connection requests
    """
    try:
        connection_id = event['requestContext']['connectionId']
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        topic = query_params.get('topic', 'default')
        
        # Extract user info from authorizer context if available
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        user_id = authorizer_context.get('userId', 'anonymous')
        
        logger.info(f"New WebSocket connection: {connection_id}, topic: {topic}, user: {user_id}")
        
        # Calculate TTL (24 hours from now)
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        
        # Store connection in DynamoDB
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'topic': topic,
                'userId': user_id,
                'domainName': domain_name,
                'stage': stage,
                'connectedAt': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
        )
        
        logger.info(f"Connection {connection_id} stored successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Connected successfully',
                'connectionId': connection_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling connection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to connect',
                'error': str(e)
            })
        }

