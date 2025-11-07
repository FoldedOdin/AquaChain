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

from .location_service import LocationService
from .availability_manager import TechnicianAvailabilityManager
from .assignment_algorithm import TechnicianAssignmentAlgorithm
from .service_request_manager import ServiceRequestManager

# Add shared utilities to path
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='technician-service')

# AWS clients
dynamodb = boto3.resource('dynamodb')
location_client = boto3.client('location')
sns = boto3.client('sns')

# Environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'aquachain-users')
SERVICE_REQUESTS_TABLE = os.environ.get('SERVICE_REQUESTS_TABLE', 'aquachain-service-requests')
LOCATION_MAP_NAME = os.environ.get('LOCATION_MAP_NAME', 'aquachain-map')
LOCATION_ROUTE_CALCULATOR = os.environ.get('LOCATION_ROUTE_CALCULATOR', 'aquachain-routes')
LOCATION_PLACE_INDEX = os.environ.get('LOCATION_PLACE_INDEX', 'aquachain-places')
ADMIN_TOPIC_ARN = os.environ.get('ADMIN_TOPIC_ARN')
NOTIFICATION_TOPIC_ARN = os.environ.get('NOTIFICATION_TOPIC_ARN')
WEBSOCKET_API_ENDPOINT = os.environ.get('WEBSOCKET_API_ENDPOINT')

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
        if resource == '/api/v1/service-requests' and http_method == 'POST':
            return create_service_request(body, user_info)
        elif resource == '/api/v1/service-requests/{requestId}' and http_method == 'GET':
            return get_service_request(path_parameters['requestId'], user_info)
        elif resource == '/api/v1/service-requests/{requestId}/status' and http_method == 'PUT':
            return update_service_request_status(path_parameters['requestId'], body, user_info)
        elif resource == '/api/v1/technician/tasks' and http_method == 'GET':
            return get_technician_tasks(query_parameters, user_info)
        elif resource == '/api/v1/technicians/available' and http_method == 'GET':
            return get_available_technicians(query_parameters, user_info)
        elif resource == '/api/v1/technicians/{technicianId}/availability' and http_method == 'PUT':
            return update_technician_availability(path_parameters['technicianId'], body, user_info)
        elif resource == '/api/v1/technicians/{technicianId}/schedule' and http_method == 'PUT':
            return update_technician_schedule(path_parameters['technicianId'], body, user_info)
        else:
            return create_response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def extract_user_from_token(event):
    """Extract user information from JWT token in request context"""
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    
    return {
        'userId': authorizer.get('sub'),
        'email': authorizer.get('email'),
        'role': authorizer.get('custom:role', 'consumer'),
        'groups': authorizer.get('cognito:groups', [])
    }


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
            task = {
                'taskId': sr['requestId'],
                'serviceRequestId': sr['requestId'],
                'deviceId': sr.get('deviceId'),
                'consumerId': sr.get('consumerId'),
                'priority': sr.get('priority', 'normal'),
                'status': sr.get('status'),
                'location': sr.get('location'),
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