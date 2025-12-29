"""
Handle courier webhook callbacks for shipment tracking
"""
import boto3
import json
import os
from datetime import datetime
import hmac
import hashlib
from typing import Dict, Any, Optional

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'default-secret')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def handler(event, context):
    """
    Process courier webhook
    """
    try:
        # Verify webhook signature
        if not verify_webhook_signature(event):
            return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid signature'})}
        
        # Parse webhook payload
        body = json.loads(event['body'])
        courier_name = event['pathParameters'].get('courier', 'unknown')
        
        # Normalize courier-specific payload
        normalized = normalize_webhook_payload(courier_name, body)
        
        if not normalized:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid payload'})}
        
        tracking_number = normalized['tracking_number']
        courier_status = normalized['status']
        location = normalized['location']
        timestamp = normalized['timestamp']
        description = normalized['description']
        
        # Lookup shipment by tracking number
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        response = shipments_table.query(
            IndexName='tracking_number-index',
            KeyConditionExpression='tracking_number = :tracking',
            ExpressionAttributeValues={':tracking': tracking_number}
        )
        
        if not response['Items']:
            print(f"Shipment not found for tracking: {tracking_number}")
            return {'statusCode': 404, 'body': json.dumps({'error': 'Shipment not found'})}
        
        shipment = response['Items'][0]
        shipment_id = shipment['shipment_id']
        
        # Map courier status to internal status
        internal_status = map_courier_status(courier_status)
        
        # Validate state transition
        if not is_valid_transition(shipment['internal_status'], internal_status):
            print(f"Invalid transition: {shipment['internal_status']} -> {internal_status}")
            # Log but don't fail - courier might send out-of-order updates
        
        # Update shipment record
        update_shipment(
            shipment_id=shipment_id,
            internal_status=internal_status,
            courier_status=courier_status,
            location=location,
            timestamp=timestamp,
            description=description,
            raw_payload=body
        )
        
        # Handle status-specific logic
        if internal_status == 'delivered':
            handle_delivery_confirmation(shipment)
        elif internal_status == 'delivery_failed':
            handle_delivery_failure(shipment)
        elif internal_status == 'out_for_delivery':
            handle_out_for_delivery(shipment)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'processed': shipment_id})
        }
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def verify_webhook_signature(event: Dict) -> bool:
    """
    Verify webhook authenticity using HMAC signature
    """
    signature = event.get('headers', {}).get('X-Webhook-Signature', '')
    body = event.get('body', '')
    
    if not signature:
        print("No signature provided, skipping verification (dev mode)")
        return True  # Allow in development
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


def normalize_webhook_payload(courier_name: str, payload: Dict) -> Optional[Dict]:
    """
    Normalize courier-specific webhook to internal format
    """
    try:
        if courier_name.lower() == 'delhivery':
            return {
                'tracking_number': payload.get('waybill', ''),
                'status': payload.get('Status', ''),
                'location': payload.get('Scans', [{}])[-1].get('ScanDetail', {}).get('ScannedLocation', 'Unknown'),
                'timestamp': payload.get('Scans', [{}])[-1].get('ScanDetail', {}).get('ScanDateTime', datetime.utcnow().isoformat()),
                'description': payload.get('Scans', [{}])[-1].get('ScanDetail', {}).get('Instructions', 'Status update')
            }
        
        elif courier_name.lower() == 'bluedart':
            return {
                'tracking_number': payload.get('awb_number', ''),
                'status': payload.get('status', ''),
                'location': payload.get('current_location', 'Unknown'),
                'timestamp': payload.get('status_date', datetime.utcnow().isoformat()),
                'description': payload.get('status_description', 'Status update')
            }
        
        elif courier_name.lower() == 'dtdc':
            return {
                'tracking_number': payload.get('reference_number', ''),
                'status': payload.get('shipment_status', ''),
                'location': payload.get('location', 'Unknown'),
                'timestamp': payload.get('timestamp', datetime.utcnow().isoformat()),
                'description': payload.get('remarks', 'Status update')
            }
        
        # Default fallback
        return {
            'tracking_number': payload.get('tracking_number', ''),
            'status': payload.get('status', ''),
            'location': payload.get('location', 'Unknown'),
            'timestamp': payload.get('timestamp', datetime.utcnow().isoformat()),
            'description': payload.get('description', 'Status update')
        }
    
    except Exception as e:
        print(f"Payload normalization error: {str(e)}")
        return None


def map_courier_status(courier_status: str) -> str:
    """
    Map courier-specific status codes to internal status
    """
    status_map = {
        # Delhivery
        'Pickup Scheduled': 'shipment_created',
        'Picked Up': 'picked_up',
        'In Transit': 'in_transit',
        'Out for Delivery': 'out_for_delivery',
        'Delivered': 'delivered',
        'Delivery Failed': 'delivery_failed',
        'RTO': 'returned',
        
        # BlueDart
        'MANIFESTED': 'picked_up',
        'IN TRANSIT': 'in_transit',
        'OUT FOR DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered',
        
        # DTDC
        'BOOKED': 'shipment_created',
        'PICKED': 'picked_up',
        'IN-TRANSIT': 'in_transit',
        'OUT-FOR-DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered'
    }
    
    return status_map.get(courier_status, 'in_transit')


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if status transition is allowed
    """
    valid_transitions = {
        'shipment_created': ['picked_up', 'cancelled'],
        'picked_up': ['in_transit', 'returned'],
        'in_transit': ['in_transit', 'out_for_delivery', 'returned'],
        'out_for_delivery': ['delivered', 'delivery_failed', 'in_transit'],
        'delivery_failed': ['in_transit', 'out_for_delivery', 'returned'],
        'delivered': [],
        'returned': [],
        'cancelled': []
    }
    
    allowed = valid_transitions.get(current_status, [])
    return new_status in allowed or new_status == current_status


def update_shipment(shipment_id: str, internal_status: str, courier_status: str,
                   location: str, timestamp: str, description: str, raw_payload: Dict):
    """
    Update shipment with new status
    """
    shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
    
    timeline_entry = {
        'status': internal_status,
        'timestamp': timestamp,
        'location': location,
        'description': description
    }
    
    webhook_event = {
        'event_id': f"evt_{int(datetime.now().timestamp() * 1000)}",
        'received_at': datetime.utcnow().isoformat(),
        'courier_status': courier_status,
        'raw_payload': json.dumps(raw_payload)[:1000]  # Truncate to avoid size limits
    }
    
    update_expr = 'SET internal_status = :status, updated_at = :time'
    expr_values = {
        ':status': internal_status,
        ':time': datetime.utcnow().isoformat(),
        ':timeline': [timeline_entry],
        ':event': [webhook_event]
    }
    
    if internal_status == 'delivered':
        update_expr += ', delivered_at = :delivered'
        expr_values[':delivered'] = timestamp
    elif internal_status == 'delivery_failed':
        update_expr += ', failed_at = :failed'
        expr_values[':failed'] = timestamp
    
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression=update_expr + ', timeline = list_append(timeline, :timeline), webhook_events = list_append(webhook_events, :event)',
        ExpressionAttributeValues=expr_values
    )


def handle_delivery_confirmation(shipment: Dict):
    """
    Trigger actions when delivery is confirmed
    """
    print(f"Delivery confirmed for shipment: {shipment['shipment_id']}")
    
    if SNS_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Device Delivered',
            Message=json.dumps({
                'eventType': 'DEVICE_DELIVERED',
                'shipment_id': shipment['shipment_id'],
                'order_id': shipment['order_id'],
                'tracking_number': shipment['tracking_number'],
                'delivered_at': shipment.get('delivered_at'),
                'action': 'Notify technician - ready to install'
            })
        )


def handle_delivery_failure(shipment: Dict):
    """
    Handle failed delivery attempts
    """
    retry_count = shipment.get('retry_config', {}).get('retry_count', 0)
    max_retries = shipment.get('retry_config', {}).get('max_retries', 3)
    
    print(f"Delivery failed for shipment: {shipment['shipment_id']}, retry {retry_count}/{max_retries}")
    
    if retry_count >= max_retries:
        # Escalate to admin
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Delivery Failed - Manual Intervention Required',
                Message=json.dumps({
                    'eventType': 'DELIVERY_FAILED_MAX_RETRIES',
                    'shipment_id': shipment['shipment_id'],
                    'order_id': shipment['order_id'],
                    'retry_count': retry_count,
                    'action': 'Admin intervention required'
                })
            )


def handle_out_for_delivery(shipment: Dict):
    """
    Notify stakeholders when package is out for delivery
    """
    print(f"Out for delivery: {shipment['shipment_id']}")
    
    if SNS_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Device Out for Delivery',
            Message=json.dumps({
                'eventType': 'OUT_FOR_DELIVERY',
                'shipment_id': shipment['shipment_id'],
                'order_id': shipment['order_id'],
                'tracking_number': shipment['tracking_number'],
                'action': 'Notify consumer and technician'
            })
        )
