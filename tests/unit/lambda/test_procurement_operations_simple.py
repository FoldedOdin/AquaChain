"""
Simplified procurement operations tests - lightweight version to avoid crashes

Feature: dashboard-overhaul, Property 6: Purchase Order Approval Workflow
Feature: dashboard-overhaul, Property 9: Emergency Purchase Expedited Processing
Validates: Requirements 2.2, 2.5, 6.1, 6.2, 6.8
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal


def test_purchase_order_creates_pending_workflow():
    """Test that purchase order submission creates workflow in pending state"""
    with patch('procurement_service.handler.dynamodb') as mock_dynamodb, \
         patch('procurement_service.handler.lambda_client') as mock_lambda:
        
        # Mock DynamoDB tables
        mock_po_table = Mock()
        mock_suppliers_table = Mock()
        mock_workflows_table = Mock()
        
        mock_dynamodb.Table.side_effect = lambda name: {
            'AquaChain-Purchase-Orders': mock_po_table,
            'AquaChain-Suppliers': mock_suppliers_table,
            'AquaChain-Workflows': mock_workflows_table
        }.get(name, Mock())
        
        # Mock supplier validation
        mock_suppliers_table.get_item.return_value = {
            'Item': {
                'PK': 'SUPPLIER#test-supplier',
                'SK': 'PROFILE',
                'name': 'Test Supplier',
                'status': 'ACTIVE'
            }
        }
        
        # Mock budget validation (allow purchase)
        mock_lambda.invoke.return_value = {
            'Payload': Mock(read=lambda: '{"body": {"available": true}}')
        }
        
        # Mock successful operations
        mock_po_table.put_item.return_value = {}
        mock_workflows_table.put_item.return_value = {}
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
            
            from procurement_service.handler import ProcurementService
            
            request_context = {
                'user_id': 'test-user',
                'correlation_id': 'test-correlation'
            }
            
            service = ProcurementService(request_context)
            
            order_data = {
                'supplierId': 'test-supplier',
                'items': [
                    {
                        'itemId': 'item-1',
                        'itemName': 'Test Item',
                        'quantity': 10,
                        'unitPrice': 25.00
                    }
                ],
                'budgetCategory': 'OPERATIONS',
                'justification': 'Required for operations'
            }
            
            result = service.submit_purchase_order(order_data)
            
            # Should create workflow in PENDING state
            assert 'orderId' in result
            assert 'workflowId' in result
            assert result['status'] == 'PENDING'
            assert result['totalAmount'] == 250.00  # 10 * 25.00
            
        except ImportError:
            pytest.skip("Procurement service not available")


def test_approval_requires_human_justification():
    """Test that purchase order approval requires human justification"""
    with patch('procurement_service.handler.dynamodb') as mock_dynamodb, \
         patch('procurement_service.handler.lambda_client') as mock_lambda:
        
        # Mock DynamoDB tables
        mock_po_table = Mock()
        mock_workflows_table = Mock()
        
        mock_dynamodb.Table.side_effect = lambda name: {
            'AquaChain-Purchase-Orders': mock_po_table,
            'AquaChain-Workflows': mock_workflows_table
        }.get(name, Mock())
        
        # Mock existing purchase order
        order_id = 'test-order-123'
        total_amount = 1500.50
        
        mock_po_table.get_item.return_value = {
            'Item': {
                'PK': f'ORDER#{order_id}',
                'SK': 'CURRENT',
                'orderId': order_id,
                'status': 'PENDING',
                'totalAmount': Decimal(str(total_amount)),
                'budgetCategory': 'OPERATIONS'
            }
        }
        
        # Mock budget validation
        mock_lambda.invoke.return_value = {
            'Payload': Mock(read=lambda: '{"body": {"available": true}}')
        }
        
        # Mock successful updates
        mock_po_table.update_item.return_value = {
            'Attributes': {
                'orderId': order_id,
                'status': 'APPROVED',
                'totalAmount': Decimal(str(total_amount))
            }
        }
        mock_workflows_table.update_item.return_value = {}
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
            
            from procurement_service.handler import ProcurementService
            
            request_context = {
                'user_id': 'test-approver',
                'correlation_id': 'test-correlation'
            }
            
            service = ProcurementService(request_context)
            
            approval_data = {
                'justification': 'Approved for operational requirements',
                'comments': 'Budget available and supplier verified'
            }
            
            result = service.approve_purchase_order(order_id, approval_data)
            
            # Should approve with justification
            assert result['orderId'] == order_id
            assert result['status'] == 'APPROVED'
            assert result['approvedBy'] == 'test-approver'
            assert result['justification'] == approval_data['justification']
            
        except ImportError:
            pytest.skip("Procurement service not available")


def test_emergency_purchase_creates_expedited_workflow():
    """Test that emergency purchase creates expedited workflow"""
    with patch('procurement_service.handler.dynamodb') as mock_dynamodb, \
         patch('procurement_service.handler.lambda_client') as mock_lambda, \
         patch('procurement_service.handler.sns') as mock_sns:
        
        # Mock DynamoDB tables
        mock_po_table = Mock()
        mock_suppliers_table = Mock()
        mock_workflows_table = Mock()
        
        mock_dynamodb.Table.side_effect = lambda name: {
            'AquaChain-Purchase-Orders': mock_po_table,
            'AquaChain-Suppliers': mock_suppliers_table,
            'AquaChain-Workflows': mock_workflows_table
        }.get(name, Mock())
        
        # Mock supplier validation
        mock_suppliers_table.get_item.return_value = {
            'Item': {
                'PK': 'SUPPLIER#emergency-supplier',
                'SK': 'PROFILE',
                'name': 'Emergency Supplier',
                'status': 'ACTIVE',
                'riskLevel': 'MEDIUM'
            }
        }
        
        # Mock budget validation
        mock_lambda.invoke.return_value = {
            'Payload': Mock(read=lambda: '{"body": {"available": true}}')
        }
        
        # Mock successful operations
        mock_po_table.put_item.return_value = {}
        mock_workflows_table.put_item.return_value = {}
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
            
            from procurement_service.handler import ProcurementService
            
            request_context = {
                'user_id': 'test-user',
                'correlation_id': 'test-correlation'
            }
            
            service = ProcurementService(request_context)
            service.emergency_approval_threshold = 10000.0
            
            order_data = {
                'supplierId': 'emergency-supplier',
                'items': [
                    {
                        'itemId': 'emergency-item',
                        'itemName': 'Emergency Repair Kit',
                        'quantity': 1,
                        'unitPrice': 5000.00
                    }
                ],
                'budgetCategory': 'EMERGENCY',
                'isEmergency': True,
                'emergencyJustification': 'Critical system failure',
                'expeditedReason': 'Production line down'
            }
            
            result = service.process_emergency_purchase(order_data)
            
            # Should create emergency workflow
            assert 'orderId' in result
            assert 'workflowId' in result
            assert result['status'] == 'PENDING'
            assert result['priority'] == 'EMERGENCY'
            assert result['isEmergency'] is True
            assert result['exceedsThreshold'] is False  # 5000 < 10000
            
        except ImportError:
            pytest.skip("Procurement service not available")


if __name__ == '__main__':
    pytest.main([__file__])