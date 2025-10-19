"""
Readings API Lambda function for historical data access
Handles water quality reading queries and historical data retrieval
"""
import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Table references
readings_table = dynamodb.Table('aquachain-readings')
users_table = dynamodb.Table('aquachain-users')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """Main Lambda handler for readings API"""
    try:
        # Parse request
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {}) or {}
        query_parameters = event.get('queryStringParameters', {}) or {}
        body = event.get('body')
        
        # Get user context from authorizer
        user_context = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = user_context.get('sub')
        user_groups = user_context.get('cognito:groups', '').split(',')
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized', 'message': 'User not authenticated'})
        
        # Route request based on HTTP method and path
        if http_method == 'GET':
            if 'deviceId' in path_parameters:
                return get_device_readings(path_parameters['deviceId'], query_parameters, user_id, user_groups)
            else:
                return get_user_readings(user_id, query_parameters, user_groups)
        
        elif http_method == 'POST':
            # Only administrators can manually add readings
            if 'administrators' not in user_groups:
                return create_response(403, {'error': 'Forbidden', 'message': 'Insufficient permissions'})
            return create_reading(json.loads(body), user_id)
        
        else:
            return create_response(405, {'error': 'Method Not Allowed'})
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_device_readings(device_id: str, query_params: Dict[str, str], user_id: str, user_groups: List[str]) -> Dict[str, Any]:
    """Get readings for a specific device"""
    try:
        # Check if user has access to this device
        if not has_device_access(user_id, device_id, user_groups):
            return create_response(403, {'error': 'Forbidden', 'message': 'Access denied to this device'})
        
        # Parse query parameters
        days = int(query_params.get('days', 7))
        limit = int(query_params.get('limit', 100))
        start_date = query_params.get('startDate')
        end_date = query_params.get('endDate')
        
        # Validate parameters
        if days > 90:
            return create_response(400, {'error': 'Bad Request', 'message': 'Maximum 90 days of data allowed'})
        
        if limit > 1000:
            return create_response(400, {'error': 'Bad Request', 'message': 'Maximum 1000 records per request'})
        
        # Calculate date range
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=days)
        
        # Query readings with time-windowed partition keys
        readings = []
        current_month = start_dt.replace(day=1)
        
        while current_month <= end_dt:
            partition_key = f"{device_id}#{current_month.strftime('%Y%m')}"
            
            response = readings_table.query(
                KeyConditionExpression='#pk = :pk AND #sk BETWEEN :start AND :end',
                ExpressionAttributeNames={
                    '#pk': 'deviceId#YYYYMM',
                    '#sk': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':pk': partition_key,
                    ':start': start_dt.isoformat(),
                    ':end': end_dt.isoformat()
                },
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            readings.extend(response.get('Items', []))
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Sort by timestamp (most recent first) and limit results
        readings.sort(key=lambda x: x['timestamp'], reverse=True)
        readings = readings[:limit]
        
        # Calculate summary statistics
        summary = calculate_reading_summary(readings)
        
        return create_response(200, {
            'deviceId': device_id,
            'readings': readings,
            'summary': summary,
            'count': len(readings),
            'dateRange': {
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat()
            }
        })
    
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return create_response(500, {'error': 'Database Error', 'message': 'Failed to retrieve readings'})
    except ValueError as e:
        logger.error(f"Parameter error: {str(e)}")
        return create_response(400, {'error': 'Bad Request', 'message': str(e)})


def get_user_readings(user_id: str, query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get readings for all user's devices"""
    try:
        # Get user's devices
        if 'administrators' in user_groups:
            # Administrators can see all devices
            device_ids = get_all_device_ids()
        else:
            device_ids = get_user_device_ids(user_id)
        
        if not device_ids:
            return create_response(200, {
                'devices': [],
                'message': 'No devices found for user'
            })
        
        # Parse query parameters
        days = int(query_params.get('days', 1))
        latest_only = query_params.get('latest', 'false').lower() == 'true'
        
        # Get latest reading for each device
        device_readings = []
        for device_id in device_ids:
            if latest_only:
                reading = get_latest_reading(device_id)
                if reading:
                    device_readings.append({
                        'deviceId': device_id,
                        'latestReading': reading
                    })
            else:
                readings = get_recent_readings(device_id, days)
                device_readings.append({
                    'deviceId': device_id,
                    'readings': readings,
                    'count': len(readings)
                })
        
        return create_response(200, {
            'devices': device_readings,
            'totalDevices': len(device_ids)
        })
    
    except Exception as e:
        logger.error(f"Error getting user readings: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def create_reading(reading_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Create a new reading (admin only)"""
    try:
        # Validate required fields
        required_fields = ['deviceId', 'readings', 'location']
        for field in required_fields:
            if field not in reading_data:
                return create_response(400, {'error': 'Bad Request', 'message': f'Missing required field: {field}'})
        
        # Generate reading entry
        timestamp = datetime.utcnow().isoformat()
        device_id = reading_data['deviceId']
        partition_key = f"{device_id}#{datetime.utcnow().strftime('%Y%m')}"
        
        reading_item = {
            'deviceId#YYYYMM': partition_key,
            'timestamp': timestamp,
            'deviceId': device_id,
            'readings': reading_data['readings'],
            'location': reading_data['location'],
            'wqi': reading_data.get('wqi', 0),
            'anomalyType': reading_data.get('anomalyType', 'normal'),
            'createdBy': user_id,
            'source': 'manual'
        }
        
        # Store in DynamoDB
        readings_table.put_item(Item=reading_item)
        
        logger.info(f"Manual reading created for device {device_id} by user {user_id}")
        
        return create_response(201, {
            'message': 'Reading created successfully',
            'reading': reading_item
        })
    
    except Exception as e:
        logger.error(f"Error creating reading: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def has_device_access(user_id: str, device_id: str, user_groups: List[str]) -> bool:
    """Check if user has access to device"""
    try:
        # Administrators have access to all devices
        if 'administrators' in user_groups:
            return True
        
        # Check if device is associated with user
        response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            return False
        
        user_device_ids = response['Item'].get('deviceIds', set())
        return device_id in user_device_ids
    
    except Exception as e:
        logger.error(f"Error checking device access: {str(e)}")
        return False


def get_user_device_ids(user_id: str) -> List[str]:
    """Get list of device IDs for user"""
    try:
        response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            return []
        
        device_ids = response['Item'].get('deviceIds', set())
        return list(device_ids)
    
    except Exception as e:
        logger.error(f"Error getting user devices: {str(e)}")
        return []


def get_all_device_ids() -> List[str]:
    """Get all device IDs (admin only)"""
    try:
        # This would typically come from a devices table
        # For now, scan readings table for unique device IDs
        response = readings_table.scan(
            ProjectionExpression='deviceId',
            Limit=1000
        )
        
        device_ids = set()
        for item in response.get('Items', []):
            device_ids.add(item['deviceId'])
        
        return list(device_ids)
    
    except Exception as e:
        logger.error(f"Error getting all devices: {str(e)}")
        return []


def get_latest_reading(device_id: str) -> Optional[Dict[str, Any]]:
    """Get latest reading for device"""
    try:
        # Query current month first
        current_month = datetime.utcnow().strftime('%Y%m')
        partition_key = f"{device_id}#{current_month}"
        
        response = readings_table.query(
            KeyConditionExpression='#pk = :pk',
            ExpressionAttributeNames={'#pk': 'deviceId#YYYYMM'},
            ExpressionAttributeValues={':pk': partition_key},
            Limit=1,
            ScanIndexForward=False
        )
        
        if response.get('Items'):
            return response['Items'][0]
        
        # If no readings in current month, check previous month
        prev_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime('%Y%m')
        partition_key = f"{device_id}#{prev_month}"
        
        response = readings_table.query(
            KeyConditionExpression='#pk = :pk',
            ExpressionAttributeNames={'#pk': 'deviceId#YYYYMM'},
            ExpressionAttributeValues={':pk': partition_key},
            Limit=1,
            ScanIndexForward=False
        )
        
        return response.get('Items', [None])[0]
    
    except Exception as e:
        logger.error(f"Error getting latest reading: {str(e)}")
        return None


def get_recent_readings(device_id: str, days: int) -> List[Dict[str, Any]]:
    """Get recent readings for device"""
    try:
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=days)
        
        # Query current month
        current_month = end_dt.strftime('%Y%m')
        partition_key = f"{device_id}#{current_month}"
        
        response = readings_table.query(
            KeyConditionExpression='#pk = :pk AND #sk >= :start',
            ExpressionAttributeNames={
                '#pk': 'deviceId#YYYYMM',
                '#sk': 'timestamp'
            },
            ExpressionAttributeValues={
                ':pk': partition_key,
                ':start': start_dt.isoformat()
            },
            Limit=100,
            ScanIndexForward=False
        )
        
        return response.get('Items', [])
    
    except Exception as e:
        logger.error(f"Error getting recent readings: {str(e)}")
        return []


def calculate_reading_summary(readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for readings"""
    if not readings:
        return {}
    
    try:
        # Extract numeric values
        wqi_values = [float(r.get('wqi', 0)) for r in readings if r.get('wqi')]
        ph_values = [float(r.get('readings', {}).get('pH', 0)) for r in readings if r.get('readings', {}).get('pH')]
        
        # Calculate averages
        avg_wqi = sum(wqi_values) / len(wqi_values) if wqi_values else 0
        avg_ph = sum(ph_values) / len(ph_values) if ph_values else 0
        
        # Count anomalies
        anomaly_counts = {}
        for reading in readings:
            anomaly_type = reading.get('anomalyType', 'normal')
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1
        
        return {
            'averageWQI': round(avg_wqi, 2),
            'averagePH': round(avg_ph, 2),
            'anomalyCounts': anomaly_counts,
            'totalReadings': len(readings),
            'dateRange': {
                'earliest': min(r['timestamp'] for r in readings),
                'latest': max(r['timestamp'] for r in readings)
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating summary: {str(e)}")
        return {}


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }