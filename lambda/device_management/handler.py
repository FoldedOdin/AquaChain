"""
Device management service using optimized GSI queries (Phase 4)
Demonstrates efficient DynamoDB query patterns with pagination
"""

import json
import boto3
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import uuid
from decimal import Decimal

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import error handling
from errors import ValidationError, ResourceNotFoundError, DatabaseError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Import optimized queries
from dynamodb_queries import (
    query_devices_by_user,
    query_devices_by_status
)

# Import cache service
from cache_service import get_cache_service

# Import audit logging
from audit_logger import audit_logger

logger = get_logger(__name__, service='device-management')


class DeviceManagementService:
    """
    Service for managing devices with optimized GSI queries
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.devices_table = self.dynamodb.Table('aquachain-devices')
        self.cache = get_cache_service()
    
    def list_user_devices(self, user_id: str, limit: int = 100, 
                         last_key: Optional[Dict] = None) -> Dict:
        """
        List all devices for a user using user_id-created_at-index GSI
        Implements pagination for efficient data retrieval
        """
        try:
            result = query_devices_by_user(
                user_id=user_id,
                limit=limit,
                last_key=last_key,
                table_name='aquachain-devices'
            )
            
            logger.info(f"Listed {len(result['items'])} devices for user {user_id}",
                user_id=user_id,
                item_count=len(result['items']),
                duration_ms=result.get('duration_ms')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing user devices: {e}", user_id=user_id)
            raise DatabaseError("Failed to list devices", details={'user_id': user_id})
    
    def list_devices_by_status(self, status: str, limit: int = 100,
                              last_key: Optional[Dict] = None) -> Dict:
        """
        List devices by status using status-last_seen-index GSI
        Useful for monitoring active/inactive devices
        """
        try:
            # Validate status
            valid_statuses = ['active', 'inactive', 'maintenance', 'offline']
            if status not in valid_statuses:
                raise ValidationError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                    details={'status': status}
                )
            
            result = query_devices_by_status(
                status=status,
                limit=limit,
                last_key=last_key,
                table_name='aquachain-devices'
            )
            
            logger.info(f"Listed {len(result['items'])} devices with status {status}",
                status=status,
                item_count=len(result['items']),
                duration_ms=result.get('duration_ms')
            )
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error listing devices by status: {e}", status=status)
            raise DatabaseError("Failed to list devices", details={'status': status})
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """
        Get device by ID (primary key lookup) with caching
        """
        cache_key = f"device:{device_id}"
        
        try:
            # Try cache first
            cached_device = self.cache.get(cache_key)
            if cached_device:
                logger.info(f"Device found in cache: {device_id}", 
                           device_id=device_id, cache_hit=True)
                return cached_device
            
            # Cache miss - fetch from DynamoDB
            response = self.devices_table.get_item(Key={'device_id': device_id})
            device = response.get('Item')
            
            if device:
                # Cache for 5 minutes
                self.cache.set(cache_key, device, ttl=300)
                logger.info(f"Device found: {device_id}", 
                           device_id=device_id, cache_hit=False)
            else:
                logger.info(f"Device not found: {device_id}", device_id=device_id)
            
            return device
            
        except Exception as e:
            logger.error(f"Error getting device: {e}", device_id=device_id)
            raise DatabaseError("Failed to get device", details={'device_id': device_id})
    
    def update_device_status(self, device_id: str, status: str) -> Dict:
        """
        Update device status and last_seen timestamp with cache invalidation
        """
        try:
            # Validate status
            valid_statuses = ['active', 'inactive', 'maintenance', 'offline']
            if status not in valid_statuses:
                raise ValidationError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                    details={'status': status}
                )
            
            # Update device
            response = self.devices_table.update_item(
                Key={'device_id': device_id},
                UpdateExpression='SET #status = :status, last_seen = :last_seen',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':last_seen': datetime.utcnow().isoformat()
                },
                ReturnValues='ALL_NEW'
            )
            
            # Invalidate cache for this device
            cache_key = f"device:{device_id}"
            self.cache.delete(cache_key)
            
            logger.info(f"Device status updated: {device_id}",
                device_id=device_id,
                status=status,
                cache_invalidated=True
            )
            
            return response['Attributes']
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating device status: {e}",
                device_id=device_id,
                status=status
            )
            raise DatabaseError("Failed to update device", details={
                'device_id': device_id,
                'status': status
            })


def create_demo_device(user_id: str, request_data: Dict) -> Dict:
    """Create demo device data structure"""
    now = datetime.utcnow()
    device_id = request_data.get('device_id') or f"demo_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"
    
    return {
        'device_id': device_id,
        'user_id': user_id,
        'name': request_data.get('name', 'Demo Water Monitor'),
        'location': request_data.get('location', 'Kitchen Sink - Demo Location'),
        'status': 'active',
        'type': 'ESP32-WQ-Monitor-Demo',
        'installation_date': now.isoformat(),
        'last_reading': now.isoformat(),
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'last_seen': now.isoformat(),
        'metadata': {
            'isDemo': True,
            'description': 'Demonstration device with simulated water quality data',
            'firmware_version': 'demo-v1.0.0',
            'hardware_version': 'demo-hw-v1.0'
        },
        'settings': {
            'reading_interval': 300,  # 5 minutes
            'alert_thresholds': {
                'pH_min': Decimal('6.5'),
                'pH_max': Decimal('8.5'),
                'turbidity_max': Decimal('5.0'),
                'tds_max': Decimal('500'),
                'temperature_min': Decimal('15'),
                'temperature_max': Decimal('25')
            }
        },
        'current_reading': {
            'pH': Decimal(str(request_data.get('readings', {}).get('pH', 7.2))),
            'turbidity': Decimal(str(request_data.get('readings', {}).get('turbidity', 2.1))),
            'tds': Decimal(str(request_data.get('readings', {}).get('tds', 145))),
            'temperature': Decimal(str(request_data.get('readings', {}).get('temperature', 22.5))),
            'timestamp': now.isoformat()
        }
    }


def save_demo_device(device: Dict) -> None:
    """Save demo device to DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        devices_table = dynamodb.Table('aquachain-devices')
        devices_table.put_item(Item=device)
        logger.info(f"Demo device saved: {device['device_id']}")
    except Exception as e:
        logger.error(f"Error saving demo device: {str(e)}")
        raise DatabaseError("Failed to save demo device", details={'device_id': device['device_id']})


def _get_request_context(event: Dict) -> Dict:
    """Extract request context for audit logging"""
    return {
        'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
        'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
        'source': 'api'
    }

@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for device management operations
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    device_service = DeviceManagementService(region)
    request_context = _get_request_context(event)
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    query_params = event.get('queryStringParameters', {}) or {}
    path_params = event.get('pathParameters', {}) or {}
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    
    if http_method == 'GET' and '/devices/by-user' in path:
        # List devices by user using GSI
        user_id = query_params.get('userId')
        limit = int(query_params.get('limit', 100))
        last_key_encoded = query_params.get('lastKey')
        
        if not user_id:
            raise ValidationError('userId parameter required')
        
        # Decode last_key if provided
        last_key = None
        if last_key_encoded:
            try:
                last_key = json.loads(base64.b64decode(last_key_encoded))
            except Exception as e:
                raise ValidationError('Invalid lastKey parameter')
        
        result = device_service.list_user_devices(
            user_id=user_id,
            limit=limit,
            last_key=last_key
        )
        
        # Encode last_key for response
        if result.get('last_key'):
            result['last_key'] = base64.b64encode(
                json.dumps(result['last_key']).encode()
            ).decode()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    elif http_method == 'GET' and '/devices/by-status' in path:
        # List devices by status using GSI
        status = query_params.get('status')
        limit = int(query_params.get('limit', 100))
        last_key_encoded = query_params.get('lastKey')
        
        if not status:
            raise ValidationError('status parameter required')
        
        # Decode last_key if provided
        last_key = None
        if last_key_encoded:
            try:
                last_key = json.loads(base64.b64decode(last_key_encoded))
            except Exception as e:
                raise ValidationError('Invalid lastKey parameter')
        
        result = device_service.list_devices_by_status(
            status=status,
            limit=limit,
            last_key=last_key
        )
        
        # Encode last_key for response
        if result.get('last_key'):
            result['last_key'] = base64.b64encode(
                json.dumps(result['last_key']).encode()
            ).decode()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    elif http_method == 'GET' and '/devices/' in path:
        # Get device by ID
        device_id = path_params.get('deviceId')
        
        if not device_id:
            raise ValidationError('deviceId parameter required')
        
        device = device_service.get_device(device_id)
        
        if not device:
            raise ResourceNotFoundError('Device not found', details={'device_id': device_id})
        
        # Log data access
        audit_logger.log_data_access(
            user_id=event.get('userContext', {}).get('userId', 'system'),
            resource_type='DEVICE',
            resource_id=device_id,
            operation='GET',
            request_context=request_context
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(device)
        }
    
    elif http_method == 'PUT' and '/devices/' in path and '/status' in path:
        # Update device status
        device_id = path_params.get('deviceId')
        status = body.get('status')
        
        if not device_id:
            raise ValidationError('deviceId parameter required')
        if not status:
            raise ValidationError('status field required in body')
        
        # Get current device for audit log
        current_device = device_service.get_device(device_id)
        previous_status = current_device.get('status') if current_device else None
        
        updated_device = device_service.update_device_status(device_id, status)
        
        # Log data modification
        audit_logger.log_data_modification(
            user_id=event.get('userContext', {}).get('userId', 'system'),
            resource_type='DEVICE',
            resource_id=device_id,
            modification_type='UPDATE',
            previous_values={'status': previous_status},
            new_values={'status': status},
            request_context=request_context
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(updated_device)
        }
    
    elif http_method == 'POST' and '/devices/demo' in path:
        # Add demo device
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            raise ValidationError('User ID not found in request context')
        
        # Create demo device
        demo_device = create_demo_device(user_id, body)
        
        # Save to DynamoDB
        save_demo_device(demo_device)
        
        # Log device creation
        audit_logger.log_data_modification(
            user_id=user_id,
            resource_type='DEVICE',
            resource_id=demo_device['device_id'],
            modification_type='CREATE',
            previous_values={},
            new_values=demo_device,
            request_context=request_context
        )
        
        logger.info(f"Demo device created: {demo_device['device_id']}", 
                   device_id=demo_device['device_id'], user_id=user_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'device': demo_device,
                'message': 'Demo device added successfully'
            })
        }
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')
