"""
Technician Service Lambda Handler
Handles technician assignment, availability management, and service requests
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal

# Add shared utilities to path
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import local modules using absolute imports (Lambda-compatible)
from location_service import LocationService
from availability_manager import TechnicianAvailabilityManager
from assignment_algorithm import TechnicianAssignmentAlgorithm
from service_request_manager import ServiceRequestManager

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='technician-service')

# AWS clients
dynamodb = boto3.resource('dynamodb')
location_client = boto3.client('location')
sns = boto3.client('sns')
ses = boto3.client('ses', region_name='ap-south-1')

# Environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
SERVICE_REQUESTS_TABLE = os.environ.get('SERVICE_REQUESTS_TABLE', 'aquachain-service-requests')
LOCATION_MAP_NAME = os.environ.get('LOCATION_MAP_NAME', 'aquachain-map')
LOCATION_ROUTE_CALCULATOR = os.environ.get('LOCATION_ROUTE_CALCULATOR', 'aquachain-routes')
LOCATION_PLACE_INDEX = os.environ.get('LOCATION_PLACE_INDEX', 'aquachain-places')
ADMIN_TOPIC_ARN = os.environ.get('ADMIN_TOPIC_ARN')
NOTIFICATION_TOPIC_ARN = os.environ.get('NOTIFICATION_TOPIC_ARN')
WEBSOCKET_API_ENDPOINT = os.environ.get('WEBSOCKET_API_ENDPOINT')
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'contact.aquachain@gmail.com')

ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'aquachain-orders')

# Initialize service components
location_service = LocationService(LOCATION_MAP_NAME, LOCATION_ROUTE_CALCULATOR, LOCATION_PLACE_INDEX)
availability_manager = TechnicianAvailabilityManager(USERS_TABLE, SERVICE_REQUESTS_TABLE)
assignment_algorithm = TechnicianAssignmentAlgorithm(location_service, availability_manager, ADMIN_TOPIC_ARN)
service_request_manager = ServiceRequestManager(SERVICE_REQUESTS_TABLE, USERS_TABLE, WEBSOCKET_API_ENDPOINT, NOTIFICATION_TOPIC_ARN)

# DynamoDB tables
users_table = dynamodb.Table(USERS_TABLE)
service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)


def lambda_handler(event, context):
    """Main Lambda handler for technician service operations"""
    try:
        http_method = event.get('httpMethod', '')
        resource = event.get('resource', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Extract user info from JWT token
        user_info = extract_user_from_token(event)
        
        logger.info(f"Processing {http_method} {resource} for user {user_info.get('userId')}")
        
        # Route to appropriate handler
        if resource == '/api/v1/service-requests' and http_method == 'GET':
            return list_service_requests(query_parameters, user_info)
        elif resource == '/api/v1/service-requests' and http_method == 'POST':
            return create_service_request(body, user_info)
        elif resource == '/api/v1/service-requests/{requestId}' and http_method == 'GET':
            return get_service_request(path_parameters['requestId'], user_info)
        elif resource == '/api/v1/service-requests/{requestId}/status' and http_method == 'PUT':
            return update_service_request_status(path_parameters['requestId'], body, user_info)
        elif resource == '/api/v1/technician/tasks' and http_method == 'GET':
            return get_technician_tasks(query_parameters, user_info)
        elif resource == '/api/v1/technician/orders' and http_method == 'GET':
            return get_technician_orders(query_parameters, user_info)
        elif resource == '/api/v1/technician/tasks/{taskId}/accept' and http_method == 'POST':
            return accept_technician_task(path_parameters['taskId'], user_info)
        elif resource == '/api/v1/technician/tasks/{taskId}/status' and http_method == 'PUT':
            return update_technician_task_status(path_parameters['taskId'], body, user_info)
        elif resource == '/api/v1/technician/tasks/{taskId}/notes' and http_method == 'POST':
            return add_technician_task_note(path_parameters['taskId'], body, user_info)
        elif resource == '/api/v1/technician/tasks/{taskId}/complete' and http_method == 'POST':
            return complete_technician_task(path_parameters['taskId'], body, user_info)
        elif resource == '/api/v1/technician/tasks/history' and http_method == 'GET':
            return get_technician_task_history(query_parameters, user_info)
        elif resource == '/api/v1/technician/tasks/{taskId}/route' and http_method == 'GET':
            return get_task_route(path_parameters['taskId'], user_info)
        elif resource == '/api/v1/technician/location' and http_method == 'PUT':
            return update_technician_location(body, user_info)
        elif resource == '/api/v1/technicians/available' and http_method == 'GET':
            return get_available_technicians(query_parameters, user_info)
        elif resource == '/api/v1/technicians/{technicianId}/availability' and http_method == 'PUT':
            return update_technician_availability(path_parameters['technicianId'], body, user_info)
        elif resource == '/api/v1/technicians/{technicianId}/schedule' and http_method == 'PUT':
            return update_technician_schedule(path_parameters['technicianId'], body, user_info)
        elif resource == '/api/v1/technician/inventory' and http_method == 'GET':
            return get_technician_inventory(query_parameters, user_info)
        elif resource == '/api/v1/technician/inventory/checkout' and http_method == 'POST':
            return checkout_inventory_item(body, user_info)
        elif resource == '/api/v1/technician/inventory/return' and http_method == 'POST':
            return return_inventory_item(body, user_info)
        elif resource == '/api/v1/technician/inventory/request-restock' and http_method == 'POST':
            return request_inventory_restock(body, user_info)
        elif http_method == 'OPTIONS':
            return create_response(204, {})
        else:
            return create_response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def extract_user_from_token(event):
    """Extract user information from JWT token in request context"""
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    
    # Cognito User Pool authorizer puts claims under 'claims' key
    claims = authorizer.get('claims', {})
    
    # Extract groups from cognito:groups claim
    groups_str = claims.get('cognito:groups', '') or authorizer.get('cognito:groups', '')
    groups = groups_str.split(',') if groups_str else []
    
    # Determine role from groups (priority: administrators > technicians > consumers)
    role = 'consumer'  # Default role
    if 'administrators' in groups:
        role = 'admin'
    elif 'technicians' in groups:
        role = 'technician'
    elif 'consumers' in groups:
        role = 'consumer'
    
    user_info = {
        'userId': claims.get('sub') or authorizer.get('sub'),
        'email': claims.get('email') or authorizer.get('email'),
        'role': role,
        'groups': groups
    }
    
    # Log for debugging
    logger.info(f"Extracted user info - userId: {user_info['userId']}, role: {user_info['role']}, groups: {groups}")
    
    return user_info


def create_response(status_code: int, body: dict, headers: dict = None):
    """Create standardized API response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }


def create_service_request(request_data: dict, user_info: dict):
    """Create a new service request and assign technician"""
    try:
        # Use service request manager to create request
        result = service_request_manager.create_service_request(user_info['userId'], request_data)
        
        if not result['success']:
            return create_response(400, {'error': result['error']})
        
        service_request = result['service_request']
        
        # Attempt to assign technician
        assignment_result = assignment_algorithm.assign_technician(service_request)
        
        if assignment_result['success']:
            # Update service request with assignment
            technician = assignment_result['technician']
            update_result = service_request_manager.update_service_request_status(
                service_request['requestId'],
                'assigned',
                'system',
                f"Assigned to technician {technician['name']}",
                {
                    'technicianId': technician['userId'],
                    'estimatedArrival': assignment_result['estimated_arrival']
                }
            )
            
            if update_result['success']:
                service_request = update_result['service_request']
        else:
            # Assignment failed - request remains in pending status
            logger.warning(f"Failed to assign technician to request {service_request['requestId']}: {assignment_result.get('error')}")
        
        return create_response(201, service_request)
        
    except Exception as e:
        logger.error(f"Error creating service request: {str(e)}")
        return create_response(500, {'error': 'Failed to create service request'})


def list_service_requests(query_params: dict, user_info: dict):
    """List service requests with optional status filter"""
    try:
        # Get status filter if provided (can be comma-separated)
        status_filter = query_params.get('status', '')
        statuses = [s.strip() for s in status_filter.split(',')] if status_filter else []
        
        limit = int(query_params.get('limit', 50))
        
        # For technicians, only show their assigned requests
        if user_info['role'] == 'technician':
            result = service_request_manager.get_service_request_history(
                user_info['userId'], 
                'technician',
                limit,
                status_filter
            )
            
            if not result['success']:
                return create_response(400, {'error': result['error']})
            
            return create_response(200, {
                'serviceRequests': result['service_requests'],
                'count': len(result['service_requests'])
            })
        
        # For admins, show all requests (optionally filtered by status)
        elif user_info['role'] == 'administrator':
            if statuses:
                # Query by status using GSI or scan with filter
                items = []
                for status in statuses:
                    response = service_requests_table.scan(
                        FilterExpression='#status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': status},
                        Limit=limit
                    )
                    items.extend(response.get('Items', []))
            else:
                # Get all service requests
                response = service_requests_table.scan(Limit=limit)
                items = response.get('Items', [])
            
            return create_response(200, {
                'serviceRequests': items,
                'count': len(items)
            })
        
        # For consumers, show only their requests
        elif user_info['role'] == 'consumer':
            result = service_request_manager.get_service_request_history(
                user_info['userId'], 
                'consumer',
                limit,
                status_filter
            )
            
            if not result['success']:
                return create_response(400, {'error': result['error']})
            
            return create_response(200, {
                'serviceRequests': result['service_requests'],
                'count': len(result['service_requests'])
            })
        
        else:
            return create_response(403, {'error': 'Access denied'})
        
    except Exception as e:
        logger.error(f"Error listing service requests: {str(e)}")
        return create_response(500, {'error': 'Failed to list service requests'})





def get_service_request(request_id: str, user_info: dict):
    """Get service request details"""
    try:
        response = service_requests_table.get_item(Key={'requestId': request_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Service request not found'})
        
        service_request = response['Item']
        
        # Check authorization
        if (user_info['role'] == 'consumer' and service_request['consumerId'] != user_info['userId']) or \
           (user_info['role'] == 'technician' and service_request.get('technicianId') != user_info['userId']):
            if user_info['role'] != 'administrator':
                return create_response(403, {'error': 'Access denied'})
        
        return create_response(200, service_request)
        
    except Exception as e:
        logger.error(f"Error getting service request: {str(e)}")
        return create_response(500, {'error': 'Failed to get service request'})


def update_service_request_status(request_id: str, update_data: dict, user_info: dict):
    """Update service request status"""
    try:
        # Check authorization first
        response = service_requests_table.get_item(Key={'requestId': request_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Service request not found'})
        
        service_request = response['Item']
        
        if user_info['role'] == 'technician' and service_request.get('technicianId') != user_info['userId']:
            return create_response(403, {'error': 'Access denied'})
        
        # Use service request manager to update status
        new_status = update_data.get('status')
        note = update_data.get('note', '')
        
        if not new_status:
            return create_response(400, {'error': 'Status is required'})
        
        result = service_request_manager.update_service_request_status(
            request_id, new_status, user_info['userId'], note, update_data
        )
        
        if result['success']:
            return create_response(200, result['service_request'])
        else:
            return create_response(400, {'error': result['error']})
        
    except Exception as e:
        logger.error(f"Error updating service request status: {str(e)}")
        return create_response(500, {'error': 'Failed to update service request'})


def get_available_technicians(query_params: dict, user_info: dict):
    """Get list of available technicians (admin only)"""
    try:
        if user_info['role'] != 'administrator':
            return create_response(403, {'error': 'Access denied'})
        
        available_technicians = availability_manager.find_all_available_technicians()
        
        return create_response(200, {'technicians': available_technicians})
        
    except Exception as e:
        logger.error(f"Error getting available technicians: {str(e)}")
        return create_response(500, {'error': 'Failed to get available technicians'})


def update_technician_availability(technician_id: str, update_data: dict, user_info: dict):
    """Update technician availability status"""
    try:
        # Check authorization
        if user_info['role'] != 'technician' or user_info['userId'] != technician_id:
            if user_info['role'] != 'administrator':
                return create_response(403, {'error': 'Access denied'})
        
        override_status = update_data.get('overrideStatus')
        if not override_status:
            return create_response(400, {'error': 'overrideStatus is required'})
        
        result = availability_manager.update_availability_status(
            technician_id, override_status, user_info['userId']
        )
        
        if result['success']:
            return create_response(200, {'message': result['message']})
        else:
            return create_response(400, {'error': result['error']})
        
    except Exception as e:
        logger.error(f"Error updating technician availability: {str(e)}")
        return create_response(500, {'error': 'Failed to update availability'})


def update_technician_schedule(technician_id: str, schedule_data: dict, user_info: dict):
    """Update technician work schedule"""
    try:
        # Check authorization
        if user_info['role'] != 'technician' or user_info['userId'] != technician_id:
            if user_info['role'] != 'administrator':
                return create_response(403, {'error': 'Access denied'})
        
        result = availability_manager.update_work_schedule(
            technician_id, schedule_data, user_info['userId']
        )
        
        if result['success']:
            return create_response(200, {'message': result['message']})
        else:
            return create_response(400, {'error': result['error']})
        
    except Exception as e:
        logger.error(f"Error updating technician schedule: {str(e)}")
        return create_response(500, {'error': 'Failed to update schedule'})


def get_technician_tasks(query_params: dict, user_info: dict):
    """Get assigned tasks for the current technician"""
    try:
        # Only technicians can access their own tasks
        if user_info['role'] != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        # Get status filter if provided
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', 50))
        
        # Get service requests assigned to this technician
        result = service_request_manager.get_service_request_history(
            user_info['userId'], 
            'technician',
            limit,
            status_filter
        )
        
        if not result['success']:
            return create_response(400, {'error': result['error']})
        
        # Transform service requests to task format
        tasks = []
        for sr in result['service_requests']:
            # Normalize location: handle both flat {latitude, longitude} and
            # nested {coordinates: {latitude, longitude}} structures
            raw_location = sr.get('location', {})
            coords = raw_location.get('coordinates', {})
            normalized_location = {
                'address': raw_location.get('address', ''),
                'latitude': float(raw_location.get('latitude') or coords.get('latitude') or 0),
                'longitude': float(raw_location.get('longitude') or coords.get('longitude') or 0),
            }

            task = {
                'taskId': sr['requestId'],
                'serviceRequestId': sr['requestId'],
                'deviceId': sr.get('deviceId'),
                'consumerId': sr.get('consumerId'),
                'priority': sr.get('priority', 'normal'),
                'status': sr.get('status'),
                'location': normalized_location,
                'estimatedArrival': sr.get('estimatedArrival'),
                'description': sr.get('description'),
                'assignedAt': sr.get('createdAt'),
                'dueDate': sr.get('dueDate'),
                'notes': sr.get('notes', [])
            }
            
            # Add optional fields if present
            if 'deviceInfo' in sr:
                task['deviceInfo'] = sr['deviceInfo']
            if 'customerInfo' in sr:
                task['customerInfo'] = sr['customerInfo']
            if 'acceptedAt' in sr:
                task['acceptedAt'] = sr['acceptedAt']
            if 'completedAt' in sr:
                task['completedAt'] = sr['completedAt']
                
            tasks.append(task)
        
        # Also get recent activity for the dashboard
        recent_activities = []
        for task in tasks[:5]:  # Last 5 tasks
            if task.get('completedAt'):
                recent_activities.append({
                    'id': f"activity-{task['taskId']}",
                    'action': 'Completed task',
                    'task': task.get('description', 'Service task'),
                    'time': _format_relative_time(task['completedAt'])
                })
        
        return create_response(200, {
            'tasks': tasks,
            'recentActivities': recent_activities,
            'count': len(tasks)
        })
        
    except Exception as e:
        logger.error(f"Error getting technician tasks: {str(e)}")
        return create_response(500, {'error': 'Failed to get tasks'})


def get_technician_orders(query_params: dict, user_info: dict):
    """Get orders assigned to the current technician from the orders table.

    Orders may store the technician reference in several ways:
      - assignedTechnicianId: full Cognito sub (ideal, but often missing)
      - assignedTechnician: short ID like 'tech_XXXXXXXX' where XXXXXXXX is
        the first 8 hex chars of the Cognito sub
      - technicianAssignment.technicianId: same short ID format

    We match on all three to be resilient to whichever format was written.
    """
    try:
        if user_info['role'] != 'technician':
            return create_response(403, {'error': 'Access denied'})

        technician_id = user_info['userId']  # Full Cognito sub, e.g. '31333d7a-7031-...'
        orders_table = dynamodb.Table(ORDERS_TABLE)

        # Derive the short tech ID used by the assignment algorithm
        # Format: 'tech_' + first 8 chars of UUID (strip hyphens first)
        short_id = 'tech_' + technician_id.replace('-', '')[:8]

        logger.info(f"Searching orders for technician_id={technician_id}, short_id={short_id}")

        # Scan with OR filter across all three possible fields
        from boto3.dynamodb.conditions import Attr
        filter_expr = (
            Attr('assignedTechnicianId').eq(technician_id) |
            Attr('assignedTechnician').eq(short_id) |
            Attr('assignedTechnician').eq(technician_id) |
            Attr('technicianAssignment.technicianId').eq(short_id) |
            Attr('technicianAssignment.technicianId').eq(technician_id)
        )

        response = orders_table.scan(FilterExpression=filter_expr)
        orders = response.get('Items', [])

        # Handle DynamoDB pagination
        while 'LastEvaluatedKey' in response:
            response = orders_table.scan(
                FilterExpression=filter_expr,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            orders.extend(response.get('Items', []))

        logger.info(f"Found {len(orders)} orders for technician {technician_id}")

        # Enrich orders with consumer phone from users table
        consumer_ids = list({o.get('userId') for o in orders if o.get('userId')})
        consumer_profiles: dict = {}
        if consumer_ids:
            try:
                keys = [{'userId': cid} for cid in consumer_ids]
                batch_resp = dynamodb.batch_get_item(
                    RequestItems={USERS_TABLE: {'Keys': keys}}
                )
                for user in batch_resp.get('Responses', {}).get(USERS_TABLE, []):
                    uid = user.get('userId')
                    if uid:
                        consumer_profiles[uid] = user
            except Exception as enrich_err:
                logger.warning(f"Could not enrich consumer profiles: {enrich_err}")

        for order in orders:
            uid = order.get('userId')
            if uid and uid in consumer_profiles:
                profile = consumer_profiles[uid].get('profile', {})
                # Phone
                if not order.get('consumerPhone') and not order.get('phone'):
                    order['consumerPhone'] = profile.get('phone', '')
                # Name
                if not order.get('consumerName') or order.get('consumerName') == order.get('consumerEmail'):
                    first = profile.get('firstName', '')
                    last = profile.get('lastName', '')
                    full_name = f"{first} {last}".strip()
                    if full_name:
                        order['consumerName'] = full_name
                # Always use the latest address from the consumer profile
                # so technicians see the current address, not the stale order-time snapshot
                profile_address = profile.get('address')
                if profile_address:
                    order['deliveryAddress'] = profile_address

        # Sort by createdAt descending
        orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        return create_response(200, {
            'orders': orders,
            'tasks': orders,
            'count': len(orders)
        })

    except Exception as e:
        logger.error(f"Error getting technician orders: {str(e)}")
        return create_response(500, {'error': 'Failed to get orders'})


def _format_relative_time(iso_timestamp: str) -> str:
    """Format ISO timestamp as relative time (e.g., '2 hours ago')"""
    try:
        timestamp = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return iso_timestamp



def get_technician_inventory(query_params: dict, user_info: dict):
    """Get inventory items available to technician"""
    try:
        # Log user info for debugging
        logger.info(f"User info: {json.dumps(user_info)}")
        
        # Only technicians can access inventory
        if user_info.get('role') != 'technician':
            logger.warning(f"Access denied for user {user_info.get('userId')} with role {user_info.get('role')}")
            return create_response(403, {'error': 'Access denied', 'userRole': user_info.get('role')})
        
        # Mock inventory data - in production, this would query DynamoDB inventory table
        inventory_items = [
            {
                'partId': 'item-001',
                'name': 'pH Sensor',
                'category': 'Sensors',
                'quantity': 15,
                'checkedOut': 3,
                'available': 12,
                'location': 'Warehouse A',
                'lastRestocked': '2024-02-15T10:30:00Z'
            },
            {
                'partId': 'item-002',
                'name': 'TDS Sensor',
                'category': 'Sensors',
                'quantity': 20,
                'checkedOut': 5,
                'available': 15,
                'location': 'Warehouse A',
                'lastRestocked': '2024-02-14T14:20:00Z'
            },
            {
                'partId': 'item-003',
                'name': 'Turbidity Sensor',
                'category': 'Sensors',
                'quantity': 12,
                'checkedOut': 2,
                'available': 10,
                'location': 'Warehouse B',
                'lastRestocked': '2024-02-16T09:15:00Z'
            },
            {
                'partId': 'item-004',
                'name': 'Temperature Sensor',
                'category': 'Sensors',
                'quantity': 25,
                'checkedOut': 4,
                'available': 21,
                'location': 'Warehouse A',
                'lastRestocked': '2024-02-13T11:45:00Z'
            },
            {
                'partId': 'item-005',
                'name': 'Calibration Solution',
                'category': 'Supplies',
                'quantity': 30,
                'checkedOut': 8,
                'available': 22,
                'location': 'Warehouse C',
                'lastRestocked': '2024-02-17T08:00:00Z'
            }
        ]
        
        return create_response(200, {
            'inventory': inventory_items,
            'count': len(inventory_items)
        })
        
    except Exception as e:
        logger.error(f"Error getting technician inventory: {str(e)}")
        return create_response(500, {'error': 'Failed to get inventory'})


def checkout_inventory_item(checkout_data: dict, user_info: dict):
    """Checkout an inventory item"""
    try:
        # Only technicians can checkout inventory
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        # Accept both partId and itemId for backward compatibility
        part_id = checkout_data.get('partId') or checkout_data.get('itemId')
        quantity = checkout_data.get('quantity', 1)
        task_id = checkout_data.get('taskId')
        
        if not part_id:
            return create_response(400, {'error': 'Part ID is required'})
        
        if quantity <= 0:
            return create_response(400, {'error': 'Quantity must be greater than 0'})
        
        # In production, this would update DynamoDB inventory table
        logger.info(f"Technician {user_info['userId']} checked out {quantity} of part {part_id}" + 
                   (f" for task {task_id}" if task_id else ""))
        
        return create_response(200, {
            'success': True,
            'message': f'Successfully checked out {quantity} item(s)',
            'partId': part_id,
            'quantity': quantity,
            'taskId': task_id,
            'technicianId': user_info['userId'],
            'checkedOutAt': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error checking out inventory item: {str(e)}")
        return create_response(500, {'error': 'Failed to checkout item'})


def return_inventory_item(return_data: dict, user_info: dict):
    """Return an inventory item"""
    try:
        # Only technicians can return inventory
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        # Accept both partId and itemId for backward compatibility
        part_id = return_data.get('partId') or return_data.get('itemId')
        quantity = return_data.get('quantity', 1)
        condition = return_data.get('condition', 'good')
        
        if not part_id:
            return create_response(400, {'error': 'Part ID is required'})
        
        if quantity <= 0:
            return create_response(400, {'error': 'Quantity must be greater than 0'})
        
        # In production, this would update DynamoDB inventory table
        logger.info(f"Technician {user_info['userId']} returned {quantity} of part {part_id} in {condition} condition")
        
        return create_response(200, {
            'success': True,
            'message': f'Successfully returned {quantity} item(s)',
            'partId': part_id,
            'quantity': quantity,
            'condition': condition,
            'technicianId': user_info['userId'],
            'returnedAt': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error returning inventory item: {str(e)}")
        return create_response(500, {'error': 'Failed to return item'})


def request_inventory_restock(restock_data: dict, user_info: dict):
    """Request restock of an inventory item"""
    try:
        # Only technicians can request restocks
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        # Accept both partId and itemId for backward compatibility
        part_id = restock_data.get('partId') or restock_data.get('itemId')
        part_name = restock_data.get('partName', 'Unknown Part')
        quantity = restock_data.get('quantity', 1)
        urgency = restock_data.get('urgency', 'normal')
        reason = restock_data.get('reason', '')
        current_stock = restock_data.get('currentStock', 0)
        
        if not part_id:
            return create_response(400, {'error': 'Part ID is required'})
        
        if quantity <= 0:
            return create_response(400, {'error': 'Quantity must be greater than 0'})
        
        # In production, this would create a restock request in DynamoDB
        logger.info(f"Technician {user_info['userId']} requested restock of {quantity} of part {part_id} ({part_name}) with {urgency} urgency")
        
        # Optionally notify admin via SNS
        if ADMIN_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=ADMIN_TOPIC_ARN,
                    Subject=f"Inventory Restock Request - {urgency.upper()}",
                    Message=json.dumps({
                        'type': 'restock_request',
                        'partId': part_id,
                        'partName': part_name,
                        'quantity': quantity,
                        'currentStock': current_stock,
                        'urgency': urgency,
                        'reason': reason,
                        'requestedBy': user_info['userId'],
                        'requestedAt': datetime.utcnow().isoformat() + 'Z'
                    })
                )
            except Exception as sns_error:
                logger.warning(f"Failed to send SNS notification: {str(sns_error)}")
        
        return create_response(200, {
            'success': True,
            'message': 'Restock request submitted successfully',
            'requestId': f"restock-{int(datetime.utcnow().timestamp())}",
            'partId': part_id,
            'partName': part_name,
            'quantity': quantity,
            'urgency': urgency,
            'requestedBy': user_info['userId'],
            'requestedAt': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Error requesting inventory restock: {str(e)}")
        return create_response(500, {'error': 'Failed to submit restock request'})



def _send_technician_accepted_email(
    consumer_email: str,
    consumer_name: str,
    technician_name: str,
    order_id: str,
    technician_phone: str
) -> None:
    """Send SES email to consumer when a technician accepts their order."""
    try:
        if not consumer_email or not SES_FROM_EMAIL:
            logger.warning("Skipping acceptance email: missing consumer_email or SES_FROM_EMAIL")
            return

        subject = 'A Technician Has Accepted Your Installation Request'
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0066cc;">Technician Assigned ✅</h2>
                <p>Hi {consumer_name},</p>
                <p>Great news! A technician has accepted your installation request and will be in touch with you shortly.</p>

                <div style="background-color: #f0f9ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0066cc;">
                    <p style="margin: 5px 0;"><strong>Order ID:</strong> {order_id}</p>
                    <p style="margin: 5px 0;"><strong>Technician:</strong> {technician_name}</p>
                    <p style="margin: 5px 0;"><strong>Contact:</strong> {technician_phone or 'Will be provided soon'}</p>
                </div>

                <h3 style="color: #0066cc;">What Happens Next?</h3>
                <ul>
                    <li>Your technician will contact you to confirm the installation time</li>
                    <li>The installation typically takes 30–45 minutes</li>
                    <li>Please ensure someone is available at the delivery address</li>
                </ul>

                <p>You can track the status of your order in the AquaChain dashboard at any time.</p>
                <p style="margin-top: 30px;">Best regards,<br>The AquaChain Team</p>
            </div>
        </body>
        </html>
        """
        body_text = (
            f"Hi {consumer_name}, a technician ({technician_name}) has accepted your "
            f"installation request for order {order_id}. "
            f"They will contact you shortly. Phone: {technician_phone or 'TBD'}."
        )

        ses.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [consumer_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': body_html},
                    'Text': {'Data': body_text}
                }
            }
        )
        logger.info(f"Technician-accepted email sent to {consumer_email} for order {order_id}")

    except Exception as e:
        # Non-fatal — log and continue; don't fail the accept flow
        logger.error(f"Failed to send technician-accepted email to {consumer_email}: {str(e)}")


def accept_technician_task(task_id: str, user_info: dict):
    """Accept a task assignment.

    Supports both service-request IDs (SR-...) and order IDs (ord_...).
    Orders assigned to technicians are stored in the orders table; accepting
    them sets the order status to 'accepted'.
    """
    try:
        # Only technicians can accept tasks
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})

        # Order-based tasks — any ID that is NOT an SR- service request
        # Order IDs are plain UUIDs (e.g. 550e8400-e29b-41d4-a716-446655440000)
        # or may carry an ord_/ord- prefix. SR IDs always start with 'SR-'.
        is_service_request = task_id.upper().startswith('SR-')
        if not is_service_request:
            orders_table = dynamodb.Table(ORDERS_TABLE)
            response = orders_table.get_item(Key={'orderId': task_id})
            if 'Item' not in response:
                return create_response(404, {'error': 'Order not found'})

            order = response['Item']

            # Verify this order is assigned to the requesting technician.
            # The assignedTechnician field may hold a full Cognito UUID, a short
            # 'tech_XXXXXXXX' ID, or may be absent (admin-created orders).
            # We match against all known formats; if none match we still allow
            # the accept when the order appears in the technician's own task list
            # (i.e. get_technician_orders already filtered it for them).
            technician_id = user_info.get('userId') or ''
            short_id = ('tech_' + technician_id.replace('-', '')[:8]) if technician_id else ''
            assigned_to = (
                order.get('assignedTechnicianId') or
                order.get('assignedTechnician') or
                (order.get('technicianAssignment') or {}).get('technicianId', '')
            )
            # Only block if there IS an explicit assignment to a different technician
            if assigned_to and assigned_to not in (technician_id, short_id):
                return create_response(403, {'error': 'This order is not assigned to you'})

            now = datetime.utcnow().isoformat()
            audit_entry = {
                'action': 'ORDER_ACCEPTED',
                'by': technician_id,
                'at': now
            }

            orders_table.update_item(
                Key={'orderId': task_id},
                UpdateExpression='SET #s = :s, acceptedAt = :at, updatedAt = :at, auditTrail = list_append(if_not_exists(auditTrail, :empty), :entry)',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':s': 'accepted',
                    ':at': now,
                    ':entry': [audit_entry],
                    ':empty': []
                }
            )

            # Notify consumer that technician accepted the order
            consumer_id = order.get('userId') or order.get('consumerId')
            if NOTIFICATION_TOPIC_ARN and consumer_id:
                try:
                    sns.publish(
                        TopicArn=NOTIFICATION_TOPIC_ARN,
                        Subject=f'Order Accepted: {task_id}',
                        Message=json.dumps({
                            'type': 'service_request_status_updated',
                            'orderId': task_id,
                            'consumerId': consumer_id,
                            'technicianId': technician_id,
                            'status': 'accepted',
                            'previous_status': order.get('status'),
                            'timestamp': now
                        })
                    )
                except Exception as notify_err:
                    logger.error(f"Failed to send acceptance notification for order {task_id}: {str(notify_err)}")

            # Send SES email directly to the consumer
            try:
                # Fetch consumer profile
                consumer_resp = users_table.get_item(Key={'userId': consumer_id}) if consumer_id else {}
                consumer_record = consumer_resp.get('Item', {})
                consumer_email = consumer_record.get('email', order.get('consumerEmail', ''))
                consumer_profile = consumer_record.get('profile', {})
                consumer_name = (
                    f"{consumer_profile.get('firstName', '')} {consumer_profile.get('lastName', '')}".strip()
                    or order.get('consumerName', 'Customer')
                )

                # Fetch technician profile
                tech_resp = users_table.get_item(Key={'userId': technician_id}) if technician_id else {}
                tech_record = tech_resp.get('Item', {})
                tech_profile = tech_record.get('profile', {})
                technician_name = (
                    f"{tech_profile.get('firstName', '')} {tech_profile.get('lastName', '')}".strip()
                    or 'Your Technician'
                )
                technician_phone = tech_profile.get('phone', '')

                _send_technician_accepted_email(
                    consumer_email=consumer_email,
                    consumer_name=consumer_name,
                    technician_name=technician_name,
                    order_id=task_id,
                    technician_phone=technician_phone
                )
            except Exception as email_err:
                logger.error(f"Error preparing acceptance email for order {task_id}: {str(email_err)}")

            return create_response(200, {
                'success': True,
                'message': 'Task accepted successfully',
                'orderId': task_id
            })

        # Legacy service-request IDs (SR-...) — use the service request manager
        result = service_request_manager.update_service_request_status(
            task_id,
            'accepted',
            user_info['userId'],
            'Task accepted by technician'
        )

        if result['success']:
            return create_response(200, {
                'success': True,
                'message': 'Task accepted successfully',
                'task': result['service_request']
            })
        else:
            return create_response(400, {'error': result['error']})

    except Exception as e:
        logger.error(f"Error accepting task: {str(e)}")
        return create_response(500, {'error': 'Failed to accept task'})


def update_technician_task_status(task_id: str, update_data: dict, user_info: dict):
    """Update task status"""
    try:
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})

        status = update_data.get('status')
        note = update_data.get('note', '')

        if not status:
            return create_response(400, {'error': 'Status is required'})

        # Order-based tasks — update orders table directly
        if task_id.startswith('ord_') or task_id.startswith('ord-'):
            orders_table = dynamodb.Table(ORDERS_TABLE)

            # Guard: prevent starting work before device is shipped/out for delivery
            if status == 'in_progress':
                order_resp = orders_table.get_item(Key={'orderId': task_id})
                if 'Item' in order_resp:
                    current_status = order_resp['Item'].get('status', '')
                    allowed_to_start = current_status in (
                        'SHIPPED', 'shipped', 'OUT_FOR_DELIVERY', 'out_for_delivery',
                        'accepted', 'TECHNICIAN_ASSIGNED', 'assigned'
                    )
                    if not allowed_to_start:
                        return create_response(400, {
                            'error': 'Cannot start work before the device has been shipped',
                            'currentStatus': current_status
                        })

            now = datetime.utcnow().isoformat()
            audit_entry = {'action': f'STATUS_UPDATED_{status.upper()}', 'by': user_info['userId'], 'at': now}
            orders_table.update_item(
                Key={'orderId': task_id},
                UpdateExpression='SET #s = :s, updatedAt = :at, auditTrail = list_append(if_not_exists(auditTrail, :empty), :entry)',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': status, ':at': now, ':entry': [audit_entry], ':empty': []}
            )
            return create_response(200, {'success': True, 'message': 'Task status updated successfully', 'orderId': task_id, 'status': status})

        # Legacy service-request IDs
        result = service_request_manager.update_service_request_status(
            task_id, status, user_info['userId'], note, update_data
        )

        if result['success']:
            return create_response(200, {'success': True, 'message': 'Task status updated successfully', 'task': result['service_request']})
        else:
            return create_response(400, {'error': result['error']})

    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        return create_response(500, {'error': 'Failed to update task status'})


def add_technician_task_note(task_id: str, note_data: dict, user_info: dict):
    """Add a note to a task"""
    try:
        # Only technicians can add notes
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        content = note_data.get('content')
        if not content:
            return create_response(400, {'error': 'Note content is required'})
        
        # Add note to service request
        result = service_request_manager.add_service_note(
            task_id,
            user_info['userId'],
            'technician_note',
            content,
            note_data.get('attachments')
        )
        
        if result['success']:
            return create_response(200, {
                'success': True,
                'message': 'Note added successfully',
                'note': result['note']
            })
        else:
            return create_response(400, {'error': result['error']})
        
    except Exception as e:
        logger.error(f"Error adding task note: {str(e)}")
        return create_response(500, {'error': 'Failed to add note'})


def complete_technician_task(task_id: str, completion_data: dict, user_info: dict):
    """Complete a task"""
    try:
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})

        # Order-based tasks — mark order as completed/installed in orders table
        if task_id.startswith('ord_') or task_id.startswith('ord-'):
            orders_table = dynamodb.Table(ORDERS_TABLE)
            now = datetime.utcnow().isoformat()
            audit_entry = {'action': 'INSTALLATION_COMPLETED', 'by': user_info['userId'], 'at': now}
            update_expr = 'SET #s = :s, completedAt = :at, updatedAt = :at, auditTrail = list_append(if_not_exists(auditTrail, :empty), :entry)'
            expr_values = {':s': 'completed', ':at': now, ':entry': [audit_entry], ':empty': []}
            if completion_data.get('deviceId'):
                update_expr += ', installedDeviceId = :did'
                expr_values[':did'] = completion_data['deviceId']
            if completion_data.get('location'):
                update_expr += ', installationLocation = :loc'
                expr_values[':loc'] = completion_data['location']
            orders_table.update_item(
                Key={'orderId': task_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues=expr_values
            )
            return create_response(200, {'success': True, 'message': 'Task completed successfully', 'orderId': task_id})

        # Legacy service-request IDs
        result = service_request_manager.complete_service_request(
            task_id, user_info['userId'], completion_data
        )

        if result['success']:
            return create_response(200, {'success': True, 'message': 'Task completed successfully', 'task': result['service_request']})
        else:
            return create_response(400, {'error': result['error']})

    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        return create_response(500, {'error': 'Failed to complete task'})


def get_technician_task_history(query_params: dict, user_info: dict):
    """Get task history for technician"""
    try:
        # Only technicians can access their history
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        limit = int(query_params.get('limit', 50))
        
        # Get service request history
        result = service_request_manager.get_service_request_history(
            user_info['userId'],
            'technician',
            limit,
            'completed'  # Only show completed tasks in history
        )
        
        if result['success']:
            return create_response(200, {
                'tasks': result['service_requests'],
                'count': result['count']
            })
        else:
            return create_response(400, {'error': result['error']})
        
    except Exception as e:
        logger.error(f"Error getting task history: {str(e)}")
        return create_response(500, {'error': 'Failed to get task history'})


def get_task_route(task_id: str, user_info: dict):
    """Get route to task location"""
    try:
        # Only technicians can get routes
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        # Get service request
        response = service_requests_table.get_item(Key={'requestId': task_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Task not found'})
        
        service_request = response['Item']
        
        # Verify technician is assigned to this task
        if service_request.get('technicianId') != user_info['userId']:
            return create_response(403, {'error': 'Access denied'})
        
        # Get task location and normalize coordinates structure
        raw_location = service_request.get('location')
        if not raw_location:
            return create_response(400, {'error': 'Task location not available'})

        coords = raw_location.get('coordinates', {})
        lat = float(raw_location.get('latitude') or coords.get('latitude') or 0)
        lng = float(raw_location.get('longitude') or coords.get('longitude') or 0)
        task_location = {
            'address': raw_location.get('address', ''),
            'latitude': lat,
            'longitude': lng,
        }

        # In production, this would use AWS Location Service to calculate route
        # For now, return mock route data
        route_data = {
            'taskId': task_id,
            'destination': task_location,
            'estimatedDuration': 1800,  # 30 minutes in seconds
            'estimatedDistance': 15000,  # 15 km in meters
            'routeUrl': f"https://maps.google.com/?q={lat},{lng}"
        }
        
        return create_response(200, route_data)
        
    except Exception as e:
        logger.error(f"Error getting task route: {str(e)}")
        return create_response(500, {'error': 'Failed to get route'})


def update_technician_location(location_data: dict, user_info: dict):
    """Update technician's current location"""
    try:
        # Only technicians can update their location
        if user_info.get('role') != 'technician':
            return create_response(403, {'error': 'Access denied'})
        
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        
        if latitude is None or longitude is None:
            return create_response(400, {'error': 'Latitude and longitude are required'})
        
        # Update technician location in users table
        try:
            users_table.update_item(
                Key={'userId': user_info['userId']},
                UpdateExpression='SET currentLocation = :location, locationUpdatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':location': {
                        'latitude': Decimal(str(latitude)),
                        'longitude': Decimal(str(longitude))
                    },
                    ':timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            logger.info(f"Updated location for technician {user_info['userId']}")
            
            return create_response(200, {
                'success': True,
                'message': 'Location updated successfully',
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            })
            
        except Exception as db_error:
            logger.error(f"Error updating location in database: {str(db_error)}")
            return create_response(500, {'error': 'Failed to update location'})
        
    except Exception as e:
        logger.error(f"Error updating technician location: {str(e)}")
        return create_response(500, {'error': 'Failed to update location'})
