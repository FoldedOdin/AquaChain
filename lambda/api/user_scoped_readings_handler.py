"""
User-Scoped Readings API Handler
Enforces user-level data isolation for all reading queries
"""

import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings-dev')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices-dev')

# DynamoDB tables
readings_table = dynamodb.Table(READINGS_TABLE)
devices_table = dynamodb.Table(DEVICES_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def extract_user_from_token(event: Dict[str, Any]) -> str:
    """
    Extract authenticated user ID from Cognito JWT token
    
    Returns:
        User ID (sub claim from JWT)
    
    Raises:
        ValueError: If user not authenticated
    """
    try:
        # API Gateway with Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims['sub']
        
        print(f"✅ Authenticated user: {user_id}")
        return user_id
        
    except KeyError:
        raise ValueError("Missing authentication token")


def verify_device_ownership(device_id: str, user_id: str) -> bool:
    """
    Verify that the device belongs to the authenticated user
    
    Returns:
        True if user owns device, False otherwise
    """
    try:
        response = devices_table.get_item(Key={'device_id': device_id})
        
        if 'Item' not in response:
            return False
        
        device = response['Item']
        return device.get('user_id') == user_id
        
    except ClientError as e:
        print(f"❌ Error verifying device ownership: {e}")
        return False


def get_user_devices(user_id: str) -> List[str]:
    """Get list of device IDs owned by user"""
    try:
        response = devices_table.query(
            IndexName='user_id-created_at-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        devices = response.get('Items', [])
        return [device['device_id'] for device in devices]
        
    except ClientError as e:
        print(f"❌ Error getting user devices: {e}")
        return []


def query_readings_by_user_and_device(user_id: str, device_id: str, 
                                      start_time: str, end_time: str,
                                      limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query readings with user-level isolation
    
    This ensures users can ONLY access their own device data
    """
    # First verify ownership
    if not verify_device_ownership(device_id, user_id):
        raise PermissionError(f"Access denied: Device {device_id} does not belong to user {user_id}")
    
    # Build partition key with user context
    start_month = start_time[:7]  # YYYY-MM
    end_month = end_time[:7]
    
    all_readings = []
    
    # Query each month in the range
    current_month = start_month
    while current_month <= end_month:
        partition_key = f"{user_id}#{device_id}#{current_month}"
        
        try:
            response = readings_table.query(
                KeyConditionExpression=Key('deviceId_month').eq(partition_key) & 
                                      Key('timestamp').between(start_time, end_time),
                Limit=limit
            )
            
            all_readings.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response and len(all_readings) < limit:
                response = readings_table.query(
                    KeyConditionExpression=Key('deviceId_month').eq(partition_key) & 
                                          Key('timestamp').between(start_time, end_time),
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    Limit=limit - len(all_readings)
                )
                all_readings.extend(response.get('Items', []))
            
        except ClientError as e:
            print(f"❌ Error querying readings for {current_month}: {e}")
        
        # Move to next month
        year, month = map(int, current_month.split('-'))
        if month == 12:
            current_month = f"{year + 1}-01"
        else:
            current_month = f"{year}-{month + 1:02d}"
    
    # Sort by timestamp and limit
    all_readings.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_readings[:limit]


def query_all_user_readings(user_id: str, start_time: str, end_time: str,
                            limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query readings across all user's devices
    
    Enforces user-level data isolation
    """
    # Get all user's devices
    device_ids = get_user_devices(user_id)
    
    if not device_ids:
        return []
    
    all_readings = []
    
    # Query readings for each device
    for device_id in device_ids:
        try:
            readings = query_readings_by_user_and_device(
                user_id=user_id,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            all_readings.extend(readings)
        except PermissionError:
            # Skip devices user doesn't own (shouldn't happen)
            continue
    
    # Sort and limit
    all_readings.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_readings[:limit]


def get_latest_reading(user_id: str, device_id: str) -> Dict[str, Any]:
    """Get most recent reading for a device with ownership check"""
    if not verify_device_ownership(device_id, user_id):
        raise PermissionError(f"Access denied: Device {device_id} does not belong to user {user_id}")
    
    # Query last 7 days
    end_time = datetime.utcnow().isoformat()
    start_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    readings = query_readings_by_user_and_device(
        user_id=user_id,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=1
    )
    
    if not readings:
        return None
    
    return readings[0]


def lambda_handler(event, context):
    """
    API Gateway handler with user-scoped data access
    
    Supported operations:
    - GET /readings?device_id={id}&start={iso}&end={iso}
    - GET /readings/latest?device_id={id}
    - GET /readings/all?start={iso}&end={iso}
    """
    print(f"📥 Received event: {json.dumps(event)}")
    
    try:
        # 1️⃣ CRITICAL: Extract and validate authenticated user
        auth_user_id = extract_user_from_token(event)
        
        # 2️⃣ Parse request
        http_method = event['httpMethod']
        path = event['path']
        query_params = event.get('queryStringParameters') or {}
        
        # 3️⃣ Route to appropriate handler
        if path == '/readings' and http_method == 'GET':
            # Get readings for specific device
            device_id = query_params.get('device_id')
            start_time = query_params.get('start')
            end_time = query_params.get('end')
            limit = int(query_params.get('limit', 100))
            
            if not device_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'device_id is required'})
                }
            
            if not start_time or not end_time:
                # Default to last 24 hours
                end_time = datetime.utcnow().isoformat()
                start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            # ✅ User-scoped query with ownership verification
            readings = query_readings_by_user_and_device(
                user_id=auth_user_id,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'user_id': auth_user_id,
                    'device_id': device_id,
                    'count': len(readings),
                    'readings': readings
                }, cls=DecimalEncoder)
            }
        
        elif path == '/readings/latest' and http_method == 'GET':
            # Get latest reading for device
            device_id = query_params.get('device_id')
            
            if not device_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'device_id is required'})
                }
            
            # ✅ User-scoped query with ownership verification
            reading = get_latest_reading(auth_user_id, device_id)
            
            if not reading:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'No readings found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'user_id': auth_user_id,
                    'device_id': device_id,
                    'reading': reading
                }, cls=DecimalEncoder)
            }
        
        elif path == '/readings/all' and http_method == 'GET':
            # Get readings across all user's devices
            start_time = query_params.get('start')
            end_time = query_params.get('end')
            limit = int(query_params.get('limit', 100))
            
            if not start_time or not end_time:
                # Default to last 24 hours
                end_time = datetime.utcnow().isoformat()
                start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            # ✅ User-scoped query across all devices
            readings = query_all_user_readings(
                user_id=auth_user_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'user_id': auth_user_id,
                    'count': len(readings),
                    'readings': readings
                }, cls=DecimalEncoder)
            }
        
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
    
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    except PermissionError as e:
        print(f"❌ Authorization error: {e}")
        return {
            'statusCode': 403,
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
