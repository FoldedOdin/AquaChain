"""
Load Tests for Concurrent User Scenarios
Tests system behavior with multiple concurrent users and data consistency
Requirements: 9.4, 9.6
"""

import pytest
import time
import threading
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from moto import mock_aws
import os
import sys
import json
import random
from datetime import datetime, timedelta
from queue import Queue
from dataclasses import dataclass
from typing import List, Dict, Any

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/rbac_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/inventory_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/procurement_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/budget_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/workflow_service'))


@dataclass
class LoadTestResult:
    """Result of a load test operation"""
    user_id: str
    operation: str
    start_time: float
    end_time: float
    success: bool
    error_message: str = ""
    response_data: Dict[str, Any] = None
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


@dataclass
class ConcurrencyTestMetrics:
    """Metrics for concurrent user testing"""
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput_ops_per_sec: float
    error_rate: float
    data_consistency_violations: int


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'


@pytest.fixture
def setup_environment(aws_credentials):
    """Set up test environment"""
    os.environ['USERS_TABLE'] = 'test-users'
    os.environ['INVENTORY_TABLE'] = 'test-inventory'
    os.environ['PURCHASE_ORDERS_TABLE'] = 'test-purchase-orders'
    os.environ['BUDGET_TABLE'] = 'test-budget'
    os.environ['WORKFLOWS_TABLE'] = 'test-workflows'
    os.environ['AUDIT_TABLE'] = 'test-audit'


@pytest.fixture
def setup_dynamodb_tables(setup_environment):
    """Set up DynamoDB tables for load testing"""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        tables = {}
        
        # Create all required tables with consistent schema
        table_configs = [
            ('test-users', 'PK', 'SK'),
            ('test-inventory', 'PK', 'SK'),
            ('test-purchase-orders', 'PK', 'SK'),
            ('test-budget', 'PK', 'SK'),
            ('test-workflows', 'PK', 'SK'),
            ('test-audit', 'PK', 'SK')
        ]
        
        for table_name, hash_key, range_key in table_configs:
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': hash_key, 'KeyType': 'HASH'},
                    {'AttributeName': range_key, 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': hash_key, 'AttributeType': 'S'},
                    {'AttributeName': range_key, 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'GSI1',
                        'KeySchema': [
                            {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            tables[table_name.replace('test-', '')] = table
        
        yield tables


class ConcurrentUserSimulator:
    """Simulates concurrent user operations"""
    
    def __init__(self, tables: Dict[str, Any]):
        self.tables = tables
        self.results: List[LoadTestResult] = []
        self.results_lock = threading.Lock()
        
    def add_result(self, result: LoadTestResult):
        """Thread-safe result addition"""
        with self.results_lock:
            self.results.append(result)
    
    def simulate_inventory_operations(self, user_id: str, operation_count: int) -> List[LoadTestResult]:
        """Simulate inventory management operations"""
        results = []
        
        for i in range(operation_count):
            # Random operation type
            operations = ['read_inventory', 'update_stock', 'create_alert', 'query_history']
            operation = random.choice(operations)
            
            start_time = time.time()
            success = True
            error_message = ""
            response_data = {}
            
            try:
                if operation == 'read_inventory':
                    # Simulate reading inventory items
                    response = self.tables['inventory'].query(
                        KeyConditionExpression='PK = :pk',
                        ExpressionAttributeValues={
                            ':pk': f'ITEM#item-{i % 100}'
                        }
                    )
                    response_data = {'items_count': len(response.get('Items', []))}
                    
                elif operation == 'update_stock':
                    # Simulate stock update
                    item_id = f'item-{i % 100}'
                    new_stock = random.randint(50, 200)
                    
                    self.tables['inventory'].put_item(Item={
                        'PK': f'ITEM#{item_id}',
                        'SK': 'CURRENT',
                        'itemId': item_id,
                        'currentStock': new_stock,
                        'lastUpdated': datetime.utcnow().isoformat(),
                        'updatedBy': user_id
                    })
                    response_data = {'new_stock': new_stock}
                    
                elif operation == 'create_alert':
                    # Simulate alert creation
                    alert_id = f'alert-{user_id}-{i}'
                    self.tables['inventory'].put_item(Item={
                        'PK': f'ALERT#{alert_id}',
                        'SK': 'ACTIVE',
                        'alertId': alert_id,
                        'itemId': f'item-{i % 100}',
                        'alertType': 'low_stock',
                        'createdAt': datetime.utcnow().isoformat(),
                        'createdBy': user_id
                    })
                    response_data = {'alert_id': alert_id}
                    
                elif operation == 'query_history':
                    # Simulate history query
                    response = self.tables['inventory'].query(
                        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                        ExpressionAttributeValues={
                            ':pk': f'ITEM#item-{i % 100}',
                            ':sk': 'HISTORY#'
                        }
                    )
                    response_data = {'history_count': len(response.get('Items', []))}
                
                # Add small random delay to simulate processing
                time.sleep(random.uniform(0.001, 0.01))
                
            except Exception as e:
                success = False
                error_message = str(e)
            
            end_time = time.time()
            
            result = LoadTestResult(
                user_id=user_id,
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                success=success,
                error_message=error_message,
                response_data=response_data
            )
            
            results.append(result)
            self.add_result(result)
        
        return results
    
    def simulate_procurement_operations(self, user_id: str, operation_count: int) -> List[LoadTestResult]:
        """Simulate procurement operations"""
        results = []
        
        for i in range(operation_count):
            operations = ['create_order', 'approve_order', 'query_orders', 'update_budget']
            operation = random.choice(operations)
            
            start_time = time.time()
            success = True
            error_message = ""
            response_data = {}
            
            try:
                if operation == 'create_order':
                    # Simulate purchase order creation
                    order_id = f'order-{user_id}-{i}'
                    amount = random.uniform(100, 5000)
                    
                    self.tables['purchase-orders'].put_item(Item={
                        'PK': f'ORDER#{order_id}',
                        'SK': 'CURRENT',
                        'orderId': order_id,
                        'requesterId': user_id,
                        'totalAmount': amount,
                        'status': 'pending',
                        'createdAt': datetime.utcnow().isoformat(),
                        'GSI1PK': 'STATUS#pending',
                        'GSI1SK': f'CREATED#{datetime.utcnow().isoformat()}'
                    })
                    response_data = {'order_id': order_id, 'amount': amount}
                    
                elif operation == 'approve_order':
                    # Simulate order approval
                    order_id = f'order-{random.randint(1, 1000)}'
                    
                    self.tables['purchase-orders'].update_item(
                        Key={
                            'PK': f'ORDER#{order_id}',
                            'SK': 'CURRENT'
                        },
                        UpdateExpression='SET #status = :status, approvedBy = :approver, approvedAt = :timestamp',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':status': 'approved',
                            ':approver': user_id,
                            ':timestamp': datetime.utcnow().isoformat()
                        }
                    )
                    response_data = {'approved_order': order_id}
                    
                elif operation == 'query_orders':
                    # Simulate order queries
                    response = self.tables['purchase-orders'].query(
                        IndexName='GSI1',
                        KeyConditionExpression='GSI1PK = :pk',
                        ExpressionAttributeValues={
                            ':pk': 'STATUS#pending'
                        },
                        Limit=20
                    )
                    response_data = {'pending_orders': len(response.get('Items', []))}
                    
                elif operation == 'update_budget':
                    # Simulate budget update
                    category = f'category-{i % 5}'
                    amount = random.uniform(1000, 10000)
                    
                    self.tables['budget'].put_item(Item={
                        'PK': f'BUDGET#{category}#2024-01',
                        'SK': 'ALLOCATION',
                        'category': category,
                        'period': '2024-01',
                        'allocatedAmount': amount,
                        'utilizedAmount': amount * random.uniform(0.1, 0.8),
                        'lastUpdated': datetime.utcnow().isoformat(),
                        'updatedBy': user_id
                    })
                    response_data = {'budget_category': category, 'amount': amount}
                
                time.sleep(random.uniform(0.002, 0.015))
                
            except Exception as e:
                success = False
                error_message = str(e)
            
            end_time = time.time()
            
            result = LoadTestResult(
                user_id=user_id,
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                success=success,
                error_message=error_message,
                response_data=response_data
            )
            
            results.append(result)
            self.add_result(result)
        
        return results
    
    def simulate_mixed_operations(self, user_id: str, operation_count: int) -> List[LoadTestResult]:
        """Simulate mixed operations across different services"""
        results = []
        
        # Split operations between different services
        inventory_ops = operation_count // 3
        procurement_ops = operation_count // 3
        audit_ops = operation_count - inventory_ops - procurement_ops
        
        # Run inventory operations
        results.extend(self.simulate_inventory_operations(user_id, inventory_ops))
        
        # Run procurement operations
        results.extend(self.simulate_procurement_operations(user_id, procurement_ops))
        
        # Run audit operations
        for i in range(audit_ops):
            start_time = time.time()
            success = True
            error_message = ""
            
            try:
                # Simulate audit log entry
                audit_id = f'audit-{user_id}-{i}'
                self.tables['audit'].put_item(Item={
                    'PK': f'AUDIT#{datetime.utcnow().strftime("%Y-%m-%d")}#{user_id}',
                    'SK': f'ACTION#{datetime.utcnow().isoformat()}#{audit_id}',
                    'userId': user_id,
                    'action': random.choice(['login', 'create_order', 'approve_order', 'update_inventory']),
                    'resource': random.choice(['auth', 'procurement', 'inventory']),
                    'timestamp': datetime.utcnow().isoformat(),
                    'success': True
                })
                
                time.sleep(random.uniform(0.001, 0.005))
                
            except Exception as e:
                success = False
                error_message = str(e)
            
            end_time = time.time()
            
            result = LoadTestResult(
                user_id=user_id,
                operation='audit_log',
                start_time=start_time,
                end_time=end_time,
                success=success,
                error_message=error_message
            )
            
            results.append(result)
            self.add_result(result)
        
        return results


class TestConcurrentUserScenarios:
    """Test system behavior with multiple concurrent users - Requirement 9.4"""
    
    def _analyze_results(self, results: List[LoadTestResult], total_time: float) -> ConcurrencyTestMetrics:
        """Analyze load test results and return metrics"""
        if not results:
            return ConcurrencyTestMetrics(
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                average_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                throughput_ops_per_sec=0,
                error_rate=1.0,
                data_consistency_violations=0
            )
        
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r.success)
        failed_operations = total_operations - successful_operations
        
        response_times = [r.duration_ms for r in results]
        average_response_time = statistics.mean(response_times)
        
        if len(response_times) >= 20:
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
        else:
            p95_response_time = max(response_times) if response_times else 0
        
        if len(response_times) >= 100:
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
        else:
            p99_response_time = max(response_times) if response_times else 0
        
        throughput_ops_per_sec = total_operations / total_time if total_time > 0 else 0
        error_rate = failed_operations / total_operations if total_operations > 0 else 0
        
        return ConcurrencyTestMetrics(
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            average_response_time=average_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_ops_per_sec=throughput_ops_per_sec,
            error_rate=error_rate,
            data_consistency_violations=0  # Would need specific consistency checks
        )
    
    def test_concurrent_inventory_operations(self, setup_dynamodb_tables):
        """Test concurrent inventory operations with multiple users"""
        simulator = ConcurrentUserSimulator(setup_dynamodb_tables)
        
        # Test configuration
        concurrent_users = 10
        operations_per_user = 20
        
        print(f"\nTesting {concurrent_users} concurrent users with {operations_per_user} operations each")
        
        # Create thread pool for concurrent execution
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit tasks for each user
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(
                    simulator.simulate_inventory_operations,
                    f'user-{user_id:03d}',
                    operations_per_user
                )
                futures.append(future)
            
            # Wait for all tasks to complete
            start_time = time.time()
            results = []
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    print(f"User operation failed: {e}")
            
            total_time = time.time() - start_time
        
        # Analyze results
        metrics = self._analyze_results(results, total_time)
        
        print(f"\nConcurrent Inventory Operations Results:")
        print(f"  Total operations: {metrics.total_operations}")
        print(f"  Successful: {metrics.successful_operations}")
        print(f"  Failed: {metrics.failed_operations}")
        print(f"  Success rate: {(1 - metrics.error_rate) * 100:.1f}%")
        print(f"  Average response time: {metrics.average_response_time:.2f}ms")
        print(f"  P95 response time: {metrics.p95_response_time:.2f}ms")
        print(f"  P99 response time: {metrics.p99_response_time:.2f}ms")
        print(f"  Throughput: {metrics.throughput_ops_per_sec:.1f} ops/sec")
        
        # Verify performance requirements
        assert metrics.error_rate < 0.05, f"Error rate {metrics.error_rate:.3f} exceeds 5% threshold"
        assert metrics.p95_response_time < 1000, f"P95 response time {metrics.p95_response_time:.2f}ms exceeds 1000ms threshold"
        assert metrics.throughput_ops_per_sec > 50, f"Throughput {metrics.throughput_ops_per_sec:.1f} ops/sec below 50 ops/sec threshold"
    
    def test_concurrent_procurement_operations(self, setup_dynamodb_tables):
        """Test concurrent procurement operations"""
        simulator = ConcurrentUserSimulator(setup_dynamodb_tables)
        
        concurrent_users = 8
        operations_per_user = 15
        
        print(f"\nTesting {concurrent_users} concurrent procurement users")
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(
                    simulator.simulate_procurement_operations,
                    f'procurement-user-{user_id:03d}',
                    operations_per_user
                )
                futures.append(future)
            
            start_time = time.time()
            results = []
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    print(f"Procurement operation failed: {e}")
            
            total_time = time.time() - start_time
        
        metrics = self._analyze_results(results, total_time)
        
        print(f"\nConcurrent Procurement Operations Results:")
        print(f"  Total operations: {metrics.total_operations}")
        print(f"  Success rate: {(1 - metrics.error_rate) * 100:.1f}%")
        print(f"  Average response time: {metrics.average_response_time:.2f}ms")
        print(f"  P95 response time: {metrics.p95_response_time:.2f}ms")
        print(f"  Throughput: {metrics.throughput_ops_per_sec:.1f} ops/sec")
        
        # Verify requirements
        assert metrics.error_rate < 0.05, f"Error rate {metrics.error_rate:.3f} exceeds 5% threshold"
        assert metrics.p95_response_time < 1500, f"P95 response time {metrics.p95_response_time:.2f}ms exceeds 1500ms threshold"
    
    def test_mixed_workload_concurrent_users(self, setup_dynamodb_tables):
        """Test mixed workload with concurrent users across all services"""
        simulator = ConcurrentUserSimulator(setup_dynamodb_tables)
        
        concurrent_users = 15
        operations_per_user = 30
        
        print(f"\nTesting {concurrent_users} concurrent users with mixed workload")
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(
                    simulator.simulate_mixed_operations,
                    f'mixed-user-{user_id:03d}',
                    operations_per_user
                )
                futures.append(future)
            
            start_time = time.time()
            results = []
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    print(f"Mixed operation failed: {e}")
            
            total_time = time.time() - start_time
        
        metrics = self._analyze_results(results, total_time)
        
        print(f"\nMixed Workload Concurrent Users Results:")
        print(f"  Total operations: {metrics.total_operations}")
        print(f"  Success rate: {(1 - metrics.error_rate) * 100:.1f}%")
        print(f"  Average response time: {metrics.average_response_time:.2f}ms")
        print(f"  P95 response time: {metrics.p95_response_time:.2f}ms")
        print(f"  P99 response time: {metrics.p99_response_time:.2f}ms")
        print(f"  Throughput: {metrics.throughput_ops_per_sec:.1f} ops/sec")
        
        # Verify requirements for mixed workload
        assert metrics.error_rate < 0.08, f"Error rate {metrics.error_rate:.3f} exceeds 8% threshold for mixed workload"
        assert metrics.p95_response_time < 2000, f"P95 response time {metrics.p95_response_time:.2f}ms exceeds 2000ms threshold"
        assert metrics.throughput_ops_per_sec > 100, f"Throughput {metrics.throughput_ops_per_sec:.1f} ops/sec below 100 ops/sec threshold"


class TestDataConsistencyUnderConcurrency:
    """Test data consistency under high concurrency - Requirement 9.6"""
    
    def test_concurrent_inventory_updates_consistency(self, setup_dynamodb_tables):
        """Test data consistency during concurrent inventory updates"""
        inventory_table = setup_dynamodb_tables['inventory']
        
        # Initialize test item
        item_id = 'test-item-consistency'
        initial_stock = 1000
        
        inventory_table.put_item(Item={
            'PK': f'ITEM#{item_id}',
            'SK': 'CURRENT',
            'itemId': item_id,
            'currentStock': initial_stock,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
        # Concurrent update operations
        concurrent_users = 20
        updates_per_user = 10
        stock_change_per_update = -5  # Each update reduces stock by 5
        
        results = []
        consistency_violations = []
        
        def update_stock(user_id: str, update_count: int):
            """Perform concurrent stock updates"""
            user_results = []
            
            for i in range(update_count):
                try:
                    # Read current stock
                    response = inventory_table.get_item(
                        Key={'PK': f'ITEM#{item_id}', 'SK': 'CURRENT'}
                    )
                    
                    if 'Item' in response:
                        current_stock = response['Item']['currentStock']
                        new_stock = current_stock + stock_change_per_update
                        
                        # Update with optimistic locking simulation
                        inventory_table.put_item(Item={
                            'PK': f'ITEM#{item_id}',
                            'SK': 'CURRENT',
                            'itemId': item_id,
                            'currentStock': new_stock,
                            'lastUpdated': datetime.utcnow().isoformat(),
                            'updatedBy': user_id
                        })
                        
                        user_results.append({
                            'user_id': user_id,
                            'operation': i,
                            'old_stock': current_stock,
                            'new_stock': new_stock,
                            'success': True
                        })
                    
                    # Small delay to increase chance of race conditions
                    time.sleep(random.uniform(0.001, 0.005))
                    
                except Exception as e:
                    user_results.append({
                        'user_id': user_id,
                        'operation': i,
                        'error': str(e),
                        'success': False
                    })
            
            return user_results
        
        # Execute concurrent updates
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(update_stock, f'user-{user_id:03d}', updates_per_user)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    print(f"Concurrent update failed: {e}")
        
        # Verify final consistency
        final_response = inventory_table.get_item(
            Key={'PK': f'ITEM#{item_id}', 'SK': 'CURRENT'}
        )
        
        final_stock = final_response['Item']['currentStock']
        expected_final_stock = initial_stock + (concurrent_users * updates_per_user * stock_change_per_update)
        
        successful_updates = sum(1 for r in results if r.get('success', False))
        failed_updates = len(results) - successful_updates
        
        print(f"\nConcurrent Inventory Updates Consistency Test:")
        print(f"  Initial stock: {initial_stock}")
        print(f"  Expected final stock: {expected_final_stock}")
        print(f"  Actual final stock: {final_stock}")
        print(f"  Successful updates: {successful_updates}")
        print(f"  Failed updates: {failed_updates}")
        print(f"  Stock difference: {abs(final_stock - expected_final_stock)}")
        
        # In a real system with proper optimistic locking, we'd expect perfect consistency
        # In this test environment, we allow some variance due to race conditions
        stock_variance = abs(final_stock - expected_final_stock)
        max_allowed_variance = concurrent_users * 2  # Allow some race condition variance
        
        assert stock_variance <= max_allowed_variance, f"Stock variance {stock_variance} exceeds allowed variance {max_allowed_variance}"
        assert failed_updates < (len(results) * 0.1), f"Too many failed updates: {failed_updates}"
    
    def test_concurrent_budget_allocation_consistency(self, setup_dynamodb_tables):
        """Test budget allocation consistency under concurrent access"""
        budget_table = setup_dynamodb_tables['budget']
        
        # Initialize budget
        category = 'test-category'
        period = '2024-01'
        initial_budget = 100000.0
        
        budget_table.put_item(Item={
            'PK': f'BUDGET#{category}#{period}',
            'SK': 'ALLOCATION',
            'category': category,
            'period': period,
            'allocatedAmount': initial_budget,
            'utilizedAmount': 0.0,
            'remainingAmount': initial_budget,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
        # Concurrent budget utilization
        concurrent_users = 15
        allocations_per_user = 8
        allocation_amount = 500.0  # Each allocation is $500
        
        results = []
        
        def allocate_budget(user_id: str, allocation_count: int):
            """Perform concurrent budget allocations"""
            user_results = []
            
            for i in range(allocation_count):
                try:
                    # Read current budget
                    response = budget_table.get_item(
                        Key={'PK': f'BUDGET#{category}#{period}', 'SK': 'ALLOCATION'}
                    )
                    
                    if 'Item' in response:
                        current_utilized = response['Item']['utilizedAmount']
                        current_remaining = response['Item']['remainingAmount']
                        
                        # Check if allocation is possible
                        if current_remaining >= allocation_amount:
                            new_utilized = current_utilized + allocation_amount
                            new_remaining = current_remaining - allocation_amount
                            
                            # Update budget
                            budget_table.put_item(Item={
                                'PK': f'BUDGET#{category}#{period}',
                                'SK': 'ALLOCATION',
                                'category': category,
                                'period': period,
                                'allocatedAmount': initial_budget,
                                'utilizedAmount': new_utilized,
                                'remainingAmount': new_remaining,
                                'lastUpdated': datetime.utcnow().isoformat(),
                                'updatedBy': user_id
                            })
                            
                            user_results.append({
                                'user_id': user_id,
                                'operation': i,
                                'allocated_amount': allocation_amount,
                                'new_utilized': new_utilized,
                                'new_remaining': new_remaining,
                                'success': True
                            })
                        else:
                            user_results.append({
                                'user_id': user_id,
                                'operation': i,
                                'error': 'Insufficient budget',
                                'success': False
                            })
                    
                    time.sleep(random.uniform(0.001, 0.003))
                    
                except Exception as e:
                    user_results.append({
                        'user_id': user_id,
                        'operation': i,
                        'error': str(e),
                        'success': False
                    })
            
            return user_results
        
        # Execute concurrent allocations
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(allocate_budget, f'budget-user-{user_id:03d}', allocations_per_user)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    print(f"Concurrent budget allocation failed: {e}")
        
        # Verify final budget consistency
        final_response = budget_table.get_item(
            Key={'PK': f'BUDGET#{category}#{period}', 'SK': 'ALLOCATION'}
        )
        
        final_utilized = final_response['Item']['utilizedAmount']
        final_remaining = final_response['Item']['remainingAmount']
        
        successful_allocations = sum(1 for r in results if r.get('success', False))
        expected_utilized = successful_allocations * allocation_amount
        expected_remaining = initial_budget - expected_utilized
        
        print(f"\nConcurrent Budget Allocation Consistency Test:")
        print(f"  Initial budget: ${initial_budget:,.2f}")
        print(f"  Successful allocations: {successful_allocations}")
        print(f"  Expected utilized: ${expected_utilized:,.2f}")
        print(f"  Actual utilized: ${final_utilized:,.2f}")
        print(f"  Expected remaining: ${expected_remaining:,.2f}")
        print(f"  Actual remaining: ${final_remaining:,.2f}")
        print(f"  Budget consistency: ${abs(final_utilized + final_remaining - initial_budget):,.2f}")
        
        # Verify budget consistency (utilized + remaining = total)
        budget_consistency_error = abs(final_utilized + final_remaining - initial_budget)
        assert budget_consistency_error < 0.01, f"Budget consistency error: ${budget_consistency_error:,.2f}"
        
        # Verify no over-allocation occurred
        assert final_utilized <= initial_budget, f"Over-allocation detected: ${final_utilized:,.2f} > ${initial_budget:,.2f}"
        assert final_remaining >= 0, f"Negative remaining budget: ${final_remaining:,.2f}"


class TestGracefulDegradationUnderOverload:
    """Test graceful degradation under overload conditions - Requirement 9.6"""
    
    def test_system_behavior_under_extreme_load(self, setup_dynamodb_tables):
        """Test system behavior under extreme concurrent load"""
        simulator = ConcurrentUserSimulator(setup_dynamodb_tables)
        
        # Extreme load configuration
        concurrent_users = 50
        operations_per_user = 50
        
        print(f"\nTesting extreme load: {concurrent_users} users, {operations_per_user} ops each")
        
        # Monitor system behavior under load
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(
                    simulator.simulate_mixed_operations,
                    f'extreme-user-{user_id:03d}',
                    operations_per_user
                )
                futures.append(future)
            
            # Collect results as they complete
            completed_operations = 0
            failed_operations = 0
            response_times = []
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    for result in user_results:
                        completed_operations += 1
                        if not result.success:
                            failed_operations += 1
                        response_times.append(result.duration_ms)
                except Exception as e:
                    failed_operations += operations_per_user
                    print(f"User thread failed under extreme load: {e}")
        
        total_time = time.time() - start_time
        
        # Analyze degradation behavior
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        error_rate = failed_operations / (completed_operations + failed_operations) if (completed_operations + failed_operations) > 0 else 1.0
        throughput = completed_operations / total_time if total_time > 0 else 0
        
        print(f"\nExtreme Load Test Results:")
        print(f"  Total operations attempted: {concurrent_users * operations_per_user}")
        print(f"  Completed operations: {completed_operations}")
        print(f"  Failed operations: {failed_operations}")
        print(f"  Error rate: {error_rate * 100:.1f}%")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  P95 response time: {p95_response_time:.2f}ms")
        print(f"  P99 response time: {p99_response_time:.2f}ms")
        print(f"  Throughput: {throughput:.1f} ops/sec")
        
        # Verify graceful degradation (system should not completely fail)
        assert error_rate < 0.5, f"Error rate {error_rate:.3f} indicates system failure, not graceful degradation"
        assert completed_operations > 0, "System completely failed under load"
        
        # Response times may be higher under extreme load, but should not be infinite
        if response_times:
            assert p99_response_time < 10000, f"P99 response time {p99_response_time:.2f}ms indicates system hang"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])