"""
Device Provisioning Lambda
Handles device provisioning hook and user association
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

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Provisioning hook handler
    Called during device provisioning to validate and customize
    """
    try:
        logger.info(f"Provisioning event: {json.dumps(event)}")
        
        # Extract provisioning parameters
        parameters = event.get('parameters', {})
        device_id = parameters.get('DeviceId')
        serial_number = parameters.get('SerialNumber')
        
        if not device_id or not serial_number:
            return {
                'allowProvisioning': False,
                'parameterOverrides': {}
            }
        
        # Validate device ID format (ESP32-XXXXXX)
        if not device_id.startswith('ESP32-'):
            logger.error(f"Invalid device ID format: {device_id}")
            return {
                'allowProvisioning': False,
                'parameterOverrides': {}
            }
        
        # Check if device already exists
        devices_table = dynamodb.Table(DEVICES_TABLE)
        existing_device = devices_table.get_item(
            Key={'deviceId': device_id}
        ).get('Item')
        
        if existing_device:
            logger.warning(f"Device {device_id} already provisioned")
            # Allow re-provisioning but keep existing user association
            return {
                'allowProvisioning': True,
                'parameterOverrides': {
                    'DeviceId': device_id,
                    'SerialNumber': serial_number
                }
            }
        
        # Create device record in DynamoDB
        timestamp = datetime.utcnow().isoformat() + 'Z'
        device_record = {
            'deviceId': device_id,
            'serialNumber': serial_number,
            'status': 'provisioning',
            'provisionedAt': timestamp,
            'lastSeen': timestamp,
            'firmwareVersion': 'unknown',
            'userId': None,  # Will be set when user pairs device
            'metadata': {
                'batteryLevel': 100,
                'signalStrength': 0
            }
        }
        
        devices_table.put_item(Item=device_record)
        logger.info(f"Device {device_id} provisioned successfully")
        
        return {
            'allowProvisioning': True,
            'parameterOverrides': {
                'DeviceId': device_id,
                'SerialNumber': serial_number
            }
        }
        
    except Exception as e:
        logger.error(f"Provisioning error: {str(e)}", exc_info=True)
        return {
            'allowProvisioning': False,
            'parameterOverrides': {}
        }


def pair_device_with_user(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API endpoint to pair a device with a user
    Called from frontend when user scans QR code or enters device ID
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        device_id = body.get('deviceId')
        user_id = body.get('userId')
        device_name = body.get('deviceName', 'My AquaChain Device')
        
        if not device_id or not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing deviceId or userId',
                    'code': 'MISSING_PARAMETERS'
                })
            }
        
        # Verify device exists and is not already paired
        devices_table = dynamodb.Table(DEVICES_TABLE)
        device = devices_table.get_item(
            Key={'deviceId': device_id}
        ).get('Item')
        
        if not device:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Device not found',
                    'code': 'DEVICE_NOT_FOUND'
                })
            }
        
        if device.get('userId') and device['userId'] != user_id:
            return {
                'statusCode': 409,
                'body': json.dumps({
                    'error': 'Device already paired with another user',
                    'code': 'DEVICE_ALREADY_PAIRED'
                })
            }
        
        # Verify user exists
        users_table = dynamodb.Table(USERS_TABLE)
        user = users_table.get_item(
            Key={'userId': user_id}
        ).get('Item')
        
        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                })
            }
        
        # Update device with user association
        timestamp = datetime.utcnow().isoformat() + 'Z'
        devices_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET userId = :userId, deviceName = :deviceName, status = :status, pairedAt = :pairedAt',
            ExpressionAttributeValues={
                ':userId': user_id,
                ':deviceName': device_name,
                ':status': 'active',
                ':pairedAt': timestamp
            }
        )
        
        # Add device to user's device list
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET devices = list_append(if_not_exists(devices, :empty_list), :device)',
            ExpressionAttributeValues={
                ':empty_list': [],
                ':device': [device_id]
            }
        )
        
        # Add device to active Thing Group
        try:
            iot_client.add_thing_to_thing_group(
                thingGroupName=f"aquachain-active-{os.environ.get('ENVIRONMENT', 'dev')}",
                thingName=device_id
            )
        except Exception as e:
            logger.warning(f"Failed to add device to thing group: {str(e)}")
        
        logger.info(f"Device {device_id} paired with user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Device paired successfully',
                'deviceId': device_id,
                'userId': user_id,
                'pairedAt': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Pairing error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            })
        }


def unpair_device(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API endpoint to unpair a device from a user
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        device_id = body.get('deviceId')
        user_id = body.get('userId')
        
        if not device_id or not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing deviceId or userId',
                    'code': 'MISSING_PARAMETERS'
                })
            }
        
        # Verify device belongs to user
        devices_table = dynamodb.Table(DEVICES_TABLE)
        device = devices_table.get_item(
            Key={'deviceId': device_id}
        ).get('Item')
        
        if not device:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Device not found',
                    'code': 'DEVICE_NOT_FOUND'
                })
            }
        
        if device.get('userId') != user_id:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Device does not belong to this user',
                    'code': 'UNAUTHORIZED'
                })
            }
        
        # Remove user association from device
        timestamp = datetime.utcnow().isoformat() + 'Z'
        devices_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET userId = :null, status = :status, unpairedAt = :unpairedAt',
            ExpressionAttributeValues={
                ':null': None,
                ':status': 'provisioning',
                ':unpairedAt': timestamp
            }
        )
        
        # Remove device from user's device list
        users_table = dynamodb.Table(USERS_TABLE)
        user = users_table.get_item(
            Key={'userId': user_id}
        ).get('Item')
        
        if user and 'devices' in user:
            devices = [d for d in user['devices'] if d != device_id]
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET devices = :devices',
                ExpressionAttributeValues={
                    ':devices': devices
                }
            )
        
        logger.info(f"Device {device_id} unpaired from user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Device unpaired successfully',
                'deviceId': device_id,
                'unpairedAt': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Unpairing error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            })
        }
