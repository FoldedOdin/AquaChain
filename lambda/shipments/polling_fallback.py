"""
Lambda function for polling fallback mechanism

This Lambda function handles shipment tracking when webhooks fail by:
1. Querying Shipments table for active shipments (not delivered/returned/cancelled)
2. Filtering shipments with updated_at > 4 hours ago
3. Calling courier tracking API for each stale shipment
4. Updating shipment if status has changed

Requirements: 9.1, 9.2, 9.3
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

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
DELHIVERY_API_KEY = os.environ.get('DELHIVERY_API_KEY', '')
BLUEDART_API_KEY = os.environ.get('BLUEDART_API_KEY', '')
DTDC_API_KEY = os.environ.get('DTDC_API_KEY', '')
STALE_THRESHOLD_HOURS = int(os.environ.get('STALE_THRESHOLD_HOURS', '4'))

# Initialize logger
logger = get_logger(__name__, service='polling-fallback')


def handler(event, context):
    """
    Poll courier APIs for stale shipments
    
    Triggered by CloudWatch Event Rule every 4 hours.
    Queries active shipments with no updates for 4+ hours.
    
    Input: CloudWatch Event (scheduled)
    
    Output:
    {
      "success": true,
      "shipments_checked": 10,
      "shipments_updated": 3,
      "errors": []
    }
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    logger.info(
        "Starting polling fallback",
        request_id=request_id,
        stale_threshold_hours=STALE_THRESHOLD_HOURS
    )
    
    try:
        # Query Shipments table for active shipments
        active_shipments = get_active_shipments()
        
        logger.info(
            f"Found {len(active_shipments)} active shipments",
            request_id=request_id,
            count=len(active_shipments)
        )
        
        # Filter shipments with updated_at > 4 hours ago
        stale_shipments = filter_stale_shipments(active_shipments, STALE_THRESHOLD_HOURS)
        
        logger.info(
            f"Found {len(stale_shipments)} stale shipments (no updates for {STALE_THRESHOLD_HOURS}+ hours)",
            request_id=request_id,
            count=len(stale_shipments)
        )
        
        # Process each stale shipment
        shipments_updated = 0
        errors = []
        
        for shipment in stale_shipments:
            try:
                # Query courier API for current status
                updated = poll_courier_status(shipment)
                
                if updated:
                    shipments_updated += 1
                    logger.info(
                        "Updated shipment from polling",
                        shipment_id=shipment['shipment_id'],
                        tracking_number=shipment['tracking_number']
                    )
                
            except Exception as e:
                error_msg = f"Failed to poll shipment {shipment['shipment_id']}: {str(e)}"
                logger.error(
                    error_msg,
                    shipment_id=shipment['shipment_id'],
                    error_type=type(e).__name__
                )
                errors.append(error_msg)
        
        logger.info(
            "Polling fallback completed",
            request_id=request_id,
            shipments_checked=len(stale_shipments),
            shipments_updated=shipments_updated,
            errors_count=len(errors)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'shipments_checked': len(stale_shipments),
                'shipments_updated': shipments_updated,
                'errors': errors
            })
        }
        
    except Exception as e:
        logger.error(
            f"Polling fallback failed: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def get_active_shipments() -> List[Dict[str, Any]]:
    """
    Query Shipments table for active shipments.
    
    Active shipments are those NOT in terminal states:
    - delivered
    - returned
    - cancelled
    
    Requirements: 9.1
    
    Returns:
        List of active shipment records
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        # Terminal statuses to exclude
        terminal_statuses = ['delivered', 'returned', 'cancelled']
        
        # Scan table for all shipments (in production, consider using GSI)
        # Note: For large tables, this should use pagination
        response = shipments_table.scan()
        
        all_shipments = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = shipments_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_shipments.extend(response.get('Items', []))
        
        # Filter out terminal statuses
        active_shipments = [
            shipment for shipment in all_shipments
            if shipment.get('internal_status') not in terminal_statuses
        ]
        
        logger.info(
            f"Retrieved {len(active_shipments)} active shipments from {len(all_shipments)} total",
            active_count=len(active_shipments),
            total_count=len(all_shipments)
        )
        
        return active_shipments
        
    except Exception as e:
        logger.error(
            f"Failed to query active shipments: {str(e)}",
            error_type=type(e).__name__
        )
        raise


def filter_stale_shipments(shipments: List[Dict[str, Any]], threshold_hours: int) -> List[Dict[str, Any]]:
    """
    Filter shipments with updated_at > threshold_hours ago.
    
    Requirements: 9.1
    
    Args:
        shipments: List of shipment records
        threshold_hours: Number of hours to consider stale (default 4)
        
    Returns:
        List of stale shipment records
    """
    try:
        # Calculate threshold timestamp
        threshold_time = datetime.utcnow() - timedelta(hours=threshold_hours)
        
        stale_shipments = []
        
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
                # Handle both ISO format with and without 'Z' suffix
                updated_at_str = updated_at_str.rstrip('Z')
                updated_at = datetime.fromisoformat(updated_at_str)
                
                # Check if older than threshold
                if updated_at < threshold_time:
                    stale_shipments.append(shipment)
                    
                    logger.debug(
                        "Found stale shipment",
                        shipment_id=shipment.get('shipment_id'),
                        updated_at=updated_at_str,
                        hours_since_update=(datetime.utcnow() - updated_at).total_seconds() / 3600
                    )
                    
            except ValueError as e:
                logger.warning(
                    f"Failed to parse updated_at timestamp: {updated_at_str}",
                    shipment_id=shipment.get('shipment_id'),
                    error=str(e)
                )
                # Consider shipment stale if timestamp is unparseable
                stale_shipments.append(shipment)
        
        return stale_shipments
        
    except Exception as e:
        logger.error(
            f"Failed to filter stale shipments: {str(e)}",
            error_type=type(e).__name__
        )
        raise


def poll_courier_status(shipment: Dict[str, Any]) -> bool:
    """
    Query courier tracking API for current status.
    Compare with stored internal_status.
    Update shipment if status has changed.
    
    Requirements: 9.2, 9.3
    
    Args:
        shipment: Shipment record from DynamoDB
        
    Returns:
        True if shipment was updated, False otherwise
    """
    shipment_id = shipment['shipment_id']
    tracking_number = shipment['tracking_number']
    courier_name = shipment['courier_name']
    current_status = shipment['internal_status']
    
    logger.info(
        "Polling courier API",
        shipment_id=shipment_id,
        tracking_number=tracking_number,
        courier_name=courier_name,
        current_status=current_status
    )
    
    try:
        # Query courier tracking API based on courier name
        courier_response = query_courier_tracking_api(
            courier_name=courier_name,
            tracking_number=tracking_number
        )
        
        if not courier_response:
            logger.warning(
                "No response from courier API",
                shipment_id=shipment_id,
                courier_name=courier_name
            )
            return False
        
        # Extract status from courier response
        new_courier_status = courier_response.get('status')
        new_location = courier_response.get('location', 'Unknown')
        new_timestamp = courier_response.get('timestamp', datetime.utcnow().isoformat())
        new_description = courier_response.get('description', 'Status update from polling')
        
        if not new_courier_status:
            logger.warning(
                "No status in courier response",
                shipment_id=shipment_id
            )
            return False
        
        # Map courier status to internal status
        new_internal_status = map_courier_status(new_courier_status)
        
        # Compare with stored status
        if new_internal_status == current_status:
            logger.info(
                "No status change detected",
                shipment_id=shipment_id,
                status=current_status
            )
            # Update updated_at even if status hasn't changed
            update_shipment_timestamp(shipment_id)
            return False
        
        logger.info(
            "Status change detected from polling",
            shipment_id=shipment_id,
            old_status=current_status,
            new_status=new_internal_status
        )
        
        # Update shipment with new status
        update_shipment_from_polling(
            shipment_id=shipment_id,
            internal_status=new_internal_status,
            courier_status=new_courier_status,
            location=new_location,
            timestamp=new_timestamp,
            description=new_description
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to poll courier status: {str(e)}",
            shipment_id=shipment_id,
            courier_name=courier_name,
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
    
    Requirements: 9.2
    
    Args:
        courier_name: Name of courier service
        tracking_number: Tracking number to query
        
    Returns:
        Dictionary with status, location, timestamp, description
        None if API call fails
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


def map_courier_status(courier_status: str) -> str:
    """
    Map courier-specific status codes to internal status.
    Reuses the same mapping logic as webhook_handler.
    
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


def update_shipment_from_polling(
    shipment_id: str,
    internal_status: str,
    courier_status: str,
    location: str,
    timestamp: str,
    description: str
) -> None:
    """
    Update shipment record with status from polling.
    Similar to webhook update but marks source as 'polling'.
    
    Requirements: 9.3
    
    Args:
        shipment_id: Shipment ID to update
        internal_status: Internal status code
        courier_status: Courier-specific status
        location: Current location
        timestamp: Status timestamp
        description: Status description
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        # Create timeline entry
        timeline_entry = {
            'status': internal_status,
            'timestamp': timestamp,
            'location': location,
            'description': f"{description} (from polling)"
        }
        
        # Create polling event entry (similar to webhook event)
        polling_event = {
            'event_id': f"poll_{int(datetime.utcnow().timestamp() * 1000)}",
            'received_at': datetime.utcnow().isoformat(),
            'courier_status': courier_status,
            'source': 'polling',
            'raw_payload': json.dumps({
                'status': courier_status,
                'location': location,
                'timestamp': timestamp,
                'description': description
            })
        }
        
        # Build update expression
        update_expr = 'SET internal_status = :status, updated_at = :time'
        expr_values = {
            ':status': internal_status,
            ':time': datetime.utcnow().isoformat(),
            ':timeline': [timeline_entry],
            ':event': [polling_event],
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
        
        # Append to timeline and webhook_events arrays
        update_expr += ', timeline = list_append(if_not_exists(timeline, :empty_list), :timeline)'
        update_expr += ', webhook_events = list_append(if_not_exists(webhook_events, :empty_list), :event)'
        
        # Execute update
        shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        logger.info(
            "Updated shipment from polling",
            shipment_id=shipment_id,
            new_status=internal_status
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update shipment from polling: {str(e)}",
            shipment_id=shipment_id,
            error_type=type(e).__name__
        )
        raise


def update_shipment_timestamp(shipment_id: str) -> None:
    """
    Update shipment's updated_at timestamp without changing status.
    Used when polling confirms status hasn't changed.
    
    Args:
        shipment_id: Shipment ID to update
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        shipments_table.update_item(
            Key={'shipment_id': shipment_id},
            UpdateExpression='SET updated_at = :time',
            ExpressionAttributeValues={
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        logger.debug(
            "Updated shipment timestamp",
            shipment_id=shipment_id
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update shipment timestamp: {str(e)}",
            shipment_id=shipment_id,
            error_type=type(e).__name__
        )
        # Don't raise - timestamp update failure is non-critical
