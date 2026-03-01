"""
Lambda function to create device orders with atomic inventory reservation
"""
import boto3
import json
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
INVENTORY_TABLE = os.environ.get('INVENTORY_TABLE', 'Inventory')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')


def validate_order_input(body):
    """Validate order input data"""
    required_fields = ['deviceSKU', 'address', 'phone', 'paymentMethod', 'preferredSlot']
    for field in required_fields:
        if field not in body or not body[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate phone format
    if not body['phone'].replace('+', '').replace('-', '').isdigit():
        raise ValueError("Invalid phone number format")
    
    # Validate payment method
    if body['paymentMethod'] not in ['COD', 'ONLINE', 'UPI']:
        raise ValueError("Invalid payment method")
    
    return True


def handler(event, context):
    """
    Create a new device order with atomic inventory reservation
    
    Args:
        event: API Gateway event with order details
        context: Lambda context
        
    Returns:
        API Gateway response with order ID and status
    """
    try:
        # Parse request
        body = json.loads(event['body'])
        
        # Get consumer ID from Cognito authorizer
        consumer_id = event['requestContext']['authorizer']['claims']['sub']
        consumer_email = event['requestContext']['authorizer']['claims']['email']
        consumer_name = event['requestContext']['authorizer']['claims'].get('name', consumer_email)
        
        # Validate input
        validate_order_input(body)
        
        # Generate order ID
        order_id = f"ord_{int(datetime.now().timestamp() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        
        # DynamoDB Transaction - Atomic operation
        try:
            dynamodb.meta.client.transact_write_items(
                TransactItems=[
                    {
                        # Create order
                        'Put': {
                            'TableName': ORDERS_TABLE,
                            'Item': {
                                'orderId': {'S': order_id},
                                'userId': {'S': consumer_id},
                                'consumerName': {'S': consumer_name},
                                'consumerEmail': {'S': consumer_email},
                                'deviceSKU': {'S': body['deviceSKU']},
                                'status': {'S': 'PENDING'},
                                'address': {'S': body['address']},
                                'phone': {'S': body['phone']},
                                'paymentMethod': {'S': body['paymentMethod']},
                                'preferredSlot': {'S': body['preferredSlot']},
                                'createdAt': {'S': timestamp},
                                'updatedAt': {'S': timestamp},
                                'auditTrail': {'L': [{
                                    'M': {
                                        'action': {'S': 'ORDER_CREATED'},
                                        'by': {'S': consumer_id},
                                        'at': {'S': timestamp}
                                    }
                                }]}
                            }
                        }
                    },
                    {
                        # Reserve inventory
                        'Update': {
                            'TableName': INVENTORY_TABLE,
                            'Key': {'sku': {'S': body['deviceSKU']}},
                            'UpdateExpression': 'SET reservedCount = if_not_exists(reservedCount, :zero) + :qty, availableCount = availableCount - :qty, updatedAt = :time',
                            'ConditionExpression': 'availableCount >= :qty',
                            'ExpressionAttributeValues': {
                                ':qty': {'N': '1'},
                                ':zero': {'N': '0'},
                                ':time': {'S': timestamp}
                            }
                        }
                    }
                ]
            )
        except dynamodb.meta.client.exceptions.TransactionCanceledException as e:
            print(f"Transaction cancelled: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Insufficient inventory or device SKU not found'
                })
            }
        
        # Publish event to SNS
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({
                    'eventType': 'ORDER_PLACED',
                    'orderId': order_id,
                    'userId': consumer_id,
                    'consumerName': consumer_name,
                    'deviceSKU': body['deviceSKU'],
                    'timestamp': timestamp
                }),
                Subject=f'New Order: {order_id}'
            )
        
        print(f"Order created successfully: {order_id}")
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'orderId': order_id,
                'status': 'PENDING',
                'message': 'Order created successfully'
            })
        }
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }
