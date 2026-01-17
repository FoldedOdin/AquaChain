"""
Lambda function for detecting and handling stale shipments

This Lambda function handles stale shipment detection by:
1. Querying Shipments table using status-created_at-index
2. Filtering shipments with updated_at > 7 days ago
3. Excluding terminal statuses (delivered, returned, cancelled)
4. Querying courier API directly for latest status
5. Marking shipment as "lost" if courier has no updates
6. Creating high-priority admin task for investigation
7. Sending notification to Consumer with apology and resolution steps

Requirements: 5.3, 9.5
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests

from structured_logger import get_logger
from cloudwatch_metrics import emit_stale_shipments, emit_lambda_error

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
sns = boto3.client('sns')

# Environment variables
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ADMIN_TASKS_TABLE = os.environ.get('ADMIN_TASKS_TABLE', 'aquachain-admin-tasks')
DELHIVERY_API_KEY = os.environ.get('DELHIVERY_API_KEY', '')
BLUEDART_API_KEY = os.environ.get('BLUEDART_API_KEY', '')
DTDC_API_KEY = os.environ.get('DTDC_API_KEY', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
STALE_THRESHOLD_DAYS = int(os.environ.get('STALE_THRESHOLD_DAYS', '7'))

# Initialize logger
logger = get_logger(__name__, service='stale-shipment-detector')


def handler(event, context):
    """
    Detect and handle stale shipments
    
    Triggered by CloudWatch Event Rule daily at 9 AM.
    Queries shipments with no updates for 7+ days.
    
    Input: CloudWatch Event (scheduled)
    
    Output:
    {
      "success": true,
      "stale_shipments_found": 5,
      "shipments_marked_lost": 2,
      "admin_tasks_created": 2,
      "errors": []
    }
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    logger.info(
        "Starting stale shipment detection",
        request_id=request_id,
        stale_threshold_days=STALE_THRESHOLD_DAYS
    )
    
    try:
        # Query Shipments table for stale shipments
        stale_shipments = get_stale_shipments()
        
        logger.info(
            f"Found {len(stale_shipments)} stale shipments (no updates for {STALE_THRESHOLD_DAYS}+ days)",
            request_id=request_id,
            count=len(stale_shipments)
        )
        
        # Emit stale shipments metric
        emit_stale_shipments(len(stale_shipments))
        
        # Process each stale shipment
        shipments_marked_lost = 0
        admin_tasks_created = 0
        errors = []
        
        for shipment in stale_shipments:
            try:
                # Handle stale shipment
                result = handle_stale_shipment(shipment)
                
                if result['marked_lost']:
                    shipments_marked_lost += 1
                
                if result['admin_task_created']:
                    admin_tasks_created += 1
                
                logger.info(
                    "Processed stale shipment",
                    shipment_id=shipment['shipment_id'],
                    marked_lost=result['marked_lost'],
                    admin_task_created=result['admin_task_created']
                )
                
            except Exception as e:
                error_msg = f"Failed to process stale shipment {shipment['shipment_id']}: {str(e)}"
                logger.error(
                    error_msg,
                    shipment_id=shipment['shipment_id'],
                    error_type=type(e).__name__
                )
                errors.append(error_msg)
        
        logger.info(
            "Stale shipment detection completed",
            request_id=request_id,
            stale_shipments_found=len(stale_shipments),
            shipments_marked_lost=shipments_marked_lost,
            admin_tasks_created=admin_tasks_created,
            errors_count=len(errors)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'stale_shipments_found': len(stale_shipments),
                'shipments_marked_lost': shipments_marked_lost,
                'admin_tasks_created': admin_tasks_created,
                'errors': errors
            })
        }
        
    except Exception as e:
        logger.error(
            f"Stale shipment detection failed: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        
        emit_lambda_error('stale_shipment_detector', type(e).__name__)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def get_stale_shipments() -> List[Dict[str, Any]]:
    """
    Query Shipments table for stale shipments.
    
    Stale shipments are those:
    - With updated_at > 7 days ago
    - NOT in terminal states (delivered, returned, cancelled)
    
    Uses status-created_at-index GSI to efficiently query non-terminal shipments.
    
    Requirements: 5.3, 9.5
    
    Returns:
        List of stale shipment records
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        # Calculate threshold timestamp (7 days ago)
        threshold_time = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)
        threshold_str = threshold_time.isoformat()
        
        # Terminal statuses to exclude
        terminal_statuses = ['delivered', 'returned', 'cancelled']
        
        # Active statuses to query
        active_statuses = [
            'shipment_created',
            'picked_up',
            'in_transit',
            'out_for_delivery',
            'delivery_failed'
        ]
        
        stale_shipments = []
        
        # Query each active status using GSI
        for status in active_statuses:
            try:
                logger.debug(
                    f"Querying shipments with status: {status}",
                    status=status
                )
                
                response = shipments_table.query(
                    IndexName='status-created_at-index',
                    KeyConditionExpression='internal_status = :status',
                    ExpressionAttributeValues={
                        ':status': status
                    }
                )
                
                shipments = response.get('Items', [])
                
                # Handle pagination
                while 'LastEvaluatedKey' in response:
                    response = shipments_table.query(
                        IndexName='status-created_at-index',
                        KeyConditionExpression='internal_status = :status',
                        ExpressionAttributeValues={
                            ':status': status
                        },
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    shipments.extend(response.get('Items', []))
                
                # Filter by updated_at threshold
                for shipment in shipments:
                    updated_at_str = shipment.get('updated_at', '')
                    
                    if not updated_at_str:
                        # No updated_at field - consider stale
                        logger.warning(
                            "Shipment missing updated_at field",
                            shipment_id=shipment.get('shipment_id')
                        )
                        stale_shipments.append(shipment)
                        continue
                    
                    try:
                        # Parse updated_at timestamp
                        updated_at_str = updated_at_str.rstrip('Z')
                        updated_at = datetime.fromisoformat(updated_at_str)
                        
                        # Check if older than threshold
                        if updated_at < threshold_time:
                            stale_shipments.append(shipment)
                            
                            logger.debug(
                                "Found stale shipment",
                                shipment_id=shipment.get('shipment_id'),
                                status=status,
                                updated_at=updated_at_str,
                                days_since_update=(datetime.utcnow() - updated_at).days
                            )
                    
                    except ValueError as e:
                        logger.warning(
                            f"Failed to parse updated_at timestamp: {updated_at_str}",
                            shipment_id=shipment.get('shipment_id'),
                            error=str(e)
                        )
                        # Consider shipment stale if timestamp is unparseable
                        stale_shipments.append(shipment)
                
            except Exception as e:
                logger.error(
                    f"Failed to query status {status}: {str(e)}",
                    status=status,
                    error_type=type(e).__name__
                )
                # Continue with other statuses
                continue
        
        logger.info(
            f"Retrieved {len(stale_shipments)} stale shipments",
            count=len(stale_shipments)
        )
        
        return stale_shipments
        
    except Exception as e:
        logger.error(
            f"Failed to query stale shipments: {str(e)}",
            error_type=type(e).__name__
        )
        raise


def handle_stale_shipment(shipment: Dict[str, Any]) -> Dict[str, bool]:
    """
    Handle stale shipment by querying courier API and taking appropriate action.
    
    Steps:
    1. Query courier API directly for latest status
    2. If courier has updates, update shipment record
    3. If courier has no updates, mark shipment as "lost"
    4. Create high-priority admin task for investigation
    5. Send notification to Consumer with apology and resolution steps
    
    Requirements: 5.3
    
    Args:
        shipment: Stale shipment record from DynamoDB
        
    Returns:
        Dictionary with marked_lost and admin_task_created flags
    """
    shipment_id = shipment['shipment_id']
    tracking_number = shipment['tracking_number']
    courier_name = shipment['courier_name']
    order_id = shipment['order_id']
    
    logger.info(
        "Handling stale shipment",
        shipment_id=shipment_id,
        tracking_number=tracking_number,
        courier_name=courier_name
    )
    
    result = {
        'marked_lost': False,
        'admin_task_created': False
    }
    
    try:
        # Query courier API directly for latest status
        courier_response = query_courier_tracking_api(
            courier_name=courier_name,
            tracking_number=tracking_number
        )
        
        if courier_response and courier_response.get('status'):
            # Courier has updates - update shipment record
            logger.info(
                "Courier has updates for stale shipment",
                shipment_id=shipment_id,
                courier_status=courier_response.get('status')
            )
            
            # Update shipment with courier data
            update_shipment_from_courier(shipment_id, courier_response)
            
            # Don't mark as lost or create admin task
            return result
        
        # Courier has no updates - mark as lost
        logger.warning(
            "Courier has no updates for stale shipment - marking as lost",
            shipment_id=shipment_id,
            tracking_number=tracking_number
        )
        
        # Mark shipment as "lost"
        mark_shipment_as_lost(shipment_id)
        result['marked_lost'] = True
        
        # Create high-priority admin task
        create_stale_shipment_admin_task(shipment)
        result['admin_task_created'] = True
        
        # Send notification to Consumer
        notify_consumer_about_lost_shipment(shipment)
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to handle stale shipment: {str(e)}",
            shipment_id=shipment_id,
            error_type=type(e).__name__
        )
        raise


def query_courier_tracking_api(courier_name: str, tracking_number: str) -> Optional[Dict[str, Any]]:
    """
    Query courier tracking API for shipment status.
    
    Supports:
    - Delhivery
    - BlueDart
    - DTDC
    
    Requirements: 5.3
    
    Args:
        courier_name: Name of courier service
        tracking_number: Tracking number to query
        
    Returns:
        Dictionary with status, location, timestamp, description
        None if API call fails or no data available
    """
    try:
        if courier_name.lower() == 'delhivery':
            return query_delhivery_tracking(tracking_number)
        elif courier_name.lower() == 'bluedart':
            return query_bluedart_tracking(tracking_number)
        elif courier_name.lower() == 'dtdc':
            return query_dtdc_tracking(tracking_number)
        else:
            logger.warning(
                f"Unknown courier: {courier_name}",
                courier_name=courier_name
            )
            return None
            
    except Exception as e:
        logger.error(
            f"Courier API query failed: {str(e)}",
            courier_name=courier_name,
            tracking_number=tracking_number,
            error_type=type(e).__name__
        )
        return None


def query_delhivery_tracking(tracking_number: str) -> Optional[Dict[str, Any]]:
    """
    Query Delhivery tracking API.
    
    Args:
        tracking_number: Delhivery waybill number
        
    Returns:
        Normalized tracking data or None
    """
    if not DELHIVERY_API_KEY:
        logger.warning("No DELHIVERY_API_KEY configured")
        return None
    
    try:
        logger.info(
            "Querying Delhivery tracking API",
            tracking_number=tracking_number
        )
        
        response = requests.get(
            f'https://track.delhivery.com/api/v1/packages/json/?waybill={tracking_number}',
            headers={
                'Authorization': f'Token {DELHIVERY_API_KEY}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract tracking data from response
        if 'ShipmentData' in data and len(data['ShipmentData']) > 0:
            shipment_data = data['ShipmentData'][0]
            shipment = shipment_data.get('Shipment', {})
            
            status = shipment.get('Status', {}).get('Status', '')
            
            # Get latest scan
            scans = shipment.get('Scans', [])
            if scans and len(scans) > 0:
                latest_scan = scans[-1]
                scan_detail = latest_scan.get('ScanDetail', {})
                location = scan_detail.get('ScannedLocation', 'Unknown')
                timestamp = scan_detail.get('ScanDateTime', datetime.utcnow().isoformat())
                description = scan_detail.get('Instructions', 'Status update')
            else:
                location = 'Unknown'
                timestamp = datetime.utcnow().isoformat()
                description = 'Status update'
            
            return {
                'status': status,
                'location': location,
                'timestamp': timestamp,
                'description': description
            }
        
        logger.warning(
            "No shipment data in Delhivery response",
            tracking_number=tracking_number
        )
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Delhivery API request failed: {str(e)}",
            tracking_number=tracking_number,
            error_type=type(e).__name__
        )
        return None
    except Exception as e:
        logger.error(
            f"Failed to parse Delhivery response: {str(e)}",
            tracking_number=tracking_number,
            error_type=type(e).__name__
        )
        return None


def query_bluedart_tracking(tracking_number: str) -> Optional[Dict[str, Any]]:
    """
    Query BlueDart tracking API (placeholder).
    
    Args:
        tracking_number: BlueDart AWB number
        
    Returns:
        Normalized tracking data or None
    """
    if not BLUEDART_API_KEY:
        logger.warning("No BLUEDART_API_KEY configured")
        return None
    
    # TODO: Implement BlueDart API integration
    logger.info(
        "BlueDart tracking API not yet implemented",
        tracking_number=tracking_number
    )
    return None


def query_dtdc_tracking(tracking_number: str) -> Optional[Dict[str, Any]]:
    """
    Query DTDC tracking API (placeholder).
    
    Args:
        tracking_number: DTDC reference number
        
    Returns:
        Normalized tracking data or None
    """
    if not DTDC_API_KEY:
        logger.warning("No DTDC_API_KEY configured")
        return None
    
    # TODO: Implement DTDC API integration
    logger.info(
        "DTDC tracking API not yet implemented",
        tracking_number=tracking_number
    )
    return None


def update_shipment_from_courier(shipment_id: str, courier_response: Dict[str, Any]) -> None:
    """
    Update shipment record with data from courier API.
    
    Args:
        shipment_id: Shipment ID to update
        courier_response: Response from courier API
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        courier_status = courier_response.get('status', '')
        location = courier_response.get('location', 'Unknown')
        timestamp = courier_response.get('timestamp', datetime.utcnow().isoformat())
        description = courier_response.get('description', 'Status update from stale detection')
        
        # Map courier status to internal status
        internal_status = map_courier_status(courier_status)
        
        # Create timeline entry
        timeline_entry = {
            'status': internal_status,
            'timestamp': timestamp,
            'location': location,
            'description': f"{description} (from stale detection)"
        }
        
        # Build update expression
        update_expr = 'SET internal_status = :status, updated_at = :time'
        expr_values = {
            ':status': internal_status,
            ':time': datetime.utcnow().isoformat(),
            ':timeline': [timeline_entry],
            ':empty_list': []
        }
        
        # Set delivered_at for delivered status
        if internal_status == 'delivered':
            update_expr += ', delivered_at = :delivered'
            expr_values[':delivered'] = timestamp
        
        # Set failed_at for delivery_failed status
        elif internal_status == 'delivery_failed':
            update_expr += ', failed_at = :failed'
            expr_values[':failed'] = timestamp
        
        # Append to timeline array
        update_expr += ', timeline = list_append(if_not_exists(timeline, :empty_list), :timeline)'
        
        # Execute update
        shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        logger.info(
            "Updated shipment from courier API",
            shipment_id=shipment_id,
            new_status=internal_status
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update shipment from courier: {str(e)}",
            shipment_id=shipment_id,
            error_type=type(e).__name__
        )
        raise


def map_courier_status(courier_status: str) -> str:
    """
    Map courier-specific status codes to internal status.
    
    Args:
        courier_status: Courier-specific status string
        
    Returns:
        Internal status code
    """
    if not courier_status:
        return 'in_transit'
    
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
        'RETURNED': 'returned'
    }
    
    # Try exact match
    if courier_status in status_map:
        return status_map[courier_status]
    
    # Try case-insensitive match
    for key, value in status_map.items():
        if key.lower() == courier_status.lower():
            return value
    
    # Default to in_transit
    logger.warning(
        f"Unknown courier status: {courier_status}, defaulting to in_transit",
        courier_status=courier_status
    )
    return 'in_transit'


def mark_shipment_as_lost(shipment_id: str) -> None:
    """
    Mark shipment as "lost" in DynamoDB.
    
    Updates:
    - internal_status to "lost"
    - updated_at to current timestamp
    - Appends timeline entry
    
    Requirements: 5.3
    
    Args:
        shipment_id: Shipment ID to mark as lost
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        current_time = datetime.utcnow().isoformat()
        
        # Create timeline entry
        timeline_entry = {
            'status': 'lost',
            'timestamp': current_time,
            'location': 'Unknown',
            'description': 'Shipment marked as lost due to no updates for 7+ days'
        }
        
        # Update shipment
        shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression='SET internal_status = :status, updated_at = :time, timeline = list_append(if_not_exists(timeline, :empty_list), :timeline)',
            ExpressionAttributeValues={
                ':status': 'lost',
                ':time': current_time,
                ':timeline': [timeline_entry],
                ':empty_list': []
            }
        )
        
        logger.info(
            "Marked shipment as lost",
            shipment_id=shipment_id
        )
        
    except Exception as e:
        logger.error(
            f"Failed to mark shipment as lost: {str(e)}",
            shipment_id=shipment_id,
            error_type=type(e).__name__
        )
        raise


def create_stale_shipment_admin_task(shipment: Dict[str, Any]) -> None:
    """
    Create high-priority admin task for stale shipment investigation.
    
    Creates a task with:
    - type: "STALE_SHIPMENT"
    - priority: HIGH
    - shipment_id, order_id, tracking_number
    - recommended actions
    
    Requirements: 5.3
    
    Args:
        shipment: Stale shipment record
    """
    try:
        shipment_id = shipment['shipment_id']
        order_id = shipment['order_id']
        tracking_number = shipment['tracking_number']
        courier_name = shipment['courier_name']
        updated_at = shipment.get('updated_at', 'Unknown')
        
        # Generate unique task ID
        task_id = f"task_{int(datetime.utcnow().timestamp() * 1000)}"
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Calculate days since last update
        try:
            updated_at_str = updated_at.rstrip('Z')
            updated_at_dt = datetime.fromisoformat(updated_at_str)
            days_since_update = (datetime.utcnow() - updated_at_dt).days
        except:
            days_since_update = STALE_THRESHOLD_DAYS
        
        # Build admin task item
        task_item = {
            'task_id': task_id,
            'task_type': 'STALE_SHIPMENT',
            'priority': 'HIGH',
            'status': 'PENDING',
            'shipment_id': shipment_id,
            'order_id': order_id,
            'tracking_number': tracking_number,
            'courier_name': courier_name,
            'days_since_update': days_since_update,
            'title': f'Stale Shipment Detected - No Updates for {days_since_update} Days',
            'description': f'Shipment {shipment_id} (tracking: {tracking_number}) for order {order_id} has had no updates for {days_since_update} days. Courier {courier_name} has no recent tracking information. Manual investigation required.',
            'recommended_actions': [
                'Contact courier directly to locate package',
                'Verify tracking number is correct',
                'Check if package is stuck at customs or sorting facility',
                'Contact customer to verify delivery address',
                'Initiate insurance claim if package is confirmed lost',
                'Arrange replacement shipment if necessary',
                'Update customer with investigation status'
            ],
            'created_at': current_time,
            'updated_at': current_time,
            'assigned_to': None,
            'resolved_at': None,
            'resolution_notes': None
        }
        
        # Store task in DynamoDB
        try:
            admin_tasks_table = dynamodb.Table(ADMIN_TASKS_TABLE)
            admin_tasks_table.put_item(Item=task_item)
            logger.info(
                f"Created admin task {task_id} for stale shipment {shipment_id}",
                task_id=task_id,
                shipment_id=shipment_id
            )
        except Exception as db_error:
            # If admin tasks table doesn't exist, log the task details
            logger.warning(
                f"Could not store admin task in DynamoDB (table may not exist): {str(db_error)}",
                task_id=task_id
            )
            logger.info(
                f"Admin task details: {json.dumps(task_item, indent=2)}",
                task_id=task_id
            )
            
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
                    logger.info(
                        f"Sent admin task notification for {task_id}",
                        task_id=task_id
                    )
                except Exception as sns_error:
                    logger.error(
                        f"Failed to send admin task notification: {str(sns_error)}",
                        task_id=task_id
                    )
        
    except Exception as e:
        logger.error(
            f"Failed to create admin task: {str(e)}",
            shipment_id=shipment.get('shipment_id'),
            error_type=type(e).__name__
        )
        # Don't raise - task creation failure shouldn't block stale detection


def notify_consumer_about_lost_shipment(shipment: Dict[str, Any]) -> None:
    """
    Send notification to Consumer about lost shipment.
    
    Includes:
    - Apology for the inconvenience
    - Explanation of the situation
    - Resolution steps being taken
    - Contact information for support
    
    Requirements: 5.3
    
    Args:
        shipment: Lost shipment record
    """
    if not SNS_TOPIC_ARN:
        logger.warning("No SNS_TOPIC_ARN configured, skipping consumer notification")
        return
    
    try:
        shipment_id = shipment['shipment_id']
        order_id = shipment['order_id']
        tracking_number = shipment['tracking_number']
        courier_name = shipment['courier_name']
        
        logger.info(
            "Sending lost shipment notification to consumer",
            shipment_id=shipment_id,
            order_id=order_id
        )
        
        # Build notification message
        message = {
            'eventType': 'SHIPMENT_LOST',
            'priority': 'HIGH',
            'shipment_id': shipment_id,
            'order_id': order_id,
            'tracking_number': tracking_number,
            'courier_name': courier_name,
            'recipients': ['consumer'],
            'subject': 'Important Update About Your Shipment',
            'message': f'''
Dear Customer,

We sincerely apologize for the inconvenience. We have been unable to locate your shipment (tracking number: {tracking_number}) with {courier_name}.

What we're doing:
- Our team is actively investigating with the courier service
- We are working to locate your package or arrange a replacement
- You will receive updates within 24-48 hours

What you can do:
- Contact our support team if you have any questions
- We will keep you informed of all developments

We deeply regret this situation and are committed to resolving it as quickly as possible.

Thank you for your patience and understanding.

Best regards,
AquaChain Support Team
            '''.strip(),
            'resolution_steps': [
                'Investigation initiated with courier service',
                'Replacement shipment will be arranged if package cannot be located',
                'Customer will be updated within 24-48 hours',
                'Full refund or replacement guaranteed'
            ],
            'support_contact': {
                'email': 'support@aquachain.com',
                'phone': '+91-1800-XXX-XXXX'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Publish to SNS topic
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Important Update About Your Shipment',
            Message=json.dumps(message),
            MessageAttributes={
                'event_type': {
                    'DataType': 'String',
                    'StringValue': 'SHIPMENT_LOST'
                },
                'priority': {
                    'DataType': 'String',
                    'StringValue': 'HIGH'
                },
                'shipment_id': {
                    'DataType': 'String',
                    'StringValue': shipment_id
                },
                'order_id': {
                    'DataType': 'String',
                    'StringValue': order_id
                }
            }
        )
        
        logger.info(
            "Sent lost shipment notification to consumer",
            shipment_id=shipment_id,
            message_id=response.get('MessageId')
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send consumer notification: {str(e)}",
            shipment_id=shipment.get('shipment_id'),
            error_type=type(e).__name__
        )
        # Don't raise - notification failure shouldn't block stale detection
