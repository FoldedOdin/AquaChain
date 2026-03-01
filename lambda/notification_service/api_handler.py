"""
Notification API Handler for API Gateway HTTP requests
Provides REST API endpoints for notification management
"""

import json
import boto3
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

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
logger = get_logger(__name__, service='notification-api')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
NOTIFICATIONS_TABLE = os.environ.get('NOTIFICATIONS_TABLE', 'aquachain-notifications')

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
        
        elif http_method == 'PUT' and '/read' in path:
            # PUT /api/notifications/{notificationId}/read - Mark one as read
            notification_id = path_params.get('notificationId')
            if not notification_id:
                raise ValidationError('Notification ID required')
            return handle_mark_as_read(user_id, notification_id)
        
        elif http_method == 'DELETE' and path_params.get('notificationId'):
            # DELETE /api/notifications/{notificationId} - Delete notification
            notification_id = path_params.get('notificationId')
            return handle_delete_notification(user_id, notification_id)
        
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
        
        notifications = response.get('Items', [])
        
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
        
        # Create notification record
        notification_id = f"{body['userId']}:{int(datetime.utcnow().timestamp() * 1000)}"
        
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
    Get count of unread notifications for user
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Query unread notifications
        response = table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            FilterExpression='#read = :read',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':userId': user_id,
                ':read': False
            },
            Select='COUNT'
        )
        
        count = response.get('Count', 0)
        
        logger.info(f"User {user_id} has {count} unread notifications")
        return success_response({'count': count})
    
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise DatabaseError(f"Failed to get unread count: {str(e)}")


def handle_mark_as_read(user_id: str, notification_id: str) -> Dict:
    """
    Mark a specific notification as read
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Verify notification belongs to user
        response = table.get_item(Key={'notificationId': notification_id})
        notification = response.get('Item')
        
        if not notification:
            raise ResourceNotFoundError('Notification not found')
        
        if notification.get('userId') != user_id:
            raise AuthenticationError('Not authorized to modify this notification')
        
        # Mark as read
        table.update_item(
            Key={'notificationId': notification_id},
            UpdateExpression='SET #read = :read, readAt = :readAt',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':read': True,
                ':readAt': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Marked notification {notification_id} as read for user {user_id}")
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
        response = table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :userId',
            FilterExpression='#read = :read',
            ExpressionAttributeNames={'#read': 'read'},
            ExpressionAttributeValues={
                ':userId': user_id,
                ':read': False
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
        
        # Verify notification belongs to user
        response = table.get_item(Key={'notificationId': notification_id})
        notification = response.get('Item')
        
        if not notification:
            raise ResourceNotFoundError('Notification not found')
        
        if notification.get('userId') != user_id:
            raise AuthenticationError('Not authorized to delete this notification')
        
        # Delete notification
        table.delete_item(Key={'notificationId': notification_id})
        
        logger.info(f"Deleted notification {notification_id} for user {user_id}")
        return success_response({'message': 'Notification deleted'})
    
    except (ResourceNotFoundError, AuthenticationError):
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise DatabaseError(f"Failed to delete notification: {str(e)}")
