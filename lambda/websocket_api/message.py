"""
WebSocket Message Handler
Handles incoming WebSocket messages from clients.
Route selection expression is $request.body.action, so clients send
{ "action": "ping" } etc. We also accept the legacy "type" field.
"""

import json
import boto3
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'AquaChain-WebSocketConnections-dev'))


def _get_apigw_client(domain_name: str, stage: str):
    return boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f"https://{domain_name}/{stage}"
    )


def _safe_post(client, connection_id: str, message: dict) -> None:
    try:
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
    except Exception as e:
        logger.warning(f"post_to_connection failed for {connection_id}: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        connection_id = event['requestContext']['connectionId']
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']

        body = json.loads(event.get('body') or '{}')

        # Route selection expression uses 'action'; legacy clients may use 'type'
        action = body.get('action') or body.get('type', 'unknown')

        logger.info(f"Message from {connection_id}: action={action}")

        client = _get_apigw_client(domain_name, stage)

        if action == 'ping':
            _safe_post(client, connection_id, {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            })
            # Keep lastPing fresh
            try:
                connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET lastPing = :ts',
                    ExpressionAttributeValues={':ts': datetime.utcnow().isoformat()}
                )
            except Exception:
                pass  # Non-fatal

        elif action == 'subscribe':
            topic = body.get('topic') or body.get('subscriptionType', 'consumer-updates')
            try:
                connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET topic = :topic',
                    ExpressionAttributeValues={':topic': topic}
                )
                logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
            except Exception as db_err:
                logger.error(f"DynamoDB update failed for {connection_id}: {db_err}")

        elif action == 'auth':
            _safe_post(client, connection_id, {
                'type': 'auth_success',
                'message': 'Authentication successful'
            })

        else:
            logger.warning(f"Unknown action '{action}' from {connection_id}")

        return {'statusCode': 200}

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        # Always return 200 — a non-200 causes API Gateway to send 502 to the client
        return {'statusCode': 200}
