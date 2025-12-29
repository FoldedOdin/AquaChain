"""
Lambda function to create shipment and integrate with courier API
"""
import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import requests

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
COURIER_API_KEY = os.environ.get('COURIER_API_KEY', '')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def handler(event, context):
    """
    Create shipment record and register with courier service
    
    Input:
    {
      "order_id": "ord_xxx",
      "courier_name": "Delhivery",
      "service_type": "Surface",
      "destination": {...},
      "package_details": {...}
    }
    """
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        order_id = body['order_id']
        
        # Fetch order details
        orders_table = dynamodb.Table(ORDERS_TABLE)
        order_response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in order_response:
            return error_response(404, 'Order not found')
        
        order = order_response['Item']
        
        # Generate shipment ID
        shipment_id = f"ship_{int(datetime.now().timestamp() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        
        # Call courier API to create shipment
        courier_response = create_courier_shipment(
            courier_name=body['courier_name'],
            destination=body['destination'],
            package=body['package_details'],
            order_id=order_id
        )
        
        tracking_number = courier_response['tracking_number']
        estimated_delivery = courier_response['estimated_delivery']
        
        # Create shipment record
        shipment_item = {
            'shipment_id': shipment_id,
            'order_id': order_id,
            'device_id': order.get('device_id', ''),
            'tracking_number': tracking_number,
            'courier_name': body['courier_name'],
            'courier_service_type': body.get('service_type', 'Surface'),
            'internal_status': 'shipment_created',
            'external_status': 'shipped',
            'destination': body['destination'],
            'estimated_delivery': estimated_delivery,
            'timeline': [{
                'status': 'shipment_created',
                'timestamp': timestamp,
                'location': body.get('origin', {}).get('address', 'Warehouse'),
                'description': 'Shipment created and handed to courier'
            }],
            'webhook_events': [],
            'retry_config': {
                'max_retries': 3,
                'retry_count': 0,
                'last_retry_at': None
            },
            'metadata': body['package_details'],
            'created_at': timestamp,
            'updated_at': timestamp,
            'delivered_at': None,
            'failed_at': None,
            'created_by': event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub', 'system')
        }
        
        # Atomic transaction: Create shipment + Update order
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': SHIPMENTS_TABLE,
                        'Item': convert_to_dynamodb_format(shipment_item)
                    }
                },
                {
                    'Update': {
                        'TableName': ORDERS_TABLE,
                        'Key': {'orderId': {'S': order_id}},
                        'UpdateExpression': 'SET #status = :shipped, tracking_number = :tracking, shipment_id = :shipment_id, shipped_at = :time',
                        'ExpressionAttributeNames': {'#status': 'status'},
                        'ExpressionAttributeValues': {
                            ':shipped': {'S': 'shipped'},
                            ':tracking': {'S': tracking_number},
                            ':shipment_id': {'S': shipment_id},
                            ':time': {'S': timestamp}
                        }
                    }
                }
            ]
        )
        
        # Send notifications
        if SNS_TOPIC_ARN:
            notify_stakeholders(order, shipment_item, 'shipment_created')
        
        print(f"Shipment created successfully: {shipment_id}")
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'shipment_id': shipment_id,
                'tracking_number': tracking_number,
                'estimated_delivery': estimated_delivery
            })
        }
        
    except Exception as e:
        print(f"Error creating shipment: {str(e)}")
        return error_response(500, f'Internal server error: {str(e)}')


def create_courier_shipment(courier_name: str, destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Integrate with courier API
    """
    if courier_name.lower() == 'delhivery':
        return create_delhivery_shipment(destination, package, order_id)
    elif courier_name.lower() == 'bluedart':
        return create_bluedart_shipment(destination, package, order_id)
    else:
        # Mock response for testing
        return {
            'tracking_number': f"MOCK{int(datetime.now().timestamp())}",
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }


def create_delhivery_shipment(destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Create shipment via Delhivery API
    """
    if not COURIER_API_KEY:
        # Return mock for development
        return {
            'tracking_number': f"DELHUB{int(datetime.now().timestamp())}",
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }
    
    try:
        response = requests.post(
            'https://track.delhivery.com/api/cmu/create.json',
            headers={
                'Authorization': f'Token {COURIER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'shipments': [{
                    'name': destination['contact_name'],
                    'add': destination['address'],
                    'pin': destination['pincode'],
                    'phone': destination['contact_phone'],
                    'payment_mode': 'Prepaid',
                    'return_name': 'AquaChain Warehouse',
                    'return_add': 'Mumbai',
                    'return_pin': '400001',
                    'return_phone': '+919999999999',
                    'weight': package.get('weight', '0.5'),
                    'seller_name': 'AquaChain',
                    'products_desc': 'IoT Water Quality Monitor',
                    'hsn_code': '85176290',
                    'cod_amount': '0',
                    'order': f"AQUA{order_id}",
                    'total_amount': str(package.get('declared_value', 5000))
                }],
                'pickup_location': {
                    'name': 'Mumbai Warehouse'
                }
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            'tracking_number': data['packages'][0]['waybill'],
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }
    
    except Exception as e:
        print(f"Delhivery API error: {str(e)}")
        raise


def create_bluedart_shipment(destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Create shipment via BlueDart API (placeholder)
    """
    return {
        'tracking_number': f"BD{int(datetime.now().timestamp())}",
        'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat()
    }


def convert_to_dynamodb_format(item: Dict) -> Dict:
    """
    Convert Python dict to DynamoDB format
    """
    def convert_value(val):
        if isinstance(val, str):
            return {'S': val}
        elif isinstance(val, (int, float)):
            return {'N': str(val)}
        elif isinstance(val, bool):
            return {'BOOL': val}
        elif isinstance(val, dict):
            return {'M': {k: convert_value(v) for k, v in val.items()}}
        elif isinstance(val, list):
            return {'L': [convert_value(v) for v in val]}
        elif val is None:
            return {'NULL': True}
        else:
            return {'S': str(val)}
    
    return {k: convert_value(v) for k, v in item.items()}


def notify_stakeholders(order: Dict, shipment: Dict, event_type: str):
    """
    Send notifications to stakeholders
    """
    message = {
        'eventType': event_type,
        'shipment_id': shipment['shipment_id'],
        'order_id': shipment['order_id'],
        'tracking_number': shipment['tracking_number'],
        'estimated_delivery': shipment['estimated_delivery'],
        'consumer_email': order.get('consumerEmail'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps(message),
        Subject=f'Shipment Created: {shipment["tracking_number"]}'
    )


def error_response(status_code: int, message: str) -> Dict:
    """
    Return error response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }
