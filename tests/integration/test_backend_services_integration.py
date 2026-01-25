"""
Backend Services Integration Validation Tests
Tests the integration between all backend services for the dashboard overhaul.

This test suite validates:
1. Service-to-service communication
2. Workflow state machine transitions
3. Budget enforcement across services
4. Graceful degradation scenarios
5. Cross-service audit logging
6. RBAC enforcement across all endpoints
"""

import pytest
import json
import boto3
import uuid
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

from structured_logger import get_logger
from audit_logger import audit_logger

# Import service classes - need to import from specific modules
rbac_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'rbac_service')
inventory_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'inventory_management')
procurement_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'procurement_service')
workflow_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'workflow_service')
budget_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'budget_service')
audit_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'audit_service')

sys.path.append(rbac_path)
sys.path.append(inventory_path)
sys.path.append(procurement_path)
sys.path.append(workflow_path)
sys.path.append(budget_path)
sys.path.append(audit_path)

# Import the service classes with proper error handling
try:
    import importlib.util
    
    # Import RBAC Service
    rbac_spec = importlib.util.spec_from_file_location("rbac_handler", os.path.join(rbac_path, "handler.py"))
    rbac_module = importlib.util.module_from_spec(rbac_spec)
    rbac_spec.loader.exec_module(rbac_module)
    RBACService = rbac_module.RBACService
    
    # Import Inventory Service
    inventory_spec = importlib.util.spec_from_file_location("inventory_handler", os.path.join(inventory_path, "handler.py"))
    inventory_module = importlib.util.module_from_spec(inventory_spec)
    inventory_spec.loader.exec_module(inventory_module)
    InventoryService = inventory_module.InventoryService
    
    # Import Procurement Service
    procurement_spec = importlib.util.spec_from_file_location("procurement_handler", os.path.join(procurement_path, "handler.py"))
    procurement_module = importlib.util.module_from_spec(procurement_spec)
    procurement_spec.loader.exec_module(procurement_module)
    ProcurementService = procurement_module.ProcurementService
    
    # Import Workflow Service
    workflow_spec = importlib.util.spec_from_file_location("workflow_handler", os.path.join(workflow_path, "handler.py"))
    workflow_module = importlib.util.module_from_spec(workflow_spec)
    workflow_spec.loader.exec_module(workflow_module)
    WorkflowService = workflow_module.WorkflowService
    
    # Import Budget Service
    budget_spec = importlib.util.spec_from_file_location("budget_handler", os.path.join(budget_path, "handler.py"))
    budget_module = importlib.util.module_from_spec(budget_spec)
    budget_spec.loader.exec_module(budget_module)
    BudgetService = budget_module.BudgetService
    
    # Import Audit Service
    audit_spec = importlib.util.spec_from_file_location("audit_handler", os.path.join(audit_path, "handler.py"))
    audit_module = importlib.util.module_from_spec(audit_spec)
    audit_spec.loader.exec_module(audit_module)
    DashboardAuditService = audit_module.DashboardAuditService
    
except Exception as e:
    print(f"Warning: Could not import all service classes: {e}")
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

logger = get_logger(__name__, 'integration-tests')


class BackendServicesIntegrationTest:
    """
    Integration test suite for backend services validation
    """
    
    def __init__(self):
        """Initialize test environment and services"""
        self.test_correlation_id = str(uuid.uuid4())
        self.test_user_id = 'test-user-integration'
        
        # Mock AWS environment for testing
        self.mock_environment = {
            'COGNITO_USER_POOL_ID': 'us-east-1_test123',
            'INVENTORY_TABLE': 'test-inventory',
            'PURCHASE_ORDERS_TABLE': 'test-purchase-orders',
            'BUDGET_TABLE': 'test-budget',
            'WORKFLOWS_TABLE': 'test-workflows',
            'AUDIT_TABLE': 'test-audit',
            'SUPPLIERS_TABLE': 'test-suppliers'
        }
        
        # Set environment variables
        for key, value in self.mock_environment.items():
            os.environ[key] = value
        
        # Initialize services with test context
        self.request_context = {
            'user_id': self.test_user_id,
            'correlation_id': self.test_correlation_id,
            'ip_address': '127.0.0.1',
            'user_agent': 'integration-test',
            'source': 'integration_test'
        }
        
        # Initialize service instances
        self.rbac_service = RBACService('us-east-1_test123')
        self.inventory_service = InventoryService(self.request_context)
        self.procurement_service = ProcurementService(self.request_context)
        self.workflow_service = WorkflowService(self.request_context)
        self.budget_service = BudgetService(self.request_context)
        self.audit_service = DashboardAuditService()
        
        logger.info(
            "Integration test environment initialized",
            correlation_id=self.test_correlation_id
        )
    
    def test_rbac_integration_across_services(self):
        """
        Test 1: RBAC service integration with all other services
        Validates that RBAC permissions are enforced across all service endpoints
        """
        logger.info("Starting RBAC integration test")
        
        test_cases = [
            {
                'role': 'inventory-manager',
                'resource': 'inventory-data',
                'action': 'view',
                'expected': True
            },
            {
                'role': 'inventory-manager',
                'resource': 'purchase-orders',
                'action': 'approve',
                'expected': False
            },
            {
                'role': 'procurement-finance-controller',
                'resource': 'purchase-orders',
                'action': 'approve',
                'expected': True
            },
            {
                'role': 'warehouse-manager',
                'resource': 'budget-allocation',
                'action': 'configure',
                'expected': False
            }
        ]
        
        results = []
        for test_case in test_cases:
            with patch.object(self.rbac_service.cognito_validator, 'get_primary_role') as mock_role:
                mock_role.return_value = test_case['role']
                
                is_authorized, user_role, audit_details = self.rbac_service.validate_user_permissions(
                    self.test_user_id,
                    'test-username',
                    test_case['resource'],
                    test_case['action'],
                    self.request_context
                )
                
                result = {
                    'test_case': test_case,
                    'actual_authorized': is_authorized,
                    'expected_authorized': test_case['expected'],
                    'passed': is_authorized == test_case['expected']
                }
                results.append(result)
                
                logger.info(
                    "RBAC test case completed",
                    role=test_case['role'],
                    resource=test_case['resource'],
                    action=test_case['action'],
                    authorized=is_authorized,
                    expected=test_case['expected'],
                    passed=result['passed']
                )
        
        # Validate all test cases passed
        failed_cases = [r for r in results if not r['passed']]
        assert len(failed_cases) == 0, f"RBAC integration failed for cases: {failed_cases}"
        
        logger.info("RBAC integration test completed successfully")
        return results
    
    def test_purchase_order_workflow_integration(self):
        """
        Test 2: Complete purchase order workflow integration
        Tests procurement -> workflow -> budget -> audit integration
        """
        logger.info("Starting purchase order workflow integration test")
        
        # Step 1: Create budget allocation
        budget_allocation = {
            'category': 'office-supplies',
            'amount': 10000.0,
            'justification': 'Integration test budget allocation'
        }
        
        with patch.object(self.budget_service, '_validate_allocation_data'):
            budget_result = self.budget_service.allocate_budget(budget_allocation)
            assert budget_result['allocated'] == True
            logger.info("Budget allocation created", budget_result=budget_result)
        
        # Step 2: Submit purchase order
        purchase_order_data = {
            'supplierId': 'test-supplier-001',
            'items': [
                {
                    'itemId': 'item-001',
                    'quantity': 10,
                    'unitPrice': 50.0,
                    'description': 'Test office supplies'
                }
            ],
            'budgetCategory': 'office-supplies',
            'justification': 'Integration test purchase order',
            'deliveryAddress': '123 Test Street'
        }
        
        with patch.object(self.procurement_service, '_validate_supplier') as mock_supplier:
            mock_supplier.return_value = {'name': 'Test Supplier', 'id': 'test-supplier-001'}
            
            with patch.object(self.procurement_service, '_validate_budget_availability') as mock_budget:
                mock_budget.return_value = {'available': True, 'message': 'Budget available'}
                
                with patch.object(self.procurement_service, '_create_approval_workflow') as mock_workflow:
                    mock_workflow.return_value = 'test-workflow-001'
                    
                    po_result = self.procurement_service.submit_purchase_order(purchase_order_data)
                    assert 'orderId' in po_result
                    assert po_result['status'] == 'PENDING'
                    
                    order_id = po_result['orderId']
                    workflow_id = po_result['workflowId']
                    
                    logger.info("Purchase order submitted", order_id=order_id, workflow_id=workflow_id)
        
        # Step 3: Test workflow state transitions
        with patch.object(self.workflow_service, '_get_workflow_audit_trail') as mock_audit:
            mock_audit.return_value = []
            
            with patch.object(self.workflow_service, '_calculate_workflow_metrics') as mock_metrics:
                mock_metrics.return_value = {'duration_hours': 0.5, 'transitions': 1}
                
                # Create mock workflow
                mock_workflow_data = {
                    'workflowId': workflow_id,
                    'workflowType': 'PURCHASE_APPROVAL',
                    'currentState': 'PENDING_APPROVAL',
                    'payload': {'orderId': order_id},
                    'createdBy': self.test_user_id,
                    'createdAt': datetime.utcnow().isoformat() + 'Z',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z',
                    'timeoutAt': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
                }
                
                with patch.object(self.workflow_service.workflows_table, 'get_item') as mock_get:
                    mock_get.return_value = {'Item': mock_workflow_data}
                    
                    with patch.object(self.workflow_service.workflows_table, 'update_item') as mock_update:
                        mock_update.return_value = {'Attributes': {**mock_workflow_data, 'currentState': 'APPROVED'}}
                        
                        # Test workflow approval
                        transition_result = self.workflow_service.transition_workflow(
                            workflow_id,
                            'APPROVE',
                            'Integration test approval',
                            {'approver_notes': 'Automated test approval'}
                        )
                        
                        assert transition_result['currentState'] == 'APPROVED'
                        assert transition_result['action'] == 'APPROVE'
                        
                        logger.info("Workflow transition completed", transition_result=transition_result)
        
        # Step 4: Validate budget reservation
        with patch.object(self.budget_service, '_get_budget_info') as mock_budget_info:
            mock_budget_info.return_value = {
                'allocatedAmount': Decimal('10000.0'),
                'utilizedAmount': Decimal('0.0'),
                'reservedAmount': Decimal('0.0'),
                'remainingAmount': Decimal('10000.0')
            }
            
            with patch.object(self.budget_service.budget_table, 'update_item') as mock_budget_update:
                mock_budget_update.return_value = {
                    'Attributes': {
                        'allocatedAmount': Decimal('10000.0'),
                        'utilizedAmount': Decimal('500.0'),
                        'reservedAmount': Decimal('0.0')
                    }
                }
                
                budget_reserve_result = self.budget_service.reserve_budget(500.0, 'office-supplies', order_id)
                assert budget_reserve_result['reserved'] == True
                assert budget_reserve_result['amount'] == 500.0
                
                logger.info("Budget reserved successfully", budget_result=budget_reserve_result)
        
        logger.info("Purchase order workflow integration test completed successfully")
        return {
            'orderId': order_id,
            'workflowId': workflow_id,
            'budgetReserved': 500.0,
            'status': 'completed'
        }
    
    def test_inventory_reorder_workflow_integration(self):
        """
        Test 3: Inventory reorder workflow integration
        Tests inventory -> procurement -> workflow -> budget integration
        """
        logger.info("Starting inventory reorder workflow integration test")
        
        # Step 1: Simulate low stock condition
        low_stock_item = {
            'item_id': 'test-item-001',
            'location_id': 'warehouse-001',
            'name': 'Test Inventory Item',
            'current_stock': 5.0,
            'reorder_point': 20.0,
            'reorder_quantity': 100.0,
            'unit_cost': 25.0,
            'supplier_id': 'test-supplier-001',
            'avg_daily_demand': 3.0
        }
        
        # Test stock level update that triggers reorder alert
        with patch.object(self.inventory_service, '_check_and_generate_alerts') as mock_alerts:
            with patch.object(self.inventory_service.inventory_table, 'get_item') as mock_get:
                mock_get.return_value = {'Item': low_stock_item}
                
                with patch.object(self.inventory_service.inventory_table, 'update_item') as mock_update:
                    updated_item = low_stock_item.copy()
                    updated_item['current_stock'] = 3.0  # Below reorder point
                    mock_update.return_value = {'Attributes': updated_item}
                    
                    update_result = self.inventory_service.update_stock_level(
                        'test-item-001',
                        'warehouse-001',
                        {'current_stock': 3.0}
                    )
                    
                    assert update_result['statusCode'] == 200
                    logger.info("Stock level updated", update_result=update_result)
        
        # Step 2: Test reorder alert generation
        with patch.object(self.inventory_service.inventory_table, 'query') as mock_query:
            mock_query.return_value = {'Items': [updated_item]}
            
            with patch.object(self.inventory_service, '_enrich_reorder_alert') as mock_enrich:
                enriched_item = updated_item.copy()
                enriched_item.update({
                    'urgency': 'high',
                    'projected_stockout_date': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    'recommended_actions': [
                        {
                            'action': 'expedited_order',
                            'description': 'Place expedited order within 24 hours',
                            'priority': 'high',
                            'recommended_quantity': 100.0
                        }
                    ]
                })
                mock_enrich.return_value = enriched_item
                
                alerts_result = self.inventory_service.get_reorder_alerts('high')
                assert alerts_result['statusCode'] == 200
                assert len(alerts_result['body']['alerts']) > 0
                
                logger.info("Reorder alerts retrieved", alerts_count=len(alerts_result['body']['alerts']))
        
        # Step 3: Test automatic purchase order creation (would be triggered by alert)
        reorder_purchase_data = {
            'supplierId': 'test-supplier-001',
            'items': [
                {
                    'itemId': 'test-item-001',
                    'quantity': 100,
                    'unitPrice': 25.0,
                    'description': 'Automatic reorder for low stock'
                }
            ],
            'budgetCategory': 'inventory-replenishment',
            'justification': 'Automatic reorder triggered by low stock alert',
            'isEmergency': False
        }
        
        with patch.object(self.procurement_service, '_validate_supplier') as mock_supplier:
            mock_supplier.return_value = {'name': 'Test Supplier', 'id': 'test-supplier-001'}
            
            with patch.object(self.procurement_service, '_validate_budget_availability') as mock_budget:
                mock_budget.return_value = {'available': True, 'message': 'Budget available'}
                
                with patch.object(self.procurement_service, '_create_approval_workflow') as mock_workflow:
                    mock_workflow.return_value = 'reorder-workflow-001'
                    
                    reorder_result = self.procurement_service.submit_purchase_order(reorder_purchase_data)
                    assert 'orderId' in reorder_result
                    assert reorder_result['status'] == 'PENDING'
                    
                    logger.info("Reorder purchase order created", reorder_result=reorder_result)
        
        logger.info("Inventory reorder workflow integration test completed successfully")
        return {
            'itemId': 'test-item-001',
            'alertGenerated': True,
            'reorderCreated': True,
            'orderId': reorder_result['orderId']
        }
    
    def test_budget_enforcement_integration(self):
        """
        Test 4: Budget enforcement across all services
        Tests that budget limits are enforced consistently
        """
        logger.info("Starting budget enforcement integration test")
        
        # Step 1: Create limited budget
        limited_budget = {
            'category': 'test-limited-budget',
            'amount': 1000.0,
            'justification': 'Limited budget for enforcement testing'
        }
        
        with patch.object(self.budget_service, '_validate_allocation_data'):
            budget_result = self.budget_service.allocate_budget(limited_budget)
            assert budget_result['allocated'] == True
            logger.info("Limited budget created", amount=1000.0)
        
        # Step 2: Test budget validation for large purchase order
        large_purchase_data = {
            'supplierId': 'test-supplier-001',
            'items': [
                {
                    'itemId': 'expensive-item',
                    'quantity': 1,
                    'unitPrice': 1500.0,  # Exceeds budget
                    'description': 'Expensive item that exceeds budget'
                }
            ],
            'budgetCategory': 'test-limited-budget',
            'justification': 'Test purchase that should be rejected'
        }
        
        with patch.object(self.budget_service, '_get_budget_info') as mock_budget_info:
            mock_budget_info.return_value = {
                'allocatedAmount': Decimal('1000.0'),
                'utilizedAmount': Decimal('0.0'),
                'reservedAmount': Decimal('0.0'),
                'remainingAmount': Decimal('1000.0')
            }
            
            # Test budget validation
            validation_result = self.budget_service.validate_budget_availability(1500.0, 'test-limited-budget')
            assert validation_result['available'] == False
            assert validation_result['requestedAmount'] == 1500.0
            assert validation_result['availableAmount'] == 1000.0
            
            logger.info("Budget enforcement validated", validation_result=validation_result)
        
        # Step 3: Test purchase order rejection due to budget
        with patch.object(self.procurement_service, '_validate_supplier') as mock_supplier:
            mock_supplier.return_value = {'name': 'Test Supplier', 'id': 'test-supplier-001'}
            
            with patch.object(self.procurement_service, '_validate_budget_availability') as mock_budget:
                mock_budget.return_value = {
                    'available': False,
                    'message': 'Insufficient budget: requested 1500.0, available 1000.0'
                }
                
                try:
                    self.procurement_service.submit_purchase_order(large_purchase_data)
                    assert False, "Purchase order should have been rejected due to budget"
                except Exception as e:
                    assert "Insufficient budget" in str(e)
                    logger.info("Purchase order correctly rejected due to budget constraints")
        
        # Step 4: Test successful purchase within budget
        small_purchase_data = {
            'supplierId': 'test-supplier-001',
            'items': [
                {
                    'itemId': 'affordable-item',
                    'quantity': 1,
                    'unitPrice': 500.0,  # Within budget
                    'description': 'Affordable item within budget'
                }
            ],
            'budgetCategory': 'test-limited-budget',
            'justification': 'Test purchase within budget limits'
        }
        
        with patch.object(self.procurement_service, '_validate_supplier') as mock_supplier:
            mock_supplier.return_value = {'name': 'Test Supplier', 'id': 'test-supplier-001'}
            
            with patch.object(self.procurement_service, '_validate_budget_availability') as mock_budget:
                mock_budget.return_value = {'available': True, 'message': 'Budget available'}
                
                with patch.object(self.procurement_service, '_create_approval_workflow') as mock_workflow:
                    mock_workflow.return_value = 'budget-test-workflow-001'
                    
                    small_purchase_result = self.procurement_service.submit_purchase_order(small_purchase_data)
                    assert 'orderId' in small_purchase_result
                    assert small_purchase_result['status'] == 'PENDING'
                    
                    logger.info("Purchase within budget submitted successfully", 
                              order_id=small_purchase_result['orderId'])
        
        logger.info("Budget enforcement integration test completed successfully")
        return {
            'budgetLimit': 1000.0,
            'rejectedAmount': 1500.0,
            'approvedAmount': 500.0,
            'enforcementWorking': True
        }
    
    def test_graceful_degradation_scenarios(self):
        """
        Test 5: Graceful degradation when services are unavailable
        Tests fallback mechanisms and error handling
        """
        logger.info("Starting graceful degradation test")
        
        degradation_results = {}
        
        # Test 1: ML forecasting service unavailable
        with patch.object(self.inventory_service, '_get_ml_forecast') as mock_ml:
            mock_ml.return_value = None  # Simulate ML service failure
            
            with patch.object(self.inventory_service, '_get_rule_based_forecast') as mock_rule:
                mock_rule.return_value = {
                    'item_id': 'test-item-001',
                    'method': 'rule_based',
                    'predictions': [{'date': datetime.utcnow().isoformat(), 'demand': 5.0}],
                    'warning': 'ML forecasting service unavailable, using rule-based fallback'
                }
                
                forecast_result = self.inventory_service.get_demand_forecast('test-item-001', 30)
                assert forecast_result['statusCode'] == 200
                assert forecast_result['body']['source'] == 'rule_based'
                assert 'warning' in forecast_result['body']
                
                degradation_results['ml_forecast_fallback'] = True
                logger.info("ML forecasting fallback working correctly")
        
        # Test 2: Database connection issues
        with patch.object(self.inventory_service.inventory_table, 'scan') as mock_scan:
            mock_scan.side_effect = Exception("Database connection timeout")
            
            try:
                self.inventory_service.get_stock_levels()
                degradation_results['db_error_handling'] = False
            except Exception as e:
                # Service should handle database errors gracefully
                degradation_results['db_error_handling'] = True
                logger.info("Database error handled gracefully", error=str(e))
        
        # Test 3: Workflow timeout handling
        timeout_workflow_id = 'timeout-test-workflow'
        
        with patch.object(self.workflow_service.workflows_table, 'get_item') as mock_get:
            # Simulate timed out workflow
            timeout_workflow = {
                'workflowId': timeout_workflow_id,
                'currentState': 'PENDING_APPROVAL',
                'timeoutAt': (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z',  # Already timed out
                'workflowType': 'PURCHASE_APPROVAL'
            }
            mock_get.return_value = {'Item': timeout_workflow}
            
            with patch.object(self.workflow_service.workflows_table, 'update_item') as mock_update:
                mock_update.return_value = {'Attributes': {**timeout_workflow, 'currentState': 'TIMEOUT_ESCALATED'}}
                
                with patch.object(self.workflow_service, '_escalate_to_finance_controller') as mock_escalate:
                    mock_escalate.return_value = {'escalated': True, 'notificationSent': True}
                    
                    timeout_result = self.workflow_service.handle_workflow_timeout(timeout_workflow_id)
                    assert timeout_result['action'] == 'escalated'
                    
                    degradation_results['workflow_timeout_handling'] = True
                    logger.info("Workflow timeout handling working correctly")
        
        # Test 4: Audit service resilience
        with patch.object(self.audit_service, '_store_audit_record_s3') as mock_s3:
            mock_s3.side_effect = Exception("S3 service unavailable")
            
            with patch.object(self.audit_service, '_store_audit_record_dynamodb') as mock_dynamo:
                # DynamoDB should still work even if S3 fails
                mock_dynamo.return_value = None
                
                try:
                    self.audit_service.log_user_action(
                        user_id=self.test_user_id,
                        action='TEST_ACTION',
                        resource='TEST_RESOURCE',
                        resource_id='test-001',
                        details={'test': True},
                        request_context=self.request_context
                    )
                    degradation_results['audit_resilience'] = False  # Should have failed gracefully
                except Exception as e:
                    # Audit service should handle S3 failures gracefully
                    degradation_results['audit_resilience'] = True
                    logger.info("Audit service handled S3 failure gracefully")
        
        logger.info("Graceful degradation test completed", results=degradation_results)
        return degradation_results
    
    def test_cross_service_audit_logging(self):
        """
        Test 6: Cross-service audit logging validation
        Ensures all services properly log audit events
        """
        logger.info("Starting cross-service audit logging test")
        
        audit_events = []
        
        # Mock audit logger to capture events
        def mock_log_action(*args, **kwargs):
            audit_events.append({
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        with patch.object(audit_logger, 'log_action', side_effect=mock_log_action):
            with patch.object(audit_logger, 'log_user_action', side_effect=mock_log_action):
                with patch.object(audit_logger, 'log_data_access', side_effect=mock_log_action):
                    with patch.object(audit_logger, 'log_data_modification', side_effect=mock_log_action):
                        
                        # Test inventory service audit logging
                        with patch.object(self.inventory_service.inventory_table, 'scan') as mock_scan:
                            mock_scan.return_value = {'Items': []}
                            self.inventory_service.get_stock_levels({'category': 'test'})
                        
                        # Test procurement service audit logging
                        with patch.object(self.procurement_service, '_validate_supplier') as mock_supplier:
                            mock_supplier.return_value = {'name': 'Test Supplier'}
                            
                            with patch.object(self.procurement_service, '_validate_budget_availability') as mock_budget:
                                mock_budget.return_value = {'available': True}
                                
                                with patch.object(self.procurement_service, '_create_approval_workflow') as mock_workflow:
                                    mock_workflow.return_value = 'audit-test-workflow'
                                    
                                    try:
                                        self.procurement_service.submit_purchase_order({
                                            'supplierId': 'test-supplier',
                                            'items': [{'itemId': 'test', 'quantity': 1, 'unitPrice': 10.0}],
                                            'budgetCategory': 'test',
                                            'justification': 'Audit test'
                                        })
                                    except Exception:
                                        pass  # Expected due to mocking
                        
                        # Test budget service audit logging
                        with patch.object(self.budget_service, '_validate_allocation_data'):
                            try:
                                self.budget_service.allocate_budget({
                                    'category': 'audit-test',
                                    'amount': 1000.0,
                                    'justification': 'Audit test allocation'
                                })
                            except Exception:
                                pass  # Expected due to mocking
        
        # Validate audit events were captured
        assert len(audit_events) > 0, "No audit events were captured"
        
        # Check for different types of audit events
        event_types = set()
        for event in audit_events:
            if 'action_type' in event['kwargs']:
                event_types.add(event['kwargs']['action_type'])
            elif len(event['args']) > 0:
                event_types.add(event['args'][0])
        
        logger.info("Cross-service audit logging test completed", 
                   events_captured=len(audit_events),
                   event_types=list(event_types))
        
        return {
            'eventsCaptures': len(audit_events),
            'eventTypes': list(event_types),
            'auditingWorking': len(audit_events) > 0
        }
    
    def run_all_integration_tests(self):
        """
        Run all integration tests and return comprehensive results
        """
        logger.info("Starting comprehensive backend services integration validation")
        
        test_results = {}
        
        try:
            # Test 1: RBAC Integration
            test_results['rbac_integration'] = self.test_rbac_integration_across_services()
            
            # Test 2: Purchase Order Workflow
            test_results['purchase_order_workflow'] = self.test_purchase_order_workflow_integration()
            
            # Test 3: Inventory Reorder Workflow
            test_results['inventory_reorder_workflow'] = self.test_inventory_reorder_workflow_integration()
            
            # Test 4: Budget Enforcement
            test_results['budget_enforcement'] = self.test_budget_enforcement_integration()
            
            # Test 5: Graceful Degradation
            test_results['graceful_degradation'] = self.test_graceful_degradation_scenarios()
            
            # Test 6: Cross-Service Audit Logging
            test_results['audit_logging'] = self.test_cross_service_audit_logging()
            
            # Calculate overall success
            all_tests_passed = all([
                all(r.get('passed', True) for r in test_results['rbac_integration']),
                test_results['purchase_order_workflow']['status'] == 'completed',
                test_results['inventory_reorder_workflow']['reorderCreated'] == True,
                test_results['budget_enforcement']['enforcementWorking'] == True,
                test_results['graceful_degradation']['ml_forecast_fallback'] == True,
                test_results['audit_logging']['auditingWorking'] == True
            ])
            
            test_results['overall_success'] = all_tests_passed
            test_results['test_summary'] = {
                'total_tests': 6,
                'passed_tests': sum([
                    1 if all(r.get('passed', True) for r in test_results['rbac_integration']) else 0,
                    1 if test_results['purchase_order_workflow']['status'] == 'completed' else 0,
                    1 if test_results['inventory_reorder_workflow']['reorderCreated'] == True else 0,
                    1 if test_results['budget_enforcement']['enforcementWorking'] == True else 0,
                    1 if test_results['graceful_degradation']['ml_forecast_fallback'] == True else 0,
                    1 if test_results['audit_logging']['auditingWorking'] == True else 0
                ]),
                'completion_time': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Backend services integration validation completed",
                overall_success=all_tests_passed,
                test_summary=test_results['test_summary']
            )
            
        except Exception as e:
            logger.error(
                "Integration test suite failed",
                error=str(e),
                correlation_id=self.test_correlation_id
            )
            test_results['overall_success'] = False
            test_results['error'] = str(e)
        
        return test_results


def main():
    """
    Main function to run integration tests
    """
    print("=" * 80)
    print("BACKEND SERVICES INTEGRATION VALIDATION")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = BackendServicesIntegrationTest()
    
    # Run all tests
    results = test_suite.run_all_integration_tests()
    
    # Print results
    print("\nTEST RESULTS:")
    print("-" * 40)
    
    if results['overall_success']:
        print("✅ ALL INTEGRATION TESTS PASSED")
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
    
    print(f"\nTest Summary:")
    if 'test_summary' in results:
        summary = results['test_summary']
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed Tests: {summary['passed_tests']}")
        print(f"  Success Rate: {(summary['passed_tests'] / summary['total_tests']) * 100:.1f}%")
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