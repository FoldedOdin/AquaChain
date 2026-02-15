"""
Lambda function to get user's order history
"""
import boto3
import json
import os
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
    Get order history for the authenticated user
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with order list
    """
    try:
        # Get consumer ID from Cognito authorizer
        try:
            consumer_id = event['requestContext']['authorizer']['claims']['sub']
        except (KeyError, TypeError):
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Unauthorized'
                })
            }
        
        # Query orders table for this user
        orders_table = dynamodb.Table(ORDERS_TABLE)
        
        # Query by userId (assuming there's a GSI on userId)
        try:
            response = orders_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression='userId = :userId',
                ExpressionAttributeValues={
                    ':userId': consumer_id
                },
                ScanIndexForward=False  # Sort by createdAt descending
            )
            orders = response.get('Items', [])
        except Exception as query_error:
            # If GSI doesn't exist, fall back to scan (not recommended for production)
            print(f"Query failed, falling back to scan: {str(query_error)}")
            response = orders_table.scan(
                FilterExpression='userId = :userId',
                ExpressionAttributeValues={
                    ':userId': consumer_id
                }
            )
            orders = response.get('Items', [])
        
        # Transform orders to match frontend expectations
        transformed_orders = []
        for order in orders:
            # Parse JSON strings back to objects
            delivery_address = json.loads(order.get('deliveryAddress', '{}')) if isinstance(order.get('deliveryAddress'), str) else order.get('deliveryAddress', {})
            contact_info = json.loads(order.get('contactInfo', '{}')) if isinstance(order.get('contactInfo'), str) else order.get('contactInfo', {})
            status_history = order.get('statusHistory', [])
            
            transformed_order = {
                'orderId': order.get('orderId'),  # Keep as orderId for frontend
                'id': order.get('orderId'),  # Also include id for compatibility
                'consumerId': order.get('userId'),
                'deviceType': order.get('deviceType'),
                'deviceSKU': order.get('deviceType'),  # Map deviceType to deviceSKU for frontend compatibility
                'serviceType': order.get('serviceType'),
                'paymentMethod': order.get('paymentMethod'),
                'status': order.get('status'),
                'amount': int(order.get('amount', 0)) if isinstance(order.get('amount'), Decimal) else order.get('amount', 0),
                'deliveryAddress': delivery_address,
                'contactInfo': contact_info,
                'paymentId': order.get('paymentId', ''),
                'createdAt': order.get('createdAt'),
                'updatedAt': order.get('updatedAt'),
                'statusHistory': status_history,
                'specialInstructions': order.get('specialInstructions', '')
            }
            transformed_orders.append(transformed_order)
        
        # Sort by createdAt descending
        transformed_orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        print(f"Retrieved {len(transformed_orders)} orders for user {consumer_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'orders': transformed_orders
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error retrieving orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if os.environ.get('DEBUG') else None
            })
        }
