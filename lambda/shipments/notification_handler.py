"""
Lambda function to handle shipment notifications triggered by DynamoDB Streams

This Lambda function:
1. Subscribes to Shipments table DynamoDB Stream
2. Detects status changes from stream events
3. Routes to appropriate notification function based on status
4. Sends email, SMS, and WebSocket notifications

Requirements: 1.5, 4.1, 13.1, 13.2, 13.3, 13.4
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from structured_logger import get_logger

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
ses = boto3.client('ses')
apigateway_client = boto3.client('apigatewaymanagementapi')

# Environment variables
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
CONNECTIONS_TABLE = os.environ.get('CONNECTIONS_TABLE', 'aquachain-websocket-connections')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'noreply@aquachain.com')
WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_ENDPOINT', '')

# Initialize logger
logger = get_logger(__name__, service='shipment-notifications')


def handler(event, context):
    """
    Process DynamoDB Stream events from Shipments table
    
    Detects status changes and routes to appropriate notification handlers
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    try:
        logger.info(
            "Processing DynamoDB Stream event",
            request_id=request_id,
            record_count=len(event.get('Records', []))
        )
        
        # Process each record from the stream
        for record in event.get('Records', []):
            process_stream_record(record, request_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'processed': len(event.get('Records', []))})
        }
        
    except Exception as e:
        logger.error(
            f"Error processing stream event: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        # Don't raise - we don't want to block the stream
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_stream_record(record: Dict[str, Any], request_id: str) -> None:
    """
    Process a single DynamoDB Stream record
    
    Detects status changes and routes to appropriate notification function
    """
    try:
        event_name = record['eventName']
        
        # Only process INSERT and MODIFY events
        if event_name not in ['INSERT', 'MODIFY']:
            return
        
        # Extract old and new images
        old_image = record.get('dynamodb', {}).get('OldImage')
        new_image = record.get('dynamodb', {}).get('NewImage')
        
        if not new_image:
            return
        
        # Convert DynamoDB format to Python dict
        new_shipment = convert_dynamodb_to_dict(new_image)
        old_shipment = convert_dynamodb_to_dict(old_image) if old_image else {}
        
        shipment_id = new_shipment.get('shipment_id')
        new_status = new_shipment.get('internal_status')
        old_status = old_shipment.get('internal_status')
        
        logger.info(
            "Processing shipment stream record",
            request_id=request_id,
            shipment_id=shipment_id,
            event_name=event_name,
            old_status=old_status,
            new_status=new_status
        )
        
        # Detect status change
        if event_name == 'INSERT' or (event_name == 'MODIFY' and new_status != old_status):
            # Status changed - route to appropriate handler
            route_notification(new_shipment, new_status, request_id)
        
    except Exception as e:
        logger.error(
            f"Error processing stream record: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )


def route_notification(shipment: Dict[str, Any], status: str, request_id: str) -> None:
    """
    Route to appropriate notification function based on status
    
    Requirements: 1.5, 4.1, 13.1, 13.2, 13.3, 13.4
    """
    try:
        shipment_id = shipment.get('shipment_id')
        order_id = shipment.get('order_id')
        
        logger.info(
            f"Routing notification for status: {status}",
            request_id=request_id,
            shipment_id=shipment_id,
            status=status
        )
        
        # Fetch order details for consumer/technician info
        order = fetch_order_details(order_id)
        
        if not order:
            logger.warning(
                f"Order not found for shipment {shipment_id}",
                request_id=request_id,
                order_id=order_id
            )
            return
        
        # Route based on status
        if status == 'shipment_created':
            send_shipment_created_notifications(shipment, order, request_id)
        elif status == 'out_for_delivery':
            send_out_for_delivery_notifications(shipment, order, request_id)
        elif status == 'delivered':
            send_delivery_confirmation_notifications(shipment, order, request_id)
        elif status == 'delivery_failed':
            send_delivery_failed_notifications(shipment, order, request_id)
        else:
            # For other statuses, send WebSocket update only
            send_websocket_notification(shipment, order, status, request_id)
        
    except Exception as e:
        logger.error(
            f"Error routing notification: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )


def fetch_order_details(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch order details from DeviceOrders table
    """
    try:
        orders_table = dynamodb.Table(ORDERS_TABLE)
        response = orders_table.get_item(Key={'orderId': order_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Failed to fetch order details: {str(e)}", order_id=order_id)
        return None


def send_shipment_created_notifications(shipment: Dict, order: Dict, request_id: str) -> None:
    """
    Send notifications when shipment is created
    
    - Email to Consumer with tracking info
    - WebSocket update
    
    Requirements: 13.1
    """
    try:
        shipment_id = shipment['shipment_id']
        tracking_number = shipment['tracking_number']
        estimated_delivery = shipment.get('estimated_delivery', 'TBD')
        courier_name = shipment.get('courier_name', 'Courier')
        
        consumer_email = order.get('consumerEmail', order.get('consumer_email'))
        consumer_name = order.get('consumerName', order.get('consumer_name', 'Customer'))
        
        logger.info(
            "Sending shipment created notifications",
            request_id=request_id,
            shipment_id=shipment_id
        )
        
        # Send email notification
        if consumer_email and SES_FROM_EMAIL:
            send_email_notification(
                to_email=consumer_email,
                subject='Your Device Has Been Shipped!',
                body_html=format_shipment_created_email(
                    consumer_name, tracking_number, courier_name, estimated_delivery
                ),
                body_text=f"Your device has been shipped! Tracking number: {tracking_number}"
            )
        
        # Send WebSocket notification
        send_websocket_notification(shipment, order, 'shipment_created', request_id)
        
    except Exception as e:
        logger.error(
            f"Error sending shipment created notifications: {str(e)}",
            request_id=request_id
        )


def send_out_for_delivery_notifications(shipment: Dict, order: Dict, request_id: str) -> None:
    """
    Send notifications when package is out for delivery
    
    - Email to Consumer with ETA
    - SMS to Consumer
    - WebSocket update
    
    Requirements: 13.2
    """
    try:
        shipment_id = shipment['shipment_id']
        tracking_number = shipment['tracking_number']
        estimated_delivery = shipment.get('estimated_delivery', 'today')
        
        consumer_email = order.get('consumerEmail', order.get('consumer_email'))
        consumer_phone = order.get('consumerPhone', order.get('consumer_phone'))
        consumer_name = order.get('consumerName', order.get('consumer_name', 'Customer'))
        
        logger.info(
            "Sending out for delivery notifications",
            request_id=request_id,
            shipment_id=shipment_id
        )
        
        # Send email notification
        if consumer_email and SES_FROM_EMAIL:
            send_email_notification(
                to_email=consumer_email,
                subject='Your Device is Out for Delivery!',
                body_html=format_out_for_delivery_email(
                    consumer_name, tracking_number, estimated_delivery
                ),
                body_text=f"Your device is out for delivery! Expected: {estimated_delivery}"
            )
        
        # Send SMS notification
        if consumer_phone and SNS_TOPIC_ARN:
            send_sms_notification(
                phone_number=consumer_phone,
                message=f"Your AquaChain device is out for delivery! Track: {tracking_number}"
            )
        
        # Send WebSocket notification
        send_websocket_notification(shipment, order, 'out_for_delivery', request_id)
        
    except Exception as e:
        logger.error(
            f"Error sending out for delivery notifications: {str(e)}",
            request_id=request_id
        )


def send_delivery_confirmation_notifications(shipment: Dict, order: Dict, request_id: str) -> None:
    """
    Send notifications when delivery is confirmed
    
    - Email to Consumer
    - SMS to Consumer
    - WebSocket update
    - Notification to Technician
    
    Requirements: 4.1, 13.3
    """
    try:
        shipment_id = shipment['shipment_id']
        tracking_number = shipment['tracking_number']
        delivered_at = shipment.get('delivered_at', datetime.utcnow().isoformat())
        
        consumer_email = order.get('consumerEmail', order.get('consumer_email'))
        consumer_phone = order.get('consumerPhone', order.get('consumer_phone'))
        consumer_name = order.get('consumerName', order.get('consumer_name', 'Customer'))
        technician_id = order.get('technicianId', order.get('technician_id'))
        
        logger.info(
            "Sending delivery confirmation notifications",
            request_id=request_id,
            shipment_id=shipment_id
        )
        
        # Send email to consumer
        if consumer_email and SES_FROM_EMAIL:
            send_email_notification(
                to_email=consumer_email,
                subject='Your Device Has Been Delivered!',
                body_html=format_delivery_confirmation_email(
                    consumer_name, tracking_number, delivered_at
                ),
                body_text=f"Your device has been delivered! Tracking: {tracking_number}"
            )
        
        # Send SMS to consumer
        if consumer_phone and SNS_TOPIC_ARN:
            send_sms_notification(
                phone_number=consumer_phone,
                message=f"Your AquaChain device has been delivered! Installation will be scheduled soon."
            )
        
        # Send WebSocket notification
        send_websocket_notification(shipment, order, 'delivered', request_id)
        
        # Notify technician if assigned
        if technician_id:
            notify_technician_delivery(shipment, order, technician_id, request_id)
        
    except Exception as e:
        logger.error(
            f"Error sending delivery confirmation notifications: {str(e)}",
            request_id=request_id
        )


def send_delivery_failed_notifications(shipment: Dict, order: Dict, request_id: str) -> None:
    """
    Send notifications when delivery fails
    
    - Email to Consumer with next steps
    - WebSocket update
    
    Requirements: 13.4
    """
    try:
        shipment_id = shipment['shipment_id']
        tracking_number = shipment['tracking_number']
        retry_config = shipment.get('retry_config', {})
        retry_count = retry_config.get('retry_count', 0)
        max_retries = retry_config.get('max_retries', 3)
        
        consumer_email = order.get('consumerEmail', order.get('consumer_email'))
        consumer_name = order.get('consumerName', order.get('consumer_name', 'Customer'))
        
        logger.info(
            "Sending delivery failed notifications",
            request_id=request_id,
            shipment_id=shipment_id,
            retry_count=retry_count
        )
        
        # Send email notification
        if consumer_email and SES_FROM_EMAIL:
            send_email_notification(
                to_email=consumer_email,
                subject='Delivery Attempt Failed - Action Required',
                body_html=format_delivery_failed_email(
                    consumer_name, tracking_number, retry_count, max_retries
                ),
                body_text=f"Delivery attempt failed. Tracking: {tracking_number}. We will retry."
            )
        
        # Send WebSocket notification
        send_websocket_notification(shipment, order, 'delivery_failed', request_id)
        
    except Exception as e:
        logger.error(
            f"Error sending delivery failed notifications: {str(e)}",
            request_id=request_id
        )


def notify_technician_delivery(shipment: Dict, order: Dict, technician_id: str, request_id: str) -> None:
    """
    Notify technician when device is delivered
    
    Requirements: 4.1
    """
    try:
        shipment_id = shipment['shipment_id']
        order_id = shipment['order_id']
        
        logger.info(
            "Notifying technician of delivery",
            request_id=request_id,
            shipment_id=shipment_id,
            technician_id=technician_id
        )
        
        # Send SNS notification (can be routed to technician's email/SMS)
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Device Delivered - Ready for Installation',
                Message=json.dumps({
                    'eventType': 'TECHNICIAN_DEVICE_DELIVERED',
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'technician_id': technician_id,
                    'consumer_name': order.get('consumerName', order.get('consumer_name')),
                    'consumer_address': shipment.get('destination', {}).get('address'),
                    'consumer_phone': order.get('consumerPhone', order.get('consumer_phone')),
                    'message': 'Device has been delivered. You can now proceed with installation.',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
            )
        
    except Exception as e:
        logger.error(
            f"Error notifying technician: {str(e)}",
            request_id=request_id
        )


# ============================================================================
# Email Notification Functions (SES)
# ============================================================================

def send_email_notification(to_email: str, subject: str, body_html: str, body_text: str) -> None:
    """
    Send email notification via SES
    
    Requirements: 13.1, 13.3, 13.4
    """
    try:
        if not SES_FROM_EMAIL:
            logger.warning("SES_FROM_EMAIL not configured, skipping email")
            return
        
        logger.info(f"Sending email to {to_email}: {subject}")
        
        ses.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': body_html},
                    'Text': {'Data': body_text}
                }
            }
        )
        
        logger.info(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}", to_email=to_email)


def format_shipment_created_email(name: str, tracking: str, courier: str, eta: str) -> str:
    """Format HTML email for shipment created"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0066cc;">Your Device Has Been Shipped! 📦</h2>
            <p>Hi {name},</p>
            <p>Great news! Your AquaChain water quality monitoring device has been shipped and is on its way to you.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Tracking Number:</strong> {tracking}</p>
                <p style="margin: 5px 0;"><strong>Courier:</strong> {courier}</p>
                <p style="margin: 5px 0;"><strong>Estimated Delivery:</strong> {eta}</p>
            </div>
            
            <p>You can track your shipment using the tracking number above on the {courier} website.</p>
            <p>Once your device arrives, our technician will contact you to schedule the installation.</p>
            
            <p style="margin-top: 30px;">Best regards,<br>The AquaChain Team</p>
        </div>
    </body>
    </html>
    """


def format_out_for_delivery_email(name: str, tracking: str, eta: str) -> str:
    """Format HTML email for out for delivery"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #00cc66;">Your Device is Out for Delivery! 🚛</h2>
            <p>Hi {name},</p>
            <p>Your AquaChain device is out for delivery and should arrive soon!</p>
            
            <div style="background-color: #f0f9ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #00cc66;">
                <p style="margin: 5px 0;"><strong>Tracking Number:</strong> {tracking}</p>
                <p style="margin: 5px 0;"><strong>Expected Delivery:</strong> {eta}</p>
            </div>
            
            <p>Please ensure someone is available to receive the package.</p>
            <p>After delivery, our technician will contact you to schedule the installation.</p>
            
            <p style="margin-top: 30px;">Best regards,<br>The AquaChain Team</p>
        </div>
    </body>
    </html>
    """


def format_delivery_confirmation_email(name: str, tracking: str, delivered_at: str) -> str:
    """Format HTML email for delivery confirmation"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #00cc66;">Your Device Has Been Delivered! ✅</h2>
            <p>Hi {name},</p>
            <p>Great news! Your AquaChain water quality monitoring device has been successfully delivered.</p>
            
            <div style="background-color: #f0fff4; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #00cc66;">
                <p style="margin: 5px 0;"><strong>Tracking Number:</strong> {tracking}</p>
                <p style="margin: 5px 0;"><strong>Delivered At:</strong> {delivered_at}</p>
            </div>
            
            <h3 style="color: #0066cc;">What's Next?</h3>
            <p>Our technician will contact you within 24 hours to schedule the installation of your device.</p>
            <p>The installation typically takes 30-45 minutes and includes:</p>
            <ul>
                <li>Device setup and configuration</li>
                <li>Connection to your water supply</li>
                <li>Mobile app setup and training</li>
                <li>Initial water quality assessment</li>
            </ul>
            
            <p style="margin-top: 30px;">Best regards,<br>The AquaChain Team</p>
        </div>
    </body>
    </html>
    """


def format_delivery_failed_email(name: str, tracking: str, retry_count: int, max_retries: int) -> str:
    """Format HTML email for delivery failure"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #cc6600;">Delivery Attempt Failed - Action Required</h2>
            <p>Hi {name},</p>
            <p>We attempted to deliver your AquaChain device, but the delivery was unsuccessful.</p>
            
            <div style="background-color: #fff5f0; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #cc6600;">
                <p style="margin: 5px 0;"><strong>Tracking Number:</strong> {tracking}</p>
                <p style="margin: 5px 0;"><strong>Attempt:</strong> {retry_count} of {max_retries}</p>
            </div>
            
            <h3 style="color: #cc6600;">What You Need to Do:</h3>
            <ul>
                <li>Ensure someone is available to receive the package</li>
                <li>Verify your delivery address is correct</li>
                <li>Check for any access restrictions</li>
                <li>Contact us if you need to update delivery instructions</li>
            </ul>
            
            <p>We will attempt redelivery soon. If you have any questions, please contact our support team.</p>
            
            <p style="margin-top: 30px;">Best regards,<br>The AquaChain Team</p>
        </div>
    </body>
    </html>
    """


# ============================================================================
# SMS Notification Functions (SNS)
# ============================================================================

def send_sms_notification(phone_number: str, message: str) -> None:
    """
    Send SMS notification via SNS
    
    Requirements: 13.2, 13.3
    """
    try:
        if not phone_number:
            logger.warning("No phone number provided, skipping SMS")
            return
        
        logger.info(f"Sending SMS to {phone_number}")
        
        # Publish SMS via SNS
        sns.publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'  # High priority
                }
            }
        )
        
        logger.info(f"SMS sent successfully to {phone_number}")
        
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}", phone_number=phone_number)


# ============================================================================
# WebSocket Notification Functions
# ============================================================================

def send_websocket_notification(shipment: Dict, order: Dict, status: str, request_id: str) -> None:
    """
    Send real-time WebSocket notification to connected clients
    
    Includes shipment_id, order_id, new status
    Triggers UI refresh on client side
    
    Requirements: 13.5
    """
    try:
        if not WEBSOCKET_ENDPOINT:
            logger.warning("WEBSOCKET_ENDPOINT not configured, skipping WebSocket notification")
            return
        
        shipment_id = shipment['shipment_id']
        order_id = shipment['order_id']
        consumer_id = order.get('consumerId', order.get('consumer_id'))
        technician_id = order.get('technicianId', order.get('technician_id'))
        
        logger.info(
            "Sending WebSocket notification",
            request_id=request_id,
            shipment_id=shipment_id,
            status=status
        )
        
        # Build WebSocket message
        message = {
            'type': 'shipment_status_update',
            'shipment_id': shipment_id,
            'order_id': order_id,
            'tracking_number': shipment.get('tracking_number'),
            'internal_status': status,
            'status_display': status.replace('_', ' ').title(),
            'estimated_delivery': shipment.get('estimated_delivery'),
            'delivered_at': shipment.get('delivered_at'),
            'timeline': shipment.get('timeline', []),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Get connections for consumer
        consumer_connections = []
        if consumer_id:
            consumer_connections = get_subscribed_connections('shipment_updates', {'userId': consumer_id})
        
        # Get connections for technician
        technician_connections = []
        if technician_id:
            technician_connections = get_subscribed_connections('shipment_updates', {'technicianId': technician_id})
        
        # Get admin connections
        admin_connections = get_subscribed_connections('shipment_updates', {'role': 'admin'})
        
        # Combine all connections
        all_connections = consumer_connections + technician_connections + admin_connections
        
        if not all_connections:
            logger.info("No WebSocket connections found for shipment update")
            return
        
        # Broadcast to all connections
        results = broadcast_to_connections(all_connections, message)
        
        logger.info(
            f"WebSocket notification sent: {results['successful']} successful, {results['failed']} failed",
            request_id=request_id,
            shipment_id=shipment_id
        )
        
    except Exception as e:
        logger.error(
            f"Error sending WebSocket notification: {str(e)}",
            request_id=request_id
        )


def get_subscribed_connections(subscription_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get WebSocket connections subscribed to specific data stream with matching filters
    """
    try:
        if not CONNECTIONS_TABLE:
            return []
        
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Scan for active connections
        response = table.scan(
            FilterExpression='attribute_exists(connectionId)'
        )
        connections = response.get('Items', [])
        
        matching_connections = []
        
        for connection in connections:
            subscriptions = connection.get('subscriptions', [])
            
            for subscription in subscriptions:
                if subscription.get('type') == subscription_type:
                    # Check if filters match
                    if subscription_matches_filters(subscription.get('filters', {}), filters):
                        matching_connections.append(connection)
                        break
        
        return matching_connections
        
    except Exception as e:
        logger.error(f"Error getting subscribed connections: {str(e)}")
        return []


def subscription_matches_filters(subscription_filters: Dict[str, Any], 
                               broadcast_filters: Dict[str, Any]) -> bool:
    """
    Check if subscription filters match broadcast filters
    """
    try:
        # If no broadcast filters, match all subscriptions
        if not broadcast_filters:
            return True
        
        # Check user ID
        sub_user_id = subscription_filters.get('userId')
        broadcast_user_id = broadcast_filters.get('userId')
        
        if broadcast_user_id and sub_user_id:
            if sub_user_id != broadcast_user_id:
                return False
        
        # Check technician ID
        sub_technician_id = subscription_filters.get('technicianId')
        broadcast_technician_id = broadcast_filters.get('technicianId')
        
        if broadcast_technician_id and sub_technician_id:
            if sub_technician_id != broadcast_technician_id:
                return False
        
        # Check role
        sub_role = subscription_filters.get('role')
        broadcast_role = broadcast_filters.get('role')
        
        if broadcast_role and sub_role:
            if sub_role != broadcast_role:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error matching subscription filters: {str(e)}")
        return False


def broadcast_to_connections(connections: List[Dict[str, Any]], 
                           message: Dict[str, Any]) -> Dict[str, int]:
    """
    Send message to multiple WebSocket connections
    """
    successful = 0
    failed = 0
    stale_connections = []
    
    # Configure API Gateway Management API endpoint
    if WEBSOCKET_ENDPOINT:
        apigateway_client.meta.client.meta.endpoint_url = WEBSOCKET_ENDPOINT
    
    for connection in connections:
        connection_id = connection['connectionId']
        
        try:
            apigateway_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
            successful += 1
            
        except apigateway_client.exceptions.GoneException:
            # Connection is stale, mark for removal
            logger.info(f"Connection {connection_id} is gone, marking for removal")
            stale_connections.append(connection_id)
            failed += 1
            
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {str(e)}")
            failed += 1
    
    # Clean up stale connections
    for connection_id in stale_connections:
        remove_stale_connection(connection_id)
    
    return {'successful': successful, 'failed': failed}


def remove_stale_connection(connection_id: str) -> None:
    """
    Remove stale WebSocket connection from database
    """
    try:
        if not CONNECTIONS_TABLE:
            return
        
        table = dynamodb.Table(CONNECTIONS_TABLE)
        table.delete_item(Key={'connectionId': connection_id})
        logger.info(f"Removed stale connection: {connection_id}")
        
    except Exception as e:
        logger.warning(f"Error removing stale connection {connection_id}: {str(e)}")


# ============================================================================
# Utility Functions
# ============================================================================

def convert_dynamodb_to_dict(dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert DynamoDB item format to regular dictionary
    """
    def convert_value(value):
        if isinstance(value, dict):
            if 'S' in value:
                return value['S']
            elif 'N' in value:
                return float(value['N']) if '.' in value['N'] else int(value['N'])
            elif 'B' in value:
                return value['B']
            elif 'SS' in value:
                return value['SS']
            elif 'NS' in value:
                return [float(n) if '.' in n else int(n) for n in value['NS']]
            elif 'BS' in value:
                return value['BS']
            elif 'M' in value:
                return {k: convert_value(v) for k, v in value['M'].items()}
            elif 'L' in value:
                return [convert_value(item) for item in value['L']]
            elif 'NULL' in value:
                return None
            elif 'BOOL' in value:
                return value['BOOL']
        return value
    
    return {key: convert_value(value) for key, value in dynamodb_item.items()}
