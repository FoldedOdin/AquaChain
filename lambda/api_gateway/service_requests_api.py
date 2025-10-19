"""
Service Requests API Lambda function
Handles service request creation, management, and status updates
"""
import json
import boto3
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
location_client = boto3.client('location')

# Table references
service_requests_table = dynamodb.Table('aquachain-service-requests')
users_table = dynamodb.Table('aquachain-users')
technicians_table = dynamodb.Table('aquachain-technicians')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """Main Lambda handler for service requests API"""
    try:
        # Parse request
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {}) or {}
        query_parameters = event.get('queryStringParameters', {}) or {}
        body = event.get('body')
        
        # Get user context from authorizer
        user_context = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = user_context.get('sub')
        user_groups = user_context.get('cognito:groups', '').split(',')
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized', 'message': 'User not authenticated'})
        
        # Route request based on HTTP method and path
        if http_method == 'GET':
            if 'requestId' in path_parameters:
                return get_service_request(path_parameters['requestId'], user_id, user_groups)
            else:
                return get_user_service_requests(user_id, query_parameters, user_groups)
        
        elif http_method == 'POST':
            if 'consumers' not in user_groups and 'administrators' not in user_groups:
                return create_response(403, {'error': 'Forbidden', 'message': 'Only consumers can create service requests'})
            return create_service_request(json.loads(body), user_id)
        
        elif http_method == 'PUT':
            if 'requestId' in path_parameters:
                return update_service_request(path_parameters['requestId'], json.loads(body), user_id, user_groups)
            else:
                return create_response(400, {'error': 'Bad Request', 'message': 'Request ID required for updates'})
        
        else:
            return create_response(405, {'error': 'Method Not Allowed'})
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def create_service_request(request_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Create a new service request"""
    try:
        # Validate required fields
        required_fields = ['deviceId', 'location', 'issueDescription']
        for field in required_fields:
            if field not in request_data:
                return create_response(400, {'error': 'Bad Request', 'message': f'Missing required field: {field}'})
        
        # Generate request ID and timestamp
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Find available technician
        assigned_technician = find_available_technician(request_data['location'])
        
        # Create service request item
        service_request = {
            'requestId': request_id,
            'timestamp': timestamp,
            'consumerId': user_id,
            'deviceId': request_data['deviceId'],
            'status': 'assigned' if assigned_technician else 'pending',
            'location': request_data['location'],
            'issueDescription': request_data['issueDescription'],
            'priority': request_data.get('priority', 'normal'),
            'notes': [],
            'createdAt': timestamp
        }
        
        if assigned_technician:
            service_request['technicianId'] = assigned_technician['technicianId']
            service_request['estimatedArrival'] = assigned_technician['estimatedArrival']
            
            # Add assignment note
            service_request['notes'].append({
                'timestamp': timestamp,
                'author': 'system',
                'type': 'status_update',
                'content': f"Assigned to technician {assigned_technician['technicianName']}"
            })
        else:
            # Create P1 admin ticket for no available technicians
            create_p1_admin_ticket(service_request)
            
            service_request['notes'].append({
                'timestamp': timestamp,
                'author': 'system',
                'type': 'status_update',
                'content': 'No technicians available. Admin ticket created.'
            })
        
        # Store in DynamoDB
        service_requests_table.put_item(Item=service_request)
        
        # Send notifications
        send_service_request_notifications(service_request)
        
        logger.info(f"Service request created: {request_id}")
        
        return create_response(201, {
            'message': 'Service request created successfully',
            'serviceRequest': service_request
        })
    
    except Exception as e:
        logger.error(f"Error creating service request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_service_request(request_id: str, user_id: str, user_groups: List[str]) -> Dict[str, Any]:
    """Get a specific service request"""
    try:
        # Get service request
        response = service_requests_table.get_item(Key={'requestId': request_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Not Found', 'message': 'Service request not found'})
        
        service_request = response['Item']
        
        # Check access permissions
        if not has_service_request_access(service_request, user_id, user_groups):
            return create_response(403, {'error': 'Forbidden', 'message': 'Access denied to this service request'})
        
        return create_response(200, {
            'serviceRequest': service_request
        })
    
    except Exception as e:
        logger.error(f"Error getting service request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_user_service_requests(user_id: str, query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get service requests for user"""
    try:
        # Parse query parameters
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', 50))
        days = int(query_params.get('days', 30))
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query based on user role
        if 'administrators' in user_groups:
            # Administrators can see all requests
            service_requests = get_all_service_requests(status_filter, limit, start_date, end_date)
        elif 'technicians' in user_groups:
            # Technicians see assigned requests
            service_requests = get_technician_service_requests(user_id, status_filter, limit, start_date, end_date)
        else:
            # Consumers see their own requests
            service_requests = get_consumer_service_requests(user_id, status_filter, limit, start_date, end_date)
        
        return create_response(200, {
            'serviceRequests': service_requests,
            'count': len(service_requests),
            'filters': {
                'status': status_filter,
                'days': days,
                'limit': limit
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting user service requests: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def update_service_request(request_id: str, update_data: Dict[str, Any], user_id: str, user_groups: List[str]) -> Dict[str, Any]:
    """Update service request status or add notes"""
    try:
        # Get existing service request
        response = service_requests_table.get_item(Key={'requestId': request_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Not Found', 'message': 'Service request not found'})
        
        service_request = response['Item']
        
        # Check update permissions
        if not can_update_service_request(service_request, user_id, user_groups, update_data):
            return create_response(403, {'error': 'Forbidden', 'message': 'Cannot update this service request'})
        
        # Prepare update expression
        update_expression = "SET #updatedAt = :updatedAt"
        expression_attribute_names = {'#updatedAt': 'updatedAt'}
        expression_attribute_values = {':updatedAt': datetime.utcnow().isoformat()}
        
        # Handle status updates
        if 'status' in update_data:
            new_status = update_data['status']
            if is_valid_status_transition(service_request.get('status'), new_status):
                update_expression += ", #status = :status"
                expression_attribute_names['#status'] = 'status'
                expression_attribute_values[':status'] = new_status
                
                # Add status update note
                status_note = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'author': user_id,
                    'type': 'status_update',
                    'content': f"Status changed to {new_status}"
                }
                
                # Update notes list
                notes = service_request.get('notes', [])
                notes.append(status_note)
                update_expression += ", notes = :notes"
                expression_attribute_values[':notes'] = notes
            else:
                return create_response(400, {'error': 'Bad Request', 'message': f'Invalid status transition'})
        
        # Handle note additions
        if 'note' in update_data:
            note = {
                'timestamp': datetime.utcnow().isoformat(),
                'author': user_id,
                'type': update_data.get('noteType', 'technician_note'),
                'content': update_data['note']
            }
            
            notes = service_request.get('notes', [])
            notes.append(note)
            update_expression += ", notes = :notes"
            expression_attribute_values[':notes'] = notes
        
        # Handle completion data
        if 'completionData' in update_data and update_data.get('status') == 'completed':
            update_expression += ", completedAt = :completedAt"
            expression_attribute_values[':completedAt'] = datetime.utcnow().isoformat()
            
            if 'customerRating' in update_data['completionData']:
                update_expression += ", customerRating = :rating"
                expression_attribute_values[':rating'] = update_data['completionData']['customerRating']
        
        # Update the item
        service_requests_table.update_item(
            Key={'requestId': request_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        # Send notifications for status changes
        if 'status' in update_data:
            send_status_update_notifications(request_id, update_data['status'], service_request)
        
        logger.info(f"Service request updated: {request_id}")
        
        return create_response(200, {
            'message': 'Service request updated successfully',
            'requestId': request_id
        })
    
    except Exception as e:
        logger.error(f"Error updating service request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def find_available_technician(location: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find available technician with shortest ETA"""
    try:
        # This would integrate with the technician service
        # For now, return a mock response
        return {
            'technicianId': 'tech-001',
            'technicianName': 'John Smith',
            'estimatedArrival': (datetime.utcnow() + timedelta(minutes=45)).isoformat(),
            'eta': 45
        }
    
    except Exception as e:
        logger.error(f"Error finding technician: {str(e)}")
        return None


def create_p1_admin_ticket(service_request: Dict[str, Any]):
    """Create P1 admin ticket for unassigned service requests"""
    try:
        # Send SNS notification to admin group
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:aquachain-admin-alerts',
            Subject='P1: No Technicians Available',
            Message=json.dumps({
                'alertType': 'P1_ADMIN_TICKET',
                'serviceRequestId': service_request['requestId'],
                'location': service_request['location'],
                'deviceId': service_request['deviceId'],
                'timestamp': service_request['timestamp'],
                'message': 'No technicians available in service zone'
            })
        )
        
        logger.info(f"P1 admin ticket created for service request: {service_request['requestId']}")
    
    except Exception as e:
        logger.error(f"Error creating P1 admin ticket: {str(e)}")


def send_service_request_notifications(service_request: Dict[str, Any]):
    """Send notifications for new service request"""
    try:
        # Notify consumer
        consumer_message = {
            'type': 'service_request_created',
            'requestId': service_request['requestId'],
            'status': service_request['status'],
            'estimatedArrival': service_request.get('estimatedArrival'),
            'message': 'Your service request has been created'
        }
        
        # Notify technician if assigned
        if service_request.get('technicianId'):
            technician_message = {
                'type': 'service_request_assigned',
                'requestId': service_request['requestId'],
                'location': service_request['location'],
                'deviceId': service_request['deviceId'],
                'issueDescription': service_request['issueDescription'],
                'message': 'New service request assigned to you'
            }
            
            # Send to technician topic
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:aquachain-technician-notifications',
                Message=json.dumps(technician_message),
                MessageAttributes={
                    'technicianId': {
                        'DataType': 'String',
                        'StringValue': service_request['technicianId']
                    }
                }
            )
        
        logger.info(f"Notifications sent for service request: {service_request['requestId']}")
    
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")


def send_status_update_notifications(request_id: str, new_status: str, service_request: Dict[str, Any]):
    """Send notifications for status updates"""
    try:
        message = {
            'type': 'service_request_status_update',
            'requestId': request_id,
            'status': new_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to consumer
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:aquachain-consumer-notifications',
            Message=json.dumps(message),
            MessageAttributes={
                'consumerId': {
                    'DataType': 'String',
                    'StringValue': service_request['consumerId']
                }
            }
        )
        
        logger.info(f"Status update notification sent for request: {request_id}")
    
    except Exception as e:
        logger.error(f"Error sending status update notification: {str(e)}")


def has_service_request_access(service_request: Dict[str, Any], user_id: str, user_groups: List[str]) -> bool:
    """Check if user has access to service request"""
    # Administrators have access to all requests
    if 'administrators' in user_groups:
        return True
    
    # Consumers can access their own requests
    if service_request.get('consumerId') == user_id:
        return True
    
    # Technicians can access assigned requests
    if 'technicians' in user_groups and service_request.get('technicianId') == user_id:
        return True
    
    return False


def can_update_service_request(service_request: Dict[str, Any], user_id: str, user_groups: List[str], update_data: Dict[str, Any]) -> bool:
    """Check if user can update service request"""
    # Administrators can update any request
    if 'administrators' in user_groups:
        return True
    
    # Technicians can update assigned requests
    if 'technicians' in user_groups and service_request.get('technicianId') == user_id:
        return True
    
    # Consumers can only add notes and rate completed services
    if service_request.get('consumerId') == user_id:
        allowed_updates = {'note', 'noteType', 'customerRating'}
        return all(key in allowed_updates for key in update_data.keys())
    
    return False


def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    """Validate status transition"""
    valid_transitions = {
        'pending': ['assigned', 'cancelled'],
        'assigned': ['accepted', 'cancelled'],
        'accepted': ['en_route', 'cancelled'],
        'en_route': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': []
    }
    
    return new_status in valid_transitions.get(current_status, [])


def get_all_service_requests(status_filter: Optional[str], limit: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get all service requests (admin only)"""
    try:
        # Scan table with filters
        scan_kwargs = {
            'Limit': limit,
            'FilterExpression': 'attribute_exists(requestId)'
        }
        
        if status_filter:
            scan_kwargs['FilterExpression'] += ' AND #status = :status'
            scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            scan_kwargs['ExpressionAttributeValues'] = {':status': status_filter}
        
        response = service_requests_table.scan(**scan_kwargs)
        return response.get('Items', [])
    
    except Exception as e:
        logger.error(f"Error getting all service requests: {str(e)}")
        return []


def get_technician_service_requests(technician_id: str, status_filter: Optional[str], limit: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get service requests for technician"""
    try:
        # Query by technician ID using GSI
        query_kwargs = {
            'IndexName': 'TechnicianIndex',
            'KeyConditionExpression': 'technicianId = :technicianId',
            'ExpressionAttributeValues': {':technicianId': technician_id},
            'Limit': limit,
            'ScanIndexForward': False
        }
        
        if status_filter:
            query_kwargs['FilterExpression'] = '#status = :status'
            query_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            query_kwargs['ExpressionAttributeValues'][':status'] = status_filter
        
        response = service_requests_table.query(**query_kwargs)
        return response.get('Items', [])
    
    except Exception as e:
        logger.error(f"Error getting technician service requests: {str(e)}")
        return []


def get_consumer_service_requests(consumer_id: str, status_filter: Optional[str], limit: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get service requests for consumer"""
    try:
        # Query by consumer ID using GSI
        query_kwargs = {
            'IndexName': 'ConsumerIndex',
            'KeyConditionExpression': 'consumerId = :consumerId',
            'ExpressionAttributeValues': {':consumerId': consumer_id},
            'Limit': limit,
            'ScanIndexForward': False
        }
        
        if status_filter:
            query_kwargs['FilterExpression'] = '#status = :status'
            query_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            query_kwargs['ExpressionAttributeValues'][':status'] = status_filter
        
        response = service_requests_table.query(**query_kwargs)
        return response.get('Items', [])
    
    except Exception as e:
        logger.error(f"Error getting consumer service requests: {str(e)}")
        return []


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }