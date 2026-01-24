"""
Lambda function to create shipment and integrate with courier API

This Lambda function handles shipment creation by:
1. Validating request body and required fields
2. Fetching order details from DeviceOrders table
3. Calling courier API to create shipment and get tracking number
4. Creating shipment record in Shipments table atomically with order update
5. Sending notifications to stakeholders

Requirements: 1.1, 1.2, 1.3, 1.5
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import time
from botocore.exceptions import ClientError

from structured_logger import get_logger
from errors import ValidationError, ResourceNotFoundError, DatabaseError
from cloudwatch_metrics import emit_shipment_created, emit_lambda_error
from audit_trail import (
    create_timeline_entry,
    create_admin_action_log,
    calculate_ttl_timestamp
)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
sns = boto3.client('sns')

# Environment variables
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
COURIER_API_KEY = os.environ.get('COURIER_API_KEY', '')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

# Initialize logger
logger = get_logger(__name__, service='create-shipment')


def handler(event, context):
    """
    Create shipment record and register with courier service
    
    Input:
    {
      "order_id": "ord_xxx",
      "courier_name": "Delhivery",
      "service_type": "Surface",
      "destination": {
        "address": "123 Main St, Bangalore",
        "pincode": "560001",
        "contact_name": "John Doe",
        "contact_phone": "+919876543210"
      },
      "package_details": {
        "weight": "0.5kg",
        "declared_value": 5000,
        "insurance": true
      }
    }
    
    Output:
    {
      "success": true,
      "shipment_id": "ship_xxx",
      "tracking_number": "DELHUB123456789",
      "estimated_delivery": "2025-12-31T18:00:00Z"
    }
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    try:
        # Parse request body
        body = parse_request_body(event)
        
        # Validate required fields
        validate_request_body(body)
        
        order_id = body['order_id']
        
        logger.info(
            "Starting shipment creation",
            request_id=request_id,
            order_id=order_id,
            courier_name=body['courier_name']
        )
        
        # Fetch order details from DeviceOrders table
        order = fetch_order_details(order_id)
        
        # Generate unique shipment_id using timestamp
        shipment_id = generate_shipment_id()
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Get user ID from request context
        user_id = extract_user_id(event)
        
        logger.info(
            "Calling courier API",
            request_id=request_id,
            shipment_id=shipment_id,
            order_id=order_id
        )
        
        # Call courier API to create shipment and get tracking number
        courier_response = create_courier_shipment(
            courier_name=body['courier_name'],
            destination=body['destination'],
            package=body['package_details'],
            order_id=order_id
        )
        
        tracking_number = courier_response['tracking_number']
        estimated_delivery = courier_response['estimated_delivery']
        
        logger.info(
            "Courier shipment created",
            request_id=request_id,
            shipment_id=shipment_id,
            tracking_number=tracking_number
        )
        
        # Create shipment record
        shipment_item = build_shipment_item(
            shipment_id=shipment_id,
            order_id=order_id,
            order=order,
            body=body,
            tracking_number=tracking_number,
            estimated_delivery=estimated_delivery,
            timestamp=timestamp,
            user_id=user_id
        )
        
        # Atomic transaction: Create shipment + Update order
        execute_atomic_transaction(
            shipment_item=shipment_item,
            order_id=order_id,
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            timestamp=timestamp
        )
        
        logger.info(
            "Shipment created successfully",
            request_id=request_id,
            shipment_id=shipment_id,
            order_id=order_id,
            tracking_number=tracking_number
        )
        
        # Emit CloudWatch metric for shipment creation
        emit_shipment_created(shipment_id, order_id, body['courier_name'])
        
        # Send notifications to stakeholders
        if SNS_TOPIC_ARN:
            notify_stakeholders(order, shipment_item, 'shipment_created')
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'shipment_id': shipment_id,
                'tracking_number': tracking_number,
                'estimated_delivery': estimated_delivery
            })
        }
        
    except ValidationError as e:
        logger.warning(
            f"Validation error: {e.message}",
            request_id=request_id,
            error_code=e.error_code,
            details=e.details
        )
        emit_lambda_error('create_shipment', 'ValidationError')
        return error_response(400, e.message)
        
    except ResourceNotFoundError as e:
        logger.warning(
            f"Resource not found: {e.message}",
            request_id=request_id,
            error_code=e.error_code
        )
        emit_lambda_error('create_shipment', 'ResourceNotFoundError')
        return error_response(404, e.message)
        
    except DatabaseError as e:
        logger.error(
            f"Database error: {e.message}",
            request_id=request_id,
            error_code=e.error_code,
            details=e.details
        )
        emit_lambda_error('create_shipment', 'DatabaseError')
        return error_response(500, 'Failed to create shipment. Please try again.')
        
    except Exception as e:
        logger.error(
            f"Unexpected error creating shipment: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        emit_lambda_error('create_shipment', type(e).__name__)
        return error_response(500, f'Internal server error: {str(e)}')


def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse request body from API Gateway event
    
    Args:
        event: Lambda event object
        
    Returns:
        Parsed request body as dictionary
        
    Raises:
        ValidationError: If body is missing or invalid JSON
    """
    if 'body' in event:
        if isinstance(event['body'], str):
            try:
                return json.loads(event['body'])
            except json.JSONDecodeError as e:
                raise ValidationError(
                    message='Invalid JSON in request body',
                    error_code='INVALID_JSON',
                    details={'error': str(e)}
                )
        else:
            return event['body']
    else:
        # Direct invocation (testing)
        return event


def validate_request_body(body: Dict[str, Any]) -> None:
    """
    Validate required fields in request body
    
    Args:
        body: Request body dictionary
        
    Raises:
        ValidationError: If required fields are missing or invalid
    """
    required_fields = ['order_id', 'courier_name', 'destination', 'package_details']
    missing_fields = [field for field in required_fields if field not in body]
    
    if missing_fields:
        raise ValidationError(
            message=f'Missing required fields: {", ".join(missing_fields)}',
            error_code='MISSING_REQUIRED_FIELDS',
            details={'missing_fields': missing_fields}
        )
    
    # Validate destination fields
    destination = body['destination']
    required_dest_fields = ['address', 'pincode', 'contact_name', 'contact_phone']
    missing_dest_fields = [field for field in required_dest_fields if field not in destination]
    
    if missing_dest_fields:
        raise ValidationError(
            message=f'Missing required destination fields: {", ".join(missing_dest_fields)}',
            error_code='MISSING_DESTINATION_FIELDS',
            details={'missing_fields': missing_dest_fields}
        )
    
    # Validate package details
    package = body['package_details']
    if 'weight' not in package and 'declared_value' not in package:
        raise ValidationError(
            message='Package details must include weight or declared_value',
            error_code='INVALID_PACKAGE_DETAILS'
        )


def fetch_order_details(order_id: str) -> Dict[str, Any]:
    """
    Fetch order details from DeviceOrders table
    
    Args:
        order_id: Order ID to fetch
        
    Returns:
        Order item from DynamoDB
        
    Raises:
        ResourceNotFoundError: If order not found
        DatabaseError: If DynamoDB query fails
    """
    try:
        orders_table = dynamodb.Table(ORDERS_TABLE)
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            raise ResourceNotFoundError(
                message=f'Order not found: {order_id}',
                error_code='ORDER_NOT_FOUND',
                details={'order_id': order_id}
            )
        
        return response['Item']
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        raise DatabaseError(
            message=f'Failed to fetch order details: {str(e)}',
            error_code='DATABASE_QUERY_FAILED',
            details={'order_id': order_id, 'error': str(e)}
        )


def generate_shipment_id() -> str:
    """
    Generate unique shipment_id using timestamp
    
    Returns:
        Shipment ID in format: ship_{timestamp_ms}
    """
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    return f"ship_{timestamp_ms}"


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract user ID from request context
    
    Args:
        event: Lambda event object
        
    Returns:
        User ID or 'system' if not found
    """
    try:
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub', 'system')
    except Exception:
        return 'system'


def build_shipment_item(
    shipment_id: str,
    order_id: str,
    order: Dict[str, Any],
    body: Dict[str, Any],
    tracking_number: str,
    estimated_delivery: str,
    timestamp: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Build shipment item for DynamoDB
    
    Args:
        shipment_id: Generated shipment ID
        order_id: Order ID
        order: Order details from DeviceOrders table
        body: Request body
        tracking_number: Tracking number from courier
        estimated_delivery: Estimated delivery date
        timestamp: Current timestamp
        user_id: User ID creating the shipment
        
    Returns:
        Shipment item dictionary
    """
    # Create initial timeline entry with proper audit trail
    initial_timeline_entry = create_timeline_entry(
        status='shipment_created',
        timestamp=timestamp,
        location=body.get('origin', {}).get('address', 'Warehouse'),
        description='Shipment created and handed to courier'
    )
    
    # Create admin action log for shipment creation
    admin_action = create_admin_action_log(
        action_type='SHIPMENT_CREATED',
        user_id=user_id,
        details={
            'courier_name': body['courier_name'],
            'tracking_number': tracking_number,
            'destination': body['destination'].get('address', 'N/A')
        }
    )
    
    # Calculate TTL for 2-year retention
    ttl_timestamp = calculate_ttl_timestamp(years=2)
    
    return {
        'shipment_id': shipment_id,
        'order_id': order_id,
        'device_id': order.get('device_id', order.get('deviceId', '')),
        'tracking_number': tracking_number,
        'courier_name': body['courier_name'],
        'courier_service_type': body.get('service_type', 'Surface'),
        'internal_status': 'shipment_created',
        'external_status': 'shipped',
        'destination': body['destination'],
        'estimated_delivery': estimated_delivery,
        'timeline': [initial_timeline_entry],
        'webhook_events': [],
        'admin_actions': [admin_action],
        'retry_config': {
            'max_retries': 3,
            'retry_count': 0,
            'last_retry_at': None
        },
        'metadata': body['package_details'],
        'created_at': timestamp,
        'updated_at': timestamp,
        'delivered_at': None,
        'failed_at': None,
        'created_by': user_id,
        'audit_ttl': ttl_timestamp
    }


def execute_atomic_transaction(
    shipment_item: Dict[str, Any],
    order_id: str,
    shipment_id: str,
    tracking_number: str,
    timestamp: str
) -> None:
    """
    Execute atomic transaction to create shipment and update order
    
    Uses DynamoDB transact_write_items to ensure atomicity:
    - Creates Shipments table record with initial status "shipment_created"
    - Updates DeviceOrders table with shipment_id and tracking_number
    - Ensures transaction rolls back completely on any failure
    
    Graceful degradation:
    - If Shipments table is unavailable, allows order to proceed with manual tracking
    - Logs error and alerts DevOps
    - Order status is still updated to "shipped"
    
    Args:
        shipment_item: Shipment item to create
        order_id: Order ID to update
        shipment_id: Shipment ID
        tracking_number: Tracking number
        timestamp: Current timestamp
        
    Raises:
        DatabaseError: If transaction fails
        
    Requirements: 8.4
    """
    try:
        logger.info(
            "Executing atomic transaction",
            shipment_id=shipment_id,
            order_id=order_id
        )
        
        # Convert shipment item to DynamoDB format
        shipment_item_dynamodb = convert_to_dynamodb_format(shipment_item)
        
        # Execute atomic transaction
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': SHIPMENTS_TABLE,
                        'Item': shipment_item_dynamodb,
                        'ConditionExpression': 'attribute_not_exists(shipment_id)'
                    }
                },
                {
                    'Update': {
                        'TableName': ORDERS_TABLE,
                        'Key': {'orderId': {'S': order_id}},
                        'UpdateExpression': 'SET #status = :shipped, tracking_number = :tracking, shipment_id = :shipment_id, shipped_at = :time',
                        'ExpressionAttributeNames': {'#status': 'status'},
                        'ExpressionAttributeValues': {
                            ':shipped': {'S': 'shipped'},
                            ':tracking': {'S': tracking_number},
                            ':shipment_id': {'S': shipment_id},
                            ':time': {'S': timestamp},
                            ':approved': {'S': 'approved'}
                        },
                        'ConditionExpression': 'attribute_exists(orderId) AND #status = :approved'
                    }
                }
            ]
        )
        
        logger.info(
            "Atomic transaction completed successfully",
            shipment_id=shipment_id,
            order_id=order_id
        )
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Check if it's a TransactionCanceledException (conditional check failed)
        if error_code == 'TransactionCanceledException':
            # Parse cancellation reasons to determine the specific failure
            cancellation_reasons = e.response.get('CancellationReasons', [])
            
            # Check if shipment already exists (duplicate attempt)
            if any(reason and reason.get('Code') == 'ConditionalCheckFailed' 
                   for reason in cancellation_reasons):
                logger.warning(
                    "Shipment creation failed - duplicate shipment or order not in approved state",
                    shipment_id=shipment_id,
                    order_id=order_id,
                    cancellation_reasons=cancellation_reasons
                )
                
                # Check which condition failed
                # If first transaction item failed: shipment already exists
                # If second transaction item failed: order not found or not approved
                if cancellation_reasons[0] and cancellation_reasons[0].get('Code') == 'ConditionalCheckFailed':
                    raise DatabaseError(
                        message='Shipment already exists for this order',
                        error_code='SHIPMENT_ALREADY_EXISTS',
                        details={
                            'order_id': order_id,
                            'shipment_id': shipment_id,
                            'reason': 'A shipment has already been created for this order'
                        }
                    )
                elif cancellation_reasons[1] and cancellation_reasons[1].get('Code') == 'ConditionalCheckFailed':
                    raise DatabaseError(
                        message='Order not found or not in approved state',
                        error_code='ORDER_NOT_FOUND',
                        details={
                            'order_id': order_id,
                            'reason': 'Order must exist and be in approved state before creating shipment'
                        }
                    )
            
            # Unknown transaction cancellation reason
            logger.error(
                "Transaction cancelled for unknown reason",
                shipment_id=shipment_id,
                order_id=order_id,
                cancellation_reasons=cancellation_reasons
            )
            raise DatabaseError(
                message='Transaction cancelled',
                error_code='TRANSACTION_CANCELLED',
                details={
                    'order_id': order_id,
                    'shipment_id': shipment_id,
                    'cancellation_reasons': cancellation_reasons
                }
            )
        
        # Check if it's a ResourceNotFoundException (Shipments table doesn't exist)
        elif error_code == 'ResourceNotFoundException':
            # Shipments table doesn't exist - graceful degradation
            logger.error(
                "Shipments table not found - falling back to manual tracking",
                shipment_id=shipment_id,
                order_id=order_id,
                error=str(e)
            )
            
            # Alert DevOps about missing table
            alert_devops_shipments_table_unavailable(order_id, shipment_id, tracking_number)
            
            # Update order status to "shipped" without shipment tracking
            # This allows the order to proceed with manual tracking
            try:
                fallback_update_order_status(order_id, tracking_number, timestamp)
                logger.info(
                    "Order updated successfully with manual tracking fallback",
                    order_id=order_id,
                    tracking_number=tracking_number
                )
            except Exception as fallback_error:
                logger.error(
                    f"Fallback order update failed: {str(fallback_error)}",
                    order_id=order_id
                )
                raise DatabaseError(
                    message='Failed to update order status',
                    error_code='FALLBACK_UPDATE_FAILED',
                    details={'order_id': order_id, 'error': str(fallback_error)}
                )
        else:
            # Other ClientError - re-raise
            raise
        
    except dynamodb_client.exceptions.TransactionCanceledException as e:
        # Transaction was cancelled due to condition check failure
        cancellation_reasons = e.response.get('CancellationReasons', [])
        
        logger.error(
            "Transaction cancelled",
            shipment_id=shipment_id,
            order_id=order_id,
            reasons=cancellation_reasons
        )
        
        # Check which condition failed by examining the cancellation reasons
        # Reasons are in order: [Shipments Put, DeviceOrders Update]
        shipment_failed = False
        order_failed = False
        
        if len(cancellation_reasons) >= 1:
            shipment_reason = cancellation_reasons[0]
            if shipment_reason.get('Code') == 'ConditionalCheckFailed':
                shipment_failed = True
        
        if len(cancellation_reasons) >= 2:
            order_reason = cancellation_reasons[1]
            if order_reason.get('Code') == 'ConditionalCheckFailed':
                order_failed = True
        
        # Prioritize shipment already exists error (more specific)
        if shipment_failed:
            raise DatabaseError(
                message=f'Shipment already exists: {shipment_id}',
                error_code='SHIPMENT_ALREADY_EXISTS',
                details={'shipment_id': shipment_id}
            )
        
        # Check if order doesn't exist or status is not 'approved'
        if order_failed:
            raise DatabaseError(
                message=f'Order not found or already shipped: {order_id}',
                error_code='ORDER_NOT_FOUND',
                details={'order_id': order_id}
            )
        
        raise DatabaseError(
            message='Transaction failed due to condition check',
            error_code='TRANSACTION_CANCELLED',
            details={'reasons': cancellation_reasons}
        )
        
    except Exception as e:
        logger.error(
            f"Transaction failed: {str(e)}",
            shipment_id=shipment_id,
            order_id=order_id,
            error_type=type(e).__name__
        )
        
        raise DatabaseError(
            message=f'Failed to create shipment: {str(e)}',
            error_code='TRANSACTION_FAILED',
            details={'shipment_id': shipment_id, 'order_id': order_id}
        )


def convert_to_dynamodb_format(item: Dict) -> Dict:
    """
    Convert Python dict to DynamoDB format
    
    Args:
        item: Python dictionary
        
    Returns:
        DynamoDB formatted dictionary
    """
    def convert_value(val):
        if isinstance(val, str):
            return {'S': val}
        elif isinstance(val, bool):
            # Must check bool before int/float since bool is subclass of int
            return {'BOOL': val}
        elif isinstance(val, int):
            return {'N': str(val)}
        elif isinstance(val, float):
            return {'N': str(val)}
        elif isinstance(val, dict):
            return {'M': {k: convert_value(v) for k, v in val.items()}}
        elif isinstance(val, list):
            return {'L': [convert_value(v) for v in val]}
        elif val is None:
            return {'NULL': True}
        else:
            return {'S': str(val)}
    
    return {k: convert_value(v) for k, v in item.items()}


def create_courier_shipment(courier_name: str, destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Integrate with courier API
    
    Routes to appropriate courier API based on courier_name.
    Handles unsupported couriers with error message.
    
    Args:
        courier_name: Name of courier service (Delhivery, BlueDart, DTDC)
        destination: Destination address details
        package: Package details
        order_id: Order ID
        
    Returns:
        Dictionary with tracking_number and estimated_delivery
        
    Raises:
        ValidationError: If courier is not supported
        
    Requirements: 7.3
    """
    courier_lower = courier_name.lower()
    
    # Route to appropriate courier API
    if courier_lower == 'delhivery':
        return create_delhivery_shipment(destination, package, order_id)
    elif courier_lower == 'bluedart':
        return create_bluedart_shipment(destination, package, order_id)
    elif courier_lower == 'dtdc':
        return create_dtdc_shipment(destination, package, order_id)
    else:
        # Unsupported courier - raise error
        supported_couriers = ['Delhivery', 'BlueDart', 'DTDC']
        raise ValidationError(
            message=f'Unsupported courier: {courier_name}. Supported couriers: {", ".join(supported_couriers)}',
            error_code='UNSUPPORTED_COURIER',
            details={'courier_name': courier_name, 'supported_couriers': supported_couriers}
        )


def create_delhivery_shipment(destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Create shipment via Delhivery API with retry logic
    
    Implements exponential backoff retry strategy for API failures.
    Retries up to 5 times with delays: 1s, 2s, 4s, 8s, 16s
    
    Args:
        destination: Destination address details
        package: Package details (weight, declared_value, insurance)
        order_id: Order ID for reference
        
    Returns:
        Dictionary with tracking_number and estimated_delivery
        
    Raises:
        Exception: If API call fails after all retries
    """
    if not COURIER_API_KEY:
        # Return mock for development/testing
        logger.warning("No COURIER_API_KEY configured, returning mock tracking number")
        return {
            'tracking_number': f"DELHUB{int(datetime.now().timestamp())}",
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat() + 'Z'
        }
    
    # Prepare API request payload
    payload = {
        'shipments': [{
            'name': destination['contact_name'],
            'add': destination['address'],
            'pin': destination['pincode'],
            'phone': destination['contact_phone'],
            'payment_mode': 'Prepaid',
            'return_name': 'AquaChain Warehouse',
            'return_add': 'Mumbai',
            'return_pin': '400001',
            'return_phone': '+919999999999',
            'weight': package.get('weight', '0.5'),
            'seller_name': 'AquaChain',
            'products_desc': 'IoT Water Quality Monitor',
            'hsn_code': '85176290',
            'cod_amount': '0',
            'order': f"AQUA{order_id}",
            'total_amount': str(package.get('declared_value', 5000))
        }],
        'pickup_location': {
            'name': 'Mumbai Warehouse'
        }
    }
    
    # Retry configuration
    max_retries = 5
    base_delay = 1  # seconds
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Calling Delhivery API (attempt {attempt + 1}/{max_retries})",
                order_id=order_id
            )
            
            response = requests.post(
                'https://track.delhivery.com/api/cmu/create.json',
                headers={
                    'Authorization': f'Token {COURIER_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract tracking number from response
            if 'packages' in data and len(data['packages']) > 0:
                tracking_number = data['packages'][0]['waybill']
                
                logger.info(
                    "Delhivery shipment created successfully",
                    order_id=order_id,
                    tracking_number=tracking_number,
                    attempt=attempt + 1
                )
                
                return {
                    'tracking_number': tracking_number,
                    'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat() + 'Z'
                }
            else:
                raise Exception(f"Invalid response format from Delhivery API: {data}")
        
        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(
                f"Delhivery API timeout (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e)
            )
            
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else None
            
            logger.warning(
                f"Delhivery API HTTP error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                status_code=status_code,
                error=str(e)
            )
            
            # Don't retry on 4xx errors (client errors)
            if status_code and 400 <= status_code < 500:
                raise Exception(f"Delhivery API client error: {str(e)}")
        
        except Exception as e:
            last_error = e
            logger.warning(
                f"Delhivery API error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__
            )
        
        # Calculate exponential backoff delay
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            logger.info(
                f"Retrying Delhivery API call in {delay} seconds",
                order_id=order_id,
                attempt=attempt + 1
            )
            time.sleep(delay)
    
    # All retries exhausted
    error_msg = f"Delhivery API failed after {max_retries} attempts: {str(last_error)}"
    logger.error(
        error_msg,
        order_id=order_id
    )
    raise Exception(error_msg)


def create_bluedart_shipment(destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Create shipment via BlueDart API with retry logic
    
    Implements exponential backoff retry strategy for API failures.
    Retries up to 5 times with delays: 1s, 2s, 4s, 8s, 16s
    
    Args:
        destination: Destination address details
        package: Package details (weight, declared_value, insurance)
        order_id: Order ID for reference
        
    Returns:
        Dictionary with tracking_number and estimated_delivery
        
    Raises:
        Exception: If API call fails after all retries
        
    Requirements: 7.1, 7.2, 7.3
    """
    bluedart_api_key = os.environ.get('BLUEDART_API_KEY', '')
    
    if not bluedart_api_key:
        # Return mock for development/testing
        logger.warning("No BLUEDART_API_KEY configured, returning mock tracking number")
        return {
            'tracking_number': f"BD{int(datetime.now().timestamp())}",
            'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat() + 'Z'
        }
    
    # Prepare API request payload (BlueDart format)
    payload = {
        'consignee': {
            'name': destination['contact_name'],
            'address': destination['address'],
            'pincode': destination['pincode'],
            'phone': destination['contact_phone']
        },
        'shipper': {
            'name': 'AquaChain',
            'address': 'Mumbai Warehouse',
            'pincode': '400001',
            'phone': '+919999999999'
        },
        'shipment': {
            'product_code': 'D',  # Domestic
            'service_type': 'Express',
            'payment_mode': 'Prepaid',
            'weight': package.get('weight', '0.5'),
            'declared_value': str(package.get('declared_value', 5000)),
            'description': 'IoT Water Quality Monitor',
            'reference_number': f"AQUA{order_id}"
        }
    }
    
    # Retry configuration
    max_retries = 5
    base_delay = 1  # seconds
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Calling BlueDart API (attempt {attempt + 1}/{max_retries})",
                order_id=order_id
            )
            
            response = requests.post(
                'https://api.bluedart.com/api/v1/shipments',
                headers={
                    'Authorization': f'Bearer {bluedart_api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract tracking number from response
            if 'awb_number' in data:
                tracking_number = data['awb_number']
                
                logger.info(
                    "BlueDart shipment created successfully",
                    order_id=order_id,
                    tracking_number=tracking_number,
                    attempt=attempt + 1
                )
                
                return {
                    'tracking_number': tracking_number,
                    'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat() + 'Z'
                }
            else:
                raise Exception(f"Invalid response format from BlueDart API: {data}")
        
        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(
                f"BlueDart API timeout (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e)
            )
            
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else None
            
            logger.warning(
                f"BlueDart API HTTP error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                status_code=status_code,
                error=str(e)
            )
            
            # Don't retry on 4xx errors (client errors)
            if status_code and 400 <= status_code < 500:
                raise Exception(f"BlueDart API client error: {str(e)}")
        
        except Exception as e:
            last_error = e
            logger.warning(
                f"BlueDart API error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__
            )
        
        # Calculate exponential backoff delay
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            logger.info(
                f"Retrying BlueDart API call in {delay} seconds",
                order_id=order_id,
                attempt=attempt + 1
            )
            time.sleep(delay)
    
    # All retries exhausted
    error_msg = f"BlueDart API failed after {max_retries} attempts: {str(last_error)}"
    logger.error(
        error_msg,
        order_id=order_id
    )
    raise Exception(error_msg)


def create_dtdc_shipment(destination: Dict, package: Dict, order_id: str) -> Dict[str, str]:
    """
    Create shipment via DTDC API with retry logic
    
    Implements exponential backoff retry strategy for API failures.
    Retries up to 5 times with delays: 1s, 2s, 4s, 8s, 16s
    
    Args:
        destination: Destination address details
        package: Package details (weight, declared_value, insurance)
        order_id: Order ID for reference
        
    Returns:
        Dictionary with tracking_number and estimated_delivery
        
    Raises:
        Exception: If API call fails after all retries
        
    Requirements: 7.1, 7.2, 7.3
    """
    dtdc_api_key = os.environ.get('DTDC_API_KEY', '')
    
    if not dtdc_api_key:
        # Return mock for development/testing
        logger.warning("No DTDC_API_KEY configured, returning mock tracking number")
        return {
            'tracking_number': f"DTDC{int(datetime.now().timestamp())}",
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat() + 'Z'
        }
    
    # Prepare API request payload (DTDC format)
    payload = {
        'consignee_details': {
            'name': destination['contact_name'],
            'address': destination['address'],
            'pincode': destination['pincode'],
            'phone': destination['contact_phone']
        },
        'shipper_details': {
            'name': 'AquaChain',
            'address': 'Mumbai Warehouse',
            'pincode': '400001',
            'phone': '+919999999999'
        },
        'shipment_details': {
            'service_type': 'Express',
            'payment_mode': 'Prepaid',
            'weight': package.get('weight', '0.5'),
            'declared_value': str(package.get('declared_value', 5000)),
            'product_description': 'IoT Water Quality Monitor',
            'customer_reference': f"AQUA{order_id}"
        }
    }
    
    # Retry configuration
    max_retries = 5
    base_delay = 1  # seconds
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Calling DTDC API (attempt {attempt + 1}/{max_retries})",
                order_id=order_id
            )
            
            response = requests.post(
                'https://api.dtdc.com/api/shipment/create',
                headers={
                    'Authorization': f'Bearer {dtdc_api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract tracking number from response
            if 'reference_number' in data:
                tracking_number = data['reference_number']
                
                logger.info(
                    "DTDC shipment created successfully",
                    order_id=order_id,
                    tracking_number=tracking_number,
                    attempt=attempt + 1
                )
                
                return {
                    'tracking_number': tracking_number,
                    'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat() + 'Z'
                }
            else:
                raise Exception(f"Invalid response format from DTDC API: {data}")
        
        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(
                f"DTDC API timeout (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e)
            )
            
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else None
            
            logger.warning(
                f"DTDC API HTTP error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                status_code=status_code,
                error=str(e)
            )
            
            # Don't retry on 4xx errors (client errors)
            if status_code and 400 <= status_code < 500:
                raise Exception(f"DTDC API client error: {str(e)}")
        
        except Exception as e:
            last_error = e
            logger.warning(
                f"DTDC API error (attempt {attempt + 1}/{max_retries})",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__
            )
        
        # Calculate exponential backoff delay
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            logger.info(
                f"Retrying DTDC API call in {delay} seconds",
                order_id=order_id,
                attempt=attempt + 1
            )
            time.sleep(delay)
    
    # All retries exhausted
    error_msg = f"DTDC API failed after {max_retries} attempts: {str(last_error)}"
    logger.error(
        error_msg,
        order_id=order_id
    )
    raise Exception(error_msg)


def notify_stakeholders(order: Dict, shipment: Dict, event_type: str):
    """
    Send notifications to stakeholders via SNS
    
    Sends notifications to:
    - Consumer: With tracking info and estimated delivery date
    - Admin: Confirming shipment creation
    
    Args:
        order: Order details from DeviceOrders table
        shipment: Shipment details
        event_type: Type of event (e.g., 'shipment_created')
    """
    try:
        # Build notification message
        message = {
            'eventType': event_type,
            'shipment_id': shipment['shipment_id'],
            'order_id': shipment['order_id'],
            'tracking_number': shipment['tracking_number'],
            'estimated_delivery': shipment['estimated_delivery'],
            'courier_name': shipment['courier_name'],
            'consumer_email': order.get('consumerEmail', order.get('consumer_email')),
            'consumer_name': order.get('consumerName', order.get('consumer_name')),
            'device_id': shipment.get('device_id'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add destination info for consumer notification
        if 'destination' in shipment:
            message['destination'] = {
                'address': shipment['destination'].get('address'),
                'pincode': shipment['destination'].get('pincode'),
                'contact_name': shipment['destination'].get('contact_name')
            }
        
        logger.info(
            "Sending shipment creation notification",
            shipment_id=shipment['shipment_id'],
            order_id=shipment['order_id'],
            event_type=event_type
        )
        
        # Publish to SNS topic
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f'Shipment Created: {shipment["tracking_number"]}',
            MessageAttributes={
                'event_type': {
                    'DataType': 'String',
                    'StringValue': event_type
                },
                'shipment_id': {
                    'DataType': 'String',
                    'StringValue': shipment['shipment_id']
                },
                'order_id': {
                    'DataType': 'String',
                    'StringValue': shipment['order_id']
                }
            }
        )
        
        logger.info(
            "Notification sent successfully",
            shipment_id=shipment['shipment_id'],
            message_id=response.get('MessageId')
        )
        
    except Exception as e:
        # Log error but don't fail the shipment creation
        logger.error(
            f"Failed to send notification: {str(e)}",
            shipment_id=shipment.get('shipment_id'),
            order_id=shipment.get('order_id'),
            error_type=type(e).__name__
        )
        # Don't raise - notifications are non-critical


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


def alert_devops_shipments_table_unavailable(order_id: str, shipment_id: str, tracking_number: str):
    """
    Alert DevOps that Shipments table is unavailable
    
    Sends SNS notification to DevOps team about infrastructure issue.
    
    Args:
        order_id: Order ID
        shipment_id: Shipment ID
        tracking_number: Tracking number
        
    Requirements: 8.4
    """
    try:
        if not SNS_TOPIC_ARN:
            logger.warning("No SNS_TOPIC_ARN configured, cannot alert DevOps")
            return
        
        message = {
            'alert_type': 'SHIPMENTS_TABLE_UNAVAILABLE',
            'severity': 'HIGH',
            'order_id': order_id,
            'shipment_id': shipment_id,
            'tracking_number': tracking_number,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': 'Shipments table is unavailable. Order proceeding with manual tracking.',
            'action_required': 'Check DynamoDB table status and restore if needed'
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject='ALERT: Shipments Table Unavailable',
            MessageAttributes={
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'SHIPMENTS_TABLE_UNAVAILABLE'
                },
                'severity': {
                    'DataType': 'String',
                    'StringValue': 'HIGH'
                }
            }
        )
        
        logger.info(
            "DevOps alert sent for Shipments table unavailability",
            order_id=order_id,
            shipment_id=shipment_id
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send DevOps alert: {str(e)}",
            order_id=order_id,
            error_type=type(e).__name__
        )


def fallback_update_order_status(order_id: str, tracking_number: str, timestamp: str):
    """
    Fallback: Update order status without shipment tracking
    
    When Shipments table is unavailable, this function updates the order
    to "shipped" status with tracking number, allowing manual tracking.
    
    Args:
        order_id: Order ID to update
        tracking_number: Tracking number from courier
        timestamp: Current timestamp
        
    Raises:
        Exception: If order update fails
        
    Requirements: 8.4
    """
    try:
        orders_table = dynamodb.Table(ORDERS_TABLE)
        
        # Update order status to "shipped" with tracking number
        # Don't include shipment_id since Shipments table is unavailable
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :shipped, tracking_number = :tracking, shipped_at = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':shipped': 'shipped',
                ':tracking': tracking_number,
                ':time': timestamp,
                ':approved': 'approved'
            },
            ConditionExpression='attribute_exists(orderId) AND #status = :approved'
        )
        
        logger.info(
            "Order status updated with manual tracking fallback",
            order_id=order_id,
            tracking_number=tracking_number
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update order status in fallback: {str(e)}",
            order_id=order_id,
            error_type=type(e).__name__
        )
        raise


