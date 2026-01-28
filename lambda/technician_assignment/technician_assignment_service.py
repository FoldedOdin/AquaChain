"""
Technician Assignment Service for Enhanced Consumer Ordering System

This Lambda function implements the Technician Assignment Service with support for:
- Geographic proximity calculation using Haversine formula
- Technician availability management
- Assignment logic with conflict resolution
- Integration with enhanced ordering system

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import sys
import os
import json
import boto3
import math
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
import uuid
from botocore.exceptions import ClientError

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger
from input_validator import InputValidator, ValidationRule, FieldType, ValidationError
from error_handler import (
    AquaChainError, ErrorCode, ResourceNotFoundError, ConflictError,
    BusinessRuleViolationError, create_lambda_error_response
)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')

# Environment variables
ORDERS_TABLE = os.environ.get('ENHANCED_ORDERS_TABLE', 'aquachain-orders')
TECHNICIANS_TABLE = os.environ.get('ENHANCED_TECHNICIANS_TABLE', 'aquachain-technicians')
SNS_TOPIC_ARN = os.environ.get('TECHNICIAN_EVENTS_TOPIC_ARN')
EVENTBRIDGE_BUS = os.environ.get('EVENTBRIDGE_BUS', 'default')

# Initialize logger
logger = get_logger(__name__, service='technician-assignment')


class TechnicianAssignmentService:
    """
    Technician Assignment Service with geographic proximity and availability management
    """
    
    def __init__(self):
        self.orders_table = dynamodb.Table(ORDERS_TABLE)
        self.technicians_table = dynamodb.Table(TECHNICIANS_TABLE)
        self.validator = InputValidator()
        self._register_validation_schemas()
        
        # Assignment parameters
        self.MAX_ASSIGNMENT_DISTANCE_KM = 50  # Maximum distance for assignment
        self.ASSIGNMENT_TIMEOUT_MINUTES = 30  # Time before assignment expires
    
    def _register_validation_schemas(self):
        """Register validation schemas for technician assignment operations"""
        
        # Assign technician schema
        assign_technician_schema = {
            'orderId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            ),
            'serviceLocation': ValidationRule(
                field_type=FieldType.OBJECT,
                required=True
            )
        }
        
        # Update availability schema
        update_availability_schema = {
            'technicianId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            ),
            'available': ValidationRule(
                field_type=FieldType.BOOLEAN,
                required=True
            )
        }
        
        self.validator.register_schema('assign_technician', assign_technician_schema)
        self.validator.register_schema('update_availability', update_availability_schema)
    
    def assign_technician(self, request_data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Assign the nearest available technician to an order
        
        Args:
            request_data: Assignment request data with orderId and serviceLocation
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Assignment result with technician details
            
        Raises:
            ValidationError: If input validation fails
            ResourceNotFoundError: If order not found
            BusinessRuleViolationError: If no technicians available
        """
        logger.start_operation('assign_technician')
        
        try:
            # Validate input
            validated_data = self.validator.validate_input(
                request_data, 'assign_technician', correlation_id
            )
            
            order_id = validated_data['orderId']
            service_location = validated_data['serviceLocation']
            
            # Validate service location coordinates
            if not self._validate_location(service_location):
                raise ValidationError('Invalid service location coordinates')
            
            # Get available technicians
            available_technicians = self._get_available_technicians()
            
            if not available_technicians:
                logger.warning('No available technicians found', order_id=order_id)
                return self._handle_no_technicians_available(order_id, correlation_id)
            
            # Calculate distances and find nearest technician
            technicians_with_distance = self._calculate_technician_distances(
                available_technicians, service_location
            )
            
            # Filter technicians within service area
            nearby_technicians = [
                tech for tech in technicians_with_distance
                if tech['distance_km'] <= self.MAX_ASSIGNMENT_DISTANCE_KM
            ]
            
            if not nearby_technicians:
                logger.warning('No technicians within service area', 
                             order_id=order_id, max_distance=self.MAX_ASSIGNMENT_DISTANCE_KM)
                return self._handle_no_technicians_in_area(order_id, technicians_with_distance, correlation_id)
            
            # Select best technician (nearest with highest rating)
            selected_technician = self._select_best_technician(nearby_technicians)
            
            # Create assignment
            assignment = self._create_technician_assignment(
                order_id, selected_technician, service_location, correlation_id
            )
            
            # Update order with technician assignment
            self._update_order_with_assignment(order_id, assignment, correlation_id)
            
            # Update technician availability
            self._mark_technician_busy(selected_technician['id'], order_id, correlation_id)
            
            # Publish assignment event
            self._publish_assignment_event('TECHNICIAN_ASSIGNED', assignment, correlation_id)
            
            logger.end_operation('assign_technician', success=True, 
                               order_id=order_id, technician_id=selected_technician['id'])
            
            return {
                'success': True,
                'data': assignment,
                'message': f'Technician {selected_technician["name"]} assigned successfully'
            }
            
        except (ValidationError, ResourceNotFoundError, BusinessRuleViolationError):
            logger.end_operation('assign_technician', success=False)
            raise
        except Exception as e:
            logger.error('Unexpected error during technician assignment', error=str(e), correlation_id=correlation_id)
            logger.end_operation('assign_technician', success=False)
            raise AquaChainError(
                'Internal error during technician assignment',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def get_available_technicians(self, request_data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of available technicians within specified radius
        
        Args:
            request_data: Request with location and optional radius
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            List of available technicians
        """
        logger.start_operation('get_available_technicians')
        
        try:
            location = request_data.get('location')
            radius = request_data.get('radius', self.MAX_ASSIGNMENT_DISTANCE_KM)
            
            # Get all available technicians
            available_technicians = self._get_available_technicians()
            
            if location:
                # Filter by location if provided
                technicians_with_distance = self._calculate_technician_distances(
                    available_technicians, location
                )
                nearby_technicians = [
                    tech for tech in technicians_with_distance
                    if tech['distance_km'] <= radius
                ]
            else:
                nearby_technicians = available_technicians
            
            logger.end_operation('get_available_technicians', success=True, count=len(nearby_technicians))
            
            return {
                'success': True,
                'data': nearby_technicians,
                'count': len(nearby_technicians)
            }
            
        except Exception as e:
            logger.error('Error getting available technicians', error=str(e), correlation_id=correlation_id)
            logger.end_operation('get_available_technicians', success=False)
            raise AquaChainError(
                'Failed to get available technicians',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def update_technician_availability(self, request_data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update technician availability status
        
        Args:
            request_data: Request with technicianId and available status
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Update result
        """
        logger.start_operation('update_technician_availability')
        
        try:
            # Validate input
            validated_data = self.validator.validate_input(
                request_data, 'update_availability', correlation_id
            )
            
            technician_id = validated_data['technicianId']
            available = validated_data['available']
            
            # Get current technician record
            technician = self._get_technician_by_id(technician_id)
            if not technician:
                raise ResourceNotFoundError('Technician', technician_id, correlation_id)
            
            # Update availability
            timestamp = datetime.now(timezone.utc).isoformat()
            
            try:
                self.technicians_table.update_item(
                    Key={
                        'PK': f'TECHNICIAN#{technician_id}',
                        'SK': f'TECHNICIAN#{technician_id}'
                    },
                    UpdateExpression='SET available = :available, updatedAt = :timestamp',
                    ExpressionAttributeValues={
                        ':available': available,
                        ':timestamp': timestamp
                    }
                )
                
                # Update GSI1 for availability filtering
                self.technicians_table.update_item(
                    Key={
                        'PK': f'TECHNICIAN#{technician_id}',
                        'SK': f'TECHNICIAN#{technician_id}'
                    },
                    UpdateExpression='SET GSI1SK = :gsi1sk',
                    ExpressionAttributeValues={
                        ':gsi1sk': f'AVAILABLE#{available}#{technician_id}'
                    }
                )
                
            except ClientError as e:
                logger.error('DynamoDB error updating technician availability', error=str(e), correlation_id=correlation_id)
                raise AquaChainError(
                    'Failed to update technician availability',
                    ErrorCode.DATABASE_ERROR,
                    500,
                    correlation_id=correlation_id
                )
            
            # Publish availability update event
            self._publish_assignment_event('TECHNICIAN_AVAILABILITY_UPDATED', {
                'technicianId': technician_id,
                'available': available,
                'timestamp': timestamp
            }, correlation_id)
            
            logger.end_operation('update_technician_availability', success=True, 
                               technician_id=technician_id, available=available)
            
            return {
                'success': True,
                'message': f'Technician availability updated to {available}'
            }
            
        except (ValidationError, ResourceNotFoundError):
            logger.end_operation('update_technician_availability', success=False)
            raise
        except Exception as e:
            logger.error('Unexpected error updating technician availability', error=str(e), correlation_id=correlation_id)
            logger.end_operation('update_technician_availability', success=False)
            raise AquaChainError(
                'Internal error updating technician availability',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def _get_available_technicians(self) -> List[Dict[str, Any]]:
        """Get all available technicians from DynamoDB"""
        try:
            response = self.technicians_table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :location_key',
                FilterExpression='available = :available',
                ExpressionAttributeValues={
                    ':location_key': 'LOCATION#ALL',  # Assuming all technicians have this GSI1PK
                    ':available': True
                }
            )
            
            technicians = []
            for item in response.get('Items', []):
                technician = {
                    'id': item['technicianId'],
                    'name': item['name'],
                    'phone': item['phone'],
                    'email': item['email'],
                    'location': item['location'],
                    'available': item['available'],
                    'skills': item.get('skills', []),
                    'rating': float(item.get('rating', 0))
                }
                technicians.append(technician)
            
            return technicians
            
        except Exception as e:
            logger.error('Error getting available technicians from database', error=str(e))
            return []
    
    def _get_technician_by_id(self, technician_id: str) -> Optional[Dict[str, Any]]:
        """Get technician by ID from DynamoDB"""
        try:
            response = self.technicians_table.get_item(
                Key={
                    'PK': f'TECHNICIAN#{technician_id}',
                    'SK': f'TECHNICIAN#{technician_id}'
                }
            )
            return response.get('Item')
        except Exception:
            return None
    
    def _validate_location(self, location: Dict[str, Any]) -> bool:
        """Validate location coordinates"""
        try:
            lat = float(location.get('latitude', 0))
            lon = float(location.get('longitude', 0))
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, TypeError):
            return False
    
    def _calculate_haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using Haversine formula
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        
        return c * r
    
    def _calculate_technician_distances(self, technicians: List[Dict[str, Any]], 
                                      service_location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate distances from service location to all technicians"""
        service_lat = float(service_location['latitude'])
        service_lon = float(service_location['longitude'])
        
        technicians_with_distance = []
        
        for technician in technicians:
            try:
                tech_lat = float(technician['location']['latitude'])
                tech_lon = float(technician['location']['longitude'])
                
                distance = self._calculate_haversine_distance(
                    service_lat, service_lon, tech_lat, tech_lon
                )
                
                technician_copy = technician.copy()
                technician_copy['distance_km'] = round(distance, 2)
                technician_copy['estimated_travel_time_minutes'] = round(distance * 2, 0)  # Rough estimate: 30 km/h average
                
                technicians_with_distance.append(technician_copy)
                
            except (ValueError, KeyError, TypeError) as e:
                logger.warning('Invalid technician location data', 
                             technician_id=technician.get('id'), error=str(e))
                continue
        
        # Sort by distance (nearest first)
        technicians_with_distance.sort(key=lambda x: x['distance_km'])
        
        return technicians_with_distance
    
    def _select_best_technician(self, technicians: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select the best technician based on distance and rating
        
        Args:
            technicians: List of technicians with distance calculated
            
        Returns:
            Selected technician
        """
        if not technicians:
            raise BusinessRuleViolationError(
                'No technicians available for selection',
                'no_technicians_available'
            )
        
        # If only one technician, select them
        if len(technicians) == 1:
            return technicians[0]
        
        # Find technicians with minimum distance
        min_distance = technicians[0]['distance_km']
        nearest_technicians = [
            tech for tech in technicians
            if tech['distance_km'] <= min_distance + 2  # 2km tolerance
        ]
        
        # Among nearest technicians, select the one with highest rating
        best_technician = max(nearest_technicians, key=lambda x: x['rating'])
        
        return best_technician
    
    def _create_technician_assignment(self, order_id: str, technician: Dict[str, Any], 
                                    service_location: Dict[str, Any], 
                                    correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Create technician assignment record"""
        timestamp = datetime.now(timezone.utc).isoformat()
        estimated_arrival = datetime.now(timezone.utc) + timedelta(
            minutes=technician.get('estimated_travel_time_minutes', 30)
        )
        
        assignment = {
            'orderId': order_id,
            'technicianId': technician['id'],
            'technicianName': technician['name'],
            'technicianPhone': technician['phone'],
            'assignedAt': timestamp,
            'estimatedArrival': estimated_arrival.isoformat(),
            'distance': technician['distance_km'],
            'estimatedTravelTime': technician.get('estimated_travel_time_minutes', 30),
            'status': 'assigned',
            'serviceLocation': service_location
        }
        
        return assignment
    
    def _update_order_with_assignment(self, order_id: str, assignment: Dict[str, Any], 
                                    correlation_id: Optional[str] = None):
        """Update order record with technician assignment"""
        try:
            self.orders_table.update_item(
                Key={
                    'PK': f'ORDER#{order_id}',
                    'SK': f'ORDER#{order_id}'
                },
                UpdateExpression='''
                    SET assignedTechnician = :technician_id,
                        technicianAssignment = :assignment,
                        updatedAt = :timestamp
                ''',
                ExpressionAttributeValues={
                    ':technician_id': assignment['technicianId'],
                    ':assignment': assignment,
                    ':timestamp': assignment['assignedAt']
                }
            )
        except ClientError as e:
            logger.error('Failed to update order with assignment', 
                        order_id=order_id, error=str(e), correlation_id=correlation_id)
            raise AquaChainError(
                'Failed to update order with technician assignment',
                ErrorCode.DATABASE_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def _mark_technician_busy(self, technician_id: str, order_id: str, 
                            correlation_id: Optional[str] = None):
        """Mark technician as busy with current order"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            self.technicians_table.update_item(
                Key={
                    'PK': f'TECHNICIAN#{technician_id}',
                    'SK': f'TECHNICIAN#{technician_id}'
                },
                UpdateExpression='''
                    SET available = :available,
                        currentOrderId = :order_id,
                        assignedAt = :timestamp,
                        updatedAt = :timestamp,
                        GSI1SK = :gsi1sk
                ''',
                ExpressionAttributeValues={
                    ':available': False,
                    ':order_id': order_id,
                    ':timestamp': timestamp,
                    ':gsi1sk': f'AVAILABLE#False#{technician_id}'
                }
            )
        except ClientError as e:
            logger.error('Failed to mark technician as busy', 
                        technician_id=technician_id, error=str(e), correlation_id=correlation_id)
            # Don't raise error here as assignment was successful
    
    def _handle_no_technicians_available(self, order_id: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle case when no technicians are available"""
        logger.warning('No technicians available for assignment', order_id=order_id)
        
        # Publish event for admin notification
        self._publish_assignment_event('NO_TECHNICIANS_AVAILABLE', {
            'orderId': order_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': 'No technicians currently available'
        }, correlation_id)
        
        raise BusinessRuleViolationError(
            'No technicians are currently available for assignment. The order will be queued and assigned when a technician becomes available.',
            'no_technicians_available',
            correlation_id
        )
    
    def _handle_no_technicians_in_area(self, order_id: str, all_technicians: List[Dict[str, Any]], 
                                     correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle case when no technicians are within service area"""
        nearest_distance = min(tech['distance_km'] for tech in all_technicians) if all_technicians else 0
        
        logger.warning('No technicians within service area', 
                      order_id=order_id, nearest_distance=nearest_distance)
        
        # Publish event for admin notification
        self._publish_assignment_event('NO_TECHNICIANS_IN_AREA', {
            'orderId': order_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': f'No technicians within {self.MAX_ASSIGNMENT_DISTANCE_KM}km service area',
            'nearestTechnicianDistance': nearest_distance
        }, correlation_id)
        
        raise BusinessRuleViolationError(
            f'No technicians available within {self.MAX_ASSIGNMENT_DISTANCE_KM}km service area. The nearest technician is {nearest_distance:.1f}km away.',
            'no_technicians_in_area',
            correlation_id
        )
    
    def _publish_assignment_event(self, event_type: str, event_data: Dict[str, Any], 
                                correlation_id: Optional[str] = None):
        """Publish assignment event to SNS and EventBridge"""
        try:
            event_payload = {
                'eventType': event_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlationId': correlation_id,
                **event_data
            }
            
            # Publish to SNS for real-time notifications
            if SNS_TOPIC_ARN:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=json.dumps(event_payload),
                    Subject=f'Technician Assignment Event: {event_type}'
                )
            
            # Publish to EventBridge for workflow automation
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.technician-assignment',
                        'DetailType': event_type,
                        'Detail': json.dumps(event_payload),
                        'EventBusName': EVENTBRIDGE_BUS
                    }
                ]
            )
            
        except Exception as e:
            logger.warning('Failed to publish assignment event', error=str(e), event_type=event_type)


# Initialize service
assignment_service = TechnicianAssignmentService()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for technician assignment operations
    
    Supported operations:
    - POST /technician-assignment - Assign technician to order
    - GET /technicians/available - Get available technicians
    - PUT /technicians/{technicianId}/availability - Update technician availability
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Extract request information
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body', '{}')
        
        # Parse request body
        try:
            request_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON in request body')
        
        # Add correlation ID to request data
        request_data['correlationId'] = correlation_id
        
        # Route to appropriate operation
        if http_method == 'POST' and path == '/technician-assignment':
            # Assign technician to order
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(assignment_service.assign_technician(request_data, correlation_id))
            }
        
        elif http_method == 'GET' and path == '/technicians/available':
            # Get available technicians
            # Add query parameters to request data
            if query_parameters:
                if 'latitude' in query_parameters and 'longitude' in query_parameters:
                    request_data['location'] = {
                        'latitude': float(query_parameters['latitude']),
                        'longitude': float(query_parameters['longitude'])
                    }
                if 'radius' in query_parameters:
                    request_data['radius'] = float(query_parameters['radius'])
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(assignment_service.get_available_technicians(request_data, correlation_id))
            }
        
        elif http_method == 'PUT' and path_parameters.get('technicianId') and 'availability' in path:
            # Update technician availability
            request_data['technicianId'] = path_parameters['technicianId']
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(assignment_service.update_technician_availability(request_data, correlation_id))
            }
        
        else:
            # Unsupported operation
            raise ValidationError(f'Unsupported operation: {http_method} {path}')
    
    except AquaChainError as e:
        logger.error('AquaChain error in technician assignment', error=str(e), correlation_id=correlation_id)
        return create_lambda_error_response(e, correlation_id, 'technician-assignment')
    
    except Exception as e:
        logger.error('Unexpected error in technician assignment', error=str(e), correlation_id=correlation_id)
        error = AquaChainError(
            'Internal server error',
            ErrorCode.INTERNAL_ERROR,
            500,
            correlation_id=correlation_id
        )
        return create_lambda_error_response(error, correlation_id, 'technician-assignment')