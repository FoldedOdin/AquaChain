"""
Notification API Handler for API Gateway HTTP requests
Provides REST API endpoints for notification management
"""

import json
import boto3
import logging
import sys
import os
import uuid
from urllib.parse import unquote
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import CORS utilities
from cors_utils import handle_options, cors_response, success_response, error_response

# Import error handling
from error_handler import (
    handle_errors,
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    DatabaseError,
)

# Import structured logging
from structured_logger import get_logger

# Configure logging
logger = get_logger(__name__, service='notification-api')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
NOTIFICATIONS_TABLE = os.environ.get('NOTIFICATIONS_TABLE', 'aquachain-notifications')
USERS_TABLE = os.environ.get('USERS_TABLE', 'aquachain-users')

@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for notification API requests
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
    
    logger.info(f"Notification API request: {http_method} {path}", user_id=user_id)
    
    try:
        # Parse body if present
        body = {}
        if event.get('body'):
            body = json.loads(event.get('body', '{}'))
        
        # Route to appropriate handler
        if http_method == 'GET' and path.endswith('/notifications'):
            # GET /api/notifications - List user notifications
            return handle_list_notifications(user_id, query_params)
        
        elif http_method == 'POST' and path.endswith('/notifications'):
            # POST /api/notifications - Create notification (admin only)
            return handle_create_notification(user_id, body)
        
        elif http_method == 'GET' and '/unread-count' in path:
            # GET /api/notifications/unread-count - Get unread count
            return handle_get_unread_count(user_id)
        
        elif http_method == 'PUT' and '/read-all' in path:
            # PUT /api/notifications/read-all - Mark all as read
            return handle_mark_all_read(user_id)
        
        elif http_method == 'PUT' and path.endswith('/read'):
            # PUT /api/notifications/{notificationId}/read - Mark one as read
            notification_id = path_params.get('notificationId')
            if not notification_id:
                raise ValidationError('Notification ID required')
            return handle_mark_as_read(user_id, _decode_id(notification_id))
        
        elif http_method == 'PUT' and path_params.get('notificationId'):
            # PUT /api/notifications/{notificationId} - also mark as read (legacy path)
            notification_id = path_params.get('notificationId')
            return handle_mark_as_read(user_id, _decode_id(notification_id))
        
        elif http_method == 'DELETE' and path_params.get('notificationId'):
            # DELETE /api/notifications/{notificationId} - Delete notification
            notification_id = path_params.get('notificationId')
            return handle_delete_notification(user_id, _decode_id(notification_id))
        
        elif http_method == 'POST' and '/broadcast' in path:
            # POST /api/notifications/broadcast - Send system-wide announcement (admin only)
            return handle_broadcast_announcement(user_id, body, event)
        
        elif http_method == 'GET' and '/announcements' in path:
            # GET /api/notifications/announcements - List past announcements (admin only)
            return handle_list_announcements(user_id, query_params, event)
        
        else:
            raise ValidationError(f'Endpoint not found: {http_method} {path}')
    
    except (ValidationError, AuthenticationError, DatabaseError, ResourceNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in notification API: {e}")
        raise DatabaseError(f"Notification API error: {str(e)}")


def _get_user_id_from_event(event: Dict) -> Optional[str]:
    """Extract user ID from Cognito authorizer context"""
    try:
        # Try to get from authorizer claims
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        if user_id:
            return user_id
        
        # Fallback: try to get email and look up user
        email = claims.get('email')
        if email:
            # For now, use email as user identifier
            # In production, you'd query DynamoDB to get userId from email
            return email
        
        return None
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None


def _map_notification(item: Dict) -> Dict:
    """
    Map a raw DynamoDB notification record to the shape the frontend expects.
    The notification_service/handler.py stores fields like notificationId,
    notificationType, and embeds title/message inside a 'content' map.
    The frontend NotificationCenter expects: id, type, title, message, timestamp, read, priority.
    """
    content = item.get('content', {})

    # Derive a human-readable type from notificationType
    raw_type = item.get('notificationType', 'info')
    type_map = {
        'water_quality_alert': 'warning',
        'contact_form_submission': 'info',
        'service_update': 'info',
        'system_alert': 'error',
        'device_offline': 'warning',
        'device_online': 'success',
    }
    mapped_type = type_map.get(raw_type, 'info')

    # Derive priority from alertLevel
    alert_level = item.get('alertLevel', 'medium')
    priority_map = {'critical': 'high', 'warning': 'medium', 'info': 'low'}
    priority = priority_map.get(alert_level, 'medium')

    # Build a meaningful message from content if no explicit message field
    message = content.get('message') or item.get('message') or ''
    if not message:
        if raw_type == 'water_quality_alert':
            device_id = content.get('deviceId', '')
            wqi = content.get('wqi', '')
            reasons = content.get('alertReasons', [])
            if reasons:
                message = f"Device {device_id}: {reasons[0]}" if device_id else reasons[0]
            elif wqi:
                message = f"Device {device_id}: Water Quality Index is {wqi}" if device_id else f"Water Quality Index is {wqi}"
        elif raw_type == 'contact_form_submission':
            message = content.get('subject') or content.get('name') or 'New contact form submission received'

    # deviceId may be top-level or inside content
    device_id = item.get('deviceId') or content.get('deviceId')

    return {
        'id': item.get('notificationId', ''),
        'type': mapped_type,
        'title': content.get('title') or item.get('title') or raw_type.replace('_', ' ').title(),
        'message': message,
        'timestamp': item.get('createdAt', ''),
        'read': item.get('read', False),
        'priority': item.get('priority', priority),
        'userId': item.get('userId'),
        'deviceId': device_id,
        'actionUrl': item.get('actionUrl'),
    }


def handle_list_notifications(user_id: str, query_params: Dict) -> Dict:
    """
    List notifications for user with pagination
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Get pagination parameters
        limit = int(query_params.get('limit', 50))
        limit = min(limit, 100)  # Max 100 per request
        
        # Query notifications for user
        query_kwargs = {
            'IndexName': 'userId-createdAt-index',
            'KeyConditionExpression': 'userId = :userId',
            'ExpressionAttributeValues': {':userId': user_id},
            'ScanIndexForward': False,  # Most recent first
            'Limit': limit
        }
        
        # Handle pagination
        last_key = query_params.get('lastKey')
        if last_key:
            import base64
            query_kwargs['ExclusiveStartKey'] = json.loads(base64.b64decode(last_key))
        
        response = table.query(**query_kwargs)
        
        # Map raw DynamoDB items to the shape the frontend expects
        notifications = [_map_notification(item) for item in response.get('Items', [])]
        
        # Format response
        result = {
            'notifications': notifications,
            'count': len(notifications)
        }
        
        # Add pagination token if more results
        if 'LastEvaluatedKey' in response:
            import base64
            result['lastKey'] = base64.b64encode(
                json.dumps(response['LastEvaluatedKey']).encode()
            ).decode()
        
        logger.info(f"Listed {len(notifications)} notifications for user {user_id}")
        return success_response(result)
    
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise DatabaseError(f"Failed to list notifications: {str(e)}")


def handle_create_notification(user_id: str, body: Dict) -> Dict:
    """
    Create a new notification (admin/system use)
    """
    try:
        # Validate required fields
        if not body.get('userId'):
            raise ValidationError('userId is required')
        
        if not body.get('type'):
            raise ValidationError('type is required')
        
        if not body.get('message'):
            raise ValidationError('message is required')
        
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Create notification record — use UUID to avoid composite key issues
        notification_id = str(uuid.uuid4())
        
        notification = {
            'notificationId': notification_id,
            'userId': body['userId'],
            'type': body['type'],
            'title': body.get('title', 'Notification'),
            'message': body['message'],
            'priority': body.get('priority', 'medium'),
            'read': False,
            'timestamp': datetime.utcnow().isoformat(),
            'createdAt': datetime.utcnow().isoformat(),
            'deviceId': body.get('deviceId'),
            'actionUrl': body.get('actionUrl')
        }
        
        table.put_item(Item=notification)
        
        logger.info(f"Created notification {notification_id} for user {body['userId']}")
        return success_response({'notification': notification}, status_code=201)
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise DatabaseError(f"Failed to create notification: {str(e)}")


def handle_get_unread_count(user_id: str) -> Dict:
    """
    Get count of unread notifications for user.
    Counts records where read is False OR read attribute is absent (new notifications).
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Query all notifications for user, filter unread client-side
        # (attribute_not_exists handles records created before 'read' field was added)
        response = table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            FilterExpression='#read = :false OR attribute_not_exists(#read)',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':userId': user_id,
                ':false': False
            },
            Select='COUNT'
        )
        
        count = response.get('Count', 0)
        
        logger.info(f"User {user_id} has {count} unread notifications")
        return success_response({'count': count})
    
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise DatabaseError(f"Failed to get unread count: {str(e)}")


def _decode_id(notification_id: str) -> str:
    """URL-decode a notification ID (API Gateway may leave %3A un-decoded)."""
    return unquote(notification_id)


def _resolve_notification_id(table, notification_id: str):
    """
    Look up a notification by ID. If not found and the ID contains a legacy
    composite suffix (uuid:timestamp), retry with just the UUID portion.
    Returns the DynamoDB item or None.
    """
    response = table.get_item(Key={'notificationId': notification_id})
    item = response.get('Item')
    if item:
        return item
    # Legacy IDs were stored as "{userId}:{timestamp}" — the frontend may still
    # hold old IDs in the format "{uuid}:{timestamp}". Try stripping the suffix.
    if ':' in notification_id:
        stripped = notification_id.rsplit(':', 1)[0]
        response = table.get_item(Key={'notificationId': stripped})
        return response.get('Item')
    return None


def handle_mark_as_read(user_id: str, notification_id: str) -> Dict:
    """
    Mark a specific notification as read
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Verify notification belongs to user (handles legacy composite IDs)
        notification = _resolve_notification_id(table, notification_id)
        resolved_id = notification.get('notificationId') if notification else notification_id
        
        if not notification:
            raise ResourceNotFoundError('Notification not found')
        
        if notification.get('userId') != user_id:
            raise AuthenticationError('Not authorized to modify this notification')
        
        # Mark as read using the actual stored ID
        table.update_item(
            Key={'notificationId': resolved_id},
            UpdateExpression='SET #read = :read, readAt = :readAt',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':read': True,
                ':readAt': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Marked notification {resolved_id} as read for user {user_id}")
        return success_response({'message': 'Notification marked as read'})
    
    except (ResourceNotFoundError, AuthenticationError):
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise DatabaseError(f"Failed to mark notification as read: {str(e)}")


def handle_mark_all_read(user_id: str) -> Dict:
    """
    Mark all notifications as read for user
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Query all unread notifications for user
        # Include records where read is False OR read attribute is absent (new notifications)
        response = table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            FilterExpression='#read = :false OR attribute_not_exists(#read)',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':userId': user_id,
                ':false': False
            }
        )
        
        notifications = response.get('Items', [])
        
        # Mark each as read
        updated_count = 0
        for notification in notifications:
            try:
                table.update_item(
                    Key={'notificationId': notification['notificationId']},
                    UpdateExpression='SET #read = :read, readAt = :readAt',
                    ExpressionAttributeNames={'#read': 'read'},
                    ExpressionAttributeValues={
                        ':read': True,
                        ':readAt': datetime.utcnow().isoformat()
                    }
                )
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to mark notification {notification['notificationId']} as read: {e}")
        
        logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
        return success_response({
            'message': f'Marked {updated_count} notifications as read',
            'count': updated_count
        })
    
    except Exception as e:
        logger.error(f"Error marking all as read: {e}")
        raise DatabaseError(f"Failed to mark all as read: {str(e)}")


def handle_delete_notification(user_id: str, notification_id: str) -> Dict:
    """
    Delete a notification
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Verify notification belongs to user (handles legacy composite IDs)
        notification = _resolve_notification_id(table, notification_id)
        resolved_id = notification.get('notificationId') if notification else notification_id
        
        if not notification:
            raise ResourceNotFoundError('Notification not found')
        
        if notification.get('userId') != user_id:
            raise AuthenticationError('Not authorized to delete this notification')
        
        # Delete using the actual stored ID
        table.delete_item(Key={'notificationId': resolved_id})
        
        logger.info(f"Deleted notification {resolved_id} for user {user_id}")
        return success_response({'message': 'Notification deleted'})
    
    except (ResourceNotFoundError, AuthenticationError):
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise DatabaseError(f"Failed to delete notification: {str(e)}")


def _is_admin(event: Dict) -> bool:
    """Check if the caller has admin role via Cognito groups claim."""
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')
    if isinstance(groups, list):
        return any('admin' in g.lower() for g in groups)
    return 'admin' in str(groups).lower()


def _get_users_by_role(role_filter: str) -> List[Dict]:
    """
    Scan the users table and return real users matching the role filter.
    Excludes simulator-generated users (userId starting with 'user-').
    role_filter: 'all' | 'consumer' | 'technician'
    Returns list of dicts with at least userId and role.
    """
    table = dynamodb.Table(USERS_TABLE)
    scan_kwargs: Dict[str, Any] = {
        'ProjectionExpression': 'userId, #r',
        'ExpressionAttributeNames': {'#r': 'role'},
        # Exclude simulator-generated users (user-{timestamp} pattern)
        'FilterExpression': 'NOT begins_with(userId, :sim_prefix)',
        'ExpressionAttributeValues': {':sim_prefix': 'user-'},
    }
    if role_filter != 'all':
        scan_kwargs['FilterExpression'] += ' AND #r = :role'
        scan_kwargs['ExpressionAttributeValues'][':role'] = role_filter

    users: List[Dict] = []
    while True:
        response = table.scan(**scan_kwargs)
        users.extend(response.get('Items', []))
        last_key = response.get('LastEvaluatedKey')
        if not last_key:
            break
        scan_kwargs['ExclusiveStartKey'] = last_key

    return users


def handle_broadcast_announcement(user_id: str, body: Dict, event: Dict) -> Dict:
    """
    POST /api/notifications/broadcast
    Admin-only: send a system-wide announcement to all users, only consumers, or only technicians.
    Body: { title, message, type ('info'|'warning'|'error'), audience ('all'|'consumer'|'technician') }
    """
    if not _is_admin(event):
        raise AuthenticationError('Admin role required to send announcements')

    title = (body.get('title') or '').strip()
    message = (body.get('message') or '').strip()
    announcement_type = body.get('type', 'info')
    audience = body.get('audience', 'all')

    if not title:
        raise ValidationError('title is required')
    if not message:
        raise ValidationError('message is required')
    if announcement_type not in ('info', 'warning', 'error', 'success'):
        raise ValidationError('type must be one of: info, warning, error, success')
    if audience not in ('all', 'consumer', 'technician'):
        raise ValidationError('audience must be one of: all, consumer, technician')

    # Fetch target users
    target_users = _get_users_by_role(audience)
    if not target_users:
        return success_response({'message': 'No users found for the selected audience', 'sent': 0})

    notifications_table = dynamodb.Table(NOTIFICATIONS_TABLE)
    announcement_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + 'Z'
    ttl_seconds = int(datetime.utcnow().timestamp()) + (30 * 24 * 3600)  # 30-day TTL

    sent = 0
    with notifications_table.batch_writer() as batch:
        for u in target_users:
            target_user_id = u.get('userId')
            if not target_user_id:
                continue
            notification_id = f"ann_{announcement_id}_{target_user_id}"
            batch.put_item(Item={
                'notificationId': notification_id,
                'userId': target_user_id,
                'notificationType': 'announcement',
                'announcementId': announcement_id,
                'content': {
                    'title': title,
                    'message': message,
                },
                'type': announcement_type,
                'title': title,
                'message': message,
                'priority': 'medium' if announcement_type == 'info' else 'high',
                'read': False,
                'createdAt': now,
                'sentBy': user_id,
                'audience': audience,
                'ttl': ttl_seconds,
            })
            sent += 1

    logger.info(
        f"Broadcast announcement sent - announcement_id={announcement_id}, "
        f"audience={audience}, sent={sent}, sent_by={user_id}"
    )

    return success_response({
        'message': f'Announcement sent to {sent} user(s)',
        'announcementId': announcement_id,
        'audience': audience,
        'sent': sent,
    }, status_code=201)


def handle_list_announcements(user_id: str, query_params: Dict, event: Dict) -> Dict:
    """
    GET /api/notifications/announcements
    Admin-only: list past announcements (one record per announcement, not per user).
    Scans for notificationType='announcement' and deduplicates by announcementId.
    """
    if not _is_admin(event):
        raise AuthenticationError('Admin role required to view announcements')

    table = dynamodb.Table(NOTIFICATIONS_TABLE)
    response = table.scan(
        FilterExpression='notificationType = :t',
        ExpressionAttributeValues={':t': 'announcement'},
        ProjectionExpression='announcementId, title, #msg, #tp, audience, sentBy, createdAt',
        ExpressionAttributeNames={'#msg': 'message', '#tp': 'type'},
    )

    # Deduplicate — one entry per announcementId (keep earliest createdAt record)
    seen: Dict[str, Dict] = {}
    for item in response.get('Items', []):
        aid = item.get('announcementId', '')
        if aid not in seen or item.get('createdAt', '') < seen[aid].get('createdAt', ''):
            seen[aid] = item

    announcements = sorted(seen.values(), key=lambda x: x.get('createdAt', ''), reverse=True)

    return success_response({'announcements': announcements, 'count': len(announcements)})
