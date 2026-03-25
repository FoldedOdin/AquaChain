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
        
        # Also check for consumerId query param as a fallback
        query_params = event.get('queryStringParameters') or {}
        param_consumer_id = query_params.get('consumerId') or query_params.get('userId')
        
        print(f"JWT sub (consumer_id): {consumer_id}")
        print(f"Query param consumerId: {param_consumer_id}")
        
        # Query orders table for this user
        orders_table = dynamodb.Table(ORDERS_TABLE)
        
        # Query by consumerId using userId-createdAt-index
        def query_orders_by_user_id(uid):
            try:
                response = orders_table.query(
                    IndexName='userId-createdAt-index',
                    KeyConditionExpression='userId = :consumer_id',
                    ExpressionAttributeValues={
                        ':consumer_id': uid
                    },
                    ScanIndexForward=False  # Sort by createdAt descending (most recent first)
                )
                return response.get('Items', [])
            except Exception as query_error:
                print(f"Query failed for userId={uid}: {str(query_error)}")
                import traceback
                traceback.print_exc()
                return []
        
        orders = query_orders_by_user_id(consumer_id)
        print(f"Found {len(orders)} orders for JWT sub: {consumer_id}")
        
        # Fallback: if no orders found via JWT sub, try the consumerId query param
        if not orders and param_consumer_id and param_consumer_id != consumer_id:
            print(f"No orders found via JWT sub, trying query param consumerId: {param_consumer_id}")
            orders = query_orders_by_user_id(param_consumer_id)
            print(f"Found {len(orders)} orders for query param consumerId: {param_consumer_id}")
        
        # Second fallback: scan by consumerId field (some orders may use consumerId instead of userId)
        if not orders:
            try:
                from boto3.dynamodb.conditions import Attr
                ids_to_try = list({consumer_id, param_consumer_id} - {None})
                for uid in ids_to_try:
                    scan_response = orders_table.scan(
                        FilterExpression=Attr('consumerId').eq(uid),
                        Limit=100
                    )
                    scan_orders = scan_response.get('Items', [])
                    if scan_orders:
                        print(f"Found {len(scan_orders)} orders via consumerId scan for: {uid}")
                        orders = scan_orders
                        break
            except Exception as scan_err:
                print(f"consumerId scan fallback failed: {str(scan_err)}")
        
        # Transform orders to match frontend expectations
        transformed_orders = []
        for order in orders:
            # Get delivery address and contact info - handle both string and dict formats
            delivery_address = order.get('deliveryAddress', {})
            contact_info = order.get('contactInfo', {})
            status_history = order.get('statusHistory', [])
            
            # Handle deliveryAddress - it might be a string or dict
            if isinstance(delivery_address, str):
                try:
                    delivery_address = json.loads(delivery_address)
                except (json.JSONDecodeError, TypeError):
                    delivery_address = {}
            elif not isinstance(delivery_address, dict):
                delivery_address = {}
            
            # Handle contactInfo - it might be a string or dict
            if isinstance(contact_info, str):
                try:
                    contact_info = json.loads(contact_info)
                except (json.JSONDecodeError, TypeError):
                    contact_info = {}
            elif not isinstance(contact_info, dict):
                contact_info = {}
            
            # Format address as a string for frontend display
            address_str = ''
            if delivery_address and isinstance(delivery_address, dict):
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
            phone = contact_info.get('phone', '') if isinstance(contact_info, dict) else ''
            
            # Extract technician assignment details
            technician_assignment = order.get('technicianAssignment', {})
            assigned_technician = order.get('assignedTechnician')
            
            # Build technician object if assignment exists
            technician = None
            if technician_assignment or assigned_technician or order.get('assignedTechnicianName'):
                # Get technician data from the order directly if available
                existing_technician = order.get('technician', {})
                
                # Build comprehensive technician object
                technician = {
                    'id': (existing_technician.get('id') or 
                          technician_assignment.get('technicianId') or 
                          assigned_technician or ''),
                    'name': (existing_technician.get('name') or 
                            technician_assignment.get('technicianName') or
                            order.get('assignedTechnicianName') or ''),
                    'phone': (existing_technician.get('phone') or 
                             technician_assignment.get('technicianPhone') or ''),
                    'email': (existing_technician.get('email') or 
                             technician_assignment.get('technicianEmail') or ''),
                    'address': (existing_technician.get('address') or 
                               technician_assignment.get('technicianAddress') or ''),
                    'experience': (existing_technician.get('experience') or 
                                  technician_assignment.get('experience') or ''),
                    'rating': float(existing_technician.get('rating', 0) or 
                                   technician_assignment.get('rating', 0) or 0),
                    'estimatedArrival': technician_assignment.get('estimatedArrival', ''),
                    'distance': float(technician_assignment.get('distance', 0) or 0),
                    'status': (existing_technician.get('status') or 
                              technician_assignment.get('status', 'assigned'))
                }
                # Only include technician object if we have meaningful data
                if not technician['name'] and not technician['phone'] and not technician['id']:
                    technician = None

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
                'specialInstructions': order.get('specialInstructions', ''),
                # Technician assignment details
                'assignedTechnician': assigned_technician,
                'assignedTechnicianName': (
                    technician_assignment.get('technicianName') or
                    order.get('assignedTechnicianName') or
                    ''
                ),
                'technician': technician,
                'technicianAssignment': technician_assignment
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
