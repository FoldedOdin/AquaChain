#!/usr/bin/env python3
"""
Readings Service Lambda Function
Handles device readings API endpoints
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
readings_table = dynamodb.Table('AquaChain-Readings')

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def create_response(status_code: int, body: Dict[str, Any], cors: bool = True) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        'statusCode': status_code,
        'body': json.dumps(body, default=decimal_default)
    }
    
    if cors:
        response['headers'] = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
            'Content-Type': 'application/json'
        }
    
    return response

def get_latest_reading(device_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest reading for a device"""
    try:
        # Get current month for partition key
        now = datetime.utcnow()
        device_month = f"{device_id}_{now.strftime('%Y-%m')}"
        
        logger.info(f"Querying latest reading for device: {device_id}, month: {device_month}")
        
        # Query the table with device_month partition key, sorted by timestamp descending
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Sort descending (latest first)
            Limit=1
        )
        
        if response['Items']:
            reading = response['Items'][0]
            logger.info(f"Found latest reading: {reading}")
            return reading
        
        # If no readings in current month, try previous month
        prev_month = (now.replace(day=1) - timedelta(days=1))
        prev_device_month = f"{device_id}_{prev_month.strftime('%Y-%m')}"
        
        logger.info(f"No readings in current month, trying previous: {prev_device_month}")
        
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': prev_device_month
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        if response['Items']:
            reading = response['Items'][0]
            logger.info(f"Found reading in previous month: {reading}")
            return reading
        
        logger.warning(f"No readings found for device: {device_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting latest reading for {device_id}: {e}")
        return None

def get_device_history(device_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get reading history for a device"""
    try:
        readings = []
        now = datetime.utcnow()
        
        # Calculate how many months to check
        start_date = now - timedelta(days=days)
        
        # Get readings from current month
        current_month = f"{device_id}_{now.strftime('%Y-%m')}"
        
        logger.info(f"Getting {days} days of history for device: {device_id}")
        
        # Query current month
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month AND #ts >= :start_time',
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            },
            ExpressionAttributeValues={
                ':device_month': current_month,
                ':start_time': start_date.isoformat() + 'Z'
            },
            ScanIndexForward=False,  # Latest first
            Limit=100  # Reasonable limit
        )
        
        readings.extend(response['Items'])
        
        # If we need more data and start_date is in previous month, query previous month too
        if start_date.month != now.month:
            prev_month = start_date.strftime('%Y-%m')
            prev_device_month = f"{device_id}_{prev_month}"
            
            logger.info(f"Also querying previous month: {prev_device_month}")
            
            response = readings_table.query(
                KeyConditionExpression='deviceId_month = :device_month AND #ts >= :start_time',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':device_month': prev_device_month,
                    ':start_time': start_date.isoformat() + 'Z'
                },
                ScanIndexForward=False,
                Limit=100
            )
            
            readings.extend(response['Items'])
        
        # Sort by timestamp descending
        readings.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Found {len(readings)} readings for device {device_id}")
        return readings
        
    except Exception as e:
        logger.error(f"Error getting history for {device_id}: {e}")
        return []

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        logger.info(f"Method: {http_method}, Path: {path}")
        logger.info(f"Path params: {path_parameters}")
        logger.info(f"Query params: {query_parameters}")
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight'})
        
        # Extract device ID from path parameters
        device_id = path_parameters.get('deviceId')
        if not device_id:
            return create_response(400, {
                'error': 'Device ID is required',
                'code': 'MISSING_DEVICE_ID'
            })
        
        # Route based on path
        if path.endswith('/latest'):
            # Get latest reading
            reading = get_latest_reading(device_id)
            
            if reading:
                return create_response(200, {
                    'success': True,
                    'reading': reading,
                    'deviceId': device_id
                })
            else:
                return create_response(404, {
                    'error': f'No readings found for device {device_id}',
                    'code': 'NO_READINGS_FOUND',
                    'deviceId': device_id
                })
        
        elif path.endswith('/history'):
            # Get reading history
            days = int(query_parameters.get('days', 7))
            readings = get_device_history(device_id, days)
            
            return create_response(200, {
                'success': True,
                'readings': readings,
                'deviceId': device_id,
                'days': days,
                'count': len(readings)
            })
        
        else:
            return create_response(404, {
                'error': f'Endpoint not found: {path}',
                'code': 'ENDPOINT_NOT_FOUND'
            })
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return create_response(500, {
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })