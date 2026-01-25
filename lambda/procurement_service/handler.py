"""
AquaChain Procurement Service - Dashboard Overhaul
Enhanced procurement service with purchase order management, approval workflows,
emergency purchase processing, and comprehensive financial audit logging.

Requirements: 2.1, 2.2, 2.5, 2.6
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import uuid
import logging
from botocore.exceptions import ClientError
import sys
import traceback

# Add shared modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger, TimedOperation, SystemHealthMonitor
from audit_logger import audit_logger
from rbac_middleware import require_permission, validate_user_permissions
from transaction_manager import TransactionManager, TransactionError, ConcurrencyError
from input_validator import validator, ValidationError as InputValidationError, idempotency_manager
from error_handler import (
    ErrorHandler, AquaChainError, ValidationError, BusinessRuleViolationError,
    ConflictError, create_lambda_error_response
)

# Initialize structured logging
logger = get_logger(__name__, 'procurement-service')
health_monitor = SystemHealthMonitor('procurement-service')

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')
lambda_client = boto3.client('lambda')
stepfunctions = boto3.client('stepfunctions')

# Table references
purchase_orders_table = dynamodb.Table(os.environ.get('PURCHASE_ORDERS_TABLE', 'AquaChain-Purchase-Orders'))
suppliers_table = dynamodb.Table(os.environ.get('SUPPLIERS_TABLE', 'AquaChain-Suppliers'))
budget_table = dynamodb.Table(os.environ.get('BUDGET_TABLE', 'AquaChain-Budget-Allocations'))
workflows_table = dynamodb.Table(os.environ.get('WORKFLOWS_TABLE', 'AquaChain-Workflows'))
audit_table = dynamodb.Table(os.environ.get('AUDIT_TABLE', 'AquaChain-Audit-Logs'))


class ProcurementServiceError(Exception):
    """Custom exception for procurement service errors"""
    pass


class ProcurementService:
    """
    Enhanced procurement service with purchase order management, approval workflows,
    emergency purchase processing, and comprehensive financial audit logging.
    
    Features:
    - Purchase order submission and management
    - Approval queue functionality for finance controllers
    - Emergency purchase expedited processing
    - Financial audit logging for all decisions
    - Budget validation and enforcement
    - Supplier integration and risk assessment
    """
    
    def __init__(self, request_context: Optional[Dict] = None):
        """
        Initialize procurement service with request context for audit logging
        
        Args:
            request_context: Request context containing user_id, correlation_id, etc.
        """
        self.request_context = request_context or {}
        self.user_id = self.request_context.get('user_id', 'system')
        self.correlation_id = self.request_context.get('correlation_id', str(uuid.uuid4()))
        
        # Initialize error handler
        self.error_handler = ErrorHandler('procurement-service', enable_debug=False)
        
        # Configuration
        self.approval_topic = os.environ.get('APPROVAL_NOTIFICATIONS_TOPIC')
        self.workflow_state_machine_arn = os.environ.get('WORKFLOW_STATE_MACHINE_ARN')
        self.budget_service_function = os.environ.get('BUDGET_SERVICE_FUNCTION', 'budget-service')
        self.emergency_approval_threshold = float(os.environ.get('EMERGENCY_APPROVAL_THRESHOLD', '10000.0'))
        
        logger.info(
            "Procurement service initialized",
            correlation_id=self.correlation_id,
            user_id=self.user_id
        )
    
    def submit_purchase_order(self, order_data: Dict, idempotency_key: Optional[str] = None) -> Dict:
        """
        Submit a new purchase order with validation and workflow initiation
        
        Args:
            order_data: Purchase order data including items, supplier, budget category
            idempotency_key: Optional idempotency key for duplicate prevention
            
        Returns:
            Created purchase order with workflow information
            
        Raises:
            ValidationError: If input validation fails
            BusinessRuleViolationError: If business rules are violated
            ConflictError: If duplicate operation detected
        """
        with TimedOperation(logger, "submit_purchase_order"):
            try:
                # Check for duplicate operation if idempotency key provided
                if idempotency_key:
                    if not idempotency_manager.validate_idempotency_key(idempotency_key):
                        raise ValidationError("Invalid idempotency key format")
                    
                    operation_signature = f"submit_purchase_order_{json.dumps(order_data, sort_keys=True)}"
                    
                    if idempotency_manager.is_duplicate_operation(idempotency_key, operation_signature):
                        cached_result = idempotency_manager.get_cached_result(idempotency_key)
                        if cached_result:
                            logger.info(
                                "Returning cached result for duplicate operation",
                                idempotency_key=idempotency_key,
                                correlation_id=self.correlation_id
                            )
                            return cached_result
                
                # Validate input data using schema
                try:
                    validated_data = validator.validate_input(
                        order_data, 
                        'purchase_order', 
                        self.correlation_id
                    )
                except InputValidationError as e:
                    raise ValidationError(
                        message=e.message,
                        field_errors=[{
                            'field': e.field,
                            'message': e.message,
                            'code': e.code
                        }] if e.field else [],
                        correlation_id=self.correlation_id
                    )
                
                # Generate order ID and timestamp
                order_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Calculate total amount
                total_amount = self._calculate_total_amount(validated_data['items'])
                
                # Validate budget availability
                budget_validation = self._validate_budget_availability(
                    total_amount, 
                    validated_data['budgetCategory']
                )
                
                if not budget_validation['available']:
                    raise BusinessRuleViolationError(
                        f"Insufficient budget: {budget_validation['message']}",
                        rule="BUDGET_AVAILABILITY",
                        correlation_id=self.correlation_id
                    )
                
                # Validate supplier
                supplier_info = self._validate_supplier(validated_data['supplierId'])
                
                # Determine if emergency purchase
                is_emergency = validated_data.get('isEmergency', False)
                priority = 'EMERGENCY' if is_emergency else 'NORMAL'
                
                # Create purchase order record
                purchase_order = {
                    'PK': f"ORDER#{order_id}",
                    'SK': 'CURRENT',
                    'orderId': order_id,
                    'requesterId': self.user_id,
                    'supplierId': validated_data['supplierId'],
                    'supplierName': supplier_info['name'],
                    'items': validated_data['items'],
                    'totalAmount': Decimal(str(total_amount)),
                    'budgetCategory': validated_data['budgetCategory'],
                    'priority': priority,
                    'status': 'PENDING',
                    'justification': validated_data.get('justification', ''),
                    'deliveryAddress': validated_data.get('deliveryAddress', ''),
                    'requestedDeliveryDate': validated_data.get('requestedDeliveryDate'),
                    'createdAt': timestamp,
                    'updatedAt': timestamp,
                    'correlationId': self.correlation_id,
                    'version': 1,
                    'GSI1PK': f"STATUS#PENDING",
                    'GSI1SK': f"CREATED#{timestamp}",
                    'GSI2PK': f"REQUESTER#{self.user_id}",
                    'GSI2SK': f"CREATED#{timestamp}"
                }
                
                # Store purchase order
                purchase_orders_table.put_item(Item=purchase_order)
                
                # Create workflow instance
                workflow_id = self._create_approval_workflow(order_id, is_emergency, total_amount)
                
                # Update purchase order with workflow ID
                purchase_orders_table.update_item(
                    Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'},
                    UpdateExpression='SET workflowId = :wid',
                    ExpressionAttributeValues={':wid': workflow_id}
                )
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='SUBMIT_PURCHASE_ORDER',
                    resource='PURCHASE_ORDER',
                    resource_id=order_id,
                    details={
                        'totalAmount': float(total_amount),
                        'budgetCategory': validated_data['budgetCategory'],
                        'supplierId': validated_data['supplierId'],
                        'priority': priority,
                        'workflowId': workflow_id,
                        'idempotencyKey': idempotency_key
                    },
                    request_context=self.request_context,
                    after_state=purchase_order
                )
                
                # Send notification for approval queue
                self._notify_approval_queue(order_id, is_emergency, total_amount)
                
                result = {
                    'orderId': order_id,
                    'workflowId': workflow_id,
                    'status': 'PENDING',
                    'totalAmount': float(total_amount),
                    'priority': priority,
                    'createdAt': timestamp
                }
                
                # Cache result if idempotency key provided
                if idempotency_key:
                    idempotency_manager.store_operation_result(
                        idempotency_key, 
                        operation_signature, 
                        result
                    )
                
                logger.info(
                    "Purchase order submitted successfully",
                    order_id=order_id,
                    workflow_id=workflow_id,
                    total_amount=total_amount,
                    priority=priority,
                    idempotency_key=idempotency_key,
                    correlation_id=self.correlation_id
                )
                
                return result
                
            except (ValidationError, BusinessRuleViolationError, ConflictError) as e:
                # Re-raise known errors
                raise
            except Exception as e:
                logger.error(
                    "Failed to submit purchase order",
                    error=str(e),
                    correlation_id=self.correlation_id,
                    user_id=self.user_id
                )
                raise AquaChainError(
                    message="Failed to submit purchase order",
                    code="SUBMISSION_FAILED",
                    status_code=500,
                    correlation_id=self.correlation_id
                )
    
    def get_approval_queue(self, filters: Optional[Dict] = None) -> Dict:
        """
        Get approval queue for finance controllers with filtering and pagination
        
        Args:
            filters: Optional filters for status, priority, date range, etc.
            
        Returns:
            List of pending purchase orders for approval
        """
        with TimedOperation(logger, "get_approval_queue"):
            try:
                # Default filters
                filters = filters or {}
                status_filter = filters.get('status', 'PENDING')
                priority_filter = filters.get('priority')
                limit = min(filters.get('limit', 50), 100)  # Max 100 items
                
                # Query parameters
                query_params = {
                    'IndexName': 'GSI1',
                    'KeyConditionExpression': 'GSI1PK = :status',
                    'ExpressionAttributeValues': {':status': f"STATUS#{status_filter}"},
                    'ScanIndexForward': False,  # Most recent first
                    'Limit': limit
                }
                
                # Add priority filter if specified
                if priority_filter:
                    query_params['FilterExpression'] = 'priority = :priority'
                    query_params['ExpressionAttributeValues'][':priority'] = priority_filter
                
                # Execute query
                response = purchase_orders_table.query(**query_params)
                
                # Process results
                orders = []
                for item in response['Items']:
                    # Convert Decimal to float for JSON serialization
                    order = self._convert_decimals(item)
                    
                    # Add calculated fields
                    order['daysInQueue'] = self._calculate_days_in_queue(order['createdAt'])
                    order['riskLevel'] = self._calculate_risk_level(order)
                    
                    orders.append(order)
                
                logger.info(
                    "Retrieved approval queue",
                    count=len(orders),
                    status_filter=status_filter,
                    priority_filter=priority_filter,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'orders': orders,
                    'count': len(orders),
                    'hasMore': 'LastEvaluatedKey' in response,
                    'lastEvaluatedKey': response.get('LastEvaluatedKey')
                }
                
            except Exception as e:
                logger.error(
                    "Failed to retrieve approval queue",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to retrieve approval queue: {str(e)}")
    
    def approve_purchase_order(self, order_id: str, approval_data: Dict) -> Dict:
        """
        Approve a purchase order with mandatory justification using atomic transactions
        
        Args:
            order_id: Purchase order ID to approve
            approval_data: Approval details including justification
            
        Returns:
            Updated purchase order status
        """
        with TimedOperation(logger, "approve_purchase_order"):
            try:
                # Validate approval data
                if not approval_data.get('justification'):
                    raise ProcurementServiceError("Approval justification is required")
                
                # Get current purchase order with version for optimistic concurrency
                response = purchase_orders_table.get_item(
                    Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise ProcurementServiceError(f"Purchase order {order_id} not found")
                
                current_order = response['Item']
                current_version = int(current_order.get('version', 0))
                
                # Validate current status
                if current_order['status'] != 'PENDING':
                    raise ProcurementServiceError(
                        f"Cannot approve order in {current_order['status']} status"
                    )
                
                # Validate budget one more time before approval
                budget_validation = self._validate_budget_availability(
                    float(current_order['totalAmount']),
                    current_order['budgetCategory']
                )
                
                if not budget_validation['available']:
                    raise ProcurementServiceError(
                        f"Budget no longer available: {budget_validation['message']}"
                    )
                
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Execute atomic transaction for approval
                tm = TransactionManager(self.correlation_id)
                
                with tm.transaction_context(idempotency_key=f"approve_order_{order_id}_{timestamp}") as txn:
                    # Update purchase order status with version check
                    txn.update(
                        table_name=purchase_orders_table.name,
                        key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'},
                        update_expression='''
                            SET #status = :status,
                                approvedBy = :approver,
                                approvedAt = :timestamp,
                                approvalJustification = :justification,
                                updatedAt = :timestamp,
                                GSI1PK = :gsi1pk
                        ''',
                        expression_attribute_names={'#status': 'status'},
                        expression_attribute_values={
                            ':status': 'APPROVED',
                            ':approver': self.user_id,
                            ':timestamp': timestamp,
                            ':justification': approval_data['justification'],
                            ':gsi1pk': 'STATUS#APPROVED'
                        },
                        expected_version=current_version
                    )
                    
                    # Update workflow status if exists
                    if current_order.get('workflowId'):
                        workflow_response = workflows_table.get_item(
                            Key={'PK': f"WORKFLOW#{current_order['workflowId']}", 'SK': 'CURRENT'}
                        )
                        
                        if 'Item' in workflow_response:
                            workflow_version = int(workflow_response['Item'].get('version', 0))
                            
                            txn.update(
                                table_name=workflows_table.name,
                                key={'PK': f"WORKFLOW#{current_order['workflowId']}", 'SK': 'CURRENT'},
                                update_expression='''
                                    SET currentState = :state,
                                        updatedAt = :timestamp,
                                        approvalDetails = :details
                                ''',
                                expression_attribute_values={
                                    ':state': 'APPROVED',
                                    ':timestamp': timestamp,
                                    ':details': {
                                        'approvedBy': self.user_id,
                                        'justification': approval_data['justification'],
                                        'approvedAt': timestamp
                                    }
                                },
                                expected_version=workflow_version
                            )
                    
                    # Reserve budget atomically
                    current_period = self._get_current_budget_period()
                    budget_key = {'PK': f"BUDGET#{current_order['budgetCategory']}#{current_period}", 'SK': 'ALLOCATION'}
                    
                    # Get current budget info for version check
                    budget_response = budget_table.get_item(Key=budget_key)
                    if 'Item' in budget_response:
                        budget_version = int(budget_response['Item'].get('version', 0))
                        
                        txn.update(
                            table_name=budget_table.name,
                            key=budget_key,
                            update_expression='ADD reservedAmount :amount SET updatedAt = :timestamp',
                            expression_attribute_values={
                                ':amount': current_order['totalAmount'],
                                ':timestamp': timestamp
                            },
                            expected_version=budget_version
                        )
                
                # Get the updated order for response
                updated_response = purchase_orders_table.get_item(
                    Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'}
                )
                updated_order = updated_response['Item']
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='APPROVE_PURCHASE_ORDER',
                    resource='PURCHASE_ORDER',
                    resource_id=order_id,
                    details={
                        'totalAmount': float(current_order['totalAmount']),
                        'budgetCategory': current_order['budgetCategory'],
                        'justification': approval_data['justification'],
                        'workflowId': current_order.get('workflowId'),
                        'transactionId': self.correlation_id
                    },
                    request_context=self.request_context,
                    before_state=current_order,
                    after_state=updated_order
                )
                
                # Send approval notification (async, outside transaction)
                self._send_approval_notification(order_id, 'APPROVED', current_order['requesterId'])
                
                logger.info(
                    "Purchase order approved atomically",
                    order_id=order_id,
                    approver=self.user_id,
                    total_amount=float(current_order['totalAmount']),
                    transaction_id=self.correlation_id,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'orderId': order_id,
                    'status': 'APPROVED',
                    'approvedBy': self.user_id,
                    'approvedAt': timestamp,
                    'justification': approval_data['justification'],
                    'transactionId': self.correlation_id
                }
                
            except ConcurrencyError as e:
                logger.warning(
                    "Concurrent modification detected during approval",
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Order was modified by another user. Please refresh and try again.")
                
            except TransactionError as e:
                logger.error(
                    "Transaction failed during approval",
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to approve purchase order: {str(e)}")
                
            except Exception as e:
                logger.error(
                    "Failed to approve purchase order",
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to approve purchase order: {str(e)}")
    
    def reject_purchase_order(self, order_id: str, rejection_data: Dict) -> Dict:
        """
        Reject a purchase order with mandatory justification
        
        Args:
            order_id: Purchase order ID to reject
            rejection_data: Rejection details including justification
            
        Returns:
            Updated purchase order status
        """
        with TimedOperation(logger, "reject_purchase_order"):
            try:
                # Validate rejection data
                if not rejection_data.get('justification'):
                    raise ProcurementServiceError("Rejection justification is required")
                
                # Get current purchase order
                response = purchase_orders_table.get_item(
                    Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise ProcurementServiceError(f"Purchase order {order_id} not found")
                
                current_order = response['Item']
                
                # Validate current status
                if current_order['status'] != 'PENDING':
                    raise ProcurementServiceError(
                        f"Cannot reject order in {current_order['status']} status"
                    )
                
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Update purchase order status
                updated_order = purchase_orders_table.update_item(
                    Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'},
                    UpdateExpression='''
                        SET #status = :status,
                            rejectedBy = :rejector,
                            rejectedAt = :timestamp,
                            rejectionJustification = :justification,
                            updatedAt = :timestamp,
                            GSI1PK = :gsi1pk
                    ''',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'REJECTED',
                        ':rejector': self.user_id,
                        ':timestamp': timestamp,
                        ':justification': rejection_data['justification'],
                        ':gsi1pk': 'STATUS#REJECTED'
                    },
                    ReturnValues='ALL_NEW'
                )
                
                # Update workflow status
                if current_order.get('workflowId'):
                    self._update_workflow_status(
                        current_order['workflowId'],
                        'REJECTED',
                        rejection_data['justification']
                    )
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='REJECT_PURCHASE_ORDER',
                    resource='PURCHASE_ORDER',
                    resource_id=order_id,
                    details={
                        'totalAmount': float(current_order['totalAmount']),
                        'budgetCategory': current_order['budgetCategory'],
                        'justification': rejection_data['justification'],
                        'workflowId': current_order.get('workflowId')
                    },
                    request_context=self.request_context,
                    before_state=current_order,
                    after_state=updated_order['Attributes']
                )
                
                # Send rejection notification
                self._send_approval_notification(order_id, 'REJECTED', current_order['requesterId'])
                
                logger.info(
                    "Purchase order rejected",
                    order_id=order_id,
                    rejector=self.user_id,
                    total_amount=float(current_order['totalAmount']),
                    correlation_id=self.correlation_id
                )
                
                return {
                    'orderId': order_id,
                    'status': 'REJECTED',
                    'rejectedBy': self.user_id,
                    'rejectedAt': timestamp,
                    'justification': rejection_data['justification']
                }
                
            except Exception as e:
                logger.error(
                    "Failed to reject purchase order",
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to reject purchase order: {str(e)}")
    
    def process_emergency_purchase(self, order_data: Dict) -> Dict:
        """
        Process emergency purchase with expedited workflow
        
        Args:
            order_data: Emergency purchase order data
            
        Returns:
            Created emergency purchase order
        """
        with TimedOperation(logger, "process_emergency_purchase"):
            try:
                # Mark as emergency and add expedited processing
                order_data['isEmergency'] = True
                order_data['expeditedReason'] = order_data.get('expeditedReason', 'Emergency purchase')
                
                # Validate emergency justification
                if not order_data.get('emergencyJustification'):
                    raise ProcurementServiceError("Emergency justification is required")
                
                # Calculate total amount for threshold check
                total_amount = self._calculate_total_amount(order_data['items'])
                
                # Check if amount exceeds emergency threshold
                if total_amount > self.emergency_approval_threshold:
                    logger.warning(
                        "Emergency purchase exceeds threshold",
                        total_amount=total_amount,
                        threshold=self.emergency_approval_threshold,
                        correlation_id=self.correlation_id
                    )
                
                # Submit as regular purchase order but with emergency priority
                result = self.submit_purchase_order(order_data)
                
                # Additional emergency processing
                self._process_emergency_notifications(result['orderId'], total_amount)
                
                # Log emergency purchase audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='SUBMIT_EMERGENCY_PURCHASE',
                    resource='PURCHASE_ORDER',
                    resource_id=result['orderId'],
                    details={
                        'totalAmount': total_amount,
                        'emergencyJustification': order_data['emergencyJustification'],
                        'expeditedReason': order_data['expeditedReason'],
                        'exceedsThreshold': total_amount > self.emergency_approval_threshold
                    },
                    request_context=self.request_context
                )
                
                logger.info(
                    "Emergency purchase processed",
                    order_id=result['orderId'],
                    total_amount=total_amount,
                    exceeds_threshold=total_amount > self.emergency_approval_threshold,
                    correlation_id=self.correlation_id
                )
                
                return {
                    **result,
                    'isEmergency': True,
                    'exceedsThreshold': total_amount > self.emergency_approval_threshold
                }
                
            except Exception as e:
                logger.error(
                    "Failed to process emergency purchase",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to process emergency purchase: {str(e)}")
    
    def get_financial_audit_log(self, filters: Optional[Dict] = None) -> Dict:
        """
        Get financial audit log with filtering and export capabilities
        
        Args:
            filters: Optional filters for date range, user, action type, etc.
            
        Returns:
            Filtered audit log entries
        """
        with TimedOperation(logger, "get_financial_audit_log"):
            try:
                # Default filters
                filters = filters or {}
                start_date = filters.get('startDate')
                end_date = filters.get('endDate')
                action_filter = filters.get('action')
                user_filter = filters.get('userId')
                limit = min(filters.get('limit', 100), 500)  # Max 500 items
                
                # Build query parameters
                query_params = {
                    'IndexName': 'GSI1',
                    'KeyConditionExpression': 'GSI1PK = :resource',
                    'ExpressionAttributeValues': {':resource': 'RESOURCE#PURCHASE_ORDER'},
                    'ScanIndexForward': False,  # Most recent first
                    'Limit': limit
                }
                
                # Add filters
                filter_expressions = []
                if start_date:
                    filter_expressions.append('createdAt >= :start_date')
                    query_params['ExpressionAttributeValues'][':start_date'] = start_date
                
                if end_date:
                    filter_expressions.append('createdAt <= :end_date')
                    query_params['ExpressionAttributeValues'][':end_date'] = end_date
                
                if action_filter:
                    filter_expressions.append('action = :action')
                    query_params['ExpressionAttributeValues'][':action'] = action_filter
                
                if user_filter:
                    filter_expressions.append('userId = :user_id')
                    query_params['ExpressionAttributeValues'][':user_id'] = user_filter
                
                if filter_expressions:
                    query_params['FilterExpression'] = ' AND '.join(filter_expressions)
                
                # Execute query
                response = audit_table.query(**query_params)
                
                # Process results
                audit_entries = []
                for item in response['Items']:
                    entry = self._convert_decimals(item)
                    audit_entries.append(entry)
                
                logger.info(
                    "Retrieved financial audit log",
                    count=len(audit_entries),
                    filters=filters,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'auditEntries': audit_entries,
                    'count': len(audit_entries),
                    'hasMore': 'LastEvaluatedKey' in response,
                    'lastEvaluatedKey': response.get('LastEvaluatedKey'),
                    'filters': filters
                }
                
            except Exception as e:
                logger.error(
                    "Failed to retrieve financial audit log",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise ProcurementServiceError(f"Failed to retrieve financial audit log: {str(e)}")
    
    # Private helper methods
    
    def _validate_purchase_order_data(self, order_data: Dict) -> None:
        """Validate purchase order input data"""
        required_fields = ['supplierId', 'items', 'budgetCategory']
        for field in required_fields:
            if field not in order_data:
                raise ProcurementServiceError(f"Missing required field: {field}")
        
        if not order_data['items'] or len(order_data['items']) == 0:
            raise ProcurementServiceError("Purchase order must contain at least one item")
        
        # Validate each item
        for item in order_data['items']:
            if not all(key in item for key in ['itemId', 'quantity', 'unitPrice']):
                raise ProcurementServiceError("Each item must have itemId, quantity, and unitPrice")
            
            if item['quantity'] <= 0 or item['unitPrice'] <= 0:
                raise ProcurementServiceError("Item quantity and unit price must be positive")
    
    def _calculate_total_amount(self, items: List[Dict]) -> float:
        """Calculate total amount for purchase order items"""
        total = 0.0
        for item in items:
            total += item['quantity'] * item['unitPrice']
        return total
    
    def _get_current_budget_period(self) -> str:
        """Get current budget period in YYYY-MM format"""
        return datetime.utcnow().strftime('%Y-%m')
    
    def _validate_budget_availability(self, amount: float, budget_category: str) -> Dict:
        """Validate budget availability for purchase amount"""
        try:
            # Call budget service to validate availability
            response = lambda_client.invoke(
                FunctionName=self.budget_service_function,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'validate_budget',
                    'amount': amount,
                    'category': budget_category,
                    'correlationId': self.correlation_id
                })
            )
            
            result = json.loads(response['Payload'].read())
            return result.get('body', {'available': False, 'message': 'Budget validation failed'})
            
        except Exception as e:
            logger.warning(
                "Budget validation service unavailable, allowing purchase",
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Graceful degradation - allow purchase but log warning
            return {'available': True, 'message': 'Budget validation unavailable'}
    
    def _validate_supplier(self, supplier_id: str) -> Dict:
        """Validate supplier exists and is active"""
        try:
            response = suppliers_table.get_item(
                Key={'PK': f"SUPPLIER#{supplier_id}", 'SK': 'PROFILE'}
            )
            
            if 'Item' not in response:
                raise ProcurementServiceError(f"Supplier {supplier_id} not found")
            
            supplier = response['Item']
            if supplier.get('status') != 'ACTIVE':
                raise ProcurementServiceError(f"Supplier {supplier_id} is not active")
            
            return {
                'id': supplier_id,
                'name': supplier.get('name', 'Unknown'),
                'status': supplier.get('status'),
                'riskLevel': supplier.get('riskLevel', 'MEDIUM')
            }
            
        except ClientError as e:
            logger.error(
                "Failed to validate supplier",
                supplier_id=supplier_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise ProcurementServiceError(f"Failed to validate supplier: {str(e)}")
    
    def _create_approval_workflow(self, order_id: str, is_emergency: bool, amount: float) -> str:
        """Create approval workflow for purchase order"""
        try:
            workflow_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Determine workflow type and timeout
            workflow_type = 'EMERGENCY_PURCHASE_APPROVAL' if is_emergency else 'PURCHASE_APPROVAL'
            timeout_hours = 4 if is_emergency else 24  # Emergency: 4 hours, Normal: 24 hours
            timeout_at = (datetime.utcnow() + timedelta(hours=timeout_hours)).isoformat() + 'Z'
            
            # Create workflow record
            workflow_record = {
                'PK': f"WORKFLOW#{workflow_id}",
                'SK': 'CURRENT',
                'workflowId': workflow_id,
                'workflowType': workflow_type,
                'currentState': 'PENDING_APPROVAL',
                'orderId': order_id,
                'amount': Decimal(str(amount)),
                'isEmergency': is_emergency,
                'createdBy': self.user_id,
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'timeoutAt': timeout_at,
                'correlationId': self.correlation_id,
                'GSI1PK': f"TYPE#{workflow_type}",
                'GSI1SK': f"STATE#PENDING_APPROVAL#{timestamp}"
            }
            
            workflows_table.put_item(Item=workflow_record)
            
            # Start Step Functions workflow if configured
            if self.workflow_state_machine_arn:
                stepfunctions.start_execution(
                    stateMachineArn=self.workflow_state_machine_arn,
                    name=f"approval-{workflow_id}",
                    input=json.dumps({
                        'workflowId': workflow_id,
                        'orderId': order_id,
                        'isEmergency': is_emergency,
                        'amount': amount,
                        'timeoutAt': timeout_at
                    })
                )
            
            return workflow_id
            
        except Exception as e:
            logger.error(
                "Failed to create approval workflow",
                order_id=order_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise ProcurementServiceError(f"Failed to create approval workflow: {str(e)}")
    
    def _update_workflow_status(self, workflow_id: str, status: str, justification: str) -> None:
        """Update workflow status"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            workflows_table.update_item(
                Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'},
                UpdateExpression='''
                    SET currentState = :status,
                        updatedAt = :timestamp,
                        completedBy = :user_id,
                        completedAt = :timestamp,
                        justification = :justification,
                        GSI1SK = :gsi1sk
                ''',
                ExpressionAttributeValues={
                    ':status': status,
                    ':timestamp': timestamp,
                    ':user_id': self.user_id,
                    ':justification': justification,
                    ':gsi1sk': f"STATE#{status}#{timestamp}"
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to update workflow status",
                workflow_id=workflow_id,
                status=status,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical for the main operation
    
    def _reserve_budget(self, amount: float, budget_category: str, order_id: str) -> None:
        """Reserve budget for approved purchase order"""
        try:
            lambda_client.invoke(
                FunctionName=self.budget_service_function,
                InvocationType='Event',  # Async call
                Payload=json.dumps({
                    'action': 'reserve_budget',
                    'amount': amount,
                    'category': budget_category,
                    'orderId': order_id,
                    'correlationId': self.correlation_id
                })
            )
            
        except Exception as e:
            logger.error(
                "Failed to reserve budget",
                amount=amount,
                budget_category=budget_category,
                order_id=order_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as approval is already complete
    
    def _notify_approval_queue(self, order_id: str, is_emergency: bool, amount: float) -> None:
        """Send notification to approval queue"""
        try:
            if self.approval_topic:
                message = {
                    'orderId': order_id,
                    'isEmergency': is_emergency,
                    'amount': amount,
                    'requesterId': self.user_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'correlationId': self.correlation_id
                }
                
                sns.publish(
                    TopicArn=self.approval_topic,
                    Message=json.dumps(message),
                    Subject=f"{'Emergency ' if is_emergency else ''}Purchase Order Approval Required"
                )
                
        except Exception as e:
            logger.error(
                "Failed to send approval queue notification",
                order_id=order_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical
    
    def _send_approval_notification(self, order_id: str, status: str, requester_id: str) -> None:
        """Send approval/rejection notification to requester"""
        try:
            if self.approval_topic:
                message = {
                    'orderId': order_id,
                    'status': status,
                    'requesterId': requester_id,
                    'approver': self.user_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'correlationId': self.correlation_id
                }
                
                sns.publish(
                    TopicArn=self.approval_topic,
                    Message=json.dumps(message),
                    Subject=f"Purchase Order {status.title()}"
                )
                
        except Exception as e:
            logger.error(
                "Failed to send approval notification",
                order_id=order_id,
                status=status,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical
    
    def _process_emergency_notifications(self, order_id: str, amount: float) -> None:
        """Process additional notifications for emergency purchases"""
        try:
            # Send high-priority notification
            if self.approval_topic:
                message = {
                    'orderId': order_id,
                    'type': 'EMERGENCY_PURCHASE',
                    'amount': amount,
                    'requesterId': self.user_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'correlationId': self.correlation_id,
                    'priority': 'HIGH'
                }
                
                sns.publish(
                    TopicArn=self.approval_topic,
                    Message=json.dumps(message),
                    Subject="URGENT: Emergency Purchase Order Requires Immediate Approval",
                    MessageAttributes={
                        'priority': {'DataType': 'String', 'StringValue': 'HIGH'},
                        'type': {'DataType': 'String', 'StringValue': 'EMERGENCY_PURCHASE'}
                    }
                )
            
            # Send EventBridge event for additional processing
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.procurement',
                        'DetailType': 'Emergency Purchase Submitted',
                        'Detail': json.dumps({
                            'orderId': order_id,
                            'amount': amount,
                            'requesterId': self.user_id,
                            'correlationId': self.correlation_id
                        })
                    }
                ]
            )
            
        except Exception as e:
            logger.error(
                "Failed to process emergency notifications",
                order_id=order_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical
    
    def _calculate_days_in_queue(self, created_at: str) -> int:
        """Calculate number of days order has been in queue"""
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - created_date).days
        except:
            return 0
    
    def _calculate_risk_level(self, order: Dict) -> str:
        """Calculate risk level for purchase order"""
        try:
            amount = float(order.get('totalAmount', 0))
            days_in_queue = order.get('daysInQueue', 0)
            is_emergency = order.get('priority') == 'EMERGENCY'
            
            if is_emergency or amount > 50000:
                return 'HIGH'
            elif amount > 10000 or days_in_queue > 3:
                return 'MEDIUM'
            else:
                return 'LOW'
        except:
            return 'MEDIUM'
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj


# Lambda handler function
def lambda_handler(event, context):
    """
    Main Lambda handler for procurement service
    
    Supported actions:
    - submit_purchase_order
    - get_approval_queue
    - approve_purchase_order
    - reject_purchase_order
    - process_emergency_purchase
    - get_financial_audit_log
    """
    try:
        # Extract request context
        request_context = {
            'user_id': event.get('requestContext', {}).get('authorizer', {}).get('userId', 'anonymous'),
            'username': event.get('requestContext', {}).get('authorizer', {}).get('username', 'unknown'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4())),
            'ipAddress': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'userAgent': event.get('headers', {}).get('User-Agent', 'unknown')
        }
        
        # Initialize service
        service = ProcurementService(request_context)
        
        # Parse request body
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        action = body.get('action') or event.get('pathParameters', {}).get('action')
        
        # Route to appropriate method
        if action == 'submit_purchase_order':
            # Validate RBAC permissions for purchase order submission
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'purchase-orders',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for purchase order submission",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'purchase-orders',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.submit_purchase_order(body.get('orderData', {}))
            
        elif action == 'get_approval_queue':
            # Validate RBAC permissions for approval queue access
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'purchase-orders',
                'approve',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for approval queue access",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'purchase-orders',
                        'action': 'approve',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.get_approval_queue(body.get('filters', {}))
            
        elif action == 'approve_purchase_order':
            # Validate RBAC permissions for purchase order approval
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'purchase-orders',
                'approve',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for purchase order approval",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'purchase-orders',
                        'action': 'approve',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            order_id = body.get('orderId') or event.get('pathParameters', {}).get('orderId')
            result = service.approve_purchase_order(order_id, body.get('approvalData', {}))
            
        elif action == 'reject_purchase_order':
            # Validate RBAC permissions for purchase order rejection
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'purchase-orders',
                'approve',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for purchase order rejection",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'purchase-orders',
                        'action': 'approve',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            order_id = body.get('orderId') or event.get('pathParameters', {}).get('orderId')
            result = service.reject_purchase_order(order_id, body.get('rejectionData', {}))
            
        elif action == 'process_emergency_purchase':
            # Validate RBAC permissions for emergency purchases
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'emergency-purchases',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for emergency purchase processing",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'emergency-purchases',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.process_emergency_purchase(body.get('orderData', {}))
            
        elif action == 'get_financial_audit_log':
            # Validate RBAC permissions for financial audit log access
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'audit-trails',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for financial audit log access",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'audit-trails',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.get_financial_audit_log(body.get('filters', {}))
        else:
            raise ProcurementServiceError(f"Unknown action: {action}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context['correlation_id']
            },
            'body': json.dumps({
                'success': True,
                'data': result,
                'correlationId': request_context['correlation_id']
            })
        }
        
    except ProcurementServiceError as e:
        logger.error(
            "Procurement service error",
            error=str(e),
            correlation_id=request_context.get('correlation_id', 'unknown')
        )
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context.get('correlation_id', 'unknown')
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'correlationId': request_context.get('correlation_id', 'unknown')
            })
        }
        
    except Exception as e:
        logger.error(
            "Unexpected error in procurement service",
            error=str(e),
            traceback=traceback.format_exc(),
            correlation_id=request_context.get('correlation_id', 'unknown')
        )
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context.get('correlation_id', 'unknown')
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'correlationId': request_context.get('correlation_id', 'unknown')
            })
        }