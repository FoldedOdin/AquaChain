"""
Lambda function to get device orders with backward compatibility

This Lambda ensures that the DeviceOrders API returns unchanged status
even when shipment tracking is integrated. The external status remains
"shipped" while internal shipment states are managed separately.

Requirements: 8.1, 8.2, 8.3
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal

from structured_logger import get_logger

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')

# Initialize logger
logger = get_logger(__name__, service='get-orders')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def handler(event, context):
    """
    Get device orders for a user
    
    This handler ensures backward compatibility by:
    - Returning orders with unchanged status field
    - Not exposing internal shipment states
    - Maintaining existing API response format
    
    Query Parameters:
    - userId: Filter by user ID (optional for admin)
    - status: Filter by status (optional)
    
    Returns:
    {
      "success": true,
      "orders": [...]
    }
    
    Requirements: 8.1, 8.2, 8.3
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    try:
        # Extract user ID from authorizer context
        user_id = extract_user_id(event)
        user_role = extract_user_role(event)
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        filter_status = query_params.get('status')
        filter_user_id = query_params.get('userId')
        
        logger.info(
            "Fetching orders",
            request_id=request_id,
            user_id=user_id,
            user_role=user_role,
            filter_status=filter_status
        )
        
        # Fetch orders based on user role
        if user_role == 'admin':
            # Admin can see all orders or filter by userId
            if filter_user_id:
                orders = get_orders_by_user(filter_user_id, filter_status)
            else:
                orders = get_all_orders(filter_status)
        else:
            # Regular users can only see their own orders
            orders = get_orders_by_user(user_id, filter_status)
        
        # Ensure backward compatibility - don't expose internal shipment fields
        compatible_orders = ensure_backward_compatibility(orders)
        
        logger.info(
            "Orders fetched successfully",
            request_id=request_id,
            count=len(compatible_orders)
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'orders': compatible_orders
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(
            f"Error fetching orders: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Failed to fetch orders'
            })
        }


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract user ID from request context
    
    Args:
        event: Lambda event object
        
    Returns:
        User ID from Cognito authorizer
    """
    try:
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub', '')
    except Exception:
        return ''


def extract_user_role(event: Dict[str, Any]) -> str:
    """
    Extract user role from request context
    
    Args:
        event: Lambda event object
        
    Returns:
        User role (admin, consumer, technician)
    """
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        # Check custom:role or cognito:groups
        role = claims.get('custom:role', '')
        if not role:
            groups = claims.get('cognito:groups', '')
            if 'admin' in groups.lower():
                role = 'admin'
            elif 'technician' in groups.lower():
                role = 'technician'
            else:
                role = 'consumer'
        return role.lower()
    except Exception:
        return 'consumer'


def get_orders_by_user(user_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get orders for a specific user
    
    Args:
        user_id: User ID to filter by
        status_filter: Optional status filter
        
    Returns:
        List of order items
    """
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        # Query using userId-createdAt-index GSI
        if status_filter:
            response = orders_table.query(
                IndexName='userId-createdAt-index',
                KeyConditionExpression='userId = :uid',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':status': status_filter
                }
            )
        else:
            response = orders_table.query(
                IndexName='userId-createdAt-index',
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error querying orders by user: {str(e)}", user_id=user_id)
        raise


def get_all_orders(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all orders (admin only)
    
    Args:
        status_filter: Optional status filter
        
    Returns:
        List of order items
    """
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        if status_filter:
            # Use status-createdAt-index GSI for filtering
            response = orders_table.query(
                IndexName='status-createdAt-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status_filter}
            )
        else:
            # Scan all orders (expensive, but admin use case)
            response = orders_table.scan()
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error scanning all orders: {str(e)}")
        raise


def ensure_backward_compatibility(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure backward compatibility by maintaining existing API format
    
    This function:
    - Keeps the status field unchanged (e.g., "shipped")
    - Does not expose internal shipment_id, tracking_number, or internal_status
    - Maintains the same response structure as before
    - Removes duplicate orders based on orderId and createdAt
    
    Args:
        orders: List of order items from DynamoDB
        
    Returns:
        List of orders with backward-compatible format
        
    Requirements: 8.1, 8.2, 8.3
    """
    compatible_orders = []
    seen_orders = set()  # Track unique orders to prevent duplicates
    
    for order in orders:
        # Create a copy to avoid modifying original
        compatible_order = dict(order)
        
        # Create unique key for deduplication
        order_key = f"{compatible_order.get('orderId', '')}_{compatible_order.get('createdAt', '')}"
        
        # Skip if we've already seen this order
        if order_key in seen_orders:
            logger.warning(
                "Duplicate order detected in database",
                order_id=compatible_order.get('orderId'),
                created_at=compatible_order.get('createdAt')
            )
            continue
        
        seen_orders.add(order_key)
        
        # Remove internal shipment fields from response
        # These fields exist in DynamoDB but should not be exposed
        # to maintain backward compatibility
        if 'shipment_id' in compatible_order:
            del compatible_order['shipment_id']
        if 'tracking_number' in compatible_order:
            del compatible_order['tracking_number']
        if 'internal_status' in compatible_order:
            del compatible_order['internal_status']
        
        # Ensure status field remains unchanged
        # Even if shipment tracking is active, external status stays "shipped"
        # Internal shipment states are managed in Shipments table
        
        compatible_orders.append(compatible_order)
    
    # Log deduplication stats
    original_count = len(orders)
    final_count = len(compatible_orders)
    if original_count != final_count:
        logger.warning(
            "Removed duplicate orders from response",
            original_count=original_count,
            final_count=final_count,
            duplicates_removed=original_count - final_count
        )
    
    return compatible_orders


def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single order by ID
    
    Args:
        order_id: Order ID
        
    Returns:
        Order item or None if not found
    """
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        response = orders_table.get_item(Key={'orderId': order_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting order by ID: {str(e)}", order_id=order_id)
        return None
