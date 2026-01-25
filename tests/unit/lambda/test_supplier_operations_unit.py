"""
Unit tests for supplier operations - Task 6.2
Tests supplier CRUD operations, performance scoring calculations,
and risk assessment logic.

Requirements: 1.3, 2.7
"""

import pytest
import json
import boto3
from moto import mock_aws
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

from supplier_management.handler import (
    SupplierManager, 
    SupplierRiskAssessment, 
    ContractManager,
    lambda_handler
)

# Mock the audit_logger at module level
import supplier_management.handler
supplier_management.handler.audit_logger = Mock()


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_tables(aws_credentials):
    """Create mock DynamoDB tables for testing."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create suppliers table
        suppliers_table = dynamodb.create_table(
            TableName='AquaChain-Suppliers',
            KeySchema=[
                {'AttributeName': 'supplier_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                {'AttributeName': 'supplier_type', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'supplier_type', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create contracts table
        contracts_table = dynamodb.create_table(
            TableName='AquaChain-Supplier-Contracts',
            KeySchema=[
                {'AttributeName': 'supplier_id', 'KeyType': 'HASH'},
                {'AttributeName': 'contract_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                {'AttributeName': 'contract_id', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create purchase orders table
        purchase_orders_table = dynamodb.create_table(
            TableName='AquaChain-Purchase-Orders',
            KeySchema=[
                {'AttributeName': 'po_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'po_id', 'AttributeType': 'S'},
                {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SupplierOrdersIndex',
                    'KeySchema': [
                        {'AttributeName': 'supplier_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create financial data table
        financial_data_table = dynamodb.create_table(
            TableName='AquaChain-Financial-Data',
            KeySchema=[
                {'AttributeName': 'supplier_id', 'KeyType': 'HASH'},
                {'AttributeName': 'data_type', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'supplier_id', 'AttributeType': 'S'},
                {'AttributeName': 'data_type', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create inventory table
        inventory_table = dynamodb.create_table(
            TableName='AquaChain-Inventory-Items',
            KeySchema=[
                {'AttributeName': 'item_id', 'KeyType': 'HASH'},
                {'AttributeName': 'location_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'item_id', 'AttributeType': 'S'},
                {'AttributeName': 'location_id', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create audit logs table
        audit_logs_table = dynamodb.create_table(
            TableName='aquachain-dev-audit-logs',
            KeySchema=[
                {'AttributeName': 'log_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'log_id', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Patch the module-level table references
        with patch('supplier_management.handler.suppliers_table', suppliers_table), \
             patch('supplier_management.handler.contracts_table', contracts_table), \
             patch('supplier_management.handler.purchase_orders_table', purchase_orders_table), \
             patch('supplier_management.handler.financial_data_table', financial_data_table), \
             patch('supplier_management.handler.inventory_table', inventory_table):
            
            yield {
                'suppliers_table': suppliers_table,
                'contracts_table': contracts_table,
                'purchase_orders_table': purchase_orders_table,
                'financial_data_table': financial_data_table,
                'inventory_table': inventory_table,
                'audit_logs_table': audit_logs_table
            }


@pytest.fixture
def supplier_manager():
    """Create supplier manager instance for testing."""
    return SupplierManager()


@pytest.fixture
def risk_assessment():
    """Create risk assessment instance for testing."""
    return SupplierRiskAssessment()


@pytest.fixture
def contract_manager():
    """Create contract manager instance for testing."""
    return ContractManager()


@pytest.fixture
def sample_suppliers():
    """Sample supplier data for testing."""
    return [
        {
            'supplier_id': 'SUP-001',
            'name': 'Test Supplier 1',
            'supplier_type': 'equipment',
            'contact_email': 'supplier1@test.com',
            'status': 'active',
            'performance_score': Decimal('85'),
            'risk_level': 'LOW',
            'total_orders': 10,
            'on_time_deliveries': 9
        },
        {
            'supplier_id': 'SUP-002',
            'name': 'Test Supplier 2',
            'supplier_type': 'materials',
            'contact_email': 'supplier2@test.com',
            'status': 'active',
            'performance_score': Decimal('70'),
            'risk_level': 'MEDIUM',
            'total_orders': 5,
            'on_time_deliveries': 3
        }
    ]


@pytest.fixture
def sample_purchase_orders():
    """Sample purchase order data for testing."""
    return [
        {
            'po_id': 'PO-001',
            'supplier_id': 'SUP-001',
            'status': 'delivered',
            'total_amount': Decimal('1000'),
            'created_date': '2024-01-01T10:00:00Z',
            'expected_delivery': '2024-01-10T10:00:00Z',
            'actual_delivery_date': '2024-01-09T10:00:00Z',
            'quality_issues': 0
        },
        {
            'po_id': 'PO-002',
            'supplier_id': 'SUP-001',
            'status': 'delivered',
            'total_amount': Decimal('2000'),
            'created_date': '2024-01-05T10:00:00Z',
            'expected_delivery': '2024-01-15T10:00:00Z',
            'actual_delivery_date': '2024-01-16T10:00:00Z',  # Late delivery
            'quality_issues': 1
        },
        {
            'po_id': 'PO-003',
            'supplier_id': 'SUP-002',
            'status': 'pending',
            'total_amount': Decimal('500'),
            'created_date': '2024-01-10T10:00:00Z',
            'expected_delivery': '2024-01-20T10:00:00Z'
        }
    ]


class TestSupplierCRUDOperations:
    """Test supplier CRUD operations."""
    
    @patch('supplier_management.handler.audit_logger')
    def test_create_supplier_success(self, mock_audit_logger, mock_tables, supplier_manager):
        """Test successful supplier creation."""
        supplier_data = {
            'name': 'New Test Supplier',
            'supplier_type': 'equipment',
            'contact_email': 'newtest@supplier.com',
            'phone': '+1-555-0123',
            'address': '123 Test St, Test City'
        }
        
        user_id = 'test-user'
        request_context = {
            'ip_address': '127.0.0.1',
            'user_agent': 'test-agent',
            'request_id': 'test-request-123'
        }
        
        result = supplier_manager.create_supplier(supplier_data, user_id, request_context)
        
        assert result['statusCode'] == 201
        assert 'supplier' in result['body']
        assert result['body']['supplier']['name'] == 'New Test Supplier'
        assert result['body']['supplier']['status'] == 'active'
        assert result['body']['supplier']['performance_score'] == Decimal('75')
        assert 'supplier_id' in result['body']['supplier']
    
    @patch('supplier_management.handler.audit_logger')
    def test_create_supplier_missing_fields(self, mock_audit_logger, mock_tables, supplier_manager):
        """Test supplier creation with missing required fields."""
        supplier_data = {
            'name': 'Incomplete Supplier',
            # Missing supplier_type, contact_email
        }
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = supplier_manager.create_supplier(supplier_data, user_id, request_context)
        
        assert result['statusCode'] == 400
        assert 'Missing required field' in result['body']['error']
    
    @patch('supplier_management.handler.audit_logger')
    def test_get_suppliers_success(self, mock_audit_logger, mock_tables, supplier_manager, sample_suppliers):
        """Test successful supplier retrieval."""
        # Add sample suppliers
        for supplier in sample_suppliers:
            mock_tables['suppliers_table'].put_item(Item=supplier)
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = supplier_manager.get_suppliers(None, user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 2
        assert len(result['body']['suppliers']) == 2
        assert result['body']['active_count'] == 2
    
    @patch('supplier_management.handler.audit_logger')
    def test_get_suppliers_with_filters(self, mock_audit_logger, mock_tables, supplier_manager, sample_suppliers):
        """Test supplier retrieval with filters."""
        # Add sample suppliers
        for supplier in sample_suppliers:
            mock_tables['suppliers_table'].put_item(Item=supplier)
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        # Test filter by supplier type
        result = supplier_manager.get_suppliers({'supplier_type': 'equipment'}, user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 1
        assert result['body']['suppliers'][0]['supplier_type'] == 'equipment'
        
        # Test filter by status
        result = supplier_manager.get_suppliers({'status': 'active'}, user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 2
    
    @patch('supplier_management.handler.audit_logger')
    def test_update_supplier_success(self, mock_audit_logger, mock_tables, supplier_manager, sample_suppliers):
        """Test successful supplier update."""
        # Add sample supplier
        supplier = sample_suppliers[0]
        mock_tables['suppliers_table'].put_item(Item=supplier)
        
        updates = {
            'contact_email': 'updated@supplier.com',
            'phone': '+1-555-9999',
            'status': 'inactive'
        }
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = supplier_manager.update_supplier('SUP-001', updates, user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['supplier']['contact_email'] == 'updated@supplier.com'
        assert result['body']['supplier']['phone'] == '+1-555-9999'
        assert result['body']['supplier']['status'] == 'inactive'
    
    @patch('supplier_management.handler.audit_logger')
    def test_update_supplier_not_found(self, mock_audit_logger, mock_tables, supplier_manager):
        """Test supplier update with non-existent supplier."""
        updates = {'contact_email': 'updated@supplier.com'}
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = supplier_manager.update_supplier('NONEXISTENT', updates, user_id, request_context)
        
        assert result['statusCode'] == 404
        assert 'Supplier not found' in result['body']['error']


class TestPerformanceScoringCalculations:
    """Test performance scoring calculations."""
    
    def test_calculate_comprehensive_performance_metrics_success(self, mock_tables, supplier_manager, sample_purchase_orders):
        """Test comprehensive performance metrics calculation."""
        # Add sample purchase orders
        for order in sample_purchase_orders:
            mock_tables['purchase_orders_table'].put_item(Item=order)
        
        # Test performance calculation for SUP-001
        metrics = supplier_manager._calculate_comprehensive_performance_metrics('SUP-001')
        
        assert metrics['total_orders'] == 2
        assert metrics['delivered_orders'] == 2
        assert metrics['pending_orders'] == 0
        assert metrics['on_time_delivery_rate'] == 50.0  # 1 out of 2 on time
        assert metrics['quality_score'] == 50.0  # 1 quality issue out of 2 orders
        assert metrics['total_value'] == 3000.0  # 1000 + 2000
        assert metrics['average_order_value'] == 1500.0
        assert 'overall_score' in metrics
        assert 'last_updated' in metrics
    
    def test_calculate_comprehensive_performance_metrics_no_orders(self, mock_tables, supplier_manager):
        """Test performance metrics calculation with no orders."""
        metrics = supplier_manager._calculate_comprehensive_performance_metrics('NONEXISTENT')
        
        assert metrics['total_orders'] == 0
        assert metrics['on_time_delivery_rate'] == 0
        assert metrics['quality_score'] == 0
        assert metrics['average_lead_time'] == 0
        assert metrics['total_value'] == 0
        assert metrics['overall_score'] == 0
    
    def test_is_delivery_on_time_success(self, supplier_manager):
        """Test on-time delivery calculation."""
        # On-time delivery
        order_on_time = {
            'expected_delivery': '2024-01-10T10:00:00Z',
            'actual_delivery_date': '2024-01-09T10:00:00Z'
        }
        
        assert supplier_manager._is_delivery_on_time(order_on_time) is True
        
        # Late delivery
        order_late = {
            'expected_delivery': '2024-01-10T10:00:00Z',
            'actual_delivery_date': '2024-01-11T10:00:00Z'
        }
        
        assert supplier_manager._is_delivery_on_time(order_late) is False
        
        # Missing data
        order_incomplete = {
            'expected_delivery': '2024-01-10T10:00:00Z'
            # Missing actual_delivery_date
        }
        
        assert supplier_manager._is_delivery_on_time(order_incomplete) is False
    
    def test_generate_comprehensive_recommendations(self, mock_tables, supplier_manager, sample_suppliers):
        """Test comprehensive recommendation generation."""
        supplier = sample_suppliers[0]  # High performance supplier
        
        performance = {
            'overall_score': 95,
            'on_time_delivery_rate': 95,
            'quality_score': 98
        }
        
        risk = {
            'risk_level': 'LOW',
            'overall_risk_score': 85
        }
        
        recommendations = supplier_manager._generate_comprehensive_recommendations(supplier, performance, risk)
        
        assert len(recommendations) > 0
        assert any('preferred vendor status' in rec for rec in recommendations)
        assert any('Low risk supplier' in rec for rec in recommendations)
        
        # Test poor performance supplier
        poor_performance = {
            'overall_score': 45,
            'on_time_delivery_rate': 60,
            'quality_score': 70
        }
        
        high_risk = {
            'risk_level': 'HIGH',
            'overall_risk_score': 35
        }
        
        recommendations = supplier_manager._generate_comprehensive_recommendations(supplier, poor_performance, high_risk)
        
        assert any('Poor performance' in rec for rec in recommendations)
        assert any('Address delivery performance' in rec for rec in recommendations)
        assert any('Monitor closely' in rec for rec in recommendations)


class TestRiskAssessmentLogic:
    """Test risk assessment logic."""
    
    def test_calculate_financial_risk_score_success(self, mock_tables, risk_assessment, sample_purchase_orders):
        """Test financial risk score calculation."""
        # Add sample purchase orders for performance metrics
        for order in sample_purchase_orders:
            mock_tables['purchase_orders_table'].put_item(Item=order)
        
        financial_data = {
            'credit_rating': 'A',
            'debt_to_equity_ratio': 0.5,
            'cash_flow_trend': 0.1,
            'market_reputation_score': 85,
            'industry_rating': 'Good'
        }
        
        result = risk_assessment.calculate_financial_risk_score('SUP-001', financial_data)
        
        assert 'supplier_id' in result
        assert 'overall_risk_score' in result
        assert 'risk_level' in result
        assert 'risk_indicators' in result
        assert 'recommendations' in result
        assert result['supplier_id'] == 'SUP-001'
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0 <= result['overall_risk_score'] <= 100
    
    def test_calculate_financial_risk_score_high_risk(self, mock_tables, risk_assessment):
        """Test financial risk score calculation for high-risk supplier."""
        financial_data = {
            'credit_rating': 'C',
            'debt_to_equity_ratio': 2.0,
            'cash_flow_trend': -0.2,
            'market_reputation_score': 40,
            'industry_rating': 'Poor'
        }
        
        result = risk_assessment.calculate_financial_risk_score('SUP-002', financial_data)
        
        assert result['risk_level'] in ['HIGH', 'CRITICAL']
        assert result['overall_risk_score'] < 60
        assert len(result['recommendations']) > 0
    
    def test_get_supplier_performance_metrics(self, mock_tables, risk_assessment, sample_purchase_orders):
        """Test supplier performance metrics retrieval for risk assessment."""
        # Add sample purchase orders
        for order in sample_purchase_orders:
            mock_tables['purchase_orders_table'].put_item(Item=order)
        
        metrics = risk_assessment._get_supplier_performance_metrics('SUP-001')
        
        assert 'on_time_delivery_rate' in metrics
        assert 'quality_score' in metrics
        assert 'defect_rate' in metrics
        assert 'total_orders' in metrics
        assert 'delivered_orders' in metrics
        
        # Verify calculations
        assert metrics['total_orders'] == 2
        assert metrics['delivered_orders'] == 2
        assert metrics['on_time_delivery_rate'] == 50.0  # 1 out of 2 on time
        assert metrics['defect_rate'] == 50.0  # 1 quality issue out of 2 orders
        assert metrics['quality_score'] == 50.0  # 100 - defect_rate
    
    def test_get_supplier_performance_metrics_no_orders(self, mock_tables, risk_assessment):
        """Test performance metrics with no orders."""
        metrics = risk_assessment._get_supplier_performance_metrics('NONEXISTENT')
        
        assert metrics['on_time_delivery_rate'] == 0
        assert metrics['quality_score'] == 0
        assert metrics['defect_rate'] == 0
        assert metrics['total_orders'] == 0
        assert metrics['delivered_orders'] == 0
    
    def test_generate_risk_recommendations(self, risk_assessment):
        """Test risk recommendation generation."""
        # Critical risk level
        critical_indicators = {
            'financial_stability': {'score': 20},
            'delivery_performance': {'score': 30},
            'quality_score': {'score': 40},
            'contract_compliance': {'score': 50},
            'market_reputation': {'score': 30}
        }
        
        recommendations = risk_assessment._generate_risk_recommendations('CRITICAL', critical_indicators)
        
        assert len(recommendations) > 0
        assert any('URGENT' in rec for rec in recommendations)
        assert any('immediate supplier review' in rec for rec in recommendations)
        
        # Low risk level
        low_risk_indicators = {
            'financial_stability': {'score': 90},
            'delivery_performance': {'score': 95},
            'quality_score': {'score': 98},
            'contract_compliance': {'score': 92},
            'market_reputation': {'score': 88}
        }
        
        recommendations = risk_assessment._generate_risk_recommendations('LOW', low_risk_indicators)
        
        # Should have fewer or no urgent recommendations
        assert not any('URGENT' in rec for rec in recommendations)


class TestContractManagement:
    """Test contract management operations."""
    
    @patch('supplier_management.handler.audit_logger')
    def test_create_contract_success(self, mock_audit_logger, mock_tables, contract_manager):
        """Test successful contract creation."""
        contract_data = {
            'supplier_id': 'SUP-001',
            'contract_type': 'service_agreement',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'contract_value': 50000,
            'terms': 'Standard service agreement terms'
        }
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = contract_manager.create_contract(contract_data, user_id, request_context)
        
        assert result['statusCode'] == 201
        assert 'contract' in result['body']
        assert result['body']['contract']['supplier_id'] == 'SUP-001'
        assert result['body']['contract']['contract_status'] == 'draft'
        assert result['body']['contract']['version'] == 1
        assert 'contract_id' in result['body']['contract']
    
    @patch('supplier_management.handler.audit_logger')
    def test_create_contract_missing_fields(self, mock_audit_logger, mock_tables, contract_manager):
        """Test contract creation with missing required fields."""
        contract_data = {
            'supplier_id': 'SUP-001',
            # Missing contract_type, start_date, end_date, terms
        }
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = contract_manager.create_contract(contract_data, user_id, request_context)
        
        assert result['statusCode'] == 400
        assert 'Missing required field' in result['body']['error']
    
    @patch('supplier_management.handler.audit_logger')
    def test_get_supplier_contracts_success(self, mock_audit_logger, mock_tables, contract_manager):
        """Test successful supplier contracts retrieval."""
        # Add sample contract
        contract_data = {
            'supplier_id': 'SUP-001',
            'contract_id': 'CONTRACT-001',
            'contract_type': 'service_agreement',
            'contract_status': 'active',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        mock_tables['contracts_table'].put_item(Item=contract_data)
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = contract_manager.get_supplier_contracts('SUP-001', user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 1
        assert result['body']['active_contracts'] == 1
        assert len(result['body']['contracts']) == 1
    
    @patch('supplier_management.handler.audit_logger')
    def test_update_contract_status_success(self, mock_audit_logger, mock_tables, contract_manager):
        """Test successful contract status update."""
        # Add sample contract
        contract_data = {
            'contract_id': 'CONTRACT-001',
            'supplier_id': 'SUP-001',
            'contract_status': 'draft',
            'contract_type': 'service_agreement'
        }
        mock_tables['contracts_table'].put_item(Item=contract_data)
        
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = contract_manager.update_contract_status('CONTRACT-001', 'active', user_id, request_context)
        
        assert result['statusCode'] == 200
        assert result['body']['contract']['contract_status'] == 'active'
    
    @patch('supplier_management.handler.audit_logger')
    def test_update_contract_status_not_found(self, mock_audit_logger, mock_tables, contract_manager):
        """Test contract status update with non-existent contract."""
        user_id = 'test-user'
        request_context = {'ip_address': '127.0.0.1'}
        
        result = contract_manager.update_contract_status('NONEXISTENT', 'active', user_id, request_context)
        
        assert result['statusCode'] == 404
        assert 'Contract not found' in result['body']['error']


class TestLambdaHandler:
    """Test Lambda handler routing."""
    
    @patch('supplier_management.handler.audit_logger')
    def test_lambda_handler_get_suppliers(self, mock_audit_logger, mock_tables, sample_suppliers):
        """Test Lambda handler for get suppliers endpoint."""
        # Add sample suppliers
        for supplier in sample_suppliers:
            mock_tables['suppliers_table'].put_item(Item=supplier)
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/suppliers',
            'queryStringParameters': None,
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        body = result['body']
        assert body['count'] == 2
        assert len(body['suppliers']) == 2
    
    @patch('supplier_management.handler.audit_logger')
    def test_lambda_handler_create_supplier(self, mock_audit_logger, mock_tables):
        """Test Lambda handler for create supplier endpoint."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/suppliers',
            'body': json.dumps({
                'name': 'New Test Supplier',
                'supplier_type': 'equipment',
                'contact_email': 'newtest@supplier.com'
            }),
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 201
        assert 'supplier' in result['body']
        assert result['body']['supplier']['name'] == 'New Test Supplier'
    
    @patch('supplier_management.handler.audit_logger')
    def test_lambda_handler_get_supplier_performance(self, mock_audit_logger, mock_tables, sample_suppliers, sample_purchase_orders):
        """Test Lambda handler for supplier performance endpoint."""
        # Add sample data
        supplier = sample_suppliers[0]
        mock_tables['suppliers_table'].put_item(Item=supplier)
        
        for order in sample_purchase_orders:
            mock_tables['purchase_orders_table'].put_item(Item=order)
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/suppliers/SUP-001/performance',
            'pathParameters': {'supplier_id': 'SUP-001'},
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        assert 'supplier' in result['body']
        assert 'performance_metrics' in result['body']
        assert 'risk_assessment' in result['body']
        assert 'recommendations' in result['body']
    
    @patch('supplier_management.handler.audit_logger')
    def test_lambda_handler_create_contract(self, mock_audit_logger, mock_tables):
        """Test Lambda handler for create contract endpoint."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/contracts',
            'body': json.dumps({
                'supplier_id': 'SUP-001',
                'contract_type': 'service_agreement',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'terms': 'Standard terms'
            }),
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 201
        assert 'contract' in result['body']
    
    def test_lambda_handler_health_check(self, mock_tables):
        """Test Lambda handler for health check endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/health',
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        assert result['body']['status'] == 'healthy'
        assert result['body']['service'] == 'supplier-management'
        assert result['body']['version'] == '2.0.0'
    
    def test_lambda_handler_invalid_endpoint(self, mock_tables):
        """Test Lambda handler for invalid endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/invalid',
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 404
        assert 'Endpoint not found' in result['body']['error']
    
    def test_lambda_handler_invalid_json(self, mock_tables):
        """Test Lambda handler with invalid JSON body."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/suppliers',
            'body': 'invalid json',
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'},
                'requestId': 'test-request-123'
            },
            'headers': {'User-Agent': 'test-agent'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 500
        assert 'Internal server error' in result['body']['error']


if __name__ == '__main__':
    pytest.main([__file__])