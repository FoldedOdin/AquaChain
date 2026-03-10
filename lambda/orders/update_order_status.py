"""
Lambda function to update order status
Simple, dependency-free implementation
"""
import boto3
import json
import os
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'aquachain-orders')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def handler(event, context):
    """
    Update order status
    
    Args:
        event: API Gateway event with orderId in path and status in body
        context: Lambda context
        
    Returns:
        API Gateway response with updated order
    """
    try:
        # Extract order ID from path parameters
        path_parameters = event.get('pathParameters') or {}
        order_id = path_parameters.get('orderId')
        
        if not order_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'PUT,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Order ID is required'
                })
            }
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'PUT,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                })
            }
        
        new_status = body.get('status')
        reason = body.get('reason', f'Status updated to {new_status}')
        
        if not new_status:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'PUT,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Status is required'
                })
            }
        
        # Validate status - aligned with frontend OrderStatus enum
        valid_statuses = [
            'PENDING_PAYMENT', 'PENDING_CONFIRMATION', 'ORDER_PLACED',
            'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED', 'FAILED'
        ]
        if new_status not in valid_statuses:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'PUT,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                })
            }
        
        # Update order in DynamoDB
        orders_table = dynamodb.Table(ORDERS_TABLE)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create new status history entry
        new_history_entry = {
            'status': new_status,
            'timestamp': timestamp,
            'message': reason,
            'metadata': {}
        }
        
        # Update order in DynamoDB using atomic list_append
        # This handles missing statusHistory gracefully
        try:
            update_response = orders_table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET #status = :status, updatedAt = :timestamp, statusHistory = list_append(if_not_exists(statusHistory, :emptyList), :newEntry)',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': new_status,
                    ':timestamp': timestamp,
                    ':emptyList': [],
                    ':newEntry': [new_history_entry]
                },
                ConditionExpression='attribute_exists(orderId)',
                ReturnValues='ALL_NEW'
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'PUT,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Order not found'
                })
            }
        
        updated_order = update_response['Attributes']
        
        print(f"✅ Updated order {order_id} to status {new_status}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'PUT,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': updated_order,
                'message': f'Order status updated to {new_status}'
            }, cls=DecimalEncoder)
        }
        
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"❌ Order not found: {order_id}")
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'PUT,OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Order not found'
            })
        }
    except dynamodb.meta.client.exceptions.ValidationException as e:
        print(f"❌ DynamoDB validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'PUT,OPTIONS',
                'x-error-code': 'VALIDATION_ERROR'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Invalid update expression or attribute',
                'details': str(e) if os.environ.get('DEBUG') else None
            })
        }
    except dynamodb.meta.client.exceptions.ProvisionedThroughputExceededException:
        print(f"❌ DynamoDB throttled")
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'PUT,OPTIONS',
                'x-error-code': 'THROTTLED'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Service temporarily unavailable, please retry'
            })
        }
    except Exception as e:
        print(f"❌ Error updating order status: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'PUT,OPTIONS',
                'x-error-code': 'DATABASE_ERROR'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if os.environ.get('DEBUG') else None
            })
        }
