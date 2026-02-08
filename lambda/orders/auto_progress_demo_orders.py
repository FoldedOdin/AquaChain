"""
Auto-Progress Demo Orders Lambda Function

This Lambda function automatically progresses demo orders through different stages
with 10-second delays to simulate a realistic ordering flow for demonstration purposes.

Triggered by: EventBridge rule (every 10 seconds) or order creation event
"""

import sys
import os
import json
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# Environment variables
ORDERS_TABLE = os.environ.get('ENHANCED_ORDERS_TABLE', 'aquachain-orders')

# Initialize logger
logger = get_logger(__name__, service='auto-progress-demo-orders')

# Order status progression for demo
STATUS_PROGRESSION = [
    'ORDER_PLACED',      # Initial status after COD order
    'SHIPPED',           # After 10 seconds
    'OUT_FOR_DELIVERY',  # After 20 seconds
    'DELIVERED'          # After 30 seconds (final)
]


def get_next_status(current_status: str) -> str | None:
    """Get the next status in the progression"""
    try:
        current_index = STATUS_PROGRESSION.index(current_status)
        if current_index < len(STATUS_PROGRESSION) - 1:
            return STATUS_PROGRESSION[current_index + 1]
        return None  # Already at final status
    except ValueError:
        logger.warning(f'Status {current_status} not in progression')
        return None


def get_orders_to_progress() -> List[Dict[str, Any]]:
    """Get all orders that need to be progressed"""
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        # Scan for orders that are not in final status and were created recently
        response = orders_table.scan(
            FilterExpression='#status IN (:status1, :status2, :status3) AND attribute_exists(createdAt)',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status1': 'ORDER_PLACED',
                ':status2': 'SHIPPED',
                ':status3': 'OUT_FOR_DELIVERY'
            }
        )
        
        orders = response.get('Items', [])
        logger.info(f'Found {len(orders)} orders to potentially progress')
        
        # Filter orders that are ready to progress (created/updated more than 10 seconds ago)
        now = datetime.now(timezone.utc)
        orders_to_progress = []
        
        for order in orders:
            updated_at = order.get('updatedAt')
            if updated_at:
                try:
                    updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    time_diff = (now - updated_time).total_seconds()
                    
                    # Progress if more than 10 seconds have passed
                    if time_diff >= 10:
                        orders_to_progress.append(order)
                        logger.info(f'Order {order.get("orderId")} ready to progress (age: {time_diff}s)')
                except Exception as e:
                    logger.error(f'Error parsing timestamp for order {order.get("orderId")}: {e}')
        
        return orders_to_progress
        
    except Exception as e:
        logger.error(f'Error scanning orders: {e}')
        return []


def progress_order(order: Dict[str, Any]) -> bool:
    """Progress an order to the next status"""
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        order_id = order['orderId']
        current_status = order['status']
        current_version = order.get('version', 1)
        
        # Get next status
        next_status = get_next_status(current_status)
        if not next_status:
            logger.info(f'Order {order_id} already at final status: {current_status}')
            return False
        
        # Prepare status update
        timestamp = datetime.now(timezone.utc).isoformat()
        new_version = current_version + 1
        
        # Create status update entry
        status_update = {
            'status': next_status,
            'timestamp': timestamp,
            'message': f'Order automatically progressed to {next_status} (Demo Mode)',
            'metadata': {
                'autoProgressed': True,
                'previousStatus': current_status
            }
        }
        
        # Update status history
        status_history = order.get('statusHistory', [])
        status_history.append(status_update)
        
        # Update order with optimistic locking
        response = orders_table.update_item(
            Key={
                'PK': f'ORDER#{order_id}',
                'SK': f'ORDER#{order_id}'
            },
            UpdateExpression='''
                SET #status = :new_status,
                    #updatedAt = :timestamp,
                    #version = :new_version,
                    #statusHistory = :status_history,
                    GSI2PK = :gsi2pk,
                    GSI2SK = :gsi2sk
            ''',
            ConditionExpression='#version = :current_version',
            ExpressionAttributeNames={
                '#status': 'status',
                '#updatedAt': 'updatedAt',
                '#version': 'version',
                '#statusHistory': 'statusHistory'
            },
            ExpressionAttributeValues={
                ':new_status': next_status,
                ':timestamp': timestamp,
                ':new_version': new_version,
                ':current_version': current_version,
                ':status_history': status_history,
                ':gsi2pk': f'STATUS#{next_status}',
                ':gsi2sk': f'{timestamp}#{order_id}'
            },
            ReturnValues='ALL_NEW'
        )
        
        logger.info(f'✅ Order {order_id} progressed from {current_status} to {next_status}')
        
        # Publish event for real-time updates
        try:
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.orders.demo',
                        'DetailType': 'ORDER_STATUS_UPDATED',
                        'Detail': json.dumps({
                            'orderId': order_id,
                            'previousStatus': current_status,
                            'newStatus': next_status,
                            'timestamp': timestamp,
                            'autoProgressed': True
                        }),
                        'EventBusName': 'default'
                    }
                ]
            )
        except Exception as e:
            logger.warning(f'Failed to publish event for order {order_id}: {e}')
        
        return True
        
    except Exception as e:
        logger.error(f'Error progressing order {order.get("orderId")}: {e}')
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for auto-progressing demo orders
    
    Can be triggered by:
    - EventBridge scheduled rule (every 10 seconds)
    - Manual invocation
    - Order creation event
    """
    logger.start_operation('auto_progress_demo_orders')
    
    try:
        # Get orders that need to be progressed
        orders_to_progress = get_orders_to_progress()
        
        if not orders_to_progress:
            logger.info('No orders to progress at this time')
            logger.end_operation('auto_progress_demo_orders', success=True)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No orders to progress',
                    'ordersProcessed': 0
                })
            }
        
        # Progress each order
        progressed_count = 0
        failed_count = 0
        
        for order in orders_to_progress:
            if progress_order(order):
                progressed_count += 1
            else:
                failed_count += 1
        
        logger.info(f'Progressed {progressed_count} orders, {failed_count} failed')
        logger.end_operation('auto_progress_demo_orders', success=True)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully progressed {progressed_count} orders',
                'ordersProcessed': progressed_count,
                'ordersFailed': failed_count
            })
        }
        
    except Exception as e:
        logger.error(f'Error in auto-progress handler: {e}')
        logger.end_operation('auto_progress_demo_orders', success=False)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to auto-progress orders',
                'message': str(e)
            })
        }
