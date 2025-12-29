"""
Get shipment status and timeline for UI display
"""
import boto3
import json
import os
from typing import Dict, Optional

dynamodb = boto3.resource('dynamodb')
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')


def handler(event, context):
    """
    Get shipment details by shipment_id or order_id
    
    GET /api/shipments/{shipmentId}
    GET /api/shipments?orderId=xxx
    """
    try:
        shipment_id = event.get('pathParameters', {}).get('shipmentId')
        order_id = event.get('queryStringParameters', {}).get('orderId') if event.get('queryStringParameters') else None
        
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        if shipment_id:
            response = shipments_table.get_item(Key={'shipment_id': shipment_id})
            shipment = response.get('Item')
        elif order_id:
            response = shipments_table.query(
                IndexName='order_id-index',
                KeyConditionExpression='order_id = :order_id',
                ExpressionAttributeValues={':order_id': order_id}
            )
            shipment = response['Items'][0] if response['Items'] else None
        else:
            return error_response(400, 'shipmentId or orderId required')
        
        if not shipment:
            return error_response(404, 'Shipment not found')
        
        # Calculate delivery progress
        progress = calculate_delivery_progress(shipment)
        
        # Format timeline for UI
        formatted_timeline = format_timeline(shipment.get('timeline', []))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'shipment': {
                    'shipment_id': shipment['shipment_id'],
                    'order_id': shipment['order_id'],
                    'tracking_number': shipment['tracking_number'],
                    'courier_name': shipment['courier_name'],
                    'internal_status': shipment['internal_status'],
                    'destination': shipment.get('destination', {}),
                    'estimated_delivery': shipment.get('estimated_delivery'),
                    'delivered_at': shipment.get('delivered_at'),
                    'created_at': shipment['created_at'],
                    'timeline': formatted_timeline
                },
                'progress': progress
            }, default=str)
        }
        
    except Exception as e:
        print(f"Error getting shipment: {str(e)}")
        return error_response(500, f'Internal server error: {str(e)}')


def calculate_delivery_progress(shipment: Dict) -> Dict:
    """
    Calculate delivery progress percentage and status
    """
    status_progress = {
        'shipment_created': 10,
        'picked_up': 30,
        'in_transit': 60,
        'out_for_delivery': 90,
        'delivered': 100,
        'delivery_failed': 0,
        'returned': 0,
        'cancelled': 0
    }
    
    current_status = shipment['internal_status']
    percentage = status_progress.get(current_status, 0)
    
    # Determine status color
    status_colors = {
        'shipment_created': 'blue',
        'picked_up': 'blue',
        'in_transit': 'blue',
        'out_for_delivery': 'green',
        'delivered': 'green',
        'delivery_failed': 'red',
        'returned': 'orange',
        'cancelled': 'gray'
    }
    
    # Determine status message
    status_messages = {
        'shipment_created': 'Shipment created and ready for pickup',
        'picked_up': 'Package picked up by courier',
        'in_transit': 'Package is on the way',
        'out_for_delivery': 'Out for delivery today',
        'delivered': 'Successfully delivered',
        'delivery_failed': 'Delivery attempt failed',
        'returned': 'Package returned to sender',
        'cancelled': 'Shipment cancelled'
    }
    
    return {
        'percentage': percentage,
        'current_status': current_status,
        'status_display': current_status.replace('_', ' ').title(),
        'status_color': status_colors.get(current_status, 'gray'),
        'status_message': status_messages.get(current_status, 'Status update'),
        'estimated_delivery': shipment.get('estimated_delivery'),
        'actual_delivery': shipment.get('delivered_at'),
        'timeline_count': len(shipment.get('timeline', [])),
        'is_completed': current_status in ['delivered', 'returned', 'cancelled']
    }


def format_timeline(timeline: list) -> list:
    """
    Format timeline for UI display with icons and colors
    """
    status_icons = {
        'shipment_created': '📦',
        'picked_up': '🚚',
        'in_transit': '🛣️',
        'out_for_delivery': '🚛',
        'delivered': '✅',
        'delivery_failed': '❌',
        'returned': '↩️',
        'cancelled': '🚫'
    }
    
    formatted = []
    for entry in timeline:
        formatted.append({
            'status': entry['status'],
            'status_display': entry['status'].replace('_', ' ').title(),
            'icon': status_icons.get(entry['status'], '📍'),
            'timestamp': entry['timestamp'],
            'location': entry.get('location', 'Unknown'),
            'description': entry.get('description', 'Status update')
        })
    
    return formatted


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
