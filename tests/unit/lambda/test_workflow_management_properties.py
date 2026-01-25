"""
Property-based tests for workflow management

Feature: dashboard-overhaul, Property 8: Workflow State Transition Validation
Feature: dashboard-overhaul, Property 13: Workflow Timeout Escalation
Feature: dashboard-overhaul, Property 17: Notification Delivery for Workflow Changes
Validates: Requirements 6.3, 6.6, 6.7, 13.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

# Mock shared modules before importing workflow service
mock_logger = Mock()
mock_timed_operation = Mock()
mock_timed_operation.__enter__ = Mock(return_value=mock_timed_operation)
mock_timed_operation.__exit__ = Mock(return_value=None)

mock_structured_logger = Mock()
mock_structured_logger.get_logger = Mock(return_value=mock_logger)
mock_structured_logger.TimedOperation = Mock(return_value=mock_timed_operation)
mock_structured_logger.SystemHealthMonitor = Mock()

mock_audit_logger = Mock()
mock_audit_logger.audit_logger = Mock()

sys.modules['structured_logger'] = mock_structured_logger
sys.modules['audit_logger'] = mock_audit_logger

from workflow_service.handler import (
    WorkflowService, WorkflowState, WorkflowType, WorkflowAction, 
    WorkflowStateMachine, WorkflowServiceError
)


# Hypothesis strategies for generating test data

# Valid workflow types
workflow_type_strategy = st.sampled_from([
    WorkflowType.PURCHASE_APPROVAL.value,
    WorkflowType.EMERGENCY_PURCHASE_APPROVAL.value,
    WorkflowType.BUDGET_ALLOCATION.value,
    WorkflowType.SUPPLIER_APPROVAL.value
])

# Valid workflow states
workflow_state_strategy = st.sampled_from([
    WorkflowState.PENDING_APPROVAL.value,
    WorkflowState.APPROVED.value,
    WorkflowState.REJECTED.value,
    WorkflowState.TIMEOUT_ESCALATED.value,
    WorkflowState.CANCELLED.value,
    WorkflowState.COMPLETED.value,
    WorkflowState.FAILED.value
])

# Valid workflow actions
workflow_action_strategy = st.sampled_from([
    WorkflowAction.APPROVE.value,
    WorkflowAction.REJECT.value,
    WorkflowAction.ESCALATE.value,
    WorkflowAction.CANCEL.value,
    WorkflowAction.TIMEOUT.value,
    WorkflowAction.COMPLETE.value
])

# User IDs
user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=10,
    max_size=50
)

# Justification text
justification_strategy = st.text(min_size=10, max_size=500)

# Workflow payload data
workflow_payload_strategy = st.fixed_dictionaries({
    'orderId': st.text(min_size=10, max_size=36),
    'supplierId': st.text(min_size=10, max_size=36),
    'totalAmount': st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    'budgetCategory': st.sampled_from(['OPERATIONS', 'MAINTENANCE', 'EQUIPMENT', 'SUPPLIES']),
    'items': st.lists(
        st.fixed_dictionaries({
            'itemId': st.text(min_size=5, max_size=20),
            'quantity': st.integers(min_value=1, max_value=100),
            'unitPrice': st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)
        }),
        min_size=1,
        max_size=5
    )
})

# Request context
request_context_strategy = st.fixed_dictionaries({
    'user_id': user_id_strategy,
    'correlation_id': st.uuids().map(str),
    'ipAddress': st.ip_addresses().map(str),
    'userAgent': st.text(min_size=10, max_size=100)
})

# Finance controller data
finance_controller_strategy = st.fixed_dictionaries({
    'userId': user_id_strategy,
    'email': st.emails(),
    'role': st.just('FINANCE_CONTROLLER'),
    'status': st.just('ACTIVE')
})


class TestWorkflowStateTransitionValidation:
    """
    Property 8: Workflow State Transition Validation
    
    For any workflow state transition, the system SHALL validate the transition is 
    legal according to the workflow definition, require proper authorization for 
    the transition, and maintain rollback capabilities for failed transitions.
    """
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy,
        action=workflow_action_strategy,
        justification=justification_strategy
    )
    @settings(max_examples=1)
    def test_workflow_state_transitions_follow_state_machine_rules(
        self, workflow_type, payload, request_context, action, justification
    ):
        """
        Property Test: All workflow state transitions must follow state machine rules
        
        For any workflow state transition attempt, the system must:
        1. Validate transition is legal according to WorkflowStateMachine
        2. Reject invalid transitions with appropriate error
        3. Allow valid transitions with proper audit logging
        4. Maintain state consistency throughout the process
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.get_lambda_client') as mock_get_lambda, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB table
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other AWS services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            mock_lambda_client = Mock()
            mock_get_lambda.return_value = mock_lambda_client
            
            # Mock successful DynamoDB operations
            mock_table.put_item.return_value = {}
            mock_table.get_item.return_value = {'Item': {}}
            mock_table.update_item.return_value = {'Attributes': {}}
            
            # Patch the global table variables that the service uses
            with patch('workflow_service.handler.workflows_table', mock_table), \
                 patch('workflow_service.handler.purchase_orders_table', mock_table), \
                 patch('workflow_service.handler.users_table', mock_table), \
                 patch('workflow_service.handler.audit_table', mock_table):
            
                # Initialize service
                service = WorkflowService(request_context)
                
                # Create workflow
                create_result = service.create_workflow(workflow_type, payload)
                workflow_id = create_result['workflowId']
                current_state = WorkflowState(create_result['currentState'])
                
                # Mock workflow retrieval for transition
                mock_workflow_item = {
                    'PK': f"WORKFLOW#{workflow_id}",
                    'SK': 'CURRENT',
                    'workflowId': workflow_id,
                    'workflowType': workflow_type,
                    'currentState': current_state.value,
                    'payload': payload,
                    'createdBy': request_context['user_id'],
                    'createdAt': datetime.utcnow().isoformat() + 'Z',
                    'timeoutAt': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z',
                    'rollbackData': {}
                }
                mock_table.get_item.return_value = {'Item': mock_workflow_item}
                
                try:
                    # Determine expected new state based on action
                    wf_action = WorkflowAction(action)
                    expected_new_state = service._determine_new_state(current_state, wf_action)
                    
                    # Check if transition should be valid
                    is_valid_transition = WorkflowStateMachine.is_valid_transition(current_state, expected_new_state)
                    
                    if is_valid_transition:
                        # Valid transition should succeed
                        result = service.transition_workflow(workflow_id, action, justification)
                        
                        # Verify successful transition
                        assert result['workflowId'] == workflow_id
                        assert result['previousState'] == current_state.value
                        assert result['currentState'] == expected_new_state.value
                        assert result['action'] == action
                        assert result['justification'] == justification
                        
                        # Verify DynamoDB update was called
                        mock_table.update_item.assert_called()
                        
                        # Verify audit logging was called
                        mock_audit_logger.log_user_action.assert_called()
                        
                    else:
                        # Invalid transition should fail
                        with pytest.raises(WorkflowServiceError, match="Invalid transition"):
                            service.transition_workflow(workflow_id, action, justification)
                            
                except ValueError:
                    # Invalid action enum value - should be handled gracefully
                    with pytest.raises(WorkflowServiceError, match="Invalid workflow action"):
                        service.transition_workflow(workflow_id, action, justification)
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_workflow_transitions_require_proper_authorization(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: All workflow transitions require proper authorization
        
        For any workflow transition attempt, the system must:
        1. Validate user has permission to perform the action
        2. Record the user who performed the action
        3. Maintain audit trail of authorization checks
        4. Reject unauthorized transitions
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            
            # Mock successful operations
            mock_table.put_item.return_value = {}
            mock_table.update_item.return_value = {'Attributes': {}}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Mock workflow for transition
            mock_workflow_item = {
                'workflowId': workflow_id,
                'currentState': WorkflowState.PENDING_APPROVAL.value,
                'createdBy': request_context['user_id'],
                'payload': payload,
                'rollbackData': {}
            }
            mock_table.get_item.return_value = {'Item': mock_workflow_item}
            
            # Attempt transition
            result = service.transition_workflow(
                workflow_id, 
                WorkflowAction.APPROVE.value, 
                "Test approval"
            )
            
            # Verify authorization was recorded
            assert result['actionBy'] == request_context['user_id']
            
            # Verify audit logging captured authorization
            mock_audit_logger.log_user_action.assert_called()
            audit_call = mock_audit_logger.log_user_action.call_args
            assert audit_call[1]['user_id'] == request_context['user_id']
            assert audit_call[1]['action'] == 'WORKFLOW_APPROVE'
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_workflow_transitions_maintain_rollback_capabilities(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: Workflow transitions maintain rollback capabilities
        
        For any successful workflow transition, the system must:
        1. Store rollback data before making changes
        2. Enable rollback to previous state if needed
        3. Maintain data consistency during rollback
        4. Audit rollback operations
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            
            # Mock successful operations
            mock_table.put_item.return_value = {}
            mock_table.update_item.return_value = {'Attributes': {}}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Mock workflow for transition
            initial_state = WorkflowState.PENDING_APPROVAL.value
            mock_workflow_item = {
                'workflowId': workflow_id,
                'currentState': initial_state,
                'createdBy': request_context['user_id'],
                'payload': payload,
                'rollbackData': {}
            }
            mock_table.get_item.return_value = {'Item': mock_workflow_item}
            
            # Perform transition (approve)
            service.transition_workflow(
                workflow_id, 
                WorkflowAction.APPROVE.value, 
                "Test approval"
            )
            
            # Verify rollback data was stored in update call
            update_call = mock_table.update_item.call_args
            update_expression = update_call[1]['UpdateExpression']
            assert 'rollbackData' in update_expression
            
            # Mock approved workflow for rollback test
            approved_workflow_item = {
                'workflowId': workflow_id,
                'currentState': WorkflowState.APPROVED.value,
                'createdBy': request_context['user_id'],
                'payload': payload,
                'rollbackData': {
                    'previousState': initial_state,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'userId': request_context['user_id']
                }
            }
            mock_table.get_item.return_value = {'Item': approved_workflow_item}
            
            # Test rollback capability
            rollback_result = service.rollback_workflow(workflow_id, "Test rollback")
            
            # Verify rollback succeeded
            assert rollback_result['workflowId'] == workflow_id
            assert rollback_result['rolledBackFrom'] == WorkflowState.APPROVED.value
            assert rollback_result['rolledBackTo'] == initial_state
            assert rollback_result['rollbackReason'] == "Test rollback"
            
            # Verify rollback was audited
            mock_audit_logger.log_user_action.assert_called()


class TestWorkflowTimeoutEscalation:
    """
    Property 13: Workflow Timeout Escalation
    
    For any approval workflow that exceeds defined timeout periods, the system 
    SHALL automatically escalate to the Procurement & Finance Controller, send 
    timeout notifications to relevant stakeholders, and log the escalation event 
    with complete audit details.
    """
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy,
        finance_controllers=st.lists(finance_controller_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=1)
    def test_workflow_timeout_triggers_automatic_escalation(
        self, workflow_type, payload, request_context, finance_controllers
    ):
        """
        Property Test: Workflow timeout triggers automatic escalation
        
        For any workflow that exceeds its timeout period, the system must:
        1. Automatically transition to TIMEOUT_ESCALATED state
        2. Send notifications to all finance controllers
        3. Log escalation event with complete audit details
        4. Maintain workflow data integrity during escalation
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.get_lambda_client') as mock_get_lambda, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB
            mock_workflows_table = Mock()
            mock_users_table = Mock()
            mock_dynamodb = Mock()
            
            def table_factory(name):
                if 'Workflows' in name:
                    return mock_workflows_table
                elif 'Users' in name:
                    return mock_users_table
                return Mock()
            
            mock_dynamodb.Table.side_effect = table_factory
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            mock_lambda_client = Mock()
            mock_get_lambda.return_value = mock_lambda_client
            
            # Mock successful operations
            mock_workflows_table.put_item.return_value = {}
            mock_workflows_table.update_item.return_value = {'Attributes': {}}
            
            # Mock finance controllers query
            mock_users_table.query.return_value = {'Items': finance_controllers}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Mock workflow that has timed out
            past_timeout = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
            timed_out_workflow = {
                'workflowId': workflow_id,
                'workflowType': workflow_type,
                'currentState': WorkflowState.PENDING_APPROVAL.value,
                'payload': payload,
                'createdBy': request_context['user_id'],
                'timeoutAt': past_timeout,
                'createdAt': (datetime.utcnow() - timedelta(hours=25)).isoformat() + 'Z'
            }
            mock_workflows_table.get_item.return_value = {'Item': timed_out_workflow}
            
            # Handle timeout
            timeout_result = service.handle_workflow_timeout(workflow_id)
            
            # Verify escalation occurred
            assert timeout_result['workflowId'] == workflow_id
            assert timeout_result['action'] == 'escalated'
            assert 'escalatedAt' in timeout_result
            assert timeout_result['originalTimeout'] == past_timeout
            
            # Verify workflow state was updated to TIMEOUT_ESCALATED
            update_calls = mock_workflows_table.update_item.call_args_list
            state_update_call = None
            for call in update_calls:
                if 'currentState' in call[1]['UpdateExpression']:
                    state_update_call = call
                    break
            
            assert state_update_call is not None
            assert state_update_call[1]['ExpressionAttributeValues'][':new_state'] == WorkflowState.TIMEOUT_ESCALATED.value
            
            # Verify escalation was audited
            mock_audit_logger.log_system_event.assert_called()
            audit_call = mock_audit_logger.log_system_event.call_args
            assert audit_call[1]['event_type'] == 'WORKFLOW_TIMEOUT_ESCALATION'
            assert audit_call[1]['resource_id'] == workflow_id
            
            # Verify escalation results include finance controllers
            escalation_result = timeout_result['escalationResult']
            assert escalation_result['escalatedTo'] == len(finance_controllers)
            assert 'results' in escalation_result
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_timeout_escalation_sends_notifications_to_stakeholders(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: Timeout escalation sends notifications to stakeholders
        
        For any workflow timeout escalation, the system must:
        1. Send notifications to all finance controllers
        2. Include complete workflow context in notifications
        3. Use appropriate notification channels (SNS, Lambda)
        4. Handle notification failures gracefully
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_lambda_client') as mock_get_lambda, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger, \
             patch.dict(os.environ, {
                 'ESCALATION_NOTIFICATIONS_TOPIC': 'arn:aws:sns:us-east-1:123456789012:escalation-topic',
                 'NOTIFICATION_SERVICE_FUNCTION': 'notification-service'
             }):
            
            # Mock DynamoDB
            mock_workflows_table = Mock()
            mock_users_table = Mock()
            mock_dynamodb = Mock()
            
            def table_factory(name):
                if 'Workflows' in name:
                    return mock_workflows_table
                elif 'Users' in name:
                    return mock_users_table
                return Mock()
            
            mock_dynamodb.Table.side_effect = table_factory
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_lambda_client = Mock()
            mock_get_lambda.return_value = mock_lambda_client
            
            # Mock successful operations
            mock_workflows_table.put_item.return_value = {}
            mock_workflows_table.update_item.return_value = {'Attributes': {}}
            
            # Mock finance controllers
            finance_controllers = [
                {'userId': 'fc-1', 'email': 'fc1@example.com'},
                {'userId': 'fc-2', 'email': 'fc2@example.com'}
            ]
            mock_users_table.query.return_value = {'Items': finance_controllers}
            
            # Mock notification service responses
            mock_lambda_client.invoke.return_value = {'MessageId': 'msg-123'}
            mock_sns_client.publish.return_value = {'MessageId': 'sns-456'}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Mock timed out workflow
            past_timeout = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
            timed_out_workflow = {
                'workflowId': workflow_id,
                'workflowType': workflow_type,
                'currentState': WorkflowState.PENDING_APPROVAL.value,
                'payload': payload,
                'timeoutAt': past_timeout
            }
            mock_workflows_table.get_item.return_value = {'Item': timed_out_workflow}
            
            # Handle timeout
            timeout_result = service.handle_workflow_timeout(workflow_id)
            
            # Verify SNS notification was sent
            mock_sns_client.publish.assert_called()
            sns_call = mock_sns_client.publish.call_args
            assert 'escalation-topic' in sns_call[1]['TopicArn']
            
            # Verify notification message contains workflow context
            message_body = json.loads(sns_call[1]['Message'])
            assert message_body['workflowId'] == workflow_id
            assert message_body['workflowType'] == workflow_type
            assert message_body['originalTimeout'] == past_timeout
            assert 'payload' in message_body
            
            # Verify Lambda notifications were sent to finance controllers
            lambda_calls = mock_lambda_client.invoke.call_args_list
            assert len(lambda_calls) == len(finance_controllers)
            
            for i, call in enumerate(lambda_calls):
                payload_data = json.loads(call[1]['Payload'])
                assert payload_data['action'] == 'send_system_notification'
                assert payload_data['systemNotification']['notificationType'] == 'workflow_timeout_escalation'
                assert payload_data['systemNotification']['workflowId'] == workflow_id
                assert payload_data['systemNotification']['urgency'] == 'high'
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_timeout_escalation_logs_complete_audit_details(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: Timeout escalation logs complete audit details
        
        For any workflow timeout escalation, the system must:
        1. Log escalation event with complete audit details
        2. Include original timeout, escalation timestamp, and stakeholders
        3. Maintain audit trail integrity
        4. Enable audit queries for escalation events
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB
            mock_workflows_table = Mock()
            mock_users_table = Mock()
            mock_dynamodb = Mock()
            
            def table_factory(name):
                if 'Workflows' in name:
                    return mock_workflows_table
                elif 'Users' in name:
                    return mock_users_table
                return Mock()
            
            mock_dynamodb.Table.side_effect = table_factory
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            
            # Mock successful operations
            mock_workflows_table.put_item.return_value = {}
            mock_workflows_table.update_item.return_value = {'Attributes': {}}
            mock_users_table.query.return_value = {'Items': []}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Mock timed out workflow
            past_timeout = (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z'
            timed_out_workflow = {
                'workflowId': workflow_id,
                'workflowType': workflow_type,
                'currentState': WorkflowState.PENDING_APPROVAL.value,
                'payload': payload,
                'timeoutAt': past_timeout
            }
            mock_workflows_table.get_item.return_value = {'Item': timed_out_workflow}
            
            # Handle timeout
            service.handle_workflow_timeout(workflow_id)
            
            # Verify system event was logged
            mock_audit_logger.log_system_event.assert_called()
            audit_call = mock_audit_logger.log_system_event.call_args
            
            # Verify audit details are complete
            assert audit_call[1]['event_type'] == 'WORKFLOW_TIMEOUT_ESCALATION'
            assert audit_call[1]['resource'] == 'WORKFLOW'
            assert audit_call[1]['resource_id'] == workflow_id
            
            audit_details = audit_call[1]['details']
            assert audit_details['originalTimeout'] == past_timeout
            assert audit_details['workflowType'] == workflow_type
            assert audit_details['escalatedTo'] == 'FINANCE_CONTROLLER'
            assert 'escalationResult' in audit_details


class TestNotificationDeliveryForWorkflowChanges:
    """
    Property 17: Notification Delivery for Workflow Changes
    
    For any workflow status change, the system SHALL send notifications to all 
    relevant stakeholders based on their roles and notification preferences, 
    with delivery confirmation and retry logic for failed notifications.
    """
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy,
        action=st.sampled_from([
            WorkflowAction.APPROVE.value,
            WorkflowAction.REJECT.value,
            WorkflowAction.CANCEL.value
        ]),
        justification=justification_strategy
    )
    @settings(max_examples=1)
    def test_workflow_status_changes_send_notifications_to_stakeholders(
        self, workflow_type, payload, request_context, action, justification
    ):
        """
        Property Test: Workflow status changes send notifications to stakeholders
        
        For any workflow status change, the system must:
        1. Send notifications to relevant stakeholders
        2. Include complete workflow context in notifications
        3. Use configured notification channels (SNS topics)
        4. Handle notification delivery confirmation
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger, \
             patch.dict(os.environ, {
                 'WORKFLOW_NOTIFICATIONS_TOPIC': 'arn:aws:sns:us-east-1:123456789012:workflow-notifications'
             }):
            
            # Mock DynamoDB
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            
            # Mock successful operations
            mock_table.put_item.return_value = {}
            mock_table.update_item.return_value = {'Attributes': {}}
            mock_sns_client.publish.return_value = {'MessageId': 'msg-123'}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Verify creation notification was sent
            creation_calls = mock_sns_client.publish.call_args_list
            assert len(creation_calls) >= 1
            
            creation_call = creation_calls[0]
            assert 'workflow-notifications' in creation_call[1]['TopicArn']
            
            creation_message = json.loads(creation_call[1]['Message'])
            assert creation_message['workflowId'] == workflow_id
            assert creation_message['action'] == 'created'
            assert creation_message['payload'] == payload
            
            # Reset mock for transition test
            mock_sns_client.reset_mock()
            
            # Mock workflow for transition
            mock_workflow_item = {
                'workflowId': workflow_id,
                'currentState': WorkflowState.PENDING_APPROVAL.value,
                'payload': payload,
                'createdBy': request_context['user_id'],
                'rollbackData': {}
            }
            mock_table.get_item.return_value = {'Item': mock_workflow_item}
            
            # Perform transition
            service.transition_workflow(workflow_id, action, justification)
            
            # Verify transition notification was sent
            transition_calls = mock_sns_client.publish.call_args_list
            assert len(transition_calls) >= 1
            
            transition_call = transition_calls[0]
            assert 'workflow-notifications' in transition_call[1]['TopicArn']
            
            transition_message = json.loads(transition_call[1]['Message'])
            assert transition_message['workflowId'] == workflow_id
            assert transition_message['action'] == action.lower()
            assert transition_message['justification'] == justification
            assert transition_message['payload'] == payload
            assert 'timestamp' in transition_message
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_notifications_include_complete_workflow_context(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: Notifications include complete workflow context
        
        For any workflow notification, the system must:
        1. Include workflow ID, type, and current state
        2. Include complete payload data
        3. Include timestamp and correlation ID
        4. Include user context and justification (where applicable)
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger, \
             patch.dict(os.environ, {
                 'WORKFLOW_NOTIFICATIONS_TOPIC': 'arn:aws:sns:us-east-1:123456789012:workflow-notifications'
             }):
            
            # Mock DynamoDB
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            
            # Mock successful operations
            mock_table.put_item.return_value = {}
            mock_sns_client.publish.return_value = {'MessageId': 'msg-123'}
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow
            create_result = service.create_workflow(workflow_type, payload)
            workflow_id = create_result['workflowId']
            
            # Verify notification was sent with complete context
            notification_calls = mock_sns_client.publish.call_args_list
            assert len(notification_calls) >= 1
            
            notification_call = notification_calls[0]
            message_data = json.loads(notification_call[1]['Message'])
            
            # Verify required context fields
            assert message_data['workflowId'] == workflow_id
            assert message_data['payload'] == payload
            assert message_data['correlationId'] == request_context['correlation_id']
            assert 'timestamp' in message_data
            
            # Verify message structure
            required_fields = ['workflowId', 'state', 'action', 'timestamp', 'payload', 'correlationId']
            for field in required_fields:
                assert field in message_data, f"Missing required field: {field}"
    
    @given(
        workflow_type=workflow_type_strategy,
        payload=workflow_payload_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=1)
    def test_notification_delivery_handles_failures_gracefully(
        self, workflow_type, payload, request_context
    ):
        """
        Property Test: Notification delivery handles failures gracefully
        
        For any notification delivery failure, the system must:
        1. Continue workflow processing despite notification failures
        2. Log notification failures for monitoring
        3. Not block workflow operations due to notification issues
        4. Maintain workflow state consistency
        """
        with patch('workflow_service.handler.get_dynamodb') as mock_get_dynamodb, \
             patch('workflow_service.handler.get_sns') as mock_get_sns, \
             patch('workflow_service.handler.get_eventbridge') as mock_get_eventbridge, \
             patch('workflow_service.handler.audit_logger') as mock_audit_logger, \
             patch('workflow_service.handler.logger') as mock_logger, \
             patch.dict(os.environ, {
                 'WORKFLOW_NOTIFICATIONS_TOPIC': 'arn:aws:sns:us-east-1:123456789012:workflow-notifications'
             }):
            
            # Mock DynamoDB
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_get_dynamodb.return_value = mock_dynamodb
            
            # Mock other services
            mock_sns_client = Mock()
            mock_get_sns.return_value = mock_sns_client
            mock_eventbridge_client = Mock()
            mock_get_eventbridge.return_value = mock_eventbridge_client
            
            # Mock successful DynamoDB operations
            mock_table.put_item.return_value = {}
            
            # Mock SNS failure
            from botocore.exceptions import ClientError
            mock_sns_client.publish.side_effect = ClientError(
                error_response={'Error': {'Code': 'ServiceUnavailable'}},
                operation_name='Publish'
            )
            
            # Initialize service
            service = WorkflowService(request_context)
            
            # Create workflow - should succeed despite notification failure
            create_result = service.create_workflow(workflow_type, payload)
            
            # Verify workflow was created successfully
            assert 'workflowId' in create_result
            assert create_result['workflowType'] == workflow_type
            assert create_result['currentState'] == WorkflowState.PENDING_APPROVAL.value
            
            # Verify DynamoDB put was called (workflow was stored)
            mock_table.put_item.assert_called()
            
            # Verify notification failure was logged
            mock_logger.error.assert_called()
            error_calls = mock_logger.error.call_args_list
            notification_error_logged = any(
                'notification' in str(call).lower() 
                for call in error_calls
            )
            assert notification_error_logged, "Notification failure should be logged"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
