"""
Lambda function wrapper for orders API
Routes requests to appropriate handlers
"""
import json
from create_order import handler as create_order_handler
from get_orders import handler as get_orders_handler
from update_order_status import handler as update_status_handler
from cancel_order import handler as cancel_order_handler


def lambda_handler(event, context):
    """
    Main Lambda handler that routes requests to appropriate functions
    
    Routes:
    - POST /api/orders -> create_order
    - GET /api/orders -> get_orders
    - GET /api/orders/{orderId} -> get_order
    - PUT /api/orders/{orderId}/status -> update_status
    - PUT /api/orders/{orderId}/cancel -> cancel_order
    """
    try:
        # Extract HTTP method and path
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
        path = event.get('path', event.get('rawPath', ''))
        
        print(f"Request: {http_method} {path}")
        
        # Route based on method and path
        if http_method == 'POST' and path == '/api/orders':
            # Create order
            return create_order_handler(event, context)
        
        elif http_method == 'GET' and path == '/api/orders':
            # Get orders list
            return get_orders_handler(event, context)
        
        elif http_method == 'GET' and '/api/orders/' in path and '/status' not in path and '/cancel' not in path:
            # Get specific order
            return get_orders_handler(event, context)
        
        elif http_method == 'PUT' and '/status' in path:
            # Update order status
            return update_status_handler(event, context)
        
        elif http_method == 'PUT' and '/cancel' in path:
            # Cancel order
            return cancel_order_handler(event, context)
        
        else:
            # Unknown route
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Route not found: {http_method} {path}'
                })
            }
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
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
