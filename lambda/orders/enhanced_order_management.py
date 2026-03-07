"""
Enhanced Order Management Service for AquaChain Consumer Ordering System

This Lambda function implements the Order Management Service with support for:
- Order creation with payment method selection (COD/Online)
- Order status updates with state transition validation
- Order retrieval with proper filtering and pagination
- Optimistic locking for concurrent updates
- Comprehensive error handling and validation

Requirements: 1.3, 8.1, 8.4
"""

import sys
import os
import json
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
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
sns = boto3.client('sns')
eventbridge = boto3.client('events')

# Environment variables
ORDERS_TABLE = os.environ.get('ORDERS_TABLE_NAME', os.environ.get('ENHANCED_ORDERS_TABLE', 'aquachain-orders'))
PAYMENTS_TABLE = os.environ.get('PAYMENTS_TABLE_NAME', os.environ.get('ENHANCED_PAYMENTS_TABLE', 'aquachain-payments'))
TECHNICIANS_TABLE = os.environ.get('TECHNICIANS_TABLE_NAME', os.environ.get('ENHANCED_TECHNICIANS_TABLE', 'aquachain-technicians'))
SIMULATIONS_TABLE = os.environ.get('ORDER_SIMULATIONS_TABLE_NAME', os.environ.get('ENHANCED_SIMULATIONS_TABLE', 'aquachain-order-simulations'))
SNS_TOPIC_ARN = os.environ.get('ORDER_EVENTS_TOPIC_ARN')
EVENTBRIDGE_BUS = os.environ.get('ORDERING_EVENT_BUS_NAME', os.environ.get('EVENTBRIDGE_BUS', 'default'))

# Initialize logger
logger = get_logger(__name__, service='enhanced-order-management')


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING_PAYMENT = 'PENDING_PAYMENT'
    PENDING_CONFIRMATION = 'PENDING_CONFIRMATION'
    ORDER_PLACED = 'ORDER_PLACED'
    SHIPPED = 'SHIPPED'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'


class PaymentMethod(Enum):
    """Payment method enumeration"""
    COD = 'COD'
    ONLINE = 'ONLINE'


class OrderManagementService:
    """
    Enhanced Order Management Service with comprehensive functionality
    """
    
    def __init__(self):
        self.orders_table = dynamodb.Table(ORDERS_TABLE)
        self.validator = InputValidator()
        self._register_validation_schemas()
        
        # Valid state transitions
        self.valid_transitions = {
            OrderStatus.PENDING_PAYMENT: [OrderStatus.ORDER_PLACED, OrderStatus.CANCELLED, OrderStatus.FAILED],
            OrderStatus.ORDER_PLACED: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],  # Terminal state
            OrderStatus.CANCELLED: [],  # Terminal state
            OrderStatus.FAILED: []  # Terminal state
        }
    
    def _register_validation_schemas(self):
        """Register validation schemas for order operations"""
        
        # Create order schema
        create_order_schema = {
            'consumerId': ValidationRule(
                field_type=FieldType.UUID,
                required=True
            ),
            'deviceType': ValidationRule(
                field_type=FieldType.STRING,
                required=True,
                min_length=1,
                max_length=100,
                pattern=r'^[a-zA-Z0-9\s\-_]+$',
                sanitize=False
            ),
            'serviceType': ValidationRule(
                field_type=FieldType.STRING,
                required=True,
                min_length=1,
                max_length=100,
                pattern=r'^[a-zA-Z0-9\s\-_]+$',
                sanitize=False
            ),
            'paymentMethod': ValidationRule(
                field_type=FieldType.ENUM,
                required=True,
                enum_values=['COD', 'ONLINE']
            ),
            'deliveryAddress': ValidationRule(
                field_type=FieldType.OBJECT,
                required=True
            ),
            'contactInfo': ValidationRule(
                field_type=FieldType.OBJECT,
                required=True
            ),
            'specialInstructions': ValidationRule(
                field_type=FieldType.STRING,
                required=False,
                max_length=1000,
                sanitize=False
            ),
            'amount': ValidationRule(
                field_type=FieldType.DECIMAL,
                required=False,
                min_value=Decimal('0.01'),
                max_value=Decimal('100000.00')
            )
        }
        
        # Update order status schema
        update_status_schema = {
            'orderId': ValidationRule(
                field_type=FieldType.STRING,
                required=True,
                pattern=r'^ord_\d+$',  # Match format: ord_TIMESTAMP
                min_length=5,
                max_length=50
            ),
            'status': ValidationRule(
                field_type=FieldType.ENUM,
                required=True,
                enum_values=[status.value for status in OrderStatus]
            ),
            'metadata': ValidationRule(
                field_type=FieldType.OBJECT,
                required=False
            ),
            'reason': ValidationRule(
                field_type=FieldType.STRING,
                required=False,
                max_length=500
            )
        }
        
        self.validator.register_schema('create_order', create_order_schema)
        self.validator.register_schema('update_status', update_status_schema)
    
    def create_order(self, request_data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new order with proper validation and state management
        
        Args:
            request_data: Order creation request data
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Created order data
            
        Raises:
            ValidationError: If input validation fails
            BusinessRuleViolationError: If business rules are violated
        """
        logger.start_operation('create_order')
        
        try:
            # Validate input
            validated_data = self.validator.validate_input(
                request_data, 'create_order', correlation_id
            )
            
            # Generate order ID and timestamps
            order_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Determine initial status based on payment method
            # COD orders go directly to ORDER_PLACED since pricing is fixed upfront
            payment_method = PaymentMethod(validated_data['paymentMethod'])
            initial_status = (
                OrderStatus.ORDER_PLACED if payment_method == PaymentMethod.COD
                else OrderStatus.PENDING_PAYMENT
            )
            
            # Create order record
            order_record = {
                'PK': f'ORDER#{order_id}',
                'SK': f'ORDER#{order_id}',
                'GSI1PK': f'CONSUMER#{validated_data["consumerId"]}',
                'GSI1SK': f'ORDER#{timestamp}#{order_id}',
                'GSI2PK': f'STATUS#{initial_status.value}',
                'GSI2SK': f'{timestamp}#{order_id}',
                
                # Order data
                'orderId': order_id,
                'consumerId': validated_data['consumerId'],
                'deviceType': validated_data['deviceType'],
                'serviceType': validated_data['serviceType'],
                'paymentMethod': validated_data['paymentMethod'],
                'status': initial_status.value,
                'deliveryAddress': validated_data['deliveryAddress'],
                'contactInfo': validated_data['contactInfo'],
                'specialInstructions': validated_data.get('specialInstructions'),
                'amount': validated_data.get('amount', Decimal('0')),
                
                # Metadata
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'version': 1,
                
                # Status history
                'statusHistory': [{
                    'status': initial_status.value,
                    'timestamp': timestamp,
                    'message': f'Order created with {payment_method.value} payment method',
                    'metadata': {}
                }],
                
                # TTL for demo orders (30 days)
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
            }
            
            # Store order in DynamoDB
            self.orders_table.put_item(
                Item=order_record,
                ConditionExpression='attribute_not_exists(PK)'
            )
            
            # Publish order created event
            self._publish_order_event('ORDER_CREATED', order_record, correlation_id)
            
            # Convert to response format
            response_order = self._convert_to_response_format(order_record)
            
            logger.end_operation('create_order', success=True, order_id=order_id)
            
            return {
                'success': True,
                'data': response_order,
                'message': 'Order created successfully'
            }
            
        except ValidationError as e:
            logger.error('Order creation validation failed', error=str(e), correlation_id=correlation_id)
            raise
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ConflictError('Order already exists', correlation_id=correlation_id)
            logger.error('DynamoDB error during order creation', error=str(e), correlation_id=correlation_id)
            raise AquaChainError(
                'Failed to create order',
                ErrorCode.DATABASE_ERROR,
                500,
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error('Unexpected error during order creation', error=str(e), correlation_id=correlation_id)
            logger.end_operation('create_order', success=False)
            raise AquaChainError(
                'Internal error during order creation',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def update_order_status(self, request_data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update order status with state transition validation and optimistic locking
        
        Args:
            request_data: Status update request data
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Updated order data
            
        Raises:
            ValidationError: If input validation fails
            ResourceNotFoundError: If order not found
            BusinessRuleViolationError: If state transition is invalid
            ConflictError: If optimistic locking fails
        """
        logger.start_operation('update_order_status')
        
        try:
            # Validate input
            validated_data = self.validator.validate_input(
                request_data, 'update_status', correlation_id
            )
            
            order_id = validated_data['orderId']
            new_status = OrderStatus(validated_data['status'])
            metadata = validated_data.get('metadata', {})
            reason = validated_data.get('reason', '')
            
            # Get current order
            current_order = self._get_order_by_id(order_id)
            if not current_order:
                raise ResourceNotFoundError('Order', order_id, correlation_id)
            
            current_status = OrderStatus(current_order['status'])
            
            # Validate state transition
            if not self._is_valid_transition(current_status, new_status):
                raise BusinessRuleViolationError(
                    f'Invalid state transition from {current_status.value} to {new_status.value}',
                    f'transition_{current_status.value}_to_{new_status.value}',
                    correlation_id
                )
            
            # Prepare update
            timestamp = datetime.now(timezone.utc).isoformat()
            current_version = current_order.get('version', 0)  # Default to 0 if no version exists
            new_version = current_version + 1
            
            # Create status update entry
            status_update = {
                'status': new_status.value,
                'timestamp': timestamp,
                'message': reason or f'Status updated to {new_status.value}',
                'metadata': metadata
            }
            
            # Update status history
            status_history = current_order.get('statusHistory', [])
            status_history.append(status_update)
            
            # Update order with optimistic locking
            try:
                # Build condition expression - check version if it exists, otherwise just check order exists
                if current_version > 0:
                    condition_expression = 'attribute_exists(orderId) AND #version = :current_version'
                else:
                    condition_expression = 'attribute_exists(orderId)'
                
                response = self.orders_table.update_item(
                    Key={
                        'orderId': order_id
                    },
                    UpdateExpression='''
                        SET #status = :new_status,
                            #updatedAt = :timestamp,
                            #version = :new_version,
                            #statusHistory = :status_history
                    ''',
                    ConditionExpression=condition_expression,
                    ExpressionAttributeNames={
                        '#status': 'status',
                        '#updatedAt': 'updatedAt',
                        '#version': 'version',
                        '#statusHistory': 'statusHistory'
                    },
                    ExpressionAttributeValues={
                        ':new_status': new_status.value,
                        ':timestamp': timestamp,
                        ':new_version': new_version,
                        ':current_version': current_version,
                        ':status_history': status_history
                    },
                    ReturnValues='ALL_NEW'
                )
                
                updated_order = response['Attributes']
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    raise ConflictError(
                        'Order was modified by another process. Please retry.',
                        correlation_id=correlation_id
                    )
                raise
            
            # Publish status update event
            self._publish_order_event('ORDER_STATUS_UPDATED', updated_order, correlation_id)
            
            # Convert to response format
            response_order = self._convert_to_response_format(updated_order)
            
            logger.end_operation('update_order_status', success=True, 
                               order_id=order_id, new_status=new_status.value)
            
            return {
                'success': True,
                'data': response_order,
                'message': f'Order status updated to {new_status.value}'
            }
            
        except (ValidationError, ResourceNotFoundError, BusinessRuleViolationError, ConflictError):
            logger.end_operation('update_order_status', success=False)
            raise
        except ClientError as e:
            logger.error('DynamoDB error during status update', error=str(e), correlation_id=correlation_id)
            logger.end_operation('update_order_status', success=False)
            raise AquaChainError(
                'Failed to update order status',
                ErrorCode.DATABASE_ERROR,
                500,
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error('Unexpected error during status update', error=str(e), correlation_id=correlation_id)
            logger.end_operation('update_order_status', success=False)
            raise AquaChainError(
                'Internal error during status update',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def get_order(self, order_id: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a single order by ID
        
        Args:
            order_id: Order ID to retrieve
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Order data
            
        Raises:
            ResourceNotFoundError: If order not found
        """
        logger.start_operation('get_order')
        
        try:
            order = self._get_order_by_id(order_id)
            if not order:
                raise ResourceNotFoundError('Order', order_id, correlation_id)
            
            response_order = self._convert_to_response_format(order)
            
            logger.end_operation('get_order', success=True, order_id=order_id)
            
            return {
                'success': True,
                'data': response_order
            }
            
        except ResourceNotFoundError:
            logger.end_operation('get_order', success=False)
            raise
        except Exception as e:
            logger.error('Error retrieving order', error=str(e), correlation_id=correlation_id)
            logger.end_operation('get_order', success=False)
            raise AquaChainError(
                'Failed to retrieve order',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def get_orders_by_consumer(self, consumer_id: str, limit: int = 50, 
                             last_evaluated_key: Optional[str] = None,
                             correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve orders for a specific consumer with pagination
        
        Args:
            consumer_id: Consumer ID to filter by
            limit: Maximum number of orders to return
            last_evaluated_key: Pagination token
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            List of orders with pagination info
        """
        logger.start_operation('get_orders_by_consumer')
        
        try:
            query_params = {
                'IndexName': 'GSI1',
                'KeyConditionExpression': 'GSI1PK = :consumer_pk',
                'ExpressionAttributeValues': {
                    ':consumer_pk': f'CONSUMER#{consumer_id}'
                },
                'ScanIndexForward': False,  # Most recent first
                'Limit': min(limit, 100)  # Cap at 100
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = json.loads(last_evaluated_key)
            
            response = self.orders_table.query(**query_params)
            
            orders = [self._convert_to_response_format(item) for item in response.get('Items', [])]
            
            result = {
                'success': True,
                'data': orders,
                'count': len(orders)
            }
            
            if 'LastEvaluatedKey' in response:
                result['lastEvaluatedKey'] = json.dumps(response['LastEvaluatedKey'])
            
            logger.end_operation('get_orders_by_consumer', success=True, 
                               consumer_id=consumer_id, count=len(orders))
            
            return result
            
        except Exception as e:
            logger.error('Error retrieving consumer orders', error=str(e), correlation_id=correlation_id)
            logger.end_operation('get_orders_by_consumer', success=False)
            raise AquaChainError(
                'Failed to retrieve consumer orders',
                ErrorCode.INTERNAL_ERROR,
                500,
                correlation_id=correlation_id
            )
    
    def cancel_order(self, order_id: str, reason: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an order with reason
        
        Args:
            order_id: Order ID to cancel
            reason: Cancellation reason
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Cancelled order data
        """
        return self.update_order_status({
            'orderId': order_id,
            'status': OrderStatus.CANCELLED.value,
            'reason': reason
        }, correlation_id)
    
    def _get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID from DynamoDB"""
        try:
            logger.info(f'Querying DynamoDB for order', order_id=order_id, table=ORDERS_TABLE)
            response = self.orders_table.get_item(
                Key={
                    'orderId': order_id
                }
            )
            item = response.get('Item')
            logger.info(f'DynamoDB query result', order_id=order_id, found=item is not None)
            return item
        except Exception as e:
            logger.error(f'Error querying DynamoDB', order_id=order_id, error=str(e))
            return None
    
    def _is_valid_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Check if status transition is valid"""
        return new_status in self.valid_transitions.get(current_status, [])
    
    def _convert_to_response_format(self, order_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB record to API response format"""
        return {
            'id': order_record['orderId'],
            'consumerId': order_record['consumerId'],
            'deviceType': order_record['deviceType'],
            'serviceType': order_record['serviceType'],
            'paymentMethod': order_record['paymentMethod'],
            'status': order_record['status'],
            'amount': order_record.get('amount'),
            'deliveryAddress': order_record['deliveryAddress'],
            'contactInfo': order_record['contactInfo'],
            'assignedTechnician': order_record.get('assignedTechnician'),
            'paymentId': order_record.get('paymentId'),
            'specialInstructions': order_record.get('specialInstructions'),
            'createdAt': order_record['createdAt'],
            'updatedAt': order_record['updatedAt'],
            'statusHistory': order_record.get('statusHistory', [])
        }
    
    def _publish_order_event(self, event_type: str, order_data: Dict[str, Any], 
                           correlation_id: Optional[str] = None):
        """Publish order event to SNS and EventBridge"""
        try:
            # Convert Decimal values to float for JSON serialization
            serializable_data = {}
            for key, value in order_data.items():
                if isinstance(value, Decimal):
                    serializable_data[key] = float(value)
                else:
                    serializable_data[key] = value
            
            event_payload = {
                'eventType': event_type,
                'orderId': serializable_data['orderId'],
                'consumerId': serializable_data['consumerId'],
                'status': serializable_data['status'],
                'paymentMethod': serializable_data['paymentMethod'],
                'amount': serializable_data.get('amount'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlationId': correlation_id
            }
            
            # Publish to SNS for real-time notifications
            if SNS_TOPIC_ARN:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=json.dumps(event_payload),
                    Subject=f'Order Event: {event_type}'
                )
            
            # Publish to EventBridge for workflow automation
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.orders',
                        'DetailType': event_type,
                        'Detail': json.dumps(event_payload),
                        'EventBusName': EVENTBRIDGE_BUS
                    }
                ]
            )
            
        except Exception as e:
            logger.warning('Failed to publish order event', error=str(e), event_type=event_type)


# Initialize service
order_service = OrderManagementService()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for order management operations
    
    Supported operations:
    - POST /orders - Create order
    - PUT /orders/{orderId}/status - Update order status
    - GET /orders/{orderId} - Get order by ID
    - GET /orders?consumerId={consumerId} - Get orders by consumer
    - PUT /orders/{orderId}/cancel - Cancel order
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
        
        # Normalize path (remove /api prefix if present)
        normalized_path = path.replace('/api', '') if path.startswith('/api') else path
        
        # Route to appropriate operation
        if http_method == 'POST' and normalized_path == '/orders':
            # Create order
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(order_service.create_order(request_data, correlation_id))
            }
        
        elif http_method == 'PUT' and path_parameters.get('orderId') and 'status' in normalized_path:
            # Update order status
            request_data['orderId'] = path_parameters['orderId']
            logger.info('Updating order status', order_id=path_parameters['orderId'], 
                       new_status=request_data.get('status'), correlation_id=correlation_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(order_service.update_order_status(request_data, correlation_id))
            }
        
        elif http_method == 'GET' and path_parameters.get('orderId'):
            # Get order by ID
            order_id = path_parameters['orderId']
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(order_service.get_order(order_id, correlation_id))
            }
        
        elif http_method == 'GET' and normalized_path == '/orders' and query_parameters.get('consumerId'):
            # Get orders by consumer
            consumer_id = query_parameters['consumerId']
            limit = int(query_parameters.get('limit', 50))
            last_evaluated_key = query_parameters.get('lastEvaluatedKey')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(order_service.get_orders_by_consumer(
                    consumer_id, limit, last_evaluated_key, correlation_id
                ))
            }
        
        elif http_method == 'PUT' and path_parameters.get('orderId') and 'cancel' in normalized_path:
            # Cancel order
            order_id = path_parameters['orderId']
            reason = request_data.get('reason', 'Order cancelled by user')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'X-Correlation-ID': correlation_id
                },
                'body': json.dumps(order_service.cancel_order(order_id, reason, correlation_id))
            }
        
        else:
            # Unsupported operation
            raise ValidationError(f'Unsupported operation: {http_method} {path}')
    
    except AquaChainError as e:
        logger.error('AquaChain error in order management', error=str(e), correlation_id=correlation_id)
        return create_lambda_error_response(e, correlation_id, 'enhanced-order-management')
    
    except Exception as e:
        logger.error('Unexpected error in order management', error=str(e), correlation_id=correlation_id)
        error = AquaChainError(
            'Internal server error',
            ErrorCode.INTERNAL_ERROR,
            500,
            correlation_id=correlation_id
        )
        return create_lambda_error_response(error, correlation_id, 'enhanced-order-management')