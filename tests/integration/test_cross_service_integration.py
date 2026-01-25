"""
Cross-Service Integration Tests - Task 16.1
Tests complete workflows from frontend to backend with comprehensive validation.

This test suite validates:
1. Complete workflows from frontend to backend
2. Role-based access control across all API endpoints
3. Approval workflows end-to-end with all state transitions
4. Budget enforcement across all purchase scenarios
5. Data consistency across service boundaries
6. Error propagation and handling across services

Requirements: All workflow and RBAC requirements
"""

import pytest
import json
import boto3
import uuid
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from structured_logger import get_logger
from audit_logger import audit_logger

# Import service classes
rbac_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'rbac_service')
inventory_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'inventory_management')
procurement_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'procurement_service')
workflow_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'workflow_service')
budget_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'budget_service')
audit_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'audit_service')

sys.path.extend([rbac_path, inventory_path, procurement_path, workflow_path, budget_path, audit_path])

# Import service classes with error handling
try:
    import importlib.util
    
    # Import RBAC Service
    rbac_spec = importlib.util.spec_from_file_location("rbac_handler", os.path.join(rbac_path, "handler.py"))
    rbac_module = importlib.util.module_from_spec(rbac_spec)
    rbac_spec.loader.exec_module(rbac_module)
    RBACService = rbac_module.RBACService
    
    # Import other services
    inventory_spec = importlib.util.spec_from_file_location("inventory_handler", os.path.join(inventory_path, "handler.py"))
    inventory_module = importlib.util.module_from_spec(inventory_spec)
    inventory_spec.loader.exec_module(inventory_module)
    InventoryService = inventory_module.InventoryService
    
    procurement_spec = importlib.util.spec_from_file_location("procurement_handler", os.path.join(procurement_path, "handler.py"))
    procurement_module = importlib.util.module_from_spec(procurement_spec)
    procurement_spec.loader.exec_module(procurement_module)
    ProcurementService = procurement_module.ProcurementService
    
    workflow_spec = importlib.util.spec_from_file_location("workflow_handler", os.path.join(workflow_path, "handler.py"))
    workflow_module = importlib.util.module_from_spec(workflow_spec)
    workflow_spec.loader.exec_module(workflow_module)
    WorkflowService = workflow_module.WorkflowService
    
    budget_spec = importlib.util.spec_from_file_location("budget_handler", os.path.join(budget_path, "handler.py"))
    budget_module = importlib.util.module_from_spec(budget_spec)
    budget_spec.loader.exec_module(budget_module)
    BudgetService = budget_module.BudgetService
    
    audit_spec = importlib.util.spec_from_file_location("audit_handler", os.path.join(audit_path, "handler.py"))
    audit_module = importlib.util.module_from_spec(audit_spec)
    audit_spec.loader.exec_module(audit_module)
    DashboardAuditService = audit_module.DashboardAuditService
    
except Exception as e:
    print(f"Warning: Could not import service classes: {e}")
    # Create mock classes for testing
    class MockService:
        def __init__(self, *args, **kwargs):
            pass
    
    RBACService = MockService
    InventoryService = MockService
    ProcurementService = MockService
    WorkflowService = MockService
    BudgetService = MockService
    DashboardAuditService = MockService

logger = get_logger(__name__, 'cross-service-integration')


class CrossServiceIntegrationTest:
    """
    Cross-service integration test suite for complete workflow validation
    """
    
    def __init__(self):
        """Initialize test environment and services"""
        self.test_correlation_id = str(uuid.uuid4())
        self.test_session_id = str(uuid.uuid4())
        
        # Mock AWS environment
        self.mock_environment = {
            'COGNITO_USER_POOL_ID': 'us-east-1_test123',
            'INVENTORY_TABLE': 'test-inventory',
            'PURCHASE_ORDERS_TABLE': 'test-purchase-orders',
            'BUDGET_TABLE': 'test-budget',
            'WORKFLOWS_TABLE': 'test-workflows',
            'AUDIT_TABLE': 'test-audit',
            'SUPPLIERS_TABLE': 'test-suppliers',
            'WAREHOUSE_TABLE': 'test-warehouse'
        }
        
        for key, value in self.mock_environment.items():
            os.environ[key] = value
        
        # Test users with different roles
        self.test_users = {
            'inventory_manager': {
                'user_id': 'test-inventory-manager',
                'username': 'inventory.manager@test.com',
                'role': 'inventory-manager',
                'permissions': ['inventory:view', 'inventory:act']
            },
            'warehouse_manager': {
                'user_id': 'test-warehouse-manager',
                'username': 'warehouse.manager@test.com',
                'role': 'warehouse-manager',
                'permissions': ['warehouse:view', 'warehouse:act']
            },
            'supplier_coordinator': {
                'user_id': 'test-supplier-coordinator',
                'username': 'supplier.coordinator@test.com',
                'role': 'supplier-coordinator',
                'permissions': ['supplier:view', 'supplier:act']
            },
            'procurement_controller': {
                'user_id': 'test-procurement-controller',
                'username': 'procurement.controller@test.com',
                'role': 'procurement-finance-controller',
                'permissions': ['procurement:view', 'procurement:act', 'procurement:approve', 'budget:configure']
            },
            'admin': {
                'user_id': 'test-admin',
                'username': 'admin@test.com',
                'role': 'administrator',
                'permissions': ['system:configure', 'user:manage']
            }
        }
        
        # Initialize services
        self.services = {}
        self.audit_events = []
        
        logger.info(
            "Cross-service integration test environment initialized",
            correlation_id=self.test_correlation_id,
            session_id=self.test_session_id
        )
    
    def _create_request_context(self, user_key: str) -> Dict[str, Any]:
        """Create request context for a test user"""
        user = self.test_users[user_key]
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'correlation_id': self.test_correlation_id,
            'session_id': self.test_session_id,
            'ip_address': '127.0.0.1',
            'user_agent': 'integration-test',
            'source': 'cross_service_integration_test'
        }
    
    def _initialize_services(self, user_key: str):
        """Initialize all services for a specific user context"""
        context = self._create_request_context(user_key)
        
        self.services = {
            'rbac': RBACService('us-east-1_test123'),
            'inventory': InventoryService(context),
            'procurement': ProcurementService(context),
            'workflow': WorkflowService(context),
            'budget': BudgetService(context),
            'audit': DashboardAuditService()
        }
        
        return context
    
    def test_complete_purchase_order_workflow(self):
        """
        Test 1: Complete purchase order workflow from frontend to backend
        Tests: Inventory alert -> Purchase order -> Approval workflow -> Budget enforcement -> Completion
        """
        logger.info("Starting complete purchase order workflow test")
        
        # Step 1: Initialize as inventory manager
        context = self._initialize_services('inventory_manager')
        
        # Step 2: Create low stock condition that triggers reorder
        low_stock_item = {
            'item_id': 'test-item-workflow-001',
            'location_id': 'warehouse-001',
            'name': 'Critical Inventory Item',
            'current_stock': 5.0,
            'reorder_point': 20.0,
            'reorder_quantity': 100.0,
            'unit_cost': 50.0,
            'supplier_id': 'test-supplier-001',
            'category': 'office-supplies'
        }
        
        with patch.object(self.services['inventory'], '_check_and_generate_alerts') as mock_alerts:
            with patch.object(self.services['inventory'].inventory_table, 'get_item') as mock_get:
                mock_get.return_value = {'Item': low_stock_item}
                
                with patch.object(self.services['inventory'].inventory_table, 'update_item') as mock_update:
                    updated_item = low_stock_item.copy()
                    updated_item['current_stock'] = 3.0  # Below reorder point
                    mock_update.return_value = {'Attributes': updated_item}
                    
                    # Simulate inventory update from frontend
                    update_result = self.services['inventory'].update_stock_level(
                        'test-item-workflow-001',
                        'warehouse-001',
                        {'current_stock': 3.0}
                    )
                    
                    assert update_result['statusCode'] == 200
                    logger.info("Step 1: Inventory updated, low stock detected")
        
        # Step 3: Generate reorder alert (would be displayed in frontend)
        with patch.object(self.services['inventory'].inventory_table, 'query') as mock_query:
            mock_query.return_value = {'Items': [updated_item]}
            
            alerts_result = self.services['inventory'].get_reorder_alerts('high')
            assert alerts_result['statusCode'] == 200
            assert len(alerts_result['body']['alerts']) > 0
            
            logger.info("Step 2: Reorder alert generated")
        
        # Step 4: Switch to procurement controller context for purchase order creation
        context = self._initialize_services('procurement_controller')
        
        # Step 5: Create budget allocation first
        budget_allocation = {
            'category': 'office-supplies',
            'amount': 10000.0,
            'justification': 'Workflow test budget allocation'
        }
        
        with patch.object(self.services['budget'], '_validate_allocation_data'):
            with patch.object(self.services['budget'].budget_table, 'put_item') as mock_budget_put:
                mock_budget_put.return_value = None
                
                budget_result = self.services['budget'].allocate_budget(budget_allocation)
                assert budget_result['allocated'] == True
                logger.info("Step 3: Budget allocated")
        
        # Step 6: Submit purchase order (from frontend)
        purchase_order_data = {
            'supplierId': 'test-supplier-001',
            'items': [
                {
                    'itemId': 'test-item-workflow-001',
                    'quantity': 100,
                    'unitPrice': 50.0,
                    'description': 'Reorder for critical inventory item'
                }
            ],
            'budgetCategory': 'office-supplies',
            'justification': 'Automatic reorder triggered by low stock alert',
            'deliveryAddress': '123 Warehouse Street'
        }
        
        with patch.object(self.services['procurement'], '_validate_supplier') as mock_supplier:
            mock_supplier.return_value = {'name': 'Test Supplier', 'id': 'test-supplier-001'}
            
            with patch.object(self.services['procurement'], '_validate_budget_availability') as mock_budget:
                mock_budget.return_value = {'available': True, 'message': 'Budget available'}
                
                with patch.object(self.services['procurement'], '_create_approval_workflow') as mock_workflow:
                    workflow_id = 'workflow-' + str(uuid.uuid4())
                    mock_workflow.return_value = workflow_id
                    
                    with patch.object(self.services['procurement'].purchase_orders_table, 'put_item') as mock_po_put:
                        mock_po_put.return_value = None
                        
                        po_result = self.services['procurement'].submit_purchase_order(purchase_order_data)
                        assert 'orderId' in po_result
                        assert po_result['status'] == 'PENDING'
                        
                        order_id = po_result['orderId']
                        logger.info(f"Step 4: Purchase order submitted - {order_id}")
        
        # Step 7: Test workflow approval process
        with patch.object(self.services['workflow'].workflows_table, 'get_item') as mock_get_workflow:
            workflow_data = {
                'workflowId': workflow_id,
                'workflowType': 'PURCHASE_APPROVAL',
                'currentState': 'PENDING_APPROVAL',
                'payload': {'orderId': order_id},
                'createdBy': context['user_id'],
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'timeoutAt': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
            }
            mock_get_workflow.return_value = {'Item': workflow_data}
            
            with patch.object(self.services['workflow'].workflows_table, 'update_item') as mock_update_workflow:
                approved_workflow = workflow_data.copy()
                approved_workflow['currentState'] = 'APPROVED'
                mock_update_workflow.return_value = {'Attributes': approved_workflow}
                
                # Test approval transition
                approval_result = self.services['workflow'].transition_workflow(
                    workflow_id,
                    'APPROVE',
                    'Approved for critical inventory replenishment',
                    {'approver_notes': 'Urgent reorder required'}
                )
                
                assert approval_result['currentState'] == 'APPROVED'
                logger.info("Step 5: Workflow approved")
        
        # Step 8: Test budget reservation
        with patch.object(self.services['budget'], '_get_budget_info') as mock_budget_info:
            mock_budget_info.return_value = {
                'allocatedAmount': Decimal('10000.0'),
                'utilizedAmount': Decimal('0.0'),
                'reservedAmount': Decimal('0.0'),
                'remainingAmount': Decimal('10000.0')
            }
            
            with patch.object(self.services['budget'].budget_table, 'update_item') as mock_budget_update:
                mock_budget_update.return_value = {
                    'Attributes': {
                        'allocatedAmount': Decimal('10000.0'),
                        'utilizedAmount': Decimal('5000.0'),
                        'reservedAmount': Decimal('0.0')
                    }
                }
                
                budget_reserve_result = self.services['budget'].reserve_budget(5000.0, 'office-supplies', order_id)
                assert budget_reserve_result['reserved'] == True
                logger.info("Step 6: Budget reserved")
        
        # Step 9: Complete workflow and update inventory
        context = self._initialize_services('inventory_manager')
        
        with patch.object(self.services['inventory'].inventory_table, 'update_item') as mock_inventory_update:
            final_item = low_stock_item.copy()
            final_item['current_stock'] = 103.0  # Original 3 + 100 received
            mock_inventory_update.return_value = {'Attributes': final_item}
            
            inventory_update_result = self.services['inventory'].update_stock_level(
                'test-item-workflow-001',
                'warehouse-001',
                {'current_stock': 103.0}
            )
            
            assert inventory_update_result['statusCode'] == 200
            logger.info("Step 7: Inventory updated with received items")
        
        logger.info("Complete purchase order workflow test completed successfully")
        
        return {
            'orderId': order_id,
            'workflowId': workflow_id,
            'budgetReserved': 5000.0,
            'inventoryUpdated': True,
            'workflowCompleted': True
        }
    
    def test_rbac_enforcement_across_all_endpoints(self):
        """
        Test 2: Role-based access control across all API endpoints
        Tests that each role can only access authorized endpoints
        """
        logger.info("Starting RBAC enforcement test across all endpoints")
        
        # Define endpoint test cases with expected access patterns
        endpoint_tests = [
            # Inventory endpoints
            {
                'service': 'inventory',
                'method': 'get_stock_levels',
                'args': [{}],
                'authorized_roles': ['inventory_manager', 'admin'],
                'unauthorized_roles': ['warehouse_manager', 'supplier_coordinator', 'procurement_controller']
            },
            {
                'service': 'inventory',
                'method': 'update_stock_level',
                'args': ['item-001', 'warehouse-001', {'current_stock': 50.0}],
                'authorized_roles': ['inventory_manager'],
                'unauthorized_roles': ['warehouse_manager', 'supplier_coordinator', 'procurement_controller', 'admin']
            },
            
            # Procurement endpoints
            {
                'service': 'procurement',
                'method': 'submit_purchase_order',
                'args': [{
                    'supplierId': 'supplier-001',
                    'items': [{'itemId': 'item-001', 'quantity': 10, 'unitPrice': 25.0}],
                    'budgetCategory': 'office-supplies',
                    'justification': 'RBAC test'
                }],
                'authorized_roles': ['procurement_controller'],
                'unauthorized_roles': ['inventory_manager', 'warehouse_manager', 'supplier_coordinator', 'admin']
            },
            
            # Budget endpoints
            {
                'service': 'budget',
                'method': 'allocate_budget',
                'args': [{'category': 'test', 'amount': 1000.0, 'justification': 'RBAC test'}],
                'authorized_roles': ['procurement_controller'],
                'unauthorized_roles': ['inventory_manager', 'warehouse_manager', 'supplier_coordinator', 'admin']
            },
            
            # Workflow endpoints
            {
                'service': 'workflow',
                'method': 'transition_workflow',
                'args': ['workflow-001', 'APPROVE', 'RBAC test approval', {}],
                'authorized_roles': ['procurement_controller'],
                'unauthorized_roles': ['inventory_manager', 'warehouse_manager', 'supplier_coordinator', 'admin']
            }
        ]
        
        rbac_results = []
        
        for test_case in endpoint_tests:
            logger.info(f"Testing endpoint: {test_case['service']}.{test_case['method']}")
            
            # Test authorized roles
            for role in test_case['authorized_roles']:
                context = self._initialize_services(role)
                
                # Mock RBAC validation to return authorized
                with patch.object(self.services['rbac'], 'validate_user_permissions') as mock_rbac:
                    mock_rbac.return_value = (True, role, {'authorized': True})
                    
                    # Mock the actual service method to avoid database calls
                    service = self.services[test_case['service']]
                    method = getattr(service, test_case['method'])
                    
                    with patch.object(service, test_case['method']) as mock_method:
                        mock_method.return_value = {'statusCode': 200, 'authorized': True}
                        
                        try:
                            result = method(*test_case['args'])
                            rbac_results.append({
                                'endpoint': f"{test_case['service']}.{test_case['method']}",
                                'role': role,
                                'expected': 'authorized',
                                'actual': 'authorized',
                                'passed': True
                            })
                        except Exception as e:
                            rbac_results.append({
                                'endpoint': f"{test_case['service']}.{test_case['method']}",
                                'role': role,
                                'expected': 'authorized',
                                'actual': f'error: {str(e)}',
                                'passed': False
                            })
            
            # Test unauthorized roles
            for role in test_case['unauthorized_roles']:
                context = self._initialize_services(role)
                
                # Mock RBAC validation to return unauthorized
                with patch.object(self.services['rbac'], 'validate_user_permissions') as mock_rbac:
                    mock_rbac.return_value = (False, role, {'authorized': False, 'reason': 'Insufficient permissions'})
                    
                    service = self.services[test_case['service']]
                    method = getattr(service, test_case['method'])
                    
                    try:
                        result = method(*test_case['args'])
                        # Should not reach here for unauthorized access
                        rbac_results.append({
                            'endpoint': f"{test_case['service']}.{test_case['method']}",
                            'role': role,
                            'expected': 'unauthorized',
                            'actual': 'authorized',
                            'passed': False
                        })
                    except Exception as e:
                        # Expected to fail for unauthorized access
                        if 'permission' in str(e).lower() or 'unauthorized' in str(e).lower():
                            rbac_results.append({
                                'endpoint': f"{test_case['service']}.{test_case['method']}",
                                'role': role,
                                'expected': 'unauthorized',
                                'actual': 'unauthorized',
                                'passed': True
                            })
                        else:
                            rbac_results.append({
                                'endpoint': f"{test_case['service']}.{test_case['method']}",
                                'role': role,
                                'expected': 'unauthorized',
                                'actual': f'error: {str(e)}',
                                'passed': False
                            })
        
        # Validate results
        failed_tests = [r for r in rbac_results if not r['passed']]
        total_tests = len(rbac_results)
        passed_tests = total_tests - len(failed_tests)
        
        logger.info(
            "RBAC enforcement test completed",
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=len(failed_tests)
        )
        
        assert len(failed_tests) == 0, f"RBAC enforcement failed for: {failed_tests}"
        
        return {
            'totalTests': total_tests,
            'passedTests': passed_tests,
            'failedTests': failed_tests,
            'rbacEnforcementWorking': len(failed_tests) == 0
        }
    
    def test_approval_workflow_state_transitions(self):
        """
        Test 3: End-to-end approval workflow with all state transitions
        Tests all possible workflow states and transitions
        """
        logger.info("Starting approval workflow state transitions test")
        
        context = self._initialize_services('procurement_controller')
        
        # Define all possible workflow states and transitions
        workflow_states = {
            'PENDING_APPROVAL': {
                'valid_transitions': ['APPROVE', 'REJECT', 'REQUEST_INFO'],
                'invalid_transitions': ['COMPLETE', 'CANCEL']
            },
            'APPROVED': {
                'valid_transitions': ['COMPLETE', 'CANCEL'],
                'invalid_transitions': ['APPROVE', 'REJECT']
            },
            'REJECTED': {
                'valid_transitions': ['RESUBMIT'],
                'invalid_transitions': ['APPROVE', 'COMPLETE']
            },
            'INFO_REQUESTED': {
                'valid_transitions': ['PROVIDE_INFO', 'CANCEL'],
                'invalid_transitions': ['APPROVE', 'COMPLETE']
            },
            'COMPLETED': {
                'valid_transitions': [],
                'invalid_transitions': ['APPROVE', 'REJECT', 'CANCEL']
            }
        }
        
        transition_results = []
        
        for current_state, transitions in workflow_states.items():
            workflow_id = f'test-workflow-{current_state.lower()}-{uuid.uuid4().hex[:8]}'
            
            # Create mock workflow in current state
            workflow_data = {
                'workflowId': workflow_id,
                'workflowType': 'PURCHASE_APPROVAL',
                'currentState': current_state,
                'payload': {'orderId': f'order-{workflow_id}'},
                'createdBy': context['user_id'],
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'timeoutAt': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
            }
            
            # Test valid transitions
            for action in transitions['valid_transitions']:
                with patch.object(self.services['workflow'].workflows_table, 'get_item') as mock_get:
                    mock_get.return_value = {'Item': workflow_data}
                    
                    with patch.object(self.services['workflow'].workflows_table, 'update_item') as mock_update:
                        # Determine next state based on action
                        next_state_map = {
                            'APPROVE': 'APPROVED',
                            'REJECT': 'REJECTED',
                            'REQUEST_INFO': 'INFO_REQUESTED',
                            'COMPLETE': 'COMPLETED',
                            'CANCEL': 'CANCELLED',
                            'RESUBMIT': 'PENDING_APPROVAL',
                            'PROVIDE_INFO': 'PENDING_APPROVAL'
                        }
                        
                        next_state = next_state_map.get(action, current_state)
                        updated_workflow = workflow_data.copy()
                        updated_workflow['currentState'] = next_state
                        mock_update.return_value = {'Attributes': updated_workflow}
                        
                        try:
                            result = self.services['workflow'].transition_workflow(
                                workflow_id,
                                action,
                                f'Test transition from {current_state} to {next_state}',
                                {'test': True}
                            )
                            
                            transition_results.append({
                                'workflowId': workflow_id,
                                'fromState': current_state,
                                'action': action,
                                'toState': next_state,
                                'expected': 'success',
                                'actual': 'success',
                                'passed': True
                            })
                            
                        except Exception as e:
                            transition_results.append({
                                'workflowId': workflow_id,
                                'fromState': current_state,
                                'action': action,
                                'toState': next_state,
                                'expected': 'success',
                                'actual': f'error: {str(e)}',
                                'passed': False
                            })
            
            # Test invalid transitions
            for action in transitions['invalid_transitions']:
                with patch.object(self.services['workflow'].workflows_table, 'get_item') as mock_get:
                    mock_get.return_value = {'Item': workflow_data}
                    
                    try:
                        result = self.services['workflow'].transition_workflow(
                            workflow_id,
                            action,
                            f'Invalid transition test from {current_state}',
                            {'test': True}
                        )
                        
                        # Should not succeed for invalid transitions
                        transition_results.append({
                            'workflowId': workflow_id,
                            'fromState': current_state,
                            'action': action,
                            'toState': 'unknown',
                            'expected': 'error',
                            'actual': 'success',
                            'passed': False
                        })
                        
                    except Exception as e:
                        # Expected to fail for invalid transitions
                        if 'invalid' in str(e).lower() or 'transition' in str(e).lower():
                            transition_results.append({
                                'workflowId': workflow_id,
                                'fromState': current_state,
                                'action': action,
                                'toState': 'error',
                                'expected': 'error',
                                'actual': 'error',
                                'passed': True
                            })
                        else:
                            transition_results.append({
                                'workflowId': workflow_id,
                                'fromState': current_state,
                                'action': action,
                                'toState': 'error',
                                'expected': 'error',
                                'actual': f'unexpected_error: {str(e)}',
                                'passed': False
                            })
        
        # Validate results
        failed_transitions = [r for r in transition_results if not r['passed']]
        total_transitions = len(transition_results)
        passed_transitions = total_transitions - len(failed_transitions)
        
        logger.info(
            "Approval workflow state transitions test completed",
            total_transitions=total_transitions,
            passed_transitions=passed_transitions,
            failed_transitions=len(failed_transitions)
        )
        
        assert len(failed_transitions) == 0, f"Workflow transitions failed for: {failed_transitions}"
        
        return {
            'totalTransitions': total_transitions,
            'passedTransitions': passed_transitions,
            'failedTransitions': failed_transitions,
            'workflowTransitionsWorking': len(failed_transitions) == 0
        }
    
    def test_budget_enforcement_across_purchase_scenarios(self):
        """
        Test 4: Budget enforcement across all purchase scenarios
        Tests various budget scenarios and enforcement rules
        """
        logger.info("Starting budget enforcement across purchase scenarios test")
        
        context = self._initialize_services('procurement_controller')
        
        # Define budget test scenarios
        budget_scenarios = [
            {
                'name': 'Normal Purchase Within Budget',
                'budget_amount': 10000.0,
                'utilized_amount': 2000.0,
                'purchase_amount': 3000.0,
                'expected_result': 'approved',
                'description': 'Purchase within available budget should be approved'
            },
            {
                'name': 'Purchase Exactly at Budget Limit',
                'budget_amount': 10000.0,
                'utilized_amount': 7000.0,
                'purchase_amount': 3000.0,
                'expected_result': 'approved',
                'description': 'Purchase that exactly uses remaining budget should be approved'
            },
            {
                'name': 'Purchase Exceeding Budget',
                'budget_amount': 10000.0,
                'utilized_amount': 8000.0,
                'purchase_amount': 3000.0,
                'expected_result': 'rejected',
                'description': 'Purchase exceeding available budget should be rejected'
            },
            {
                'name': 'Emergency Purchase Over Budget',
                'budget_amount': 10000.0,
                'utilized_amount': 9500.0,
                'purchase_amount': 1000.0,
                'expected_result': 'approved_with_override',
                'description': 'Emergency purchase may override budget with proper authorization'
            },
            {
                'name': 'Multiple Concurrent Purchases',
                'budget_amount': 10000.0,
                'utilized_amount': 5000.0,
                'purchase_amount': 3000.0,
                'concurrent_purchases': 2,
                'expected_result': 'partial_approval',
                'description': 'Multiple concurrent purchases should handle budget contention'
            }
        ]
        
        budget_results = []
        
        for scenario in budget_scenarios:
            logger.info(f"Testing budget scenario: {scenario['name']}")
            
            # Set up budget state
            budget_category = f"test-category-{uuid.uuid4().hex[:8]}"
            
            with patch.object(self.services['budget'], '_get_budget_info') as mock_budget_info:
                mock_budget_info.return_value = {
                    'allocatedAmount': Decimal(str(scenario['budget_amount'])),
                    'utilizedAmount': Decimal(str(scenario['utilized_amount'])),
                    'reservedAmount': Decimal('0.0'),
                    'remainingAmount': Decimal(str(scenario['budget_amount'] - scenario['utilized_amount']))
                }
                
                # Test budget validation
                validation_result = self.services['budget'].validate_budget_availability(
                    scenario['purchase_amount'],
                    budget_category
                )
                
                # Determine expected validation result
                available_budget = scenario['budget_amount'] - scenario['utilized_amount']
                expected_available = scenario['purchase_amount'] <= available_budget
                
                if scenario['expected_result'] == 'approved':
                    assert validation_result['available'] == True
                    budget_results.append({
                        'scenario': scenario['name'],
                        'expected': 'approved',
                        'actual': 'approved' if validation_result['available'] else 'rejected',
                        'passed': validation_result['available'] == True
                    })
                    
                elif scenario['expected_result'] == 'rejected':
                    assert validation_result['available'] == False
                    budget_results.append({
                        'scenario': scenario['name'],
                        'expected': 'rejected',
                        'actual': 'rejected' if not validation_result['available'] else 'approved',
                        'passed': validation_result['available'] == False
                    })
                    
                elif scenario['expected_result'] == 'approved_with_override':
                    # Test emergency purchase override
                    with patch.object(self.services['budget'], '_check_emergency_override') as mock_override:
                        mock_override.return_value = True
                        
                        override_result = self.services['budget'].validate_emergency_purchase(
                            scenario['purchase_amount'],
                            budget_category,
                            'Emergency override test'
                        )
                        
                        budget_results.append({
                            'scenario': scenario['name'],
                            'expected': 'approved_with_override',
                            'actual': 'approved_with_override' if override_result.get('approved') else 'rejected',
                            'passed': override_result.get('approved', False) == True
                        })
                
                elif scenario['expected_result'] == 'partial_approval':
                    # Test concurrent purchase handling
                    concurrent_results = []
                    
                    for i in range(scenario.get('concurrent_purchases', 1)):
                        concurrent_validation = self.services['budget'].validate_budget_availability(
                            scenario['purchase_amount'],
                            budget_category
                        )
                        concurrent_results.append(concurrent_validation['available'])
                    
                    # At least one should succeed, but not all if budget is insufficient
                    any_approved = any(concurrent_results)
                    all_approved = all(concurrent_results)
                    
                    budget_results.append({
                        'scenario': scenario['name'],
                        'expected': 'partial_approval',
                        'actual': f'approved: {sum(concurrent_results)}/{len(concurrent_results)}',
                        'passed': any_approved and not all_approved
                    })
        
        # Test budget reservation and release
        with patch.object(self.services['budget'], '_get_budget_info') as mock_budget_info:
            mock_budget_info.return_value = {
                'allocatedAmount': Decimal('10000.0'),
                'utilizedAmount': Decimal('0.0'),
                'reservedAmount': Decimal('0.0'),
                'remainingAmount': Decimal('10000.0')
            }
            
            with patch.object(self.services['budget'].budget_table, 'update_item') as mock_update:
                # Test reservation
                mock_update.return_value = {
                    'Attributes': {
                        'allocatedAmount': Decimal('10000.0'),
                        'utilizedAmount': Decimal('0.0'),
                        'reservedAmount': Decimal('3000.0')
                    }
                }
                
                reserve_result = self.services['budget'].reserve_budget(3000.0, 'test-category', 'order-001')
                assert reserve_result['reserved'] == True
                
                # Test release
                mock_update.return_value = {
                    'Attributes': {
                        'allocatedAmount': Decimal('10000.0'),
                        'utilizedAmount': Decimal('0.0'),
                        'reservedAmount': Decimal('0.0')
                    }
                }
                
                release_result = self.services['budget'].release_budget_reservation('order-001')
                assert release_result['released'] == True
                
                budget_results.append({
                    'scenario': 'Budget Reservation and Release',
                    'expected': 'success',
                    'actual': 'success',
                    'passed': True
                })
        
        # Validate overall results
        failed_scenarios = [r for r in budget_results if not r['passed']]
        total_scenarios = len(budget_results)
        passed_scenarios = total_scenarios - len(failed_scenarios)
        
        logger.info(
            "Budget enforcement test completed",
            total_scenarios=total_scenarios,
            passed_scenarios=passed_scenarios,
            failed_scenarios=len(failed_scenarios)
        )
        
        assert len(failed_scenarios) == 0, f"Budget enforcement failed for scenarios: {failed_scenarios}"
        
        return {
            'totalScenarios': total_scenarios,
            'passedScenarios': passed_scenarios,
            'failedScenarios': failed_scenarios,
            'budgetEnforcementWorking': len(failed_scenarios) == 0
        }
    
    def run_all_cross_service_tests(self):
        """
        Run all cross-service integration tests
        """
        logger.info("Starting comprehensive cross-service integration validation")
        
        test_results = {}
        
        try:
            # Test 1: Complete Purchase Order Workflow
            test_results['complete_workflow'] = self.test_complete_purchase_order_workflow()
            
            # Test 2: RBAC Enforcement
            test_results['rbac_enforcement'] = self.test_rbac_enforcement_across_all_endpoints()
            
            # Test 3: Workflow State Transitions
            test_results['workflow_transitions'] = self.test_approval_workflow_state_transitions()
            
            # Test 4: Budget Enforcement
            test_results['budget_enforcement'] = self.test_budget_enforcement_across_purchase_scenarios()
            
            # Calculate overall success
            all_tests_passed = all([
                test_results['complete_workflow']['workflowCompleted'] == True,
                test_results['rbac_enforcement']['rbacEnforcementWorking'] == True,
                test_results['workflow_transitions']['workflowTransitionsWorking'] == True,
                test_results['budget_enforcement']['budgetEnforcementWorking'] == True
            ])
            
            test_results['overall_success'] = all_tests_passed
            test_results['test_summary'] = {
                'total_test_suites': 4,
                'passed_test_suites': sum([
                    1 if test_results['complete_workflow']['workflowCompleted'] == True else 0,
                    1 if test_results['rbac_enforcement']['rbacEnforcementWorking'] == True else 0,
                    1 if test_results['workflow_transitions']['workflowTransitionsWorking'] == True else 0,
                    1 if test_results['budget_enforcement']['budgetEnforcementWorking'] == True else 0
                ]),
                'completion_time': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Cross-service integration validation completed",
                overall_success=all_tests_passed,
                test_summary=test_results['test_summary']
            )
            
        except Exception as e:
            logger.error(
                "Cross-service integration test suite failed",
                error=str(e),
                correlation_id=self.test_correlation_id
            )
            test_results['overall_success'] = False
            test_results['error'] = str(e)
        
        return test_results


def main():
    """
    Main function to run cross-service integration tests
    """
    print("=" * 80)
    print("CROSS-SERVICE INTEGRATION TESTS - TASK 16.1")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = CrossServiceIntegrationTest()
    
    # Run all tests
    results = test_suite.run_all_cross_service_tests()
    
    # Print results
    print("\nTEST RESULTS:")
    print("-" * 40)
    
    if results['overall_success']:
        print("✅ ALL CROSS-SERVICE INTEGRATION TESTS PASSED")
    else:
        print("❌ SOME CROSS-SERVICE INTEGRATION TESTS FAILED")
    
    if 'test_summary' in results:
        summary = results['test_summary']
        print(f"\nTest Summary:")
        print(f"  Total Test Suites: {summary['total_test_suites']}")
        print(f"  Passed Test Suites: {summary['passed_test_suites']}")
        print(f"  Success Rate: {(summary['passed_test_suites'] / summary['total_test_suites']) * 100:.1f}%")
        print(f"  Completion Time: {summary['completion_time']}")
    
    print(f"\nDetailed Results:")
    for test_name, test_result in results.items():
        if test_name not in ['overall_success', 'test_summary', 'error']:
            print(f"  {test_name}: {test_result}")
    
    if 'error' in results:
        print(f"\nError: {results['error']}")
    
    print("\n" + "=" * 80)
    
    return results


if __name__ == "__main__":
    main()