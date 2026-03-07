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
        
        # Query by consumerId using GSI1 (CONSUMER#{consumerId})
        try:
            response = orders_table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :consumer_pk',
                ExpressionAttributeValues={
                    ':consumer_pk': f'CONSUMER#{consumer_id}'
                },
                ScanIndexForward=False  # Sort by createdAt descending (most recent first)
            )
            orders = response.get('Items', [])
        except Exception as query_error:
            # Log error and return empty list
            print(f"Query failed: {str(query_error)}")
            import traceback
            traceback.print_exc()
            orders = []
        
        # Transform orders to match frontend expectations
        transformed_orders = []
        for order in orders:
            # Get delivery address and contact info (already objects, not JSON strings)
            delivery_address = order.get('deliveryAddress', {})
            contact_info = order.get('contactInfo', {})
            status_history = order.get('statusHistory', [])
            
            # Format address as a string for frontend display
            address_str = ''
            if delivery_address:
                address_parts = []
                if delivery_address.get('street'):
                    address_parts.append(delivery_address['street'])
                if delivery_address.get('city'):
                    address_parts.append(delivery_address['city'])
                if delivery_address.get('state'):
                    address_parts.append(delivery_address['state'])
                if delivery_address.get('pincode'):
                    address_parts.append(delivery_address['pincode'])
                address_str = ', '.join(address_parts) if address_parts else ''
            
            # Extract phone from contactInfo
            phone = contact_info.get('phone', '') if contact_info else ''
            
            transformed_order = {
                'orderId': order.get('orderId'),
                'id': order.get('orderId'),  # Also include id for compatibility
                'consumerId': order.get('consumerId'),
                'deviceType': order.get('deviceType'),
                'deviceSKU': order.get('deviceType'),  # Map deviceType to deviceSKU for frontend compatibility
                'serviceType': order.get('serviceType'),
                'paymentMethod': order.get('paymentMethod'),
                'status': order.get('status'),
                'amount': int(order.get('amount', 0)) if isinstance(order.get('amount'), Decimal) else order.get('amount', 0),
                'deliveryAddress': delivery_address,
                'contactInfo': contact_info,
                # Add flattened fields for frontend compatibility
                'address': address_str,
                'phone': phone,
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
