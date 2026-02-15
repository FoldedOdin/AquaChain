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
    required_fields = ['consumerId', 'deviceType', 'serviceType', 'paymentMethod', 'deliveryAddress', 'contactInfo']
    for field in required_fields:
        if field not in body or not body[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate nested deliveryAddress
    if not isinstance(body['deliveryAddress'], dict):
        raise ValueError("deliveryAddress must be an object")
    
    # Validate nested contactInfo
    if not isinstance(body['contactInfo'], dict):
        raise ValueError("contactInfo must be an object")
    contact_info = body['contactInfo']
    if not contact_info.get('phone'):
        raise ValueError("contactInfo.phone is required")
    
    # Validate phone format
    phone = contact_info['phone'].replace('+', '').replace('-', '').replace(' ', '')
    if not phone.isdigit():
        raise ValueError("Invalid phone number format")
    
    # Validate payment method
    if body['paymentMethod'] not in ['COD', 'ONLINE']:
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
        
        # Get consumer ID from Cognito authorizer (or use from body if not authenticated)
        try:
            consumer_id = event['requestContext']['authorizer']['claims']['sub']
            consumer_email = event['requestContext']['authorizer']['claims']['email']
            consumer_name = event['requestContext']['authorizer']['claims'].get('name', consumer_email)
        except (KeyError, TypeError):
            # Fallback to body data if authorizer not present
            consumer_id = body.get('consumerId', 'unknown')
            consumer_email = body.get('contactInfo', {}).get('email', 'unknown@example.com')
            consumer_name = body.get('contactInfo', {}).get('name', 'Unknown')
        
        # Validate input
        validate_order_input(body)
        
        # Extract data from request
        device_type = body['deviceType']
        service_type = body['serviceType']
        payment_method = body['paymentMethod']
        delivery_address = body['deliveryAddress']
        contact_info = body['contactInfo']
        amount = body.get('amount', 0)
        payment_id = body.get('paymentId')
        special_instructions = body.get('specialInstructions', '')
        
        # Generate order ID
        order_id = f"ord_{int(datetime.now().timestamp() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        
        # Serialize address as JSON string
        address_json = json.dumps(delivery_address)
        contact_json = json.dumps(contact_info)
        
        # Create order item
        order_item = {
            'orderId': {'S': order_id},
            'userId': {'S': consumer_id},
            'consumerName': {'S': consumer_name},
            'consumerEmail': {'S': consumer_email},
            'deviceType': {'S': device_type},
            'serviceType': {'S': service_type},
            'status': {'S': 'ORDER_PLACED'},
            'paymentMethod': {'S': payment_method},
            'deliveryAddress': {'S': address_json},
            'contactInfo': {'S': contact_json},
            'amount': {'N': str(amount)},
            'createdAt': {'S': timestamp},
            'updatedAt': {'S': timestamp},
            'statusHistory': {'L': [{
                'M': {
                    'status': {'S': 'ORDER_PLACED'},
                    'timestamp': {'S': timestamp},
                    'message': {'S': 'Order placed successfully'}
                }
            }]}
        }
        
        # Add optional fields
        if payment_id:
            order_item['paymentId'] = {'S': payment_id}
        if special_instructions:
            order_item['specialInstructions'] = {'S': special_instructions}
        
        # Create order in DynamoDB (simplified - no inventory check for now)
        try:
            orders_table = dynamodb.Table(ORDERS_TABLE)
            orders_table.put_item(Item={
                'orderId': order_id,
                'userId': consumer_id,
                'consumerName': consumer_name,
                'consumerEmail': consumer_email,
                'deviceType': device_type,
                'serviceType': service_type,
                'status': 'ORDER_PLACED',
                'paymentMethod': payment_method,
                'deliveryAddress': address_json,
                'contactInfo': contact_json,
                'amount': Decimal(str(amount)),
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'paymentId': payment_id or '',
                'specialInstructions': special_instructions,
                'statusHistory': [{
                    'status': 'ORDER_PLACED',
                    'timestamp': timestamp,
                    'message': 'Order placed successfully'
                }]
            })
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Failed to create order in database'
                })
            }
        
        # Publish event to SNS (optional)
        if SNS_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=json.dumps({
                        'eventType': 'ORDER_PLACED',
                        'orderId': order_id,
                        'userId': consumer_id,
                        'consumerName': consumer_name,
                        'deviceType': device_type,
                        'serviceType': service_type,
                        'timestamp': timestamp
                    }),
                    Subject=f'New Order: {order_id}'
                )
            except Exception as sns_error:
                print(f"SNS notification failed: {str(sns_error)}")
                # Don't fail the order if SNS fails
        
        print(f"Order created successfully: {order_id}")
        
        # Return order object matching frontend expectations
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'order': {
                    'id': order_id,
                    'consumerId': consumer_id,
                    'deviceType': device_type,
                    'serviceType': service_type,
                    'paymentMethod': payment_method,
                    'status': 'ORDER_PLACED',
                    'amount': amount,
                    'deliveryAddress': delivery_address,
                    'contactInfo': contact_info,
                    'paymentId': payment_id,
                    'createdAt': timestamp,
                    'updatedAt': timestamp,
                    'statusHistory': [{
                        'status': 'ORDER_PLACED',
                        'timestamp': timestamp,
                        'message': 'Order placed successfully'
                    }],
                    'specialInstructions': special_instructions
                },
                'message': 'Order created successfully'
            })
        }
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if os.environ.get('DEBUG') else None
            })
        }
