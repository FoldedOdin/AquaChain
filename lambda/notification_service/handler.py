"""
Multi-Channel Notification Service Lambda for AquaChain System
Handles SMS, email, and push notifications with rate limiting and delivery tracking
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from botocore.exceptions import ClientError

# Add shared utilities to path
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging and consent checker
from structured_logger import get_logger
from consent_checker import check_marketing_consent, check_analytics_consent

# Configure structured logging
logger = get_logger(__name__, service='notification-service')

# Initialize AWS clients
sns_client = boto3.client('sns')
ses_client = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm')

# Environment variables
USERS_TABLE = 'aquachain-users'
NOTIFICATIONS_TABLE = 'aquachain-notifications'
RATE_LIMIT_TABLE = 'aquachain-rate-limits'
SES_FROM_EMAIL = 'alerts@aquachain.io'
SES_CONFIGURATION_SET = 'aquachain-notifications'

# Rate limiting settings
SMS_RATE_LIMIT = {
    'max_per_hour': 10,  # Max 10 SMS per hour per user
    'max_per_day': 50    # Max 50 SMS per day per user
}

EMAIL_RATE_LIMIT = {
    'max_per_hour': 50,  # Max 50 emails per hour per user
    'max_per_day': 200   # Max 200 emails per day per user
}

PUSH_RATE_LIMIT = {
    'max_per_hour': 100,  # Max 100 push notifications per hour per user
    'max_per_day': 500    # Max 500 push notifications per day per user
}

class NotificationError(Exception):
    """Custom exception for notification errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for multi-channel notifications
    """
    try:
        logger.info(f"Processing notification request: {json.dumps(event)}")
        
        action = event.get('action')
        
        if action == 'send_alert':
            return handle_alert_notification(event['alert'])
        elif action == 'send_service_update':
            return handle_service_notification(event['serviceUpdate'])
        elif action == 'send_system_notification':
            return handle_system_notification(event['systemNotification'])
        else:
            raise NotificationError(f"Unknown action: {action}")
        
    except Exception as e:
        logger.error(f"Notification service error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def handle_alert_notification(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle water quality alert notifications
    """
    try:
        device_id = alert['deviceId']
        alert_level = alert['alertLevel']
        
        # Get users associated with the device
        users = get_device_users(device_id)
        
        if not users:
            logger.warning(f"No users found for device {device_id}")
            return create_success_response("No users to notify")
        
        notification_results = []
        
        for user in users:
            user_id = user['userId']
            preferences = user.get('preferences', {}).get('notifications', {})
            
            # Create notification record
            notification = create_notification_record(
                user_id=user_id,
                notification_type='water_quality_alert',
                alert_level=alert_level,
                content=alert,
                channels=get_enabled_channels(preferences, alert_level)
            )
            
            # Send notifications through enabled channels
            channel_results = send_multi_channel_notification(user, notification)
            notification_results.extend(channel_results)
        
        return create_success_response(f"Alert notifications sent", notification_results)
        
    except Exception as e:
        logger.error(f"Error handling alert notification: {e}")
        raise NotificationError(f"Alert notification failed: {e}")

def handle_service_notification(service_update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle service request update notifications
    """
    try:
        consumer_id = service_update['consumerId']
        technician_id = service_update.get('technicianId')
        update_type = service_update['updateType']
        
        notification_results = []
        
        # Notify consumer
        consumer = get_user_by_id(consumer_id)
        if consumer:
            consumer_notification = create_notification_record(
                user_id=consumer_id,
                notification_type='service_update',
                alert_level='info',
                content=service_update,
                channels=['push', 'email']  # Service updates via push and email
            )
            
            consumer_results = send_multi_channel_notification(consumer, consumer_notification)
            notification_results.extend(consumer_results)
        
        # Notify technician if assigned
        if technician_id:
            technician = get_user_by_id(technician_id)
            if technician:
                technician_notification = create_notification_record(
                    user_id=technician_id,
                    notification_type='service_assignment',
                    alert_level='info',
                    content=service_update,
                    channels=['push', 'sms']  # Technician gets push and SMS
                )
                
                technician_results = send_multi_channel_notification(technician, technician_notification)
                notification_results.extend(technician_results)
        
        return create_success_response("Service notifications sent", notification_results)
        
    except Exception as e:
        logger.error(f"Error handling service notification: {e}")
        raise NotificationError(f"Service notification failed: {e}")

def handle_system_notification(system_notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle system-wide notifications (admin alerts, maintenance, etc.)
    """
    try:
        target_role = system_notification.get('targetRole', 'administrator')
        notification_type = system_notification['notificationType']
        
        # Get users with target role
        users = get_users_by_role(target_role)
        
        notification_results = []
        
        for user in users:
            notification = create_notification_record(
                user_id=user['userId'],
                notification_type=notification_type,
                alert_level='critical',
                content=system_notification,
                channels=['push', 'email', 'sms']  # All channels for system notifications
            )
            
            channel_results = send_multi_channel_notification(user, notification)
            notification_results.extend(channel_results)
        
        return create_success_response("System notifications sent", notification_results)
        
    except Exception as e:
        logger.error(f"Error handling system notification: {e}")
        raise NotificationError(f"System notification failed: {e}")

def get_device_users(device_id: str) -> List[Dict[str, Any]]:
    """
    Get users associated with a specific device
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        response = table.scan(
            FilterExpression='contains(deviceIds, :deviceId)',
            ExpressionAttributeValues={
                ':deviceId': device_id
            }
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting device users: {e}")
        return []

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user by user ID
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        response = table.get_item(Key={'userId': user_id})
        return response.get('Item')
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None

def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Get all users with a specific role
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        response = table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': role}
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting users by role {role}: {e}")
        return []

def get_enabled_channels(preferences: Dict[str, Any], alert_level: str) -> List[str]:
    """
    Get enabled notification channels based on user preferences and alert level
    """
    channels = []
    
    # Default preferences if not specified
    default_preferences = {
        'push': True,
        'email': True,
        'sms': alert_level == 'critical'  # SMS only for critical alerts by default
    }
    
    # Merge with user preferences
    effective_preferences = {**default_preferences, **preferences}
    
    if effective_preferences.get('push', False):
        channels.append('push')
    
    if effective_preferences.get('email', False):
        channels.append('email')
    
    if effective_preferences.get('sms', False):
        channels.append('sms')
    
    return channels

def create_notification_record(user_id: str, notification_type: str, alert_level: str,
                             content: Dict[str, Any], channels: List[str]) -> Dict[str, Any]:
    """
    Create notification record for tracking and delivery
    """
    notification_id = f"{user_id}:{int(time.time() * 1000)}"
    
    notification = {
        'notificationId': notification_id,
        'userId': user_id,
        'notificationType': notification_type,
        'alertLevel': alert_level,
        'content': content,
        'channels': channels,
        'status': 'pending',
        'createdAt': datetime.utcnow().isoformat(),
        'deliveryResults': {},
        'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
    }
    
    # Store notification record
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        table.put_item(Item=notification)
    except Exception as e:
        logger.warning(f"Error storing notification record: {e}")
    
    return notification

def send_multi_channel_notification(user: Dict[str, Any], 
                                   notification: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Send notification through multiple channels
    """
    results = []
    channels = notification['channels']
    
    for channel in channels:
        try:
            # Check rate limits
            if not check_rate_limit(user['userId'], channel):
                logger.warning(f"Rate limit exceeded for user {user['userId']} on channel {channel}")
                results.append({
                    'channel': channel,
                    'status': 'rate_limited',
                    'message': 'Rate limit exceeded'
                })
                continue
            
            # Send notification based on channel
            if channel == 'push':
                result = send_push_notification(user, notification)
            elif channel == 'email':
                result = send_email_notification(user, notification)
            elif channel == 'sms':
                result = send_sms_notification(user, notification)
            else:
                result = {'status': 'error', 'message': f'Unknown channel: {channel}'}
            
            result['channel'] = channel
            results.append(result)
            
            # Update rate limit counter
            update_rate_limit_counter(user['userId'], channel)
            
        except Exception as e:
            logger.error(f"Error sending {channel} notification to user {user['userId']}: {e}")
            results.append({
                'channel': channel,
                'status': 'error',
                'message': str(e)
            })
    
    # Update notification record with results
    update_notification_results(notification['notificationId'], results)
    
    return results

def send_push_notification(user: Dict[str, Any], notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send push notification via SNS
    """
    try:
        # Get user's device endpoints from user profile
        device_endpoints = user.get('deviceEndpoints', [])
        
        if not device_endpoints:
            return {'status': 'skipped', 'message': 'No device endpoints registered'}
        
        content = notification['content']
        notification_type = notification['notificationType']
        
        # Create push notification message
        message = create_push_message(content, notification_type)
        
        successful_sends = 0
        failed_sends = 0
        
        for endpoint in device_endpoints:
            try:
                response = sns_client.publish(
                    TargetArn=endpoint['endpointArn'],
                    Message=json.dumps({
                        'default': message['body'],
                        'GCM': json.dumps({
                            'data': {
                                'title': message['title'],
                                'body': message['body'],
                                'notificationType': notification_type,
                                'alertLevel': notification['alertLevel']
                            }
                        }),
                        'APNS': json.dumps({
                            'aps': {
                                'alert': {
                                    'title': message['title'],
                                    'body': message['body']
                                },
                                'badge': 1,
                                'sound': 'default'
                            },
                            'notificationType': notification_type,
                            'alertLevel': notification['alertLevel']
                        })
                    }),
                    MessageStructure='json'
                )
                successful_sends += 1
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'EndpointDisabled':
                    # Remove disabled endpoint
                    logger.info(f"Removing disabled endpoint: {endpoint['endpointArn']}")
                    remove_device_endpoint(user['userId'], endpoint['endpointArn'])
                failed_sends += 1
        
        if successful_sends > 0:
            return {
                'status': 'success',
                'message': f'Push notification sent to {successful_sends} devices',
                'successful': successful_sends,
                'failed': failed_sends
            }
        else:
            return {
                'status': 'failed',
                'message': 'No successful push notifications sent'
            }
        
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return {'status': 'error', 'message': str(e)}

def send_email_notification(user: Dict[str, Any], notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email notification via SES
    """
    try:
        email = user.get('email')
        if not email:
            return {'status': 'skipped', 'message': 'No email address'}
        
        content = notification['content']
        notification_type = notification['notificationType']
        
        # Check consent for marketing emails
        if notification_type in ['marketing', 'promotional', 'newsletter']:
            user_id = user.get('userId')
            if user_id and not check_marketing_consent(user_id):
                logger.info(f"Skipping marketing email for user {user_id} - no consent")
                return {'status': 'skipped', 'message': 'User has not consented to marketing communications'}
        
        # Create email content
        email_content = create_email_content(content, notification_type)
        
        # Send email via SES
        response = ses_client.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': email_content['subject'], 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': email_content['html_body'], 'Charset': 'UTF-8'},
                    'Text': {'Data': email_content['text_body'], 'Charset': 'UTF-8'}
                }
            },
            ConfigurationSetName=SES_CONFIGURATION_SET,
            Tags=[
                {'Name': 'NotificationType', 'Value': notification_type},
                {'Name': 'AlertLevel', 'Value': notification['alertLevel']},
                {'Name': 'UserId', 'Value': user['userId']}
            ]
        )
        
        return {
            'status': 'success',
            'message': 'Email sent successfully',
            'messageId': response['MessageId']
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'MessageRejected':
            return {'status': 'rejected', 'message': 'Email rejected by SES'}
        elif error_code == 'MailFromDomainNotVerified':
            return {'status': 'error', 'message': 'Sender domain not verified'}
        else:
            return {'status': 'error', 'message': f'SES error: {error_code}'}
    except Exception as e:
        logger.error(f"Error sending email notification: {e}")
        return {'status': 'error', 'message': str(e)}

def send_sms_notification(user: Dict[str, Any], notification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send SMS notification via SNS
    """
    try:
        phone = user.get('profile', {}).get('phone')
        if not phone:
            return {'status': 'skipped', 'message': 'No phone number'}
        
        content = notification['content']
        notification_type = notification['notificationType']
        
        # Create SMS message
        sms_message = create_sms_message(content, notification_type)
        
        # Send SMS via SNS
        response = sns_client.publish(
            PhoneNumber=phone,
            Message=sms_message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': 'AquaChain'},
                'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Transactional'}
            }
        )
        
        return {
            'status': 'success',
            'message': 'SMS sent successfully',
            'messageId': response['MessageId']
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidParameter':
            return {'status': 'error', 'message': 'Invalid phone number'}
        else:
            return {'status': 'error', 'message': f'SNS error: {error_code}'}
    except Exception as e:
        logger.error(f"Error sending SMS notification: {e}")
        return {'status': 'error', 'message': str(e)}

def create_push_message(content: Dict[str, Any], notification_type: str) -> Dict[str, str]:
    """
    Create push notification message content
    """
    if notification_type == 'water_quality_alert':
        alert_level = content['alertLevel']
        device_id = content['deviceId']
        wqi = content['wqi']
        
        if alert_level == 'critical':
            title = "🚨 Critical Water Quality Alert"
            body = f"Device {device_id}: Water quality is unsafe (WQI: {wqi:.1f}). Take immediate action!"
        else:
            title = "⚠️ Water Quality Warning"
            body = f"Device {device_id}: Water quality needs attention (WQI: {wqi:.1f})"
    
    elif notification_type == 'service_update':
        update_type = content['updateType']
        if update_type == 'assigned':
            title = "🔧 Technician Assigned"
            body = f"A technician has been assigned to your service request"
        elif update_type == 'en_route':
            title = "🚗 Technician En Route"
            body = f"Your technician is on the way. ETA: {content.get('eta', 'Unknown')}"
        else:
            title = "📋 Service Update"
            body = f"Your service request has been updated: {update_type}"
    
    else:
        title = "AquaChain Notification"
        body = "You have a new notification from AquaChain"
    
    return {'title': title, 'body': body}

def create_email_content(content: Dict[str, Any], notification_type: str) -> Dict[str, str]:
    """
    Create email notification content
    """
    if notification_type == 'water_quality_alert':
        alert_level = content['alertLevel']
        device_id = content['deviceId']
        wqi = content['wqi']
        alert_reasons = content.get('alertReasons', [])
        
        subject = f"{'🚨 CRITICAL' if alert_level == 'critical' else '⚠️ WARNING'} Water Quality Alert - Device {device_id}"
        
        html_body = f"""
        <html>
        <body>
            <h2 style="color: {'#dc3545' if alert_level == 'critical' else '#ffc107'};">
                {alert_level.title()} Water Quality Alert
            </h2>
            <p><strong>Device:</strong> {device_id}</p>
            <p><strong>Water Quality Index:</strong> {wqi:.1f}</p>
            <p><strong>Alert Time:</strong> {content['timestamp']}</p>
            
            <h3>Alert Reasons:</h3>
            <ul>
                {''.join(f'<li>{reason}</li>' for reason in alert_reasons)}
            </ul>
            
            <p style="color: {'#dc3545' if alert_level == 'critical' else '#856404'};">
                {'Please take immediate action to ensure water safety.' if alert_level == 'critical' 
                 else 'Please monitor your water quality closely.'}
            </p>
            
        </body>
        </html>
        """
        
        text_body = f"""
        {alert_level.title()} Water Quality Alert
        
        Device: {device_id}
        Water Quality Index: {wqi:.1f}
        Alert Time: {content['timestamp']}
        
        Alert Reasons:
        {chr(10).join(f'- {reason}' for reason in alert_reasons)}
        
        {'Please take immediate action to ensure water safety.' if alert_level == 'critical' 
         else 'Please monitor your water quality closely.'}
        
        View your dashboard: https://app.aquachain.io/dashboard
        """
    
    else:
        subject = "AquaChain Notification"
        html_body = "<html><body><p>You have a new notification from AquaChain.</p></body></html>"
        text_body = "You have a new notification from AquaChain."
    
    return {
        'subject': subject,
        'html_body': html_body,
        'text_body': text_body
    }

def create_sms_message(content: Dict[str, Any], notification_type: str) -> str:
    """
    Create SMS notification message (160 character limit)
    """
    if notification_type == 'water_quality_alert':
        alert_level = content['alertLevel']
        device_id = content['deviceId']
        wqi = content['wqi']
        
        if alert_level == 'critical':
            message = f"🚨 CRITICAL: Device {device_id} water unsafe (WQI: {wqi:.1f}). Check immediately!"
        else:
            message = f"⚠️ WARNING: Device {device_id} water quality issue (WQI: {wqi:.1f}). Monitor closely."
    
    elif notification_type == 'service_assignment':
        message = f"🔧 AquaChain: Technician assigned to your service request. Check app for details."
    
    else:
        message = "AquaChain: You have a new notification. Check the app for details."
    
    # Ensure message is within SMS limits
    return message[:160]

def check_rate_limit(user_id: str, channel: str) -> bool:
    """
    Check if user has exceeded rate limits for the channel
    """
    try:
        table = dynamodb.Table(RATE_LIMIT_TABLE)
        current_time = datetime.utcnow()
        
        # Get rate limit settings for channel
        if channel == 'sms':
            limits = SMS_RATE_LIMIT
        elif channel == 'email':
            limits = EMAIL_RATE_LIMIT
        elif channel == 'push':
            limits = PUSH_RATE_LIMIT
        else:
            return True  # No limits for unknown channels
        
        # Check hourly limit
        hour_key = f"{user_id}:{channel}:{current_time.strftime('%Y%m%d%H')}"
        hour_response = table.get_item(Key={'limitKey': hour_key})
        hour_count = hour_response.get('Item', {}).get('count', 0)
        
        if hour_count >= limits['max_per_hour']:
            return False
        
        # Check daily limit
        day_key = f"{user_id}:{channel}:{current_time.strftime('%Y%m%d')}"
        day_response = table.get_item(Key={'limitKey': day_key})
        day_count = day_response.get('Item', {}).get('count', 0)
        
        if day_count >= limits['max_per_day']:
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error checking rate limit: {e}")
        return True  # Allow if check fails

def update_rate_limit_counter(user_id: str, channel: str) -> None:
    """
    Update rate limit counters for user and channel
    """
    try:
        table = dynamodb.Table(RATE_LIMIT_TABLE)
        current_time = datetime.utcnow()
        
        # Update hourly counter
        hour_key = f"{user_id}:{channel}:{current_time.strftime('%Y%m%d%H')}"
        hour_ttl = int((current_time + timedelta(hours=2)).timestamp())
        
        table.update_item(
            Key={'limitKey': hour_key},
            UpdateExpression='ADD #count :inc SET #ttl = :ttl',
            ExpressionAttributeNames={'#count': 'count', '#ttl': 'ttl'},
            ExpressionAttributeValues={':inc': 1, ':ttl': hour_ttl}
        )
        
        # Update daily counter
        day_key = f"{user_id}:{channel}:{current_time.strftime('%Y%m%d')}"
        day_ttl = int((current_time + timedelta(days=2)).timestamp())
        
        table.update_item(
            Key={'limitKey': day_key},
            UpdateExpression='ADD #count :inc SET #ttl = :ttl',
            ExpressionAttributeNames={'#count': 'count', '#ttl': 'ttl'},
            ExpressionAttributeValues={':inc': 1, ':ttl': day_ttl}
        )
        
    except Exception as e:
        logger.warning(f"Error updating rate limit counter: {e}")

def update_notification_results(notification_id: str, results: List[Dict[str, Any]]) -> None:
    """
    Update notification record with delivery results
    """
    try:
        table = dynamodb.Table(NOTIFICATIONS_TABLE)
        
        # Determine overall status
        successful_channels = [r for r in results if r['status'] == 'success']
        failed_channels = [r for r in results if r['status'] in ['error', 'failed']]
        
        if successful_channels:
            overall_status = 'delivered' if not failed_channels else 'partial'
        else:
            overall_status = 'failed'
        
        table.update_item(
            Key={'notificationId': notification_id},
            UpdateExpression='SET #status = :status, deliveryResults = :results, deliveredAt = :deliveredAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': overall_status,
                ':results': {r['channel']: r for r in results},
                ':deliveredAt': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.warning(f"Error updating notification results: {e}")

def remove_device_endpoint(user_id: str, endpoint_arn: str) -> None:
    """
    Remove disabled device endpoint from user profile
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        
        # Get current user data
        response = table.get_item(Key={'userId': user_id})
        user = response.get('Item')
        
        if user and 'deviceEndpoints' in user:
            # Filter out the disabled endpoint
            updated_endpoints = [
                ep for ep in user['deviceEndpoints'] 
                if ep.get('endpointArn') != endpoint_arn
            ]
            
            # Update user record
            table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET deviceEndpoints = :endpoints',
                ExpressionAttributeValues={':endpoints': updated_endpoints}
            )
            
            logger.info(f"Removed disabled endpoint {endpoint_arn} from user {user_id}")
        
    except Exception as e:
        logger.warning(f"Error removing device endpoint: {e}")

def create_success_response(message: str, data: Any = None) -> Dict[str, Any]:
    """
    Create standardized success response
    """
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
    
    if data:
        body = json.loads(response['body'])
        body['data'] = data
        response['body'] = json.dumps(body)
    
    return response