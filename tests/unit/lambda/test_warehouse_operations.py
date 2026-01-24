"""
Unit tests for warehouse operations
Tests receiving/dispatch workflows, location management CRUD operations,
and stock movement validation and logging.

Requirements: 1.2
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

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda', 'shared'))

from warehouse_management.handler import WarehouseService, lambda_handler


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
        
        # Create warehouse locations table
        warehouse_table = dynamodb.create_table(
            TableName='AquaChain-Warehouse-Locations',
            KeySchema=[
                {'AttributeName': 'location_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'location_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'warehouse_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'WarehouseIndex',
                    'KeySchema': [
                        {'AttributeName': 'warehouse_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
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
        
        # Create purchase orders table
        purchase_orders_table = dynamodb.create_table(
            TableName='AquaChain-Purchase-Orders',
            KeySchema=[
                {'AttributeName': 'po_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'po_id', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create stock movements table
        stock_movements_table = dynamodb.create_table(
            TableName='AquaChain-Stock-Movements',
            KeySchema=[
                {'AttributeName': 'movement_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'movement_id', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'},
                {'AttributeName': 'location_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'LocationIndex',
                    'KeySchema': [
                        {'AttributeName': 'location_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create performance metrics table
        performance_metrics_table = dynamodb.create_table(
            TableName='AquaChain-Performance-Metrics',
            KeySchema=[
                {'AttributeName': 'metric_type', 'KeyType': 'HASH'},
                {'AttributeName': 'metric_date', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'metric_type', 'AttributeType': 'S'},
                {'AttributeName': 'metric_date', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Create audit table
        audit_table = dynamodb.create_table(
            TableName='AquaChain-Audit-Logs',
            KeySchema=[
                {'AttributeName': 'audit_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'audit_id', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        yield {
            'warehouse_table': warehouse_table,
            'inventory_table': inventory_table,
            'purchase_orders_table': purchase_orders_table,
            'stock_movements_table': stock_movements_table,
            'performance_metrics_table': performance_metrics_table,
            'audit_table': audit_table
        }


@pytest.fixture
def warehouse_service():
    """Create warehouse service instance for testing."""
    request_context = {
        'user_id': 'test-user',
        'correlation_id': str(uuid.uuid4())
    }
    return WarehouseService(request_context)


@pytest.fixture
def sample_warehouse_locations():
    """Sample warehouse location data for testing."""
    return [
        {
            'location_id': 'LOC-WH1-A-001',
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '001',
            'capacity': 100,
            'current_usage': 50,
            'status': 'available'
        },
        {
            'location_id': 'LOC-WH1-A-002',
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '002',
            'capacity': 100,
            'current_usage': 90,
            'status': 'occupied'
        },
        {
            'location_id': 'LOC-WH1-B-001',
            'warehouse_id': 'WH1',
            'zone': 'B',
            'shelf': '001',
            'capacity': 150,
            'current_usage': 0,
            'status': 'available'
        }
    ]


class TestReceivingWorkflows:
    """Test receiving workflow management."""
    
    def test_process_receiving_workflow_success(self, mock_tables, warehouse_service):
        """Test successful receiving workflow processing."""
        # Setup test data
        po_data = {
            'po_id': 'PO-001',
            'status': 'APPROVED',
            'supplier_id': 'SUP-001'
        }
        mock_tables['purchase_orders_table'].put_item(Item=po_data)
        
        receiving_data = {
            'po_id': 'PO-001',
            'supplier_id': 'SUP-001',
            'received_by': 'test-user',
            'items': [
                {
                    'item_id': 'ITEM-001',
                    'quantity_received': 50
                }
            ]
        }
        
        # Execute
        result = warehouse_service.process_receiving_workflow(receiving_data)
        
        # Verify
        assert result['statusCode'] == 200
        assert 'workflow_id' in result['body']
        assert result['body']['items_processed'] == 1
        assert result['body']['status'] in ['COMPLETED', 'PARTIAL']
    
    def test_process_receiving_workflow_missing_fields(self, mock_tables, warehouse_service):
        """Test receiving workflow with missing required fields."""
        receiving_data = {
            'po_id': 'PO-001',
            # Missing supplier_id, items, received_by
        }
        
        result = warehouse_service.process_receiving_workflow(receiving_data)
        
        assert result['statusCode'] == 400
        assert 'Missing required field' in result['body']['error']
    
    def test_process_receiving_workflow_invalid_po(self, mock_tables, warehouse_service):
        """Test receiving workflow with invalid purchase order."""
        receiving_data = {
            'po_id': 'INVALID-PO',
            'supplier_id': 'SUP-001',
            'received_by': 'test-user',
            'items': [{'item_id': 'ITEM-001', 'quantity_received': 50}]
        }
        
        result = warehouse_service.process_receiving_workflow(receiving_data)
        
        assert result['statusCode'] == 400
        assert 'Purchase order not found' in result['body']['error']


class TestDispatchWorkflows:
    """Test dispatch workflow management."""
    
    def test_process_dispatch_workflow_success(self, mock_tables, warehouse_service):
        """Test successful dispatch workflow processing."""
        # Setup inventory data
        inventory_data = {
            'item_id': 'ITEM-001',
            'location_id': 'LOC-001',
            'current_stock': 100,
            'zone': 'A',
            'shelf': '001'
        }
        mock_tables['inventory_table'].put_item(Item=inventory_data)
        
        dispatch_data = {
            'order_id': 'ORD-001',
            'dispatch_by': 'test-user',
            'items': [
                {
                    'item_id': 'ITEM-001',
                    'quantity': 25,
                    'name': 'Test Item'
                }
            ]
        }
        
        # Execute
        result = warehouse_service.process_dispatch_workflow(dispatch_data)
        
        # Verify
        assert result['statusCode'] == 200
        assert 'workflow_id' in result['body']
        assert 'pick_list' in result['body']
        assert result['body']['status'] == 'PENDING_PICK'
    
    def test_process_dispatch_workflow_insufficient_inventory(self, mock_tables, warehouse_service):
        """Test dispatch workflow with insufficient inventory."""
        dispatch_data = {
            'order_id': 'ORD-001',
            'dispatch_by': 'test-user',
            'items': [
                {
                    'item_id': 'NONEXISTENT-ITEM',
                    'quantity': 25,
                    'name': 'Test Item'
                }
            ]
        }
        
        # Execute
        result = warehouse_service.process_dispatch_workflow(dispatch_data)
        
        # Verify - should still create workflow but with unavailable items
        assert result['statusCode'] == 400
        assert 'Insufficient inventory' in result['body']['error']


class TestLocationManagement:
    """Test warehouse location CRUD operations."""
    
    def test_create_warehouse_location_success(self, mock_tables, warehouse_service):
        """Test successful warehouse location creation."""
        location_data = {
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '001',
            'capacity': 100
        }
        
        result = warehouse_service.manage_warehouse_locations('create', location_data)
        
        assert result['statusCode'] == 201
        assert 'location' in result['body']
        assert result['body']['location']['location_id'] == 'LOC-WH1-A-001'
        assert result['body']['location']['status'] == 'available'
    
    def test_create_warehouse_location_missing_fields(self, mock_tables, warehouse_service):
        """Test warehouse location creation with missing fields."""
        location_data = {
            'warehouse_id': 'WH1',
            # Missing zone, shelf, capacity
        }
        
        result = warehouse_service.manage_warehouse_locations('create', location_data)
        
        assert result['statusCode'] == 400
        assert 'Missing required field' in result['body']['error']
    
    def test_update_warehouse_location_success(self, mock_tables, warehouse_service):
        """Test successful warehouse location update."""
        # Create location first
        location_data = {
            'location_id': 'LOC-WH1-A-001',
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '001',
            'capacity': 100,
            'current_usage': 0,
            'status': 'available'
        }
        mock_tables['warehouse_table'].put_item(Item=location_data)
        
        # Update location
        update_data = {
            'location_id': 'LOC-WH1-A-001',
            'capacity': 150,
            'status': 'occupied'
        }
        
        result = warehouse_service.manage_warehouse_locations('update', update_data)
        
        assert result['statusCode'] == 200
        assert result['body']['location']['capacity'] == 150
        assert result['body']['location']['status'] == 'occupied'
    
    def test_delete_warehouse_location_success(self, mock_tables, warehouse_service):
        """Test successful warehouse location deletion (soft delete)."""
        # Create location first
        location_data = {
            'location_id': 'LOC-WH1-A-001',
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '001',
            'capacity': 100,
            'current_usage': 0,
            'status': 'available'
        }
        mock_tables['warehouse_table'].put_item(Item=location_data)
        
        result = warehouse_service.manage_warehouse_locations('delete', {'location_id': 'LOC-WH1-A-001'})
        
        assert result['statusCode'] == 200
        assert 'deleted successfully' in result['body']['message']
    
    def test_delete_warehouse_location_with_inventory(self, mock_tables, warehouse_service):
        """Test warehouse location deletion with current inventory (should fail)."""
        # Create location with current usage
        location_data = {
            'location_id': 'LOC-WH1-A-001',
            'warehouse_id': 'WH1',
            'zone': 'A',
            'shelf': '001',
            'capacity': 100,
            'current_usage': 50,  # Has inventory
            'status': 'occupied'
        }
        mock_tables['warehouse_table'].put_item(Item=location_data)
        
        result = warehouse_service.manage_warehouse_locations('delete', {'location_id': 'LOC-WH1-A-001'})
        
        assert result['statusCode'] == 409
        assert 'Cannot delete location with current inventory' in result['body']['error']
    
    def test_list_warehouse_locations(self, mock_tables, warehouse_service, sample_warehouse_locations):
        """Test listing warehouse locations with filtering."""
        # Add sample locations
        for location in sample_warehouse_locations:
            mock_tables['warehouse_table'].put_item(Item=location)
        
        # Test list all locations
        result = warehouse_service.manage_warehouse_locations('list', {})
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 3
        assert len(result['body']['locations']) == 3
        
        # Test filter by status
        result = warehouse_service.manage_warehouse_locations('list', {'status': 'available'})
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 2  # Two available locations


class TestStockMovementTracking:
    """Test stock movement validation and logging."""
    
    def test_track_stock_movements_by_item(self, mock_tables, warehouse_service):
        """Test tracking stock movements by item ID."""
        # Create sample stock movements
        movements = [
            {
                'movement_id': 'MOV-001',
                'item_id': 'ITEM-001',
                'location_id': 'LOC-001',
                'movement_type': 'RECEIVING',
                'quantity': 50,
                'movement_date': datetime.utcnow().isoformat()
            },
            {
                'movement_id': 'MOV-002',
                'item_id': 'ITEM-001',
                'location_id': 'LOC-001',
                'movement_type': 'DISPATCH',
                'quantity': -25,
                'movement_date': datetime.utcnow().isoformat()
            }
        ]
        
        for movement in movements:
            mock_tables['stock_movements_table'].put_item(Item=movement)
        
        # Test tracking by item
        result = warehouse_service.track_stock_movements({'item_id': 'ITEM-001'})
        
        assert result['statusCode'] == 200
        assert result['body']['count'] == 2
        assert 'analytics' in result['body']
    
    def test_track_stock_movements_analytics(self, mock_tables, warehouse_service):
        """Test stock movement analytics calculation."""
        # Create diverse stock movements
        movements = [
            {
                'movement_id': 'MOV-001',
                'item_id': 'ITEM-001',
                'location_id': 'LOC-001',
                'movement_type': 'RECEIVING',
                'quantity': 100,
                'movement_date': '2024-01-01T10:00:00Z'
            },
            {
                'movement_id': 'MOV-002',
                'item_id': 'ITEM-002',
                'location_id': 'LOC-002',
                'movement_type': 'DISPATCH',
                'quantity': 50,
                'movement_date': '2024-01-01T11:00:00Z'
            },
            {
                'movement_id': 'MOV-003',
                'item_id': 'ITEM-001',
                'location_id': 'LOC-001',
                'movement_type': 'RECEIVING',
                'quantity': 75,
                'movement_date': '2024-01-02T09:00:00Z'
            }
        ]
        
        for movement in movements:
            mock_tables['stock_movements_table'].put_item(Item=movement)
        
        # Test analytics
        result = warehouse_service.track_stock_movements({})
        
        assert result['statusCode'] == 200
        analytics = result['body']['analytics']
        assert 'movement_types' in analytics
        assert 'daily_trends' in analytics
        assert analytics['total_movements'] == 3


class TestPerformanceMetrics:
    """Test performance metrics collection."""
    
    def test_get_performance_metrics_success(self, mock_tables, warehouse_service):
        """Test successful performance metrics retrieval."""
        # Create sample performance metrics
        metric_data = {
            'metric_type': 'warehouse',
            'metric_date': datetime.utcnow().isoformat(),
            'workflow_type': 'RECEIVING',
            'workflow_id': 'RCV-001',
            'completion_time': datetime.utcnow().isoformat(),
            'status': 'COMPLETED'
        }
        mock_tables['performance_metrics_table'].put_item(Item=metric_data)
        
        result = warehouse_service.get_performance_metrics('daily')
        
        assert result['statusCode'] == 200
        assert 'realtime_metrics' in result['body']
        assert 'historical_metrics' in result['body']
        assert 'summary' in result['body']
        assert 'trends' in result['body']
    
    def test_get_performance_metrics_different_time_ranges(self, mock_tables, warehouse_service):
        """Test performance metrics with different time ranges."""
        time_ranges = ['daily', 'weekly', 'monthly']
        
        for time_range in time_ranges:
            result = warehouse_service.get_performance_metrics(time_range)
            
            assert result['statusCode'] == 200
            assert result['body']['time_range'] == time_range


class TestWarehouseOverview:
    """Test warehouse overview functionality."""
    
    def test_get_warehouse_overview_success(self, mock_tables, warehouse_service, sample_warehouse_locations):
        """Test successful warehouse overview retrieval."""
        # Add sample locations
        for location in sample_warehouse_locations:
            mock_tables['warehouse_table'].put_item(Item=location)
        
        result = warehouse_service.get_warehouse_overview()
        
        assert result['statusCode'] == 200
        overview = result['body']['overview']
        assert overview['total_locations'] == 3
        assert overview['occupied_locations'] == 1
        assert overview['available_locations'] == 2
        assert overview['occupancy_rate'] == 33.33  # 1/3 * 100
        assert 'receiving_workflows' in overview
        assert 'dispatch_workflows' in overview
        assert 'performance_metrics' in overview


class TestLambdaHandler:
    """Test Lambda handler routing."""
    
    def test_lambda_handler_warehouse_overview(self, mock_tables):
        """Test Lambda handler for warehouse overview endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/warehouse/overview',
            'headers': {'X-Correlation-ID': str(uuid.uuid4())},
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'}
            }
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        assert 'Content-Type' in result['headers']
        assert 'Access-Control-Allow-Origin' in result['headers']
    
    def test_lambda_handler_invalid_endpoint(self, mock_tables):
        """Test Lambda handler for invalid endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/warehouse/invalid',
            'headers': {'X-Correlation-ID': str(uuid.uuid4())},
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'}
            }
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 404
        assert 'Endpoint not found' in json.loads(result['body'])['error']
    
    def test_lambda_handler_invalid_json(self, mock_tables):
        """Test Lambda handler with invalid JSON body."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/warehouse/receiving',
            'body': 'invalid json',
            'headers': {'X-Correlation-ID': str(uuid.uuid4())},
            'requestContext': {
                'authorizer': {'user_id': 'test-user'},
                'identity': {'sourceIp': '127.0.0.1'}
            }
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        assert 'Invalid JSON' in json.loads(result['body'])['error']


if __name__ == '__main__':
    pytest.main([__file__])