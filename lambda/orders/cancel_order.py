"""
Lambda function to cancel an order
"""
import boto3
import json
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'aquachain-orders')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def cors_headers():
    """Return consistent CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'PUT,DELETE,OPTIONS'
    }


def handler(event, context):
    """
    Cancel an order
    
    Args:
        event: API Gateway event with orderId in path parameters
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Safely get order ID from path parameters
        path_params = event.get('pathParameters') or {}
        order_id = path_params.get('orderId')
        
        if not order_id:
            return {
                'statusCode': 400,
                'headers': cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing orderId in path'
                })
            }
        
        # Parse request body for cancellation reason
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            except json.JSONDecodeError:
                pass
        
        cancellation_reason = body.get('cancellationReason', body.get('reason', 'No reason provided'))
        
        # Get consumer ID from Cognito authorizer
        try:
            consumer_id = event['requestContext']['authorizer']['claims']['sub']
        except (KeyError, TypeError):
            return {
                'statusCode': 401,
                'headers': cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': 'Unauthorized'
                })
            }
        
        # Get the order from DynamoDB
        orders_table = dynamodb.Table(ORDERS_TABLE)
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': 'Order not found'
                })
            }
        
        order = response['Item']
        
        # Verify the order belongs to the user (check both userId and consumerId for compatibility)
        order_owner = order.get('userId') or order.get('consumerId')
        if order_owner != consumer_id:
            return {
                'statusCode': 403,
                'headers': cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': 'You do not have permission to cancel this order'
                })
            }
        
        # Check if order can be cancelled (only ORDER_PLACED or PENDING status)
        current_status = order.get('status', '')
        if current_status not in ['ORDER_PLACED', 'PENDING', 'PENDING_CONFIRMATION']:
            return {
                'statusCode': 400,
                'headers': cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'error': f'Order cannot be cancelled. Current status: {current_status}'
                })
            }
        
        # Update order status to CANCELLED
        timestamp = datetime.utcnow().isoformat()
        
        # Get existing status history
        status_history = order.get('statusHistory', [])
        status_history.append({
            'status': 'CANCELLED',
            'timestamp': timestamp,
            'message': f'Order cancelled by customer. Reason: {cancellation_reason}'
        })
        
        # Update the order with cancellation reason and return updated item
        update_response = orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, updatedAt = :timestamp, statusHistory = :history, cancellationReason = :reason',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'CANCELLED',
                ':timestamp': timestamp,
                ':history': status_history,
                ':reason': cancellation_reason
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_order = update_response.get('Attributes', {})
        
        print(f"Order {order_id} cancelled successfully by user {consumer_id}")
        
        # Return the full updated order object
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Order cancelled successfully',
                'order': {
                    'id': updated_order.get('orderId'),
                    'consumerId': updated_order.get('userId') or updated_order.get('consumerId'),
                    'status': updated_order.get('status'),
                    'cancellationReason': updated_order.get('cancellationReason'),
                    'updatedAt': updated_order.get('updatedAt'),
                    'statusHistory': updated_order.get('statusHistory', [])
                }
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error cancelling order: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if os.environ.get('DEBUG') else None
            })
        }
