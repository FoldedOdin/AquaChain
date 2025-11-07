"""
Get Devices Lambda Handler
Retrieves all devices for a user
"""

import json
import os
import boto3
from typing import Dict, Any
import logging
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get all devices for a user
    """
    try:
        # Get user ID from authorizer context
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Unauthorized - User ID not found'
                })
            }
        
        # Query devices by user_id
        devices_table = dynamodb.Table(DEVICES_TABLE)
        
        # Use GSI if available, otherwise scan with filter
        try:
            response = devices_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            devices = response.get('Items', [])
        except Exception as e:
            logger.warning(f'GSI query failed, falling back to scan: {str(e)}')
            # Fallback to scan if GSI doesn't exist
            response = devices_table.scan(
                FilterExpression=Key('user_id').eq(user_id)
            )
            devices = response.get('Items', [])
        
        logger.info(f'Retrieved {len(devices)} devices for user {user_id}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'devices': devices,
                'count': len(devices)
            })
        }
        
    except Exception as e:
        logger.error(f'Error retrieving devices: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': str(e) if os.environ.get('DEBUG') else 'Failed to retrieve devices'
            })
        }
