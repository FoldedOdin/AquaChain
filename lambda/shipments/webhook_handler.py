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
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from cloudwatch_metrics import (
    emit_webhook_processed, 
    emit_delivery_time, 
    emit_failed_delivery,
    emit_lambda_error
)
from audit_trail import (
    create_timeline_entry,
    create_webhook_event,
    validate_timeline_entry,
    sort_timeline_chronologically
)

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
ADMIN_TASKS_TABLE = os.environ.get('ADMIN_TASKS_TABLE', 'aquachain-admin-tasks')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'default-secret')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def handler(event, context):
    """
    Process courier webhook
    """
    start_time = datetime.utcnow()
    
    try:
        # Verify webhook signature
        if not verify_webhook_signature(event):
            emit_webhook_processed('unknown', 'unknown', 'signature_failed', success=False)
            return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid signature'})}
        
        # Parse webhook payload
        body = json.loads(event['body'])
        courier_name = event['pathParameters'].get('courier', 'unknown')
        
        # Normalize courier-specific payload
        normalized = normalize_webhook_payload(courier_name, body)
        
        if not normalized:
            emit_webhook_processed('unknown', courier_name, 'normalization_failed', success=False)
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid payload'})}
        
        tracking_number = normalized['tracking_number']
        courier_status = normalized['status']
        location = normalized['location']
        timestamp = normalized['timestamp']
        description = normalized['description']
        
        # Lookup shipment by tracking number
        shipment = lookup_shipment_by_tracking(tracking_number)
        
        if not shipment:
            emit_webhook_processed(tracking_number, courier_name, 'not_found', success=False)
            return {'statusCode': 404, 'body': json.dumps({'error': 'Shipment not found'})}
        
        shipment_id = shipment['shipment_id']
        
        # Map courier status to internal status
        internal_status = map_courier_status(courier_status)
        
        # Generate deterministic event_id for idempotency
        event_id = generate_event_id(tracking_number, timestamp, courier_status)
        
        # Check for duplicate webhook
        if is_duplicate_webhook(shipment, event_id):
            emit_webhook_processed(tracking_number, courier_name, internal_status, success=True)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Webhook already processed',
                    'event_id': event_id
                })
            }
        
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
            raw_payload=body,
            event_id=event_id
        )
        
        # Handle status-specific logic
        if internal_status == 'delivered':
            handle_delivery_confirmation(shipment)
        elif internal_status == 'delivery_failed':
            handle_delivery_failure(shipment)
        elif internal_status == 'out_for_delivery':
            handle_out_for_delivery(shipment)
        
        # Emit success metric
        emit_webhook_processed(tracking_number, courier_name, internal_status, success=True)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'processed': shipment_id})
        }
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        emit_lambda_error('webhook_handler', type(e).__name__)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def verify_webhook_signature(event: Dict) -> bool:
    """
    Verify webhook authenticity using HMAC-SHA256 signature.
    Uses constant-time comparison to prevent timing attacks.
    
    Requirements: 2.1, 10.1, 10.2
    """
    # Extract signature from X-Webhook-Signature header
    headers = event.get('headers', {})
    signature = headers.get('X-Webhook-Signature', '') or headers.get('x-webhook-signature', '')
    body = event.get('body', '')
    
    if not signature:
        print("ERROR: No signature provided in X-Webhook-Signature header")
        return False  # Reject requests without signature
    
    if not body:
        print("ERROR: Empty request body")
        return False
    
    # Compute HMAC-SHA256 signature using webhook secret
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected)
    
    if not is_valid:
        print(f"ERROR: Invalid webhook signature. Expected: {expected[:10]}..., Got: {signature[:10]}...")
    
    return is_valid


def normalize_webhook_payload(courier_name: str, payload: Dict) -> Optional[Dict]:
    """
    Normalize courier-specific webhook payload to internal format.
    Extracts: tracking_number, status, location, timestamp, description
    Handles missing or malformed fields gracefully.
    Returns None for invalid payloads.
    
    Requirements: 2.2
    """
    try:
        if not payload or not isinstance(payload, dict):
            print(f"ERROR: Invalid payload type: {type(payload)}")
            return None
        
        if courier_name.lower() == 'delhivery':
            # Extract tracking number
            tracking_number = payload.get('waybill', '').strip()
            if not tracking_number:
                print("ERROR: Missing 'waybill' in Delhivery payload")
                return None
            
            # Extract status
            status = payload.get('Status', '').strip()
            if not status:
                print("ERROR: Missing 'Status' in Delhivery payload")
                return None
            
            # Extract scan details (latest scan)
            scans = payload.get('Scans', [])
            if scans and isinstance(scans, list) and len(scans) > 0:
                latest_scan = scans[-1]
                scan_detail = latest_scan.get('ScanDetail', {}) if isinstance(latest_scan, dict) else {}
                location = scan_detail.get('ScannedLocation', 'Unknown')
                timestamp = scan_detail.get('ScanDateTime', '')
                description = scan_detail.get('Instructions', 'Status update')
            else:
                location = 'Unknown'
                timestamp = ''
                description = 'Status update'
            
            # Use current time as fallback only if timestamp is missing
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': location,
                'timestamp': timestamp,
                'description': description
            }
        
        elif courier_name.lower() == 'bluedart':
            tracking_number = payload.get('awb_number', '').strip()
            status = payload.get('status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in BlueDart payload")
                return None
            
            timestamp = payload.get('status_date', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('current_location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('status_description', 'Status update')
            }
        
        elif courier_name.lower() == 'dtdc':
            tracking_number = payload.get('reference_number', '').strip()
            status = payload.get('shipment_status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in DTDC payload")
                return None
            
            timestamp = payload.get('timestamp', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('remarks', 'Status update')
            }
        
        else:
            # Generic fallback for unknown couriers
            print(f"WARNING: Unknown courier '{courier_name}', using generic normalization")
            tracking_number = payload.get('tracking_number', '').strip()
            status = payload.get('status', '').strip()
            
            if not tracking_number or not status:
                print(f"ERROR: Missing required fields in generic payload")
                return None
            
            timestamp = payload.get('timestamp', '')
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            return {
                'tracking_number': tracking_number,
                'status': status,
                'location': payload.get('location', 'Unknown'),
                'timestamp': timestamp,
                'description': payload.get('description', 'Status update')
            }
    
    except Exception as e:
        print(f"ERROR: Payload normalization exception: {str(e)}")
        return None


def map_courier_status(courier_status: str) -> str:
    """
    Map courier-specific status codes to internal status.
    Handles unknown statuses with default "in_transit".
    
    Requirements: 2.2
    """
    if not courier_status:
        print("WARNING: Empty courier status, defaulting to 'in_transit'")
        return 'in_transit'
    
    # Normalize status for case-insensitive matching
    normalized_status = courier_status.strip()
    
    status_map = {
        # Delhivery statuses
        'Pickup Scheduled': 'shipment_created',
        'Picked Up': 'picked_up',
        'In Transit': 'in_transit',
        'Out for Delivery': 'out_for_delivery',
        'Delivered': 'delivered',
        'Delivery Failed': 'delivery_failed',
        'RTO': 'returned',
        'Returned': 'returned',
        'Cancelled': 'cancelled',
        
        # BlueDart statuses
        'MANIFESTED': 'picked_up',
        'IN TRANSIT': 'in_transit',
        'OUT FOR DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered',
        'UNDELIVERED': 'delivery_failed',
        'RTO INITIATED': 'returned',
        
        # DTDC statuses
        'BOOKED': 'shipment_created',
        'PICKED': 'picked_up',
        'IN-TRANSIT': 'in_transit',
        'OUT-FOR-DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered',
        'NOT DELIVERED': 'delivery_failed',
        'RETURNED': 'returned',
        
        # Common variations (case-insensitive)
        'SHIPMENT CREATED': 'shipment_created',
        'PICKED UP': 'picked_up',
        'IN TRANSIT': 'in_transit',
        'OUT FOR DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered',
        'FAILED': 'delivery_failed',
        'DELIVERY FAILED': 'delivery_failed',
        'RETURNED TO SENDER': 'returned',
        'CANCELLED': 'cancelled'
    }
    
    # Try exact match first
    if normalized_status in status_map:
        return status_map[normalized_status]
    
    # Try case-insensitive match
    for key, value in status_map.items():
        if key.lower() == normalized_status.lower():
            return value
    
    # Default to 'in_transit' for unknown statuses
    print(f"WARNING: Unknown courier status '{courier_status}', defaulting to 'in_transit'")
    return 'in_transit'


# Define valid state transitions (state machine)
VALID_TRANSITIONS = {
    'shipment_created': ['picked_up', 'cancelled'],
    'picked_up': ['in_transit', 'returned'],
    'in_transit': ['in_transit', 'out_for_delivery', 'returned'],
    'out_for_delivery': ['delivered', 'delivery_failed', 'in_transit'],
    'delivery_failed': ['in_transit', 'out_for_delivery', 'returned'],
    'delivered': [],  # Terminal state
    'returned': [],   # Terminal state
    'cancelled': []   # Terminal state
}


def generate_event_id(tracking_number: str, timestamp: str, status: str) -> str:
    """
    Generate deterministic event_id from tracking_number + timestamp + status.
    Used for idempotency checking.
    
    Requirements: 2.6
    """
    # Create deterministic hash from key components
    event_key = f"{tracking_number}|{timestamp}|{status}"
    event_hash = hashlib.sha256(event_key.encode()).hexdigest()[:16]
    return f"evt_{event_hash}"


def is_duplicate_webhook(shipment: Dict, event_id: str) -> bool:
    """
    Check if event_id exists in webhook_events array.
    Returns True if duplicate detected.
    
    Requirements: 2.6
    """
    webhook_events = shipment.get('webhook_events', [])
    
    if not webhook_events:
        return False
    
    # Check if event_id already exists
    for event in webhook_events:
        if event.get('event_id') == event_id:
            print(f"INFO: Duplicate webhook detected - event_id: {event_id}")
            return True
    
    return False


def lookup_shipment_by_tracking(tracking_number: str) -> Optional[Dict]:
    """
    Query Shipments table using tracking_number-index GSI.
    Returns shipment record or None if not found.
    
    Requirements: 2.2
    """
    if not tracking_number:
        print("ERROR: Empty tracking number provided")
        return None
    
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        response = shipments_table.query(
            IndexName='tracking_number-index',
            KeyConditionExpression='tracking_number = :tracking',
            ExpressionAttributeValues={':tracking': tracking_number}
        )
        
        if not response.get('Items'):
            print(f"WARNING: Shipment not found for tracking number: {tracking_number}")
            return None
        
        # Return first matching shipment (tracking numbers should be unique)
        shipment = response['Items'][0]
        print(f"INFO: Found shipment {shipment['shipment_id']} for tracking {tracking_number}")
        return shipment
        
    except Exception as e:
        print(f"ERROR: Failed to lookup shipment by tracking number: {str(e)}")
        return None


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if status transition is allowed according to state machine.
    Logs invalid transitions but doesn't fail (handles out-of-order webhooks).
    
    Requirements: 2.3
    """
    if not current_status or not new_status:
        print(f"WARNING: Empty status in transition check: '{current_status}' -> '{new_status}'")
        return False
    
    # Allow same-status updates (idempotent)
    if new_status == current_status:
        return True
    
    # Check if transition is valid
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    is_valid = new_status in allowed_transitions
    
    if not is_valid:
        print(f"WARNING: Invalid state transition: '{current_status}' -> '{new_status}'. "
              f"Allowed transitions from '{current_status}': {allowed_transitions}. "
              f"Processing anyway (may be out-of-order webhook).")
    
    return is_valid


def update_shipment(shipment_id: str, internal_status: str, courier_status: str,
                   location: str, timestamp: str, description: str, raw_payload: Dict,
                   event_id: str):
    """
    Update shipment with new status.
    Appends new entry to timeline array with status, timestamp, location.
    Appends webhook event to webhook_events array with raw payload.
    Updates internal_status and updated_at fields.
    Sets delivered_at or failed_at for terminal statuses.
    
    Requirements: 2.4, 2.5, 15.1, 15.2
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        # Create timeline entry using audit trail utility
        timeline_entry = create_timeline_entry(
            status=internal_status,
            timestamp=timestamp,
            location=location,
            description=description
        )
        
        # Validate timeline entry before adding
        if not validate_timeline_entry(timeline_entry):
            print(f"WARNING: Timeline entry validation failed for {shipment_id}")
            # Continue anyway but log the issue
        
        # Create webhook event entry using audit trail utility
        webhook_event = create_webhook_event(
            event_id=event_id,
            courier_status=courier_status,
            raw_payload=raw_payload,
            max_payload_size=1000
        )
        
        # Build update expression
        update_expr = 'SET internal_status = :status, updated_at = :time'
        expr_values = {
            ':status': internal_status,
            ':time': datetime.utcnow().isoformat() + 'Z',
            ':timeline': [timeline_entry],
            ':event': [webhook_event]
        }
        
        # Set delivered_at for delivered status
        if internal_status == 'delivered':
            update_expr += ', delivered_at = :delivered'
            expr_values[':delivered'] = timestamp
        
        # Set failed_at for delivery_failed status
        elif internal_status == 'delivery_failed':
            update_expr += ', failed_at = :failed'
            expr_values[':failed'] = timestamp
        
        # Append to timeline and webhook_events arrays
        update_expr += ', timeline = list_append(if_not_exists(timeline, :empty_list), :timeline)'
        update_expr += ', webhook_events = list_append(if_not_exists(webhook_events, :empty_list), :event)'
        expr_values[':empty_list'] = []
        
        # Execute update
        shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        print(f"INFO: Updated shipment {shipment_id} to status '{internal_status}'")
        print(f"INFO: Timeline entry added: {timeline_entry}")
        print(f"INFO: Webhook event stored: {webhook_event['event_id']}")
        
    except Exception as e:
        print(f"ERROR: Failed to update shipment {shipment_id}: {str(e)}")
        raise


def handle_delivery_confirmation(shipment: Dict):
    """
    Trigger actions when delivery is confirmed.
    Sends notifications to Consumer and Technician.
    Emits delivery time metric.
    
    Requirements: 4.1, 13.3
    """
    shipment_id = shipment['shipment_id']
    order_id = shipment['order_id']
    tracking_number = shipment['tracking_number']
    delivered_at = shipment.get('delivered_at', datetime.utcnow().isoformat())
    courier_name = shipment.get('courier_name', 'unknown')
    
    print(f"INFO: Delivery confirmed for shipment: {shipment_id}")
    
    # Calculate delivery time in hours
    try:
        created_at = datetime.fromisoformat(shipment['created_at'].replace('Z', '+00:00'))
        delivered_at_dt = datetime.fromisoformat(delivered_at.replace('Z', '+00:00'))
        delivery_hours = (delivered_at_dt - created_at).total_seconds() / 3600
        
        # Emit delivery time metric
        emit_delivery_time(shipment_id, courier_name, delivery_hours)
    except Exception as e:
        print(f"WARNING: Could not calculate delivery time: {str(e)}")
    
    if SNS_TOPIC_ARN:
        try:
            # Notify Consumer and Technician
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Device Delivered - Ready for Installation',
                Message=json.dumps({
                    'eventType': 'DEVICE_DELIVERED',
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'tracking_number': tracking_number,
                    'delivered_at': delivered_at,
                    'recipients': ['consumer', 'technician'],
                    'action': 'Notify technician - ready to install',
                    'message': 'Your device has been delivered successfully. Installation can now proceed.'
                })
            )
            print(f"INFO: Sent delivery confirmation notification for {shipment_id}")
        except Exception as e:
            print(f"ERROR: Failed to send delivery notification: {str(e)}")


def create_admin_task(shipment_id: str, order_id: str, retry_count: int):
    """
    Create admin task for delivery failure requiring manual intervention.
    
    Creates a task with:
    - type: "DELIVERY_FAILED"
    - priority: HIGH
    - shipment_id, order_id, retry_count
    - recommended actions
    
    Requirements: 6.5
    
    Args:
        shipment_id: Shipment ID
        order_id: Order ID
        retry_count: Number of failed delivery attempts
    """
    try:
        # Generate unique task ID
        task_id = f"task_{int(datetime.utcnow().timestamp() * 1000)}"
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Build admin task item
        task_item = {
            'task_id': task_id,
            'task_type': 'DELIVERY_FAILED',
            'priority': 'HIGH',
            'status': 'PENDING',
            'shipment_id': shipment_id,
            'order_id': order_id,
            'retry_count': retry_count,
            'title': f'Delivery Failed After {retry_count} Attempts',
            'description': f'Shipment {shipment_id} for order {order_id} has failed delivery after {retry_count} attempts. Manual intervention required.',
            'recommended_actions': [
                'Contact customer to verify delivery address',
                'Verify delivery instructions and accessibility',
                'Check for customer availability issues',
                'Consider alternative courier service',
                'Initiate return to sender if undeliverable',
                'Offer customer pickup option if available'
            ],
            'created_at': current_time,
            'updated_at': current_time,
            'assigned_to': None,
            'resolved_at': None,
            'resolution_notes': None
        }
        
        # Store task in DynamoDB
        # Note: This assumes an admin tasks table exists or will be created
        # For now, we'll attempt to write and log if it fails
        try:
            admin_tasks_table = dynamodb.Table(ADMIN_TASKS_TABLE)
            admin_tasks_table.put_item(Item=task_item)
            print(f"INFO: Created admin task {task_id} for shipment {shipment_id}")
        except Exception as db_error:
            # If admin tasks table doesn't exist, log the task details
            print(f"WARNING: Could not store admin task in DynamoDB (table may not exist): {str(db_error)}")
            print(f"INFO: Admin task details: {json.dumps(task_item, indent=2)}")
            
            # Still send notification even if storage fails
            if SNS_TOPIC_ARN:
                try:
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=f'Admin Task Created: {task_item["title"]}',
                        Message=json.dumps({
                            'eventType': 'ADMIN_TASK_CREATED',
                            'task': task_item
                        })
                    )
                    print(f"INFO: Sent admin task notification for {task_id}")
                except Exception as sns_error:
                    print(f"ERROR: Failed to send admin task notification: {str(sns_error)}")
        
    except Exception as e:
        print(f"ERROR: Failed to create admin task: {str(e)}")
        # Don't raise - task creation failure shouldn't block webhook processing


def schedule_redelivery(shipment_id: str, order_id: str, retry_count: int, max_retries: int):
    """
    Schedule redelivery or escalate to admin based on retry count.
    
    If retry_count < max_retries (3):
    - Send notification to Consumer with new delivery date
    
    If retry_count >= max_retries:
    - Escalate to Admin with high-priority alert
    - Create admin task for manual intervention
    
    Requirements: 6.2, 6.3, 6.4
    
    Args:
        shipment_id: Shipment ID
        order_id: Order ID
        retry_count: Current retry count after increment
        max_retries: Maximum allowed retries (default 3)
    """
    print(f"INFO: Scheduling redelivery for shipment {shipment_id}, retry {retry_count}/{max_retries}")
    
    if retry_count < max_retries:
        # Retries still available - schedule redelivery
        # Calculate new estimated delivery date (add 1 day per retry)
        from datetime import timedelta
        new_delivery_date = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        
        if SNS_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='Delivery Attempt Failed - Redelivery Scheduled',
                    Message=json.dumps({
                        'eventType': 'DELIVERY_FAILED_RETRY',
                        'shipment_id': shipment_id,
                        'order_id': order_id,
                        'retry_count': retry_count,
                        'max_retries': max_retries,
                        'new_delivery_date': new_delivery_date,
                        'recipients': ['consumer'],
                        'action': 'Notify consumer about redelivery',
                        'message': f'Delivery attempt {retry_count} of {max_retries} failed. Redelivery scheduled for {new_delivery_date}.'
                    })
                )
                print(f"INFO: Sent redelivery notification for {shipment_id} (attempt {retry_count}/{max_retries})")
            except Exception as e:
                print(f"ERROR: Failed to send redelivery notification: {str(e)}")
    
    else:
        # Max retries exceeded - escalate to admin
        print(f"WARNING: Max retries exceeded for shipment {shipment_id}")
        
        if SNS_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='URGENT: Delivery Failed - Manual Intervention Required',
                    Message=json.dumps({
                        'eventType': 'DELIVERY_FAILED_MAX_RETRIES',
                        'priority': 'HIGH',
                        'shipment_id': shipment_id,
                        'order_id': order_id,
                        'retry_count': retry_count,
                        'max_retries': max_retries,
                        'recipients': ['admin'],
                        'action': 'Admin intervention required',
                        'message': f'Delivery failed after {retry_count} attempts. Manual intervention required.',
                        'recommended_actions': [
                            'Contact customer to verify address',
                            'Verify delivery instructions',
                            'Consider alternative courier',
                            'Initiate return if undeliverable'
                        ]
                    })
                )
                print(f"INFO: Escalated to admin - max retries exceeded for {shipment_id}")
            except Exception as e:
                print(f"ERROR: Failed to send admin escalation notification: {str(e)}")
        
        # Create admin task for manual intervention
        create_admin_task(shipment_id, order_id, retry_count)


def handle_delivery_failure(shipment: Dict) -> int:
    """
    Handle failed delivery attempts.
    Increments retry counter and returns updated count for decision logic.
    Emits failed delivery metric.
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    
    Args:
        shipment: Shipment record from DynamoDB
        
    Returns:
        Updated retry_count after increment
    """
    shipment_id = shipment['shipment_id']
    order_id = shipment['order_id']
    courier_name = shipment.get('courier_name', 'unknown')
    retry_config = shipment.get('retry_config', {})
    retry_count = retry_config.get('retry_count', 0)
    max_retries = retry_config.get('max_retries', 3)
    
    print(f"INFO: Delivery failed for shipment: {shipment_id}, retry {retry_count}/{max_retries}")
    
    # Increment retry counter and update last_retry_at timestamp
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        current_time = datetime.utcnow().isoformat()
        
        response = shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression='SET retry_config.retry_count = retry_config.retry_count + :inc, retry_config.last_retry_at = :time',
            ExpressionAttributeValues={
                ':inc': 1,
                ':time': current_time
            },
            ReturnValues='ALL_NEW'
        )
        
        # Get updated retry count from response
        updated_retry_count = response['Attributes']['retry_config']['retry_count']
        print(f"INFO: Incremented retry count to {updated_retry_count} for {shipment_id}")
        print(f"INFO: Last retry at: {current_time}")
        
        # Emit failed delivery metric
        emit_failed_delivery(shipment_id, courier_name, updated_retry_count)
        
        # Call redelivery scheduling logic
        schedule_redelivery(shipment_id, order_id, updated_retry_count, max_retries)
        
        return updated_retry_count
        
    except Exception as e:
        print(f"ERROR: Failed to increment retry count: {str(e)}")
        # Return current count if update fails
        return retry_count


def handle_out_for_delivery(shipment: Dict):
    """
    Notify stakeholders when package is out for delivery.
    Sends real-time notifications to Consumer and Technician.
    
    Requirements: 13.2
    """
    shipment_id = shipment['shipment_id']
    order_id = shipment['order_id']
    tracking_number = shipment['tracking_number']
    estimated_delivery = shipment.get('estimated_delivery', 'Today')
    
    print(f"INFO: Out for delivery: {shipment_id}")
    
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Device Out for Delivery - Arriving Soon',
                Message=json.dumps({
                    'eventType': 'OUT_FOR_DELIVERY',
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'tracking_number': tracking_number,
                    'estimated_delivery': estimated_delivery,
                    'recipients': ['consumer', 'technician'],
                    'action': 'Notify consumer and technician',
                    'message': 'Your device is out for delivery and will arrive soon. Please be available to receive it.'
                })
            )
            print(f"INFO: Sent out-for-delivery notification for {shipment_id}")
        except Exception as e:
            print(f"ERROR: Failed to send out-for-delivery notification: {str(e)}")
