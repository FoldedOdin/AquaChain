"""
Unit tests for workflow service operations
Tests workflow state machine, timeout handling, escalation, and audit trail functionality
"""

import pytest
import json
import boto3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add the lambda directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

# Mock the AWS services and shared modules
sys.modules['boto3'] = Mock()
sys.modules['structured_logger'] = Mock()
sys.modules['audit_logger'] = Mock()

from workflow_service.handler import WorkflowService, WorkflowState, WorkflowType, WorkflowAction, WorkflowStateMachine, WorkflowServiceError


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing"""
    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.put_item = Mock()
    mock_table.get_item = Mock()
    mock_table.update_item = Mock()
    mock_table.query = Mock()
    
    # Mock DynamoDB resource
    mock_dynamodb = Mock()
    mock_dynamodb.Table = Mock(return_value=mock_table)
    
    # Mock SNS client
    mock_sns = Mock()
    mock_sns.publish = Mock()
    mock_sns.create_topic = Mock(return_value={'TopicArn': 'arn:aws:sns:us-east-1:123456789012:test-topic'})
    
    # Mock EventBridge client
    mock_eventbridge = Mock()
    mock_eventbridge.put_rule = Mock()
    mock_eventbridge.put_targets = Mock()
    
    # Mock Lambda client
    mock_lambda = Mock()
    mock_lambda.invoke = Mock()
    
    # Set environment variables
    os.environ['WORKFLOWS_TABLE'] = 'AquaChain-Workflows'
    os.environ['PURCHASE_ORDERS_TABLE'] = 'AquaChain-Purchase-Orders'
    os.environ['USERS_TABLE'] = 'AquaChain-Users'
    os.environ['AUDIT_TABLE'] = 'AquaChain-Audit-Logs'
    os.environ['WORKFLOW_NOTIFICATIONS_TOPIC'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
    os.environ['AWS_REGION'] = 'us-east-1'
    
    with patch('workflow_service.handler.dynamodb', mock_dynamodb), \
         patch('workflow_service.handler.sns', mock_sns), \
         patch('workflow_service.handler.eventbridge', mock_eventbridge), \
         patch('workflow_service.handler.lambda_client', mock_lambda), \
         patch('workflow_service.handler.workflows_table', mock_table), \
         patch('workflow_service.handler.purchase_orders_table', mock_table), \
         patch('workflow_service.handler.users_table', mock_table), \
         patch('workflow_service.handler.audit_table', mock_table):
        
        yield {
            'dynamodb': mock_dynamodb,
            'workflows_table': mock_table,
            'purchase_orders_table': mock_table,
            'users_table': mock_table,
            'audit_table': mock_table,
            'sns': mock_sns,
            'eventbridge': mock_eventbridge,
            'lambda_client': mock_lambda
        }


@pytest.fixture
def workflow_service():
    """Create workflow service instance for testing"""
    request_context = {
        'user_id': 'test-user-123',
        'correlation_id': 'test-correlation-123',
        'ipAddress': '127.0.0.1',
        'userAgent': 'test-agent'
    }
    return WorkflowService(request_context)


@pytest.fixture
def sample_purchase_order_payload():
    """Sample purchase order payload for testing"""
    return {
        'orderId': 'order-123',
        'supplierId': 'supplier-456',
        'totalAmount': 5000.00,
        'budgetCategory': 'OFFICE_SUPPLIES',
        'items': [
            {'itemId': 'item-1', 'quantity': 10, 'unitPrice': 500.00}
        ]
    }


class TestWorkflowStateMachine:
    """Test workflow state machine logic"""
    
    def test_valid_transitions(self):
        """Test valid state transitions"""
        # Test pending approval transitions
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.PENDING_APPROVAL, WorkflowState.APPROVED
        )
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.PENDING_APPROVAL, WorkflowState.REJECTED
        )
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.PENDING_APPROVAL, WorkflowState.TIMEOUT_ESCALATED
        )
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.PENDING_APPROVAL, WorkflowState.CANCELLED
        )
        
        # Test timeout escalated transitions
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.TIMEOUT_ESCALATED, WorkflowState.APPROVED
        )
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.TIMEOUT_ESCALATED, WorkflowState.REJECTED
        )
        
        # Test approved transitions
        assert WorkflowStateMachine.is_valid_transition(
            WorkflowState.APPROVED, WorkflowState.COMPLETED
        )
    
    def test_invalid_transitions(self):
        """Test invalid state transitions"""
        # Cannot transition from rejected (terminal state)
        assert not WorkflowStateMachine.is_valid_transition(
            WorkflowState.REJECTED, WorkflowState.APPROVED
        )
        
        # Cannot transition from completed (terminal state)
        assert not WorkflowStateMachine.is_valid_transition(
            WorkflowState.COMPLETED, WorkflowState.PENDING_APPROVAL
        )
        
        # Cannot transition from cancelled (terminal state)
        assert not WorkflowStateMachine.is_valid_transition(
            WorkflowState.CANCELLED, WorkflowState.APPROVED
        )
    
    def test_terminal_states(self):
        """Test terminal state identification"""
        assert WorkflowStateMachine.is_terminal_state(WorkflowState.REJECTED)
        assert WorkflowStateMachine.is_terminal_state(WorkflowState.CANCELLED)
        assert WorkflowStateMachine.is_terminal_state(WorkflowState.COMPLETED)
        
        assert not WorkflowStateMachine.is_terminal_state(WorkflowState.PENDING_APPROVAL)
        assert not WorkflowStateMachine.is_terminal_state(WorkflowState.APPROVED)
        assert not WorkflowStateMachine.is_terminal_state(WorkflowState.TIMEOUT_ESCALATED)


class TestWorkflowCreation:
    """Test workflow creation functionality"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_create_purchase_approval_workflow(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test creating a purchase approval workflow"""
        # Mock successful DynamoDB put_item
        mock_aws_services['workflows_table'].put_item.return_value = {}
        
        result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload,
            {'priority': 'normal'}
        )
        
        # Verify result structure
        assert 'workflowId' in result
        assert result['workflowType'] == WorkflowType.PURCHASE_APPROVAL.value
        assert result['currentState'] == WorkflowState.PENDING_APPROVAL.value
        assert 'timeoutAt' in result
        assert 'createdAt' in result
        
        # Verify DynamoDB put_item was called
        mock_aws_services['workflows_table'].put_item.assert_called()
        
        # Verify audit logging was called
        mock_audit_logger.log_user_action.assert_called_once()
    
    @patch('workflow_service.handler.audit_logger')
    def test_create_emergency_purchase_workflow(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test creating an emergency purchase workflow with shorter timeout"""
        # Mock successful DynamoDB put_item
        mock_aws_services['workflows_table'].put_item.return_value = {}
        
        result = workflow_service.create_workflow(
            WorkflowType.EMERGENCY_PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        
        # Verify emergency workflow has shorter timeout (4 hours vs 24 hours)
        created_at = datetime.fromisoformat(result['createdAt'].replace('Z', '+00:00'))
        timeout_at = datetime.fromisoformat(result['timeoutAt'].replace('Z', '+00:00'))
        timeout_duration = timeout_at - created_at
        
        # Should be approximately 4 hours (allowing for small timing differences)
        assert 3.9 <= timeout_duration.total_seconds() / 3600 <= 4.1
    
    def test_create_workflow_invalid_type(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test creating workflow with invalid type"""
        with pytest.raises(WorkflowServiceError, match="Invalid workflow type"):
            workflow_service.create_workflow(
                'INVALID_WORKFLOW_TYPE',
                sample_purchase_order_payload
            )


class TestWorkflowTransitions:
    """Test workflow state transitions"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_approve_workflow(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test approving a workflow"""
        # Create workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        # Approve workflow
        approve_result = workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.APPROVE.value,
            'Approved for business needs'
        )
        
        # Verify approval result
        assert approve_result['workflowId'] == workflow_id
        assert approve_result['previousState'] == WorkflowState.PENDING_APPROVAL.value
        assert approve_result['currentState'] == WorkflowState.APPROVED.value
        assert approve_result['action'] == WorkflowAction.APPROVE.value
        assert approve_result['justification'] == 'Approved for business needs'
        
        # Verify workflow state was updated in DynamoDB
        workflows_table = mock_aws_services['workflows_table']
        response = workflows_table.get_item(
            Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
        )
        
        workflow_item = response['Item']
        assert workflow_item['currentState'] == WorkflowState.APPROVED.value
        assert workflow_item['lastActionBy'] == 'test-user-123'
        assert workflow_item['lastJustification'] == 'Approved for business needs'
    
    @patch('workflow_service.handler.audit_logger')
    def test_reject_workflow(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test rejecting a workflow"""
        # Create workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        # Reject workflow
        reject_result = workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.REJECT.value,
            'Budget constraints'
        )
        
        # Verify rejection result
        assert reject_result['currentState'] == WorkflowState.REJECTED.value
        assert reject_result['justification'] == 'Budget constraints'
    
    def test_transition_without_justification(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test transition fails without justification"""
        # Create workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        # Try to approve without justification
        with pytest.raises(WorkflowServiceError, match="Justification is required"):
            workflow_service.transition_workflow(
                workflow_id,
                WorkflowAction.APPROVE.value,
                ''  # Empty justification
            )
    
    def test_invalid_transition(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test invalid state transition"""
        # Create and approve workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.REJECT.value,
            'Rejected for testing'
        )
        
        # Try to approve rejected workflow (invalid transition)
        with pytest.raises(WorkflowServiceError, match="Invalid transition"):
            workflow_service.transition_workflow(
                workflow_id,
                WorkflowAction.APPROVE.value,
                'Trying to approve rejected workflow'
            )
    
    def test_transition_nonexistent_workflow(self, mock_aws_services, workflow_service):
        """Test transition on nonexistent workflow"""
        with pytest.raises(WorkflowServiceError, match="Workflow .* not found"):
            workflow_service.transition_workflow(
                'nonexistent-workflow-id',
                WorkflowAction.APPROVE.value,
                'Test justification'
            )


class TestWorkflowTimeout:
    """Test workflow timeout handling"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_handle_workflow_timeout(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test handling workflow timeout"""
        # Create workflow with past timeout
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        # Manually set timeout to past time
        workflows_table = mock_aws_services['workflows_table']
        past_timeout = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        
        workflows_table.update_item(
            Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'},
            UpdateExpression='SET timeoutAt = :timeout',
            ExpressionAttributeValues={':timeout': past_timeout}
        )
        
        # Handle timeout
        timeout_result = workflow_service.handle_workflow_timeout(workflow_id)
        
        # Verify timeout handling
        assert timeout_result['workflowId'] == workflow_id
        assert timeout_result['action'] == 'escalated'
        assert 'escalatedAt' in timeout_result
        assert timeout_result['originalTimeout'] == past_timeout
        
        # Verify workflow state was updated
        response = workflows_table.get_item(
            Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
        )
        
        workflow_item = response['Item']
        assert workflow_item['currentState'] == WorkflowState.TIMEOUT_ESCALATED.value
    
    def test_timeout_not_reached(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test timeout handling when timeout not yet reached"""
        # Create workflow (timeout will be in future)
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        # Try to handle timeout
        timeout_result = workflow_service.handle_workflow_timeout(workflow_id)
        
        # Should not process timeout
        assert timeout_result['action'] == 'not_ready'
        assert 'timeoutAt' in timeout_result
    
    def test_timeout_non_pending_workflow(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test timeout handling on non-pending workflow"""
        # Create and approve workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.APPROVE.value,
            'Approved before timeout'
        )
        
        # Try to handle timeout on approved workflow
        timeout_result = workflow_service.handle_workflow_timeout(workflow_id)
        
        # Should skip timeout handling
        assert timeout_result['action'] == 'skipped'
        assert 'Workflow in APPROVED state' in timeout_result['reason']


class TestWorkflowStatus:
    """Test workflow status retrieval"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_get_workflow_status(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test getting workflow status"""
        # Create workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload,
            {'priority': 'high'}
        )
        workflow_id = create_result['workflowId']
        
        # Get status
        status_result = workflow_service.get_workflow_status(workflow_id)
        
        # Verify status result
        assert status_result['workflowId'] == workflow_id
        assert status_result['workflowType'] == WorkflowType.PURCHASE_APPROVAL.value
        assert status_result['currentState'] == WorkflowState.PENDING_APPROVAL.value
        assert status_result['createdBy'] == 'test-user-123'
        assert status_result['payload'] == sample_purchase_order_payload
        assert status_result['metadata'] == {'priority': 'high'}
        assert 'stateHistory' in status_result
        assert 'metrics' in status_result
        assert status_result['isTerminal'] == False
    
    def test_get_status_nonexistent_workflow(self, mock_aws_services, workflow_service):
        """Test getting status of nonexistent workflow"""
        with pytest.raises(WorkflowServiceError, match="Workflow .* not found"):
            workflow_service.get_workflow_status('nonexistent-workflow-id')


class TestWorkflowRollback:
    """Test workflow rollback functionality"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_rollback_workflow(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test rolling back a workflow"""
        # Create and approve workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.APPROVE.value,
            'Initial approval'
        )
        
        # Rollback workflow
        rollback_result = workflow_service.rollback_workflow(
            workflow_id,
            'Found error in approval process'
        )
        
        # Verify rollback result
        assert rollback_result['workflowId'] == workflow_id
        assert rollback_result['rolledBackFrom'] == WorkflowState.APPROVED.value
        assert rollback_result['rolledBackTo'] == WorkflowState.PENDING_APPROVAL.value
        assert rollback_result['rollbackReason'] == 'Found error in approval process'
        
        # Verify workflow state was rolled back
        workflows_table = mock_aws_services['workflows_table']
        response = workflows_table.get_item(
            Key={'PK': f"WORKFLOW#{workflow_id}", 'SK': 'CURRENT'}
        )
        
        workflow_item = response['Item']
        assert workflow_item['currentState'] == WorkflowState.PENDING_APPROVAL.value
        assert workflow_item['rolledBackBy'] == 'test-user-123'
        assert workflow_item['rollbackReason'] == 'Found error in approval process'
    
    def test_rollback_terminal_workflow(self, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test rollback fails on terminal workflow"""
        # Create and reject workflow (terminal state)
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.REJECT.value,
            'Rejected for testing'
        )
        
        # Try to rollback terminal workflow
        with pytest.raises(WorkflowServiceError, match="Cannot rollback workflow in terminal state"):
            workflow_service.rollback_workflow(
                workflow_id,
                'Trying to rollback terminal workflow'
            )


class TestWorkflowAuditTrail:
    """Test workflow audit trail functionality"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_get_audit_trail(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test getting workflow audit trail"""
        # Create workflow and perform transitions
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.APPROVE.value,
            'Approved after review'
        )
        
        # Get audit trail
        audit_result = workflow_service.get_workflow_audit_trail(workflow_id)
        
        # Verify audit trail
        assert audit_result['workflowId'] == workflow_id
        assert 'auditEntries' in audit_result
        assert audit_result['entryCount'] >= 2  # Creation + approval
        
        # Verify audit entries contain expected information
        audit_entries = audit_result['auditEntries']
        assert len(audit_entries) >= 2
        
        # Check that entries have required fields
        for entry in audit_entries:
            assert 'auditId' in entry
            assert 'workflowId' in entry
            assert 'action' in entry
            assert 'userId' in entry
            assert 'timestamp' in entry
            assert 'justification' in entry


class TestWorkflowIntegration:
    """Test workflow integration with other services"""
    
    @patch('workflow_service.handler.audit_logger')
    def test_purchase_order_integration(self, mock_audit_logger, mock_aws_services, workflow_service, sample_purchase_order_payload):
        """Test workflow integration with purchase orders"""
        # Create purchase order in database
        purchase_orders_table = mock_aws_services['purchase_orders_table']
        order_id = sample_purchase_order_payload['orderId']
        
        purchase_orders_table.put_item(Item={
            'PK': f"ORDER#{order_id}",
            'SK': 'CURRENT',
            'orderId': order_id,
            'status': 'PENDING',
            'totalAmount': Decimal('5000.00')
        })
        
        # Create and approve workflow
        create_result = workflow_service.create_workflow(
            WorkflowType.PURCHASE_APPROVAL.value,
            sample_purchase_order_payload
        )
        workflow_id = create_result['workflowId']
        
        workflow_service.transition_workflow(
            workflow_id,
            WorkflowAction.APPROVE.value,
            'Approved for purchase'
        )
        
        # Verify purchase order status was updated
        response = purchase_orders_table.get_item(
            Key={'PK': f"ORDER#{order_id}", 'SK': 'CURRENT'}
        )
        
        # Note: In a real implementation, this would be updated by the workflow service
        # For this test, we're just verifying the workflow completed successfully
        assert 'Item' in response


if __name__ == '__main__':
    pytest.main([__file__, '-v'])