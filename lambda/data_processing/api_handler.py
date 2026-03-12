"""
Data Processing API Handler for API Gateway HTTP requests
Provides REST API endpoints for dashboard stats and water quality data
"""

import json
import boto3
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Add shared utilities to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import CORS utilities
from cors_utils import handle_options, cors_response, success_response, error_response

# Import error handling
from errors import ValidationError, AuthenticationError, DatabaseError, ResourceNotFoundError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Configure logging
logger = get_logger(__name__, service='data-processing-api')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
ALERTS_TABLE = os.environ.get('ALERTS_TABLE', 'AquaChain-Alerts')


@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for data processing API requests
    """
    # Handle OPTIONS preflight requests for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()
    
    # Get HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Get user ID from Cognito authorizer
    user_id = _get_user_id_from_event(event)
    if not user_id:
        raise AuthenticationError('User not authenticated')
    
    logger.info(f"Data processing API request: {http_method} {path}", user_id=user_id)
    
    try:
        # Route to appropriate handler
        if http_method == 'GET' and path.endswith('/dashboard/stats'):
            # GET /dashboard/stats - Get dashboard statistics
            return handle_dashboard_stats(user_id, query_params)
        
        elif http_method == 'GET' and path.endswith('/water-quality/latest'):
            # GET /water-quality/latest - Get latest water quality readings
            return handle_latest_water_quality(user_id, query_params)
        
        elif http_method == 'GET' and '/readings/' in path:
            # Handle readings endpoints: /api/v1/readings/{deviceId} or /api/v1/readings/{deviceId}/history
            return handle_readings_request(user_id, path, query_params)
        
        else:
            raise ValidationError(f'Endpoint not found: {http_method} {path}')
    
    except (ValidationError, AuthenticationError, DatabaseError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in data processing API: {e}")
        raise DatabaseError(f"Data processing API error: {str(e)}")


def _get_user_id_from_event(event: Dict) -> Optional[str]:
    """Extract user ID from Cognito authorizer context"""
    try:
        # Try to get from authorizer claims
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        if user_id:
            return user_id
        
        # Fallback: try to get email
        email = claims.get('email')
        if email:
            return email
        
        return None
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None


def handle_dashboard_stats(user_id: str, query_params: Dict) -> Dict:
    """
    Get dashboard statistics for user
    Returns device count, recent readings, alerts, and quality trends
    """
    try:
        logger.info(f"Fetching dashboard stats for user: {user_id}")
        
        # Get user's devices
        devices = _get_user_devices(user_id)
        device_count = len(devices)
        
        if device_count == 0:
            # User has no devices - return empty stats
            return success_response({
                'deviceCount': 0,
                'activeDevices': 0,
                'totalReadings': 0,
                'activeAlerts': 0,
                'averageQuality': None,
                'recentReadings': [],
                'qualityTrend': 'stable',
                'message': 'No devices registered'
            })
        
        device_ids = [d['deviceId'] for d in devices]
        
        # Get statistics
        active_devices = _count_active_devices(device_ids)
        total_readings = _count_total_readings(device_ids)
        active_alerts = _count_active_alerts(device_ids)
        average_quality = _calculate_average_quality(device_ids)
        recent_readings = _get_recent_readings(device_ids, limit=10)
        quality_trend = _calculate_quality_trend(device_ids)
        
        stats = {
            'deviceCount': device_count,
            'activeDevices': active_devices,
            'totalReadings': total_readings,
            'activeAlerts': active_alerts,
            'averageQuality': average_quality,
            'recentReadings': recent_readings,
            'qualityTrend': quality_trend,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Dashboard stats retrieved successfully", user_id=user_id, device_count=device_count)
        return success_response(stats)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", user_id=user_id)
        raise DatabaseError(f"Failed to fetch dashboard stats: {str(e)}")


def handle_latest_water_quality(user_id: str, query_params: Dict) -> Dict:
    """
    Get latest water quality readings for user's devices
    """
    try:
        logger.info(f"Fetching latest water quality for user: {user_id}")
        
        # Get device ID from query params (optional)
        device_id = query_params.get('deviceId')
        
        if device_id:
            # Verify user owns this device
            if not _user_owns_device(user_id, device_id):
                raise AuthenticationError('Access denied to this device')
            device_ids = [device_id]
        else:
            # Get all user's devices
            devices = _get_user_devices(user_id)
            device_ids = [d['deviceId'] for d in devices]
        
        if not device_ids:
            return success_response({
                'readings': [],
                'message': 'No devices found'
            })
        
        # Get latest reading for each device
        readings = []
        for dev_id in device_ids:
            latest = _get_latest_reading(dev_id)
            if latest:
                readings.append(latest)
        
        logger.info(f"Latest water quality retrieved", user_id=user_id, reading_count=len(readings))
        return success_response({
            'readings': readings,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except (AuthenticationError, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest water quality: {e}", user_id=user_id)
        raise DatabaseError(f"Failed to fetch water quality data: {str(e)}")


def handle_readings_request(user_id: str, path: str, query_params: Dict) -> Dict:
    """
    Handle readings API requests: /api/v1/readings/{deviceId} and /api/v1/readings/{deviceId}/history
    """
    try:
        # Extract device ID from path
        # Path format: /api/v1/readings/{deviceId} or /api/v1/readings/{deviceId}/history
        path_parts = path.strip('/').split('/')
        
        if len(path_parts) < 4 or path_parts[2] != 'readings':
            raise ValidationError('Invalid readings endpoint path')
        
        device_id = path_parts[3]
        is_history = len(path_parts) > 4 and path_parts[4] == 'history'
        is_latest = len(path_parts) > 4 and path_parts[4] == 'latest'
        
        logger.info(f"Readings request for device: {device_id}, history: {is_history}, latest: {is_latest}", user_id=user_id)
        
        # Verify user owns this device
        if not _user_owns_device(user_id, device_id):
            raise AuthenticationError('Access denied to this device')
        
        if is_history:
            # GET /api/v1/readings/{deviceId}/history - Get historical readings
            days = int(query_params.get('days', 7))
            limit = int(query_params.get('limit', 100))
            
            readings = _get_device_historical_readings(device_id, days, limit)
            
            return success_response({
                'deviceId': device_id,
                'readings': readings,
                'days': days,
                'count': len(readings),
                'timestamp': datetime.utcnow().isoformat()
            })
        elif is_latest:
            # GET /api/v1/readings/{deviceId}/latest - Get latest reading (explicit endpoint)
            latest = _get_latest_reading(device_id)
            
            if not latest:
                return success_response({
                    'deviceId': device_id,
                    'reading': None,
                    'message': 'No readings found for this device'
                })
            
            return success_response({
                'deviceId': device_id,
                'reading': latest,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            # GET /api/v1/readings/{deviceId} - Get latest reading (default behavior)
            latest = _get_latest_reading(device_id)
            
            if not latest:
                return success_response({
                    'deviceId': device_id,
                    'reading': None,
                    'message': 'No readings found for this device'
                })
            
            return success_response({
                'deviceId': device_id,
                'reading': latest,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except (AuthenticationError, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f"Error handling readings request: {e}", user_id=user_id)
        raise DatabaseError(f"Failed to fetch readings: {str(e)}")


# Helper functions

def _get_user_devices(user_id: str) -> List[Dict]:
    """Get all devices owned by user"""
    try:
        table = dynamodb.Table(DEVICES_TABLE)
        response = table.query(
            IndexName='userId-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error querying user devices: {e}")
        return []


def _user_owns_device(user_id: str, device_id: str) -> bool:
    """Check if user owns the specified device"""
    try:
        table = dynamodb.Table(DEVICES_TABLE)
        response = table.get_item(Key={'deviceId': device_id})
        device = response.get('Item')
        return device and device.get('userId') == user_id
    except Exception as e:
        logger.error(f"Error checking device ownership: {e}")
        return False


def _count_active_devices(device_ids: List[str]) -> int:
    """Count devices that have sent data in last 24 hours"""
    try:
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        active_count = 0
        
        for device_id in device_ids:
            latest = _get_latest_reading(device_id)
            if latest and latest.get('timestamp', '') > cutoff_time:
                active_count += 1
        
        return active_count
    except Exception as e:
        logger.error(f"Error counting active devices: {e}")
        return 0


def _count_total_readings(device_ids: List[str]) -> int:
    """Count total readings across all devices"""
    try:
        # For performance, we'll estimate based on recent readings
        # In production, you might want to maintain a counter in DynamoDB
        total = 0
        for device_id in device_ids:
            # Count readings in last 30 days
            count = _count_device_readings(device_id, days=30)
            total += count
        return total
    except Exception as e:
        logger.error(f"Error counting total readings: {e}")
        return 0


def _count_device_readings(device_id: str, days: int = 30) -> int:
    """Count readings for a device in the last N days"""
    try:
        table = dynamodb.Table(READINGS_TABLE)
        cutoff_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        response = table.query(
            KeyConditionExpression='deviceId = :deviceId AND #ts > :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':deviceId': device_id,
                ':cutoff': cutoff_time
            },
            Select='COUNT'
        )
        return response.get('Count', 0)
    except Exception as e:
        logger.error(f"Error counting device readings: {e}")
        return 0


def _count_active_alerts(device_ids: List[str]) -> int:
    """Count active (unresolved) alerts for devices"""
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        active_count = 0
        
        for device_id in device_ids:
            response = table.query(
                IndexName='deviceId-status-index',
                KeyConditionExpression='deviceId = :deviceId AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':deviceId': device_id,
                    ':status': 'active'
                },
                Select='COUNT'
            )
            active_count += response.get('Count', 0)
        
        return active_count
    except Exception as e:
        logger.error(f"Error counting active alerts: {e}")
        return 0


def _calculate_average_quality(device_ids: List[str]) -> Optional[float]:
    """Calculate average water quality score across devices"""
    try:
        quality_scores = []
        
        for device_id in device_ids:
            latest = _get_latest_reading(device_id)
            if latest and 'qualityScore' in latest:
                quality_scores.append(float(latest['qualityScore']))
        
        if not quality_scores:
            return None
        
        return round(sum(quality_scores) / len(quality_scores), 2)
    except Exception as e:
        logger.error(f"Error calculating average quality: {e}")
        return None


def _get_recent_readings(device_ids: List[str], limit: int = 10) -> List[Dict]:
    """Get most recent readings across all devices"""
    try:
        all_readings = []
        
        for device_id in device_ids:
            readings = _get_device_recent_readings(device_id, limit=5)
            all_readings.extend(readings)
        
        # Sort by timestamp descending and take top N
        all_readings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return _convert_decimals(all_readings[:limit])
    except Exception as e:
        logger.error(f"Error getting recent readings: {e}")
        return []


def _get_device_recent_readings(device_id: str, limit: int = 5) -> List[Dict]:
    """Get recent readings for a specific device"""
    try:
        table = dynamodb.Table(READINGS_TABLE)
        response = table.query(
            KeyConditionExpression='deviceId = :deviceId',
            ExpressionAttributeValues={':deviceId': device_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting device recent readings: {e}")
        return []


def _get_device_historical_readings(device_id: str, days: int = 7, limit: int = 100) -> List[Dict]:
    """Get historical readings for a device within the specified time range"""
    try:
        table = dynamodb.Table(READINGS_TABLE)
        cutoff_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        response = table.query(
            KeyConditionExpression='deviceId = :deviceId AND #ts > :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':deviceId': device_id,
                ':cutoff': cutoff_time
            },
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        return _convert_decimals(response.get('Items', []))
    except Exception as e:
        logger.error(f"Error getting device historical readings: {e}")
        return []


def _get_latest_reading(device_id: str) -> Optional[Dict]:
    """Get the most recent reading for a device"""
    try:
        readings = _get_device_recent_readings(device_id, limit=1)
        if readings:
            return _convert_decimals(readings[0])
        return None
    except Exception as e:
        logger.error(f"Error getting latest reading: {e}")
        return None


def _calculate_quality_trend(device_ids: List[str]) -> str:
    """Calculate quality trend (improving/declining/stable)"""
    try:
        # Get average quality from last 7 days vs previous 7 days
        recent_scores = []
        previous_scores = []
        
        for device_id in device_ids:
            recent = _get_average_quality_for_period(device_id, days=7)
            previous = _get_average_quality_for_period(device_id, days=14, offset_days=7)
            
            if recent is not None:
                recent_scores.append(recent)
            if previous is not None:
                previous_scores.append(previous)
        
        if not recent_scores or not previous_scores:
            return 'stable'
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        previous_avg = sum(previous_scores) / len(previous_scores)
        
        # 5% threshold for trend detection
        if recent_avg > previous_avg * 1.05:
            return 'improving'
        elif recent_avg < previous_avg * 0.95:
            return 'declining'
        else:
            return 'stable'
    except Exception as e:
        logger.error(f"Error calculating quality trend: {e}")
        return 'stable'


def _get_average_quality_for_period(device_id: str, days: int, offset_days: int = 0) -> Optional[float]:
    """Get average quality score for a time period"""
    try:
        table = dynamodb.Table(READINGS_TABLE)
        end_time = datetime.utcnow() - timedelta(days=offset_days)
        start_time = end_time - timedelta(days=days)
        
        response = table.query(
            KeyConditionExpression='deviceId = :deviceId AND #ts BETWEEN :start AND :end',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':deviceId': device_id,
                ':start': start_time.isoformat(),
                ':end': end_time.isoformat()
            }
        )
        
        items = response.get('Items', [])
        if not items:
            return None
        
        scores = [float(item['qualityScore']) for item in items if 'qualityScore' in item]
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    except Exception as e:
        logger.error(f"Error getting average quality for period: {e}")
        return None


def _convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
