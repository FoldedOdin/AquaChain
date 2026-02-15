"""
Alert Detection API Handler for API Gateway HTTP requests
Provides REST API endpoints for alert management
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
logger = get_logger(__name__, service='alert-detection-api')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ALERTS_TABLE = os.environ.get('ALERTS_TABLE', 'AquaChain-Alerts')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')


@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for alert detection API requests
    """
    # Handle OPTIONS preflight requests for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()
    
    # Get HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    path_params = event.get('pathParameters', {}) or {}
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Get user ID from Cognito authorizer
    user_id = _get_user_id_from_event(event)
    if not user_id:
        raise AuthenticationError('User not authenticated')
    
    logger.info(f"Alert detection API request: {http_method} {path}", user_id=user_id)
    
    try:
        # Parse body if present
        body = {}
        if event.get('body'):
            body = json.loads(event.get('body', '{}'))
        
        # Route to appropriate handler
        if http_method == 'GET' and path.endswith('/alerts'):
            # GET /alerts - List user alerts
            return handle_get_alerts(user_id, query_params)
        
        elif http_method == 'GET' and path_params.get('alertId'):
            # GET /alerts/{alertId} - Get specific alert
            alert_id = path_params.get('alertId')
            return handle_get_alert(user_id, alert_id)
        
        elif http_method == 'PUT' and '/acknowledge' in path:
            # PUT /alerts/{alertId}/acknowledge - Acknowledge alert
            alert_id = path_params.get('alertId')
            if not alert_id:
                raise ValidationError('Alert ID required')
            return handle_acknowledge_alert(user_id, alert_id, body)
        
        elif http_method == 'PUT' and '/resolve' in path:
            # PUT /alerts/{alertId}/resolve - Resolve alert
            alert_id = path_params.get('alertId')
            if not alert_id:
                raise ValidationError('Alert ID required')
            return handle_resolve_alert(user_id, alert_id, body)
        
        else:
            raise ValidationError(f'Endpoint not found: {http_method} {path}')
    
    except (ValidationError, AuthenticationError, DatabaseError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in alert detection API: {e}")
        raise DatabaseError(f"Alert detection API error: {str(e)}")


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


def handle_get_alerts(user_id: str, query_params: Dict) -> Dict:
    """
    Get alerts for user's devices with filtering and pagination
    """
    try:
        logger.info(f"Fetching alerts for user: {user_id}")
        
        # Get user's devices
        devices = _get_user_devices(user_id)
        device_ids = [d['deviceId'] for d in devices]
        
        if not device_ids:
            return success_response({
                'alerts': [],
                'total': 0,
                'message': 'No devices found'
            })
        
        # Get filter parameters
        status = query_params.get('status', 'all')  # all, active, acknowledged, resolved
        severity = query_params.get('severity')  # critical, warning, info
        device_id = query_params.get('deviceId')
        limit = int(query_params.get('limit', 50))
        limit = min(limit, 100)  # Max 100 per request
        
        # Filter device IDs if specific device requested
        if device_id:
            if device_id not in device_ids:
                raise AuthenticationError('Access denied to this device')
            device_ids = [device_id]
        
        # Get alerts for all devices
        all_alerts = []
        for dev_id in device_ids:
            alerts = _get_device_alerts(dev_id, status, severity, limit)
            all_alerts.extend(alerts)
        
        # Sort by timestamp descending (most recent first)
        all_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        alerts = all_alerts[:limit]
        
        # Convert Decimals for JSON serialization
        alerts = _convert_decimals(alerts)
        
        logger.info(f"Alerts retrieved", user_id=user_id, alert_count=len(alerts))
        return success_response({
            'alerts': alerts,
            'total': len(all_alerts),
            'returned': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except (AuthenticationError, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", user_id=user_id)
        raise DatabaseError(f"Failed to fetch alerts: {str(e)}")


def handle_get_alert(user_id: str, alert_id: str) -> Dict:
    """
    Get specific alert details
    """
    try:
        logger.info(f"Fetching alert: {alert_id}", user_id=user_id)
        
        # Get alert
        table = dynamodb.Table(ALERTS_TABLE)
        response = table.get_item(Key={'alertId': alert_id})
        alert = response.get('Item')
        
        if not alert:
            raise ResourceNotFoundError(f'Alert not found: {alert_id}')
        
        # Verify user owns the device
        device_id = alert.get('deviceId')
        if not _user_owns_device(user_id, device_id):
            raise AuthenticationError('Access denied to this alert')
        
        alert = _convert_decimals(alert)
        
        logger.info(f"Alert retrieved", user_id=user_id, alert_id=alert_id)
        return success_response(alert)
        
    except (AuthenticationError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert: {e}", user_id=user_id, alert_id=alert_id)
        raise DatabaseError(f"Failed to fetch alert: {str(e)}")


def handle_acknowledge_alert(user_id: str, alert_id: str, body: Dict) -> Dict:
    """
    Acknowledge an alert
    """
    try:
        logger.info(f"Acknowledging alert: {alert_id}", user_id=user_id)
        
        # Get alert
        table = dynamodb.Table(ALERTS_TABLE)
        response = table.get_item(Key={'alertId': alert_id})
        alert = response.get('Item')
        
        if not alert:
            raise ResourceNotFoundError(f'Alert not found: {alert_id}')
        
        # Verify user owns the device
        device_id = alert.get('deviceId')
        if not _user_owns_device(user_id, device_id):
            raise AuthenticationError('Access denied to this alert')
        
        # Update alert status
        notes = body.get('notes', '')
        update_time = datetime.utcnow().isoformat()
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #status = :status, acknowledgedBy = :user, acknowledgedAt = :time, notes = :notes',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'acknowledged',
                ':user': user_id,
                ':time': update_time,
                ':notes': notes
            }
        )
        
        logger.info(f"Alert acknowledged", user_id=user_id, alert_id=alert_id)
        return success_response({
            'message': 'Alert acknowledged successfully',
            'alertId': alert_id,
            'status': 'acknowledged',
            'acknowledgedAt': update_time
        })
        
    except (AuthenticationError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", user_id=user_id, alert_id=alert_id)
        raise DatabaseError(f"Failed to acknowledge alert: {str(e)}")


def handle_resolve_alert(user_id: str, alert_id: str, body: Dict) -> Dict:
    """
    Resolve an alert
    """
    try:
        logger.info(f"Resolving alert: {alert_id}", user_id=user_id)
        
        # Get alert
        table = dynamodb.Table(ALERTS_TABLE)
        response = table.get_item(Key={'alertId': alert_id})
        alert = response.get('Item')
        
        if not alert:
            raise ResourceNotFoundError(f'Alert not found: {alert_id}')
        
        # Verify user owns the device
        device_id = alert.get('deviceId')
        if not _user_owns_device(user_id, device_id):
            raise AuthenticationError('Access denied to this alert')
        
        # Update alert status
        resolution_notes = body.get('resolutionNotes', '')
        update_time = datetime.utcnow().isoformat()
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #status = :status, resolvedBy = :user, resolvedAt = :time, resolutionNotes = :notes',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'resolved',
                ':user': user_id,
                ':time': update_time,
                ':notes': resolution_notes
            }
        )
        
        logger.info(f"Alert resolved", user_id=user_id, alert_id=alert_id)
        return success_response({
            'message': 'Alert resolved successfully',
            'alertId': alert_id,
            'status': 'resolved',
            'resolvedAt': update_time
        })
        
    except (AuthenticationError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", user_id=user_id, alert_id=alert_id)
        raise DatabaseError(f"Failed to resolve alert: {str(e)}")


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


def _get_device_alerts(device_id: str, status: str, severity: Optional[str], limit: int) -> List[Dict]:
    """Get alerts for a specific device with filters"""
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        # Build query based on status filter
        if status == 'all':
            # Query all alerts for device
            response = table.query(
                IndexName='deviceId-timestamp-index',
                KeyConditionExpression='deviceId = :deviceId',
                ExpressionAttributeValues={':deviceId': device_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
        else:
            # Query by status
            response = table.query(
                IndexName='deviceId-status-index',
                KeyConditionExpression='deviceId = :deviceId AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':deviceId': device_id,
                    ':status': status
                },
                ScanIndexForward=False,
                Limit=limit
            )
        
        alerts = response.get('Items', [])
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        
        return alerts
    except Exception as e:
        logger.error(f"Error getting device alerts: {e}")
        return []


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
