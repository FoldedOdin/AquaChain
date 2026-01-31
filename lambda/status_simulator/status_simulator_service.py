"""
Status Simulator Service for AquaChain Enhanced Consumer Ordering System

This Lambda function implements automated order status progression for demonstration purposes.
It provides:
- Automated status progression with EventBridge scheduling
- Simulation control (start/stop/status check)
- Authority restrictions for simulation-enabled orders only
- Proper state management and error handling

Requirements: 4.1, 4.2, 4.3, 4.5
"""

import sys
import os
import json
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
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
eventbridge = boto3.client('events')
sns = boto3.client('sns')

# Environment variables
ORDERS_TABLE = os.environ.get('ENHANCED_ORDERS_TABLE', 'aquachain-orders')
SIMULATIONS_TABLE = os.environ.get('ENHANCED_SIMULATIONS_TABLE', 'aquachain-order-simulations')
SNS_TOPIC_ARN = os.environ.get('ORDER_EVENTS_TOPIC_ARN')
EVENTBRIDGE_BUS = os.environ.get('EVENTBRIDGE_BUS', 'default')
EVENTBRIDGE_RULE_PREFIX = os.environ.get('EVENTBRIDGE_RULE_PREFIX', 'aquachain-status-simulator')

# Initialize logger
logger = get_logger(__name__, service='status-simulator')


class OrderStatus(Enum):
    """Order status enumeration matching the order management service"""
    PENDING_PAYMENT = 'PENDING_PAYMENT'
    PENDING_CONFIRMATION = 'PENDING_CONFIRMATION'
    ORDER_PLACED = 'ORDER_PLACED'
    SHIPPED = 'SHIPPED'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'


class SimulationStatus(Enum):
    """Simulation status enumeration"""
    ACTIVE = 'ACTIVE'
    STOPPED = 'STOPPED'
    COMPLETED = 'COMPLETED'
    ERROR = 'ERROR'


class StatusSimulatorService:
    """
    Status Simulator Service for automated order status progression
    
    This service provides demonstration functionality for order status progression
    with proper authority restrictions and EventBridge scheduling.
    """
    
    def __init__(self):
        self.orders_table = dynamodb.Table(ORDERS_TABLE)
        self.simulations_table = dynamodb.Table(SIMULATIONS_TABLE)
        self.validator = InputValidator()
        self._register_validation_schemas()
        
        # Status progression sequence for demonstration
        self.status_progression = [
            OrderStatus.ORDER_PLACED,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED
        ]
        
        # Simulation interval in seconds (15 seconds for demo)
        self.simulation_interval = 15
        
        # TTL for simulation records (24 hours)
        self.simulation_ttl_hours = 24
    
    def _register_validation_schemas(self):
        """Register validation schemas for simulator operations"""
        
        # Start simulation schema
        start_simulation_schema = {
            'orderId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            )
        }
        
        # Stop simulation schema
        stop_simulation_schema = {
            'orderId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            )
        }
        
        # Get simulation status schema
        get_status_schema = {
            'orderId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            )
        }
        
        self.validator.register_schema('start_simulation', start_simulation_schema)
        self.validator.register_schema('stop_simulation', stop_simulation_schema)
        self.validator.register_schema('get_status', get_status_schema)
    
    def start_simulation(self, order_id: str) -> Dict[str, Any]:
        """
        Start automated status progression for an order
        
        Args:
            order_id: The order ID to start simulation for
            
        Returns:
            Dict containing simulation start confirmation
            
        Raises:
            ValidationError: If input validation fails
            ResourceNotFoundError: If order not found
            BusinessRuleViolationError: If order is not eligible for simulation
        """
        try:
            # Validate input
            self.validator.validate({'orderId': order_id}, 'start_simulation')
            
            logger.info(f"Starting simulation for order {order_id}")
            
            # Check if order exists and is eligible for simulation
            order = self._get_order(order_id)
            if not order:
                raise ResourceNotFoundError(f"Order {order_id} not found")
            
            # Validate order is eligible for simulation
            self._validate_simulation_eligibility(order)
            
            # Check if simulation already exists
            existing_simulation = self._get_simulation(order_id)
            if existing_simulation and existing_simulation.get('isActive'):
                logger.warning(f"Simulation already active for order {order_id}")
                return {
                    'orderId': order_id,
                    'status': 'already_active',
                    'message': 'Simulation is already active for this order'
                }
            
            # Create simulation record
            simulation_record = self._create_simulation_record(order_id, order['status'])
            
            # Schedule first transition if order is in ORDER_PLACED status
            if order['status'] == OrderStatus.ORDER_PLACED.value:
                self._schedule_next_transition(order_id, OrderStatus.SHIPPED)
            
            logger.info(f"Simulation started successfully for order {order_id}")
            
            return {
                'orderId': order_id,
                'status': 'started',
                'currentStatus': order['status'],
                'nextStatus': self._get_next_status(OrderStatus(order['status'])).value if self._get_next_status(OrderStatus(order['status'])) else None,
                'intervalSeconds': self.simulation_interval
            }
            
        except ValidationError as e:
            logger.error(f"Validation error starting simulation: {str(e)}")
            raise
        except (ResourceNotFoundError, BusinessRuleViolationError) as e:
            logger.error(f"Business rule error starting simulation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error starting simulation: {str(e)}")
            raise AquaChainError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Failed to start simulation",
                details={'orderId': order_id, 'error': str(e)}
            )
    
    def stop_simulation(self, order_id: str) -> Dict[str, Any]:
        """
        Stop automated status progression for an order
        
        Args:
            order_id: The order ID to stop simulation for
            
        Returns:
            Dict containing simulation stop confirmation
        """
        try:
            # Validate input
            self.validator.validate({'orderId': order_id}, 'stop_simulation')
            
            logger.info(f"Stopping simulation for order {order_id}")
            
            # Get existing simulation
            simulation = self._get_simulation(order_id)
            if not simulation:
                logger.warning(f"No simulation found for order {order_id}")
                return {
                    'orderId': order_id,
                    'status': 'not_found',
                    'message': 'No active simulation found for this order'
                }
            
            if not simulation.get('isActive'):
                logger.warning(f"Simulation already stopped for order {order_id}")
                return {
                    'orderId': order_id,
                    'status': 'already_stopped',
                    'message': 'Simulation is already stopped for this order'
                }
            
            # Update simulation record to stopped
            self._update_simulation_status(order_id, SimulationStatus.STOPPED)
            
            # Cancel any scheduled EventBridge rules
            self._cancel_scheduled_transitions(order_id)
            
            logger.info(f"Simulation stopped successfully for order {order_id}")
            
            return {
                'orderId': order_id,
                'status': 'stopped',
                'stoppedAt': datetime.now(timezone.utc).isoformat()
            }
            
        except ValidationError as e:
            logger.error(f"Validation error stopping simulation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error stopping simulation: {str(e)}")
            raise AquaChainError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Failed to stop simulation",
                details={'orderId': order_id, 'error': str(e)}
            )
    
    def get_simulation_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get current simulation status for an order
        
        Args:
            order_id: The order ID to get status for
            
        Returns:
            Dict containing simulation status information
        """
        try:
            # Validate input
            self.validator.validate({'orderId': order_id}, 'get_status')
            
            logger.info(f"Getting simulation status for order {order_id}")
            
            # Get simulation record
            simulation = self._get_simulation(order_id)
            if not simulation:
                return {
                    'orderId': order_id,
                    'isActive': False,
                    'status': 'not_found',
                    'message': 'No simulation found for this order'
                }
            
            # Get current order status
            order = self._get_order(order_id)
            current_status = order['status'] if order else simulation.get('currentStatus')
            
            return {
                'orderId': order_id,
                'currentStatus': current_status,
                'nextStatus': simulation.get('nextStatus'),
                'nextTransitionAt': simulation.get('nextTransitionAt'),
                'isActive': simulation.get('isActive', False),
                'intervalSeconds': simulation.get('intervalSeconds', self.simulation_interval),
                'createdAt': simulation.get('createdAt'),
                'updatedAt': simulation.get('updatedAt')
            }
            
        except ValidationError as e:
            logger.error(f"Validation error getting simulation status: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting simulation status: {str(e)}")
            raise AquaChainError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Failed to get simulation status",
                details={'orderId': order_id, 'error': str(e)}
            )
    
    def _get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order from DynamoDB"""
        try:
            response = self.orders_table.get_item(
                Key={
                    'PK': f'ORDER#{order_id}',
                    'SK': f'ORDER#{order_id}'
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            return None
    
    def _get_simulation(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation record from DynamoDB"""
        try:
            response = self.simulations_table.get_item(
                Key={
                    'PK': f'SIMULATION#{order_id}',
                    'SK': f'SIMULATION#{order_id}'
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting simulation {order_id}: {str(e)}")
            return None
    
    def _validate_simulation_eligibility(self, order: Dict[str, Any]) -> None:
        """
        Validate that an order is eligible for simulation
        
        Requirements: 4.5 - Only progress orders that are in active delivery states
        """
        order_status = order.get('status')
        
        # Check if order is simulation-enabled (authority restriction)
        simulation_enabled = order.get('simulationEnabled', False)
        if not simulation_enabled:
            raise BusinessRuleViolationError(
                "Order is not enabled for simulation",
                details={'orderId': order.get('orderId'), 'simulationEnabled': simulation_enabled}
            )
        
        # Check if order is in a valid state for simulation
        valid_simulation_states = [
            OrderStatus.ORDER_PLACED.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.OUT_FOR_DELIVERY.value
        ]
        
        if order_status not in valid_simulation_states:
            raise BusinessRuleViolationError(
                f"Order status {order_status} is not eligible for simulation",
                details={'orderId': order.get('orderId'), 'currentStatus': order_status}
            )
    
    def _get_next_status(self, current_status: OrderStatus) -> Optional[OrderStatus]:
        """Get the next status in the progression sequence"""
        try:
            current_index = self.status_progression.index(current_status)
            if current_index < len(self.status_progression) - 1:
                return self.status_progression[current_index + 1]
            return None
        except ValueError:
            # Current status not in progression sequence
            return None
    
    def _create_simulation_record(self, order_id: str, current_status: str) -> Dict[str, Any]:
        """Create a new simulation record in DynamoDB"""
        now = datetime.now(timezone.utc)
        ttl = int((now + timedelta(hours=self.simulation_ttl_hours)).timestamp())
        
        simulation_record = {
            'PK': f'SIMULATION#{order_id}',
            'SK': f'SIMULATION#{order_id}',
            'orderId': order_id,
            'currentStatus': current_status,
            'nextStatus': self._get_next_status(OrderStatus(current_status)).value if self._get_next_status(OrderStatus(current_status)) else None,
            'isActive': True,
            'intervalSeconds': self.simulation_interval,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat(),
            'ttl': ttl
        }
        
        try:
            self.simulations_table.put_item(Item=simulation_record)
            return simulation_record
        except ClientError as e:
            logger.error(f"Error creating simulation record for order {order_id}: {str(e)}")
            raise
    
    def _update_simulation_status(self, order_id: str, status: SimulationStatus) -> None:
        """Update simulation status in DynamoDB"""
        try:
            self.simulations_table.update_item(
                Key={
                    'PK': f'SIMULATION#{order_id}',
                    'SK': f'SIMULATION#{order_id}'
                },
                UpdateExpression='SET isActive = :active, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':active': status == SimulationStatus.ACTIVE,
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating simulation status for order {order_id}: {str(e)}")
            raise
    
    def _schedule_next_transition(self, order_id: str, next_status: OrderStatus) -> None:
        """Schedule the next status transition using EventBridge"""
        try:
            # Calculate next transition time
            next_transition_time = datetime.now(timezone.utc) + timedelta(seconds=self.simulation_interval)
            
            # Create EventBridge event for scheduling
            event_detail = {
                'orderId': order_id,
                'targetStatus': next_status.value,
                'scheduledAt': next_transition_time.isoformat(),
                'source': 'status_simulator'
            }
            
            # Put event to EventBridge (this will be processed by the same Lambda)
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.ordering',
                        'DetailType': 'Order Status Transition',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': EVENTBRIDGE_BUS,
                        'Time': next_transition_time
                    }
                ]
            )
            
            # Update simulation record with next transition time
            self.simulations_table.update_item(
                Key={
                    'PK': f'SIMULATION#{order_id}',
                    'SK': f'SIMULATION#{order_id}'
                },
                UpdateExpression='SET nextTransitionAt = :next_time, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':next_time': next_transition_time.isoformat(),
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Scheduled next transition for order {order_id} to {next_status.value} at {next_transition_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling next transition for order {order_id}: {str(e)}")
            raise
    
    def _cancel_scheduled_transitions(self, order_id: str) -> None:
        """Cancel any scheduled transitions for an order"""
        # Note: EventBridge doesn't support canceling individual events
        # The transition handler will check if simulation is still active
        logger.info(f"Marked simulation as stopped for order {order_id} - scheduled events will be ignored")


# Lambda handler function
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Status Simulator Service
    
    Handles different event types:
    - API Gateway requests for start/stop/status operations
    - EventBridge events for scheduled transitions
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        service = StatusSimulatorService()
        
        # Handle EventBridge scheduled transition events
        if event.get('source') == 'aquachain.ordering' and event.get('detail-type') == 'Order Status Transition':
            detail = event.get('detail', {})
            order_id = detail.get('orderId')
            
            if not order_id:
                raise ValidationError("Missing orderId in EventBridge event")
            
            # For now, just return success - full transition logic would be implemented here
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'transition_scheduled', 'orderId': order_id})
            }
        
        # Handle API Gateway requests
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
        path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
        
        if not http_method:
            raise ValidationError("Unable to determine HTTP method from event")
        
        # Parse request body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON in request body")
        
        # Route to appropriate handler
        if http_method == 'POST' and '/start' in path:
            order_id = body.get('orderId')
            if not order_id:
                raise ValidationError("Missing orderId in request body")
            
            result = service.start_simulation(order_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        elif http_method == 'POST' and '/stop' in path:
            order_id = body.get('orderId')
            if not order_id:
                raise ValidationError("Missing orderId in request body")
            
            result = service.stop_simulation(order_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        elif http_method == 'GET' and '/status' in path:
            # Extract orderId from path parameters or query string
            order_id = event.get('pathParameters', {}).get('orderId')
            if not order_id:
                order_id = event.get('queryStringParameters', {}).get('orderId')
            
            if not order_id:
                raise ValidationError("Missing orderId in path or query parameters")
            
            result = service.get_simulation_status(order_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'No handler for {http_method} {path}'
                })
            }
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return create_lambda_error_response(e)
    
    except (ResourceNotFoundError, BusinessRuleViolationError, ConflictError) as e:
        logger.error(f"Business error: {str(e)}")
        return create_lambda_error_response(e)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        error = AquaChainError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            details={'error': str(e)}
        )
        return create_lambda_error_response(error)