"""
Device Bridge Service
Bridges existing active devices with the new pluggable device system
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

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
PLUGGABLE_DEVICES_TABLE = os.environ.get('PLUGGABLE_DEVICES_TABLE', 'AquaChain-PluggableDevices')
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings')

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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for device bridge operations
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        logger.info(f"Device bridge request: {http_method} {path}")
        
        if http_method == 'POST' and '/bridge-active-devices' in path:
            return bridge_active_devices(event, context)
        elif http_method == 'GET' and '/bridged-devices' in path:
            return list_bridged_devices(event, context)
        elif http_method == 'POST' and '/sync-device-status' in path:
            return sync_device_status(event, context)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Error in device bridge service: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Internal server error'})


def bridge_active_devices(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Bridge existing active devices to pluggable device system
    POST /api/v1/devices/bridge-active-devices
    """
    try:
        # Get all active devices from the traditional devices table
        devices_table = dynamodb.Table(DEVICES_TABLE)
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        
        # Scan for active devices
        response = devices_table.scan(
            FilterExpression='#status IN (:active, :online)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':active': 'active', ':online': 'online'}
        )
        
        active_devices = response.get('Items', [])
        bridged_count = 0
        
        for device in active_devices:
            device_id = device.get('deviceId')
            if not device_id:
                continue
            
            # Check if already bridged
            existing_pluggable = pluggable_devices_table.get_item(
                Key={'deviceId': device_id}
            ).get('Item')
            
            if existing_pluggable:
                logger.info(f"Device {device_id} already bridged, skipping")
                continue
            
            # Determine device type based on device ID or metadata
            device_type = determine_device_type(device)
            
            # Get device capabilities based on type
            capabilities = get_device_capabilities(device_type, device)
            
            # Get latest readings to determine connection status
            connection_status = get_device_connection_status(device_id)
            
            # Create pluggable device record
            timestamp = datetime.utcnow().isoformat() + 'Z'
            pluggable_device = {
                'deviceId': device_id,
                'userId': device.get('userId', 'system'),
                'name': device.get('deviceName', f'Device {device_id}'),
                'type': device_type,
                'connectionType': 'auto_discovery',  # Existing devices are auto-discovered
                'status': connection_status,
                'capabilities': capabilities,
                'metadata': {
                    'location': device.get('location', 'Not specified'),
                    'manufacturer': 'AquaChain',
                    'model': determine_device_model(device_id),
                    'firmwareVersion': device.get('metadata', {}).get('firmwareVersion', 'unknown'),
                    'batteryLevel': device.get('metadata', {}).get('batteryLevel', 100),
                    'signalStrength': device.get('metadata', {}).get('signalStrength', -50),
                    'isBridged': True,
                    'originalDeviceRecord': True
                },
                'connectionConfig': {
                    'type': 'auto_discovery',
                    'parameters': {
                        'bridgedFromTraditional': True,
                        'originalDeviceId': device_id
                    }
                },
                'createdAt': device.get('createdAt', timestamp),
                'lastSeen': device.get('lastSeen', timestamp),
                'isShared': False,
                'sharedWith': []
            }
            
            # Store in pluggable devices table
            pluggable_devices_table.put_item(Item=pluggable_device)
            bridged_count += 1
            
            logger.info(f"Bridged device {device_id} to pluggable system")
        
        return create_response(200, {
            'message': f'Successfully bridged {bridged_count} active devices',
            'bridgedCount': bridged_count,
            'totalActiveDevices': len(active_devices)
        })
        
    except Exception as e:
        logger.error(f"Error bridging active devices: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to bridge active devices'})


def determine_device_type(device: Dict[str, Any]) -> str:
    """Determine device type based on device metadata"""
    device_id = device.get('deviceId', '')
    
    # Check device ID patterns
    if device_id.startswith('ESP32-'):
        return 'water_quality'
    elif device_id.startswith('DEV-'):
        return 'water_quality'
    elif device_id.startswith('AIR-'):
        return 'air_quality'
    elif device_id.startswith('SOIL-'):
        return 'soil_moisture'
    elif device_id.startswith('WEATHER-'):
        return 'weather_station'
    
    # Default to water quality for AquaChain devices
    return 'water_quality'


def determine_device_model(device_id: str) -> str:
    """Determine device model based on device ID"""
    if device_id.startswith('ESP32-'):
        return 'AquaChain-ESP32-WQ'
    elif device_id.startswith('DEV-'):
        return 'AquaChain-Dev-Kit'
    else:
        return 'AquaChain-Generic'


def get_device_capabilities(device_type: str, device: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device capabilities based on type"""
    
    if device_type == 'water_quality':
        return [
            {
                'id': 'ph',
                'name': 'pH Level',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'pH',
                'range': {'min': 0, 'max': 14},
                'readonly': True
            },
            {
                'id': 'turbidity',
                'name': 'Turbidity',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'NTU',
                'range': {'min': 0, 'max': 1000},
                'readonly': True
            },
            {
                'id': 'tds',
                'name': 'Total Dissolved Solids',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'ppm',
                'range': {'min': 0, 'max': 2000},
                'readonly': True
            },
            {
                'id': 'temperature',
                'name': 'Temperature',
                'type': 'sensor',
                'dataType': 'number',
                'unit': '°C',
                'range': {'min': -10, 'max': 50},
                'readonly': True
            },
            {
                'id': 'wqi',
                'name': 'Water Quality Index',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'WQI',
                'range': {'min': 0, 'max': 100},
                'readonly': True
            }
        ]
    
    elif device_type == 'air_quality':
        return [
            {
                'id': 'pm25',
                'name': 'PM2.5',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'μg/m³',
                'range': {'min': 0, 'max': 500},
                'readonly': True
            },
            {
                'id': 'co2',
                'name': 'CO2',
                'type': 'sensor',
                'dataType': 'number',
                'unit': 'ppm',
                'range': {'min': 0, 'max': 5000},
                'readonly': True
            }
        ]
    
    # Default capabilities for unknown types
    return [
        {
            'id': 'generic_sensor',
            'name': 'Generic Sensor',
            'type': 'sensor',
            'dataType': 'number',
            'readonly': True
        }
    ]


def get_device_connection_status(device_id: str) -> str:
    """Get device connection status based on recent readings"""
    try:
        readings_table = dynamodb.Table(READINGS_TABLE)
        
        # Get the most recent reading for this device
        # Use the partition key format from the data processing lambda
        current_month = datetime.utcnow().strftime('%Y-%m')
        partition_key = f"{device_id}_{current_month}"
        
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :pk',
            ExpressionAttributeValues={':pk': partition_key},
            ScanIndexForward=False,  # Get newest first
            Limit=1
        )
        
        if response.get('Items'):
            latest_reading = response['Items'][0]
            last_seen = latest_reading.get('timestamp')
            
            if last_seen:
                # Parse timestamp and check if it's recent (within last 10 minutes)
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                now = datetime.utcnow().replace(tzinfo=last_seen_dt.tzinfo)
                time_diff = (now - last_seen_dt).total_seconds()
                
                if time_diff < 600:  # 10 minutes
                    return 'active'
                elif time_diff < 3600:  # 1 hour
                    return 'connected'
                else:
                    return 'offline'
        
        return 'offline'
        
    except Exception as e:
        logger.warning(f"Error checking device status for {device_id}: {str(e)}")
        return 'offline'


def list_bridged_devices(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all bridged devices
    GET /api/v1/devices/bridged-devices
    """
    try:
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        
        # Scan for bridged devices
        response = pluggable_devices_table.scan(
            FilterExpression='#metadata.#isBridged = :true',
            ExpressionAttributeNames={
                '#metadata': 'metadata',
                '#isBridged': 'isBridged'
            },
            ExpressionAttributeValues={':true': True}
        )
        
        bridged_devices = response.get('Items', [])
        
        return create_response(200, {
            'devices': bridged_devices,
            'count': len(bridged_devices)
        })
        
    except Exception as e:
        logger.error(f"Error listing bridged devices: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to list bridged devices'})


def sync_device_status(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Sync device status between traditional and pluggable systems
    POST /api/v1/devices/sync-device-status
    """
    try:
        body = json.loads(event.get('body', '{}'))
        device_id = body.get('deviceId')
        
        if not device_id:
            return create_response(400, {'error': 'Missing deviceId'})
        
        # Get current status from readings
        current_status = get_device_connection_status(device_id)
        
        # Update both tables
        devices_table = dynamodb.Table(DEVICES_TABLE)
        pluggable_devices_table = dynamodb.Table(PLUGGABLE_DEVICES_TABLE)
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Update traditional devices table
        try:
            devices_table.update_item(
                Key={'deviceId': device_id},
                UpdateExpression='SET #status = :status, lastSeen = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': current_status,
                    ':timestamp': timestamp
                }
            )
        except Exception as e:
            logger.warning(f"Could not update traditional device {device_id}: {str(e)}")
        
        # Update pluggable devices table
        try:
            pluggable_devices_table.update_item(
                Key={'deviceId': device_id},
                UpdateExpression='SET #status = :status, lastSeen = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': current_status,
                    ':timestamp': timestamp
                }
            )
        except Exception as e:
            logger.warning(f"Could not update pluggable device {device_id}: {str(e)}")
        
        return create_response(200, {
            'message': 'Device status synchronized',
            'deviceId': device_id,
            'status': current_status,
            'timestamp': timestamp
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error syncing device status: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Failed to sync device status'})