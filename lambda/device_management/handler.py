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
from decimal import Decimal

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


def decimal_to_number(obj):
    """Convert Decimal objects to int or float for JSON serialization"""
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj


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
        path_params = event.get('pathParameters', {})
        
        if http_method == 'POST' and '/devices/register' in path:
            return register_device(event, context)
        elif http_method == 'GET' and path_params and path_params.get('deviceId'):
            return get_device(event, context)
        elif http_method == 'GET' and '/devices' in path:
            return list_devices(event, context)
        elif http_method == 'DELETE' and path_params and path_params.get('deviceId'):
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
        device_id = body.get('deviceId') or body.get('device_id')
        user_id = get_user_id_from_event(event)
        
        if not device_id or not user_id:
            return create_response(400, {
                'error': 'Missing deviceId or userId'
            })
        
        # Validate device ID format (supports multiple formats)
        # Formats: AQ-001, ESP-001, ESP32-XXX, AquaChain-Device-001
        import re
        if not re.match(r'^(AQ-[0-9]{3}|ESP-[0-9]{3}|ESP32-.+|AquaChain-Device-[0-9]{3})$', device_id):
            return create_response(400, {
                'error': 'Invalid device ID format. Must be AQ-XXX, ESP-XXX, ESP32-XXX, or AquaChain-Device-XXX'
            })
        
        # Check if device exists in IoT Core
        try:
            iot_client.describe_thing(thingName=device_id)
        except iot_client.exceptions.ResourceNotFoundException:
            return create_response(404, {
                'error': f'Device {device_id} not found in IoT registry. Please provision device first.'
            })
        except Exception as e:
            logger.warning(f"Could not verify device in IoT Core: {str(e)}")
        
        # Check if device already registered (prevent hijacking)
        devices_table = dynamodb.Table(DEVICES_TABLE)
        existing = devices_table.get_item(Key={'deviceId': device_id}).get('Item')
        
        if existing:
            existing_owner = existing.get('userId')
            if existing_owner and existing_owner != user_id:
                return create_response(409, {
                    'error': 'Device already registered to another user'
                })
            elif existing_owner == user_id:
                return create_response(409, {
                    'error': 'Device already registered to your account'
                })
        
        # Create device record (using camelCase for DynamoDB - matches table schema)
        timestamp = datetime.utcnow().isoformat() + 'Z'
        device_record = {
            'deviceId': device_id,
            'userId': user_id,
            'deviceName': body.get('deviceName') or body.get('name', f'Device {device_id}'),
            'location': body.get('location', 'Unknown'),
            'waterSourceType': body.get('waterSourceType') or body.get('water_source_type', 'household'),
            'status': 'active',
            'connectionStatus': 'unknown',  # Will be updated when device sends data
            'createdAt': timestamp,
            'lastSeen': timestamp,
            'statusUpdatedAt': timestamp,
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
        
        # Return camelCase for frontend (already in camelCase)
        response_device = {
            'deviceId': device_id,
            'userId': user_id,
            'deviceName': device_record['deviceName'],
            'location': device_record['location'],
            'waterSourceType': device_record['waterSourceType'],
            'status': device_record['status'],
            'connectionStatus': device_record['connectionStatus'],
            'createdAt': device_record['createdAt'],
            'lastSeen': device_record['lastSeen']
        }
        
        return create_response(200, {
            'success': True,
            'message': 'Device registered successfully',
            'data': response_device
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
        
        # Query devices by user_id using GSI
        devices_table = dynamodb.Table(DEVICES_TABLE)
        
        # Use GSI for efficient query
        try:
            response = devices_table.query(
                IndexName='UserIndex',
                KeyConditionExpression='userId = :userId',
                ExpressionAttributeValues={':userId': user_id}
            )
        except Exception:
            # Fallback to scan if GSI not available
            response = devices_table.scan(
                FilterExpression='userId = :userId',
                ExpressionAttributeValues={':userId': user_id}
            )
        
        devices_raw = response.get('Items', [])
        
        # Data is already in camelCase from DynamoDB, but convert Decimals
        devices = decimal_to_number(devices_raw)
        
        logger.info(f"Found {len(devices)} devices for user {user_id}")
        
        return create_response(200, {
            'success': True,
            'data': devices,
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
        
        # Data is already in camelCase from DynamoDB, but convert Decimals
        device = decimal_to_number(device)
        
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
            UpdateExpression='REMOVE userId SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
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
