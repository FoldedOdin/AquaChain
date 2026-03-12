"""
Pluggable Device Service Lambda
Handles registration and management of pluggable devices with different connection types
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
iot_client = boto3.client('iot')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
PLUGGABLE_DEVICES_TABLE = os.environ.get('PLUGGABLE_DEVICES_TABLE', 'AquaChain-PluggableDevices')

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


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(decimal_to_number(body))
    }


def get_user_id_from_event(event: Dict[str, Any]) -> str:
    """Extract user ID from JWT token in event"""
    try:
        # In production, this would decode the JWT token
        # For now, we'll use a mock user ID from headers
        auth_header = event.get('headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            # Mock: extract user ID from token (in production, decode JWT)
            return 'user-123'  # Replace with actual JWT decoding
        return None
    except Exception as e:
        logger.error(f"Error extracting user ID: {str(e)}")
        return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for pluggable device operations
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        logger.info(f"Pluggable device request: {http_method} {path}")
        
        # Route to appropriate handler
        if http_method == 'POST' and '/register-pluggable' in path:
            return register_pluggable_device(event, context)
        elif http_method == 'POST' and '/validate-pairing' in path:
            return validate_device_pairing(event, context)
        elif http_method == 'GET' and '/pluggable-devices' in path:
            return list_pluggable_devices(event, context)
        elif http_method == 'POST' and '/unpair' in path:
            return unpair_device(event, context)
        elif http_method == 'PUT' and '/pluggable-devices' in path:
            return update_pluggable_device(event, context)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Error in pluggable device service: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Internal server error'})


def register_pluggable_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Register a new pluggable device
    POST /api/v1/devices/register-pluggable
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        # Validate required fields
        required_fields = ['deviceId', 'name', 'type', 'connectionType', 'capabilities']
        for field in required_fields:
            if not body.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        device_id = body['deviceId']
        device_name = body['name']
        device_type = body['type']
        connection_type = body['connectionType']
        capabilities = body['capabilities']
        metadata = body.get('metadata', {})
        connection_config = body.get('connectionConfig', {})
        
        # Validate device type
        valid_types = ['water_quality', 'air_quality', 'soil_moisture', 'weather_station', 'generic_iot']
        if device_type not in valid_types:
            return create_response(400, {'error': f'Invalid device type. Must be one of: {valid_types}'})
        
        # Validate connection type
        valid_connection_types = ['wifi', 'bluetooth', 'qr_code', 'manual', 'auto_discovery']
        if connection_type not in valid_connection_types:
            return create_response(400, {'error': f'Invalid connection type. Must be one of: {valid_connection_types}'})
        
        # Check if device already exists
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        existing_device = pluggable_devices_table.get_item(
            Key={'deviceId': device_id}
        ).get('Item')
        
        if existing_device:
            return create_response(409, {'error': 'Device already registered'})
        
        # Create device record
        timestamp = datetime.utcnow().isoformat() + 'Z'
        device_record = {
            'deviceId': device_id,
            'userId': user_id,
            'name': device_name,
            'type': device_type,
            'connectionType': connection_type,
            'status': 'connected',
            'capabilities': capabilities,
            'metadata': metadata,
            'connectionConfig': connection_config,
            'createdAt': timestamp,
            'lastSeen': timestamp,
            'isShared': False,
            'sharedWith': []
        }
        
        # Save to DynamoDB
        pluggable_devices_table.put_item(Item=device_record)
        
        # Also create entry in main devices table for compatibility
        devices_table = dynamodb.Table(DEVICES_TABLE)
        legacy_device_record = {
            'deviceId': device_id,
            'userId': user_id,
            'deviceName': device_name,
            'location': metadata.get('location', 'Not specified'),
            'waterSourceType': 'pluggable_device',
            'status': 'active',
            'createdAt': timestamp,
            'lastSeen': timestamp,
            'metadata': {
                'deviceType': device_type,
                'connectionType': connection_type,
                'isPluggable': True,
                **metadata
            }
        }
        
        devices_table.put_item(Item=legacy_device_record)
        
        logger.info(f"Pluggable device {device_id} registered successfully for user {user_id}")
        
        return create_response(200, {
            'message': 'Device registered successfully',
            'device': device_record
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error registering pluggable device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to register device'})


def validate_device_pairing(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validate device pairing key for QR code connections
    POST /api/v1/devices/validate-pairing
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        device_id = body.get('deviceId')
        pairing_key = body.get('pairingKey')
        connection_type = body.get('connectionType')
        
        if not all([device_id, pairing_key, connection_type]):
            return create_response(400, {'error': 'Missing required fields'})
        
        # For QR code pairing, validate the pairing key
        if connection_type == 'qr_code':
            # In production, this would validate against a secure pairing key database
            # For now, we'll use a simple validation
            expected_key = f"pair_{device_id}_{datetime.utcnow().strftime('%Y%m%d')}"
            
            # Mock validation - in production, use cryptographic validation
            is_valid = len(pairing_key) >= 8 and pairing_key.isalnum()
            
            return create_response(200, {
                'valid': is_valid,
                'deviceId': device_id,
                'message': 'Pairing key validated' if is_valid else 'Invalid pairing key'
            })
        
        return create_response(400, {'error': 'Unsupported connection type for pairing validation'})
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error validating device pairing: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to validate pairing'})


def list_pluggable_devices(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all pluggable devices for a user
    GET /api/v1/devices/pluggable-devices
    """
    try:
        user_id = get_user_id_from_event(event)
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        
        # Query devices by user ID using GSI
        response = pluggable_devices_table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id},
            ScanIndexForward=False  # Newest first
        )
        
        devices = response.get('Items', [])
        
        return create_response(200, {
            'devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error listing pluggable devices: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to list devices'})


def unpair_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Unpair a pluggable device
    POST /api/v1/devices/{deviceId}/unpair
    """
    try:
        user_id = get_user_id_from_event(event)
        device_id = event.get('pathParameters', {}).get('deviceId')
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        if not device_id:
            return create_response(400, {'error': 'Missing device ID'})
        
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        devices_table = dynamodb.Table(DEVICES_TABLE)
        
        # Check if device exists and belongs to user
        device_response = pluggable_devices_table.get_item(
            Key={'deviceId': device_id}
        )
        
        device = device_response.get('Item')
        if not device:
            return create_response(404, {'error': 'Device not found'})
        
        if device['userId'] != user_id:
            return create_response(403, {'error': 'Device does not belong to user'})
        
        # Delete from both tables
        pluggable_devices_table.delete_item(Key={'deviceId': device_id})
        devices_table.delete_item(Key={'deviceId': device_id})
        
        logger.info(f"Device {device_id} unpaired successfully for user {user_id}")
        
        return create_response(200, {
            'message': 'Device unpaired successfully',
            'deviceId': device_id
        })
        
    except Exception as e:
        logger.error(f"Error unpairing device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to unpair device'})


def update_pluggable_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update pluggable device configuration
    PUT /api/v1/devices/pluggable-devices/{deviceId}
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = get_user_id_from_event(event)
        device_id = event.get('pathParameters', {}).get('deviceId')
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        if not device_id:
            return create_response(400, {'error': 'Missing device ID'})
        
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        
        # Check if device exists and belongs to user
        device_response = pluggable_devices_table.get_item(
            Key={'deviceId': device_id}
        )
        
        device = device_response.get('Item')
        if not device:
            return create_response(404, {'error': 'Device not found'})
        
        if device['userId'] != user_id:
            return create_response(403, {'error': 'Device does not belong to user'})
        
        # Update allowed fields
        update_expression = "SET lastSeen = :lastSeen"
        expression_values = {':lastSeen': datetime.utcnow().isoformat() + 'Z'}
        
        if 'name' in body:
            update_expression += ", #name = :name"
            expression_values[':name'] = body['name']
        
        if 'metadata' in body:
            update_expression += ", metadata = :metadata"
            expression_values[':metadata'] = body['metadata']
        
        if 'status' in body:
            update_expression += ", #status = :status"
            expression_values[':status'] = body['status']
        
        expression_names = {}
        if 'name' in body:
            expression_names['#name'] = 'name'
        if 'status' in body:
            expression_names['#status'] = 'status'
        
        # Perform update
        update_params = {
            'Key': {'deviceId': device_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            update_params['ExpressionAttributeNames'] = expression_names
        
        response = pluggable_devices_table.update_item(**update_params)
        
        updated_device = response['Attributes']
        
        return create_response(200, {
            'message': 'Device updated successfully',
            'device': updated_device
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error updating pluggable device: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to update device'})