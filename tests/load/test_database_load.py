"""
Database Load Testing for AquaChain
Tests DynamoDB performance under concurrent read/write operations
"""

import boto3
import json
import time
import uuid
import statistics
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
import argparse
import random
import threading
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class DatabaseLoadTestResult:
    """Results from a database load test execution."""
    operation_type: str
    table_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    operations_per_second: float
    error_rate: float
    consumed_read_capacity: float
    consumed_write_capacity: float
    duration: float

class DatabaseLoadTester:
    """Load tester for DynamoDB operations."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        
        # Table references
        self.readings_table = self.dynamodb.Table('aquachain-readings')
        self.ledger_table = self.dynamodb.Table('aquachain-ledger')
        self.users_table = self.dynamodb.Table('aquachain-users')
        self.service_requests_table = self.dynamodb.Table('aquachain-service-requests')
        
        # Metrics collection
        self.lock = threading.Lock()
        self.consumed_capacity = {'read': 0, 'write': 0}
    
    def generate_reading_data(self, device_id: str) -> Dict:
        """Generate realistic reading data for testing."""
        timestamp = datetime.now(timezone.utc).isoformat()
        device_month = f"{device_id}#{datetime.now().strftime('%Y%m')}"
        
        return {
            'deviceId_month': device_month,
            'timestamp': timestamp,
            'deviceId': device_id,
            'readings': {
                'pH': Decimal(str(round(random.uniform(6.0, 8.5), 2))),
                'turbidity': Decimal(str(round(random.uniform(0.5, 5.0), 2))),
                'tds': Decimal(str(random.randint(100, 500))),
                'temperature': Decimal(str(round(random.uniform(20.0, 30.0), 1))),
                'humidity': Decimal(str(round(random.uniform(50.0, 80.0), 1)))
            },
            'wqi': Decimal(str(random.randint(70, 95))),
            'anomalyType': random.choice(['normal', 'sensor_fault', 'contamination']),
            'ledgerHash': f"hash_{uuid.uuid4().hex}",
            'location': {
                'latitude': Decimal(str(round(random.uniform(8.0, 12.0), 4))),
                'longitude': Decimal(str(round(random.uniform(75.0, 78.0), 4)))
            },
            'diagnostics': {
                'batteryLevel': random.randint(20, 100),
                'signalStrength': random.randint(-90, -30),
                'sensorStatus': 'normal'
            }
        }
    
    def generate_ledger_entry(self, sequence_number: int) -> Dict:
        """Generate ledger entry for testing."""
        return {
            'partition_key': 'GLOBAL_SEQUENCE',
            'sequenceNumber': sequence_number,
            'logId': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'deviceId': f"LOAD-TEST-{random.randint(1000, 9999)}",
            'dataHash': f"data_hash_{uuid.uuid4().hex}",
            'previousHash': f"prev_hash_{uuid.uuid4().hex}",
            'chainHash': f"chain_hash_{uuid.uuid4().hex}",
            'wqi': Decimal(str(random.randint(50, 100))),
            'anomalyType': random.choice(['normal', 'sensor_fault', 'contamination'])
        }
    
    def run_write_load_test(self, table_name: str, concurrent_writers: int = 50, 
                           duration: int = 300, items_per_writer: int = 100) -> DatabaseLoadTestResult:
        """Run write load test against specified table."""
        print(f"✍️  Testing write operations on {table_name}")
        print(f"   Concurrent writers: {concurrent_writers}")
        print(f"   Duration: {duration} seconds")
        print(f"   Items per writer: {items_per_writer}")
        
        table = self.dynamodb.Table(table_name)
        results = []
        consumed_capacity = {'read': 0, 'write': 0}
        
        def writer_worker():
            local_results = []
            end_time = time.time() + duration
            items_written = 0
            
            while time.time() < end_time and items_written < items_per_writer:
                start_time = time.time()
                
                try:
                    if table_name == 'aquachain-readings':
                        device_id = f"LOAD-TEST-{random.randint(1000, 9999)}"
                        item = self.generate_reading_data(device_id)
                    elif table_name == 'aquachain-ledger':
                        sequence_number = int(time.time() * 1000000) + random.randint(1, 1000)
                        item = self.generate_ledger_entry(sequence_number)
                    else:
                        # Generic item for other tables
                        item = {
                            'id': str(uuid.uuid4()),
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'data': f"test_data_{random.randint(1000, 9999)}"
                        }
                    
                    response = table.put_item(
                        Item=item,
                        ReturnConsumedCapacity='TOTAL'
                    )
                    
                    end_time_op = time.time()
                    response_time = (end_time_op - start_time) * 1000
                    
                    # Track consumed capacity
                    if 'ConsumedCapacity' in response:
                        with self.lock:
                            consumed_capacity['write'] += response['ConsumedCapacity'].get('CapacityUnits', 0)
                    
                    local_results.append((True, response_time))
                    items_written += 1
                    
                except Exception as e:
                    end_time_op = time.time()
                    response_time = (end_time_op - start_time) * 1000
                    local_results.append((False, response_time))
                
                # Small delay to avoid overwhelming the table
                time.sleep(random.uniform(0.01, 0.1))
            
            with self.lock:
                results.extend(local_results)
        
        start_time = time.time()
        
        # Start concurrent writers
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_writers) as executor:
            futures = [executor.submit(writer_worker) for _ in range(concurrent_writers)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        return self._calculate_metrics(
            results, 'WRITE', table_name, actual_duration, 
            consumed_capacity['read'], consumed_capacity['write']
        )
    
    def run_read_load_test(self, table_name: str, concurrent_readers: int = 50, 
                          duration: int = 300) -> DatabaseLoadTestResult:
        """Run read load test against specified table."""
        print(f"📖 Testing read operations on {table_name}")
        print(f"   Concurrent readers: {concurrent_readers}")
        print(f"   Duration: {duration} seconds")
        
        table = self.dynamodb.Table(table_name)
        results = []
        consumed_capacity = {'read': 0, 'write': 0}
        
        # Pre-populate some test data for reading
        self._populate_test_data(table_name, 100)
        
        def reader_worker():
            local_results = []
            end_time = time.time() + duration
            
            while time.time() < end_time:
                start_time = time.time()
                
                try:
                    if table_name == 'aquachain-readings':
                        # Query readings for a device
                        device_id = f"LOAD-TEST-{random.randint(1000, 1099)}"  # Use pre-populated range
                        device_month = f"{device_id}#{datetime.now().strftime('%Y%m')}"
                        
                        response = table.query(
                            KeyConditionExpression='deviceId_month = :pk',
                            ExpressionAttributeValues={':pk': device_month},
                            Limit=10,
                            ReturnConsumedCapacity='TOTAL'
                        )
                        
                    elif table_name == 'aquachain-ledger':
                        # Query recent ledger entries
                        response = table.query(
                            KeyConditionExpression='partition_key = :pk',
                            ExpressionAttributeValues={':pk': 'GLOBAL_SEQUENCE'},
                            ScanIndexForward=False,
                            Limit=10,
                            ReturnConsumedCapacity='TOTAL'
                        )
                        
                    else:
                        # Scan operation for other tables
                        response = table.scan(
                            Limit=10,
                            ReturnConsumedCapacity='TOTAL'
                        )
                    
                    end_time_op = time.time()
                    response_time = (end_time_op - start_time) * 1000
                    
                    # Track consumed capacity
                    if 'ConsumedCapacity' in response:
                        with self.lock:
                            consumed_capacity['read'] += response['ConsumedCapacity'].get('CapacityUnits', 0)
                    
                    local_results.append((True, response_time))
                    
                except Exception as e:
                    end_time_op = time.time()
                    response_time = (end_time_op - start_time) * 1000
                    local_results.append((False, response_time))
                
                # Small delay between reads
                time.sleep(random.uniform(0.1, 0.5))
            
            with self.lock:
                results.extend(local_results)
        
        start_time = time.time()
        
        # Start concurrent readers
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_readers) as executor:
            futures = [executor.submit(reader_worker) for _ in range(concurrent_readers)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        return self._calculate_metrics(
            results, 'READ', table_name, actual_duration, 
            consumed_capacity['read'], consumed_capacity['write']
        )
    
    def run_mixed_workload_test(self, table_name: str, concurrent_workers: int = 50, 
                               duration: int = 300, read_write_ratio: float = 0.7) -> DatabaseLoadTestResult:
        """Run mixed read/write workload test."""
        print(f"🔄 Testing mixed workload on {table_name}")
        print(f"   Concurrent workers: {concurrent_workers}")
        print(f"   Duration: {duration} seconds")
        print(f"   Read/Write ratio: {read_write_ratio:.1f}")
        
        table = self.dynamodb.Table(table_name)
        results = []
        consumed_capacity = {'read': 0, 'write': 0}
        
        # Pre-populate some test data
        self._populate_test_data(table_name, 50)
        
        def mixed_worker():
            local_results = []
            end_time = time.time() + duration
            
            while time.time() < end_time:
                # Decide whether to read or write based on ratio
                if random.random() < read_write_ratio:
                    # Perform read operation
                    start_time = time.time()
                    try:
                        if table_name == 'aquachain-readings':
                            device_id = f"LOAD-TEST-{random.randint(1000, 1049)}"
                            device_month = f"{device_id}#{datetime.now().strftime('%Y%m')}"
                            
                            response = table.query(
                                KeyConditionExpression='deviceId_month = :pk',
                                ExpressionAttributeValues={':pk': device_month},
                                Limit=5,
                                ReturnConsumedCapacity='TOTAL'
                            )
                        else:
                            response = table.scan(
                                Limit=5,
                                ReturnConsumedCapacity='TOTAL'
                            )
                        
                        end_time_op = time.time()
                        response_time = (end_time_op - start_time) * 1000
                        
                        if 'ConsumedCapacity' in response:
                            with self.lock:
                                consumed_capacity['read'] += response['ConsumedCapacity'].get('CapacityUnits', 0)
                        
                        local_results.append((True, response_time))
                        
                    except Exception:
                        end_time_op = time.time()
                        response_time = (end_time_op - start_time) * 1000
                        local_results.append((False, response_time))
                
                else:
                    # Perform write operation
                    start_time = time.time()
                    try:
                        if table_name == 'aquachain-readings':
                            device_id = f"LOAD-TEST-{random.randint(1000, 9999)}"
                            item = self.generate_reading_data(device_id)
                        elif table_name == 'aquachain-ledger':
                            sequence_number = int(time.time() * 1000000) + random.randint(1, 1000)
                            item = self.generate_ledger_entry(sequence_number)
                        else:
                            item = {
                                'id': str(uuid.uuid4()),
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'data': f"mixed_test_{random.randint(1000, 9999)}"
                            }
                        
                        response = table.put_item(
                            Item=item,
                            ReturnConsumedCapacity='TOTAL'
                        )
                        
                        end_time_op = time.time()
                        response_time = (end_time_op - start_time) * 1000
                        
                        if 'ConsumedCapacity' in response:
                            with self.lock:
                                consumed_capacity['write'] += response['ConsumedCapacity'].get('CapacityUnits', 0)
                        
                        local_results.append((True, response_time))
                        
                    except Exception:
                        end_time_op = time.time()
                        response_time = (end_time_op - start_time) * 1000
                        local_results.append((False, response_time))
                
                # Small delay between operations
                time.sleep(random.uniform(0.05, 0.2))
            
            with self.lock:
                results.extend(local_results)
        
        start_time = time.time()
        
        # Start concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [executor.submit(mixed_worker) for _ in range(concurrent_workers)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        return self._calculate_metrics(
            results, 'MIXED', table_name, actual_duration, 
            consumed_capacity['read'], consumed_capacity['write']
        )
    
    def _populate_test_data(self, table_name: str, num_items: int):
        """Pre-populate table with test data for read operations."""
        table = self.dynamodb.Table(table_name)
        
        with table.batch_writer() as batch:
            for i in range(num_items):
                if table_name == 'aquachain-readings':
                    device_id = f"LOAD-TEST-{1000 + i}"
                    item = self.generate_reading_data(device_id)
                elif table_name == 'aquachain-ledger':
                    sequence_number = 1000000 + i
                    item = self.generate_ledger_entry(sequence_number)
                else:
                    item = {
                        'id': f"test-{i}",
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'data': f"pre_populated_data_{i}"
                    }
                
                batch.put_item(Item=item)
    
    def _calculate_metrics(self, results: List[Tuple[bool, float]], operation_type: str, 
                          table_name: str, duration: float, consumed_read: float, 
                          consumed_write: float) -> DatabaseLoadTestResult:
        """Calculate performance metrics from test results."""
        successful_operations = sum(1 for success, _ in results if success)
        failed_operations = len(results) - successful_operations
        response_times = [rt for _, rt in results]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        operations_per_second = len(results) / duration if duration > 0 else 0
        error_rate = (failed_operations / len(results)) * 100 if results else 0
        
        return DatabaseLoadTestResult(
            operation_type=operation_type,
            table_name=table_name,
            total_operations=len(results),
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            operations_per_second=operations_per_second,
            error_rate=error_rate,
            consumed_read_capacity=consumed_read,
            consumed_write_capacity=consumed_write,
            duration=duration
        )
    
    def validate_sla_requirements(self, result: DatabaseLoadTestResult) -> Dict[str, bool]:
        """Validate database load test results against SLA requirements."""
        validations = {}
        
        # Database query performance: 95th percentile < 100ms
        validations['query_performance_sla'] = result.p95_response_time < 100
        
        # Error rate should be minimal
        validations['error_rate_sla'] = result.error_rate < 1.0
        
        # Minimum throughput requirements
        if result.operation_type == 'READ':
            validations['read_throughput_sla'] = result.operations_per_second > 50
        elif result.operation_type == 'WRITE':
            validations['write_throughput_sla'] = result.operations_per_second > 20
        else:  # MIXED
            validations['mixed_throughput_sla'] = result.operations_per_second > 30
        
        return validations
    
    def print_results(self, result: DatabaseLoadTestResult, test_name: str):
        """Print formatted database load test results."""
        print(f"\n📊 {test_name} Results:")
        print(f"   Table: {result.table_name}")
        print(f"   Operation Type: {result.operation_type}")
        print(f"   Total Operations: {result.total_operations}")
        print(f"   Successful: {result.successful_operations}")
        print(f"   Failed: {result.failed_operations}")
        print(f"   Error Rate: {result.error_rate:.2f}%")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Operations/sec: {result.operations_per_second:.2f}")
        print(f"   Avg Response Time: {result.avg_response_time:.2f}ms")
        print(f"   95th Percentile: {result.p95_response_time:.2f}ms")
        print(f"   99th Percentile: {result.p99_response_time:.2f}ms")
        print(f"   Max Response Time: {result.max_response_time:.2f}ms")
        print(f"   Consumed Read Capacity: {result.consumed_read_capacity:.2f}")
        print(f"   Consumed Write Capacity: {result.consumed_write_capacity:.2f}")
        
        # SLA validation
        validations = self.validate_sla_requirements(result)
        print(f"\n✅ SLA Validation:")
        for sla_name, passed in validations.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {sla_name}: {status}")

def main():
    """Main function to run database load tests."""
    parser = argparse.ArgumentParser(description='AquaChain Database Load Testing')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--concurrent-workers', type=int, default=50, 
                       help='Number of concurrent workers (default: 50)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Test duration in seconds (default: 300)')
    parser.add_argument('--test-type', type=str, choices=['read', 'write', 'mixed', 'all'], 
                       default='all', help='Type of test to run (default: all)')
    parser.add_argument('--table', type=str, choices=['readings', 'ledger', 'users', 'service-requests', 'all'], 
                       default='all', help='Table to test (default: all)')
    
    args = parser.parse_args()
    
    try:
        tester = DatabaseLoadTester(aws_region=args.aws_region)
        
        print("🔬 AquaChain Database Load Testing")
        print("=" * 50)
        
        # Define tables to test
        if args.table == 'all':
            tables = ['aquachain-readings', 'aquachain-ledger']
        else:
            table_mapping = {
                'readings': 'aquachain-readings',
                'ledger': 'aquachain-ledger',
                'users': 'aquachain-users',
                'service-requests': 'aquachain-service-requests'
            }
            tables = [table_mapping[args.table]]
        
        all_passed = True
        
        for table_name in tables:
            print(f"\n🗄️  Testing table: {table_name}")
            
            if args.test_type in ['read', 'all']:
                result = tester.run_read_load_test(
                    table_name=table_name,
                    concurrent_readers=args.concurrent_workers,
                    duration=min(args.duration, 180)
                )
                tester.print_results(result, f"Read Load Test - {table_name}")
                
                validations = tester.validate_sla_requirements(result)
                if not all(validations.values()):
                    all_passed = False
            
            if args.test_type in ['write', 'all']:
                result = tester.run_write_load_test(
                    table_name=table_name,
                    concurrent_writers=args.concurrent_workers,
                    duration=min(args.duration, 180),
                    items_per_writer=50
                )
                tester.print_results(result, f"Write Load Test - {table_name}")
                
                validations = tester.validate_sla_requirements(result)
                if not all(validations.values()):
                    all_passed = False
            
            if args.test_type in ['mixed', 'all']:
                result = tester.run_mixed_workload_test(
                    table_name=table_name,
                    concurrent_workers=args.concurrent_workers,
                    duration=args.duration
                )
                tester.print_results(result, f"Mixed Workload Test - {table_name}")
                
                validations = tester.validate_sla_requirements(result)
                if not all(validations.values()):
                    all_passed = False
        
        # Overall assessment
        print("\n🎯 Overall Assessment:")
        if all_passed:
            print("✅ All database load tests passed SLA requirements!")
            return 0
        else:
            print("❌ Some database load tests failed SLA requirements!")
            return 1
            
    except Exception as e:
        print(f"💥 Database load test failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())