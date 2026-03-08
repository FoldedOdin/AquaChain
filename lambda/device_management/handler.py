"""
Device Management Lambda
Handles device registration, pairing, and CRUD operations
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
iot_client = boto3.client('iot')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for device management operations
    Routes requests based on HTTP method and path
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        logger.info(f"Device management request: {http_method} {path}")
        
        # Route to appropriate handler
        if http_method == 'POST' and '/devices/register' in path:
            return register_device(event, context)
        elif http_method == 'GET' and '/devices' in path:
            return list_devices(event, context)
        elif http_method == 'GET' and '/devices/' in path:
            return get_device(event, context)
        elif http_method == 'DELETE' and '/devices/' in path:
            return delete_device(event, context)
        else:
            return create_response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error in device management: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Internal server error'})


def register_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Register a new device and associate with user
    POST /devices/register
    Body: {deviceId, deviceName, location, waterSourceType}
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        device_id = body.get('deviceId')
        user_id = get_user_id_from_event(event)
        
        if not device_id or not user_id:
            return create_response(400, {
                'error': 'Missing deviceId or userId'
            })
        
        # Validate device ID format
        if not device_id.startswith('ESP32-') and not device_id.startswith('AQ-'):
            return create_response(400, {
                'error': 'Invalid device ID format. Must start with ESP32- or AQ-'
            })
        
        # Check if device already registered
        devices_table = dynamodb.Table(DEVICES_TABLE)
        existing = devices_table.get_item(Key={'deviceId': device_id}).get('Item')
        
        if existing and existing.get('userId'):
            return create_response(409, {
                'error': 'Device already registered to another user'
            })
        
        # Create device record
        timestamp = datetime.utcnow().isoformat() + 'Z'
        device_record = {
            'deviceId': device_id,
            'userId': user_id,
            'deviceName': body.get('deviceName', f'Device {device_id}'),
            'location': body.get('location', 'Unknown'),
            'waterSourceType': body.get('waterSourceType', 'household'),
            'status': 'active',
            'createdAt': timestamp,
            'lastSeen': timestamp,
            'metadata': {
                'batteryLevel': 100,
                'signalStrength': 0,
                'firmwareVersion': 'unknown'
            }
        }
        
        devices_table.put_item(Item=device_record)
        
        # Add device to user's device list
        users_table = dynamodb.Table(USERS_TABLE)
        try:
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET devices = list_append(if_not_exists(devices, :empty), :device)',
                ExpressionAttributeValues={
                    ':empty': [],
                    ':device': [device_id]
                }
            )
        except Exception as e:
            logger.warning(f"Could not update user device list: {str(e)}")
        
        logger.info(f"Device {device_id} registered to user {user_id}")
        
        return create_response(200, {
            'message': 'Device registered successfully',
            'device': device_record
        })
        
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to register device'})


def list_devices(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all devices for a user
    GET /devices
    """
    try:
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        # Query devices by userId using GSI
        devices_table = dynamodb.Table(DEVICES_TABLE)
        
        # Scan with filter (not optimal but works for MVP)
        response = devices_table.scan(
            FilterExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        devices = response.get('Items', [])
        
        logger.info(f"Found {len(devices)} devices for user {user_id}")
        
        return create_response(200, {
            'devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to list devices'})


def get_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get device details
    GET /devices/{deviceId}
    """
    try:
        device_id = event.get('pathParameters', {}).get('deviceId')
        user_id = get_user_id_from_event(event)
        
        if not device_id or not user_id:
            return create_response(400, {'error': 'Missing deviceId'})
        
        # Get device
        devices_table = dynamodb.Table(DEVICES_TABLE)
        response = devices_table.get_item(Key={'deviceId': device_id})
        device = response.get('Item')
        
        if not device:
            return create_response(404, {'error': 'Device not found'})
        
        # Verify ownership
        if device.get('userId') != user_id:
            return create_response(403, {'error': 'Access denied'})
        
        return create_response(200, {'device': device})
        
    except Exception as e:
        logger.error(f"Error getting device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to get device'})


def delete_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Delete/unpair a device
    DELETE /devices/{deviceId}
    """
    try:
        device_id = event.get('pathParameters', {}).get('deviceId')
        user_id = get_user_id_from_event(event)
        
        if not device_id or not user_id:
            return create_response(400, {'error': 'Missing deviceId'})
        
        # Verify ownership
        devices_table = dynamodb.Table(DEVICES_TABLE)
        response = devices_table.get_item(Key={'deviceId': device_id})
        device = response.get('Item')
        
        if not device:
            return create_response(404, {'error': 'Device not found'})
        
        if device.get('userId') != user_id:
            return create_response(403, {'error': 'Access denied'})
        
        # Remove user association (don't delete device)
        devices_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET userId = :null, #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':null': None,
                ':status': 'unregistered'
            }
        )
        
        logger.info(f"Device {device_id} unpaired from user {user_id}")
        
        return create_response(200, {
            'message': 'Device unpaired successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to delete device'})


def get_user_id_from_event(event: Dict[str, Any]) -> str:
    """Extract user ID from Cognito authorizer claims"""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        return claims.get('sub', '')
    except Exception:
        return ''


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
