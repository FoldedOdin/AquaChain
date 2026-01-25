"""
AquaChain Workflow Service - Dashboard Overhaul
State machine for approval workflows with timeout handling, escalation,
notification system, and comprehensive audit trails with rollback capabilities.

Requirements: 6.3, 6.6, 6.7, 13.3
"""

import json
import boto3
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import uuid
import logging
from botocore.exceptions import ClientError
import sys
import traceback
from enum import Enum

# Add shared modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger, TimedOperation, SystemHealthMonitor
from audit_logger import audit_logger
from rbac_middleware import require_permission, validate_user_permissions

# Initialize structured logging
logger = get_logger(__name__, 'workflow-service')
health_monitor = SystemHealthMonitor('workflow-service')

# AWS clients - lazy initialization to reduce cold start
def get_aws_clients():
    """Get AWS clients with lazy initialization"""
    if not hasattr(get_aws_clients, '_clients'):
        get_aws_clients._clients = {
            'dynamodb': boto3.resource('dynamodb'),
            'sns': boto3.client('sns'),
            'eventbridge': boto3.client('events'),
            'lambda': boto3.client('lambda'),
            'stepfunctions': boto3.client('stepfunctions')
        }
    return get_aws_clients._clients

# Initialize clients lazily
def get_dynamodb(): return get_aws_clients()['dynamodb']
def get_sns(): return get_aws_clients()['sns']
def get_eventbridge(): return get_aws_clients()['eventbridge']
def get_lambda_client(): return get_aws_clients()['lambda']
def get_stepfunctions(): return get_aws_clients()['stepfunctions']

# Table references - lazy initialization
def get_workflows_table(): return get_dynamodb().Table(os.environ.get('WORKFLOWS_TABLE', 'AquaChain-Workflows'))
def get_purchase_orders_table(): return get_dynamodb().Table(os.environ.get('PURCHASE_ORDERS_TABLE', 'AquaChain-Purchase-Orders'))
def get_audit_table(): return get_dynamodb().Table(os.environ.get('AUDIT_TABLE', 'AquaChain-Audit-Logs'))
def get_users_table(): return get_dynamodb().Table(os.environ.get('USERS_TABLE', 'AquaChain-Users'))

# Global table references for backward compatibility
workflows_table = None
purchase_orders_table = None
users_table = None
audit_table = None

def _initialize_tables():
    """Initialize global table references"""
    global workflows_table, purchase_orders_table, users_table, audit_table
    if workflows_table is None:
        workflows_table = get_workflows_table()
        purchase_orders_table = get_purchase_orders_table()
        users_table = get_users_table()
        audit_table = get_audit_table()


class WorkflowState(Enum):
    """Workflow state enumeration"""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT_ESCALATED = "TIMEOUT_ESCALATED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowType(Enum):
    """Workflow type enumeration"""
    PURCHASE_APPROVAL = "PURCHASE_APPROVAL"
    EMERGENCY_PURCHASE_APPROVAL = "EMERGENCY_PURCHASE_APPROVAL"
    BUDGET_ALLOCATION = "BUDGET_ALLOCATION"
    SUPPLIER_APPROVAL = "SUPPLIER_APPROVAL"


class WorkflowAction(Enum):
    """Workflow action enumeration"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    CANCEL = "CANCEL"
    TIMEOUT = "TIMEOUT"
    COMPLETE = "COMPLETE"


class WorkflowServiceError(Exception):
    """Custom exception for workflow service errors"""
    pass


class WorkflowStateMachine:
    """
    State machine for workflow transitions with validation and audit logging
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        WorkflowState.PENDING_APPROVAL: [
            WorkflowState.APPROVED,
            WorkflowState.REJECTED,
            WorkflowState.TIMEOUT_ESCALATED,
            WorkflowState.CANCELLED
        ],
        WorkflowState.TIMEOUT_ESCALATED: [
            WorkflowState.APPROVED,
            WorkflowState.REJECTED,
            WorkflowState.CANCELLED
        ],
        WorkflowState.APPROVED: [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED
        ],
        WorkflowState.REJECTED: [],  # Terminal state
        WorkflowState.CANCELLED: [],  # Terminal state
        WorkflowState.COMPLETED: [],  # Terminal state
        WorkflowState.FAILED: [
            WorkflowState.PENDING_APPROVAL  # Allow retry
        ]
    }
    
    @classmethod
    def is_valid_transition(cls, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """Check if state transition is valid"""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, [])
    
    @classmethod
    def get_valid_transitions(cls, from_state: WorkflowState) -> List[WorkflowState]:
        """Get list of valid transitions from current state"""
        return cls.VALID_TRANSITIONS.get(from_state, [])
    
    @classmethod
    def is_terminal_state(cls, state: WorkflowState) -> bool:
        """Check if state is terminal (no further transitions allowed)"""
        return len(cls.VALID_TRANSITIONS.get(state, [])) == 0


class WorkflowService:
    """
    Enhanced workflow service with state machine management, timeout handling,
    escalation, notification system, and comprehensive audit trails.
    
    Features:
    - State machine for approval workflows
    - Timeout handling with escalation to finance controller
    - Notification system for workflow status changes
    - Workflow audit trail with rollback capabilities
    - Support for multiple workflow types
    - Comprehensive error handling and recovery
    """
    
    def __init__(self, request_context: Optional[Dict] = None):
        """
        Initialize workflow service with request context for audit logging
        
        Args:
            request_context: Request context containing user_id, correlation_id, etc.
        """
        # Initialize tables if not already done
        _initialize_tables()
        
        self.request_context = request_context or {}
        self.user_id = self.request_context.get('user_id', 'system')
        self.correlation_id = self.request_context.get('correlation_id', str(uuid.uuid4()))
        
        # Configuration
        self.notification_topic = os.environ.get('WORKFLOW_NOTIFICATIONS_TOPIC')
        self.escalation_topic = os.environ.get('ESCALATION_NOTIFICATIONS_TOPIC')
        self.notification_service_function = os.environ.get('NOTIFICATION_SERVICE_FUNCTION', 'notification-service')
        
        # Timeout configurations (in hours)
        self.timeout_configs = {
            WorkflowType.PURCHASE_APPROVAL: 24,
            WorkflowType.EMERGENCY_PURCHASE_APPROVAL: 4,
            WorkflowType.BUDGET_ALLOCATION: 48,
            WorkflowType.SUPPLIER_APPROVAL: 72
        }
        
        logger.info(
            "Workflow service initialized",
            correlation_id=self.correlation_id,
            user_id=self.user_id
        )
    
    def create_workflow(self, workflow_type: str, payload: Dict, metadata: Optional[Dict] = None) -> Dict:
        """
        Create a new workflow instance with initial state
        
        Args:
            workflow_type: Type of workflow (PURCHASE_APPROVAL, etc.)
            payload: Workflow payload data
            metadata: Optional metadata for the workflow
            
        Returns:
            Created workflow instance
            
        Raises:
            WorkflowServiceError: If workflow creation fails
        """
        with TimedOperation(logger, "create_workflow"):
            try:
                # Validate workflow type
                try:
                    wf_type = WorkflowType(workflow_type)
                except ValueError:
                    raise WorkflowServiceError(f"Invalid workflow type: {workflow_type}")
                
                # Generate workflow ID and timestamp
                workflow_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Calculate timeout
                timeout_hours = self.timeout_configs.get(wf_type, 24)
                timeout_at = (datetime.utcnow() + timedelta(hours=timeout_hours)).isoformat() + 'Z'
                
                # Create workflow record
                workflow_record = {
                    'PK': f"WORKFLOW#{workflow_id}",
                    'SK': 'CURRENT',
                    'workflowId': workflow_id,
                    'workflowType': workflow_type,
                    'currentState': WorkflowState.PENDING_APPROVAL.value,
                    'payload': payload,
                    'metadata': metadata or {},
                    'createdBy': self.user_id,
                    'createdAt': timestamp,
                    'updatedAt': timestamp,
                    'timeoutAt': timeout_at,
                    'correlationId': self.correlation_id,
                    'stateHistory': [],
                    'rollbackData': {},
                    'GSI1PK': f"TYPE#{workflow_type}",
                    'GSI1SK': f"STATE#{WorkflowState.PENDING_APPROVAL.value}#{timestamp}",
                    'GSI2PK': f"CREATOR#{self.user_id}",
                    'GSI2SK': f"CREATED#{timestamp}"
                }
                
                # Store workflow record
                workflows_table.put_item(Item=workflow_record)
                
                # Create initial state audit entry
                self._create_state_audit_entry(
                    workflow_id,
                    None,
                    WorkflowState.PENDING_APPROVAL.value,
                    WorkflowAction.APPROVE.value,  # Initial creation action
                    "Workflow created",
                    payload
                )
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='CREATE_WORKFLOW',
                    resource='WORKFLOW',
                    resource_id=workflow_id,
                    details={
                        'workflowType': workflow_type,
                        'timeoutAt': timeout_at,
                        'payloadKeys': list(payload.keys()) if payload else []
                    },
                    request_context=self.request_context,
                    after_state=workflow_record
                )
                
                # Send initial notification
                self._send_workflow_notification(
                    workflow_id,
                    WorkflowState.PENDING_APPROVAL.value,
                    'created',
                    payload
                )
                
                # Schedule timeout check
                self._schedule_timeout_check(workflow_id, timeout_at)
                
                logger.info(
                    "Workflow created successfully",
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    timeout_at=timeout_at,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'workflowType': workflow_type,
                    'currentState': WorkflowState.PENDING_APPROVAL.value,
                    'timeoutAt': timeout_at,
                    'createdAt': timestamp
                }
                
            except Exception as e:
                logger.error(
                    "Failed to create workflow",
                    error=str(e),
                    workflow_type=workflow_type,
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to create workflow: {str(e)}")
    
    def transition_workflow(self, workflow_id: str, action: str, justification: str, 
                          additional_data: Optional[Dict] = None) -> Dict:
        """
        Transition workflow to new state based on action
        
        Args:
            workflow_id: Workflow ID to transition
            action: Action to perform (APPROVE, REJECT, etc.)
            justification: Mandatory justification for the action
            additional_data: Optional additional data for the transition
            
        Returns:
            Updated workflow status
            
        Raises:
            WorkflowServiceError: If transition fails
        """
        with TimedOperation(logger, "transition_workflow"):
            try:
                # Validate action
                try:
                    wf_action = WorkflowAction(action)
                except ValueError:
                    raise WorkflowServiceError(f"Invalid workflow action: {action}")
                
                if not justification:
                    raise WorkflowServiceError("Justification is required for workflow transitions")
                
                # Get current workflow
                response = workflows_table.get_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise WorkflowServiceError(f"Workflow {workflow_id} not found")
                
                current_workflow = response['Item']
                current_state = WorkflowState(current_workflow['currentState'])
                
                # Determine new state based on action
                new_state = self._determine_new_state(current_state, wf_action)
                
                # Validate state transition
                if not WorkflowStateMachine.is_valid_transition(current_state, new_state):
                    raise WorkflowServiceError(
                        f"Invalid transition from {current_state.value} to {new_state.value}"
                    )
                
                # Prepare rollback data before making changes
                rollback_data = self._prepare_rollback_data(current_workflow, additional_data)
                
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Update workflow state
                updated_workflow = workflows_table.update_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'},
                    UpdateExpression='''
                        SET currentState = :new_state,
                            updatedAt = :timestamp,
                            lastActionBy = :user_id,
                            lastActionAt = :timestamp,
                            lastJustification = :justification,
                            rollbackData = :rollback_data,
                            GSI1SK = :gsi1sk
                    ''',
                    ExpressionAttributeValues={
                        ':new_state': new_state.value,
                        ':timestamp': timestamp,
                        ':user_id': self.user_id,
                        ':justification': justification,
                        ':rollback_data': rollback_data,
                        ':gsi1sk': f"STATE#{new_state.value}#{timestamp}"
                    },
                    ReturnValues='ALL_NEW'
                )
                
                # Create state audit entry
                self._create_state_audit_entry(
                    workflow_id,
                    current_state.value,
                    new_state.value,
                    action,
                    justification,
                    additional_data
                )
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action=f'WORKFLOW_{action}',
                    resource='WORKFLOW',
                    resource_id=workflow_id,
                    details={
                        'fromState': current_state.value,
                        'toState': new_state.value,
                        'justification': justification,
                        'workflowType': current_workflow['workflowType']
                    },
                    request_context=self.request_context,
                    before_state=current_workflow,
                    after_state=updated_workflow['Attributes']
                )
                
                # Handle post-transition actions
                self._handle_post_transition_actions(
                    workflow_id,
                    current_workflow,
                    new_state,
                    action,
                    justification,
                    additional_data
                )
                
                # Send notification for state change
                self._send_workflow_notification(
                    workflow_id,
                    new_state.value,
                    action.lower(),
                    current_workflow['payload'],
                    justification
                )
                
                logger.info(
                    "Workflow transitioned successfully",
                    workflow_id=workflow_id,
                    from_state=current_state.value,
                    to_state=new_state.value,
                    action=action,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'previousState': current_state.value,
                    'currentState': new_state.value,
                    'action': action,
                    'actionBy': self.user_id,
                    'actionAt': timestamp,
                    'justification': justification
                }
                
            except Exception as e:
                logger.error(
                    "Failed to transition workflow",
                    workflow_id=workflow_id,
                    action=action,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to transition workflow: {str(e)}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """
        Get current workflow status and history
        
        Args:
            workflow_id: Workflow ID to query
            
        Returns:
            Workflow status and history
        """
        with TimedOperation(logger, "get_workflow_status"):
            try:
                # Get current workflow
                response = workflows_table.get_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise WorkflowServiceError(f"Workflow {workflow_id} not found")
                
                workflow = self._convert_decimals(response['Item'])
                
                # Get state history
                state_history = self._get_workflow_audit_trail(workflow_id)
                
                # Calculate workflow metrics
                metrics = self._calculate_workflow_metrics(workflow, state_history)
                
                logger.info(
                    "Retrieved workflow status",
                    workflow_id=workflow_id,
                    current_state=workflow['currentState'],
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'workflowType': workflow['workflowType'],
                    'currentState': workflow['currentState'],
                    'createdBy': workflow['createdBy'],
                    'createdAt': workflow['createdAt'],
                    'updatedAt': workflow['updatedAt'],
                    'timeoutAt': workflow.get('timeoutAt'),
                    'lastActionBy': workflow.get('lastActionBy'),
                    'lastActionAt': workflow.get('lastActionAt'),
                    'lastJustification': workflow.get('lastJustification'),
                    'payload': workflow['payload'],
                    'metadata': workflow.get('metadata', {}),
                    'stateHistory': state_history,
                    'metrics': metrics,
                    'isTerminal': WorkflowStateMachine.is_terminal_state(
                        WorkflowState(workflow['currentState'])
                    )
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get workflow status",
                    workflow_id=workflow_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to get workflow status: {str(e)}")
    
    def handle_workflow_timeout(self, workflow_id: str) -> Dict:
        """
        Handle workflow timeout with escalation to finance controller
        
        Args:
            workflow_id: Workflow ID that timed out
            
        Returns:
            Timeout handling result
        """
        with TimedOperation(logger, "handle_workflow_timeout"):
            try:
                # Get current workflow
                response = workflows_table.get_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise WorkflowServiceError(f"Workflow {workflow_id} not found")
                
                workflow = response['Item']
                current_state = WorkflowState(workflow['currentState'])
                
                # Only handle timeout for pending workflows
                if current_state != WorkflowState.PENDING_APPROVAL:
                    logger.info(
                        "Workflow not in pending state, skipping timeout",
                        workflow_id=workflow_id,
                        current_state=current_state.value,
                        correlation_id=self.correlation_id
                    )
                    return {
                        'workflowId': workflow_id,
                        'action': 'skipped',
                        'reason': f'Workflow in {current_state.value} state'
                    }
                
                # Check if timeout is actually reached
                timeout_at = datetime.fromisoformat(workflow['timeoutAt'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                
                if now < timeout_at:
                    logger.info(
                        "Workflow timeout not yet reached",
                        workflow_id=workflow_id,
                        timeout_at=workflow['timeoutAt'],
                        correlation_id=self.correlation_id
                    )
                    return {
                        'workflowId': workflow_id,
                        'action': 'not_ready',
                        'timeoutAt': workflow['timeoutAt']
                    }
                
                # Transition to timeout escalated state
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                workflows_table.update_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'},
                    UpdateExpression='''
                        SET currentState = :new_state,
                            updatedAt = :timestamp,
                            timeoutHandledAt = :timestamp,
                            timeoutHandledBy = :system,
                            GSI1SK = :gsi1sk
                    ''',
                    ExpressionAttributeValues={
                        ':new_state': WorkflowState.TIMEOUT_ESCALATED.value,
                        ':timestamp': timestamp,
                        ':system': 'system-timeout-handler',
                        ':gsi1sk': f"STATE#{WorkflowState.TIMEOUT_ESCALATED.value}#{timestamp}"
                    }
                )
                
                # Create state audit entry
                self._create_state_audit_entry(
                    workflow_id,
                    current_state.value,
                    WorkflowState.TIMEOUT_ESCALATED.value,
                    WorkflowAction.TIMEOUT.value,
                    f"Workflow timed out after {workflow['timeoutAt']}",
                    {'originalTimeout': workflow['timeoutAt']}
                )
                
                # Send escalation notifications
                escalation_result = self._escalate_to_finance_controller(workflow_id, workflow)
                
                # Log audit event
                audit_logger.log_system_event(
                    event_type='WORKFLOW_TIMEOUT_ESCALATION',
                    resource='WORKFLOW',
                    resource_id=workflow_id,
                    details={
                        'originalTimeout': workflow['timeoutAt'],
                        'workflowType': workflow['workflowType'],
                        'escalatedTo': 'FINANCE_CONTROLLER',
                        'escalationResult': escalation_result
                    },
                    request_context={'correlation_id': self.correlation_id}
                )
                
                logger.warning(
                    "Workflow timed out and escalated",
                    workflow_id=workflow_id,
                    original_timeout=workflow['timeoutAt'],
                    escalation_result=escalation_result,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'action': 'escalated',
                    'escalatedAt': timestamp,
                    'originalTimeout': workflow['timeoutAt'],
                    'escalationResult': escalation_result
                }
                
            except Exception as e:
                logger.error(
                    "Failed to handle workflow timeout",
                    workflow_id=workflow_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to handle workflow timeout: {str(e)}")
    
    def rollback_workflow(self, workflow_id: str, rollback_reason: str) -> Dict:
        """
        Rollback workflow to previous state using stored rollback data
        
        Args:
            workflow_id: Workflow ID to rollback
            rollback_reason: Reason for rollback
            
        Returns:
            Rollback result
        """
        with TimedOperation(logger, "rollback_workflow"):
            try:
                # Get current workflow
                response = workflows_table.get_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
                )
                
                if 'Item' not in response:
                    raise WorkflowServiceError(f"Workflow {workflow_id} not found")
                
                workflow = response['Item']
                current_state = WorkflowState(workflow['currentState'])
                
                # Check if rollback is allowed
                if WorkflowStateMachine.is_terminal_state(current_state):
                    raise WorkflowServiceError(
                        f"Cannot rollback workflow in terminal state: {current_state.value}"
                    )
                
                rollback_data = workflow.get('rollbackData', {})
                if not rollback_data:
                    raise WorkflowServiceError("No rollback data available for this workflow")
                
                # Perform rollback operations
                rollback_results = self._execute_rollback_operations(workflow_id, rollback_data)
                
                # Transition back to previous state
                previous_state = rollback_data.get('previousState', WorkflowState.PENDING_APPROVAL.value)
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                workflows_table.update_item(
                    Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'},
                    UpdateExpression='''
                        SET currentState = :previous_state,
                            updatedAt = :timestamp,
                            rolledBackAt = :timestamp,
                            rolledBackBy = :user_id,
                            rollbackReason = :reason,
                            GSI1SK = :gsi1sk
                    ''',
                    ExpressionAttributeValues={
                        ':previous_state': previous_state,
                        ':timestamp': timestamp,
                        ':user_id': self.user_id,
                        ':reason': rollback_reason,
                        ':gsi1sk': f"STATE#{previous_state}#{timestamp}"
                    }
                )
                
                # Create rollback audit entry
                self._create_state_audit_entry(
                    workflow_id,
                    current_state.value,
                    previous_state,
                    'ROLLBACK',
                    rollback_reason,
                    {'rollbackResults': rollback_results}
                )
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='ROLLBACK_WORKFLOW',
                    resource='WORKFLOW',
                    resource_id=workflow_id,
                    details={
                        'fromState': current_state.value,
                        'toState': previous_state,
                        'rollbackReason': rollback_reason,
                        'rollbackResults': rollback_results
                    },
                    request_context=self.request_context
                )
                
                # Send rollback notification
                self._send_workflow_notification(
                    workflow_id,
                    previous_state,
                    'rolled_back',
                    workflow['payload'],
                    rollback_reason
                )
                
                logger.info(
                    "Workflow rolled back successfully",
                    workflow_id=workflow_id,
                    from_state=current_state.value,
                    to_state=previous_state,
                    rollback_reason=rollback_reason,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'rolledBackFrom': current_state.value,
                    'rolledBackTo': previous_state,
                    'rolledBackAt': timestamp,
                    'rollbackReason': rollback_reason,
                    'rollbackResults': rollback_results
                }
                
            except Exception as e:
                logger.error(
                    "Failed to rollback workflow",
                    workflow_id=workflow_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to rollback workflow: {str(e)}")
    
    def get_workflow_audit_trail(self, workflow_id: str, filters: Optional[Dict] = None) -> Dict:
        """
        Get comprehensive audit trail for workflow
        
        Args:
            workflow_id: Workflow ID to query
            filters: Optional filters for audit entries
            
        Returns:
            Workflow audit trail
        """
        with TimedOperation(logger, "get_workflow_audit_trail"):
            try:
                audit_entries = self._get_workflow_audit_trail(workflow_id, filters)
                
                logger.info(
                    "Retrieved workflow audit trail",
                    workflow_id=workflow_id,
                    entry_count=len(audit_entries),
                    correlation_id=self.correlation_id
                )
                
                return {
                    'workflowId': workflow_id,
                    'auditEntries': audit_entries,
                    'entryCount': len(audit_entries),
                    'filters': filters or {}
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get workflow audit trail",
                    workflow_id=workflow_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise WorkflowServiceError(f"Failed to get workflow audit trail: {str(e)}")
    
    # Private helper methods
    
    def _determine_new_state(self, current_state: WorkflowState, action: WorkflowAction) -> WorkflowState:
        """Determine new state based on current state and action"""
        state_action_map = {
            (WorkflowState.PENDING_APPROVAL, WorkflowAction.APPROVE): WorkflowState.APPROVED,
            (WorkflowState.PENDING_APPROVAL, WorkflowAction.REJECT): WorkflowState.REJECTED,
            (WorkflowState.PENDING_APPROVAL, WorkflowAction.ESCALATE): WorkflowState.TIMEOUT_ESCALATED,
            (WorkflowState.PENDING_APPROVAL, WorkflowAction.CANCEL): WorkflowState.CANCELLED,
            (WorkflowState.TIMEOUT_ESCALATED, WorkflowAction.APPROVE): WorkflowState.APPROVED,
            (WorkflowState.TIMEOUT_ESCALATED, WorkflowAction.REJECT): WorkflowState.REJECTED,
            (WorkflowState.TIMEOUT_ESCALATED, WorkflowAction.CANCEL): WorkflowState.CANCELLED,
            (WorkflowState.APPROVED, WorkflowAction.COMPLETE): WorkflowState.COMPLETED,
            (WorkflowState.FAILED, WorkflowAction.APPROVE): WorkflowState.PENDING_APPROVAL,
        }
        
        new_state = state_action_map.get((current_state, action))
        if not new_state:
            raise WorkflowServiceError(
                f"No state mapping for {current_state.value} + {action.value}"
            )
        
        return new_state
    
    def _prepare_rollback_data(self, workflow: Dict, additional_data: Optional[Dict]) -> Dict:
        """Prepare rollback data for potential future rollback"""
        rollback_data = {
            'previousState': workflow['currentState'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'userId': self.user_id,
            'correlationId': self.correlation_id
        }
        
        # Add workflow-specific rollback data
        if workflow['workflowType'] == WorkflowType.PURCHASE_APPROVAL.value:
            rollback_data['purchaseOrderData'] = additional_data or {}
        
        return rollback_data
    
    def _create_state_audit_entry(self, workflow_id: str, from_state: Optional[str], 
                                to_state: str, action: str, justification: str, 
                                additional_data: Optional[Dict]) -> None:
        """Create audit entry for state transition"""
        try:
            audit_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            audit_entry = {
                'PK': f"WORKFLOW#{workflow_id}",
                'SK': f"AUDIT#{timestamp}#{audit_id}",
                'auditId': audit_id,
                'workflowId': workflow_id,
                'fromState': from_state,
                'toState': to_state,
                'action': action,
                'justification': justification,
                'userId': self.user_id,
                'timestamp': timestamp,
                'correlationId': self.correlation_id,
                'additionalData': additional_data or {},
                'GSI1PK': f"AUDIT#{workflow_id}",
                'GSI1SK': f"TIMESTAMP#{timestamp}"
            }
            
            workflows_table.put_item(Item=audit_entry)
            
        except Exception as e:
            logger.error(
                "Failed to create state audit entry",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical for main operation
    
    def _handle_post_transition_actions(self, workflow_id: str, workflow: Dict, 
                                      new_state: WorkflowState, action: str, 
                                      justification: str, additional_data: Optional[Dict]) -> None:
        """Handle actions that need to occur after state transition"""
        try:
            # Handle purchase order workflow specific actions
            if workflow['workflowType'] == WorkflowType.PURCHASE_APPROVAL.value:
                self._handle_purchase_order_actions(
                    workflow_id, workflow, new_state, action, additional_data
                )
            
            # Handle budget allocation workflow specific actions
            elif workflow['workflowType'] == WorkflowType.BUDGET_ALLOCATION.value:
                self._handle_budget_allocation_actions(
                    workflow_id, workflow, new_state, action, additional_data
                )
            
        except Exception as e:
            logger.error(
                "Failed to handle post-transition actions",
                workflow_id=workflow_id,
                new_state=new_state.value,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as main transition is complete
    
    def _handle_purchase_order_actions(self, workflow_id: str, workflow: Dict, 
                                     new_state: WorkflowState, action: str, 
                                     additional_data: Optional[Dict]) -> None:
        """Handle purchase order specific post-transition actions"""
        try:
            order_id = workflow['payload'].get('orderId')
            if not order_id:
                return
            
            # Update purchase order status based on workflow state
            if new_state == WorkflowState.APPROVED:
                self._update_purchase_order_status(order_id, 'APPROVED', workflow_id)
            elif new_state == WorkflowState.REJECTED:
                self._update_purchase_order_status(order_id, 'REJECTED', workflow_id)
            elif new_state == WorkflowState.CANCELLED:
                self._update_purchase_order_status(order_id, 'CANCELLED', workflow_id)
            
        except Exception as e:
            logger.error(
                "Failed to handle purchase order actions",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
    
    def _handle_budget_allocation_actions(self, workflow_id: str, workflow: Dict, 
                                        new_state: WorkflowState, action: str, 
                                        additional_data: Optional[Dict]) -> None:
        """Handle budget allocation specific post-transition actions"""
        try:
            # Implement budget allocation specific logic
            # This would integrate with the budget service
            pass
            
        except Exception as e:
            logger.error(
                "Failed to handle budget allocation actions",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
    
    def _update_purchase_order_status(self, order_id: str, status: str, workflow_id: str) -> None:
        """Update purchase order status"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            purchase_orders_table.update_item(
                Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'},
                UpdateExpression='''
                    SET #status = :status,
                        updatedAt = :timestamp,
                        workflowCompletedAt = :timestamp
                ''',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':timestamp': timestamp
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to update purchase order status",
                order_id=order_id,
                status=status,
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
    
    def _escalate_to_finance_controller(self, workflow_id: str, workflow: Dict) -> Dict:
        """Escalate workflow to finance controller"""
        try:
            # Get finance controllers
            finance_controllers = self._get_finance_controllers()
            
            escalation_results = []
            
            for controller in finance_controllers:
                try:
                    # Send escalation notification
                    notification_result = self._send_escalation_notification(
                        controller, workflow_id, workflow
                    )
                    escalation_results.append({
                        'userId': controller['userId'],
                        'status': 'notified',
                        'notificationResult': notification_result
                    })
                    
                except Exception as e:
                    escalation_results.append({
                        'userId': controller['userId'],
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Send to escalation topic if configured
            if self.escalation_topic:
                try:
                    sns.publish(
                        TopicArn=self.escalation_topic,
                        Subject=f"Workflow Timeout Escalation: {workflow_id}",
                        Message=json.dumps({
                            'workflowId': workflow_id,
                            'workflowType': workflow['workflowType'],
                            'originalTimeout': workflow['timeoutAt'],
                            'escalatedAt': datetime.utcnow().isoformat() + 'Z',
                            'payload': workflow['payload']
                        })
                    )
                    escalation_results.append({
                        'channel': 'sns_topic',
                        'status': 'sent'
                    })
                    
                except Exception as e:
                    escalation_results.append({
                        'channel': 'sns_topic',
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'escalatedTo': len(finance_controllers),
                'results': escalation_results
            }
            
        except Exception as e:
            logger.error(
                "Failed to escalate to finance controller",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {'escalatedTo': 0, 'error': str(e)}
    
    def _get_finance_controllers(self) -> List[Dict]:
        """Get list of finance controllers for escalation - OPTIMIZED"""
        try:
            # Use GSI instead of expensive scan
            response = get_users_table().query(
                IndexName='GSI-Role-Index',  # Assumes role-based GSI exists
                KeyConditionExpression='#role = :role',
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={':role': 'FINANCE_CONTROLLER'},
                Limit=10  # Reasonable limit for finance controllers
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(
                "Failed to get finance controllers",
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Fallback to environment variable if query fails
            fallback_controllers = os.environ.get('FINANCE_CONTROLLER_IDS', '').split(',')
            return [{'userId': uid.strip()} for uid in fallback_controllers if uid.strip()]
    
    def _send_escalation_notification(self, controller: Dict, workflow_id: str, workflow: Dict) -> Dict:
        """Send escalation notification to finance controller"""
        try:
            if not self.notification_service_function:
                return {'status': 'skipped', 'reason': 'No notification service configured'}
            
            notification_payload = {
                'action': 'send_system_notification',
                'systemNotification': {
                    'notificationType': 'workflow_timeout_escalation',
                    'targetUserId': controller['userId'],
                    'workflowId': workflow_id,
                    'workflowType': workflow['workflowType'],
                    'originalTimeout': workflow['timeoutAt'],
                    'payload': workflow['payload'],
                    'urgency': 'high'
                }
            }
            
            response = lambda_client.invoke(
                FunctionName=self.notification_service_function,
                InvocationType='Event',  # Async
                Payload=json.dumps(notification_payload)
            )
            
            return {'status': 'sent', 'messageId': response.get('MessageId')}
            
        except Exception as e:
            logger.error(
                "Failed to send escalation notification",
                controller_id=controller.get('userId'),
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {'status': 'failed', 'error': str(e)}
    
    def _send_workflow_notification(self, workflow_id: str, state: str, action: str, 
                                  payload: Dict, justification: Optional[str] = None) -> None:
        """Send workflow status change notification"""
        try:
            if not self.notification_topic:
                return
            
            message = {
                'workflowId': workflow_id,
                'state': state,
                'action': action,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'payload': payload,
                'justification': justification,
                'correlationId': self.correlation_id
            }
            
            sns.publish(
                TopicArn=self.notification_topic,
                Subject=f"Workflow {action.title()}: {workflow_id}",
                Message=json.dumps(message)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send workflow notification",
                workflow_id=workflow_id,
                state=state,
                action=action,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical
    
    def _schedule_timeout_check(self, workflow_id: str, timeout_at: str) -> None:
        """Schedule timeout check using EventBridge"""
        try:
            # Create EventBridge rule for timeout
            rule_name = f"workflow-timeout-{workflow_id}"
            
            # Convert timeout to EventBridge schedule expression
            timeout_dt = datetime.fromisoformat(timeout_at.replace('Z', '+00:00'))
            
            eventbridge.put_rule(
                Name=rule_name,
                ScheduleExpression=f"at({timeout_dt.strftime('%Y-%m-%dT%H:%M:%S')})",
                State='ENABLED',
                Description=f"Timeout check for workflow {workflow_id}"
            )
            
            # Add target to invoke this Lambda function
            eventbridge.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': f"arn:aws:lambda:{os.environ.get('AWS_REGION')}:{os.environ.get('AWS_ACCOUNT_ID')}:function:{os.environ.get('AWS_LAMBDA_FUNCTION_NAME')}",
                        'Input': json.dumps({
                            'action': 'handle_timeout',
                            'workflowId': workflow_id,
                            'scheduledTimeout': timeout_at
                        })
                    }
                ]
            )
            
        except Exception as e:
            logger.error(
                "Failed to schedule timeout check",
                workflow_id=workflow_id,
                timeout_at=timeout_at,
                error=str(e),
                correlation_id=self.correlation_id
            )
            # Don't raise exception as this is not critical for workflow creation
    
    def _get_workflow_audit_trail(self, workflow_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Get workflow audit trail entries"""
        try:
            query_params = {
                'KeyConditionExpression': 'PK = :pk AND begins_with(SK, :sk_prefix)',
                'ExpressionAttributeValues': {
                    ':pk': f"WORKFLOW#{workflow_id}",
                    ':sk_prefix': 'AUDIT#'
                },
                'ScanIndexForward': False  # Most recent first
            }
            
            # Add filters if provided
            if filters:
                filter_expressions = []
                
                if filters.get('fromDate'):
                    filter_expressions.append('timestamp >= :from_date')
                    query_params['ExpressionAttributeValues'][':from_date'] = filters['fromDate']
                
                if filters.get('toDate'):
                    filter_expressions.append('timestamp <= :to_date')
                    query_params['ExpressionAttributeValues'][':to_date'] = filters['toDate']
                
                if filters.get('action'):
                    filter_expressions.append('action = :action')
                    query_params['ExpressionAttributeValues'][':action'] = filters['action']
                
                if filter_expressions:
                    query_params['FilterExpression'] = ' AND '.join(filter_expressions)
            
            response = workflows_table.query(**query_params)
            
            # Convert and return audit entries
            audit_entries = []
            for item in response['Items']:
                entry = self._convert_decimals(item)
                audit_entries.append(entry)
            
            return audit_entries
            
        except Exception as e:
            logger.error(
                "Failed to get workflow audit trail",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return []
    
    def _calculate_workflow_metrics(self, workflow: Dict, audit_entries: List[Dict]) -> Dict:
        """Calculate workflow performance metrics"""
        try:
            created_at = datetime.fromisoformat(workflow['createdAt'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            metrics = {
                'totalDuration': (now - created_at).total_seconds(),
                'stateTransitions': len(audit_entries),
                'averageStateTime': 0,
                'timeInCurrentState': 0
            }
            
            # Calculate time in current state
            if workflow.get('updatedAt'):
                updated_at = datetime.fromisoformat(workflow['updatedAt'].replace('Z', '+00:00'))
                metrics['timeInCurrentState'] = (now - updated_at).total_seconds()
            
            # Calculate average state time
            if len(audit_entries) > 1:
                total_state_time = 0
                for i in range(len(audit_entries) - 1):
                    current_time = datetime.fromisoformat(audit_entries[i]['timestamp'].replace('Z', '+00:00'))
                    next_time = datetime.fromisoformat(audit_entries[i + 1]['timestamp'].replace('Z', '+00:00'))
                    total_state_time += (current_time - next_time).total_seconds()
                
                metrics['averageStateTime'] = total_state_time / (len(audit_entries) - 1)
            
            return metrics
            
        except Exception as e:
            logger.error(
                "Failed to calculate workflow metrics",
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {}
    
    def _execute_rollback_operations(self, workflow_id: str, rollback_data: Dict) -> Dict:
        """Execute rollback operations based on rollback data"""
        try:
            rollback_results = {'operations': []}
            
            # Handle purchase order rollback
            if 'purchaseOrderData' in rollback_data:
                try:
                    # Rollback purchase order changes
                    order_data = rollback_data['purchaseOrderData']
                    if order_data.get('orderId'):
                        self._rollback_purchase_order(order_data['orderId'], rollback_data)
                        rollback_results['operations'].append({
                            'type': 'purchase_order_rollback',
                            'status': 'success'
                        })
                except Exception as e:
                    rollback_results['operations'].append({
                        'type': 'purchase_order_rollback',
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Handle budget rollback
            if 'budgetData' in rollback_data:
                try:
                    # Rollback budget changes
                    budget_data = rollback_data['budgetData']
                    self._rollback_budget_changes(budget_data, rollback_data)
                    rollback_results['operations'].append({
                        'type': 'budget_rollback',
                        'status': 'success'
                    })
                except Exception as e:
                    rollback_results['operations'].append({
                        'type': 'budget_rollback',
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return rollback_results
            
        except Exception as e:
            logger.error(
                "Failed to execute rollback operations",
                workflow_id=workflow_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {'operations': [], 'error': str(e)}
    
    def _rollback_purchase_order(self, order_id: str, rollback_data: Dict) -> None:
        """Rollback purchase order to previous state"""
        try:
            # Reset purchase order to pending state
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            purchase_orders_table.update_item(
                Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'},
                UpdateExpression='''
                    SET #status = :status,
                        updatedAt = :timestamp,
                        rolledBackAt = :timestamp,
                        rolledBackBy = :user_id
                ''',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PENDING',
                    ':timestamp': timestamp,
                    ':user_id': self.user_id
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to rollback purchase order",
                order_id=order_id,
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise
    
    def _rollback_budget_changes(self, budget_data: Dict, rollback_data: Dict) -> None:
        """Rollback budget allocation changes"""
        try:
            # Implement budget rollback logic
            # This would integrate with the budget service
            pass
            
        except Exception as e:
            logger.error(
                "Failed to rollback budget changes",
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise
    
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
    Main Lambda handler for workflow service
    
    Supported actions:
    - create_workflow
    - transition_workflow
    - get_workflow_status
    - handle_timeout
    - rollback_workflow
    - get_audit_trail
    """
    try:
        # Extract request context
        request_context = {
            'user_id': event.get('requestContext', {}).get('authorizer', {}).get('userId', 'system'),
            'username': event.get('requestContext', {}).get('authorizer', {}).get('username', 'unknown'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4())),
            'ipAddress': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'userAgent': event.get('headers', {}).get('User-Agent', 'unknown')
        }
        
        # Initialize service
        service = WorkflowService(request_context)
        
        # Parse request body
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        action = body.get('action') or event.get('pathParameters', {}).get('action')
        
        # Handle scheduled timeout events
        if event.get('source') == 'aws.events' and action == 'handle_timeout':
            workflow_id = event.get('workflowId')
            result = service.handle_workflow_timeout(workflow_id)
        
        # Route to appropriate method
        elif action == 'create_workflow':
            # Validate RBAC permissions for workflow creation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'workflow-management',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for workflow creation",
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
                        'resource': 'workflow-management',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.create_workflow(
                body.get('workflowType'),
                body.get('payload', {}),
                body.get('metadata', {})
            )
            
        elif action == 'transition_workflow':
            # Validate RBAC permissions for workflow transitions
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'workflow-management',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for workflow transition",
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
                        'resource': 'workflow-management',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            workflow_id = body.get('workflowId') or event.get('pathParameters', {}).get('workflowId')
            result = service.transition_workflow(
                workflow_id,
                body.get('workflowAction'),
                body.get('justification'),
                body.get('additionalData', {})
            )
            
        elif action == 'get_workflow_status':
            # Validate RBAC permissions for workflow status viewing
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'workflow-management',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for workflow status viewing",
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
                        'resource': 'workflow-management',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            workflow_id = body.get('workflowId') or event.get('pathParameters', {}).get('workflowId')
            result = service.get_workflow_status(workflow_id)
            
        elif action == 'rollback_workflow':
            # Validate RBAC permissions for workflow rollback
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'workflow-management',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for workflow rollback",
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
                        'resource': 'workflow-management',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            workflow_id = body.get('workflowId') or event.get('pathParameters', {}).get('workflowId')
            result = service.rollback_workflow(workflow_id, body.get('rollbackReason'))
            
        elif action == 'get_audit_trail':
            # Validate RBAC permissions for audit trail access
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'audit-trails',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for workflow audit trail access",
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
            
            workflow_id = body.get('workflowId') or event.get('pathParameters', {}).get('workflowId')
            result = service.get_workflow_audit_trail(workflow_id, body.get('filters', {}))
        else:
            raise WorkflowServiceError(f"Unknown action: {action}")
        
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
        
    except WorkflowServiceError as e:
        logger.error(
            "Workflow service error",
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
            "Unexpected error in workflow service",
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