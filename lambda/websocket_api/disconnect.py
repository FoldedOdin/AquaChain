"""
WebSocket Disconnect Handler
Removes connection record from DynamoDB on client disconnect.
"""

import boto3
import os
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'AquaChain-WebSocketConnections-dev'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        connection_id = event['requestContext']['connectionId']
        logger.info(f"$disconnect: connectionId={connection_id}")

        try:
            connections_table.delete_item(Key={'connectionId': connection_id})
            logger.info(f"Connection {connection_id} removed")
        except Exception as db_err:
            logger.warning(f"Failed to remove connection {connection_id}: {db_err}")

        return {'statusCode': 200}

    except Exception as e:
        logger.error(f"Error in $disconnect handler: {e}", exc_info=True)
        return {'statusCode': 200}
