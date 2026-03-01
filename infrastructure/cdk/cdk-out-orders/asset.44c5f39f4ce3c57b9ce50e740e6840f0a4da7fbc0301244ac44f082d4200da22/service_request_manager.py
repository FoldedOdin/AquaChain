"""
Service Request Lifecycle Management
Handles creation, status tracking, notifications, and completion workflow
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import uuid
from decimal import Decimal

# Import structured logging
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger

logger = get_logger(__name__, service='service-request-manager')

class ServiceRequestManager:
    """Manages the complete lifecycle of service requests"""
    
    def __init__(self, service_requests_table_name: str, users_table_name: str, 
                 websocket_api_endpoint: str = None, notification_topic_arn: str = None):
        self.dynamodb = boto3.resource('dynamodb')
        self.sns = boto3.client('sns')
        self.apigateway_management = None
        
        self.service_requests_table = self.dynamodb.Table(service_requests_table_name)
        self.users_table = self.dynamodb.Table(users_table_name)
        
        self.websocket_api_endpoint = websocket_api_endpoint
        self.notification_topic_arn = notification_topic_arn
        
        # Initialize API Gateway Management API client if endpoint provided
        if websocket_api_endpoint:
            self.apigateway_management = boto3.client(
                'apigatewaymanagementapi',
                endpoint_url=websocket_api_endpoint
            )
        
        # Service request status flow
        self.STATUS_FLOW = {
            'pending': ['assigned', 'cancelled'],
            'assigned': ['accepted', 'cancelled'],
            'accepted': ['en_route', 'cancelled'],
            'en_route': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],  # Terminal state
            'cancelled': []   # Terminal state
        }
    
    def create_service_request(self, consumer_id: str, request_data: Dict) -> Dict:
        """
        Create a new service request
        
        Args:
            consumer_id: ID of the consumer creating the request
            request_data: Request details (deviceId, location, description, etc.)
            
        Returns:
            Dict with created service request
        """
        try:
            # Validate required fields
            required_fields = ['deviceId', 'location', 'description']
            for field in required_fields:
                if field not in request_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Generate unique request ID
            request_id = f"SR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
            
            # Create service request record
            service_request = {
                'requestId': request_id,
                'consumerId': consumer_id,
                'deviceId': request_data['deviceId'],
                'status': 'pending',
                'location': request_data['location'],
                'description': request_data['description'],
                'priority': request_data.get('priority', 'normal'),
                'createdAt': datetime.utcnow().isoformat(),
                'notes': [],
                'statusHistory': [
                    {
                        'status': 'pending',
                        'timestamp': datetime.utcnow().isoformat(),
                        'updatedBy': consumer_id,
                        'note': 'Service request created'
                    }
                ]
            }
            
            # Add optional fields
            if 'urgency' in request_data:
                service_request['urgency'] = request_data['urgency']
            
            if 'preferredTimeSlot' in request_data:
                service_request['preferredTimeSlot'] = request_data['preferredTimeSlot']
            
            # Save to database
            self.service_requests_table.put_item(Item=service_request)
            
            # Send creation notification
            self._send_service_request_notification(service_request, 'created')
            
            logger.info(f"Created service request {request_id} for consumer {consumer_id}")
            
            return {
                'success': True,
                'service_request': service_request
            }
            
        except Exception as e:
            logger.error(f"Error creating service request: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create service request: {str(e)}'
            }
    
    def update_service_request_status(self, request_id: str, new_status: str, 
                                    updated_by: str, note: str = '', 
                                    additional_data: Dict = None) -> Dict:
        """
        Update service request status with validation and notifications
        
        Args:
            request_id: Service request ID
            new_status: New status to set
            updated_by: User ID making the update
            note: Optional note about the status change
            additional_data: Additional data to update (e.g., ETA, completion details)
            
        Returns:
            Dict with update results
        """
        try:
            # Get current service request
            response = self.service_requests_table.get_item(Key={'requestId': request_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Service request not found'
                }
            
            service_request = response['Item']
            current_status = service_request['status']
            
            # Validate status transition
            if not self._is_valid_status_transition(current_status, new_status):
                return {
                    'success': False,
                    'error': f'Invalid status transition from {current_status} to {new_status}'
                }
            
            # Update status and add to history
            service_request['status'] = new_status
            service_request['lastUpdated'] = datetime.utcnow().isoformat()
            
            # Add status history entry
            status_entry = {
                'status': new_status,
                'timestamp': datetime.utcnow().isoformat(),
                'updatedBy': updated_by,
                'note': note or f'Status updated to {new_status}'
            }
            
            if 'statusHistory' not in service_request:
                service_request['statusHistory'] = []
            service_request['statusHistory'].append(status_entry)
            
            # Handle specific status transitions
            if new_status == 'accepted':
                service_request['acceptedAt'] = datetime.utcnow().isoformat()
                if additional_data and 'estimatedArrival' in additional_data:
                    service_request['estimatedArrival'] = additional_data['estimatedArrival']
            
            elif new_status == 'en_route':
                service_request['enRouteAt'] = datetime.utcnow().isoformat()
                if additional_data and 'currentLocation' in additional_data:
                    service_request['technicianLocation'] = additional_data['currentLocation']
            
            elif new_status == 'in_progress':
                service_request['startedAt'] = datetime.utcnow().isoformat()
            
            elif new_status == 'completed':
                service_request['completedAt'] = datetime.utcnow().isoformat()
                if additional_data:
                    if 'workPerformed' in additional_data:
                        service_request['workPerformed'] = additional_data['workPerformed']
                    if 'partsUsed' in additional_data:
                        service_request['partsUsed'] = additional_data['partsUsed']
                    if 'followUpRequired' in additional_data:
                        service_request['followUpRequired'] = additional_data['followUpRequired']
            
            elif new_status == 'cancelled':
                service_request['cancelledAt'] = datetime.utcnow().isoformat()
                if additional_data and 'cancellationReason' in additional_data:
                    service_request['cancellationReason'] = additional_data['cancellationReason']
            
            # Add any additional data
            if additional_data:
                for key, value in additional_data.items():
                    if key not in ['estimatedArrival', 'currentLocation', 'workPerformed', 
                                 'partsUsed', 'followUpRequired', 'cancellationReason']:
                        service_request[key] = value
            
            # Save updated service request
            self.service_requests_table.put_item(Item=service_request)
            
            # Send status update notifications
            self._send_service_request_notification(service_request, 'status_updated', {
                'previous_status': current_status,
                'new_status': new_status,
                'updated_by': updated_by,
                'note': note
            })
            
            # Send real-time updates via WebSocket
            self._send_realtime_update(service_request, 'status_updated')
            
            logger.info(f"Updated service request {request_id} status from {current_status} to {new_status}")
            
            return {
                'success': True,
                'service_request': service_request,
                'previous_status': current_status
            }
            
        except Exception as e:
            logger.error(f"Error updating service request status: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to update status: {str(e)}'
            }
    
    def add_service_note(self, request_id: str, author_id: str, note_type: str, 
                        content: str, attachments: List[str] = None) -> Dict:
        """
        Add a note to a service request
        
        Args:
            request_id: Service request ID
            author_id: User ID of note author
            note_type: Type of note ('technician_note', 'customer_feedback', 'system_note')
            content: Note content
            attachments: List of attachment URLs/IDs
            
        Returns:
            Dict with update results
        """
        try:
            # Get current service request
            response = self.service_requests_table.get_item(Key={'requestId': request_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Service request not found'
                }
            
            service_request = response['Item']
            
            # Create note entry
            note_entry = {
                'noteId': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'author': author_id,
                'type': note_type,
                'content': content
            }
            
            if attachments:
                note_entry['attachments'] = attachments
            
            # Add note to service request
            if 'notes' not in service_request:
                service_request['notes'] = []
            service_request['notes'].append(note_entry)
            
            service_request['lastUpdated'] = datetime.utcnow().isoformat()
            
            # Save updated service request
            self.service_requests_table.put_item(Item=service_request)
            
            # Send notification for important notes
            if note_type in ['technician_note', 'customer_feedback']:
                self._send_service_request_notification(service_request, 'note_added', {
                    'note_type': note_type,
                    'author': author_id,
                    'content': content[:100] + '...' if len(content) > 100 else content
                })
            
            # Send real-time update
            self._send_realtime_update(service_request, 'note_added', note_entry)
            
            logger.info(f"Added {note_type} note to service request {request_id}")
            
            return {
                'success': True,
                'note': note_entry
            }
            
        except Exception as e:
            logger.error(f"Error adding service note: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to add note: {str(e)}'
            }
    
    def complete_service_request(self, request_id: str, technician_id: str, 
                               completion_data: Dict) -> Dict:
        """
        Complete a service request with work details and customer feedback prompt
        
        Args:
            request_id: Service request ID
            technician_id: ID of completing technician
            completion_data: Work performed, parts used, etc.
            
        Returns:
            Dict with completion results
        """
        try:
            # Update status to completed
            result = self.update_service_request_status(
                request_id, 'completed', technician_id,
                note='Service completed by technician',
                additional_data=completion_data
            )
            
            if not result['success']:
                return result
            
            service_request = result['service_request']
            
            # Send completion notification to consumer
            self._send_completion_notification(service_request)
            
            # Schedule customer feedback request
            self._schedule_feedback_request(service_request)
            
            logger.info(f"Completed service request {request_id}")
            
            return {
                'success': True,
                'service_request': service_request,
                'message': 'Service request completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error completing service request: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to complete service request: {str(e)}'
            }
    
    def submit_customer_rating(self, request_id: str, consumer_id: str, 
                             rating: int, feedback: str = '') -> Dict:
        """
        Submit customer rating and feedback for completed service
        
        Args:
            request_id: Service request ID
            consumer_id: Consumer submitting rating
            rating: Rating (1-5 stars)
            feedback: Optional feedback text
            
        Returns:
            Dict with submission results
        """
        try:
            # Validate rating
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return {
                    'success': False,
                    'error': 'Rating must be an integer between 1 and 5'
                }
            
            # Get service request
            response = self.service_requests_table.get_item(Key={'requestId': request_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Service request not found'
                }
            
            service_request = response['Item']
            
            # Verify consumer owns this request
            if service_request['consumerId'] != consumer_id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Verify request is completed
            if service_request['status'] != 'completed':
                return {
                    'success': False,
                    'error': 'Can only rate completed service requests'
                }
            
            # Add rating and feedback
            service_request['customerRating'] = rating
            service_request['customerFeedback'] = feedback
            service_request['ratedAt'] = datetime.utcnow().isoformat()
            service_request['lastUpdated'] = datetime.utcnow().isoformat()
            
            # Add feedback note
            feedback_note = {
                'noteId': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'author': consumer_id,
                'type': 'customer_feedback',
                'content': f'Customer rating: {rating}/5 stars' + (f' - {feedback}' if feedback else '')
            }
            
            if 'notes' not in service_request:
                service_request['notes'] = []
            service_request['notes'].append(feedback_note)
            
            # Save updated service request
            self.service_requests_table.put_item(Item=service_request)
            
            # Notify technician of rating
            if 'technicianId' in service_request:
                self._send_rating_notification(service_request)
            
            logger.info(f"Customer rating submitted for service request {request_id}: {rating}/5 stars")
            
            return {
                'success': True,
                'message': 'Rating submitted successfully',
                'rating': rating
            }
            
        except Exception as e:
            logger.error(f"Error submitting customer rating: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to submit rating: {str(e)}'
            }
    
    def get_service_request_history(self, user_id: str, user_role: str, 
                                  limit: int = 50, status_filter: str = None) -> Dict:
        """
        Get service request history for a user
        
        Args:
            user_id: User ID
            user_role: User role (consumer, technician, administrator)
            limit: Maximum number of requests to return
            status_filter: Optional status filter
            
        Returns:
            Dict with service request history
        """
        try:
            # Build filter expression based on user role
            if user_role == 'consumer':
                filter_expression = 'consumerId = :user_id'
                expression_values = {':user_id': user_id}
            elif user_role == 'technician':
                filter_expression = 'technicianId = :user_id'
                expression_values = {':user_id': user_id}
            elif user_role == 'administrator':
                filter_expression = None
                expression_values = {}
            else:
                return {
                    'success': False,
                    'error': 'Invalid user role'
                }
            
            # Add status filter if provided
            if status_filter:
                if filter_expression:
                    filter_expression += ' AND #status = :status'
                else:
                    filter_expression = '#status = :status'
                expression_values[':status'] = status_filter
            
            # Query service requests
            scan_kwargs = {
                'Limit': limit
            }
            
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
                scan_kwargs['ExpressionAttributeValues'] = expression_values
                
            if status_filter:
                scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            
            response = self.service_requests_table.scan(**scan_kwargs)
            
            # Sort by creation date (newest first)
            service_requests = sorted(
                response['Items'],
                key=lambda x: x.get('createdAt', ''),
                reverse=True
            )
            
            return {
                'success': True,
                'service_requests': service_requests,
                'count': len(service_requests)
            }
            
        except Exception as e:
            logger.error(f"Error getting service request history: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to get history: {str(e)}'
            }
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Check if status transition is valid"""
        return new_status in self.STATUS_FLOW.get(current_status, [])
    
    def _send_service_request_notification(self, service_request: Dict, 
                                         notification_type: str, context: Dict = None):
        """Send notification about service request updates"""
        try:
            if not self.notification_topic_arn:
                return
            
            message_data = {
                'type': f'service_request_{notification_type}',
                'requestId': service_request['requestId'],
                'consumerId': service_request['consumerId'],
                'status': service_request['status'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if context:
                message_data.update(context)
            
            # Add technician info if available
            if 'technicianId' in service_request:
                message_data['technicianId'] = service_request['technicianId']
            
            self.sns.publish(
                TopicArn=self.notification_topic_arn,
                Subject=f'Service Request {notification_type.title()}: {service_request["requestId"]}',
                Message=json.dumps(message_data, indent=2)
            )
            
        except Exception as e:
            logger.error(f"Error sending service request notification: {str(e)}")
    
    def _send_realtime_update(self, service_request: Dict, update_type: str, data: Dict = None):
        """Send real-time update via WebSocket"""
        try:
            if not self.apigateway_management:
                return
            
            update_message = {
                'type': f'service_request_{update_type}',
                'requestId': service_request['requestId'],
                'status': service_request['status'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if data:
                update_message['data'] = data
            
            # Send to consumer
            self._send_websocket_message(service_request['consumerId'], update_message)
            
            # Send to technician if assigned
            if 'technicianId' in service_request:
                self._send_websocket_message(service_request['technicianId'], update_message)
            
        except Exception as e:
            logger.error(f"Error sending real-time update: {str(e)}")
    
    def _send_websocket_message(self, user_id: str, message: Dict):
        """Send WebSocket message to specific user"""
        try:
            # This would typically look up active WebSocket connections for the user
            # For now, we'll log the message
            logger.info(f"WebSocket message for user {user_id}: {json.dumps(message)}")
            
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
    
    def _send_completion_notification(self, service_request: Dict):
        """Send service completion notification to consumer"""
        try:
            completion_message = {
                'type': 'service_completed',
                'requestId': service_request['requestId'],
                'completedAt': service_request.get('completedAt'),
                'workPerformed': service_request.get('workPerformed', 'Service completed'),
                'message': 'Your service request has been completed. Please rate your experience.'
            }
            
            self._send_service_request_notification(service_request, 'completed', completion_message)
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {str(e)}")
    
    def _schedule_feedback_request(self, service_request: Dict):
        """Schedule customer feedback request"""
        try:
            # This would typically schedule a delayed notification
            # For now, we'll log the scheduling
            logger.info(f"Scheduled feedback request for service request {service_request['requestId']}")
            
        except Exception as e:
            logger.error(f"Error scheduling feedback request: {str(e)}")
    
    def _send_rating_notification(self, service_request: Dict):
        """Send rating notification to technician"""
        try:
            rating_message = {
                'type': 'customer_rating_received',
                'requestId': service_request['requestId'],
                'rating': service_request.get('customerRating'),
                'feedback': service_request.get('customerFeedback', ''),
                'message': f'Customer rated your service: {service_request.get("customerRating", 0)}/5 stars'
            }
            
            self._send_service_request_notification(service_request, 'rated', rating_message)
            
        except Exception as e:
            logger.error(f"Error sending rating notification: {str(e)}")